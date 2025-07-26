from datetime import datetime
from .base import BaseModel
from ..db import db

class Portfolio(BaseModel):
    """Portfolio model for tracking portfolio state with PostgreSQL optimizations."""
    __tablename__ = 'portfolios'
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    backtest_id = db.Column(db.Integer, db.ForeignKey('backtests.id'), nullable=True, index=True)
    
    # Basic information
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    portfolio_type = db.Column(db.String(20), default='paper', nullable=False, index=True)  # paper, live, backtest
    
    # Portfolio configuration - Using Numeric for precision
    initial_capital = db.Column(db.Numeric(15, 2), nullable=False)
    currency = db.Column(db.String(3), default='USD', nullable=False)
    
    # Current state - All monetary values use Numeric
    current_capital = db.Column(db.Numeric(15, 2), nullable=False)
    cash_balance = db.Column(db.Numeric(15, 2), nullable=False)
    invested_value = db.Column(db.Numeric(15, 2), default=0.0, nullable=False)
    total_value = db.Column(db.Numeric(15, 2), nullable=False)
    
    # Performance tracking - Using Numeric for financial calculations
    total_return = db.Column(db.Numeric(15, 2), default=0.0, nullable=False)
    total_return_pct = db.Column(db.Numeric(8, 4), default=0.0, nullable=False)
    unrealized_pnl = db.Column(db.Numeric(15, 2), default=0.0, nullable=False)
    realized_pnl = db.Column(db.Numeric(15, 2), default=0.0, nullable=False)
    
    # Risk metrics - Using Numeric for precision
    max_drawdown = db.Column(db.Numeric(8, 4), default=0.0, nullable=False)
    max_drawdown_value = db.Column(db.Numeric(15, 2), default=0.0, nullable=False)
    volatility = db.Column(db.Numeric(8, 4), nullable=True)
    sharpe_ratio = db.Column(db.Numeric(8, 4), nullable=True)
    beta = db.Column(db.Numeric(8, 4), nullable=True)
    
    # Portfolio metadata
    benchmark_symbol = db.Column(db.String(20), default='SPY', nullable=False)
    rebalance_frequency = db.Column(db.String(20), default='monthly', nullable=False)
    last_rebalance_date = db.Column(db.DateTime, nullable=True)
    
    # Status
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)
    is_public = db.Column(db.Boolean, default=False, nullable=False)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Settings stored as JSONB for flexibility
    settings = db.Column(db.JSON, nullable=True)
    tags = db.Column(db.JSON, nullable=True)  # Array of tags for categorization
    
    # Relationships with proper back_populates
    user = db.relationship("User", back_populates="portfolios")
    backtest = db.relationship("Backtest", back_populates="portfolios")
    positions = db.relationship("Position", back_populates="portfolio", cascade="all, delete-orphan")
    transactions = db.relationship("Transaction", back_populates="portfolio", cascade="all, delete-orphan")
    snapshots = db.relationship("PortfolioSnapshot", back_populates="portfolio", cascade="all, delete-orphan")
    
    # Indexes for performance
    __table_args__ = (
        db.Index('idx_portfolio_user_type_active', 'user_id', 'portfolio_type', 'is_active'),
        db.Index('idx_portfolio_backtest', 'backtest_id'),
        db.Index('idx_portfolio_last_updated', 'last_updated'),
        db.CheckConstraint('initial_capital > 0', name='ck_initial_capital_positive'),
        db.CheckConstraint('current_capital >= 0', name='ck_current_capital_non_negative'),
        db.CheckConstraint('cash_balance >= 0', name='ck_cash_balance_non_negative'),
        db.CheckConstraint('invested_value >= 0', name='ck_invested_value_non_negative'),
        db.CheckConstraint('total_value >= 0', name='ck_total_value_non_negative'),
        db.CheckConstraint('portfolio_type IN (\'paper\', \'live\', \'backtest\')', name='ck_portfolio_type_valid'),
        db.CheckConstraint('length(currency) = 3', name='ck_currency_length'),
    )
    
    def calculate_portfolio_value(self):
        """Calculate total portfolio value from positions."""
        position_value = sum(pos.market_value for pos in self.positions if pos.is_open)
        self.invested_value = position_value
        self.total_value = self.cash_balance + position_value
        
        if self.initial_capital > 0:
            self.total_return = self.total_value - self.initial_capital
            self.total_return_pct = (self.total_return / self.initial_capital) * 100
        
        self.last_updated = datetime.utcnow()
    
    def get_allocation(self):
        """Get current asset allocation."""
        if self.total_value == 0:
            return {'cash': 100.0}
        
        allocation = {
            'cash': float((self.cash_balance / self.total_value) * 100)
        }
        
        for position in self.positions:
            if position.is_open and position.market_value > 0:
                weight = float((position.market_value / self.total_value) * 100)
                allocation[position.symbol] = weight
        
        return allocation

