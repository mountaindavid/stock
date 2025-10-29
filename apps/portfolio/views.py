from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import Sum, Avg, Case, When, DecimalField
from decimal import Decimal
from .models import Portfolio, Transaction
from .serializers import PortfolioSerializer, TransactionSerializer, FIFOResultSerializer
from .services import FIFOCalculator
import logging

logger = logging.getLogger(__name__)

class PortfolioListCreateView(generics.ListCreateAPIView):
    serializer_class = PortfolioSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Portfolio.objects.filter(user=self.request.user).select_related('user')

    def perform_create(self, serializer):
        try:
            serializer.save(user=self.request.user)
        except IntegrityError as e:
            logger.warning(f"Portfolio creation failed for user {self.request.user.id}: {str(e)}")
            raise ValidationError("Portfolio with this name already exists for this user.")


class PortfolioDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PortfolioSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Portfolio.objects.filter(user=self.request.user).select_related('user')


class TransactionListCreateView(generics.ListCreateAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        portfolio = get_object_or_404(Portfolio, pk=self.kwargs['portfolio_id'], user=self.request.user)
        return Transaction.objects.filter(portfolio=portfolio)

    def get_serializer_context(self):
        """Add portfolio to serializer context for validation"""
        context = super().get_serializer_context()
        portfolio = get_object_or_404(Portfolio, pk=self.kwargs['portfolio_id'], user=self.request.user)
        context['portfolio'] = portfolio
        return context

    def perform_create(self, serializer):
        try:
            portfolio = get_object_or_404(Portfolio, pk=self.kwargs['portfolio_id'], user=self.request.user)
            serializer.save(portfolio=portfolio)
        except ValidationError as e:
            logger.warning(f"Transaction validation failed for portfolio {self.kwargs['portfolio_id']}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating transaction: {str(e)}")
            raise ValidationError("Failed to create transaction. Please check your data and try again.")


class TransactionDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        portfolio = get_object_or_404(Portfolio, pk=self.kwargs['portfolio_id'], user=self.request.user)
        return Transaction.objects.filter(portfolio=portfolio)

    def get_serializer_context(self):
        """Add portfolio to serializer context for validation"""
        context = super().get_serializer_context()
        portfolio = get_object_or_404(Portfolio, pk=self.kwargs['portfolio_id'], user=self.request.user)
        context['portfolio'] = portfolio
        return context


class PortfolioFIFOView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, portfolio_id):
        """Calculate FIFO profit/loss and remaining positions for portfolio"""
        try:
            portfolio = get_object_or_404(Portfolio, pk=portfolio_id, user=request.user)
            transactions = Transaction.objects.filter(portfolio=portfolio)
            
            if not transactions.exists():
                return Response(
                    {'message': 'No transactions found for this portfolio'}, 
                    status=status.HTTP_200_OK
                )
            
            calculator = FIFOCalculator()
            fifo_result = calculator.calculate_fifo(transactions)
            serializer = FIFOResultSerializer(fifo_result)
            
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error calculating FIFO for portfolio {portfolio_id}: {str(e)}")
            return Response(
                {'error': 'Failed to calculate FIFO. Please try again later.'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



class PortfolioStockDetailView(generics.GenericAPIView):
    """Get specific stock information from a specific portfolio"""
    permission_classes = [IsAuthenticated]

    def get(self, request, portfolio_id, stock_id):
        """Get stock information from a specific portfolio"""
        try:
            # Get the portfolio and ensure it belongs to the user
            portfolio = get_object_or_404(Portfolio, pk=portfolio_id, user=request.user)
            
            # Get the stock
            from apps.stocks.models import Stock
            stock = get_object_or_404(Stock, pk=stock_id)
            
            # Get all transactions for this stock in this specific portfolio
            transactions = Transaction.objects.filter(
                portfolio=portfolio,
                ticker=stock.ticker
            ).order_by('date')
            
            if not transactions.exists():
                return Response(
                    {'error': f'No holdings found for {stock.ticker} in portfolio "{portfolio.name}"'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Use FIFOCalculator to get holdings for this specific portfolio
            calculator = FIFOCalculator()
            holdings = calculator.calculate_holdings(transactions)
            
            # Get holding data for this ticker
            holding = holdings.get(stock.ticker, {})
            current_quantity = holding.get('quantity', Decimal('0'))
            average_price_per_share = holding.get('average_price_per_share')
            last_updated = holding.get('last_updated')
            
            # Calculate values
            market_price = stock.current_price
            total_price = current_quantity * average_price_per_share if average_price_per_share else None
            
            # Round prices to 2 decimal places
            if average_price_per_share:
                average_price_per_share = average_price_per_share.quantize(Decimal('0.01'))
            if total_price:
                total_price = total_price.quantize(Decimal('0.01'))
            if market_price:
                market_price = market_price.quantize(Decimal('0.01'))
            
            return Response({
                'id': stock.id,
                'ticker': stock.ticker,
                'name': stock.name,
                'portfolio_id': portfolio.id,
                'portfolio_name': portfolio.name,
                'current_price': market_price,  # Current market price
                'quantity': str(int(current_quantity)),  # Quantity in portfolio
                'total_price': total_price,  # Quantity * average purchase price
                'average_price_per_share': average_price_per_share,  # Average purchase price
                'last_updated': last_updated or stock.last_updated
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error fetching stock from portfolio: {str(e)}")
            return Response(
                {'error': 'Failed to fetch stock information. Please try again later.'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

