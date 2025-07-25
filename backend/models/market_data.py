from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Index, CheckConstraint, Numeric, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from .base import BaseModel

class Asset(BaseModel):
    """Asset model for tradeable instruments with PostgreSQL optimizations."""
    __tablename__ = 'assets'
    
    # Asset identification
    symbol = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    asset_type = Column(String(20), nullable=False, index=True)  # stock, etf, crypto, option, etc.
    
    # Asset classification
    exchange = Column(String(10), nullable=False, index=True)
    currency = Column(String(3), default='USD', nullable=False)
    sector = Column(String(50), nullable=True, index=True)
    industry = Column(String(100), nullable=True, index=True)
    country = Column(String(2), nullable=True, index=True)  # ISO country code
    
    # Market data
    market_cap = Column(Numeric(20, 2), nullable=True)
    shares_outstanding = Column(Numeric(15, 0), nullable=True)
    float_shares = Column(Numeric(15, 0), nullable=True)
    
    # Asset status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_tradeable = Column(Boolean, default=True, nullable=False)
    listing_date = Column(DateTime, nullable=True)
    delisting_date = Column(DateTime, nullable=True)
    
    # Asset metadata stored as JSONB
    fundamentals = Column(JSONB, nullable=True)  # Key fundamental ratios
    metadata = Column(JSONB, nullable=True)      # Additional asset information
    
    # Pricing information
    last_price = Column(Numeric(10, 4), nullable=True)
    last_update = Column(DateTime, nullable=True)
    
    # Relationships
    market_data = relationship("MarketData", back_populates="asset", cascade="all, delete-orphan")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_asset_type_exchange', 'asset_type', 'exchange'),
        Index('idx_asset_sector_industry', 'sector', 'industry'),
        Index('idx_asset_active_tradeable', 'is_active', 'is_tradeable'),
        Index('idx_asset_last_update', 'last_update'),
        CheckConstraint('asset_type IN (\'stock\', \'etf\', \'crypto\', \'option\', \'future\', \'bond\', \'commodity\')', name='ck_asset_type_valid'),
        CheckConstraint('length(currency) = 3', name='ck_currency_length'),
        CheckConstraint('length(country) = 2 OR country IS NULL', name='ck_country_length'),
        CheckConstraint('market_cap >= 0 OR market_cap IS NULL', name='ck_market_cap_non_negative'),
        CheckConstraint('shares_outstanding >= 0 OR shares_outstanding IS NULL', name='ck_shares_outstanding_non_negative'),
        CheckConstraint('last_price > 0 OR last_price IS NULL', name='ck_last_price_positive_or_null'),
    )

class MarketData(BaseModel):
    """Market data model for OHLCV data with PostgreSQL optimizations and partitioning support."""
    __tablename__ = 'market_data'
    
    # Foreign key
    asset_id = Column(Integer, ForeignKey('assets.id'), nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True)  # Denormalized for performance
    
    # Time series data
    timestamp = Column(DateTime, nullable=False, index=True)
    timeframe = Column(String(10), nullable=False, index=True)  # 1m, 5m, 1h, 1d, etc.
    
    # OHLCV data - Using Numeric for precision
    open_price = Column(Numeric(10, 4), nullable=False)
    high_price = Column(Numeric(10, 4), nullable=False)
    low_price = Column(Numeric(10, 4), nullable=False)
    close_price = Column(Numeric(10, 4), nullable=False)
    volume = Column(Numeric(15, 0), default=0, nullable=False)
    
    # Adjusted prices for splits/dividends
    adj_open = Column(Numeric(10, 4), nullable=True)
    adj_high = Column(Numeric(10, 4), nullable=True)
    adj_low = Column(Numeric(10, 4), nullable=True)
    adj_close = Column(Numeric(10, 4), nullable=True)
    adj_volume = Column(Numeric(15, 0), nullable=True)
    
    # Market microstructure data
    bid_price = Column(Numeric(10, 4), nullable=True)
    ask_price = Column(Numeric(10, 4), nullable=True)
    bid_size = Column(Numeric(10, 0), nullable=True)
    ask_size = Column(Numeric(10, 0), nullable=True)
    spread = Column(Numeric(10, 4), nullable=True)
    
    # Trade statistics
    trade_count = Column(Integer, nullable=True)
    vwap = Column(Numeric(10, 4), nullable=True)  # Volume Weighted Average Price
    
    # Data quality flags
    is_adjusted = Column(Boolean, default=False, nullable=False)
    has_splits = Column(Boolean, default=False, nullable=False)
    has_dividends = Column(Boolean, default=False, nullable=False)
    
    # Additional market data stored as JSONB
    additional_data = Column(JSONB, nullable=True)  # Options data, sentiment, etc.
    
    # Relationships
    asset = relationship("Asset", back_populates="market_data")
    
    # Indexes for performance (critical for time-series queries)
    __table_args__ = (
        # Unique constraint for no duplicate data points
        UniqueConstraint('symbol', 'timestamp', 'timeframe', name='uq_market_data_symbol_time_frame'),
        # Primary time-series indexes
        Index('idx_market_data_symbol_timeframe_timestamp', 'symbol', 'timeframe', 'timestamp'),
        Index('idx_market_data_timestamp_symbol', 'timestamp', 'symbol'),
        Index('idx_market_data_asset_timeframe_timestamp', 'asset_id', 'timeframe', 'timestamp'),
        # Volume and price indexes for screening
        Index('idx_market_data_volume_timestamp', 'volume', 'timestamp'),
        Index('idx_market_data_close_timestamp', 'close_price', 'timestamp'),
        # Data quality indexes
        Index('idx_market_data_adjusted', 'is_adjusted', 'timestamp'),
        
        # Data validation constraints
        CheckConstraint('open_price > 0', name='ck_open_price_positive'),
        CheckConstraint('high_price > 0', name='ck_high_price_positive'),
        CheckConstraint('low_price > 0', name='ck_low_price_positive'),
        CheckConstraint('close_price > 0', name='ck_close_price_positive'),
        CheckConstraint('volume >= 0', name='ck_volume_non_negative'),
        CheckConstraint('high_price >= low_price', name='ck_high_low_valid'),
        CheckConstraint('high_price >= open_price', name='ck_high_open_valid'),
        CheckConstraint('high_price >= close_price', name='ck_high_close_valid'),
        CheckConstraint('low_price <= open_price', name='ck_low_open_valid'),
        CheckConstraint('low_price <= close_price', name='ck_low_close_valid'),
        CheckConstraint('timeframe IN (\'1m\', \'5m\', \'15m\', \'30m\', \'1h\', \'4h\', \'1d\', \'1w\', \'1M\')', name='ck_timeframe_valid'),
        CheckConstraint('bid_price > 0 OR bid_price IS NULL', name='ck_bid_price_positive_or_null'),
        CheckConstraint('ask_price > 0 OR ask_price IS NULL', name='ck_ask_price_positive_or_null'),
        CheckConstraint('ask_price >= bid_price OR ask_price IS NULL OR bid_price IS NULL', name='ck_bid_ask_spread_valid'),
        CheckConstraint('trade_count >= 0 OR trade_count IS NULL', name='ck_trade_count_non_negative'),
        
        # Note: In production, consider partitioning this table by timestamp ranges
        # PostgreSQL partitioning example:
        # PARTITION BY RANGE (timestamp)
        # With monthly or yearly partitions depending on data volume
    )
    
    @property
    def typical_price(self):
        """Calculate typical price (HLC/3)."""
        return (self.high_price + self.low_price + self.close_price) / 3
    
    @property
    def price_change(self):
        """Calculate price change from open to close."""
        return self.close_price - self.open_price
    
    @property
    def price_change_pct(self):
        """Calculate percentage price change."""
        if self.open_price == 0:
            return 0
        return ((self.close_price - self.open_price) / self.open_price) * 100
    
    @property
    def true_range(self):
        """Calculate True Range for volatility measures."""
        # This would typically require previous close, simplified here
        return self.high_price - self.low_price

