from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.sqlite import JSON
from datetime import datetime
import json

from .base import BaseModel

class Strategy(BaseModel):
    """Strategy model for trading strategies"""
    __tablename__ = 'strategies'
    
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    strategy_type = Column(String(50), nullable=False)  # built_in, custom, imported
    category = Column(String(50), nullable=False)  # momentum, mean_reversion, breakout, etc.
    
    # Strategy implementation
    strategy_class = Column(String(200), nullable=False)  # Python class name
    strategy_code = Column(Text, nullable=True)  # For custom strategies
    version = Column(String(20), default='1.0.0', nullable=False)
    
    # Strategy status
    is_active = Column(Boolean, default=True, nullable=False)
    is_public = Column(Boolean, default=False, nullable=False)
    is_validated = Column(Boolean, default=False, nullable=False)
    
    # Performance tracking
    total_backtests = Column(Integer, default=0, nullable=False)
    avg_return = Column(Float, nullable=True)
    avg_sharpe = Column(Float, nullable=True)
    avg_max_drawdown = Column(Float, nullable=True)
    
    # Metadata
    tags = Column(JSON, nullable=True)  # Strategy tags for filtering
    
    # Relationships
    user = relationship("User", back_populates="strategies")
    parameters = relationship("StrategyParameter", back_populates="strategy", cascade="all, delete-orphan")
    backtests = relationship("Backtest", back_populates="strategy", cascade="all, delete-orphan")
    
    # Index for efficient queries
    __table_args__ = (
        Index('idx_strategy_user_active', 'user_id', 'is_active'),
        Index('idx_strategy_type_category', 'strategy_type', 'category'),
    )
    
    def to_dict(self):
        """Convert to dictionary with tags parsing"""
        data = super().to_dict()
        if self.tags:
            data['tags'] = json.loads(self.tags) if isinstance(self.tags, str) else self.tags
        return data

class StrategyParameter(BaseModel):
    """Strategy parameter definitions"""
    __tablename__ = 'strategy_parameters'
    
    strategy_id = Column(Integer, ForeignKey('strategies.id'), nullable=False)
    parameter_name = Column(String(100), nullable=False)
    parameter_type = Column(String(20), nullable=False)  # int, float, str, bool, list
    default_value = Column(String(500), nullable=False)
    min_value = Column(Float, nullable=True)
    max_value = Column(Float, nullable=True)
    allowed_values = Column(JSON, nullable=True)  # For enum-type parameters
    description = Column(Text, nullable=True)
    is_required = Column(Boolean, default=True, nullable=False)
    display_order = Column(Integer, default=0, nullable=False)
    
    # Relationships
    strategy = relationship("Strategy", back_populates="parameters")
    
    # Index for efficient queries
    __table_args__ = (
        Index('idx_strategy_parameter', 'strategy_id', 'parameter_name'),
    )
    
    def get_typed_value(self, value=None):
        """Convert string value to appropriate type"""
        val = value if value is not None else self.default_value
        
        if self.parameter_type == 'int':
            return int(val)
        elif self.parameter_type == 'float':
            return float(val)
        elif self.parameter_type == 'bool':
            return str(val).lower() in ('true', '1', 'yes', 'on')
        elif self.parameter_type == 'list':
            return json.loads(val) if isinstance(val, str) else val
        else:
            return str(val)

class StrategyTemplate(BaseModel):
    """Strategy templates for common strategy patterns"""
    __tablename__ = 'strategy_templates'
    
    name = Column(String(200), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=False)
    template_code = Column(Text, nullable=False)
    template_parameters = Column(JSON, nullable=False)
    difficulty_level = Column(String(20), default='beginner', nullable=False)  # beginner, intermediate, advanced
    estimated_runtime = Column(Integer, nullable=True)  # in seconds
    
    # Usage statistics
    usage_count = Column(Integer, default=0, nullable=False)
    avg_rating = Column(Float, nullable=True)
    
    # Metadata
    tags = Column(JSON, nullable=True)
    author = Column(String(100), nullable=True)
    
    def to_dict(self):
        """Convert to dictionary with JSON parsing"""
        data = super().to_dict()
        for field in ['template_parameters', 'tags']:
            if data.get(field):
                data[field] = json.loads(data[field]) if isinstance(data[field], str) else data[field]
        return data

