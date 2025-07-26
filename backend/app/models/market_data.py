from datetime import datetime
from .base import BaseModel
from ..db import db

class Asset(BaseModel):
    """Asset model for tradeable instruments with PostgreSQL optimizations."""
    __tablename__ = 'assets'
    
    # Asset identification
    symbol = db.Column(db.String(20), unique=True, nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    asset_type = db.Column(db.String(20), nullable=False, index=True)  # stock, etf, crypto, option, etc.
    
    # Asset classification
    exchange = db.Column(db.String(10), nullable=False, index=True)
    currency = db.Column(db.String(3), default='USD', nullable=False)
    sector = db.Column(db.String(50), nullable=True, index=True)
    industry = db.Column(db.String(100), nullable=True, index=True)
    country = db.Column(db.String(2), nullable=True, index=True)  # ISO country code
    
    # Market data
    market_cap = db.Column(db.Numeric(20, 2), nullable=True)
    shares_outstanding = db.Column(db.Numeric(15, 0), nullable=True)
    float_shares = db.Column(db.Numeric(15, 0), nullable=True)
    
    # Asset status
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)
    is_tradeable = db.Column(db.Boolean, default=True, nullable=False)
    listing_date = db.Column(db.DateTime, nullable=True)
    delisting_date = db.Column(db.DateTime, nullable=True)
    
    # Asset metadata stored as JSONB
    fundamentals = db.Column(db.JSON, nullable=True)  # Key fundamental ratios
    additional_metadata = db.Column(db.JSON, nullable=True)      # Additional asset information
    
    # Pricing information
    last_price = db.Column(db.Numeric(10, 4), nullable=True)
    last_update = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    market_data = db.relationship("MarketData", back_populates="asset", cascade="all, delete-orphan")
    
    # Indexes for performance
    __table_args__ = (
        db.Index('idx_asset_type_exchange', 'asset_type', 'exchange'),
        db.Index('idx_asset_sector_industry', 'sector', 'industry'),
        db.Index('idx_asset_active_tradeable', 'is_active', 'is_tradeable'),
        db.Index('idx_asset_last_update', 'last_update'),
        db.CheckConstraint('asset_type IN (\'stock\', \'etf\', \'crypto\', \'option\', \'future\', \'bond\', \'commodity\')', name='ck_asset_type_valid'),
        db.CheckConstraint('length(currency) = 3', name='ck_currency_length'),
        db.CheckConstraint('length(country) = 2 OR country IS NULL', name='ck_country_length'),
        db.CheckConstraint('market_cap >= 0 OR market_cap IS NULL', name='ck_market_cap_non_negative'),
        db.CheckConstraint('shares_outstanding >= 0 OR shares_outstanding IS NULL', name='ck_shares_outstanding_non_negative'),
        db.CheckConstraint('last_price > 0 OR last_price IS NULL', name='ck_last_price_positive_or_null'),
    )

