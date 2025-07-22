from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.sqlite import JSON
from datetime import datetime
import json

from .base import BaseModel

class RiskProfile(BaseModel):
    """Risk profile settings for users/strategies"""
    __tablename__ = 'risk_profiles'
    
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    is_default = Column(Boolean, default=False, nullable=False)
    
    # Position sizing limits
    max_position_size = Column(Float, default=0.1, nullable=False)  # 10% of portfolio
    max_portfolio_risk = Column(Float, default=0.02, nullable=False)  # 2% max risk per trade
    max_sector_exposure = Column(Float, default=0.3, nullable=False)  # 30% max per sector
    max_correlation_exposure = Column(Float, default=0.5, nullable=False)  # 50% max correlated positions
    
    # Stop loss settings
    default_stop_loss = Column(Float, default=0.05, nullable=False)  # 5% stop loss
    max_stop_loss = Column(Float, default=0.15, nullable=False)  # 15% max stop loss
    trailing_stop_enabled = Column(Boolean, default=False, nullable=False)
    trailing_stop_distance = Column(Float, default=0.03, nullable=False)  # 3%
    
    # Leverage and margin
    max_leverage = Column(Float, default=1.0, nullable=False)  # No leverage by default
    margin_requirement = Column(Float, default=0.25, nullable=False)  # 25% margin requirement
    
    # Drawdown limits
    max_portfolio_drawdown = Column(Float, default=0.15, nullable=False)  # 15% max drawdown
    daily_loss_limit = Column(Float, default=0.03, nullable=False)  # 3% daily loss limit
    
    # Risk monitoring
    var_confidence_level = Column(Float, default=0.95, nullable=False)  # 95% VaR
    var_time_horizon = Column(Integer, default=1, nullable=False)  # 1 day
    stress_test_enabled = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    user = relationship("User")
    risk_limits = relationship("RiskLimit", back_populates="risk_profile", cascade="all, delete-orphan")
    
    # Index for efficient queries
    __table_args__ = (
        Index('idx_risk_profile_user_default', 'user_id', 'is_default'),
    )

class RiskLimit(BaseModel):
    """Specific risk limits and constraints"""
    __tablename__ = 'risk_limits'
    
    risk_profile_id = Column(Integer, ForeignKey('risk_profiles.id'), nullable=False)
    limit_type = Column(String(50), nullable=False)  # position_size, sector_exposure, correlation, etc.
    limit_name = Column(String(100), nullable=False)
    
    # Limit values
    max_value = Column(Float, nullable=True)
    min_value = Column(Float, nullable=True)
    target_value = Column(Float, nullable=True)
    
    # Limit scope
    applies_to = Column(String(50), nullable=False)  # portfolio, position, sector, asset_class
    scope_filter = Column(JSON, nullable=True)  # Filter criteria (sectors, symbols, etc.)
    
    # Limit behavior
    is_hard_limit = Column(Boolean, default=True, nullable=False)  # Hard vs soft limit
    warning_threshold = Column(Float, nullable=True)  # Warning level (% of limit)
    action_on_breach = Column(String(50), nullable=False)  # block, warn, reduce_position
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    risk_profile = relationship("RiskProfile", back_populates="risk_limits")
    violations = relationship("RiskViolation", back_populates="risk_limit", cascade="all, delete-orphan")
    
    # Index for efficient queries
    __table_args__ = (
        Index('idx_risk_limit_profile_type', 'risk_profile_id', 'limit_type'),
    )

class RiskMetrics(BaseModel):
    """Risk metrics calculations for portfolios"""
    __tablename__ = 'risk_metrics'
    
    portfolio_id = Column(Integer, ForeignKey('portfolios.id'), nullable=False)
    calculation_date = Column(DateTime, nullable=False, index=True)
    
    # Value at Risk metrics
    var_1d_95 = Column(Float, nullable=True)  # 1-day 95% VaR
    var_1d_99 = Column(Float, nullable=True)  # 1-day 99% VaR
    var_10d_95 = Column(Float, nullable=True)  # 10-day 95% VaR
    cvar_1d_95 = Column(Float, nullable=True)  # 1-day 95% CVaR
    cvar_1d_99 = Column(Float, nullable=True)  # 1-day 99% CVaR
    
    # Volatility metrics
    realized_volatility = Column(Float, nullable=True)  # 30-day realized vol
    implied_volatility = Column(Float, nullable=True)  # Portfolio implied vol
    volatility_forecast = Column(Float, nullable=True)  # GARCH/EWMA forecast
    
    # Drawdown metrics
    current_drawdown = Column(Float, nullable=True)
    max_drawdown_1y = Column(Float, nullable=True)
    drawdown_duration = Column(Integer, nullable=True)  # Days in drawdown
    
    # Correlation and concentration
    portfolio_correlation = Column(Float, nullable=True)  # Avg pairwise correlation
    concentration_hhi = Column(Float, nullable=True)  # Herfindahl-Hirschman Index
    effective_positions = Column(Float, nullable=True)  # 1/sum(weight^2)
    
    # Greek-like sensitivities
    market_beta = Column(Float, nullable=True)
    sector_exposures = Column(JSON, nullable=True)  # Sector exposure breakdown
    factor_exposures = Column(JSON, nullable=True)  # Risk factor exposures
    
    # Stress testing
    stress_test_results = Column(JSON, nullable=True)  # Scenario analysis results
    
    # Relationships
    portfolio = relationship("Portfolio")
    
    # Index for efficient queries
    __table_args__ = (
        Index('idx_risk_metrics_portfolio_date', 'portfolio_id', 'calculation_date'),
    )

