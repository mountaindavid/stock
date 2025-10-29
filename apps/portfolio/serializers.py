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
                from .services import FIFOCalculator
                calculator = FIFOCalculator()
                current_quantity = calculator.get_current_holdings(portfolio, ticker)
                
                if sell_quantity > current_quantity:
                    raise serializers.ValidationError({
                        'quantity': f'Insufficient shares. Trying to sell {sell_quantity} shares of {ticker}, but only have {current_quantity} shares available.'
                    })
        
        return attrs

    def create(self, validated_data):
        # If price is not specified, automatically get current price
        if 'price' not in validated_data or validated_data['price'] is None:
            ticker = validated_data['ticker']
            validated_data['price'] = self._get_current_price(ticker)
        
        # Get or create Stock object
        ticker = validated_data['ticker']
        stock, created = Stock.objects.get_or_create(
            ticker=ticker,
            defaults={'name': ticker}  # Default name, can be updated later
        )
        
        # Update current_price if it's not set or if we have a new price
        if not stock.current_price or created:
            try:
                current_price = self._get_current_price(ticker)
                stock.current_price = current_price
                stock.save(update_fields=['current_price'])
            except Exception:
                # If price fetch fails, continue without updating
                pass
        
        validated_data['stock'] = stock
        
        return super().create(validated_data)
    

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
        from .services import FIFOCalculator
        
        # Get all transactions for this portfolio
        transactions = Transaction.objects.filter(portfolio=obj)
        
        if not transactions.exists():
            return Decimal('0.00')
        
        # Use FIFOCalculator to get holdings
        calculator = FIFOCalculator()
        holdings = calculator.calculate_holdings(transactions)
        
        total_value = Decimal('0')
        
        # Calculate current market value for each holding
        for ticker, holding in holdings.items():
            quantity = holding['quantity']
            stock = holding['stock']
            
            if quantity > 0 and stock and stock.current_price:
                # Use only current market price for total_value calculation
                current_price = stock.current_price
                total_value += quantity * current_price
        
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