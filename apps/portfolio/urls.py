from django.urls import path
from . import views

urlpatterns = [
    path('', views.PortfolioListCreateView.as_view(), name='portfolio-list'),
    path('<int:pk>/', views.PortfolioDetailView.as_view(), name='portfolio-detail'),
    path('<int:portfolio_id>/transactions/', views.TransactionListCreateView.as_view(), name='transaction-list'),
    path('<int:portfolio_id>/transactions/<int:pk>/', views.TransactionDetailView.as_view(), name='transaction-detail'),
    path('<int:portfolio_id>/fifo/', views.PortfolioFIFOView.as_view(), name='portfolio-fifo'),
    path('<int:portfolio_id>/stocks/<int:stock_id>/', views.PortfolioStockDetailView.as_view(), name='portfolio-stock-detail'),
]