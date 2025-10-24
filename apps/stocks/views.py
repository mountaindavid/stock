from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .models import Stock, PriceHistory
from .serializers import StockSerializer, PriceHistorySerializer
from rest_framework.response import Response
from rest_framework import status

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

class PriceHistoryListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, stock_id):
        """GET /api/stocks/{stock_id}/price-history/"""
        stock = get_object_or_404(Stock, pk=stock_id)
        price_history = PriceHistory.objects.filter(stock=stock)
        serializer = PriceHistorySerializer(price_history, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request, stock_id):
        """POST /api/stocks/{stock_id}/price-history/"""
        stock = get_object_or_404(Stock, pk=stock_id)
        serializer = PriceHistorySerializer(data=request.data, context={'request': request, 'stock': stock})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PriceHistoryDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, stock_id, pk):
        """GET /api/stocks/{stock_id}/price-history/{pk}/"""
        stock = get_object_or_404(Stock, pk=stock_id)
        price_history = get_object_or_404(PriceHistory, pk=pk, stock=stock)
        serializer = PriceHistorySerializer(price_history)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def put(self, request, stock_id, pk):        
        """PUT /api/stocks/{stock_id}/price-history/{pk}/"""
        stock = get_object_or_404(Stock, pk=stock_id)
        price_history = get_object_or_404(PriceHistory, pk=pk, stock=stock)
        serializer = PriceHistorySerializer(price_history, data=request.data, context={'request': request, 'stock': stock})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self, request, stock_id, pk):    
        """PATCH /api/stocks/{stock_id}/price-history/{pk}/"""
        stock = get_object_or_404(Stock, pk=stock_id)   
        price_history = get_object_or_404(PriceHistory, pk=pk, stock=stock)
        serializer = PriceHistorySerializer(price_history, data=request.data, context={'request': request, 'stock': stock}, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, stock_id, pk):
        """DELETE /api/stocks/{stock_id}/price-history/{pk}/"""
        stock = get_object_or_404(Stock, pk=stock_id)
        price_history = get_object_or_404(PriceHistory, pk=pk, stock=stock)
        price_history.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)