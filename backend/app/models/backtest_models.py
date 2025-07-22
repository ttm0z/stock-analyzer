from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.sqlite import JSON
from datetime import datetime
import json

from .base import BaseModel

class Backtest(BaseModel):
    """Backtest configuration and results"""
    __tablename__ = 'backtests'
    
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    strategy_id = Column(Integer, ForeignKey('strategies.id'), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    # Backtest configuration
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    initial_capital = Column(Float, nullable=False)
    currency = Column(String(10), default='USD', nullable=False)
    
    # Trading parameters
    commission_rate = Column(Float, default=0.001, nullable=False)  # 0.1%
    slippage_rate = Column(Float, default=0.0005, nullable=False)  # 0.05%
    max_position_size = Column(Float, default=0.1, nullable=False)  # 10% of portfolio
    
    # Data configuration
    data_frequency = Column(String(10), default='1d', nullable=False)  # 1m, 5m, 1h, 1d
    benchmark_symbol = Column(String(20), nullable=True)
    
    # Execution status
    status = Column(String(20), default='pending', nullable=False)  # pending, running, completed, failed
    progress = Column(Float, default=0.0, nullable=False)  # 0-100%
    
    # Execution metadata
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    execution_time = Column(Float, nullable=True)  # in seconds
    error_message = Column(Text, nullable=True)
    
    # Strategy parameters (JSON)
    strategy_parameters = Column(JSON, nullable=True)
    
    # Results summary
    total_return = Column(Float, nullable=True)
    annualized_return = Column(Float, nullable=True)
    volatility = Column(Float, nullable=True)
    sharpe_ratio = Column(Float, nullable=True)
    max_drawdown = Column(Float, nullable=True)
    total_trades = Column(Integer, nullable=True)
    win_rate = Column(Float, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="backtests")
    strategy = relationship("Strategy", back_populates="backtests")
    trades = relationship("Trade", back_populates="backtest", cascade="all, delete-orphan")
    performance_metrics = relationship("BacktestPerformance", back_populates="backtest", cascade="all, delete-orphan")
    
    # Index for efficient queries
    __table_args__ = (
        Index('idx_backtest_user_status', 'user_id', 'status'),
        Index('idx_backtest_strategy_date', 'strategy_id', 'start_date'),
    )
    
    def to_dict(self):
        """Convert to dictionary with JSON parsing"""
        data = super().to_dict()
        if self.strategy_parameters:
            data['strategy_parameters'] = json.loads(self.strategy_parameters) if isinstance(self.strategy_parameters, str) else self.strategy_parameters
        return data

class BacktestPerformance(BaseModel):
    """Detailed backtest performance metrics"""
    __tablename__ = 'backtest_performance'
    
    backtest_id = Column(Integer, ForeignKey('backtests.id'), nullable=False)
    
    # Return metrics
    total_return = Column(Float, nullable=True)
    annualized_return = Column(Float, nullable=True)
    cumulative_return = Column(Float, nullable=True)
    
    # Risk metrics
    volatility = Column(Float, nullable=True)
    downside_deviation = Column(Float, nullable=True)
    max_drawdown = Column(Float, nullable=True)
    max_drawdown_duration = Column(Integer, nullable=True)  # in days
    
    # Risk-adjusted returns
    sharpe_ratio = Column(Float, nullable=True)
    sortino_ratio = Column(Float, nullable=True)
    calmar_ratio = Column(Float, nullable=True)
    omega_ratio = Column(Float, nullable=True)
    
    # Trade statistics
    total_trades = Column(Integer, nullable=True)
    winning_trades = Column(Integer, nullable=True)
    losing_trades = Column(Integer, nullable=True)
    win_rate = Column(Float, nullable=True)
    avg_win = Column(Float, nullable=True)
    avg_loss = Column(Float, nullable=True)
    largest_win = Column(Float, nullable=True)
    largest_loss = Column(Float, nullable=True)
    profit_factor = Column(Float, nullable=True)
    
    # Position statistics
    avg_holding_period = Column(Float, nullable=True)  # in days
    max_holding_period = Column(Float, nullable=True)  # in days
    avg_position_size = Column(Float, nullable=True)
    max_position_size = Column(Float, nullable=True)
    
    # Benchmark comparison
    benchmark_return = Column(Float, nullable=True)
    alpha = Column(Float, nullable=True)
    beta = Column(Float, nullable=True)
    correlation = Column(Float, nullable=True)
    information_ratio = Column(Float, nullable=True)
    tracking_error = Column(Float, nullable=True)
    
    # Value at Risk metrics
    var_95 = Column(Float, nullable=True)  # 95% VaR
    var_99 = Column(Float, nullable=True)  # 99% VaR
    cvar_95 = Column(Float, nullable=True)  # 95% CVaR
    cvar_99 = Column(Float, nullable=True)  # 99% CVaR
    
    # Additional metrics
    recovery_factor = Column(Float, nullable=True)
    ulcer_index = Column(Float, nullable=True)
    sterling_ratio = Column(Float, nullable=True)
    
    # Relationships
    backtest = relationship("Backtest", back_populates="performance_metrics")

class Trade(BaseModel):
    """Individual trade records"""
    __tablename__ = 'trades'
    
    backtest_id = Column(Integer, ForeignKey('backtests.id'), nullable=False)
    symbol = Column(String(20), nullable=False, index=True)
    
    # Trade identification
    trade_id = Column(String(100), nullable=False)  # Unique within backtest
    signal_id = Column(String(100), nullable=True)  # Strategy signal reference
    
    # Entry details
    entry_date = Column(DateTime, nullable=False, index=True)
    entry_price = Column(Float, nullable=False)
    entry_signal = Column(String(50), nullable=True)  # BUY, SELL_SHORT
    entry_reason = Column(Text, nullable=True)
    
    # Exit details
    exit_date = Column(DateTime, nullable=True)
    exit_price = Column(Float, nullable=True)
    exit_signal = Column(String(50), nullable=True)  # SELL, COVER
    exit_reason = Column(Text, nullable=True)
    
    # Position details
    quantity = Column(Float, nullable=False)
    side = Column(String(10), nullable=False)  # LONG, SHORT
    position_value = Column(Float, nullable=False)
    
    # Costs and fees
    entry_commission = Column(Float, default=0.0, nullable=False)
    exit_commission = Column(Float, default=0.0, nullable=False)
    entry_slippage = Column(Float, default=0.0, nullable=False)
    exit_slippage = Column(Float, default=0.0, nullable=False)
    
    # Trade results
    gross_pnl = Column(Float, nullable=True)
    net_pnl = Column(Float, nullable=True)
    return_pct = Column(Float, nullable=True)
    holding_period = Column(Integer, nullable=True)  # in days
    
    # Trade status
    is_open = Column(Boolean, default=True, nullable=False)
    is_winner = Column(Boolean, nullable=True)
    
    # Risk metrics
    max_adverse_excursion = Column(Float, nullable=True)  # MAE
    max_favorable_excursion = Column(Float, nullable=True)  # MFE
    
    # Relationships
    backtest = relationship("Backtest", back_populates="trades")
    
    # Index for efficient queries
    __table_args__ = (
        Index('idx_trade_backtest_symbol', 'backtest_id', 'symbol'),
        Index('idx_trade_entry_date', 'entry_date'),
        Index('idx_trade_status', 'is_open'),
    )
    
    def calculate_pnl(self):
        """Calculate P&L if trade is closed"""
        if not self.is_open and self.exit_price:
            if self.side == 'LONG':
                self.gross_pnl = (self.exit_price - self.entry_price) * self.quantity
            else:  # SHORT
                self.gross_pnl = (self.entry_price - self.exit_price) * self.quantity
            
            total_commission = self.entry_commission + (self.exit_commission or 0)
            total_slippage = self.entry_slippage + (self.exit_slippage or 0)
            self.net_pnl = self.gross_pnl - total_commission - total_slippage
            
            if self.position_value > 0:
                self.return_pct = (self.net_pnl / self.position_value) * 100
            
            self.is_winner = self.net_pnl > 0

class Signal(BaseModel):
    """Trading signals generated by strategies"""
    __tablename__ = 'signals'
    
    backtest_id = Column(Integer, ForeignKey('backtests.id'), nullable=False)
    symbol = Column(String(20), nullable=False, index=True)
    
    # Signal details
    signal_id = Column(String(100), nullable=False)
    signal_type = Column(String(20), nullable=False)  # BUY, SELL, HOLD
    signal_strength = Column(Float, nullable=True)  # 0-1 confidence
    timestamp = Column(DateTime, nullable=False, index=True)
    price = Column(Float, nullable=False)
    
    # Signal metadata
    indicator_values = Column(JSON, nullable=True)  # Technical indicator values
    signal_reason = Column(Text, nullable=True)
    
    # Execution status
    is_executed = Column(Boolean, default=False, nullable=False)
    execution_delay = Column(Float, nullable=True)  # in minutes
    execution_price = Column(Float, nullable=True)
    execution_slippage = Column(Float, nullable=True)
    
    # Relationships
    backtest = relationship("Backtest")
    
    # Index for efficient queries
    __table_args__ = (
        Index('idx_signal_backtest_timestamp', 'backtest_id', 'timestamp'),
        Index('idx_signal_symbol_type', 'symbol', 'signal_type'),
    )

class BacktestLog(BaseModel):
    """Execution logs for backtests"""
    __tablename__ = 'backtest_logs'
    
    backtest_id = Column(Integer, ForeignKey('backtests.id'), nullable=False)
    log_level = Column(String(10), nullable=False)  # DEBUG, INFO, WARNING, ERROR
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    component = Column(String(50), nullable=True)  # strategy, portfolio, orders, etc.
    details = Column(JSON, nullable=True)  # Additional log context
    
    # Relationships
    backtest = relationship("Backtest")
    
    # Index for efficient queries
    __table_args__ = (
        Index('idx_backtest_log_level', 'backtest_id', 'log_level'),
        Index('idx_backtest_log_timestamp', 'timestamp'),
    )

class BacktestComparison(BaseModel):
    """Comparison between multiple backtests"""
    __tablename__ = 'backtest_comparisons'
    
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    backtest_ids = Column(JSON, nullable=False)  # List of backtest IDs
    
    # Comparison metrics
    comparison_metrics = Column(JSON, nullable=True)
    best_performer = Column(Integer, nullable=True)  # Backtest ID
    comparison_criteria = Column(String(50), nullable=True)  # sharpe, return, drawdown
    
    # Relationships
    user = relationship("User")
    
    def to_dict(self):
        """Convert to dictionary with JSON parsing"""
        data = super().to_dict()
        for field in ['backtest_ids', 'comparison_metrics']:
            if data.get(field):
                data[field] = json.loads(data[field]) if isinstance(data[field], str) else data[field]
        return data