class Position(BaseModel):
    """Position model for tracking individual asset positions with PostgreSQL optimizations."""
    __tablename__ = 'positions'
    
    # Foreign keys
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolios.id'), nullable=False, index=True)
    symbol = db.Column(db.String(20), nullable=False, index=True)
    
    # Position details
    side = db.Column(db.String(10), nullable=False, index=True)  # LONG, SHORT
    quantity = db.Column(db.Numeric(15, 6), nullable=False)  # Support fractional shares
    avg_entry_price = db.Column(db.Numeric(10, 4), nullable=False)
    current_price = db.Column(db.Numeric(10, 4), nullable=False)
    
    # Cost basis and market value - Using Numeric for precision
    cost_basis = db.Column(db.Numeric(15, 2), nullable=False)
    market_value = db.Column(db.Numeric(15, 2), nullable=False)
    
    # P&L tracking - Using Numeric for financial calculations
    unrealized_pnl = db.Column(db.Numeric(15, 2), default=0.0, nullable=False)
    unrealized_pnl_pct = db.Column(db.Numeric(8, 4), default=0.0, nullable=False)
    realized_pnl = db.Column(db.Numeric(15, 2), default=0.0, nullable=False)
    
    # Position metadata
    first_entry_date = db.Column(db.DateTime, nullable=False, index=True)
    last_update_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    is_open = db.Column(db.Boolean, default=True, nullable=False, index=True)
    
    # Risk metrics - Using Numeric for precision
    position_weight = db.Column(db.Numeric(8, 4), nullable=False)  # % of portfolio
    max_position_value = db.Column(db.Numeric(15, 2), nullable=False)
    max_adverse_excursion = db.Column(db.Numeric(15, 2), default=0.0, nullable=False)
    max_favorable_excursion = db.Column(db.Numeric(15, 2), default=0.0, nullable=False)
    
    # Position metadata stored as JSONB
    additional_metadata = db.Column(db.JSON, nullable=True)  # Additional position data
    
    # Relationships
    portfolio = db.relationship("Portfolio", back_populates="positions")
    transactions = db.relationship("Transaction", back_populates="position", cascade="all, delete-orphan")
    
    # Indexes for performance
    __table_args__ = (
        db.Index('idx_position_portfolio_symbol_open', 'portfolio_id', 'symbol', 'is_open'),
        db.Index('idx_position_symbol_side', 'symbol', 'side'),
        db.Index('idx_position_entry_date', 'first_entry_date'),
        db.CheckConstraint('quantity != 0', name='ck_quantity_non_zero'),
        db.CheckConstraint('avg_entry_price > 0', name='ck_avg_entry_price_positive'),
        db.CheckConstraint('current_price > 0', name='ck_current_price_positive'),
        db.CheckConstraint('cost_basis > 0', name='ck_cost_basis_positive'),
        db.CheckConstraint('market_value >= 0', name='ck_market_value_non_negative'),
        db.CheckConstraint('side IN (\'LONG\', \'SHORT\')', name='ck_side_valid'),
        db.CheckConstraint('position_weight >= 0 AND position_weight <= 100', name='ck_position_weight_valid'),
    )
    
    def update_market_value(self, current_price):
        """Update position with current market price."""
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
        
        # Update position weight relative to portfolio
        if self.portfolio and self.portfolio.total_value > 0:
            self.position_weight = (self.market_value / self.portfolio.total_value) * 100
        
        self.last_update_date = datetime.utcnow()

