# PostgreSQL Database Schema Documentation

## Overview

This document describes the optimized PostgreSQL database schema for the trading/backtesting platform. The schema has been completely redesigned for PostgreSQL with proper data types, constraints, and performance optimizations.

## Key Improvements Implemented

### ✅ **PostgreSQL-Specific Optimizations**
- **JSONB Fields**: Replaced SQLite JSON with PostgreSQL JSONB for better performance and querying
- **Connection Pooling**: Optimized pool settings (20 base connections, 50 overflow in production)
- **Partitioning Support**: Schema designed for time-series data partitioning

### ✅ **Data Type Precision**
- **Numeric for Money**: All monetary values use `Numeric(15, 2)` for precise financial calculations
- **Numeric for Prices**: Price fields use `Numeric(10, 4)` for 4-decimal precision
- **Numeric for Quantities**: Support fractional shares with `Numeric(15, 6)`
- **No Float Usage**: Eliminated all Float types to prevent precision loss

### ✅ **Comprehensive Constraints**
- **Check Constraints**: Positive values, valid enums, logical relationships
- **Foreign Key Constraints**: Proper referential integrity across all tables
- **Unique Constraints**: Prevent duplicate data (e.g., symbol uniqueness, time-series data)
- **Data Validation**: OHLC validation, date range validation, percentage ranges

### ✅ **Performance Optimization**
- **Strategic Indexes**: Composite indexes for common query patterns
- **Time-Series Indexes**: Optimized for date-range queries on market data
- **Symbol Indexes**: Fast symbol-based lookups across all tables
- **Foreign Key Indexes**: Automatic indexing for all foreign key relationships

## Database Schema

### Core Models

#### **Users & Authentication**
```sql
users
├── id (Primary Key)
├── username (Unique, Indexed)
├── email (Unique, Indexed)
├── password_hash
├── first_name, last_name
├── is_active, is_verified
└── timestamps (created_at, updated_at)

user_preferences
├── user_id (FK to users, Unique)
├── theme, language, timezone, currency
├── trading preferences (JSONB)
├── notification settings (JSONB)
└── dashboard layout (JSONB)
```

#### **Portfolio Management**
```sql
portfolios
├── id (Primary Key)
├── user_id (FK to users)
├── backtest_id (FK to backtests, Optional)
├── name, description, portfolio_type
├── Financial fields (ALL Numeric):
│   ├── initial_capital Numeric(15,2)
│   ├── current_capital Numeric(15,2)
│   ├── cash_balance Numeric(15,2)
│   ├── total_value Numeric(15,2)
│   └── performance metrics Numeric(8,4)
├── settings (JSONB)
└── Indexes: (user_id, portfolio_type, is_active)

positions
├── id (Primary Key)
├── portfolio_id (FK to portfolios)
├── symbol (Indexed)
├── Quantity & Pricing (ALL Numeric):
│   ├── quantity Numeric(15,6)  -- Fractional shares
│   ├── avg_entry_price Numeric(10,4)
│   ├── current_price Numeric(10,4)
│   └── market_value Numeric(15,2)
├── P&L tracking (Numeric)
└── Indexes: (portfolio_id, symbol, is_open)

transactions
├── id (Primary Key)
├── portfolio_id (FK to portfolios)
├── position_id (FK to positions)
├── symbol (Indexed)
├── Transaction details (ALL Numeric):
│   ├── quantity Numeric(15,6)
│   ├── price Numeric(10,4)
│   ├── total_value Numeric(15,2)
│   └── commission, fees Numeric(10,2)
├── metadata (JSONB)
└── Indexes: (portfolio_id, transaction_date, transaction_type)
```

#### **Market Data**
```sql
assets
├── id (Primary Key)
├── symbol (Unique, Indexed)
├── name, asset_type, exchange
├── market_cap Numeric(20,2)
├── fundamentals (JSONB)
└── Indexes: (asset_type, exchange), (sector, industry)

market_data  -- Designed for partitioning
├── id (Primary Key)
├── asset_id (FK to assets)
├── symbol (Denormalized, Indexed)
├── timestamp (Indexed) -- Partition key
├── timeframe (Indexed)
├── OHLCV data (ALL Numeric(10,4)):
│   ├── open_price, high_price, low_price, close_price
│   └── volume Numeric(15,0)
├── Market microstructure (Numeric):
│   ├── bid_price, ask_price
│   └── vwap Numeric(10,4)
├── additional_data (JSONB)
└── Indexes: (symbol, timeframe, timestamp), (timestamp, symbol)
└── Constraints: OHLC validation, positive prices

benchmarks
├── id (Primary Key)
├── symbol (Unique)
├── Performance data (ALL Numeric(8,4))
├── composition (JSONB)
└── Indexes: (benchmark_type, category)
```

