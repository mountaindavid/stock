from rest_framework import serializers
from .models import Stock, PriceHistory
from datetime import datetime


class StockSerializer(serializers.ModelSerializer):
    """Serializer for Stock model"""
    
    class Meta:
        model = Stock
        fields = [
            'id', 'ticker', 'name', 'sector', 'industry',
            'current_price', 'last_updated'
        ]
        read_only_fields = ['id', 'last_updated']
    
    
    def validate_ticker(self, value):
        """Validate ticker format"""
        if not value or len(value.strip()) < 1:
            raise serializers.ValidationError('Ticker cannot be empty')
        return value.upper().strip()
    
    def validate_current_price(self, value):
        """Validate price is positive"""
        if value and value <= 0:
            raise serializers.ValidationError('Price must be positive')
        return value


class PriceHistorySerializer(serializers.ModelSerializer):
    """Serializer for PriceHistory model"""
    
    class Meta:
        model = PriceHistory
        fields = [
            'id', 'stock', 'price', 'date', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
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

