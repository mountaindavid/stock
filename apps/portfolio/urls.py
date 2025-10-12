from django.urls import path
from . import views

urlpatterns = [
    path('', views.PortfolioListView.as_view(), name='portfolio-list'),
    path('<int:pk>/', views.PortfolioDetailView.as_view(), name='portfolio-detail'),
]