#### **Strategy & Backtesting**
```sql
strategies
├── id (Primary Key)
├── user_id (FK to users)
├── name, description, strategy_type
├── Configuration (JSONB):
│   ├── parameters
│   ├── entry_rules
│   ├── exit_rules
│   └── risk_rules
├── source_code (Text)
└── Indexes: (user_id, strategy_type, is_active)

backtests
├── id (Primary Key)
├── user_id (FK to users)
├── strategy_id (FK to strategies)
├── Configuration:
│   ├── start_date, end_date (Indexed)
│   ├── initial_capital Numeric(15,2)
│   └── universe (JSONB)
├── Results (ALL Numeric):
│   ├── final_value, total_return
│   ├── sharpe_ratio, max_drawdown
│   └── trade statistics
├── parameters (JSONB)
└── Indexes: (user_id, strategy_id), (start_date, end_date)

trades
├── id (Primary Key)
├── backtest_id (FK to backtests)
├── symbol (Indexed)
├── Entry/Exit details (ALL Numeric):
│   ├── quantity Numeric(15,6)
│   ├── entry_price, exit_price Numeric(10,4)
│   └── pnl Numeric(15,2)
├── conditions (JSONB)
└── Indexes: (backtest_id, symbol, entry_date)

signals
├── id (Primary Key)
├── backtest_id (FK to backtests)
├── Signal details (Numeric):
│   ├── signal_price Numeric(10,4)
│   ├── confidence Numeric(5,4)
│   └── strength Numeric(8,4)
├── conditions (JSONB)
└── Indexes: (backtest_id, signal_date, signal_type)
```

#### **Risk Management**
```sql
risk_profiles
├── id (Primary Key)
├── user_id (FK to users)
├── Risk limits (ALL Numeric):
│   ├── max_position_size_pct Numeric(5,2)
│   ├── max_portfolio_var Numeric(8,4)
│   └── max_drawdown_limit Numeric(8,4)
├── Asset restrictions (JSONB)
├── advanced_settings (JSONB)
└── Indexes: (user_id, is_active)

risk_metrics
├── id (Primary Key)
├── risk_profile_id (FK to risk_profiles)
├── portfolio_id (FK to portfolios)
├── calculation_date (Indexed)
├── Risk calculations (ALL Numeric):
│   ├── var_1d_95, var_1d_99 Numeric(15,2)
│   ├── volatility Numeric(8,4)
│   └── drawdown metrics
├── Factor exposures (Numeric)
├── stress_test_results (JSONB)
└── Indexes: (risk_profile_id, calculation_date)
```

## Performance Features

### **Indexing Strategy**
```sql
-- Time-series performance
CREATE INDEX CONCURRENTLY idx_market_data_symbol_timeframe_timestamp 
ON market_data (symbol, timeframe, timestamp);

-- Portfolio queries
CREATE INDEX CONCURRENTLY idx_portfolio_user_type_active 
ON portfolios (user_id, portfolio_type, is_active);

-- Transaction history
CREATE INDEX CONCURRENTLY idx_transaction_portfolio_date_type 
ON transactions (portfolio_id, transaction_date, transaction_type);
```

### **Connection Pooling**
```python
# Development
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 10,
    'pool_recycle': 3600,
    'pool_pre_ping': True,
    'pool_timeout': 20,
    'max_overflow': 30
}

# Production
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 20,
    'pool_recycle': 3600,
    'pool_pre_ping': True,
    'pool_timeout': 30,
    'max_overflow': 50
}
```

### **Partitioning Strategy** (Production)
```sql
-- Partition market_data by timestamp (monthly partitions)
CREATE TABLE market_data_y2024m01 PARTITION OF market_data
FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

-- Automatic partition creation
CREATE OR REPLACE FUNCTION create_monthly_partition()
RETURNS void AS $$
-- Implementation for automatic partition management
$$;
```