class Transaction(BaseModel):
    """Transaction model for recording all portfolio transactions with PostgreSQL optimizations."""
    __tablename__ = 'transactions'
    
    # Foreign keys
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolios.id'), nullable=False, index=True)
    position_id = db.Column(db.Integer, db.ForeignKey('positions.id'), nullable=True, index=True)
    symbol = db.Column(db.String(20), nullable=False, index=True)
    
    # Transaction details
    transaction_type = db.Column(db.String(20), nullable=False, index=True)  # BUY, SELL, DIVIDEND, SPLIT, etc.
    side = db.Column(db.String(10), nullable=True, index=True)  # BUY, SELL (for compatibility)
    quantity = db.Column(db.Numeric(15, 6), nullable=False)  # Support fractional shares
    price = db.Column(db.Numeric(10, 4), nullable=False)
    total_value = db.Column(db.Numeric(15, 2), nullable=False)
    
    # Costs and fees - Using Numeric for precision
    commission = db.Column(db.Numeric(10, 2), default=0.0, nullable=False)
    fees = db.Column(db.Numeric(10, 2), default=0.0, nullable=False)
    slippage = db.Column(db.Numeric(10, 2), default=0.0, nullable=False)
    
    # Transaction metadata
    transaction_date = db.Column(db.DateTime, nullable=False, index=True)
    settlement_date = db.Column(db.DateTime, nullable=True)
    order_id = db.Column(db.String(100), nullable=True, index=True)
    execution_venue = db.Column(db.String(50), nullable=True)
    
    # Cash impact - Using Numeric for precision
    cash_impact = db.Column(db.Numeric(15, 2), nullable=False)  # Net cash flow
    
    # Transaction status
    status = db.Column(db.String(20), default='FILLED', nullable=False, index=True)
    
    # Notes and metadata
    notes = db.Column(db.Text, nullable=True)
    additional_metadata = db.Column(db.JSON, nullable=True)  # Additional transaction data
    
    # Relationships
    portfolio = db.relationship("Portfolio", back_populates="transactions")
    position = db.relationship("Position", back_populates="transactions")
    
    # Indexes for performance
    __table_args__ = (
        db.Index('idx_transaction_portfolio_date_type', 'portfolio_id', 'transaction_date', 'transaction_type'),
        db.Index('idx_transaction_symbol_date', 'symbol', 'transaction_date'),
        db.Index('idx_transaction_order_id', 'order_id'),
        db.Index('idx_transaction_status_date', 'status', 'transaction_date'),
        db.CheckConstraint('quantity != 0', name='ck_quantity_non_zero'),
        db.CheckConstraint('price > 0', name='ck_price_positive'),
        db.CheckConstraint('total_value != 0', name='ck_total_value_non_zero'),
        db.CheckConstraint('commission >= 0', name='ck_commission_non_negative'),
        db.CheckConstraint('fees >= 0', name='ck_fees_non_negative'),
        db.CheckConstraint('transaction_type IN (\'BUY\', \'SELL\', \'DIVIDEND\', \'SPLIT\', \'MERGER\', \'SPINOFF\')', name='ck_transaction_type_valid'),
        db.CheckConstraint('status IN (\'PENDING\', \'FILLED\', \'CANCELLED\', \'REJECTED\')', name='ck_status_valid'),
    )

