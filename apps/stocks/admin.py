from django.contrib import admin
from .models import Stock, PriceHistory

admin.site.register(Stock)
admin.site.register(PriceHistory)