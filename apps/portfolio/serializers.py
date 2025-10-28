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
    current_price = serializers.SerializerMethodField()
    current_total = serializers.SerializerMethodField()
    profit_loss = serializers.SerializerMethodField()
    profit_loss_percentage = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        fields = [
            'id', 'stock', 'stock_ticker', 'ticker', 'company_name', 'portfolio',
            'transaction_type', 'quantity', 'price_per_share', 'date', 'transaction_date',
            'purchase_total', 'current_price', 'current_total', 'profit_loss', 'profit_loss_percentage'
        ]
        read_only_fields = ['id', 'portfolio', 'transaction_date']
    
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
        """Calculate total purchase amount"""
        return obj.quantity * obj.price_per_share
    
    def get_current_price(self, obj):
        """Get current stock price"""
        return obj.stock.current_price if obj.stock.current_price else obj.price_per_share
    
    def get_current_total(self, obj):
        """Calculate current total value"""
        return obj.quantity * self.get_current_price(obj)
    
    def get_profit_loss(self, obj):
        """Calculate profit/loss"""
        return self.get_current_total(obj) - self.get_purchase_total(obj)

    def get_profit_loss_percentage(self, obj):
        """Calculate profit/loss percentage"""
        purchase_total = self.get_purchase_total(obj)
        if purchase_total == 0:
            return 0
        return (self.get_profit_loss(obj) / purchase_total) * 100

class PortfolioSerializer(serializers.ModelSerializer):
    """Serializer for Portfolio model"""
    transactions = TransactionSerializer(many=True, read_only=True)

    # Calculated fields
    total_value = serializers.SerializerMethodField()
    total_invested = serializers.SerializerMethodField()
    total_profit_loss = serializers.SerializerMethodField()
    
    class Meta:
        model = Portfolio
        fields = [
            'id', 'user', 'name', 'description', 
            'created_at', 'updated_at',
            'transactions', 'total_value', 'total_invested', 'total_profit_loss'
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

    def get_total_value(self, obj):
        """Calculate total current value of portfolio"""
        total = 0
        for transaction in obj.transactions.all():
            if transaction.transaction_type == 'BUY':
                # Use current price if available, otherwise use purchase price
                price = transaction.stock.current_price if transaction.stock.current_price else transaction.price_per_share
                total += price * transaction.quantity
        return total

    def get_total_invested(self, obj):
        """Calculate total amount invested"""
        total = 0
        for transaction in obj.transactions.all():
            if transaction.transaction_type == 'BUY':
                total += transaction.price_per_share * transaction.quantity
        return total

    def get_total_profit_loss(self, obj):
        """Calculate total profit/loss"""
        return self.get_total_value(obj) - self.get_total_invested(obj)