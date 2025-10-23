from django.urls import path
from . import views

urlpatterns = [
    path('', views.PortfolioListView.as_view(), name='portfolio-list'),
    path('<int:pk>/', views.PortfolioDetailView.as_view(), name='portfolio-detail'),
    path('<int:portfolio_id>/transactions', views.TransactionListView.as_view(), name='transaction-list'),
    path('<int:portfolio_id>/transactions/<int:transaction_id>/', views.TransactionDetailView.as_view(), name='transaction-detail'),
]