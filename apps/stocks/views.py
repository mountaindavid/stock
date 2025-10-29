from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ValidationError
from django.db.models import Sum, Avg, Case, When, DecimalField
from decimal import Decimal
from .models import Stock
from .serializers import StockSerializer
from .services import FinnhubService
from apps.portfolio.models import Transaction, Portfolio
import logging

logger = logging.getLogger(__name__)

class StockListCreateView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get all stocks with portfolio information"""
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
                
                # Calculate average_price_per_share (total_cost / quantity)
                average_price_per_share = total_cost / quantity if quantity > 0 else None
                total_price = quantity * average_price_per_share if average_price_per_share else None
                
                # Round prices to 2 decimal places
                if average_price_per_share:
                    average_price_per_share = average_price_per_share.quantize(Decimal('0.01'))
                if total_price:
                    total_price = total_price.quantize(Decimal('0.01'))
                
                portfolio_stocks.append({
                    'id': stock.id if stock else None,
                    'ticker': ticker,
                    'name': stock.name if stock else ticker,
                    'current_price': average_price_per_share,  # Средняя цена покупки
                    'quantity': str(int(quantity)),  # Convert to whole number
                    'total_price': total_price,
                    'average_price_per_share': average_price_per_share,
                    'last_updated': holding['last_updated']
                })
            
            # Sort by ticker
            portfolio_stocks.sort(key=lambda x: x['ticker'])
            
            return Response(portfolio_stocks, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error fetching portfolio stocks: {str(e)}")
            return Response(
                {'error': 'Failed to fetch portfolio stocks. Please try again later.'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class StockDetailView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        """Get portfolio information for a specific stock across all user's portfolios"""
        try:
            # Get the stock
            stock = Stock.objects.get(pk=pk)
            
            # Get all portfolios for the user
            portfolios = Portfolio.objects.filter(user=request.user)
            if not portfolios.exists():
                return Response(
                    {'error': 'No portfolios found for this user'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Get all transactions for this stock in user's portfolios
            transactions = Transaction.objects.filter(
                portfolio__in=portfolios,
                ticker=stock.ticker
            ).order_by('date')
            
            if not transactions.exists():
                return Response(
                    {'error': f'No holdings found for {stock.ticker} in your portfolios'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Calculate holdings using FIFO logic
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
            
            return Response({
                'id': stock.id,
                'ticker': stock.ticker,
                'name': stock.name,
                'current_price': average_price_per_share,  # Средняя цена покупки
                'quantity': str(int(current_quantity)),  # Convert to whole number
                'total_price': total_price,  # Количество * средняя цена покупки
                'average_price_per_share': average_price_per_share,
                'last_updated': last_updated or stock.last_updated
            }, status=status.HTTP_200_OK)
            
        except Stock.DoesNotExist:
            return Response(
                {'error': 'Stock not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error fetching stock portfolio info: {str(e)}")
            return Response(
                {'error': 'Failed to fetch stock information. Please try again later.'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def delete(self, request, pk):
        """Delete all holdings of a specific stock from user's portfolios"""
        try:
            # Get the stock
            stock = Stock.objects.get(pk=pk)
            
            # Get all portfolios for the user
            portfolios = Portfolio.objects.filter(user=request.user)
            if not portfolios.exists():
                return Response(
                    {'message': 'No portfolios found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Get all transactions for this stock in user's portfolios
            transactions = Transaction.objects.filter(
                portfolio__in=portfolios,
                ticker=stock.ticker
            )
            
            if not transactions.exists():
                return Response(
                    {'message': f'No holdings found for {stock.ticker}'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Delete all transactions for this stock
            deleted_count = transactions.count()
            transactions.delete()
            
            return Response(
                {'message': f'Successfully deleted {deleted_count} transactions for {stock.ticker}'}, 
                status=status.HTTP_200_OK
            )
            
        except Stock.DoesNotExist:
            return Response(
                {'error': 'Stock not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error deleting stock holdings: {str(e)}")
            return Response(
                {'error': 'Failed to delete stock holdings. Please try again later.'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class StockPriceView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, ticker):
        try:
            service = FinnhubService()
            price_data = service.get_stock_price(ticker)
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