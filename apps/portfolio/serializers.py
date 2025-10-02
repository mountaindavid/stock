from rest_framework import serializers
from .models import Portfolio, Transaction
from apps.stocks.models import Stock


class PortfolioSerializer(serializers.ModelSerializer):
    """Serializer for Portfolio model"""
    
    user = serializers.StringRelatedField(read_only=True)
    transaction_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Portfolio
        fields = [
            'id', 'user', 'name', 'description', 
            'created_at', 'updated_at', 'transaction_count'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
        extra_kwargs = {
            'name': {'help_text': 'Portfolio name (unique per user)'},
            'description': {'help_text': 'Optional portfolio description'},
        }
    
    def get_transaction_count(self, obj):
        """Get the number of transactions in this portfolio"""
        return obj.transaction_set.count()
    
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


class TransactionSerializer(serializers.ModelSerializer):
    """Serializer for Transaction model"""
    
    portfolio = serializers.StringRelatedField(read_only=True)
    stock = serializers.StringRelatedField(read_only=True)
    stock_ticker = serializers.CharField(write_only=True)
    total_value = serializers.SerializerMethodField()
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'portfolio', 'stock', 'stock_ticker', 'transaction_type',
            'quantity', 'price_per_share', 'total_value', 'transaction_date'
        ]
        read_only_fields = ['id', 'portfolio', 'transaction_date']
        extra_kwargs = {
            'quantity': {'help_text': 'Number of shares'},
            'price_per_share': {'help_text': 'Price per share at time of transaction'},
            'transaction_type': {'help_text': 'BUY or SELL'},
        }
    
    def get_total_value(self, obj):
        """Calculate total transaction value"""
        return float(obj.quantity * obj.price_per_share)
    
    def validate_stock_ticker(self, value):
        """Validate stock ticker exists"""
        try:
            stock = Stock.objects.get(ticker=value.upper())
            return value.upper()
        except Stock.DoesNotExist:
            raise serializers.ValidationError(f'Stock with ticker {value} does not exist')
    
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
        """Validate transaction logic"""
        if attrs['transaction_type'] == 'SELL':
            # Check if user has enough shares to sell
            stock_ticker = attrs['stock_ticker']
            portfolio = self.context['request'].user.portfolio_set.first()
            
            if portfolio:
                # This would need to be implemented in the model
                # For now, we'll skip this validation
                pass
        
        return attrs
    
    def create(self, validated_data):
        """Create transaction with proper stock and portfolio"""
        stock_ticker = validated_data.pop('stock_ticker')
        stock = Stock.objects.get(ticker=stock_ticker)
        
        # Get user's portfolio (assuming one portfolio per user for now)
        portfolio = self.context['request'].user.portfolio_set.first()
        if not portfolio:
            raise serializers.ValidationError('User must have a portfolio to create transactions')
        
        validated_data['stock'] = stock
        validated_data['portfolio'] = portfolio
        
        return super().create(validated_data)


class TransactionCreateSerializer(serializers.ModelSerializer):
    """Simplified serializer for creating transactions"""
    
    stock_ticker = serializers.CharField()
    
    class Meta:
        model = Transaction
        fields = [
            'stock_ticker', 'transaction_type', 'quantity', 'price_per_share'
        ]
    
    def validate_stock_ticker(self, value):
        """Validate stock ticker exists"""
        try:
            Stock.objects.get(ticker=value.upper())
            return value.upper()
        except Stock.DoesNotExist:
            raise serializers.ValidationError(f'Stock with ticker {value} does not exist')
    
    def create(self, validated_data):
        """Create transaction with proper relationships"""
        stock_ticker = validated_data.pop('stock_ticker')
        stock = Stock.objects.get(ticker=stock_ticker)
        
        # Get user's portfolio
        portfolio = self.context['request'].user.portfolio_set.first()
        if not portfolio:
            raise serializers.ValidationError('User must have a portfolio to create transactions')
        
        validated_data['stock'] = stock
        validated_data['portfolio'] = portfolio
        
        return super().create(validated_data)
