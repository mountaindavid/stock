import finnhub
import logging
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class FinnhubService:
    def __init__(self):
        self.api_key = settings.FINNHUB_API_KEY
        self.client = finnhub.Client(api_key=self.api_key)
        self.cache_timeout = getattr(settings, 'STOCK_PRICE_CACHE_TIMEOUT', 1200)

    def get_stock_price(self, ticker):
        """
        Get current stock price via Finnhub API
        
        Args:
            ticker (str): Stock ticker (e.g., 'AAPL')
            
        Returns:
            dict: Dictionary with price and metadata
            
        Raises:
            ValueError: If ticker is invalid
            Exception: If API error
        """
        if not ticker or not isinstance(ticker, str):
            raise ValueError("Ticker must be a non-empty string")
        
        ticker = ticker.upper().strip()
        
        # Check cache
        cache_key = f"stock_price_{ticker}"
        cached_data = cache.get(cache_key)
        if cached_data:
            logger.info(f"Returning cached price for {ticker}")
            return cached_data
        
        try:
            # Get data from Finnhub
            quote_data = self.client.quote(ticker)
            
            # Check that data is received
            if not quote_data or 'c' not in quote_data:
                raise ValueError(f"No price data found for ticker: {ticker}")
            
            # Form the result
            result = {
                'ticker': ticker,
                'price': float(quote_data.get('c', 0)),  # current price
                'change': float(quote_data.get('d', 0)),  # change
                'percent_change': float(quote_data.get('dp', 0)),  # percent change
                'high': float(quote_data.get('h', 0)),  # high price
                'low': float(quote_data.get('l', 0)),  # low price
                'open': float(quote_data.get('o', 0)),  # open price
                'previous_close': float(quote_data.get('pc', 0)),  # previous close
                'timestamp': quote_data.get('t', 0),  # timestamp
                'source': 'finnhub.io'
            }
            
            # Cache the result
            cache.set(cache_key, result, self.cache_timeout)
            
            logger.info(f"Successfully retrieved price for {ticker}: ${result['price']}")
            return result
            
        except Exception as e:
            logger.error(f"Error retrieving price for {ticker}: {str(e)}")
            raise ValueError(f"Failed to retrieve price for {ticker}: {str(e)}")