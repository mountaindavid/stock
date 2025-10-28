from rest_framework import serializers
from .models import Stock


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



