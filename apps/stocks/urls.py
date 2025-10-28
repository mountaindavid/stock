from django.urls import path
from . import views

urlpatterns = [
    path('', views.StockListView.as_view(), name='stock-list'),
    path('<int:pk>/', views.StockDetailView.as_view(), name='stock-detail'),
    path('<str:ticker>/price/', views.StockPriceView.as_view(), name='stock-price'),
]