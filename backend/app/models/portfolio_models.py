from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.sqlite import JSON
from datetime import datetime
import json

from .base import BaseModel

class Portfolio(BaseModel):
    """Portfolio model for tracking portfolio state"""
    __tablename__ = 'portfolios'
    
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    backtest_id = Column(Integer, ForeignKey('backtests.id'), nullable=True)  # Null for live portfolios
    
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    portfolio_type = Column(String(20), default='backtest', nullable=False)  # backtest, paper, live
    
    # Portfolio configuration
    initial_capital = Column(Float, nullable=False)
    currency = Column(String(10), default='USD', nullable=False)
    
    # Current state
    current_capital = Column(Float, nullable=False)
    cash_balance = Column(Float, nullable=False)
    invested_value = Column(Float, default=0.0, nullable=False)
    total_value = Column(Float, nullable=False)
    
    # Performance tracking
    total_return = Column(Float, default=0.0, nullable=False)
    unrealized_pnl = Column(Float, default=0.0, nullable=False)
    realized_pnl = Column(Float, default=0.0, nullable=False)
    
    # Risk metrics
    max_drawdown = Column(Float, default=0.0, nullable=False)
    volatility = Column(Float, nullable=True)
    sharpe_ratio = Column(Float, nullable=True)
    
    # Portfolio status
    is_active = Column(Boolean, default=True, nullable=False)
    last_updated = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="portfolios")
    backtest = relationship("Backtest")
    positions = relationship("Position", back_populates="portfolio", cascade="all, delete-orphan")
    snapshots = relationship("PortfolioSnapshot", back_populates="portfolio", cascade="all, delete-orphan")
    
    # Index for efficient queries
    __table_args__ = (
        Index('idx_portfolio_user_type', 'user_id', 'portfolio_type'),
        Index('idx_portfolio_backtest', 'backtest_id'),
    )
    
    def calculate_portfolio_value(self):
        """Calculate total portfolio value"""
        position_value = sum(pos.market_value for pos in self.positions if pos.is_open)
        self.invested_value = position_value
        self.total_value = self.cash_balance + position_value
        self.total_return = ((self.total_value - self.initial_capital) / self.initial_capital) * 100

class Position(BaseModel):
    """Position model for tracking individual asset positions"""
    __tablename__ = 'positions'
    
    portfolio_id = Column(Integer, ForeignKey('portfolios.id'), nullable=False)
    symbol = Column(String(20), nullable=False, index=True)
    
    # Position details
    side = Column(String(10), nullable=False)  # LONG, SHORT
    quantity = Column(Float, nullable=False)
    avg_entry_price = Column(Float, nullable=False)
    current_price = Column(Float, nullable=False)
    
    # Cost basis and market value
    cost_basis = Column(Float, nullable=False)
    market_value = Column(Float, nullable=False)
    
    # P&L tracking
    unrealized_pnl = Column(Float, default=0.0, nullable=False)
    unrealized_pnl_pct = Column(Float, default=0.0, nullable=False)
    realized_pnl = Column(Float, default=0.0, nullable=False)
    
    # Position metadata
    first_entry_date = Column(DateTime, nullable=False)
    last_update_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_open = Column(Boolean, default=True, nullable=False)
    
    # Risk metrics
    position_weight = Column(Float, nullable=False)  # % of portfolio
    max_position_value = Column(Float, nullable=False)
    max_adverse_excursion = Column(Float, default=0.0, nullable=False)
    max_favorable_excursion = Column(Float, default=0.0, nullable=False)
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="positions")
    transactions = relationship("Transaction", back_populates="position", cascade="all, delete-orphan")
    
    # Index for efficient queries
    __table_args__ = (
        Index('idx_position_portfolio_symbol', 'portfolio_id', 'symbol'),
        Index('idx_position_open', 'is_open'),
    )
    
    def update_market_value(self, current_price):
        """Update position with current market price"""
        self.current_price = current_price
        self.market_value = abs(self.quantity) * current_price
        
        if self.side == 'LONG':
            self.unrealized_pnl = (current_price - self.avg_entry_price) * self.quantity
        else:  # SHORT
            self.unrealized_pnl = (self.avg_entry_price - current_price) * abs(self.quantity)
        
        if self.cost_basis > 0:
            self.unrealized_pnl_pct = (self.unrealized_pnl / self.cost_basis) * 100
        
        # Update MAE and MFE
        if self.unrealized_pnl < self.max_adverse_excursion:
            self.max_adverse_excursion = self.unrealized_pnl
        if self.unrealized_pnl > self.max_favorable_excursion:
            self.max_favorable_excursion = self.unrealized_pnl
        
        self.last_update_date = datetime.utcnow()

