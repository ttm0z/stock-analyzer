"""
Yahoo Finance data provider implementation.
"""

import yfinance as yf
import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import time
import logging

from .data_provider import DataProvider, DataRequest, DataResponse

logger = logging.getLogger(__name__)

class YahooFinanceProvider(DataProvider):
    """Yahoo Finance data provider"""
    
    def __init__(self, config: Dict = None):
        super().__init__("yahoo_finance", config)
        self.rate_limit = 100  # Yahoo is fairly generous
        self.supported_timeframes = ['1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d', '5d', '1wk', '1mo', '3mo']
        self.supported_asset_types = ['stock', 'etf', 'index', 'crypto', 'forex']
        
    def get_historical_data(self, request: DataRequest) -> DataResponse:
        """Get historical data from Yahoo Finance"""
        try:
            self._check_rate_limit()
            
            # Validate request
            valid_symbols, invalid_symbols = self.validate_symbols(request.symbols)
            if not valid_symbols:
                return DataResponse(
                    data=pd.DataFrame(),
                    symbols=request.symbols,
                    start_date=request.start_date,
                    end_date=request.end_date,
                    timeframe=request.timeframe,
                    source=self.name,
                    missing_symbols=request.symbols,
                    errors=["No valid symbols provided"]
                )
            
            if not self.validate_timeframe(request.timeframe):
                return DataResponse(
                    data=pd.DataFrame(),
                    symbols=request.symbols,
                    start_date=request.start_date,
                    end_date=request.end_date,
                    timeframe=request.timeframe,
                    source=self.name,
                    errors=[f"Unsupported timeframe: {request.timeframe}"]
                )
            
            # Download data
            data_frames = []
            missing_symbols = []
            errors = []
            
            for symbol in valid_symbols:
                try:
                    ticker = yf.Ticker(symbol)
                    
                    # Get historical data
                    hist = ticker.history(
                        start=request.start_date,
                        end=request.end_date,
                        interval=request.timeframe,
                        auto_adjust=request.adjust_for_dividends,
                        prepost=request.include_extended_hours
                    )
                    
                    if hist.empty:
                        missing_symbols.append(symbol)
                        continue
                    
                    # Standardize dataframe
                    hist = self._standardize_dataframe(hist, symbol)
                    
                    # Handle splits if requested
                    if request.adjust_for_splits and not request.adjust_for_dividends:
                        # Get split data and adjust manually
                        splits = ticker.splits
                        if not splits.empty:
                            hist = self._adjust_for_splits(hist, splits)
                    
                    data_frames.append(hist)
                    
                except Exception as e:
                    logger.error(f"Error fetching data for {symbol}: {str(e)}")
                    errors.append(f"Error fetching {symbol}: {str(e)}")
                    missing_symbols.append(symbol)
            
            # Combine all data
            if data_frames:
                combined_data = pd.concat(data_frames)
            else:
                combined_data = pd.DataFrame()
            
            # Calculate data quality
            quality_score = self.get_data_quality_score(combined_data)
            
            return DataResponse(
                data=combined_data,
                symbols=request.symbols,
                start_date=request.start_date,
                end_date=request.end_date,
                timeframe=request.timeframe,
                source=self.name,
                missing_symbols=missing_symbols,
                errors=errors,
                metadata={
                    'quality_score': quality_score,
                    'provider_info': 'Yahoo Finance',
                    'adjusted_for_splits': request.adjust_for_splits,
                    'adjusted_for_dividends': request.adjust_for_dividends
                }
            )
            
        except Exception as e:
            logger.error(f"Error in Yahoo Finance provider: {str(e)}")
            return DataResponse(
                data=pd.DataFrame(),
                symbols=request.symbols,
                start_date=request.start_date,
                end_date=request.end_date,
                timeframe=request.timeframe,
                source=self.name,
                errors=[f"Provider error: {str(e)}"]
            )
    
    def get_real_time_quote(self, symbols: List[str]) -> Dict[str, Dict]:
        """Get real-time quotes"""
        try:
            self._check_rate_limit()
            
            valid_symbols, _ = self.validate_symbols(symbols)
            quotes = {}
            
            for symbol in valid_symbols:
                try:
                    ticker = yf.Ticker(symbol)
                    info = ticker.info
                    
                    quotes[symbol] = {
                        'price': info.get('regularMarketPrice', info.get('currentPrice')),
                        'change': info.get('regularMarketChange'),
                        'change_percent': info.get('regularMarketChangePercent'),
                        'volume': info.get('regularMarketVolume'),
                        'bid': info.get('bid'),
                        'ask': info.get('ask'),
                        'bid_size': info.get('bidSize'),
                        'ask_size': info.get('askSize'),
                        'timestamp': datetime.now(),
                        'market_state': info.get('marketState', 'REGULAR')
                    }
                except Exception as e:
                    logger.error(f"Error getting quote for {symbol}: {str(e)}")
                    quotes[symbol] = {'error': str(e)}
            
            return quotes
            
        except Exception as e:
            logger.error(f"Error getting real-time quotes: {str(e)}")
            return {symbol: {'error': str(e)} for symbol in symbols}
    
    def search_symbols(self, query: str, limit: int = 10) -> List[Dict]:
        """Search for symbols"""
        try:
            # Yahoo doesn't have a direct search API, so this is a basic implementation
            # In practice, you might want to use a separate symbol lookup service
            
            # Try to get info for the query as-is (assuming it might be a symbol)
            try:
                ticker = yf.Ticker(query.upper())
                info = ticker.info
                
                if info and 'symbol' in info:
                    return [{
                        'symbol': info.get('symbol', query.upper()),
                        'name': info.get('longName', info.get('shortName', '')),
                        'exchange': info.get('exchange', ''),
                        'asset_type': self._determine_asset_type(info),
                        'currency': info.get('currency', 'USD')
                    }]
            except:
                pass
            
            return []
            
        except Exception as e:
            logger.error(f"Error searching symbols: {str(e)}")
            return []
    
    def get_asset_info(self, symbols: List[str]) -> Dict[str, Dict]:
        """Get asset information"""
        try:
            self._check_rate_limit()
            
            valid_symbols, _ = self.validate_symbols(symbols)
            asset_info = {}
            
            for symbol in valid_symbols:
                try:
                    ticker = yf.Ticker(symbol)
                    info = ticker.info
                    
                    asset_info[symbol] = {
                        'name': info.get('longName', info.get('shortName', '')),
                        'exchange': info.get('exchange', ''),
                        'currency': info.get('currency', 'USD'),
                        'asset_type': self._determine_asset_type(info),
                        'sector': info.get('sector'),
                        'industry': info.get('industry'),
                        'market_cap': info.get('marketCap'),
                        'description': info.get('longBusinessSummary', ''),
                        'website': info.get('website'),
                        'employees': info.get('fullTimeEmployees'),
                        'country': info.get('country'),
                        'city': info.get('city'),
                        'dividend_yield': info.get('dividendYield'),
                        'pe_ratio': info.get('trailingPE'),
                        'beta': info.get('beta')
                    }
                except Exception as e:
                    logger.error(f"Error getting info for {symbol}: {str(e)}")
                    asset_info[symbol] = {'error': str(e)}
            
            return asset_info
            
        except Exception as e:
            logger.error(f"Error getting asset info: {str(e)}")
            return {symbol: {'error': str(e)} for symbol in symbols}
    
    def get_supported_timeframes(self) -> List[str]:
        """Get supported timeframes"""
        return self.supported_timeframes.copy()
    
    def get_supported_asset_types(self) -> List[str]:
        """Get supported asset types"""
        return self.supported_asset_types.copy()
    
    def _determine_asset_type(self, info: Dict) -> str:
        """Determine asset type from Yahoo Finance info"""
        quote_type = info.get('quoteType', '').lower()
        
        if quote_type == 'equity':
            return 'stock'
        elif quote_type == 'etf':
            return 'etf'
        elif quote_type == 'index':
            return 'index'
        elif quote_type == 'cryptocurrency':
            return 'crypto'
        elif quote_type == 'currency':
            return 'forex'
        else:
            # Try to infer from symbol
            symbol = info.get('symbol', '').upper()
            if symbol.endswith('=X'):
                return 'forex'
            elif symbol.endswith('-USD'):
                return 'crypto'
            else:
                return 'stock'  # Default assumption
    
    def _adjust_for_splits(self, df: pd.DataFrame, splits: pd.Series) -> pd.DataFrame:
        """Manually adjust prices for splits"""
        if splits.empty:
            return df
        
        df = df.copy()
        
        for split_date, split_ratio in splits.items():
            # Adjust all prices before the split date
            mask = df.index < split_date
            df.loc[mask, ['open', 'high', 'low', 'close']] *= split_ratio
            df.loc[mask, 'volume'] /= split_ratio
        
        return df
    
    def get_dividends(self, symbol: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Get dividend data"""
        try:
            ticker = yf.Ticker(symbol)
            dividends = ticker.dividends
            
            if not dividends.empty:
                # Filter by date range
                mask = (dividends.index >= start_date) & (dividends.index <= end_date)
                dividends = dividends[mask]
            
            return dividends
            
        except Exception as e:
            logger.error(f"Error getting dividends for {symbol}: {str(e)}")
            return pd.DataFrame()
    
    def get_splits(self, symbol: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Get stock split data"""
        try:
            ticker = yf.Ticker(symbol)
            splits = ticker.splits
            
            if not splits.empty:
                # Filter by date range
                mask = (splits.index >= start_date) & (splits.index <= end_date)
                splits = splits[mask]
            
            return splits
            
        except Exception as e:
            logger.error(f"Error getting splits for {symbol}: {str(e)}")
            return pd.DataFrame()