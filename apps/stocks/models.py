from django.db import models

class Stock(models.Model):
    ticker = models.CharField(max_length=10, unique=True, db_index=True)
    name = models.CharField(max_length=255, db_index=True)
    current_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True, db_index=True)

    def __str__(self):
        return f"{self.ticker} - {self.name}"

    class Meta:
        ordering = ['ticker']
        indexes = [
            models.Index(fields=['ticker']),
            models.Index(fields=['current_price']),
        ]

