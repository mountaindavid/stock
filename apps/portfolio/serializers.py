from rest_framework import serializers
from .models import Portfolio, Transaction
from apps.stocks.models import Stock


class PortfolioSerializer(serializers.ModelSerializer):
    """Serializer for Portfolio model"""
    
    class Meta:
        model = Portfolio
        fields = [
            'id', 'user', 'name', 'description', 
            'created_at', 'updated_at'
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


class TransactionSerializer(serializers.ModelSerializer):
    """Serializer for Transaction model"""
    
    stock_ticker = serializers.CharField(write_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'portfolio', 'stock', 'stock_ticker', 'transaction_type',
            'quantity', 'price_per_share', 'transaction_date'
        ]
        read_only_fields = ['id', 'portfolio', 'transaction_date']
    
    def validate_stock_ticker(self, value):
        """Validate stock ticker exists"""
        try:
            stock = Stock.objects.get(ticker=value.upper())
            self._validated_stock = stock
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
        validated_data.pop('stock_ticker')  
        stock = getattr(self, '_validated_stock', None)  
        
        if not stock:
            raise serializers.ValidationError('Stock validation failed')
        
        # Get user's portfolio (assuming one portfolio per user for now)
        portfolio = self.context['request'].user.portfolio_set.first()
        if not portfolio:
            raise serializers.ValidationError('User must have a portfolio to create transactions')
        
        validated_data['stock'] = stock
        validated_data['portfolio'] = portfolio
        
        return super().create(validated_data)