class StrategyLibrary(BaseModel):
    """Library of shared strategies"""
    __tablename__ = 'strategy_library'
    
    strategy_id = Column(Integer, ForeignKey('strategies.id'), nullable=False)
    library_name = Column(String(200), nullable=False)
    library_description = Column(Text, nullable=True)
    is_featured = Column(Boolean, default=False, nullable=False)
    download_count = Column(Integer, default=0, nullable=False)
    rating = Column(Float, nullable=True)
    rating_count = Column(Integer, default=0, nullable=False)
    
    # Publication info
    published_at = Column(DateTime, nullable=True)
    published_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    # Relationships
    strategy = relationship("Strategy")
    publisher = relationship("User")
    
    # Index for efficient queries
    __table_args__ = (
        Index('idx_strategy_library_featured', 'is_featured'),
        Index('idx_strategy_library_rating', 'rating'),
    )

class StrategyValidation(BaseModel):
    """Strategy validation results"""
    __tablename__ = 'strategy_validations'
    
    strategy_id = Column(Integer, ForeignKey('strategies.id'), nullable=False)
    validation_type = Column(String(50), nullable=False)  # syntax, logic, performance
    status = Column(String(20), nullable=False)  # pending, passed, failed
    
    # Validation results
    errors = Column(JSON, nullable=True)
    warnings = Column(JSON, nullable=True)
    performance_metrics = Column(JSON, nullable=True)
    
    # Validation metadata
    validator_version = Column(String(20), nullable=True)
    validation_duration = Column(Float, nullable=True)  # in seconds
    validated_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    # Relationships
    strategy = relationship("Strategy")
    validator = relationship("User")
    
    # Index for efficient queries
    __table_args__ = (
        Index('idx_strategy_validation_status', 'strategy_id', 'status'),
    )

class StrategyPerformance(BaseModel):
    """Aggregated strategy performance metrics"""
    __tablename__ = 'strategy_performance'
    
    strategy_id = Column(Integer, ForeignKey('strategies.id'), nullable=False)
    
    # Performance period
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    period_type = Column(String(20), nullable=False)  # daily, monthly, yearly, all_time
    
    # Return metrics
    total_return = Column(Float, nullable=True)
    annualized_return = Column(Float, nullable=True)
    volatility = Column(Float, nullable=True)
    sharpe_ratio = Column(Float, nullable=True)
    sortino_ratio = Column(Float, nullable=True)
    
    # Risk metrics
    max_drawdown = Column(Float, nullable=True)
    var_95 = Column(Float, nullable=True)  # Value at Risk
    cvar_95 = Column(Float, nullable=True)  # Conditional Value at Risk
    
    # Trade metrics
    total_trades = Column(Integer, nullable=True)
    winning_trades = Column(Integer, nullable=True)
    losing_trades = Column(Integer, nullable=True)
    win_rate = Column(Float, nullable=True)
    avg_win = Column(Float, nullable=True)
    avg_loss = Column(Float, nullable=True)
    profit_factor = Column(Float, nullable=True)
    
    # Benchmark comparison
    benchmark_symbol = Column(String(20), nullable=True)
    alpha = Column(Float, nullable=True)
    beta = Column(Float, nullable=True)
    information_ratio = Column(Float, nullable=True)
    
    # Relationships
    strategy = relationship("Strategy")
    
    # Index for efficient queries
    __table_args__ = (
        Index('idx_strategy_performance_period', 'strategy_id', 'period_type'),
    )