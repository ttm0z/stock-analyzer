from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Index, CheckConstraint, Numeric, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from .base import BaseModel

class Backtest(BaseModel):
    """Backtest model for strategy backtesting with PostgreSQL optimizations."""
    __tablename__ = 'backtests'
    
    # Foreign keys
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    strategy_id = Column(Integer, ForeignKey('strategies.id'), nullable=False, index=True)
    
    # Backtest identification
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    # Backtest configuration
    start_date = Column(DateTime, nullable=False, index=True)
    end_date = Column(DateTime, nullable=False, index=True)
    initial_capital = Column(Numeric(15, 2), nullable=False)
    benchmark_symbol = Column(String(20), default='SPY', nullable=False)
    
    # Universe and filters
    universe = Column(JSONB, nullable=False)  # List of symbols or universe definition
    filters = Column(JSONB, nullable=True)    # Additional filters applied
    
    # Execution settings
    commission_model = Column(String(50), default='fixed', nullable=False)
    commission_rate = Column(Numeric(8, 4), default=0.001, nullable=False)  # 0.1% default
    slippage_model = Column(String(50), default='linear', nullable=False)
    slippage_rate = Column(Numeric(8, 4), default=0.001, nullable=False)
    
    # Position sizing
    position_sizing_method = Column(String(50), default='equal_weight', nullable=False)
    max_position_size = Column(Numeric(5, 2), default=10.0, nullable=False)  # % of portfolio
    max_positions = Column(Integer, default=20, nullable=False)
    
    # Backtest status
    status = Column(String(20), default='pending', nullable=False, index=True)
    progress = Column(Numeric(5, 2), default=0.0, nullable=False)  # 0-100%
    
    # Execution timestamps
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    
    # Results summary - Using Numeric for precision
    final_value = Column(Numeric(15, 2), nullable=True)
    total_return = Column(Numeric(15, 2), nullable=True)
    total_return_pct = Column(Numeric(8, 4), nullable=True)
    annualized_return = Column(Numeric(8, 4), nullable=True)
    
    # Risk metrics - Using Numeric for precision
    volatility = Column(Numeric(8, 4), nullable=True)
    sharpe_ratio = Column(Numeric(8, 4), nullable=True)
    sortino_ratio = Column(Numeric(8, 4), nullable=True)
    max_drawdown = Column(Numeric(8, 4), nullable=True)
    max_drawdown_duration = Column(Integer, nullable=True)
    
    # Benchmark comparison
    benchmark_return = Column(Numeric(8, 4), nullable=True)
    excess_return = Column(Numeric(8, 4), nullable=True)
    tracking_error = Column(Numeric(8, 4), nullable=True)
    information_ratio = Column(Numeric(8, 4), nullable=True)
    
    # Trade statistics
    total_trades = Column(Integer, default=0, nullable=False)
    winning_trades = Column(Integer, default=0, nullable=False)
    losing_trades = Column(Integer, default=0, nullable=False)
    win_rate = Column(Numeric(5, 2), default=0.0, nullable=False)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    warnings = Column(JSONB, nullable=True)  # Array of warning messages
    
    # Backtest configuration stored as JSONB
    parameters = Column(JSONB, nullable=True)  # Strategy parameters used
    settings = Column(JSONB, nullable=True)    # Additional backtest settings
    
    # Relationships
    user = relationship("User")
    strategy = relationship("Strategy", back_populates="backtests")
    portfolios = relationship("Portfolio", back_populates="backtest")
    trades = relationship("Trade", back_populates="backtest", cascade="all, delete-orphan")
    signals = relationship("Signal", back_populates="backtest", cascade="all, delete-orphan")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_backtest_user_strategy', 'user_id', 'strategy_id'),
        Index('idx_backtest_dates', 'start_date', 'end_date'),
        Index('idx_backtest_status_created', 'status', 'created_at'),
        Index('idx_backtest_completed_return', 'completed_at', 'total_return_pct'),
        CheckConstraint('initial_capital > 0', name='ck_initial_capital_positive'),
        CheckConstraint('commission_rate >= 0', name='ck_commission_rate_non_negative'),
        CheckConstraint('slippage_rate >= 0', name='ck_slippage_rate_non_negative'),
        CheckConstraint('max_position_size > 0 AND max_position_size <= 100', name='ck_max_position_size_valid'),
        CheckConstraint('max_positions > 0', name='ck_max_positions_positive'),
        CheckConstraint('progress >= 0 AND progress <= 100', name='ck_progress_valid'),
        CheckConstraint('end_date > start_date', name='ck_dates_valid'),
        CheckConstraint('status IN (\'pending\', \'running\', \'completed\', \'failed\', \'cancelled\')', name='ck_status_valid'),
        CheckConstraint('total_trades >= 0', name='ck_total_trades_non_negative'),
        CheckConstraint('winning_trades >= 0', name='ck_winning_trades_non_negative'),
        CheckConstraint('losing_trades >= 0', name='ck_losing_trades_non_negative'),
        CheckConstraint('win_rate >= 0 AND win_rate <= 100', name='ck_win_rate_valid'),
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
    backtest_id = Column(Integer, ForeignKey('backtests.id'), nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    
    # Trade identification
    trade_id = Column(String(100), nullable=False, index=True)  # Unique per backtest
    signal_id = Column(String(100), nullable=True, index=True)   # Related signal
    
    # Trade details
    direction = Column(String(10), nullable=False, index=True)  # LONG, SHORT
    quantity = Column(Numeric(15, 6), nullable=False)
    
    # Entry details - Using Numeric for precision
    entry_date = Column(DateTime, nullable=False, index=True)
    entry_price = Column(Numeric(10, 4), nullable=False)
    entry_value = Column(Numeric(15, 2), nullable=False)
    
    # Exit details - Using Numeric for precision
    exit_date = Column(DateTime, nullable=True, index=True)
    exit_price = Column(Numeric(10, 4), nullable=True)
    exit_value = Column(Numeric(15, 2), nullable=True)
    exit_reason = Column(String(50), nullable=True)  # stop_loss, take_profit, signal, etc.
    
    # Trade performance - Using Numeric for precision
    pnl = Column(Numeric(15, 2), nullable=True)
    pnl_pct = Column(Numeric(8, 4), nullable=True)
    
    # Costs - Using Numeric for precision
    entry_commission = Column(Numeric(10, 2), default=0.0, nullable=False)
    exit_commission = Column(Numeric(10, 2), default=0.0, nullable=False)
    entry_slippage = Column(Numeric(10, 2), default=0.0, nullable=False)
    exit_slippage = Column(Numeric(10, 2), default=0.0, nullable=False)
    
    # Trade metadata
    is_open = Column(Boolean, default=True, nullable=False, index=True)
    duration_days = Column(Numeric(8, 2), nullable=True)
    
    # Risk metrics
    max_adverse_excursion = Column(Numeric(15, 2), nullable=True)
    max_favorable_excursion = Column(Numeric(15, 2), nullable=True)
    
    # Additional trade data stored as JSONB
    entry_conditions = Column(JSONB, nullable=True)  # Conditions that triggered entry
    exit_conditions = Column(JSONB, nullable=True)   # Conditions that triggered exit
    metadata = Column(JSONB, nullable=True)          # Additional trade metadata
    
    # Relationships
    backtest = relationship("Backtest", back_populates="trades")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_trade_backtest_symbol_date', 'backtest_id', 'symbol', 'entry_date'),
        Index('idx_trade_entry_exit_dates', 'entry_date', 'exit_date'),
        Index('idx_trade_direction_open', 'direction', 'is_open'),
        Index('idx_trade_pnl', 'pnl'),
        CheckConstraint('quantity > 0', name='ck_quantity_positive'),
        CheckConstraint('entry_price > 0', name='ck_entry_price_positive'),
        CheckConstraint('entry_value > 0', name='ck_entry_value_positive'),
        CheckConstraint('exit_price > 0 OR exit_price IS NULL', name='ck_exit_price_positive_or_null'),
        CheckConstraint('direction IN (\'LONG\', \'SHORT\')', name='ck_direction_valid'),
        CheckConstraint('entry_commission >= 0', name='ck_entry_commission_non_negative'),
        CheckConstraint('exit_commission >= 0', name='ck_exit_commission_non_negative'),
        CheckConstraint('entry_slippage >= 0', name='ck_entry_slippage_non_negative'),
        CheckConstraint('exit_slippage >= 0', name='ck_exit_slippage_non_negative'),
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
    backtest_id = Column(Integer, ForeignKey('backtests.id'), nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    
    # Signal identification
    signal_id = Column(String(100), nullable=False, index=True)
    signal_type = Column(String(20), nullable=False, index=True)  # BUY, SELL, HOLD
    
    # Signal details
    signal_date = Column(DateTime, nullable=False, index=True)
    signal_price = Column(Numeric(10, 4), nullable=False)
    confidence = Column(Numeric(5, 4), default=1.0, nullable=False)  # 0.0 to 1.0
    
    # Signal strength and ranking
    strength = Column(Numeric(8, 4), default=0.0, nullable=False)  # Relative signal strength
    rank = Column(Integer, nullable=True)  # Signal rank among all signals on this date
    
    # Position sizing suggestion
    suggested_quantity = Column(Numeric(15, 6), nullable=True)
    suggested_weight = Column(Numeric(5, 2), nullable=True)  # % of portfolio
    
    # Signal conditions and metadata stored as JSONB
    conditions = Column(JSONB, nullable=False)  # Conditions that generated the signal
    indicators = Column(JSONB, nullable=True)   # Technical indicators values
    metadata = Column(JSONB, nullable=True)     # Additional signal data
    
    # Signal execution
    was_executed = Column(Boolean, default=False, nullable=False, index=True)
    execution_delay = Column(Integer, nullable=True)  # Bars/periods delay
    execution_price = Column(Numeric(10, 4), nullable=True)
    execution_slippage = Column(Numeric(10, 2), nullable=True)
    
    # Relationships
    backtest = relationship("Backtest", back_populates="signals")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_signal_backtest_date_type', 'backtest_id', 'signal_date', 'signal_type'),
        Index('idx_signal_symbol_date', 'symbol', 'signal_date'),
        Index('idx_signal_executed_confidence', 'was_executed', 'confidence'),
        Index('idx_signal_strength_rank', 'strength', 'rank'),
        CheckConstraint('signal_price > 0', name='ck_signal_price_positive'),
        CheckConstraint('confidence >= 0 AND confidence <= 1', name='ck_confidence_valid'),
        CheckConstraint('suggested_weight >= 0 AND suggested_weight <= 100 OR suggested_weight IS NULL', name='ck_suggested_weight_valid'),
        CheckConstraint('signal_type IN (\'BUY\', \'SELL\', \'HOLD\', \'CLOSE\')', name='ck_signal_type_valid'),
        CheckConstraint('execution_delay >= 0 OR execution_delay IS NULL', name='ck_execution_delay_non_negative'),
        CheckConstraint('execution_price > 0 OR execution_price IS NULL', name='ck_execution_price_positive_or_null'),
    )