class RiskViolation(BaseModel):
    """Risk limit violations and breaches"""
    __tablename__ = 'risk_violations'
    
    risk_limit_id = Column(Integer, ForeignKey('risk_limits.id'), nullable=False)
    portfolio_id = Column(Integer, ForeignKey('portfolios.id'), nullable=True)
    
    # Violation details
    violation_type = Column(String(50), nullable=False)  # breach, warning, approach
    violation_date = Column(DateTime, nullable=False, index=True)
    current_value = Column(Float, nullable=False)
    limit_value = Column(Float, nullable=False)
    breach_amount = Column(Float, nullable=False)  # How much over/under limit
    breach_percentage = Column(Float, nullable=False)  # % over/under limit
    
    # Context
    affected_positions = Column(JSON, nullable=True)  # Positions involved
    violation_context = Column(JSON, nullable=True)  # Additional context data
    
    # Resolution
    is_resolved = Column(Boolean, default=False, nullable=False)
    resolution_date = Column(DateTime, nullable=True)
    resolution_action = Column(String(100), nullable=True)  # Action taken to resolve
    resolution_notes = Column(Text, nullable=True)
    
    # Impact assessment
    estimated_impact = Column(Float, nullable=True)  # Estimated P&L impact
    actual_impact = Column(Float, nullable=True)  # Actual P&L impact
    
    # Notification status
    notification_sent = Column(Boolean, default=False, nullable=False)
    notification_method = Column(String(50), nullable=True)  # email, sms, push
    acknowledged_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    
    # Relationships
    risk_limit = relationship("RiskLimit", back_populates="violations")
    portfolio = relationship("Portfolio")
    acknowledger = relationship("User")
    
    # Index for efficient queries
    __table_args__ = (
        Index('idx_risk_violation_date_resolved', 'violation_date', 'is_resolved'),
        Index('idx_risk_violation_portfolio', 'portfolio_id'),
    )

class RiskScenario(BaseModel):
    """Stress test scenarios for risk assessment"""
    __tablename__ = 'risk_scenarios'
    
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    scenario_type = Column(String(50), nullable=False)  # historical, hypothetical, monte_carlo
    
    # Scenario parameters
    market_shock = Column(Float, nullable=True)  # Market index change %
    volatility_shock = Column(Float, nullable=True)  # Volatility multiplier
    correlation_shock = Column(Float, nullable=True)  # Correlation change
    
    # Asset-specific shocks
    asset_shocks = Column(JSON, nullable=True)  # Symbol-specific shocks
    sector_shocks = Column(JSON, nullable=True)  # Sector-specific shocks
    factor_shocks = Column(JSON, nullable=True)  # Risk factor shocks
    
    # Scenario metadata
    probability = Column(Float, nullable=True)  # Estimated probability
    time_horizon = Column(Integer, default=1, nullable=False)  # Days
    
    # Historical reference
    reference_date = Column(DateTime, nullable=True)  # For historical scenarios
    reference_event = Column(String(200), nullable=True)  # Event description
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    stress_tests = relationship("StressTest", back_populates="scenario", cascade="all, delete-orphan")

class StressTest(BaseModel):
    """Stress test results for portfolios"""
    __tablename__ = 'stress_tests'
    
    portfolio_id = Column(Integer, ForeignKey('portfolios.id'), nullable=False)
    scenario_id = Column(Integer, ForeignKey('risk_scenarios.id'), nullable=False)
    test_date = Column(DateTime, nullable=False, index=True)
    
    # Test results
    base_portfolio_value = Column(Float, nullable=False)
    stressed_portfolio_value = Column(Float, nullable=False)
    absolute_loss = Column(Float, nullable=False)
    percentage_loss = Column(Float, nullable=False)
    
    # Position-level impacts
    position_impacts = Column(JSON, nullable=True)  # Impact by position
    sector_impacts = Column(JSON, nullable=True)  # Impact by sector
    
    # Risk metrics under stress
    stressed_var = Column(Float, nullable=True)
    stressed_volatility = Column(Float, nullable=True)
    stressed_correlation = Column(Float, nullable=True)
    
    # Liquidity impact
    liquidity_cost = Column(Float, nullable=True)  # Cost to liquidate
    liquidation_time = Column(Integer, nullable=True)  # Days to liquidate
    
    # Relationships
    portfolio = relationship("Portfolio")
    scenario = relationship("RiskScenario", back_populates="stress_tests")
    
    # Index for efficient queries
    __table_args__ = (
        Index('idx_stress_test_portfolio_date', 'portfolio_id', 'test_date'),
    )

