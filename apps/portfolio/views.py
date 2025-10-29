from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import Sum, Avg, Case, When, DecimalField
from decimal import Decimal
from .models import Portfolio, Transaction
from .serializers import PortfolioSerializer, TransactionSerializer, FIFOResultSerializer, PortfolioStockSerializer
from .services import calculate_fifo
import logging

logger = logging.getLogger(__name__)

class PortfolioListCreateView(generics.ListCreateAPIView):
    serializer_class = PortfolioSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Portfolio.objects.filter(user=self.request.user)

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
        return Portfolio.objects.filter(user=self.request.user)

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
            
            fifo_result = calculate_fifo(transactions)
            serializer = FIFOResultSerializer(fifo_result)
            
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error calculating FIFO for portfolio {portfolio_id}: {str(e)}")
            return Response(
                {'error': 'Failed to calculate FIFO. Please try again later.'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class PortfolioStocksView(generics.GenericAPIView):
    """Get all stocks in user's portfolios with calculated holdings"""
    permission_classes = [IsAuthenticated]
    serializer_class = PortfolioStockSerializer

    def get(self, request):
        """Get stocks with quantity, total_price, and average_price_per_share"""
        try:
            # Get all portfolios for the user
            portfolios = Portfolio.objects.filter(user=request.user)
            if not portfolios.exists():
                return Response([], status=status.HTTP_200_OK)
            
            # Get all transactions for user's portfolios
            transactions = Transaction.objects.filter(portfolio__in=portfolios)
            
            # Calculate holdings by ticker using FIFO logic
            holdings = {}
            
            # Group transactions by ticker and sort by date
            ticker_transactions = {}
            for transaction in transactions.order_by('date'):
                ticker = transaction.ticker
                if ticker not in ticker_transactions:
                    ticker_transactions[ticker] = []
                ticker_transactions[ticker].append(transaction)
            
            # Process each ticker's transactions
            for ticker, ticker_txns in ticker_transactions.items():
                # FIFO queue: list of (quantity, price) tuples
                fifo_queue = []
                current_quantity = Decimal('0')
                total_cost = Decimal('0')
                last_updated = None
                
                for transaction in ticker_txns:
                    if transaction.transaction_type == 'BUY':
                        # Add to FIFO queue
                        fifo_queue.append((transaction.quantity, transaction.price or Decimal('0')))
                        current_quantity += transaction.quantity
                        total_cost += transaction.quantity * (transaction.price or Decimal('0'))
                    else:  # SELL
                        sell_quantity = transaction.quantity
                        
                        # Validate that we have enough shares to sell
                        if sell_quantity > current_quantity:
                            logger.warning(f"Attempting to sell {sell_quantity} shares of {ticker} but only have {current_quantity}")
                            continue  # Skip this transaction
                        
                        # Process sell using FIFO
                        remaining_to_sell = sell_quantity
                        while remaining_to_sell > 0 and fifo_queue:
                            available_qty, buy_price = fifo_queue[0]
                            
                            if available_qty <= remaining_to_sell:
                                # Sell all shares from this buy
                                remaining_to_sell -= available_qty
                                total_cost -= available_qty * buy_price
                                current_quantity -= available_qty
                                fifo_queue.pop(0)
                            else:
                                # Sell partial shares from this buy
                                total_cost -= remaining_to_sell * buy_price
                                current_quantity -= remaining_to_sell
                                fifo_queue[0] = (available_qty - remaining_to_sell, buy_price)
                                remaining_to_sell = 0
                    
                    last_updated = transaction.date
                
                # Store the result
                if current_quantity > 0:
                    holdings[ticker] = {
                        'quantity': current_quantity,
                        'total_cost': total_cost,
                        'stock': ticker_txns[0].stock,
                        'last_updated': last_updated
                    }
            
            # Prepare response data
            portfolio_stocks = []
            for ticker, holding in holdings.items():
                stock = holding['stock']
                quantity = holding['quantity']
                total_cost = holding['total_cost']
                current_price = stock.current_price if stock else None
                
                # Calculate total_price (quantity * current_price)
                total_price = quantity * current_price if current_price else None
                
                # Calculate average_price_per_share (total_cost / quantity)
                average_price_per_share = total_cost / quantity if quantity > 0 else None
                
                # Round prices to 2 decimal places
                if current_price:
                    current_price = current_price.quantize(Decimal('0.01'))
                if total_price:
                    total_price = total_price.quantize(Decimal('0.01'))
                if average_price_per_share:
                    average_price_per_share = average_price_per_share.quantize(Decimal('0.01'))
                
                portfolio_stocks.append({
                    'id': stock.id if stock else None,
                    'ticker': ticker,
                    'name': stock.name if stock else ticker,
                    'quantity': int(quantity),  # Convert to whole number
                    'current_price': current_price,
                    'total_price': total_price,
                    'average_price_per_share': average_price_per_share,
                    'last_updated': holding['last_updated']
                })
            
            # Sort by ticker
            portfolio_stocks.sort(key=lambda x: x['ticker'])
            
            serializer = PortfolioStockSerializer(portfolio_stocks, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error fetching portfolio stocks: {str(e)}")
            return Response(
                {'error': 'Failed to fetch portfolio stocks. Please try again later.'}, 
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
            
            # Calculate holdings using FIFO logic for this specific portfolio
            fifo_queue = []
            current_quantity = Decimal('0')
            total_cost = Decimal('0')
            last_updated = None
            
            for transaction in transactions:
                if transaction.transaction_type == 'BUY':
                    # Add to FIFO queue
                    fifo_queue.append((transaction.quantity, transaction.price or Decimal('0')))
                    current_quantity += transaction.quantity
                    total_cost += transaction.quantity * (transaction.price or Decimal('0'))
                else:  # SELL
                    sell_quantity = transaction.quantity
                    
                    # Validate that we have enough shares to sell
                    if sell_quantity > current_quantity:
                        logger.warning(f"Attempting to sell {sell_quantity} shares of {stock.ticker} but only have {current_quantity}")
                        continue  # Skip this transaction
                    
                    # Process sell using FIFO
                    remaining_to_sell = sell_quantity
                    while remaining_to_sell > 0 and fifo_queue:
                        available_qty, buy_price = fifo_queue[0]
                        
                        if available_qty <= remaining_to_sell:
                            # Sell all shares from this buy
                            remaining_to_sell -= available_qty
                            total_cost -= available_qty * buy_price
                            current_quantity -= available_qty
                            fifo_queue.pop(0)
                        else:
                            # Sell partial shares from this buy
                            total_cost -= remaining_to_sell * buy_price
                            current_quantity -= remaining_to_sell
                            fifo_queue[0] = (available_qty - remaining_to_sell, buy_price)
                            remaining_to_sell = 0
                
                last_updated = transaction.date
            
            # Calculate values
            market_price = stock.current_price
            average_price_per_share = total_cost / current_quantity if current_quantity > 0 else None
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
                'current_price': market_price,  # Текущая рыночная цена
                'quantity': str(int(current_quantity)),  # Количество в портфеле
                'total_price': total_price,  # Количество * средняя цена покупки
                'average_price_per_share': average_price_per_share,  # Средняя цена покупки
                'last_updated': last_updated or stock.last_updated
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error fetching stock from portfolio: {str(e)}")
            return Response(
                {'error': 'Failed to fetch stock information. Please try again later.'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

