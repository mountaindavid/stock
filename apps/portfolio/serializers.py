from rest_framework import serializers
from .models import Portfolio, Transaction
from apps.stocks.models import Stock

class TransactionSerializer(serializers.ModelSerializer):
    """Serializer for Transaction model"""
    
    stock_ticker = serializers.CharField(write_only=True)
    ticker = serializers.CharField(source='stock.ticker', read_only=True) 
    company_name = serializers.CharField(source='stock.name', read_only=True)
    date = serializers.DateField(required=False, allow_null=True)

    # Calculated fields
    purchase_total = serializers.SerializerMethodField()
    current_market_price = serializers.SerializerMethodField()
    current_total = serializers.SerializerMethodField()
    profit_loss_by_transaction = serializers.SerializerMethodField()
    profit_loss_by_average = serializers.SerializerMethodField()
    average_purchase_price = serializers.SerializerMethodField()
    profit_loss_percentage_by_transaction = serializers.SerializerMethodField()
    profit_loss_percentage_by_average = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        fields = [
            'id', 'stock', 'stock_ticker', 'ticker', 'company_name', 'portfolio',
            'transaction_type', 'quantity', 'price_per_share', 'date', 'transaction_date',
            'purchase_total', 'current_market_price', 'current_total', 
            'profit_loss_by_transaction', 'profit_loss_by_average', 'average_purchase_price',
            'profit_loss_percentage_by_transaction', 'profit_loss_percentage_by_average'
        ]
        read_only_fields = ['id', 'portfolio', 'transaction_date', 'stock']
    
    def validate_stock_ticker(self, value):
        """Validate stock ticker exists"""
        try:
            stock = Stock.objects.get(ticker=value.upper())
            self._validated_stock = stock
            return value.upper()
        except Stock.DoesNotExist:
            raise serializers.ValidationError(f'Stock {value.upper()} does not exist. Please create it first.')
    
    def validate_quantity(self, value):
        """Validate quantity is positive"""
        if value <= 0:
            raise serializers.ValidationError('Quantity must be positive')
        return value
    
    def validate_price_per_share(self, value):
        """Validate price is positive"""
        if value <= 0:
            raise serializers.ValidationError('Price must be positive')
        return value
    
    def validate(self, attrs):
        """Validate transaction"""
        # Validate sell transaction
        if attrs['transaction_type'] == 'SELL':
            stock_ticker = attrs['stock_ticker']
            portfolio = self.context.get('portfolio')
            if portfolio:
                if attrs['quantity'] > portfolio.get_owned_shares(stock_ticker):
                    raise serializers.ValidationError('You do not have enough shares to sell')
        
        return attrs
    
    def create(self, validated_data):
        """Create transaction with proper stock and portfolio"""
        validated_data.pop('stock_ticker')  
        stock = getattr(self, '_validated_stock', None)  
        
        if not stock:
            raise serializers.ValidationError('Stock validation failed')
        
        # Get portfolio from context
        portfolio = self.context.get('portfolio')
        if not portfolio:
            raise serializers.ValidationError('Portfolio must be provided in context')
        
        validated_data['stock'] = stock
        validated_data['portfolio'] = portfolio
        
        return super().create(validated_data)

    def get_purchase_total(self, obj):
        """Calculate total purchase amount for this transaction"""
        return obj.quantity * obj.price_per_share
    
    def get_current_market_price(self, obj):
        """Get current market price from cache or API"""
        from django.core.cache import cache
        from apps.stocks.services import FinnhubService
        
        # Попробовать получить из кеша
        cache_key = f"stock_price_{obj.stock.ticker}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data['price']
        
        # Если нет в кеше, попробовать получить через API
        try:
            service = FinnhubService()
            price_data = service.get_stock_price(obj.stock.ticker)
            return price_data['price']
        except:
            # Fallback на цену покупки только при ошибке API
            return obj.price_per_share
    
    def get_current_total(self, obj):
        """Calculate current total value using market price"""
        return obj.quantity * self.get_current_market_price(obj)
    
    def get_average_purchase_price(self, obj):
        """Get average purchase price for this ticker in portfolio"""
        return obj.portfolio.get_average_purchase_price(obj.stock.ticker)
    
    def get_profit_loss_by_transaction(self, obj):
        """Calculate profit/loss based on this transaction's purchase price"""
        current_price = self.get_current_market_price(obj)
        return (current_price - obj.price_per_share) * obj.quantity
    
    def get_profit_loss_by_average(self, obj):
        """Calculate profit/loss based on average purchase price"""
        current_price = self.get_current_market_price(obj)
        average_price = self.get_average_purchase_price(obj)
        owned_shares = obj.portfolio.get_owned_shares(obj.stock.ticker)
        return (current_price - average_price) * owned_shares
    
    def get_profit_loss_percentage_by_transaction(self, obj):
        """Calculate profit/loss percentage based on transaction price"""
        purchase_total = self.get_purchase_total(obj)
        if purchase_total == 0:
            return 0
        return (self.get_profit_loss_by_transaction(obj) / purchase_total) * 100
    
    def get_profit_loss_percentage_by_average(self, obj):
        """Calculate profit/loss percentage based on average price"""
        average_price = self.get_average_purchase_price(obj)
        if average_price == 0:
            return 0
        owned_shares = obj.portfolio.get_owned_shares(obj.stock.ticker)
        if owned_shares == 0:
            return 0
        average_total = average_price * owned_shares
        return (self.get_profit_loss_by_average(obj) / average_total) * 100

