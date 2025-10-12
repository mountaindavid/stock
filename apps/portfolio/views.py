from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .models import Portfolio
from .serializers import PortfolioSerializer
from rest_framework.response import Response
from rest_framework import status

class PortfolioListView(APIView): 
    permission_classes = [IsAuthenticated]

    def get(self,request):
        """GET /api/portfolios/ - list all portfolios"""
        portfolios = Portfolio.objects.filter(user = request.user)  
        serializer = PortfolioSerializer(portfolios, many = True)
        return Response(serializer.data, status = status.HTTP_200_OK)

    def post(self, request):
        """POST /api/portfolios/ - create new portfolio"""
        serializer = PortfolioSerializer(data = request.data, context = {'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status = status.HTTP_201_CREATED)
        return Response(serializer.errors, status = status.HTTP_400_BAD_REQUEST)
        
class PortfolioDetailView(APIView):
    """GET /api/portfolios/1/ - get specific portfolio"""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        """GET /api/portfolios/1/ - get specific portfolio"""
        portfolio = get_object_or_404(Portfolio, pk=pk, user=request.user)
        serializer = PortfolioSerializer(portfolio)
        return Response(serializer.data, status = status.HTTP_200_OK)

    def put(self, request, pk):
        """PUT /api/portfolios/1/ - full update portfolio"""
        portfolio = get_object_or_404(Portfolio, pk=pk, user=request.user)
        serializer = PortfolioSerializer(portfolio, data = request.data, context = {'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status = status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        """PATCH /api/portfolios/1/ - partial update portfolio"""
        portfolio = get_object_or_404(Portfolio, pk=pk, user=request.user)
        serializer = PortfolioSerializer(portfolio, data = request.data, partial = True, context = {'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status = status.HTTP_200_OK)
        return Response(serializer.errors, status = status.HTTP_400_BAD_REQUEST)


    def delete(self, request, pk):
        """DELETE /api/portfolios/1/ - delete portfolio"""
        portfolio = get_object_or_404(Portfolio, pk=pk, user=request.user)
        portfolio.delete()
        return Response(status = status.HTTP_204_NO_CONTENT)