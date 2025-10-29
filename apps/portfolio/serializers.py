from rest_framework import serializers
from .models import Portfolio, Transaction
from apps.stocks.models import Stock
from decimal import Decimal

class TransactionSerializer(serializers.ModelSerializer):
    total_price = serializers.SerializerMethodField()
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'stock', 'ticker', 'quantity', 'price', 'total_price', 'date', 'transaction_type'
        ]
        read_only_fields = ['id', 'total_price']

    def validate_ticker(self, value):
        return value.upper().strip()

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError('Quantity must be positive')
        return value

    def validate_price(self, value):
        if value is not None and value <= 0:
            raise serializers.ValidationError('Price must be positive')
        return value

    def validate(self, attrs):
        """Validate transaction data including SELL quantity validation"""
        if attrs.get('transaction_type') == 'SELL':
            # We need portfolio context for validation
            portfolio = self.context.get('portfolio')
            ticker = attrs.get('ticker')
            sell_quantity = attrs.get('quantity')
            
            if portfolio and ticker and sell_quantity:
                current_quantity = self._calculate_current_holdings(portfolio, ticker)
                
                if sell_quantity > current_quantity:
                    raise serializers.ValidationError({
                        'quantity': f'Insufficient shares. Trying to sell {sell_quantity} shares of {ticker}, but only have {current_quantity} shares available.'
                    })
        
        return attrs

    def create(self, validated_data):
        # Если цена не указана, получаем текущую цену автоматически
        if 'price' not in validated_data or validated_data['price'] is None:
            ticker = validated_data['ticker']
            validated_data['price'] = self._get_current_price(ticker)
        
        # Get or create Stock object
        ticker = validated_data['ticker']
        stock, created = Stock.objects.get_or_create(
            ticker=ticker,
            defaults={'name': ticker}  # Default name, can be updated later
        )
        validated_data['stock'] = stock
        
        return super().create(validated_data)
    
    def _calculate_current_holdings(self, portfolio, ticker):
        """Calculate current holdings for a ticker using FIFO logic"""
        from decimal import Decimal
        
        transactions = Transaction.objects.filter(
            portfolio=portfolio,
            ticker=ticker
        ).order_by('date')
        
        fifo_queue = []
        current_quantity = Decimal('0')
        
        for transaction in transactions:
            if transaction.transaction_type == 'BUY':
                fifo_queue.append((transaction.quantity, transaction.price or Decimal('0')))
                current_quantity += transaction.quantity
            else:  # SELL
                sell_quantity = transaction.quantity
                
                # Process sell using FIFO
                remaining_to_sell = sell_quantity
                while remaining_to_sell > 0 and fifo_queue:
                    available_qty, buy_price = fifo_queue[0]
                    
                    if available_qty <= remaining_to_sell:
                        remaining_to_sell -= available_qty
                        current_quantity -= available_qty
                        fifo_queue.pop(0)
                    else:
                        current_quantity -= remaining_to_sell
                        fifo_queue[0] = (available_qty - remaining_to_sell, buy_price)
                        remaining_to_sell = 0
        
        return current_quantity

    def _get_current_price(self, ticker):
        """Get current price from cache or Finnhub service"""
        from django.core.cache import cache
        from apps.stocks.services import FinnhubService
        
        # Try cache first
        cache_key = f"stock_price_{ticker}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return Decimal(str(cached_data['price']))
        
        # Fallback to API
        try:
            service = FinnhubService()
            price_data = service.get_stock_price(ticker)
            return Decimal(str(price_data['price']))
        except Exception:
            raise serializers.ValidationError(f'Unable to fetch current price for {ticker}')
    
    def get_total_price(self, obj):
        """Calculate total price as quantity * price"""
        if obj.price is not None:
            return (obj.quantity * obj.price).quantize(Decimal('0.01'))
        return None

class FIFOPositionSerializer(serializers.Serializer):
    ticker = serializers.CharField()
    remaining_qty = serializers.DecimalField(max_digits=15, decimal_places=0)
    buy_price = serializers.DecimalField(max_digits=10, decimal_places=2)

class FIFOResultSerializer(serializers.Serializer):
    total_profit = serializers.DecimalField(max_digits=15, decimal_places=2)
    positions = FIFOPositionSerializer(many=True)


class PortfolioStockSerializer(serializers.Serializer):
    """Serializer for stocks in a portfolio with calculated holdings"""
    id = serializers.IntegerField()
    ticker = serializers.CharField()
    name = serializers.CharField()
    quantity = serializers.DecimalField(max_digits=15, decimal_places=0)
    current_price = serializers.DecimalField(max_digits=10, decimal_places=2, allow_null=True)
    total_price = serializers.DecimalField(max_digits=15, decimal_places=2, allow_null=True)
    average_price_per_share = serializers.DecimalField(max_digits=10, decimal_places=2, allow_null=True)
    last_updated = serializers.DateTimeField()

class PortfolioSerializer(serializers.ModelSerializer):
    total_value = serializers.SerializerMethodField()
    
    class Meta:
        model = Portfolio
        fields = ['id', 'user', 'name', 'description', 'created_at', 'updated_at', 'total_value']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at', 'total_value']

    def get_total_value(self, obj):
        """Calculate total portfolio value using current market prices"""
        from decimal import Decimal
        
        # Get all transactions for this portfolio
        transactions = Transaction.objects.filter(portfolio=obj)
        
        if not transactions.exists():
            return Decimal('0.00')
        
        # Calculate holdings by ticker using FIFO logic
        holdings = {}
        
        # Group transactions by ticker and sort by date
        ticker_transactions = {}
        for transaction in transactions.order_by('date'):
            ticker = transaction.ticker
            if ticker not in ticker_transactions:
                ticker_transactions[ticker] = []
            ticker_transactions[ticker].append(transaction)
        
        total_value = Decimal('0')
        
        # Process each ticker's transactions
        for ticker, ticker_txns in ticker_transactions.items():
            # FIFO queue: list of (quantity, price) tuples
            fifo_queue = []
            current_quantity = Decimal('0')
            
            for transaction in ticker_txns:
                if transaction.transaction_type == 'BUY':
                    # Add to FIFO queue
                    fifo_queue.append((transaction.quantity, transaction.price or Decimal('0')))
                    current_quantity += transaction.quantity
                else:  # SELL
                    sell_quantity = transaction.quantity
                    
                    # Process sell using FIFO
                    remaining_to_sell = sell_quantity
                    while remaining_to_sell > 0 and fifo_queue:
                        available_qty, buy_price = fifo_queue[0]
                        
                        if available_qty <= remaining_to_sell:
                            remaining_to_sell -= available_qty
                            current_quantity -= available_qty
                            fifo_queue.pop(0)
                        else:
                            current_quantity -= remaining_to_sell
                            fifo_queue[0] = (available_qty - remaining_to_sell, buy_price)
                            remaining_to_sell = 0
            
            # Calculate current value for this ticker
            if current_quantity > 0 and ticker_txns[0].stock and ticker_txns[0].stock.current_price:
                current_price = ticker_txns[0].stock.current_price
                total_value += current_quantity * current_price
        
        # Round to 2 decimal places
        return total_value.quantize(Decimal('0.01'))

    def validate_name(self, value):
        user = self.context['request'].user
        queryset = Portfolio.objects.filter(user=user, name=value)
        if self.instance:
            queryset = queryset.exclude(id=self.instance.id)
        if queryset.exists():
            raise serializers.ValidationError('Portfolio with this name already exists')
        return value