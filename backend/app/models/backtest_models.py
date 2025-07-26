import json
from datetime import datetime
from .base import BaseModel
from ..db import db

class Backtest(BaseModel):
    """Backtest model for strategy backtesting with PostgreSQL optimizations."""
    __tablename__ = 'backtests'
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    strategy_id = db.Column(db.Integer, db.ForeignKey('strategies.id'), nullable=False, index=True)
    
    # Backtest identification
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # Backtest configuration
    start_date = db.Column(db.DateTime, nullable=False, index=True)
    end_date = db.Column(db.DateTime, nullable=False, index=True)
    initial_capital = db.Column(db.Numeric(15, 2), nullable=False)
    benchmark_symbol = db.Column(db.String(20), default='SPY', nullable=False)
    
    # Universe and filters
    universe = db.Column(db.JSON, nullable=False)  # List of symbols or universe definition
    filters = db.Column(db.JSON, nullable=True)    # Additional filters applied
    
    # Execution settings
    commission_model = db.Column(db.String(50), default='fixed', nullable=False)
    commission_rate = db.Column(db.Numeric(8, 4), default=0.001, nullable=False)  # 0.1% default
    slippage_model = db.Column(db.String(50), default='linear', nullable=False)
    slippage_rate = db.Column(db.Numeric(8, 4), default=0.001, nullable=False)
    
    # Position sizing
    position_sizing_method = db.Column(db.String(50), default='equal_weight', nullable=False)
    max_position_size = db.Column(db.Numeric(5, 2), default=10.0, nullable=False)  # % of portfolio
    max_positions = db.Column(db.Integer, default=20, nullable=False)
    
    # Backtest status
    status = db.Column(db.String(20), default='pending', nullable=False, index=True)
    progress = db.Column(db.Numeric(5, 2), default=0.0, nullable=False)  # 0-100%
    
    # Execution timestamps
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    duration_seconds = db.Column(db.Integer, nullable=True)
    
    # Results summary - Using Numeric for precision
    final_value = db.Column(db.Numeric(15, 2), nullable=True)
    total_return = db.Column(db.Numeric(15, 2), nullable=True)
    total_return_pct = db.Column(db.Numeric(8, 4), nullable=True)
    annualized_return = db.Column(db.Numeric(8, 4), nullable=True)
    
    # Risk metrics - Using Numeric for precision
    volatility = db.Column(db.Numeric(8, 4), nullable=True)
    sharpe_ratio = db.Column(db.Numeric(8, 4), nullable=True)
    sortino_ratio = db.Column(db.Numeric(8, 4), nullable=True)
    max_drawdown = db.Column(db.Numeric(8, 4), nullable=True)
    max_drawdown_duration = db.Column(db.Integer, nullable=True)
    
    # Benchmark comparison
    benchmark_return = db.Column(db.Numeric(8, 4), nullable=True)
    excess_return = db.Column(db.Numeric(8, 4), nullable=True)
    tracking_error = db.Column(db.Numeric(8, 4), nullable=True)
    information_ratio = db.Column(db.Numeric(8, 4), nullable=True)
    
    # Trade statistics
    total_trades = db.Column(db.Integer, default=0, nullable=False)
    winning_trades = db.Column(db.Integer, default=0, nullable=False)
    losing_trades = db.Column(db.Integer, default=0, nullable=False)
    win_rate = db.Column(db.Numeric(5, 2), default=0.0, nullable=False)
    
    # Error handling
    error_message = db.Column(db.Text, nullable=True)
    warnings = db.Column(db.JSON, nullable=True)  # Array of warning messages
    
    # Backtest configuration stored as JSON
    parameters = db.Column(db.JSON, nullable=True)  # Strategy parameters used
    settings = db.Column(db.JSON, nullable=True)    # Additional backtest settings
    
    # Relationships
    user = db.relationship("User")
    strategy = db.relationship("Strategy", back_populates="backtests")
    portfolios = db.relationship("Portfolio", back_populates="backtest")
    trades = db.relationship("Trade", back_populates="backtest", cascade="all, delete-orphan")
    signals = db.relationship("Signal", back_populates="backtest", cascade="all, delete-orphan")
    performance = db.relationship("BacktestPerformance", back_populates="backtest", uselist=False)
    
    # Indexes for performance
    __table_args__ = (
        db.Index('idx_backtest_user_strategy', 'user_id', 'strategy_id'),
        db.Index('idx_backtest_dates', 'start_date', 'end_date'),
        db.Index('idx_backtest_status_created', 'status', 'created_at'),
        db.Index('idx_backtest_completed_return', 'completed_at', 'total_return_pct'),
        db.CheckConstraint('initial_capital > 0', name='ck_initial_capital_positive'),
        db.CheckConstraint('commission_rate >= 0', name='ck_commission_rate_non_negative'),
        db.CheckConstraint('slippage_rate >= 0', name='ck_slippage_rate_non_negative'),
        db.CheckConstraint('max_position_size > 0 AND max_position_size <= 100', name='ck_max_position_size_valid'),
        db.CheckConstraint('max_positions > 0', name='ck_max_positions_positive'),
        db.CheckConstraint('progress >= 0 AND progress <= 100', name='ck_progress_valid'),
        db.CheckConstraint('end_date > start_date', name='ck_dates_valid'),
        db.CheckConstraint('status IN (\'pending\', \'running\', \'completed\', \'failed\', \'cancelled\')', name='ck_status_valid'),
        db.CheckConstraint('total_trades >= 0', name='ck_total_trades_non_negative'),
        db.CheckConstraint('winning_trades >= 0', name='ck_winning_trades_non_negative'),
        db.CheckConstraint('losing_trades >= 0', name='ck_losing_trades_non_negative'),
        db.CheckConstraint('win_rate >= 0 AND win_rate <= 100', name='ck_win_rate_valid'),
    )
    
    def calculate_metrics(self):
        """Calculate win rate and other derived metrics."""
        if self.total_trades > 0:
            self.win_rate = (self.winning_trades / self.total_trades) * 100
        
        if self.completed_at and self.started_at:
            self.duration_seconds = int((self.completed_at - self.started_at).total_seconds())
    
    @property
    def is_completed(self):
        """Check if backtest is completed."""
        return self.status == 'completed'
    
    @property
    def is_successful(self):
        """Check if backtest was successful (completed without major errors)."""
        return self.status == 'completed' and self.error_message is None

