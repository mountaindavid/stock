from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .models import Portfolio, Transaction
from .serializers import PortfolioSerializer, TransactionSerializer
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


class TransactionListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, portfolio_id):
        """GET /api/portfolios/{portfolio_id}/transactions/ - list portfolio transactions"""
        portfolio = get_object_or_404(Portfolio, pk=portfolio_id, user=request.user)
        transactions = Transaction.objects.filter(portfolio=portfolio)
        serializer = TransactionSerializer(transactions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, portfolio_id):
        """POST /api/portfolios/{portfolio_id}/transactions/ - create transaction"""
        portfolio = get_object_or_404(Portfolio, pk=portfolio_id, user=request.user)
        serializer = TransactionSerializer(
            data=request.data, 
            context={'request': request, 'portfolio': portfolio}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TransactionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, portfolio_id, transaction_id):
        """GET /api/portfolios/{portfolio_id}/transactions/{transaction_id}/"""
        portfolio = get_object_or_404(Portfolio, pk=portfolio_id, user=request.user)
        transaction = get_object_or_404(Transaction, pk=transaction_id, portfolio=portfolio)
        serializer = TransactionSerializer(transaction)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, portfolio_id, transaction_id):
        """PUT /api/portfolios/{portfolio_id}/transactions/{transaction_id}/"""
        portfolio = get_object_or_404(Portfolio, pk=portfolio_id, user=request.user)
        transaction = get_object_or_404(Transaction, pk=transaction_id, portfolio=portfolio)
        serializer = TransactionSerializer(
            transaction, 
            data=request.data, 
            context={'request': request, 'portfolio': portfolio}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, portfolio_id, transaction_id):
        """PATCH /api/portfolios/{portfolio_id}/transactions/{transaction_id}/"""
        portfolio = get_object_or_404(Portfolio, pk=portfolio_id, user=request.user)
        transaction = get_object_or_404(Transaction, pk=transaction_id, portfolio=portfolio)
        serializer = TransactionSerializer(
            transaction, 
            data=request.data, 
            partial=True, 
            context={'request': request, 'portfolio': portfolio}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, portfolio_id, transaction_id):
        """DELETE /api/portfolios/{portfolio_id}/transactions/{transaction_id}/"""
        portfolio = get_object_or_404(Portfolio, pk=portfolio_id, user=request.user)
        transaction = get_object_or_404(Transaction, pk=transaction_id, portfolio=portfolio)
        transaction.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