class PortfolioSnapshot(BaseModel):
    """Daily portfolio snapshots for performance tracking with PostgreSQL optimizations."""
    __tablename__ = 'portfolio_snapshots'
    
    # Foreign key
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolios.id'), nullable=False, index=True)
    snapshot_date = db.Column(db.DateTime, nullable=False, index=True)
    
    # Portfolio values - Using Numeric for precision
    total_value = db.Column(db.Numeric(15, 2), nullable=False)
    cash_balance = db.Column(db.Numeric(15, 2), nullable=False)
    invested_value = db.Column(db.Numeric(15, 2), nullable=False)
    
    # Performance metrics - Using Numeric for financial calculations
    daily_return = db.Column(db.Numeric(8, 4), nullable=True)
    daily_return_pct = db.Column(db.Numeric(8, 4), nullable=True)
    cumulative_return = db.Column(db.Numeric(15, 2), nullable=False)
    cumulative_return_pct = db.Column(db.Numeric(8, 4), nullable=False)
    unrealized_pnl = db.Column(db.Numeric(15, 2), default=0.0, nullable=False)
    realized_pnl = db.Column(db.Numeric(15, 2), default=0.0, nullable=False)
    
    # Risk metrics - Using Numeric for precision
    volatility = db.Column(db.Numeric(8, 4), nullable=True)
    drawdown = db.Column(db.Numeric(8, 4), nullable=True)
    drawdown_value = db.Column(db.Numeric(15, 2), nullable=True)
    high_water_mark = db.Column(db.Numeric(15, 2), nullable=False)
    
    # Position counts
    total_positions = db.Column(db.Integer, default=0, nullable=False)
    long_positions = db.Column(db.Integer, default=0, nullable=False)
    short_positions = db.Column(db.Integer, default=0, nullable=False)
    
    # Sector/asset allocation stored as JSONB
    allocation_data = db.Column(db.JSON, nullable=True)  # Sector/asset breakdown
    sector_weights = db.Column(db.JSON, nullable=True)   # Sector allocation
    
    # Benchmark comparison
    benchmark_return = db.Column(db.Numeric(8, 4), nullable=True)
    relative_return = db.Column(db.Numeric(8, 4), nullable=True)  # Portfolio return - benchmark return
    
    # Relationships
    portfolio = db.relationship("Portfolio", back_populates="snapshots")
    
    # Indexes for performance (including partitioning hint)
    __table_args__ = (
        db.Index('idx_portfolio_snapshot_date', 'portfolio_id', 'snapshot_date'),
        db.Index('idx_snapshot_date_total_value', 'snapshot_date', 'total_value'),
        db.CheckConstraint('total_value >= 0', name='ck_total_value_non_negative'),
        db.CheckConstraint('cash_balance >= 0', name='ck_cash_balance_non_negative'),
        db.CheckConstraint('invested_value >= 0', name='ck_invested_value_non_negative'),
        db.CheckConstraint('total_positions >= 0', name='ck_total_positions_non_negative'),
        db.CheckConstraint('long_positions >= 0', name='ck_long_positions_non_negative'),
        db.CheckConstraint('short_positions >= 0', name='ck_short_positions_non_negative'),
        # Note: In production, consider partitioning this table by snapshot_date
    )