## Data Validation & Constraints

### **Financial Data Validation**
```sql
-- Positive monetary values
ALTER TABLE portfolios ADD CONSTRAINT ck_initial_capital_positive 
CHECK (initial_capital > 0);

-- OHLC data validation
ALTER TABLE market_data ADD CONSTRAINT ck_high_low_valid 
CHECK (high_price >= low_price);

-- Percentage ranges
ALTER TABLE risk_profiles ADD CONSTRAINT ck_max_position_size_valid 
CHECK (max_position_size_pct > 0 AND max_position_size_pct <= 100);
```

### **Business Logic Constraints**
```sql
-- Portfolio type validation
ALTER TABLE portfolios ADD CONSTRAINT ck_portfolio_type_valid 
CHECK (portfolio_type IN ('paper', 'live', 'backtest'));

-- Risk tolerance validation
ALTER TABLE risk_profiles ADD CONSTRAINT ck_risk_tolerance_valid 
CHECK (risk_tolerance IN ('conservative', 'moderate', 'aggressive'));
```

## Usage Examples

### **Precise Financial Calculations**
```python
from decimal import Decimal
from models import Portfolio, Transaction

# Create portfolio with precise capital
portfolio = Portfolio(
    name='High Precision Portfolio',
    initial_capital=Decimal('100000.50'),  # Exact precision
    cash_balance=Decimal('50000.25')
)

# Record precise transaction
transaction = Transaction(
    quantity=Decimal('123.456789'),  # Fractional shares supported
    price=Decimal('45.6789'),        # 4-decimal price precision
    commission=Decimal('9.95')       # Exact commission
)
```

### **JSONB Queries**
```python
# Query strategies by parameter
strategies = Strategy.query.filter(
    Strategy.parameters['lookback_period'].astext.cast(Integer) > 20
).all()

# Update JSONB field
strategy.parameters = {
    'lookback_period': 30,
    'threshold': 0.05,
    'risk_management': {
        'stop_loss': 0.02,
        'take_profit': 0.06
    }
}
```

### **Time-Series Queries**
```python
from datetime import datetime, timedelta

# Efficient time-range query (uses timestamp index)
recent_data = MarketData.query.filter(
    MarketData.symbol == 'AAPL',
    MarketData.timeframe == '1d',
    MarketData.timestamp >= datetime.utcnow() - timedelta(days=30)
).order_by(MarketData.timestamp.desc()).all()

# Multi-symbol query (uses composite index)
data = MarketData.query.filter(
    MarketData.symbol.in_(['AAPL', 'GOOGL', 'MSFT']),
    MarketData.timeframe == '1d'
).order_by(MarketData.timestamp.desc()).limit(100).all()
```

## Testing & Validation

### **Database Testing**
```bash
# Comprehensive database tests
python utils/db_test.py test

# Model-specific tests
python -m pytest tests/test_models.py -v

# Performance tests
python -m pytest tests/test_db.py::TestDatabasePerformance -v
```

### **Migration Management**
```bash
# Initialize migrations
flask db init

# Create migration
flask db migrate -m "Add new risk metrics"

# Apply migrations
flask db upgrade

# Migration utilities
python utils/migration_manager.py setup
python utils/migration_manager.py validate
```

### **Health Monitoring**
```bash
# Test endpoints
curl http://localhost:5000/health
curl http://localhost:5000/db-status
curl http://localhost:5000/db-test
```

## Production Considerations

### **Performance Monitoring**
- Connection pool monitoring via `/db-status` endpoint
- Query performance tracking with `SQLALCHEMY_ECHO = True` in development
- Database metrics collection for production monitoring

### **Backup Strategy**
```bash
# Automated backups (production)
python utils/migration_manager.py --config production upgrade
# Creates backup before applying migrations

# Manual backup
pg_dump -h localhost -U trading_user trading_db > backup.sql
```

### **Security**
- Connection string encryption in production
- Database user with minimal required permissions
- Regular security updates for PostgreSQL

### **Scalability**
- Read replicas for query-heavy workloads
- Connection pool tuning based on application load
- Table partitioning for large time-series datasets

This schema provides a robust, scalable foundation for a production trading platform with proper PostgreSQL optimizations, data integrity, and performance characteristics.