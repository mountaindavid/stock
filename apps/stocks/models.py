from django.db import models
from django.core.exceptions import ValidationError
from datetime import datetime

class Stock(models.Model):
    ticker = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=255)
    sector = models.CharField(max_length=100, blank=True)
    industry = models.CharField(max_length=100, blank=True)
    current_price = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.ticker

    class Meta:
        indexes = [
            models.Index(fields=['ticker']),  # Already unique, but explicit
            models.Index(fields=['sector']),  # For sector filtering
            models.Index(fields=['last_updated']),  # For price update queries
        ]

    def clean(self):
        if self.current_price and self.current_price <= 0:
            raise ValidationError(
                'Price must be positive'
            )

