from decimal import Decimal
from collections import defaultdict
from typing import List, Dict, Any, Tuple, Optional
from django.core.cache import cache
from django.db.models import QuerySet, Max
import logging

logger = logging.getLogger(__name__)


class FIFOCalculator:
    """
    Centralized FIFO calculation service with caching support.
    Handles all FIFO-related calculations for portfolio transactions.
    """
    
    def __init__(self, cache_timeout: int = 300):  # 5 minutes default
        self.cache_timeout = cache_timeout
    
    def calculate_fifo(self, transactions: QuerySet) -> Dict[str, Any]:
        """
        Calculate FIFO profit/loss and remaining positions for transactions.
        
        Args:
            transactions: QuerySet of Transaction objects
            
        Returns:
            Dict with total_profit and positions list
        """
        # Group transactions by ticker
        ticker_transactions = defaultdict(list)
        for transaction in transactions.order_by('date'):
            ticker_transactions[transaction.ticker].append(transaction)
        
        total_profit = Decimal('0')
        all_positions = []
        
        for ticker, ticker_txns in ticker_transactions.items():
            ticker_profit, positions = self._calculate_ticker_fifo(ticker_txns)
            total_profit += ticker_profit
            all_positions.extend(positions)
        
        return {
            'total_profit': total_profit,
            'positions': all_positions
        }
    
    def calculate_holdings(self, transactions: QuerySet) -> Dict[str, Dict[str, Any]]:
        """
        Calculate current holdings for all tickers using FIFO logic.
        
        Args:
            transactions: QuerySet of Transaction objects
            
        Returns:
            Dict with ticker as key and holding info as value
        """
        # Check cache first
        cache_key = self._get_holdings_cache_key(transactions)
        cached_result = cache.get(cache_key)
        if cached_result:
            logger.debug(f"Returning cached holdings for {len(transactions)} transactions")
            return cached_result
        
        # Group transactions by ticker and sort by date
        ticker_transactions = {}
        for transaction in transactions.order_by('date'):
            ticker = transaction.ticker
            if ticker not in ticker_transactions:
                ticker_transactions[ticker] = []
            ticker_transactions[ticker].append(transaction)
        
        holdings = {}
        
        # Process each ticker's transactions
        for ticker, ticker_txns in ticker_transactions.items():
            holding = self._calculate_ticker_holdings(ticker_txns)
            if holding['quantity'] > 0:
                holdings[ticker] = holding
        
        # Cache the result
        cache.set(cache_key, holdings, self.cache_timeout)
        logger.debug(f"Cached holdings for {len(transactions)} transactions")
        
        return holdings
    
    def calculate_ticker_holdings(self, transactions: List, ticker: str) -> Dict[str, Any]:
        """
        Calculate holdings for a specific ticker.
        
        Args:
            transactions: List of Transaction objects for the ticker
            ticker: Stock ticker symbol
            
        Returns:
            Dict with holding information
        """
        return self._calculate_ticker_holdings(transactions, ticker)
    
    def get_current_holdings(self, portfolio, ticker: str) -> Decimal:
        """
        Get current holdings quantity for a specific ticker in a portfolio.
        Used for SELL transaction validation.
        
        Args:
            portfolio: Portfolio instance
            ticker: Stock ticker symbol
            
        Returns:
            Current quantity held
        """
        from .models import Transaction
        
        transactions = Transaction.objects.filter(
            portfolio=portfolio,
            ticker=ticker
        ).order_by('date')
        
        holdings = self.calculate_holdings(transactions)
        return holdings.get(ticker, {}).get('quantity', Decimal('0'))
    
    def _calculate_ticker_fifo(self, transactions: List) -> Tuple[Decimal, List[Dict]]:
        """
        Calculate FIFO for a single ticker.
        
        Returns:
            Tuple of (total_profit, remaining_positions)
        """
        buy_queue = []  # List of (quantity, price, date) tuples
        total_profit = Decimal('0')
        
        for transaction in transactions:
            if transaction.transaction_type == 'BUY':
                buy_queue.append((
                    transaction.quantity,
                    transaction.price,
                    transaction.date
                ))
            elif transaction.transaction_type == 'SELL':
                remaining_sell_qty = transaction.quantity
                
                while remaining_sell_qty > 0 and buy_queue:
                    buy_qty, buy_price, buy_date = buy_queue[0]
                    
                    if buy_qty <= remaining_sell_qty:
                        # This buy is completely consumed
                        profit = (transaction.price - buy_price) * buy_qty
                        total_profit += profit
                        remaining_sell_qty -= buy_qty
                        buy_queue.pop(0)
                    else:
                        # Partial consumption of this buy
                        profit = (transaction.price - buy_price) * remaining_sell_qty
                        total_profit += profit
                        buy_queue[0] = (
                            buy_qty - remaining_sell_qty,
                            buy_price,
                            buy_date
                        )
                        remaining_sell_qty = 0
        
        # Convert remaining buy_queue to positions
        positions = []
        for qty, price, date in buy_queue:
            if qty > 0:  # Only include positions with remaining quantity
                positions.append({
                    'ticker': transactions[0].ticker,
                    'remaining_qty': qty,
                    'buy_price': price
                })
        
        return total_profit, positions
    
    def _calculate_ticker_holdings(self, transactions: List, ticker: Optional[str] = None) -> Dict[str, Any]:
        """
        Calculate holdings for a single ticker using FIFO logic.
        
        Args:
            transactions: List of Transaction objects
            ticker: Optional ticker for logging
            
        Returns:
            Dict with holding information
        """
        # FIFO queue: list of (quantity, price) tuples
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
                    logger.warning(f"Attempting to sell {sell_quantity} shares of {ticker or 'unknown'} but only have {current_quantity}")
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
        
        # Calculate average price per share
        average_price_per_share = total_cost / current_quantity if current_quantity > 0 else None
        
        # Round prices to 2 decimal places
        if average_price_per_share:
            average_price_per_share = average_price_per_share.quantize(Decimal('0.01'))
        
        return {
            'quantity': current_quantity,
            'total_cost': total_cost,
            'average_price_per_share': average_price_per_share,
            'stock': transactions[0].stock if transactions else None,
            'last_updated': last_updated
        }
    
    def _get_holdings_cache_key(self, transactions: QuerySet) -> str:
        """
        Generate cache key for holdings calculation.
        
        Args:
            transactions: QuerySet of Transaction objects
            
        Returns:
            Cache key string
        """
        # Create a hash based on transaction IDs and last update time
        transaction_ids = list(transactions.values_list('id', flat=True))
        last_update = transactions.aggregate(
            last_update=Max('date')
        )['last_update']
        
        import hashlib
        key_data = f"{sorted(transaction_ids)}_{last_update}"
        return f"fifo_holdings_{hashlib.md5(key_data.encode()).hexdigest()[:16]}"


# Backward compatibility - keep the old function
def calculate_fifo(transactions) -> Dict[str, Any]:
    """
    Legacy function for backward compatibility.
    Use FIFOCalculator.calculate_fifo() instead.
    """
    calculator = FIFOCalculator()
    return calculator.calculate_fifo(transactions)