class PositionRisk(BaseModel):
    """Risk metrics for individual positions"""
    __tablename__ = 'position_risk'
    
    position_id = Column(Integer, ForeignKey('positions.id'), nullable=False)
    calculation_date = Column(DateTime, nullable=False, index=True)
    
    # Basic risk metrics
    position_var = Column(Float, nullable=True)  # Position VaR
    position_volatility = Column(Float, nullable=True)  # Historical volatility
    beta_to_market = Column(Float, nullable=True)  # Market beta
    
    # Concentration risk
    portfolio_weight = Column(Float, nullable=False)
    risk_contribution = Column(Float, nullable=True)  # % of portfolio risk
    marginal_var = Column(Float, nullable=True)  # Marginal VaR
    component_var = Column(Float, nullable=True)  # Component VaR
    
    # Correlation metrics
    correlation_to_portfolio = Column(Float, nullable=True)
    avg_correlation = Column(Float, nullable=True)  # Avg correlation to other positions
    max_correlation = Column(Float, nullable=True)  # Max correlation to any position
    
    # Liquidity risk
    avg_daily_volume = Column(Float, nullable=True)  # 30-day avg volume
    volume_ratio = Column(Float, nullable=True)  # Position size / avg volume
    bid_ask_spread = Column(Float, nullable=True)  # Current spread
    liquidity_score = Column(Float, nullable=True)  # 0-100 liquidity score
    
    # Event risk
    earnings_date = Column(DateTime, nullable=True)  # Next earnings
    dividend_date = Column(DateTime, nullable=True)  # Next dividend
    events_risk_score = Column(Float, nullable=True)  # 0-100 event risk
    
    # Technical risk indicators
    rsi = Column(Float, nullable=True)  # Relative Strength Index
    volatility_percentile = Column(Float, nullable=True)  # Current vol vs historical
    momentum_score = Column(Float, nullable=True)  # Price momentum
    
    # Relationships
    position = relationship("Position")
    
    # Index for efficient queries
    __table_args__ = (
        Index('idx_position_risk_date', 'position_id', 'calculation_date'),
    )

class RiskAlert(BaseModel):
    """Risk alerts and notifications"""
    __tablename__ = 'risk_alerts'
    
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    portfolio_id = Column(Integer, ForeignKey('portfolios.id'), nullable=True)
    
    # Alert details
    alert_type = Column(String(50), nullable=False)  # limit_breach, high_risk, correlation, etc.
    severity = Column(String(20), nullable=False)  # low, medium, high, critical
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    
    # Alert triggers
    trigger_value = Column(Float, nullable=True)
    threshold_value = Column(Float, nullable=True)
    trigger_condition = Column(String(50), nullable=True)  # greater_than, less_than, equals
    
    # Alert metadata
    alert_date = Column(DateTime, nullable=False, index=True)
    expiry_date = Column(DateTime, nullable=True)
    
    # Status tracking
    is_acknowledged = Column(Boolean, default=False, nullable=False)
    acknowledged_at = Column(DateTime, nullable=True)
    acknowledged_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    # Notification tracking
    notification_sent = Column(Boolean, default=False, nullable=False)
    notification_methods = Column(JSON, nullable=True)  # List of notification methods used
    
    # Resolution
    is_resolved = Column(Boolean, default=False, nullable=False)
    resolved_at = Column(DateTime, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    
    # Additional context
    related_data = Column(JSON, nullable=True)  # Additional context data
    
    # Relationships
    user = relationship("User")
    portfolio = relationship("Portfolio")
    acknowledger = relationship("User", foreign_keys=[acknowledged_by])
    
    # Index for efficient queries
    __table_args__ = (
        Index('idx_risk_alert_user_date', 'user_id', 'alert_date'),
        Index('idx_risk_alert_severity_resolved', 'severity', 'is_resolved'),
    )

class RiskModelConfiguration(BaseModel):
    """Configuration for risk models and calculations"""
    __tablename__ = 'risk_model_configurations'
    
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    model_type = Column(String(50), nullable=False)  # var, stress_test, correlation, etc.
    
    # Model parameters
    lookback_period = Column(Integer, nullable=False)  # Days of historical data
    confidence_level = Column(Float, nullable=False)  # For VaR calculations
    decay_factor = Column(Float, nullable=True)  # For EWMA models
    
    # Calculation settings
    calculation_frequency = Column(String(20), nullable=False)  # daily, weekly, monthly
    auto_update = Column(Boolean, default=True, nullable=False)
    
    # Model configuration
    model_parameters = Column(JSON, nullable=True)  # Model-specific parameters
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    last_calibration = Column(DateTime, nullable=True)
    next_calibration = Column(DateTime, nullable=True)
    
    # Performance tracking
    model_accuracy = Column(Float, nullable=True)  # Backtesting accuracy
    last_validation = Column(DateTime, nullable=True)
    
    def to_dict(self):
        """Convert to dictionary with JSON parsing"""
        data = super().to_dict()
        if self.model_parameters:
            data['model_parameters'] = json.loads(self.model_parameters) if isinstance(self.model_parameters, str) else self.model_parameters
        return data