class Trade(BaseModel):
    """Trade model for backtest trade records with PostgreSQL optimizations."""
    __tablename__ = 'trades'
    
    # Foreign keys
    backtest_id = db.Column(db.Integer, db.ForeignKey('backtests.id'), nullable=False, index=True)
    symbol = db.Column(db.String(20), nullable=False, index=True)
    
    # Trade identification
    trade_id = db.Column(db.String(100), nullable=False, index=True)  # Unique per backtest
    signal_id = db.Column(db.String(100), nullable=True, index=True)   # Related signal
    
    # Trade details
    direction = db.Column(db.String(10), nullable=False, index=True)  # LONG, SHORT
    quantity = db.Column(db.Numeric(15, 6), nullable=False)
    
    # Entry details - Using Numeric for precision
    entry_date = db.Column(db.DateTime, nullable=False, index=True)
    entry_price = db.Column(db.Numeric(10, 4), nullable=False)
    entry_value = db.Column(db.Numeric(15, 2), nullable=False)
    
    # Exit details - Using Numeric for precision
    exit_date = db.Column(db.DateTime, nullable=True, index=True)
    exit_price = db.Column(db.Numeric(10, 4), nullable=True)
    exit_value = db.Column(db.Numeric(15, 2), nullable=True)
    exit_reason = db.Column(db.String(50), nullable=True)  # stop_loss, take_profit, signal, etc.
    
    # Trade performance - Using Numeric for precision
    pnl = db.Column(db.Numeric(15, 2), nullable=True)
    pnl_pct = db.Column(db.Numeric(8, 4), nullable=True)
    
    # Costs - Using Numeric for precision
    entry_commission = db.Column(db.Numeric(10, 2), default=0.0, nullable=False)
    exit_commission = db.Column(db.Numeric(10, 2), default=0.0, nullable=False)
    entry_slippage = db.Column(db.Numeric(10, 2), default=0.0, nullable=False)
    exit_slippage = db.Column(db.Numeric(10, 2), default=0.0, nullable=False)
    
    # Trade metadata
    is_open = db.Column(db.Boolean, default=True, nullable=False, index=True)
    duration_days = db.Column(db.Numeric(8, 2), nullable=True)
    
    # Risk metrics
    max_adverse_excursion = db.Column(db.Numeric(15, 2), nullable=True)
    max_favorable_excursion = db.Column(db.Numeric(15, 2), nullable=True)
    
    # Additional trade data stored as JSON
    entry_conditions = db.Column(db.JSON, nullable=True)  # Conditions that triggered entry
    exit_conditions = db.Column(db.JSON, nullable=True)   # Conditions that triggered exit
    additional_metadata = db.Column(db.JSON, nullable=True)          # Additional trade metadata
    
    # Relationships
    backtest = db.relationship("Backtest", back_populates="trades")
    
    # Indexes for performance
    __table_args__ = (
        db.Index('idx_trade_backtest_symbol_date', 'backtest_id', 'symbol', 'entry_date'),
        db.Index('idx_trade_entry_exit_dates', 'entry_date', 'exit_date'),
        db.Index('idx_trade_direction_open', 'direction', 'is_open'),
        db.Index('idx_trade_pnl', 'pnl'),
        db.CheckConstraint('quantity > 0', name='ck_quantity_positive'),
        db.CheckConstraint('entry_price > 0', name='ck_entry_price_positive'),
        db.CheckConstraint('entry_value > 0', name='ck_entry_value_positive'),
        db.CheckConstraint('exit_price > 0 OR exit_price IS NULL', name='ck_exit_price_positive_or_null'),
        db.CheckConstraint('direction IN (\'LONG\', \'SHORT\')', name='ck_direction_valid'),
        db.CheckConstraint('entry_commission >= 0', name='ck_entry_commission_non_negative'),
        db.CheckConstraint('exit_commission >= 0', name='ck_exit_commission_non_negative'),
        db.CheckConstraint('entry_slippage >= 0', name='ck_entry_slippage_non_negative'),
        db.CheckConstraint('exit_slippage >= 0', name='ck_exit_slippage_non_negative'),
    )
    
    def calculate_pnl(self):
        """Calculate P&L when trade is closed."""
        if self.exit_price is not None and self.exit_value is not None:
            if self.direction == 'LONG':
                self.pnl = self.exit_value - self.entry_value
            else:  # SHORT
                self.pnl = self.entry_value - self.exit_value
            
            # Subtract commissions and slippage
            total_costs = self.entry_commission + self.exit_commission + self.entry_slippage + self.exit_slippage
            self.pnl -= total_costs
            
            # Calculate percentage return
            if self.entry_value > 0:
                self.pnl_pct = (self.pnl / self.entry_value) * 100
            
            self.is_open = False
    
    def calculate_duration(self):
        """Calculate trade duration in days."""
        if self.exit_date:
            duration = self.exit_date - self.entry_date
            self.duration_days = duration.total_seconds() / 86400  # Convert to days