class MarketData(BaseModel):
    """Market data model for OHLCV data with PostgreSQL optimizations and partitioning support."""
    __tablename__ = 'market_data'
    
    # Foreign key
    asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'), nullable=False, index=True)
    symbol = db.Column(db.String(20), nullable=False, index=True)  # Denormalized for performance
    
    # Time series data
    timestamp = db.Column(db.DateTime, nullable=False, index=True)
    timeframe = db.Column(db.String(10), nullable=False, index=True)  # 1m, 5m, 1h, 1d, etc.
    
    # OHLCV data - Using Numeric for precision
    open_price = db.Column(db.Numeric(10, 4), nullable=False)
    high_price = db.Column(db.Numeric(10, 4), nullable=False)
    low_price = db.Column(db.Numeric(10, 4), nullable=False)
    close_price = db.Column(db.Numeric(10, 4), nullable=False)
    volume = db.Column(db.Numeric(15, 0), default=0, nullable=False)
    
    # Adjusted prices for splits/dividends
    adj_open = db.Column(db.Numeric(10, 4), nullable=True)
    adj_high = db.Column(db.Numeric(10, 4), nullable=True)
    adj_low = db.Column(db.Numeric(10, 4), nullable=True)
    adj_close = db.Column(db.Numeric(10, 4), nullable=True)
    adj_volume = db.Column(db.Numeric(15, 0), nullable=True)
    
    # Market microstructure data
    bid_price = db.Column(db.Numeric(10, 4), nullable=True)
    ask_price = db.Column(db.Numeric(10, 4), nullable=True)
    bid_size = db.Column(db.Numeric(10, 0), nullable=True)
    ask_size = db.Column(db.Numeric(10, 0), nullable=True)
    spread = db.Column(db.Numeric(10, 4), nullable=True)
    
    # Trade statistics
    trade_count = db.Column(db.Integer, nullable=True)
    vwap = db.Column(db.Numeric(10, 4), nullable=True)  # Volume Weighted Average Price
    
    # Data quality flags
    is_adjusted = db.Column(db.Boolean, default=False, nullable=False)
    has_splits = db.Column(db.Boolean, default=False, nullable=False)
    has_dividends = db.Column(db.Boolean, default=False, nullable=False)
    
    # Additional market data stored as JSONB
    additional_data = db.Column(db.JSON, nullable=True)  # Options data, sentiment, etc.
    
    # Relationships
    asset = db.relationship("Asset", back_populates="market_data")
    
    # Indexes for performance (critical for time-series queries)
    __table_args__ = (
        # Unique constraint for no duplicate data points
        db.UniqueConstraint('symbol', 'timestamp', 'timeframe', name='uq_market_data_symbol_time_frame'),
        # Primary time-series indexes
        db.Index('idx_market_data_symbol_timeframe_timestamp', 'symbol', 'timeframe', 'timestamp'),
        db.Index('idx_market_data_timestamp_symbol', 'timestamp', 'symbol'),
        db.Index('idx_market_data_asset_timeframe_timestamp', 'asset_id', 'timeframe', 'timestamp'),
        # Volume and price indexes for screening
        db.Index('idx_market_data_volume_timestamp', 'volume', 'timestamp'),
        db.Index('idx_market_data_close_timestamp', 'close_price', 'timestamp'),
        # Data quality indexes
        db.Index('idx_market_data_adjusted', 'is_adjusted', 'timestamp'),
        
        # Data validation constraints
        db.CheckConstraint('open_price > 0', name='ck_open_price_positive'),
        db.CheckConstraint('high_price > 0', name='ck_high_price_positive'),
        db.CheckConstraint('low_price > 0', name='ck_low_price_positive'),
        db.CheckConstraint('close_price > 0', name='ck_close_price_positive'),
        db.CheckConstraint('volume >= 0', name='ck_volume_non_negative'),
        db.CheckConstraint('high_price >= low_price', name='ck_high_low_valid'),
        db.CheckConstraint('high_price >= open_price', name='ck_high_open_valid'),
        db.CheckConstraint('high_price >= close_price', name='ck_high_close_valid'),
        db.CheckConstraint('low_price <= open_price', name='ck_low_open_valid'),
        db.CheckConstraint('low_price <= close_price', name='ck_low_close_valid'),
        db.CheckConstraint('timeframe IN (\'1m\', \'5m\', \'15m\', \'30m\', \'1h\', \'4h\', \'1d\', \'1w\', \'1M\')', name='ck_timeframe_valid'),
        db.CheckConstraint('bid_price > 0 OR bid_price IS NULL', name='ck_bid_price_positive_or_null'),
        db.CheckConstraint('ask_price > 0 OR ask_price IS NULL', name='ck_ask_price_positive_or_null'),
        db.CheckConstraint('ask_price >= bid_price OR ask_price IS NULL OR bid_price IS NULL', name='ck_bid_ask_spread_valid'),
        db.CheckConstraint('trade_count >= 0 OR trade_count IS NULL', name='ck_trade_count_non_negative'),
        
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
    """Benchmark indices for performance comparison"""
    __tablename__ = 'benchmarks'
    
    symbol = db.Column(db.String(20), nullable=False, unique=True, index=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    asset_class = db.Column(db.String(50), nullable=False)  # equity, bond, commodity, etc.
    geography = db.Column(db.String(50), nullable=True)  # US, Europe, Global, etc.
    currency = db.Column(db.String(10), default='USD', nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Benchmark metadata
    inception_date = db.Column(db.DateTime, nullable=True)
    methodology = db.Column(db.Text, nullable=True)
    rebalance_frequency = db.Column(db.String(20), nullable=True)  # daily, monthly, quarterly

class MarketDataAdjustment(BaseModel):
    """Market data adjustments for splits, dividends, etc."""
    __tablename__ = 'market_data_adjustments'
    
    # Foreign key
    asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'), nullable=False, index=True)
    
    # Adjustment details
    adjustment_type = db.Column(db.String(20), nullable=False, index=True)  # SPLIT, DIVIDEND, MERGER
    adjustment_date = db.Column(db.DateTime, nullable=False, index=True)
    adjustment_factor = db.Column(db.Numeric(10, 6), nullable=False)
    
    # Additional data for different adjustment types
    dividend_amount = db.Column(db.Numeric(10, 4), nullable=True)  # For dividends
    split_ratio = db.Column(db.String(20), nullable=True)  # e.g., "2:1"
    
    # Metadata
    data_source = db.Column(db.String(50), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    
    # Relationships
    asset = db.relationship("Asset", backref="adjustments")
    
    # Indexes and constraints
    __table_args__ = (
        db.Index('idx_adjustment_asset_date_type', 'asset_id', 'adjustment_date', 'adjustment_type'),
        db.CheckConstraint('adjustment_type IN (\'SPLIT\', \'DIVIDEND\', \'MERGER\')', name='ck_adjustment_type_valid'),
        db.CheckConstraint('adjustment_factor > 0', name='ck_adjustment_factor_positive'),
    )


class DataSource(BaseModel):
    """Data source configuration and metadata."""
    __tablename__ = 'data_sources'
    
    # Source identification
    name = db.Column(db.String(100), nullable=False, unique=True)
    provider = db.Column(db.String(100), nullable=False)
    source_type = db.Column(db.String(50), nullable=False, index=True)  # REAL_TIME, HISTORICAL, FUNDAMENTAL
    
    # Configuration
    api_endpoint = db.Column(db.String(500), nullable=True)
    api_key_required = db.Column(db.Boolean, default=False, nullable=False)
    rate_limit = db.Column(db.Integer, nullable=True)  # Requests per minute
    
    # Data coverage
    supported_symbols = db.Column(db.JSON, nullable=True)  # Array of supported symbol types
    supported_intervals = db.Column(db.JSON, nullable=True)  # Array of supported time intervals
    data_lag = db.Column(db.Integer, nullable=True)  # Minutes delay
    
    # Status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    last_health_check = db.Column(db.DateTime, nullable=True)
    health_status = db.Column(db.String(20), default='UNKNOWN', nullable=False)
    
    # Metadata
    configuration = db.Column(db.JSON, nullable=True)  # Source-specific config
    
    # Constraints
    __table_args__ = (
        db.Index('idx_data_source_type_active', 'source_type', 'is_active'),
        db.CheckConstraint('source_type IN (\'REAL_TIME\', \'HISTORICAL\', \'FUNDAMENTAL\', \'NEWS\')', name='ck_source_type_valid'),
        db.CheckConstraint('health_status IN (\'HEALTHY\', \'DEGRADED\', \'DOWN\', \'UNKNOWN\')', name='ck_health_status_valid'),
    )


class DataQuality(BaseModel):
    """Data quality metrics and monitoring."""
    __tablename__ = 'data_quality'
    
    # Foreign keys
    asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'), nullable=False, index=True)
    data_source_id = db.Column(db.Integer, db.ForeignKey('data_sources.id'), nullable=False, index=True)
    
    # Quality metrics
    completeness_score = db.Column(db.Numeric(5, 2), nullable=False)  # 0-100
    accuracy_score = db.Column(db.Numeric(5, 2), nullable=True)       # 0-100  
    timeliness_score = db.Column(db.Numeric(5, 2), nullable=True)     # 0-100
    consistency_score = db.Column(db.Numeric(5, 2), nullable=True)    # 0-100
    
    # Issue tracking
    missing_data_points = db.Column(db.Integer, default=0, nullable=False)
    outlier_count = db.Column(db.Integer, default=0, nullable=False)
    duplicate_count = db.Column(db.Integer, default=0, nullable=False)
    
    # Time period for these metrics
    measurement_date = db.Column(db.DateTime, nullable=False, index=True)
    measurement_period = db.Column(db.String(20), default='DAILY', nullable=False)  # DAILY, WEEKLY, MONTHLY
    
    # Quality issues
    issues = db.Column(db.JSON, nullable=True)  # Array of specific issues found
    
    # Relationships
    asset = db.relationship("Asset", backref="quality_metrics")
    data_source = db.relationship("DataSource", backref="quality_metrics")
    
    # Indexes and constraints
    __table_args__ = (
        db.Index('idx_quality_asset_source_date', 'asset_id', 'data_source_id', 'measurement_date'),
        db.CheckConstraint('completeness_score BETWEEN 0 AND 100', name='ck_completeness_valid'),
        db.CheckConstraint('accuracy_score BETWEEN 0 AND 100 OR accuracy_score IS NULL', name='ck_accuracy_valid'),
        db.CheckConstraint('timeliness_score BETWEEN 0 AND 100 OR timeliness_score IS NULL', name='ck_timeliness_valid'),
        db.CheckConstraint('consistency_score BETWEEN 0 AND 100 OR consistency_score IS NULL', name='ck_consistency_valid'),
        db.CheckConstraint('measurement_period IN (\'DAILY\', \'WEEKLY\', \'MONTHLY\')', name='ck_measurement_period_valid'),
    )


class MarketCalendar(BaseModel):
    """Market calendar for trading hours and holidays."""
    __tablename__ = 'market_calendar'
    
    # Market identification
    market_code = db.Column(db.String(10), nullable=False, index=True)  # NYSE, NASDAQ, LSE, etc.
    market_name = db.Column(db.String(100), nullable=False)
    
    # Calendar date
    calendar_date = db.Column(db.DateTime, nullable=False, index=True)
    
    # Market status
    is_trading_day = db.Column(db.Boolean, nullable=False, index=True)
    is_holiday = db.Column(db.Boolean, default=False, nullable=False)
    holiday_name = db.Column(db.String(100), nullable=True)
    
    # Trading hours (stored as time strings, e.g., "09:30")
    market_open = db.Column(db.String(5), nullable=True)   # HH:MM format
    market_close = db.Column(db.String(5), nullable=True)  # HH:MM format
    pre_market_open = db.Column(db.String(5), nullable=True)
    after_hours_close = db.Column(db.String(5), nullable=True)
    
    # Special conditions
    early_close = db.Column(db.Boolean, default=False, nullable=False)
    late_open = db.Column(db.Boolean, default=False, nullable=False)
    
    # Timezone
    timezone = db.Column(db.String(50), default='UTC', nullable=False)
    
    # Notes
    notes = db.Column(db.Text, nullable=True)
    
    # Indexes and constraints
    __table_args__ = (
        db.Index('idx_market_calendar_market_date', 'market_code', 'calendar_date'),
        db.Index('idx_market_calendar_trading_day', 'calendar_date', 'is_trading_day'),
        db.CheckConstraint('market_open ~ \'^[0-2][0-9]:[0-5][0-9]$\' OR market_open IS NULL', name='ck_market_open_format'),
        db.CheckConstraint('market_close ~ \'^[0-2][0-9]:[0-5][0-9]$\' OR market_close IS NULL', name='ck_market_close_format'),
    )