"""
Abstract base class for data providers.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import pandas as pd
from dataclasses import dataclass

@dataclass
class DataRequest:
    """Data request specification"""
    symbols: List[str]
    start_date: datetime
    end_date: datetime
    timeframe: str = '1d'  # 1m, 5m, 1h, 1d, etc.
    include_extended_hours: bool = False
    adjust_for_splits: bool = True
    adjust_for_dividends: bool = True

@dataclass
class DataResponse:
    """Data response with metadata"""
    data: pd.DataFrame
    symbols: List[str]
    start_date: datetime
    end_date: datetime
    timeframe: str
    source: str
    missing_symbols: List[str] = None
    errors: List[str] = None
    metadata: Dict = None

class DataProvider(ABC):
    """Abstract base class for market data providers"""
    
    def __init__(self, name: str, config: Dict = None):
        self.name = name
        self.config = config or {}
        self.rate_limit = self.config.get('rate_limit', 60)  # requests per minute
        self.api_key = self.config.get('api_key')
        self.is_active = True
        self._last_request_time = None
        self._request_count = 0
        
    @abstractmethod
    def get_historical_data(self, request: DataRequest) -> DataResponse:
        """Get historical OHLCV data"""
        pass
    
    @abstractmethod
    def get_real_time_quote(self, symbols: List[str]) -> Dict[str, Dict]:
        """Get real-time quotes"""
        pass
    
    @abstractmethod
    def search_symbols(self, query: str, limit: int = 10) -> List[Dict]:
        """Search for symbols"""
        pass
    
    @abstractmethod
    def get_asset_info(self, symbols: List[str]) -> Dict[str, Dict]:
        """Get asset information (name, exchange, sector, etc.)"""
        pass
    
    @abstractmethod
    def get_supported_timeframes(self) -> List[str]:
        """Get supported timeframes"""
        pass
    
    @abstractmethod
    def get_supported_asset_types(self) -> List[str]:
        """Get supported asset types"""
        pass
    
    def validate_symbols(self, symbols: List[str]) -> Tuple[List[str], List[str]]:
        """Validate symbols and return valid/invalid lists"""
        # Basic validation - override in specific providers
        valid_symbols = [s.upper().strip() for s in symbols if s and len(s) <= 10]
        invalid_symbols = [s for s in symbols if s not in valid_symbols]
        return valid_symbols, invalid_symbols
    
    def validate_timeframe(self, timeframe: str) -> bool:
        """Validate timeframe"""
        return timeframe in self.get_supported_timeframes()
    
    def validate_date_range(self, start_date: datetime, end_date: datetime) -> bool:
        """Validate date range"""
        if start_date >= end_date:
            return False
        if end_date > datetime.now():
            return False
        return True
    
    def _check_rate_limit(self):
        """Check and enforce rate limits"""
        now = datetime.now()
        if self._last_request_time:
            time_diff = (now - self._last_request_time).total_seconds()
            if time_diff < 60:  # Within the same minute
                if self._request_count >= self.rate_limit:
                    sleep_time = 60 - time_diff
                    raise Exception(f"Rate limit exceeded. Wait {sleep_time:.1f} seconds")
            else:
                self._request_count = 0
        
        self._last_request_time = now
        self._request_count += 1
    
    def _standardize_dataframe(self, df: pd.DataFrame, symbol: str = None) -> pd.DataFrame:
        """Standardize dataframe format"""
        # Ensure standard column names
        column_mapping = {
            'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close',
            'Volume': 'volume', 'Adj Close': 'adj_close', 'Adjusted_Close': 'adj_close'
        }
        
        df = df.rename(columns=column_mapping)
        
        # Ensure required columns exist
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"Missing required column: {col}")
        
        # Add adj_close if missing
        if 'adj_close' not in df.columns:
            df['adj_close'] = df['close']
        
        # Add symbol column if provided
        if symbol:
            df['symbol'] = symbol
        
        # Ensure datetime index
        if not isinstance(df.index, pd.DatetimeIndex):
            if 'date' in df.columns:
                df = df.set_index('date')
            elif 'timestamp' in df.columns:
                df = df.set_index('timestamp')
        
        # Sort by date
        df = df.sort_index()
        
        return df
    
    def get_data_quality_score(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate data quality metrics"""
        if df.empty:
            return {'completeness': 0, 'accuracy': 0, 'consistency': 0, 'overall': 0}
        
        # Completeness: % of non-null values
        completeness = (1 - df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100
        
        # Accuracy: % of valid OHLC relationships
        valid_ohlc = (
            (df['high'] >= df['low']) & 
            (df['high'] >= df['open']) & 
            (df['high'] >= df['close']) &
            (df['low'] <= df['open']) & 
            (df['low'] <= df['close'])
        ).sum()
        accuracy = (valid_ohlc / len(df)) * 100 if len(df) > 0 else 0
        
        # Consistency: % of bars with volume > 0
        consistency = (df['volume'] > 0).sum() / len(df) * 100 if len(df) > 0 else 0
        
        # Overall score
        overall = (completeness + accuracy + consistency) / 3
        
        return {
            'completeness': completeness,
            'accuracy': accuracy,
            'consistency': consistency,
            'overall': overall
        }

class DataProviderRegistry:
    """Registry for managing multiple data providers"""
    
    def __init__(self):
        self.providers: Dict[str, DataProvider] = {}
        self.default_provider = None
    
    def register_provider(self, provider: DataProvider, is_default: bool = False):
        """Register a data provider"""
        self.providers[provider.name] = provider
        if is_default or not self.default_provider:
            self.default_provider = provider.name
    
    def get_provider(self, name: str = None) -> DataProvider:
        """Get a specific provider or default"""
        provider_name = name or self.default_provider
        if provider_name not in self.providers:
            raise ValueError(f"Provider '{provider_name}' not found")
        return self.providers[provider_name]
    
    def get_available_providers(self) -> List[str]:
        """Get list of available providers"""
        return list(self.providers.keys())
    
    def get_best_provider_for_symbols(self, symbols: List[str]) -> str:
        """Get the best provider for given symbols"""
        # Simple implementation - can be enhanced with provider capabilities
        for provider_name, provider in self.providers.items():
            if provider.is_active:
                return provider_name
        return self.default_provider

# Concrete implementation using StockService
class StockServiceDataProvider(DataProvider):
    """Data provider implementation using our existing StockService"""
    
    def __init__(self, stock_service):
        super().__init__("stock_service")
        self.stock_service = stock_service
    
    def get_historical_data(self, request: DataRequest) -> DataResponse:
        """Get historical data using StockService"""
        import pandas as pd
        
        all_data = []
        missing_symbols = []
        errors = []
        
        for symbol in request.symbols:
            try:
                # Use StockService to fetch historical data
                start_str = request.start_date.strftime('%Y-%m-%d')
                end_str = request.end_date.strftime('%Y-%m-%d')
                
                data = self.stock_service.fetch_historical_data(symbol, start_str, end_str)
                
                if 'historical' in data and data['historical']:
                    # Convert to DataFrame
                    df_data = []
                    for record in data['historical']:
                        df_data.append({
                            'date': record['date'],
                            'open': record['open'],
                            'high': record['high'],
                            'low': record['low'],
                            'close': record['close'],
                            'volume': record['volume'],
                            'symbol': symbol
                        })
                    
                    if df_data:
                        df = pd.DataFrame(df_data)
                        df['date'] = pd.to_datetime(df['date'])
                        df.set_index('date', inplace=True)
                        df.sort_index(inplace=True)
                        all_data.append(df)
                    else:
                        missing_symbols.append(symbol)
                else:
                    missing_symbols.append(symbol)
                    
            except Exception as e:
                errors.append(f"Error fetching data for {symbol}: {str(e)}")
                missing_symbols.append(symbol)
        
        # Combine all data
        if all_data:
            combined_df = pd.concat(all_data)
        else:
            combined_df = pd.DataFrame()
        
        return DataResponse(
            data=combined_df,
            symbols=request.symbols,
            start_date=request.start_date,
            end_date=request.end_date,
            timeframe=request.timeframe,
            source="stock_service",
            missing_symbols=missing_symbols,
            errors=errors
        )
    
    def get_real_time_quote(self, symbols: List[str]) -> Dict[str, Dict]:
        """Get real-time quotes"""
        quotes = {}
        for symbol in symbols:
            try:
                quote_data = self.stock_service.fetch_stock_data(symbol)
                quotes[symbol] = quote_data
            except:
                pass
        return quotes
    
    def search_symbols(self, query: str, limit: int = 10) -> List[Dict]:
        """Search symbols"""
        try:
            return self.stock_service.fetch_search_query(query)[:limit]
        except:
            return []
    
    def get_asset_info(self, symbols: List[str]) -> Dict[str, Dict]:
        """Get asset information"""
        info = {}
        for symbol in symbols:
            try:
                profile = self.stock_service.get_company_profile(symbol)
                info[symbol] = profile
            except:
                pass
        return info
    
    def get_supported_timeframes(self) -> List[str]:
        """Get supported timeframes"""
        return ['1d']  # FMP API primarily supports daily data
    
    def get_supported_asset_types(self) -> List[str]:
        """Get supported asset types"""
        return ['stock', 'etf']

# Global registry instance
data_provider_registry = DataProviderRegistry()