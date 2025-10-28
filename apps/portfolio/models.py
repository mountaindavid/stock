from django.db import models
from apps.users.models import User
from apps.stocks.models import Stock
from django.core.exceptions import ValidationError
from django.db.models import Sum, Case, When, IntegerField

class Portfolio(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, null=False, blank=False)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    def get_average_purchase_price(self, ticker):
        """Get average purchase price for a specific ticker in this portfolio"""
        try:
            stock = Stock.objects.get(ticker=ticker)
        except Stock.DoesNotExist:
            return 0
        
        
        buy_transactions = Transaction.objects.filter(
            portfolio=self,
            stock=stock,
            transaction_type='BUY'
        )
        
        if not buy_transactions.exists():
            return 0
        
        total_cost = sum(t.price_per_share * t.quantity for t in buy_transactions)
        
        total_quantity = sum(t.quantity for t in buy_transactions)
        
        if total_quantity == 0:
            return 0
            
        return total_cost / total_quantity
        
    def get_owned_shares(self, ticker):
        """Get total owned shares for a specific ticker in this portfolio"""
        try:
            stock = Stock.objects.get(ticker=ticker)
        except Stock.DoesNotExist:
            return 0
        
        result = Transaction.objects.filter(
            portfolio=self,
            stock=stock
        ).aggregate(
            total=Sum(
                Case(
                    When(transaction_type='BUY', then='quantity'),
                    When(transaction_type='SELL', then=-models.F('quantity')),
                    default=0,
                    output_field=IntegerField()
                )
            )
        )['total'] or 0
        
        return result

    class Meta:
        indexes = [
            models.Index(fields=['user', 'name'])
        ]
        unique_together = ['user', 'name']


class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('BUY', 'Buy'),
        ('SELL', 'Sell'),
    ]

    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='transactions')
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=4, choices=TRANSACTION_TYPES)
    quantity = models.PositiveIntegerField()
    price_per_share = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    date = models.DateField(null=True, blank=True, help_text="Manual date")
    transaction_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.stock.ticker

    class Meta:
        indexes = [
            models.Index(fields=['portfolio', 'stock']), 
            models.Index(fields=['transaction_date']),  
            models.Index(fields=['transaction_type']), 
        ]
    
    def clean(self):
        if self.price_per_share <= 0:
            raise ValidationError(
                'Price must be positive'
            )

        if self.transaction_type == 'SELL':
            if self.pk and self.quantity > self.portfolio.get_owned_shares(self.stock.ticker):
                raise ValidationError(
                    'You do not have enough shares to sell'
                )

    @property
    def calculated_total(self):
        """instead of stored total_amount"""
        return self.quantity * self.price_per_share