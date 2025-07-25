from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Index, CheckConstraint, Numeric, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from .base import BaseModel

class Strategy(BaseModel):
    """Strategy model for trading strategies with PostgreSQL optimizations."""
    __tablename__ = 'strategies'
    
    # Foreign key
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    
    # Basic strategy information
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    strategy_type = Column(String(50), nullable=False, index=True)  # momentum, mean_reversion, etc.
    
    # Strategy classification
    category = Column(String(50), nullable=False, index=True)  # equity, options, crypto, etc.
    complexity = Column(String(20), default='intermediate', nullable=False)  # beginner, intermediate, advanced
    
    # Strategy configuration stored as JSONB
    parameters = Column(JSONB, nullable=False)  # Strategy-specific parameters
    entry_rules = Column(JSONB, nullable=False)  # Entry condition rules
    exit_rules = Column(JSONB, nullable=False)   # Exit condition rules
    risk_rules = Column(JSONB, nullable=True)    # Risk management rules
    
    # Strategy metadata
    version = Column(String(20), default='1.0.0', nullable=False)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_public = Column(Boolean, default=False, nullable=False)
    
    # Performance tracking
    total_backtests = Column(Integer, default=0, nullable=False)
    successful_backtests = Column(Integer, default=0, nullable=False)
    
    # Strategy source code (for custom strategies)
    source_code = Column(Text, nullable=True)
    code_language = Column(String(20), default='python', nullable=False)
    
    # Tags and categorization
    tags = Column(JSONB, nullable=True)  # Array of tags
    
    # Relationships
    user = relationship("User", back_populates="strategies")
    parameters_rel = relationship("StrategyParameter", back_populates="strategy", cascade="all, delete-orphan")
    backtests = relationship("Backtest", back_populates="strategy", cascade="all, delete-orphan")
    performance = relationship("StrategyPerformance", back_populates="strategy", uselist=False, cascade="all, delete-orphan")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_strategy_user_type_active', 'user_id', 'strategy_type', 'is_active'),
        Index('idx_strategy_category_public', 'category', 'is_public'),
        Index('idx_strategy_complexity', 'complexity'),
        CheckConstraint('complexity IN (\'beginner\', \'intermediate\', \'advanced\')', name='ck_complexity_valid'),
        CheckConstraint('total_backtests >= 0', name='ck_total_backtests_non_negative'),
        CheckConstraint('successful_backtests >= 0', name='ck_successful_backtests_non_negative'),
        CheckConstraint('successful_backtests <= total_backtests', name='ck_successful_backtests_valid'),
    )
    
    @property
    def success_rate(self):
        """Calculate strategy success rate."""
        if self.total_backtests == 0:
            return 0.0
        return (self.successful_backtests / self.total_backtests) * 100

class StrategyParameter(BaseModel):
    """Strategy parameter definitions with PostgreSQL optimizations."""
    __tablename__ = 'strategy_parameters'
    
    # Foreign key
    strategy_id = Column(Integer, ForeignKey('strategies.id'), nullable=False, index=True)
    
    # Parameter definition
    parameter_name = Column(String(100), nullable=False)
    parameter_type = Column(String(20), nullable=False)  # int, float, string, boolean
    default_value = Column(String(200), nullable=True)
    min_value = Column(Numeric(15, 6), nullable=True)
    max_value = Column(Numeric(15, 6), nullable=True)
    
    # Parameter metadata
    description = Column(Text, nullable=True)
    is_required = Column(Boolean, default=True, nullable=False)
    is_tunable = Column(Boolean, default=True, nullable=False)  # Can be optimized
    
    # Parameter constraints stored as JSONB
    constraints = Column(JSONB, nullable=True)  # Additional parameter constraints
    
    # Relationships
    strategy = relationship("Strategy", back_populates="parameters_rel")
    
    # Indexes and constraints
    __table_args__ = (
        Index('idx_strategy_parameter_name', 'strategy_id', 'parameter_name'),
        CheckConstraint('parameter_type IN (\'int\', \'float\', \'string\', \'boolean\', \'list\')', name='ck_parameter_type_valid'),
    )

