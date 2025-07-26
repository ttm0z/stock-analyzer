from datetime import datetime
from .base import BaseModel
from ..db import db

class Strategy(BaseModel):
    """Strategy model for trading strategies with PostgreSQL optimizations."""
    __tablename__ = 'strategies'
    
    # Foreign key
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Basic strategy information
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    strategy_type = db.Column(db.String(50), nullable=False, index=True)  # momentum, mean_reversion, etc.
    
    # Strategy classification
    category = db.Column(db.String(50), nullable=False, index=True)  # equity, options, crypto, etc.
    complexity = db.Column(db.String(20), default='intermediate', nullable=False)  # beginner, intermediate, advanced
    
    # Strategy configuration stored as JSON
    parameters = db.Column(db.JSON, nullable=False)  # Strategy-specific parameters
    entry_rules = db.Column(db.JSON, nullable=False)  # Entry condition rules
    exit_rules = db.Column(db.JSON, nullable=False)   # Exit condition rules
    risk_rules = db.Column(db.JSON, nullable=True)    # Risk management rules
    
    # Strategy metadata
    version = db.Column(db.String(20), default='1.0.0', nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)
    is_public = db.Column(db.Boolean, default=False, nullable=False)
    
    # Performance tracking
    total_backtests = db.Column(db.Integer, default=0, nullable=False)
    successful_backtests = db.Column(db.Integer, default=0, nullable=False)
    
    # Strategy source code (for custom strategies)
    source_code = db.Column(db.Text, nullable=True)
    code_language = db.Column(db.String(20), default='python', nullable=False)
    
    # Tags and categorization
    tags = db.Column(db.JSON, nullable=True)  # Array of tags
    
    # Relationships
    user = db.relationship("User", back_populates="strategies")
    parameters_rel = db.relationship("StrategyParameter", back_populates="strategy", cascade="all, delete-orphan")
    backtests = db.relationship("Backtest", back_populates="strategy", cascade="all, delete-orphan")
    performance = db.relationship("StrategyPerformance", back_populates="strategy", uselist=False, cascade="all, delete-orphan")
    
    # Indexes for performance
    __table_args__ = (
        db.Index('idx_strategy_user_type_active', 'user_id', 'strategy_type', 'is_active'),
        db.Index('idx_strategy_category_public', 'category', 'is_public'),
        db.Index('idx_strategy_complexity', 'complexity'),
        db.CheckConstraint('complexity IN (\'beginner\', \'intermediate\', \'advanced\')', name='ck_complexity_valid'),
        db.CheckConstraint('total_backtests >= 0', name='ck_total_backtests_non_negative'),
        db.CheckConstraint('successful_backtests >= 0', name='ck_successful_backtests_non_negative'),
        db.CheckConstraint('successful_backtests <= total_backtests', name='ck_successful_backtests_valid'),
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
    strategy_id = db.Column(db.Integer, db.ForeignKey('strategies.id'), nullable=False, index=True)
    
    # Parameter definition
    parameter_name = db.Column(db.String(100), nullable=False)
    parameter_type = db.Column(db.String(20), nullable=False)  # int, float, string, boolean
    default_value = db.Column(db.String(200), nullable=True)
    min_value = db.Column(db.Numeric(15, 6), nullable=True)
    max_value = db.Column(db.Numeric(15, 6), nullable=True)
    
    # Parameter metadata
    description = db.Column(db.Text, nullable=True)
    is_required = db.Column(db.Boolean, default=True, nullable=False)
    is_tunable = db.Column(db.Boolean, default=True, nullable=False)  # Can be optimized
    
    # Parameter constraints stored as JSON
    constraints = db.Column(db.JSON, nullable=True)  # Additional parameter constraints
    
    # Relationships
    strategy = db.relationship("Strategy", back_populates="parameters_rel")
    
    # Indexes and constraints
    __table_args__ = (
        db.Index('idx_strategy_parameter_name', 'strategy_id', 'parameter_name'),
        db.CheckConstraint('parameter_type IN (\'int\', \'float\', \'string\', \'boolean\', \'list\')', name='ck_parameter_type_valid'),
    )

class StrategyPerformance(BaseModel):
    """Strategy performance metrics with PostgreSQL optimizations."""
    __tablename__ = 'strategy_performance'
    
    # Foreign key
    strategy_id = db.Column(db.Integer, db.ForeignKey('strategies.id'), nullable=False, unique=True)
    
    # Performance metrics - Using Numeric for precision
    total_return = db.Column(db.Numeric(15, 2), default=0.0, nullable=False)
    total_return_pct = db.Column(db.Numeric(8, 4), default=0.0, nullable=False)
    annualized_return = db.Column(db.Numeric(8, 4), default=0.0, nullable=False)
    
    # Risk metrics - Using Numeric for precision
    volatility = db.Column(db.Numeric(8, 4), default=0.0, nullable=False)
    sharpe_ratio = db.Column(db.Numeric(8, 4), default=0.0, nullable=False)
    sortino_ratio = db.Column(db.Numeric(8, 4), default=0.0, nullable=False)
    max_drawdown = db.Column(db.Numeric(8, 4), default=0.0, nullable=False)
    max_drawdown_duration = db.Column(db.Integer, default=0, nullable=False)  # Days
    
    # Trade statistics
    total_trades = db.Column(db.Integer, default=0, nullable=False)
    winning_trades = db.Column(db.Integer, default=0, nullable=False)
    losing_trades = db.Column(db.Integer, default=0, nullable=False)
    win_rate = db.Column(db.Numeric(5, 2), default=0.0, nullable=False)  # Percentage
    
    # Trade performance - Using Numeric for precision
    avg_win = db.Column(db.Numeric(15, 2), default=0.0, nullable=False)
    avg_loss = db.Column(db.Numeric(15, 2), default=0.0, nullable=False)
    profit_factor = db.Column(db.Numeric(8, 4), default=0.0, nullable=False)
    
    # Duration metrics
    avg_trade_duration = db.Column(db.Numeric(8, 2), default=0.0, nullable=False)  # Days
    avg_winning_trade_duration = db.Column(db.Numeric(8, 2), default=0.0, nullable=False)
    avg_losing_trade_duration = db.Column(db.Numeric(8, 2), default=0.0, nullable=False)
    
    # Market correlation
    market_correlation = db.Column(db.Numeric(8, 4), default=0.0, nullable=False)
    beta = db.Column(db.Numeric(8, 4), default=0.0, nullable=False)
    alpha = db.Column(db.Numeric(8, 4), default=0.0, nullable=False)
    
    # Performance periods
    last_30_days_return = db.Column(db.Numeric(8, 4), default=0.0, nullable=False)
    last_90_days_return = db.Column(db.Numeric(8, 4), default=0.0, nullable=False)
    last_365_days_return = db.Column(db.Numeric(8, 4), default=0.0, nullable=False)
    
    # Backtest metadata
    total_backtests_run = db.Column(db.Integer, default=0, nullable=False)
    last_backtest_date = db.Column(db.DateTime, nullable=True)
    best_backtest_return = db.Column(db.Numeric(8, 4), default=0.0, nullable=False)
    worst_backtest_return = db.Column(db.Numeric(8, 4), default=0.0, nullable=False)
    
    # Additional performance data stored as JSON
    monthly_returns = db.Column(db.JSON, nullable=True)  # Monthly return breakdown
    yearly_returns = db.Column(db.JSON, nullable=True)   # Yearly return breakdown
    performance_attribution = db.Column(db.JSON, nullable=True)  # Performance attribution analysis
    
    # Relationships
    strategy = db.relationship("Strategy", back_populates="performance")
    
    # Constraints
    __table_args__ = (
        db.CheckConstraint('total_trades >= 0', name='ck_total_trades_non_negative'),
        db.CheckConstraint('winning_trades >= 0', name='ck_winning_trades_non_negative'),
        db.CheckConstraint('losing_trades >= 0', name='ck_losing_trades_non_negative'),
        db.CheckConstraint('winning_trades + losing_trades <= total_trades', name='ck_trades_sum_valid'),
        db.CheckConstraint('win_rate >= 0 AND win_rate <= 100', name='ck_win_rate_valid'),
        db.CheckConstraint('max_drawdown_duration >= 0', name='ck_max_drawdown_duration_non_negative'),
        db.CheckConstraint('avg_trade_duration >= 0', name='ck_avg_trade_duration_non_negative'),
        db.CheckConstraint('total_backtests_run >= 0', name='ck_total_backtests_run_non_negative'),
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

class StrategyTemplate(BaseModel):
    """Pre-built strategy templates."""
    __tablename__ = 'strategy_templates'
    
    # Template identification
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), nullable=False, index=True)  # MOMENTUM, MEAN_REVERSION, etc.
    
    # Template code and configuration
    code_template = db.Column(db.Text, nullable=False)  # Python code template
    default_parameters = db.Column(db.JSON, nullable=True)  # Default parameter values
    parameter_schema = db.Column(db.JSON, nullable=True)  # Parameter validation schema
    
    # Metadata
    author = db.Column(db.String(100), nullable=True)
    version = db.Column(db.String(20), default='1.0', nullable=False)
    is_public = db.Column(db.Boolean, default=True, nullable=False)
    
    # Status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Constraints
    __table_args__ = (
        db.Index('idx_template_category_active', 'category', 'is_active'),
        db.CheckConstraint('category IN (\'MOMENTUM\', \'MEAN_REVERSION\', \'BREAKOUT\', \'ARBITRAGE\', \'OTHER\')', name='ck_category_valid'),
    )