class Signal(BaseModel):
    """Signal model for strategy signals with PostgreSQL optimizations."""
    __tablename__ = 'signals'
    
    # Foreign keys
    backtest_id = db.Column(db.Integer, db.ForeignKey('backtests.id'), nullable=False, index=True)
    symbol = db.Column(db.String(20), nullable=False, index=True)
    
    # Signal identification
    signal_id = db.Column(db.String(100), nullable=False, index=True)
    signal_type = db.Column(db.String(20), nullable=False, index=True)  # BUY, SELL, HOLD
    
    # Signal details
    signal_date = db.Column(db.DateTime, nullable=False, index=True)
    signal_price = db.Column(db.Numeric(10, 4), nullable=False)
    confidence = db.Column(db.Numeric(5, 4), default=1.0, nullable=False)  # 0.0 to 1.0
    
    # Signal strength and ranking
    strength = db.Column(db.Numeric(8, 4), default=0.0, nullable=False)  # Relative signal strength
    rank = db.Column(db.Integer, nullable=True)  # Signal rank among all signals on this date
    
    # Position sizing suggestion
    suggested_quantity = db.Column(db.Numeric(15, 6), nullable=True)
    suggested_weight = db.Column(db.Numeric(5, 2), nullable=True)  # % of portfolio
    
    # Signal conditions and metadata stored as JSON
    conditions = db.Column(db.JSON, nullable=False)  # Conditions that generated the signal
    indicators = db.Column(db.JSON, nullable=True)   # Technical indicators values
    additional_metadata = db.Column(db.JSON, nullable=True)     # Additional signal data
    
    # Signal execution
    was_executed = db.Column(db.Boolean, default=False, nullable=False, index=True)
    execution_delay = db.Column(db.Integer, nullable=True)  # Bars/periods delay
    execution_price = db.Column(db.Numeric(10, 4), nullable=True)
    execution_slippage = db.Column(db.Numeric(10, 2), nullable=True)
    
    # Relationships
    backtest = db.relationship("Backtest", back_populates="signals")
    
    # Indexes for performance
    __table_args__ = (
        db.Index('idx_signal_backtest_date_type', 'backtest_id', 'signal_date', 'signal_type'),
        db.Index('idx_signal_symbol_date', 'symbol', 'signal_date'),
        db.Index('idx_signal_executed_confidence', 'was_executed', 'confidence'),
        db.Index('idx_signal_strength_rank', 'strength', 'rank'),
        db.CheckConstraint('signal_price > 0', name='ck_signal_price_positive'),
        db.CheckConstraint('confidence >= 0 AND confidence <= 1', name='ck_confidence_valid'),
        db.CheckConstraint('suggested_weight >= 0 AND suggested_weight <= 100 OR suggested_weight IS NULL', name='ck_suggested_weight_valid'),
        db.CheckConstraint('signal_type IN (\'BUY\', \'SELL\', \'HOLD\', \'CLOSE\')', name='ck_signal_type_valid'),
        db.CheckConstraint('execution_delay >= 0 OR execution_delay IS NULL', name='ck_execution_delay_non_negative'),
        db.CheckConstraint('execution_price > 0 OR execution_price IS NULL', name='ck_execution_price_positive_or_null'),
    )

