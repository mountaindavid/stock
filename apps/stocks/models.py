from django.db import models

class Stock(models.Model):
    ticker = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=255)
    sector = models.CharField(max_length=100, blank=True)
    industry = models.CharField(max_length=100, blank=True)
    current_price = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.ticker

class PriceHistory(models.Model):
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['stock', 'date']

    def __str__(self):
        return f"{self.stock.ticker} - {self.date}: ${self.price}"