class StrategyLibrary(BaseModel):
    """Strategy library for organizing and sharing strategies."""
    __tablename__ = 'strategy_library'
    
    # Library organization
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    library_type = db.Column(db.String(50), default='USER', nullable=False)  # USER, COMMUNITY, OFFICIAL
    
    # Access control
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    is_public = db.Column(db.Boolean, default=False, nullable=False)
    access_level = db.Column(db.String(20), default='PRIVATE', nullable=False)  # PRIVATE, SHARED, PUBLIC
    
    # Library contents (array of strategy IDs)
    strategy_ids = db.Column(db.JSON, nullable=True)  # Array of strategy IDs
    
    # Metadata
    tags = db.Column(db.JSON, nullable=True)  # Array of tags
    
    # Status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Relationships
    owner = db.relationship("User", backref="strategy_libraries")
    
    # Constraints
    __table_args__ = (
        db.Index('idx_library_owner_type', 'owner_id', 'library_type'),
        db.CheckConstraint('library_type IN (\'USER\', \'COMMUNITY\', \'OFFICIAL\')', name='ck_library_type_valid'),
        db.CheckConstraint('access_level IN (\'PRIVATE\', \'SHARED\', \'PUBLIC\')', name='ck_access_level_valid'),
    )


class StrategyValidation(BaseModel):
    """Strategy validation results and metrics."""
    __tablename__ = 'strategy_validation'
    
    # Foreign key
    strategy_id = db.Column(db.Integer, db.ForeignKey('strategies.id'), nullable=False, index=True)
    
    # Validation type and status
    validation_type = db.Column(db.String(50), nullable=False, index=True)  # SYNTAX, LOGIC, PERFORMANCE, RISK
    validation_status = db.Column(db.String(20), nullable=False, index=True)  # PASSED, FAILED, WARNING
    
    # Validation results
    score = db.Column(db.Numeric(5, 2), nullable=True)  # 0-100 validation score
    issues = db.Column(db.JSON, nullable=True)  # Array of validation issues
    recommendations = db.Column(db.JSON, nullable=True)  # Array of improvement recommendations
    
    # Validation metadata
    validation_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    validator_version = db.Column(db.String(20), nullable=True)
    validation_parameters = db.Column(db.JSON, nullable=True)
    
    # Detailed results
    detailed_results = db.Column(db.JSON, nullable=True)  # Full validation report
    
    # Relationships
    strategy = db.relationship("Strategy", backref="validations")
    
    # Constraints
    __table_args__ = (
        db.Index('idx_validation_strategy_type_status', 'strategy_id', 'validation_type', 'validation_status'),
        db.Index('idx_validation_date_status', 'validation_date', 'validation_status'),
        db.CheckConstraint('validation_type IN (\'SYNTAX\', \'LOGIC\', \'PERFORMANCE\', \'RISK\', \'COMPLIANCE\')', name='ck_validation_type_valid'),
        db.CheckConstraint('validation_status IN (\'PASSED\', \'FAILED\', \'WARNING\', \'PENDING\')', name='ck_validation_status_valid'),
        db.CheckConstraint('score BETWEEN 0 AND 100 OR score IS NULL', name='ck_score_valid'),
    )