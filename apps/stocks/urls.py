from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'', views.StockViewSet)
router.register(r'price-history', views.PriceHistoryViewSet)

urlpatterns = [
    path('', include(router.urls)),
]