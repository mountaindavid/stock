from rest_framework import serializers
from .models import Stock

class StockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stock
        fields = ['id', 'ticker', 'name', 'current_price', 'last_updated']
        read_only_fields = ['id', 'last_updated']

    def validate_ticker(self, value):
        return value.upper().strip()
