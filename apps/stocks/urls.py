from django.urls import path
from . import views

urlpatterns = [
    path('', views.StockListView.as_view(), name='stock-list'),
    path('<int:pk>/', views.StockDetailView.as_view(), name='stock-detail'),
    path('<int:stock_id>/price-history/', views.PriceHistoryListView.as_view(), name='price-history-list'),
    path('<int:stock_id>/price-history/<int:pk>/', views.PriceHistoryDetailView.as_view(), name='price-history-detail'),
]