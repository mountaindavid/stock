from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .services import FinnhubService
import logging

logger = logging.getLogger(__name__)


class StockPriceView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, ticker):
        try:
            service = FinnhubService()
            price_data = service.get_stock_price(ticker)
            
            # Update Stock model with current price using atomic transaction
            from .models import Stock
            from django.db import transaction
            
            with transaction.atomic():
                stock, created = Stock.objects.get_or_create(
                    ticker=ticker.upper(),
                    defaults={
                        'name': ticker.upper(),
                        'current_price': price_data['price']
                    }
                )
                
                if not created:
                    # Update existing stock with new price
                    stock.current_price = price_data['price']
                    stock.save(update_fields=['current_price'])
            
            return Response(price_data, status=status.HTTP_200_OK)
        except ValueError as e:
            logger.warning(f"Invalid ticker request: {ticker} - {str(e)}")
            return Response(
                {'error': f'Invalid ticker: {str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Unexpected error fetching price for {ticker}: {str(e)}")
            return Response(
                {'error': 'Unable to fetch stock price. Please try again later.'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )