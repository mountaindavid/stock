from django.urls import path
from . import views

urlpatterns = [
    path('<str:ticker>/price/', views.StockPriceView.as_view(), name='stock-price'),
]