class StrategyPerformance(BaseModel):
    """Strategy performance metrics with PostgreSQL optimizations."""
    __tablename__ = 'strategy_performance'
    
    # Foreign key
    strategy_id = Column(Integer, ForeignKey('strategies.id'), nullable=False, unique=True)
    
    # Performance metrics - Using Numeric for precision
    total_return = Column(Numeric(15, 2), default=0.0, nullable=False)
    total_return_pct = Column(Numeric(8, 4), default=0.0, nullable=False)
    annualized_return = Column(Numeric(8, 4), default=0.0, nullable=False)
    
    # Risk metrics - Using Numeric for precision
    volatility = Column(Numeric(8, 4), default=0.0, nullable=False)
    sharpe_ratio = Column(Numeric(8, 4), default=0.0, nullable=False)
    sortino_ratio = Column(Numeric(8, 4), default=0.0, nullable=False)
    max_drawdown = Column(Numeric(8, 4), default=0.0, nullable=False)
    max_drawdown_duration = Column(Integer, default=0, nullable=False)  # Days
    
    # Trade statistics
    total_trades = Column(Integer, default=0, nullable=False)
    winning_trades = Column(Integer, default=0, nullable=False)
    losing_trades = Column(Integer, default=0, nullable=False)
    win_rate = Column(Numeric(5, 2), default=0.0, nullable=False)  # Percentage
    
    # Trade performance - Using Numeric for precision
    avg_win = Column(Numeric(15, 2), default=0.0, nullable=False)
    avg_loss = Column(Numeric(15, 2), default=0.0, nullable=False)
    profit_factor = Column(Numeric(8, 4), default=0.0, nullable=False)
    
    # Duration metrics
    avg_trade_duration = Column(Numeric(8, 2), default=0.0, nullable=False)  # Days
    avg_winning_trade_duration = Column(Numeric(8, 2), default=0.0, nullable=False)
    avg_losing_trade_duration = Column(Numeric(8, 2), default=0.0, nullable=False)
    
    # Market correlation
    market_correlation = Column(Numeric(8, 4), default=0.0, nullable=False)
    beta = Column(Numeric(8, 4), default=0.0, nullable=False)
    alpha = Column(Numeric(8, 4), default=0.0, nullable=False)
    
    # Performance periods
    last_30_days_return = Column(Numeric(8, 4), default=0.0, nullable=False)
    last_90_days_return = Column(Numeric(8, 4), default=0.0, nullable=False)
    last_365_days_return = Column(Numeric(8, 4), default=0.0, nullable=False)
    
    # Backtest metadata
    total_backtests_run = Column(Integer, default=0, nullable=False)
    last_backtest_date = Column(DateTime, nullable=True)
    best_backtest_return = Column(Numeric(8, 4), default=0.0, nullable=False)
    worst_backtest_return = Column(Numeric(8, 4), default=0.0, nullable=False)
    
    # Additional performance data stored as JSONB
    monthly_returns = Column(JSONB, nullable=True)  # Monthly return breakdown
    yearly_returns = Column(JSONB, nullable=True)   # Yearly return breakdown
    performance_attribution = Column(JSONB, nullable=True)  # Performance attribution analysis
    
    # Relationships
    strategy = relationship("Strategy", back_populates="performance")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('total_trades >= 0', name='ck_total_trades_non_negative'),
        CheckConstraint('winning_trades >= 0', name='ck_winning_trades_non_negative'),
        CheckConstraint('losing_trades >= 0', name='ck_losing_trades_non_negative'),
        CheckConstraint('winning_trades + losing_trades <= total_trades', name='ck_trades_sum_valid'),
        CheckConstraint('win_rate >= 0 AND win_rate <= 100', name='ck_win_rate_valid'),
        CheckConstraint('max_drawdown_duration >= 0', name='ck_max_drawdown_duration_non_negative'),
        CheckConstraint('avg_trade_duration >= 0', name='ck_avg_trade_duration_non_negative'),
        CheckConstraint('total_backtests_run >= 0', name='ck_total_backtests_run_non_negative'),
    )
    
    def calculate_win_rate(self):
        """Calculate win rate from trade statistics."""
        if self.total_trades == 0:
            self.win_rate = 0.0
        else:
            self.win_rate = (self.winning_trades / self.total_trades) * 100
    
    def calculate_profit_factor(self):
        """Calculate profit factor."""
        total_losses = abs(self.avg_loss * self.losing_trades) if self.losing_trades > 0 else 0
        if total_losses == 0:
            self.profit_factor = float('inf') if self.winning_trades > 0 else 0.0
        else:
            total_wins = self.avg_win * self.winning_trades
            self.profit_factor = total_wins / total_losses