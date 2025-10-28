from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .models import Stock
from .serializers import StockSerializer
from .services import FinnhubService
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)

class StockListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """GET /api/stocks/ - list all stocks"""
        stocks = Stock.objects.all()
        serializer = StockSerializer(stocks, many = True)
        return Response(serializer.data, status = status.HTTP_200_OK)

    def post(self, request):
        """POST /api/stocks/ - create new stock"""
        serializer = StockSerializer(data = request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status = status.HTTP_201_CREATED)
        return Response(serializer.errors, status = status.HTTP_400_BAD_REQUEST)
    
class StockDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        """GET /api/stocks/{pk}/ - get specific stock"""
        stock = get_object_or_404(Stock, pk=pk)
        serializer = StockSerializer(stock)
        return Response(serializer.data, status = status.HTTP_200_OK)
    
    def put(self, request, pk):
        """PUT /api/stocks/{pk}/ - full update stock"""
        stock = get_object_or_404(Stock, pk=pk)
        serializer = StockSerializer(stock, data = request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status = status.HTTP_200_OK)
        return Response(serializer.errors, status = status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        """PATCH /api/stocks/{pk}/ - partial update stock"""
        stock = get_object_or_404(Stock, pk=pk)
        serializer = StockSerializer(stock, data = request.data, partial = True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status = status.HTTP_200_OK)
        return Response(serializer.errors, status = status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        """DELETE /api/stocks/{pk}/ - delete stock"""
        stock = get_object_or_404(Stock, pk=pk) 
        stock.delete()
        return Response(status = status.HTTP_204_NO_CONTENT)



class StockPriceView(APIView):
    """
    Эндпоинт для получения текущей цены акции через Polygon.io API
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, ticker):
        """
        GET /api/stocks/{ticker}/price/ - получить текущую цену акции
        
        Args:
            ticker (str): Тикер акции (например, AAPL)
        """
        try:
            finnhub_service = FinnhubService()
            price_data = finnhub_service.get_stock_price(ticker)
            
            return Response({
                'success': True,
                'data': price_data,
                'message': f'Price retrieved successfully for {ticker}'
            }, status=status.HTTP_200_OK)
            
        except ValueError as e:
            logger.warning(f"Invalid ticker {ticker}: {str(e)}")
            return Response({
                'success': False,
                'error': 'Invalid ticker',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Error retrieving price for {ticker}: {str(e)}")
            return Response({
                'success': False,
                'error': 'API Error',
                'message': f'Failed to retrieve price for {ticker}. Please try again later.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)