import os
import requests
import logging
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv
from .cache_service import CacheTTL



load_dotenv()

logger = logging.getLogger(__name__)

class StockService:
    """Enhanced stock service with Redis caching"""
    
    def __init__(self, api_key: str, cache_service=None):
        self.api_key = api_key
        self.base_url = 'https://financialmodelingprep.com/api/v3'
        self.cache_service = cache_service
        self.session = requests.Session()
        
        # Set default headers
        self.session.headers.update({
            'User-Agent': 'StockAnalyzer/1.0'
        })
        
        # Track API usage
        self.api_call_count = 0
        self.cache_hit_count = 0
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Any:
        """Make HTTP request to FMP API"""
        params = params or {}
        params['apikey'] = self.api_key
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            self.api_call_count += 1
            logger.info(f"🌐 FMP API Call #{self.api_call_count}: {endpoint}")
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if isinstance(data, dict) and data.get('error'):
                raise Exception(f"FMP API Error: {data['error']}")
            
            return data
            
        except requests.exceptions.Timeout:
            raise Exception("FMP API request timed out")
        except requests.exceptions.ConnectionError:
            raise Exception("Failed to connect to FMP API")
        except requests.exceptions.HTTPError as e:
            raise Exception(f"FMP API HTTP error: {e}")
        except Exception as e:
            logger.error(f"FMP API error: {e}")
            raise
    
    def fetch_stock_data(self, symbol: str) -> Dict:
        """Enhanced version of your original fetch_stock_data with caching"""
        symbol = symbol.upper().strip()
        cache_key = f"quote:{symbol}"
        
        # Try cache first
        if self.cache_service:
            cached_result = self.cache_service.get('stock_quotes', cache_key)
            if cached_result is not None:
                self.cache_hit_count += 1
                logger.debug(f"🎯 Cache hit for quote: {symbol}")
                print(f"🎯 Cache hit for quote: {symbol}")
                
                return cached_result
        
        # Make API call (your original implementation)
        result = self._make_request('/quote', {'symbol': symbol})
        print("fetching quote . . . ")
        # Handle response format
        quote_data = result[0] if isinstance(result, list) and result else result
        
        # Cache result
        if self.cache_service:
            self.cache_service.set('stock_quotes', cache_key, quote_data, CacheTTL.REAL_TIME_QUOTES)
        print(quote_data)
        return quote_data
    
    def fetch_historical_data(self, symbol: str, from_date: str = None, to_date: str = None) -> Dict:
        """Enhanced version of your original fetch_historical_data with caching"""
        symbol = symbol.upper().strip()
        
        cache_params = {'symbol': symbol}
        if from_date:
            cache_params['from'] = from_date
        if to_date:
            cache_params['to'] = to_date
        
        cache_key = f"historical:{symbol}"
        
        # Try cache first
        if self.cache_service:
            cached_result = self.cache_service.get('historical_data', cache_key, cache_params)
            if cached_result is not None:
                self.cache_hit_count += 1
                logger.debug(f"🎯 Cache hit for historical: {symbol}")
                return cached_result
        
        # Build API params
        api_params = {'symbol': symbol, 'serietype': 'line'}
        if from_date:
            api_params['from'] = from_date
        if to_date:
            api_params['to'] = to_date
        
        
        result = self._make_request('/historical-price-eod/full', api_params)
        
        # Cache result
        if self.cache_service:
            self.cache_service.set('historical_data', cache_key, result, 
                                 CacheTTL.HISTORICAL_DATA, cache_params)
        
        return result
    
    def fetch_search_query(self, keyword: str) -> List[Dict]:
        """Enhanced version of your original fetch_search_query with caching"""
        if not keyword or len(keyword.strip()) < 1:
            return []
        
        cache_key = f"search:{keyword.strip().lower()}"
        
        # Try cache first
        if self.cache_service:
            cached_result = self.cache_service.get('search_results', cache_key)
            if cached_result is not None:
                self.cache_hit_count += 1
                logger.debug(f"🎯 Cache hit for search: {keyword}")
                return cached_result
        
        # Make API call (your original implementation)
        result = self._make_request('/search', {'query': keyword, 'limit': 10})
        
        # Cache result
        if self.cache_service:
            self.cache_service.set('search_results', cache_key, result, CacheTTL.SEARCH_RESULTS)
        
        return result if isinstance(result, list) else []
    
    # New enhanced methods
    def get_company_profile(self, symbol: str) -> Dict:
        """Get company profile with caching"""
        symbol = symbol.upper().strip()
        cache_key = f"profile:{symbol}"
        
        # Try cache first
        if self.cache_service:
            cached_result = self.cache_service.get('company_profiles', cache_key)
            if cached_result is not None:
                self.cache_hit_count += 1
                return cached_result
        
        # Make API call
        result = self._make_request('/profile', {'symbol': symbol})
        
        # Handle response format
        profile_data = result[0] if isinstance(result, list) and result else result
        
        # Cache result
        if self.cache_service:
            self.cache_service.set('company_profiles', cache_key, profile_data, CacheTTL.COMPANY_PROFILES)
        
        return profile_data
    
    def get_financial_statements(self, symbol: str, statement_type: str = 'income-statement', 
                                period: str = 'annual', limit: int = 5) -> List[Dict]:
        """Get financial statements with caching"""
        symbol = symbol.upper().strip()
        
        cache_params = {
            'symbol': symbol,
            'statement_type': statement_type,
            'period': period,
            'limit': limit
        }
        cache_key = f"{statement_type}:{symbol}"
        
        # Try cache first
        if self.cache_service:
            cached_result = self.cache_service.get('financial_statements', cache_key, cache_params)
            if cached_result is not None:
                self.cache_hit_count += 1
                return cached_result
        
        # Make API call
        result = self._make_request(f'/{statement_type}', {
            'symbol': symbol,
            'period': period,
            'limit': limit
        })
        
        # Cache result
        if self.cache_service:
            self.cache_service.set('financial_statements', cache_key, result, 
                                 CacheTTL.FINANCIAL_STATEMENTS, cache_params)
        
        return result if isinstance(result, list) else []
    
    def get_batch_quotes(self, symbols: List[str]) -> List[Dict]:
        """Get multiple quotes efficiently with caching"""
        symbols = [s.upper().strip() for s in symbols if s.strip()]
        
        if not symbols:
            return []
        
        # Check cache for individual symbols
        cached_quotes = []
        uncached_symbols = []
        
        if self.cache_service:
            for symbol in symbols:
                cache_key = f"quote:{symbol}"
                cached_quote = self.cache_service.get('stock_quotes', cache_key)
                if cached_quote:
                    cached_quotes.append(cached_quote)
                    self.cache_hit_count += 1
                else:
                    uncached_symbols.append(symbol)
        else:
            uncached_symbols = symbols
        
        # Fetch uncached symbols
        if uncached_symbols:
            symbol_list = ','.join(uncached_symbols)
            result = self._make_request('/quote', {'symbol': symbol_list})
            
            # Cache individual results
            if self.cache_service and isinstance(result, list):
                for quote in result:
                    if quote.get('symbol'):
                        cache_key = f"quote:{quote['symbol']}"
                        self.cache_service.set('stock_quotes', cache_key, quote, CacheTTL.REAL_TIME_QUOTES)
            
            cached_quotes.extend(result if isinstance(result, list) else [result])
        
        return cached_quotes
    
    def get_market_news(self, limit: int = 50, tickers: str = None) -> List[Dict]:
        """Get market news with caching"""
        cache_params = {'limit': limit}
        if tickers:
            cache_params['tickers'] = tickers
        
        cache_key = "market_news"
        
        # Try cache first
        if self.cache_service:
            cached_result = self.cache_service.get('market_news', cache_key, cache_params)
            if cached_result is not None:
                self.cache_hit_count += 1
                return cached_result
        
        # Build API params
        api_params = {'limit': limit}
        if tickers:
            api_params['tickers'] = tickers
        
        # Make API call
        result = self._make_request('/stock_news', api_params)
        
        # Cache result
        if self.cache_service:
            self.cache_service.set('market_news', cache_key, result, 
                                 CacheTTL.MARKET_NEWS, cache_params)
        
        return result if isinstance(result, list) else []
    
    def get_stats(self) -> Dict:
        """Get service statistics"""
        total_requests = self.api_call_count + self.cache_hit_count
        cache_hit_rate = (self.cache_hit_count / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'api_calls': self.api_call_count,
            'cache_hits': self.cache_hit_count,
            'total_requests': total_requests,
            'cache_hit_rate': round(cache_hit_rate, 2),
            'cache_service_stats': self.cache_service.get_stats() if self.cache_service else None
        }