class Transaction(BaseModel):
    """Transaction model for recording all portfolio transactions"""
    __tablename__ = 'transactions'
    
    portfolio_id = Column(Integer, ForeignKey('portfolios.id'), nullable=False)
    position_id = Column(Integer, ForeignKey('positions.id'), nullable=True)
    symbol = Column(String(20), nullable=False, index=True)
    
    # Transaction details
    transaction_type = Column(String(20), nullable=False)  # BUY, SELL, DIVIDEND, SPLIT, etc.
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    total_value = Column(Float, nullable=False)
    
    # Costs and fees
    commission = Column(Float, default=0.0, nullable=False)
    fees = Column(Float, default=0.0, nullable=False)
    slippage = Column(Float, default=0.0, nullable=False)
    
    # Transaction metadata
    transaction_date = Column(DateTime, nullable=False, index=True)
    settlement_date = Column(DateTime, nullable=True)
    order_id = Column(String(100), nullable=True)
    execution_venue = Column(String(50), nullable=True)
    
    # Cash impact
    cash_impact = Column(Float, nullable=False)  # Net cash flow
    
    # Transaction status
    status = Column(String(20), default='executed', nullable=False)  # pending, executed, cancelled
    
    # Relationships
    portfolio = relationship("Portfolio")
    position = relationship("Position", back_populates="transactions")
    
    # Index for efficient queries
    __table_args__ = (
        Index('idx_transaction_portfolio_date', 'portfolio_id', 'transaction_date'),
        Index('idx_transaction_symbol_type', 'symbol', 'transaction_type'),
    )

class PortfolioSnapshot(BaseModel):
    """Daily portfolio snapshots for performance tracking"""
    __tablename__ = 'portfolio_snapshots'
    
    portfolio_id = Column(Integer, ForeignKey('portfolios.id'), nullable=False)
    snapshot_date = Column(DateTime, nullable=False, index=True)
    
    # Portfolio values
    total_value = Column(Float, nullable=False)
    cash_balance = Column(Float, nullable=False)
    invested_value = Column(Float, nullable=False)
    
    # Performance metrics
    daily_return = Column(Float, nullable=True)
    cumulative_return = Column(Float, nullable=False)
    unrealized_pnl = Column(Float, default=0.0, nullable=False)
    realized_pnl = Column(Float, default=0.0, nullable=False)
    
    # Risk metrics
    volatility = Column(Float, nullable=True)
    drawdown = Column(Float, nullable=True)
    high_water_mark = Column(Float, nullable=False)
    
    # Position counts
    total_positions = Column(Integer, default=0, nullable=False)
    long_positions = Column(Integer, default=0, nullable=False)
    short_positions = Column(Integer, default=0, nullable=False)
    
    # Sector/asset allocation
    allocation_data = Column(JSON, nullable=True)  # Sector/asset breakdown
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="snapshots")
    
    # Index for efficient queries
    __table_args__ = (
        Index('idx_portfolio_snapshot_date', 'portfolio_id', 'snapshot_date'),
    )

class Order(BaseModel):
    """Order model for tracking order lifecycle"""
    __tablename__ = 'orders'
    
    portfolio_id = Column(Integer, ForeignKey('portfolios.id'), nullable=False)
    symbol = Column(String(20), nullable=False, index=True)
    
    # Order identification
    order_id = Column(String(100), nullable=False, unique=True)
    parent_order_id = Column(String(100), nullable=True)  # For bracket orders
    strategy_signal_id = Column(String(100), nullable=True)
    
    # Order details
    order_type = Column(String(20), nullable=False)  # MARKET, LIMIT, STOP, STOP_LIMIT
    side = Column(String(10), nullable=False)  # BUY, SELL
    quantity = Column(Float, nullable=False)
    
    # Price parameters
    limit_price = Column(Float, nullable=True)
    stop_price = Column(Float, nullable=True)
    
    # Order timing
    time_in_force = Column(String(10), default='DAY', nullable=False)  # DAY, GTC, IOC, FOK
    order_date = Column(DateTime, nullable=False, index=True)
    expiry_date = Column(DateTime, nullable=True)
    
    # Execution details
    status = Column(String(20), default='pending', nullable=False)  # pending, partial, filled, cancelled, rejected
    filled_quantity = Column(Float, default=0.0, nullable=False)
    remaining_quantity = Column(Float, nullable=False)
    avg_fill_price = Column(Float, nullable=True)
    
    # Execution timestamps
    submitted_at = Column(DateTime, nullable=True)
    filled_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    
    # Order costs
    commission = Column(Float, default=0.0, nullable=False)
    fees = Column(Float, default=0.0, nullable=False)
    
    # Order metadata
    notes = Column(Text, nullable=True)
    
    # Relationships
    portfolio = relationship("Portfolio")
    fills = relationship("OrderFill", back_populates="order", cascade="all, delete-orphan")
    
    # Index for efficient queries
    __table_args__ = (
        Index('idx_order_portfolio_status', 'portfolio_id', 'status'),
        Index('idx_order_symbol_date', 'symbol', 'order_date'),
    )
    
    def is_complete(self):
        """Check if order is completely filled"""
        return self.filled_quantity >= self.quantity
    
    def is_active(self):
        """Check if order is still active"""
        return self.status in ['pending', 'partial']

class OrderFill(BaseModel):
    """Order fill model for tracking partial fills"""
    __tablename__ = 'order_fills'
    
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    
    # Fill details
    fill_id = Column(String(100), nullable=False)
    fill_quantity = Column(Float, nullable=False)
    fill_price = Column(Float, nullable=False)
    fill_timestamp = Column(DateTime, nullable=False, index=True)
    
    # Fill costs
    commission = Column(Float, default=0.0, nullable=False)
    fees = Column(Float, default=0.0, nullable=False)
    
    # Execution venue
    venue = Column(String(50), nullable=True)
    liquidity_flag = Column(String(10), nullable=True)  # A (Added), R (Removed)
    
    # Relationships
    order = relationship("Order", back_populates="fills")
    
    # Index for efficient queries
    __table_args__ = (
        Index('idx_order_fill_timestamp', 'fill_timestamp'),
    )