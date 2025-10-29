from decimal import Decimal
from collections import defaultdict
from typing import List, Dict, Any


def calculate_fifo(transactions) -> Dict[str, Any]:
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
        ticker_profit, positions = _calculate_ticker_fifo(ticker_txns)
        total_profit += ticker_profit
        all_positions.extend(positions)
    
    return {
        'total_profit': total_profit,
        'positions': all_positions
    }


def _calculate_ticker_fifo(transactions: List) -> tuple[Decimal, List[Dict]]:
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