class Order(BaseModel):
    """Order model for tracking trading orders with PostgreSQL optimizations."""
    __tablename__ = 'orders'
    
    # Foreign keys
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolios.id'), nullable=False, index=True)
    symbol = db.Column(db.String(20), nullable=False, index=True)
    
    # Order details
    order_type = db.Column(db.String(20), nullable=False, index=True)  # MARKET, LIMIT, STOP, STOP_LIMIT
    side = db.Column(db.String(10), nullable=False, index=True)  # BUY, SELL
    quantity = db.Column(db.Numeric(15, 6), nullable=False)  # Support fractional shares
    price = db.Column(db.Numeric(10, 4), nullable=True)  # NULL for market orders
    stop_price = db.Column(db.Numeric(10, 4), nullable=True)  # For stop orders
    
    # Order status and timing
    status = db.Column(db.String(20), default='PENDING', nullable=False, index=True)  # PENDING, FILLED, CANCELLED, REJECTED, PARTIAL
    time_in_force = db.Column(db.String(10), default='DAY', nullable=False)  # DAY, GTC, IOC, FOK
    order_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=True)
    
    # Execution details
    filled_quantity = db.Column(db.Numeric(15, 6), default=0.0, nullable=False)
    remaining_quantity = db.Column(db.Numeric(15, 6), nullable=False)
    avg_fill_price = db.Column(db.Numeric(10, 4), nullable=True)
    
    # Fees and costs
    commission = db.Column(db.Numeric(10, 2), default=0.0, nullable=False)
    fees = db.Column(db.Numeric(10, 2), default=0.0, nullable=False)
    
    # External references
    broker_order_id = db.Column(db.String(100), nullable=True, index=True)
    parent_order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True)
    
    # Order metadata
    notes = db.Column(db.Text, nullable=True)
    additional_metadata = db.Column(db.JSON, nullable=True)
    
    # Relationships
    portfolio = db.relationship("Portfolio", backref="orders")
    fills = db.relationship("OrderFill", back_populates="order", cascade="all, delete-orphan")
    child_orders = db.relationship("Order", backref="parent_order", remote_side="Order.id")
    
    # Indexes and constraints
    __table_args__ = (
        db.Index('idx_order_portfolio_status_date', 'portfolio_id', 'status', 'order_date'),
        db.Index('idx_order_symbol_side_status', 'symbol', 'side', 'status'),
        db.Index('idx_order_broker_id', 'broker_order_id'),
        db.CheckConstraint('quantity > 0', name='ck_quantity_positive'),
        db.CheckConstraint('filled_quantity >= 0', name='ck_filled_quantity_non_negative'),
        db.CheckConstraint('remaining_quantity >= 0', name='ck_remaining_quantity_non_negative'),
        db.CheckConstraint('filled_quantity <= quantity', name='ck_filled_not_exceed_quantity'),
        db.CheckConstraint('order_type IN (\'MARKET\', \'LIMIT\', \'STOP\', \'STOP_LIMIT\')', name='ck_order_type_valid'),
        db.CheckConstraint('side IN (\'BUY\', \'SELL\')', name='ck_side_valid'),
        db.CheckConstraint('status IN (\'PENDING\', \'FILLED\', \'CANCELLED\', \'REJECTED\', \'PARTIAL\')', name='ck_status_valid'),
        db.CheckConstraint('time_in_force IN (\'DAY\', \'GTC\', \'IOC\', \'FOK\')', name='ck_time_in_force_valid'),
    )
    
    def is_complete(self):
        """Check if order is completely filled."""
        return self.status == 'FILLED' and self.filled_quantity == self.quantity
    
    def calculate_remaining_quantity(self):
        """Calculate and update remaining quantity."""
        self.remaining_quantity = self.quantity - self.filled_quantity
        return self.remaining_quantity


class OrderFill(BaseModel):
    """Order fill model for tracking partial and complete order executions."""
    __tablename__ = 'order_fills'
    
    # Foreign keys
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False, index=True)
    symbol = db.Column(db.String(20), nullable=False, index=True)
    
    # Fill details
    quantity = db.Column(db.Numeric(15, 6), nullable=False)
    price = db.Column(db.Numeric(10, 4), nullable=False)
    total_value = db.Column(db.Numeric(15, 2), nullable=False)
    
    # Execution details
    fill_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    execution_venue = db.Column(db.String(50), nullable=True)
    liquidity_flag = db.Column(db.String(10), nullable=True)  # MAKER, TAKER
    
    # Costs
    commission = db.Column(db.Numeric(10, 2), default=0.0, nullable=False)
    fees = db.Column(db.Numeric(10, 2), default=0.0, nullable=False)
    
    # External references
    execution_id = db.Column(db.String(100), nullable=True, index=True)
    contra_party = db.Column(db.String(100), nullable=True)
    
    # Fill metadata
    additional_metadata = db.Column(db.JSON, nullable=True)
    
    # Relationships
    order = db.relationship("Order", back_populates="fills")
    
    # Indexes and constraints
    __table_args__ = (
        db.Index('idx_fill_order_date', 'order_id', 'fill_date'),
        db.Index('idx_fill_symbol_date', 'symbol', 'fill_date'),
        db.Index('idx_fill_execution_id', 'execution_id'),
        db.CheckConstraint('quantity > 0', name='ck_fill_quantity_positive'),
        db.CheckConstraint('price > 0', name='ck_fill_price_positive'),
        db.CheckConstraint('total_value > 0', name='ck_total_value_positive'),
        db.CheckConstraint('commission >= 0', name='ck_commission_non_negative'),
        db.CheckConstraint('fees >= 0', name='ck_fees_non_negative'),
        db.CheckConstraint('liquidity_flag IN (\'MAKER\', \'TAKER\') OR liquidity_flag IS NULL', name='ck_liquidity_flag_valid'),
    )