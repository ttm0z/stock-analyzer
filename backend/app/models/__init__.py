"""
Database models for the backtesting engine.

This module contains all SQLAlchemy models for the backtesting system,
organized by functional area.
"""

from .base import BaseModel, TimestampMixin

# User and authentication models - import from auth module
# Note: User and APIKey are imported directly from auth.models where needed to avoid circular imports
from .user_models import (
    UserSession, UserPreferences
)

# Market data models
from .market_data import (
    Asset, MarketData, Benchmark, MarketDataAdjustment, DataSource, DataQuality, MarketCalendar
)

# Strategy models
from .strategy_models import (
    Strategy, StrategyParameter, StrategyTemplate, StrategyLibrary,
    StrategyValidation, StrategyPerformance
)

# Backtest models
from .backtest_models import (
    Backtest, BacktestPerformance, Trade, Signal, BacktestLog, BacktestComparison
)

# Portfolio models
from .portfolio_models import (
    Portfolio, Position, Transaction, PortfolioSnapshot, Order, OrderFill
)

# Risk management models
from .risk_models import (
    RiskProfile, RiskLimit, RiskMetrics, RiskViolation, RiskScenario,
    StressTest, PositionRisk, RiskAlert, RiskModelConfiguration
)

# All models for easy import
__all__ = [
    # Base
    'BaseModel', 'TimestampMixin',
    
    # User models (User and APIKey imported separately from auth.models)
    'UserSession', 'UserPreferences',
    
    # Market data models
    'Asset', 'MarketData', 'MarketDataAdjustment', 'DataSource',
    'DataQuality', 'MarketCalendar', 'Benchmark',
    
    # Strategy models
    'Strategy', 'StrategyParameter', 'StrategyTemplate', 'StrategyLibrary',
    'StrategyValidation', 'StrategyPerformance',
    
    # Backtest models
    'Backtest', 'BacktestPerformance', 'Trade', 'Signal', 'BacktestLog', 'BacktestComparison',
    
    # Portfolio models
    'Portfolio', 'Position', 'Transaction', 'PortfolioSnapshot', 'Order', 'OrderFill',
    
    # Risk models
    'RiskProfile', 'RiskLimit', 'RiskMetrics', 'RiskViolation', 'RiskScenario',
    'StressTest', 'PositionRisk', 'RiskAlert', 'RiskModelConfiguration'
]

# Model groups for convenience
USER_MODELS = [UserSession, UserPreferences]  # User and APIKey imported separately from auth.models
MARKET_DATA_MODELS = [Asset, MarketData, MarketDataAdjustment, DataSource, DataQuality, MarketCalendar, Benchmark]
STRATEGY_MODELS = [Strategy, StrategyParameter, StrategyTemplate, StrategyLibrary, StrategyValidation, StrategyPerformance]
BACKTEST_MODELS = [Backtest, BacktestPerformance, Trade, Signal, BacktestLog, BacktestComparison]
PORTFOLIO_MODELS = [Portfolio, Position, Transaction, PortfolioSnapshot, Order, OrderFill]
RISK_MODELS = [RiskProfile, RiskLimit, RiskMetrics, RiskViolation, RiskScenario, StressTest, PositionRisk, RiskAlert, RiskModelConfiguration]

ALL_MODELS = (
    USER_MODELS + 
    MARKET_DATA_MODELS + 
    STRATEGY_MODELS + 
    BACKTEST_MODELS + 
    PORTFOLIO_MODELS + 
    RISK_MODELS
)