from django.db import models
from apps.users.models import User
from apps.stocks.models import Stock

class Portfolio(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    name = models.CharField(max_length=255, db_index=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        unique_together = ['user', 'name']

class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('BUY', 'Buy'),
        ('SELL', 'Sell'),
    ]

    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='transactions')
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='transactions', null=True, blank=True)
    ticker = models.CharField(max_length=10, db_index=True, default='')  # Keep for backward compatibility
    quantity = models.DecimalField(max_digits=15, decimal_places=0)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    date = models.DateTimeField(db_index=True)
    transaction_type = models.CharField(max_length=4, choices=TRANSACTION_TYPES, db_index=True)

    def __str__(self):
        return f"{self.transaction_type} {self.quantity} {self.ticker} @ {self.price}"

    class Meta:
        ordering = ['date']