class PortfolioSerializer(serializers.ModelSerializer):
    """Serializer for Portfolio model"""
    transactions = TransactionSerializer(many=True, read_only=True)

    # Calculated fields
    total_value = serializers.SerializerMethodField()
    total_invested = serializers.SerializerMethodField()
    total_profit_loss = serializers.SerializerMethodField()
    total_profit_loss_by_average = serializers.SerializerMethodField()
    total_profit_loss_percentage = serializers.SerializerMethodField()
    total_profit_loss_percentage_by_average = serializers.SerializerMethodField()
    
    class Meta:
        model = Portfolio
        fields = [
            'id', 'user', 'name', 'description', 
            'created_at', 'updated_at',
            'transactions', 'total_value', 'total_invested', 'total_profit_loss',
            'total_profit_loss_by_average', 'total_profit_loss_percentage', 
            'total_profit_loss_percentage_by_average'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def validate_name(self, value):
        """Validate portfolio name uniqueness per user"""
        user = self.context['request'].user
        if self.instance:
            # For updates, exclude current instance
            if Portfolio.objects.filter(user=user, name=value).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError('Portfolio with this name already exists')
        else:
            # For creation
            if Portfolio.objects.filter(user=user, name=value).exists():
                raise serializers.ValidationError('Portfolio with this name already exists')
        return value
    
    def create(self, validated_data):
        """Create portfolio with current user"""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

    def get_current_market_price(self, ticker):
        """Get current market price from cache or API"""
        from django.core.cache import cache
        from apps.stocks.services import FinnhubService
        
        # Попробовать получить из кеша
        cache_key = f"stock_price_{ticker}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data['price']
        
        # Если нет в кеше, попробовать получить через API
        try:
            service = FinnhubService()
            price_data = service.get_stock_price(ticker)
            return price_data['price']
        except:
            return 0

    def get_total_value(self, obj):
        """Calculate total current value of portfolio using market prices"""
        total = 0
        # Группируем транзакции по тикеру для эффективности
        ticker_quantities = {}
        
        for transaction in obj.transactions.all():
            if transaction.transaction_type == 'BUY':
                ticker = transaction.stock.ticker
                if ticker not in ticker_quantities:
                    ticker_quantities[ticker] = 0
                ticker_quantities[ticker] += transaction.quantity
            elif transaction.transaction_type == 'SELL':
                ticker = transaction.stock.ticker
                if ticker not in ticker_quantities:
                    ticker_quantities[ticker] = 0
                ticker_quantities[ticker] -= transaction.quantity
        
        # Рассчитываем стоимость по текущим рыночным ценам
        for ticker, quantity in ticker_quantities.items():
            if quantity > 0:  # Только если у нас есть акции
                current_price = self.get_current_market_price(ticker)
                total += current_price * quantity
                
        return total

    def get_total_invested(self, obj):
        """Calculate total amount invested (only BUY transactions)"""
        total = 0
        for transaction in obj.transactions.all():
            if transaction.transaction_type == 'BUY':
                total += transaction.price_per_share * transaction.quantity
        return total

    def get_total_profit_loss(self, obj):
        """Calculate total profit/loss using individual transaction prices"""
        return self.get_total_value(obj) - self.get_total_invested(obj)
    
    def get_total_profit_loss_by_average(self, obj):
        """Calculate total profit/loss using average purchase prices"""
        total_profit_loss = 0
        
        # Группируем транзакции по тикеру
        ticker_quantities = {}
        for transaction in obj.transactions.all():
            if transaction.transaction_type == 'BUY':
                ticker = transaction.stock.ticker
                if ticker not in ticker_quantities:
                    ticker_quantities[ticker] = 0
                ticker_quantities[ticker] += transaction.quantity
            elif transaction.transaction_type == 'SELL':
                ticker = transaction.stock.ticker
                if ticker not in ticker_quantities:
                    ticker_quantities[ticker] = 0
                ticker_quantities[ticker] -= transaction.quantity
        
        # Рассчитываем прибыль/убыток по средней цене
        for ticker, quantity in ticker_quantities.items():
            if quantity > 0:  # Только если у нас есть акции
                current_price = self.get_current_market_price(ticker)
                average_price = obj.get_average_purchase_price(ticker)
                total_profit_loss += (current_price - average_price) * quantity
                
        return total_profit_loss
    
    def get_total_profit_loss_percentage(self, obj):
        """Calculate total profit/loss percentage using individual transaction prices"""
        total_invested = self.get_total_invested(obj)
        if total_invested == 0:
            return 0
        return (self.get_total_profit_loss(obj) / total_invested) * 100
    
    def get_total_profit_loss_percentage_by_average(self, obj):
        """Calculate total profit/loss percentage using average purchase prices"""
        total_invested = self.get_total_invested(obj)
        if total_invested == 0:
            return 0
        return (self.get_total_profit_loss_by_average(obj) / total_invested) * 100