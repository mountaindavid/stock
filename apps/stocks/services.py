import yfinance as yf
from django.core.cache import cache
from django.conf import settings
from datetime import datetime, date, timedelta
from apps.stocks.models import Stock
import logging

logger = logging.getLogger(__name__)

class YahooFinanceService:
    """Service for fetching stock data from Yahoo Finance API"""

    def __init__(self):
        self.cache_timeout = getattr(settings, 'STOCK_PRICE_CACHE_TIMEOUT', 1200)

    def get_stock_info(self, ticker):
        """Get stock information from Yahoo Finance API"""
        cache_key = f'stock_info_{ticker}'
        stock_info = cache.get(cache_key)
        if stock_info is None:
            stock_info = yf.Ticker(ticker).info
            cache.set(cache_key, stock_info, self.cache_timeout)
        return stock_info
    
    def get_stock_price(self, ticker):
        """Get stock price from Yahoo Finance API"""
        cache_key = f'stock_price_{ticker}'
        stock_price = cache.get(cache_key)
        if stock_price is None:
            try:
                history = yf.Ticker(ticker).history(period='1d')
                if not history.empty:
                    stock_price = float(history['Close'].iloc[0])
                else:
                    return None
            except Exception as e:
                logger.error(f"Error getting stock price for {ticker}: {e}")
                return None
            cache.set(cache_key, stock_price, self.cache_timeout)
        return stock_price
    
    def get_historical_price(self, ticker, target_date):
        """Get stock price for a specific date"""
        cache_key = f"historical_price_{ticker}_{target_date}"
        cached_price = cache.get(cache_key)
        
        if cached_price:
            return cached_price
        
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(start=target_date, end=target_date + timedelta(days=1))
            
            if not hist.empty:
                price = float(hist['Close'].iloc[-1])
                cache.set(cache_key, price, 86400)  # 24 hours
                return price
        except Exception as e:
            logger.error(f"Error fetching historical price for {ticker} on {target_date}: {e}")
        
        return None

    def create_or_update_stock(self, ticker):
        """Create or update stock using Yahoo Finance data"""        
        stock_info = self.get_stock_info(ticker)
        
        stock, created = Stock.objects.get_or_create(
            ticker=ticker.upper(),
            defaults={
                'name': stock_info.get('longName', f'Company {ticker.upper()}'),
                'sector': stock_info.get('sector', ''),
                'industry': stock_info.get('industry', ''),
                'current_price': stock_info.get('currentPrice') or stock_info.get('regularMarketPrice')
            }
        )
        
        if not created:
            # Update existing stock
            stock.name = stock_info.get('longName', stock.name)
            stock.sector = stock_info.get('sector', stock.sector)
            stock.industry = stock_info.get('industry', stock.industry)
            if stock_info.get('currentPrice'):
                stock.current_price = stock_info.get('currentPrice')
            stock.save()
        
        return stock