class BacktestPerformance(BaseModel):
    """Backtest performance metrics with PostgreSQL optimizations."""
    __tablename__ = 'backtest_performance'
    
    # Foreign key
    backtest_id = db.Column(db.Integer, db.ForeignKey('backtests.id'), nullable=False, unique=True, index=True)
    
    # Performance metrics - Using Numeric for financial precision
    total_return = db.Column(db.Numeric(15, 2), nullable=False)
    total_return_pct = db.Column(db.Numeric(8, 4), nullable=False)
    annualized_return = db.Column(db.Numeric(8, 4), nullable=False)
    
    # Risk metrics
    volatility = db.Column(db.Numeric(8, 4), nullable=False)
    sharpe_ratio = db.Column(db.Numeric(8, 4), nullable=True)
    sortino_ratio = db.Column(db.Numeric(8, 4), nullable=True)
    max_drawdown = db.Column(db.Numeric(8, 4), nullable=False)
    max_drawdown_duration = db.Column(db.Integer, nullable=True)  # Days
    
    # Trade statistics
    total_trades = db.Column(db.Integer, default=0, nullable=False)
    winning_trades = db.Column(db.Integer, default=0, nullable=False)
    losing_trades = db.Column(db.Integer, default=0, nullable=False)
    win_rate = db.Column(db.Numeric(8, 4), nullable=True)
    avg_win = db.Column(db.Numeric(15, 2), nullable=True)
    avg_loss = db.Column(db.Numeric(15, 2), nullable=True)
    profit_factor = db.Column(db.Numeric(8, 4), nullable=True)
    
    # Benchmark comparison
    benchmark_return = db.Column(db.Numeric(8, 4), nullable=True)
    alpha = db.Column(db.Numeric(8, 4), nullable=True)
    beta = db.Column(db.Numeric(8, 4), nullable=True)
    correlation = db.Column(db.Numeric(8, 4), nullable=True)
    sortino_ratio = db.Column(db.Float, nullable=True)         # ✅ Newly added
    calmar_ratio = db.Column(db.Float, nullable=True)          # ✅ Newly added
    avg_holding_period = db.Column(db.Float, nullable=True)   
    # Additional metrics stored as JSON
    additional_metrics = db.Column(db.JSON, nullable=True)
    
    # Relationships
    backtest = db.relationship("Backtest", back_populates="performance")
    
    # Constraints
    __table_args__ = (
        db.CheckConstraint('total_trades >= 0', name='ck_total_trades_non_negative'),
        db.CheckConstraint('winning_trades >= 0', name='ck_winning_trades_non_negative'),
        db.CheckConstraint('losing_trades >= 0', name='ck_losing_trades_non_negative'),
        db.CheckConstraint('winning_trades + losing_trades <= total_trades', name='ck_trade_counts_valid'),
    )


