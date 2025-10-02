from rest_framework import serializers
from .models import Stock, PriceHistory
from datetime import datetime


class StockSerializer(serializers.ModelSerializer):
    """Serializer for Stock model"""
    
    price_change = serializers.SerializerMethodField()
    price_change_percent = serializers.SerializerMethodField()
    
    class Meta:
        model = Stock
        fields = [
            'id', 'ticker', 'name', 'sector', 'industry',
            'current_price', 'price_change', 'price_change_percent',
            'last_updated'
        ]
        read_only_fields = ['id', 'last_updated']
        extra_kwargs = {
            'ticker': {'help_text': 'Stock ticker symbol (e.g., AAPL)'},
            'name': {'help_text': 'Company name'},
            'sector': {'help_text': 'Business sector (e.g., Technology)'},
            'industry': {'help_text': 'Specific industry (e.g., Software)'},
            'current_price': {'help_text': 'Current stock price'},
        }
    
    def get_price_change(self, obj):
        """Calculate price change from previous day"""
        if not obj.current_price:
            return None
        
        # Get previous day's price
        yesterday = datetime.now().date()
        try:
            yesterday_price = PriceHistory.objects.filter(
                stock=obj,
                date=yesterday
            ).latest('date').price
            return float(obj.current_price - yesterday_price)
        except PriceHistory.DoesNotExist:
            return None
    
    def get_price_change_percent(self, obj):
        """Calculate price change percentage"""
        price_change = self.get_price_change(obj)
        if price_change is None or not obj.current_price:
            return None
        
        return round((price_change / float(obj.current_price)) * 100, 2)
    
    def validate_ticker(self, value):
        """Validate ticker format"""
        return value.upper().strip()
    
    def validate_current_price(self, value):
        """Validate price is positive"""
        if value and value <= 0:
            raise serializers.ValidationError('Price must be positive')
        return value


class PriceHistorySerializer(serializers.ModelSerializer):
    """Serializer for PriceHistory model"""
    
    stock_ticker = serializers.CharField(source='stock.ticker', read_only=True)
    stock_name = serializers.CharField(source='stock.name', read_only=True)
    
    class Meta:
        model = PriceHistory
        fields = [
            'id', 'stock', 'stock_ticker', 'stock_name', 'price', 
            'date', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
        extra_kwargs = {
            'price': {'help_text': 'Stock price on this date'},
            'date': {'help_text': 'Date of the price record'},
        }
    
    def validate_price(self, value):
        """Validate price is positive"""
        if value <= 0:
            raise serializers.ValidationError('Price must be positive')
        return value
    
    def validate_date(self, value):
        """Validate date is not in the future"""
        if value > datetime.now().date():
            raise serializers.ValidationError('Date cannot be in the future')
        return value
    
    def validate(self, attrs):
        """Validate unique stock-date combination"""
        stock = attrs.get('stock')
        date = attrs.get('date')
        
        if stock and date:
            # Check for existing price history for this stock on this date
            existing = PriceHistory.objects.filter(
                stock=stock, 
                date=date
            )
            
            # Exclude current instance if updating
            if self.instance:
                existing = existing.exclude(id=self.instance.id)
            
            if existing.exists():
                raise serializers.ValidationError(
                    f'Price history already exists for {stock.ticker} on {date}'
                )
        
        return attrs


class StockListSerializer(serializers.ModelSerializer):
    """Simplified serializer for stock listings"""
    
    class Meta:
        model = Stock
        fields = ['id', 'ticker', 'name', 'current_price', 'last_updated']
        read_only_fields = ['id', 'last_updated']


class PriceHistoryCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating price history records"""
    
    stock_ticker = serializers.CharField()
    
    class Meta:
        model = PriceHistory
        fields = ['stock_ticker', 'price', 'date']
    
    def validate_stock_ticker(self, value):
        """Validate stock ticker exists"""
        try:
            Stock.objects.get(ticker=value.upper())
            return value.upper()
        except Stock.DoesNotExist:
            raise serializers.ValidationError(f'Stock with ticker {value} does not exist')
    
    def create(self, validated_data):
        """Create price history with proper stock relationship"""
        stock_ticker = validated_data.pop('stock_ticker')
        stock = Stock.objects.get(ticker=stock_ticker)
        validated_data['stock'] = stock
        
        return super().create(validated_data)
