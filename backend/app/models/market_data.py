from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.sqlite import JSON
from datetime import datetime
import json

from .base import BaseModel

class Asset(BaseModel):
    """Asset model for stocks, ETFs, etc."""
    __tablename__ = 'assets'
    
    symbol = Column(String(20), nullable=False, unique=True, index=True)
    name = Column(String(200), nullable=False)
    asset_type = Column(String(20), nullable=False)  # stock, etf, index, crypto
    exchange = Column(String(10), nullable=False)
    currency = Column(String(10), default='USD', nullable=False)
    sector = Column(String(50), nullable=True)
    industry = Column(String(100), nullable=True)
    market_cap = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    metadata = Column(JSON, nullable=True)  # Additional asset information
    
    # Index for efficient queries
    __table_args__ = (
        Index('idx_asset_symbol_exchange', 'symbol', 'exchange'),
        Index('idx_asset_type_active', 'asset_type', 'is_active'),
    )
    
    def to_dict(self):
        """Convert to dictionary with metadata parsing"""
        data = super().to_dict()
        if self.metadata:
            data['metadata'] = json.loads(self.metadata) if isinstance(self.metadata, str) else self.metadata
        return data

class MarketData(BaseModel):
    """Market data model for OHLCV data"""
    __tablename__ = 'market_data'
    
    symbol = Column(String(20), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    timeframe = Column(String(10), nullable=False)  # 1m, 5m, 1h, 1d, etc.
    open_price = Column(Float, nullable=False)
    high_price = Column(Float, nullable=False)
    low_price = Column(Float, nullable=False)
    close_price = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    adjusted_close = Column(Float, nullable=True)  # For dividend/split adjustments
    
    # Additional technical data
    vwap = Column(Float, nullable=True)  # Volume Weighted Average Price
    trades_count = Column(Integer, nullable=True)
    
    # Data quality indicators
    is_validated = Column(Boolean, default=False, nullable=False)
    data_source = Column(String(50), nullable=False)
    
    # Unique constraint to prevent duplicate data
    __table_args__ = (
        UniqueConstraint('symbol', 'timestamp', 'timeframe', name='uq_market_data'),
        Index('idx_market_data_symbol_timeframe_timestamp', 'symbol', 'timeframe', 'timestamp'),
        Index('idx_market_data_timestamp', 'timestamp'),
    )
    
    def to_dict(self):
        """Convert to dictionary with calculated fields"""
        data = super().to_dict()
        # Add calculated fields
        data['price_change'] = self.close_price - self.open_price
        data['price_change_pct'] = ((self.close_price - self.open_price) / self.open_price) * 100
        data['range'] = self.high_price - self.low_price
        return data

class MarketDataAdjustment(BaseModel):
    """Corporate actions affecting market data"""
    __tablename__ = 'market_data_adjustments'
    
    symbol = Column(String(20), nullable=False, index=True)
    ex_date = Column(DateTime, nullable=False)
    adjustment_type = Column(String(20), nullable=False)  # split, dividend, rights
    adjustment_factor = Column(Float, nullable=False)
    dividend_amount = Column(Float, nullable=True)
    description = Column(Text, nullable=True)
    
    # Index for efficient queries
    __table_args__ = (
        Index('idx_adjustment_symbol_date', 'symbol', 'ex_date'),
    )

class DataSource(BaseModel):
    """Data source configuration and status"""
    __tablename__ = 'data_sources'
    
    name = Column(String(50), nullable=False, unique=True)
    provider = Column(String(50), nullable=False)  # yahoo, alpha_vantage, etc.
    is_active = Column(Boolean, default=True, nullable=False)
    api_key = Column(String(255), nullable=True)
    rate_limit = Column(Integer, nullable=True)  # requests per minute
    cost_per_request = Column(Float, nullable=True)
    supported_assets = Column(JSON, nullable=True)  # List of supported asset types
    supported_timeframes = Column(JSON, nullable=True)  # List of supported timeframes
    configuration = Column(JSON, nullable=True)  # Additional configuration
    
    def to_dict(self):
        """Convert to dictionary with configuration parsing"""
        data = super().to_dict()
        # Parse JSON fields
        for field in ['supported_assets', 'supported_timeframes', 'configuration']:
            if data.get(field):
                data[field] = json.loads(data[field]) if isinstance(data[field], str) else data[field]
        return data

class DataQuality(BaseModel):
    """Data quality metrics and validation results"""
    __tablename__ = 'data_quality'
    
    symbol = Column(String(20), nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)
    timeframe = Column(String(10), nullable=False)
    
    # Quality metrics
    missing_data_points = Column(Integer, default=0, nullable=False)
    invalid_prices = Column(Integer, default=0, nullable=False)
    zero_volume_bars = Column(Integer, default=0, nullable=False)
    price_gaps = Column(Integer, default=0, nullable=False)
    
    # Quality scores (0-100)
    completeness_score = Column(Float, nullable=False)
    accuracy_score = Column(Float, nullable=False)
    consistency_score = Column(Float, nullable=False)
    overall_score = Column(Float, nullable=False)
    
    # Validation details
    validation_errors = Column(JSON, nullable=True)
    last_validated = Column(DateTime, nullable=False)
    
    # Index for efficient queries
    __table_args__ = (
        Index('idx_data_quality_symbol_date', 'symbol', 'date'),
    )

class MarketCalendar(BaseModel):
    """Market calendar for trading days and holidays"""
    __tablename__ = 'market_calendar'
    
    exchange = Column(String(10), nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)
    is_trading_day = Column(Boolean, nullable=False)
    is_half_day = Column(Boolean, default=False, nullable=False)
    market_open = Column(DateTime, nullable=True)
    market_close = Column(DateTime, nullable=True)
    holiday_name = Column(String(100), nullable=True)
    
    # Unique constraint
    __table_args__ = (
        UniqueConstraint('exchange', 'date', name='uq_market_calendar'),
    )

class Benchmark(BaseModel):
    """Benchmark indices for performance comparison"""
    __tablename__ = 'benchmarks'
    
    symbol = Column(String(20), nullable=False, unique=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    asset_class = Column(String(50), nullable=False)  # equity, bond, commodity, etc.
    geography = Column(String(50), nullable=True)  # US, Europe, Global, etc.
    currency = Column(String(10), default='USD', nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Benchmark metadata
    inception_date = Column(DateTime, nullable=True)
    methodology = Column(Text, nullable=True)
    rebalance_frequency = Column(String(20), nullable=True)  # daily, monthly, quarterly