class BacktestLog(BaseModel):
    """Backtest execution log for debugging and analysis."""
    __tablename__ = 'backtest_logs'
    
    # Foreign key
    backtest_id = db.Column(db.Integer, db.ForeignKey('backtests.id'), nullable=False, index=True)
    
    # Log details
    log_level = db.Column(db.String(10), nullable=False, index=True)  # DEBUG, INFO, WARN, ERROR
    message = db.Column(db.Text, nullable=False)
    module = db.Column(db.String(100), nullable=True)
    function_name = db.Column(db.String(100), nullable=True)
    
    # Timing
    log_timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    simulation_date = db.Column(db.DateTime, nullable=True, index=True)  # Date in simulation
    
    # Context
    symbol = db.Column(db.String(20), nullable=True, index=True)
    trade_id = db.Column(db.Integer, db.ForeignKey('trades.id'), nullable=True)
    additional_context = db.Column(db.JSON, nullable=True)
    
    # Relationships
    backtest = db.relationship("Backtest", backref="logs")
    trade = db.relationship("Trade", backref="logs")
    
    # Indexes
    __table_args__ = (
        db.Index('idx_backtest_log_level_timestamp', 'backtest_id', 'log_level', 'log_timestamp'),
        db.Index('idx_backtest_log_simulation_date', 'backtest_id', 'simulation_date'),
        db.CheckConstraint('log_level IN (\'DEBUG\', \'INFO\', \'WARN\', \'ERROR\')', name='ck_log_level_valid'),
    )


class BacktestComparison(BaseModel):
    """Backtest comparison for analyzing multiple strategy results."""
    __tablename__ = 'backtest_comparisons'
    
    # Comparison metadata
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    comparison_type = db.Column(db.String(50), default='performance', nullable=False)
    
    # Backtests being compared (stored as array of IDs)
    backtest_ids = db.Column(db.JSON, nullable=False)  # Array of backtest IDs
    
    # Comparison results
    results = db.Column(db.JSON, nullable=True)  # Detailed comparison results
    summary = db.Column(db.JSON, nullable=True)  # Summary statistics
    
    # Analysis metadata
    analysis_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    analysis_parameters = db.Column(db.JSON, nullable=True)
    
    # Status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Constraints
    __table_args__ = (
        db.Index('idx_comparison_type_date', 'comparison_type', 'analysis_date'),
        db.CheckConstraint('comparison_type IN (\'performance\', \'risk\', \'correlation\', \'optimization\')', name='ck_comparison_type_valid'),
    )