class Benchmark(BaseModel):
    """Benchmark model for performance comparison with PostgreSQL optimizations."""
    __tablename__ = 'benchmarks'
    
    # Benchmark identification
    symbol = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    # Benchmark classification
    benchmark_type = Column(String(50), nullable=False, index=True)  # market, sector, strategy, etc.
    category = Column(String(50), nullable=False, index=True)
    geographic_focus = Column(String(50), nullable=True)
    
    # Benchmark composition
    composition = Column(JSONB, nullable=True)  # Holdings and weights
    methodology = Column(Text, nullable=True)   # How the benchmark is constructed
    
    # Performance data - Using Numeric for precision
    inception_date = Column(DateTime, nullable=False)
    current_value = Column(Numeric(15, 4), nullable=True)
    
    # Benchmark statistics
    total_return_ytd = Column(Numeric(8, 4), nullable=True)
    total_return_1y = Column(Numeric(8, 4), nullable=True)
    total_return_3y = Column(Numeric(8, 4), nullable=True)
    total_return_5y = Column(Numeric(8, 4), nullable=True)
    total_return_10y = Column(Numeric(8, 4), nullable=True)
    
    # Risk metrics - Using Numeric for precision
    volatility_1y = Column(Numeric(8, 4), nullable=True)
    volatility_3y = Column(Numeric(8, 4), nullable=True)
    max_drawdown_1y = Column(Numeric(8, 4), nullable=True)
    max_drawdown_3y = Column(Numeric(8, 4), nullable=True)
    
    # Benchmark status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_default = Column(Boolean, default=False, nullable=False)  # Default benchmark for comparison
    last_updated = Column(DateTime, nullable=True)
    
    # Data source information
    data_provider = Column(String(50), nullable=True)
    update_frequency = Column(String(20), default='daily', nullable=False)
    
    # Benchmark metadata stored as JSONB
    metadata = Column(JSONB, nullable=True)
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_benchmark_type_category', 'benchmark_type', 'category'),
        Index('idx_benchmark_active_default', 'is_active', 'is_default'),
        Index('idx_benchmark_last_updated', 'last_updated'),
        CheckConstraint('benchmark_type IN (\'market\', \'sector\', \'style\', \'strategy\', \'custom\')', name='ck_benchmark_type_valid'),
        CheckConstraint('update_frequency IN (\'realtime\', \'daily\', \'weekly\', \'monthly\')', name='ck_update_frequency_valid'),
    )
    
    def calculate_annualized_return(self, total_return, years):
        """Calculate annualized return from total return."""
        if years <= 0 or total_return is None:
            return None
        return ((1 + total_return / 100) ** (1 / years) - 1) * 100