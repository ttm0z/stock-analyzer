from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Index, CheckConstraint, Numeric, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from .base import BaseModel

class RiskProfile(BaseModel):
    """Risk profile model for user risk management with PostgreSQL optimizations."""
    __tablename__ = 'risk_profiles'
    
    # Foreign key
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    
    # Profile identification
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    profile_type = Column(String(20), default='custom', nullable=False, index=True)
    
    # Risk tolerance settings
    risk_tolerance = Column(String(20), nullable=False, index=True)  # conservative, moderate, aggressive
    time_horizon = Column(String(20), nullable=False)  # short, medium, long
    investment_experience = Column(String(20), nullable=False)  # beginner, intermediate, expert
    
    # Position sizing rules - Using Numeric for precision
    max_position_size_pct = Column(Numeric(5, 2), default=10.0, nullable=False)  # % of portfolio
    max_sector_exposure_pct = Column(Numeric(5, 2), default=25.0, nullable=False)  # % of portfolio
    max_single_stock_pct = Column(Numeric(5, 2), default=5.0, nullable=False)   # % of portfolio
    max_correlation_threshold = Column(Numeric(5, 4), default=0.7, nullable=False)
    
    # Risk limits - Using Numeric for precision
    max_portfolio_var = Column(Numeric(8, 4), default=5.0, nullable=False)  # Value at Risk %
    max_expected_shortfall = Column(Numeric(8, 4), default=7.5, nullable=False)  # Expected Shortfall %
    max_drawdown_limit = Column(Numeric(8, 4), default=20.0, nullable=False)  # Max allowable drawdown %
    
    # Volatility constraints
    max_portfolio_volatility = Column(Numeric(8, 4), default=15.0, nullable=False)  # Annual volatility %
    target_sharpe_ratio = Column(Numeric(8, 4), default=1.0, nullable=False)
    
    # Leverage and margin settings
    max_leverage = Column(Numeric(5, 2), default=1.0, nullable=False)  # 1.0 = no leverage
    allow_margin = Column(Boolean, default=False, nullable=False)
    allow_short_selling = Column(Boolean, default=False, nullable=False)
    allow_options = Column(Boolean, default=False, nullable=False)
    
    # Asset class restrictions
    allowed_asset_classes = Column(JSONB, nullable=False)  # List of allowed asset classes
    forbidden_assets = Column(JSONB, nullable=True)       # List of forbidden symbols/sectors
    geographic_restrictions = Column(JSONB, nullable=True) # Geographic investment restrictions
    
    # Rebalancing rules
    rebalancing_frequency = Column(String(20), default='monthly', nullable=False)
    rebalancing_threshold = Column(Numeric(5, 2), default=5.0, nullable=False)  # % deviation trigger
    drift_tolerance = Column(Numeric(5, 2), default=2.0, nullable=False)  # % tolerance before rebalancing
    
    # Stop-loss and take-profit rules
    default_stop_loss_pct = Column(Numeric(5, 2), nullable=True)      # Default stop-loss %
    default_take_profit_pct = Column(Numeric(5, 2), nullable=True)    # Default take-profit %
    trailing_stop_enabled = Column(Boolean, default=False, nullable=False)
    
    # Profile status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_default = Column(Boolean, default=False, nullable=False)
    last_review_date = Column(DateTime, nullable=True)
    next_review_date = Column(DateTime, nullable=True)
    
    # Advanced risk settings stored as JSONB
    advanced_settings = Column(JSONB, nullable=True)
    custom_constraints = Column(JSONB, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="risk_profiles")
    risk_metrics = relationship("RiskMetrics", back_populates="risk_profile", cascade="all, delete-orphan")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_risk_profile_user_active', 'user_id', 'is_active'),
        Index('idx_risk_profile_type_tolerance', 'profile_type', 'risk_tolerance'),
        CheckConstraint('risk_tolerance IN (\'conservative\', \'moderate\', \'aggressive\')', name='ck_risk_tolerance_valid'),
        CheckConstraint('time_horizon IN (\'short\', \'medium\', \'long\')', name='ck_time_horizon_valid'),
        CheckConstraint('investment_experience IN (\'beginner\', \'intermediate\', \'expert\')', name='ck_investment_experience_valid'),
        CheckConstraint('profile_type IN (\'conservative\', \'moderate\', \'aggressive\', \'custom\')', name='ck_profile_type_valid'),
        CheckConstraint('max_position_size_pct > 0 AND max_position_size_pct <= 100', name='ck_max_position_size_valid'),
        CheckConstraint('max_sector_exposure_pct > 0 AND max_sector_exposure_pct <= 100', name='ck_max_sector_exposure_valid'),
        CheckConstraint('max_single_stock_pct > 0 AND max_single_stock_pct <= 100', name='ck_max_single_stock_valid'),
        CheckConstraint('max_correlation_threshold >= 0 AND max_correlation_threshold <= 1', name='ck_max_correlation_valid'),
        CheckConstraint('max_portfolio_var > 0 AND max_portfolio_var <= 100', name='ck_max_var_valid'),
        CheckConstraint('max_expected_shortfall > 0 AND max_expected_shortfall <= 100', name='ck_max_es_valid'),
        CheckConstraint('max_drawdown_limit > 0 AND max_drawdown_limit <= 100', name='ck_max_drawdown_valid'),
        CheckConstraint('max_portfolio_volatility > 0', name='ck_max_volatility_positive'),
        CheckConstraint('target_sharpe_ratio >= 0', name='ck_target_sharpe_non_negative'),
        CheckConstraint('max_leverage >= 1.0', name='ck_max_leverage_valid'),
        CheckConstraint('rebalancing_frequency IN (\'daily\', \'weekly\', \'monthly\', \'quarterly\', \'annual\')', name='ck_rebalancing_frequency_valid'),
        CheckConstraint('rebalancing_threshold > 0 AND rebalancing_threshold <= 100', name='ck_rebalancing_threshold_valid'),
        CheckConstraint('drift_tolerance > 0 AND drift_tolerance <= 100', name='ck_drift_tolerance_valid'),
    )

class RiskMetrics(BaseModel):
    """Risk metrics model for portfolio risk analysis with PostgreSQL optimizations."""
    __tablename__ = 'risk_metrics'
    
    # Foreign keys
    risk_profile_id = Column(Integer, ForeignKey('risk_profiles.id'), nullable=False, index=True)
    portfolio_id = Column(Integer, ForeignKey('portfolios.id'), nullable=True, index=True)
    
    # Calculation metadata
    calculation_date = Column(DateTime, nullable=False, index=True)
    data_start_date = Column(DateTime, nullable=False)
    data_end_date = Column(DateTime, nullable=False)
    lookback_days = Column(Integer, default=252, nullable=False)  # Trading days
    
    # Basic risk metrics - Using Numeric for precision
    portfolio_value = Column(Numeric(15, 2), nullable=False)
    daily_volatility = Column(Numeric(8, 6), nullable=True)
    annual_volatility = Column(Numeric(8, 4), nullable=True)
    
    # Value at Risk (VaR) metrics
    var_1d_95 = Column(Numeric(15, 2), nullable=True)   # 1-day 95% VaR
    var_1d_99 = Column(Numeric(15, 2), nullable=True)   # 1-day 99% VaR
    var_10d_95 = Column(Numeric(15, 2), nullable=True)  # 10-day 95% VaR
    var_10d_99 = Column(Numeric(15, 2), nullable=True)  # 10-day 99% VaR
    
    # Expected Shortfall (Conditional VaR)
    es_1d_95 = Column(Numeric(15, 2), nullable=True)    # 1-day 95% Expected Shortfall
    es_1d_99 = Column(Numeric(15, 2), nullable=True)    # 1-day 99% Expected Shortfall
    
    # Drawdown analysis - Using Numeric for precision
    current_drawdown = Column(Numeric(8, 4), default=0.0, nullable=False)
    max_drawdown = Column(Numeric(8, 4), default=0.0, nullable=False)
    max_drawdown_duration = Column(Integer, default=0, nullable=False)  # Days
    high_water_mark = Column(Numeric(15, 2), nullable=False)
    
    # Beta and correlation analysis
    market_beta = Column(Numeric(8, 4), nullable=True)
    market_correlation = Column(Numeric(8, 4), nullable=True)
    benchmark_correlation = Column(Numeric(8, 4), nullable=True)
    
    # Portfolio concentration metrics
    concentration_hhi = Column(Numeric(8, 4), nullable=True)  # Herfindahl-Hirschman Index
    effective_positions = Column(Numeric(8, 2), nullable=True)  # 1/HHI
    largest_position_weight = Column(Numeric(5, 2), nullable=True)
    top_5_concentration = Column(Numeric(5, 2), nullable=True)  # Weight of top 5 positions
    top_10_concentration = Column(Numeric(5, 2), nullable=True) # Weight of top 10 positions
    
    # Sector and geographic concentration
    sector_concentration = Column(JSONB, nullable=True)    # Sector weights and concentration
    geographic_concentration = Column(JSONB, nullable=True) # Geographic exposure breakdown
    
    # Risk factor exposures
    size_factor_exposure = Column(Numeric(8, 4), nullable=True)    # Small vs Large cap exposure
    value_factor_exposure = Column(Numeric(8, 4), nullable=True)   # Value vs Growth exposure
    momentum_factor_exposure = Column(Numeric(8, 4), nullable=True) # Momentum factor exposure
    quality_factor_exposure = Column(Numeric(8, 4), nullable=True)  # Quality factor exposure
    
    # Liquidity risk metrics
    avg_daily_volume_ratio = Column(Numeric(8, 4), nullable=True)  # Portfolio volume / market volume
    liquidity_score = Column(Numeric(5, 2), nullable=True)         # Composite liquidity score (1-10)
    days_to_liquidate = Column(Numeric(8, 2), nullable=True)       # Estimated days to liquidate 50%
    
    # Tail risk metrics
    skewness = Column(Numeric(8, 4), nullable=True)
    kurtosis = Column(Numeric(8, 4), nullable=True)
    downside_deviation = Column(Numeric(8, 4), nullable=True)
    upside_capture = Column(Numeric(8, 4), nullable=True)
    downside_capture = Column(Numeric(8, 4), nullable=True)
    
    # Stress test results stored as JSONB
    stress_test_results = Column(JSONB, nullable=True)  # Scenario analysis results
    monte_carlo_results = Column(JSONB, nullable=True)  # Monte Carlo simulation results
    
    # Risk limit violations
    risk_violations = Column(JSONB, nullable=True)      # List of current risk limit violations
    warning_flags = Column(JSONB, nullable=True)        # Risk warning flags
    
    # Calculation metadata
    calculation_method = Column(String(50), default='historical', nullable=False)
    confidence_level = Column(Numeric(5, 4), default=0.95, nullable=False)
    
    # Relationships
    risk_profile = relationship("RiskProfile", back_populates="risk_metrics")
    portfolio = relationship("Portfolio")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_risk_metrics_profile_date', 'risk_profile_id', 'calculation_date'),
        Index('idx_risk_metrics_portfolio_date', 'portfolio_id', 'calculation_date'),
        Index('idx_risk_metrics_var', 'var_1d_95', 'var_1d_99'),
        Index('idx_risk_metrics_drawdown', 'current_drawdown', 'max_drawdown'),
        CheckConstraint('portfolio_value > 0', name='ck_portfolio_value_positive'),
        CheckConstraint('lookback_days > 0', name='ck_lookback_days_positive'),
        CheckConstraint('daily_volatility >= 0 OR daily_volatility IS NULL', name='ck_daily_volatility_non_negative'),
        CheckConstraint('annual_volatility >= 0 OR annual_volatility IS NULL', name='ck_annual_volatility_non_negative'),
        CheckConstraint('current_drawdown >= 0', name='ck_current_drawdown_non_negative'),
        CheckConstraint('max_drawdown >= 0', name='ck_max_drawdown_non_negative'),
        CheckConstraint('max_drawdown_duration >= 0', name='ck_max_drawdown_duration_non_negative'),
        CheckConstraint('market_beta >= -5 AND market_beta <= 5 OR market_beta IS NULL', name='ck_market_beta_reasonable'),
        CheckConstraint('market_correlation >= -1 AND market_correlation <= 1 OR market_correlation IS NULL', name='ck_market_correlation_valid'),
        CheckConstraint('concentration_hhi >= 0 AND concentration_hhi <= 1 OR concentration_hhi IS NULL', name='ck_hhi_valid'),
        CheckConstraint('largest_position_weight >= 0 AND largest_position_weight <= 100 OR largest_position_weight IS NULL', name='ck_largest_position_valid'),
        CheckConstraint('confidence_level > 0 AND confidence_level < 1', name='ck_confidence_level_valid'),
        CheckConstraint('calculation_method IN (\'historical\', \'parametric\', \'monte_carlo\')', name='ck_calculation_method_valid'),
        CheckConstraint('data_end_date >= data_start_date', name='ck_data_dates_valid'),
    )
    
    def calculate_portfolio_beta(self, portfolio_returns, market_returns):
        """Calculate portfolio beta against market."""
        # This would typically use numpy/pandas for calculation
        # Simplified implementation here
        import numpy as np
        if len(portfolio_returns) != len(market_returns) or len(portfolio_returns) == 0:
            return None
        
        covariance = np.cov(portfolio_returns, market_returns)[0][1]
        market_variance = np.var(market_returns)
        
        if market_variance == 0:
            return None
        
        return covariance / market_variance
    
    def calculate_var(self, returns, confidence_level=0.95):
        """Calculate Value at Risk from returns."""
        import numpy as np
        if len(returns) == 0:
            return None
        
        percentile = (1 - confidence_level) * 100
        return np.percentile(returns, percentile) * self.portfolio_value
    
    def calculate_expected_shortfall(self, returns, confidence_level=0.95):
        """Calculate Expected Shortfall (Conditional VaR)."""
        import numpy as np
        if len(returns) == 0:
            return None
        
        var_threshold = np.percentile(returns, (1 - confidence_level) * 100)
        tail_returns = returns[returns <= var_threshold]
        
        if len(tail_returns) == 0:
            return None
        
        return np.mean(tail_returns) * self.portfolio_value
    
class RiskLimit(BaseModel):
    """Risk limits and thresholds."""
    __tablename__ = 'risk_limits'
    
    # Foreign keys
    portfolio_id = Column(Integer, ForeignKey('portfolios.id'), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    
    # Limit definition
    limit_type = Column(String(50), nullable=False, index=True)  # MAX_POSITION_SIZE, MAX_DRAWDOWN, etc.
    limit_value = Column(Numeric(15, 2), nullable=False)
    limit_unit = Column(String(20), nullable=False)  # PERCENT, DOLLAR, SHARES
    
    # Scope
    symbol = Column(String(20), nullable=True, index=True)  # NULL for portfolio-wide limits
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    portfolio = relationship("Portfolio", backref="risk_limits")
    user = relationship("User", backref="risk_limits")


class RiskViolation(BaseModel):
    """Risk limit violations."""
    __tablename__ = 'risk_violations'
    
    # Foreign keys  
    risk_limit_id = Column(Integer, ForeignKey('risk_limits.id'), nullable=False, index=True)
    portfolio_id = Column(Integer, ForeignKey('portfolios.id'), nullable=True, index=True)
    
    # Violation details
    violation_type = Column(String(50), nullable=False, index=True)
    violation_value = Column(Numeric(15, 2), nullable=False)
    limit_value = Column(Numeric(15, 2), nullable=False)
    severity = Column(String(20), default='MEDIUM', nullable=False)
    
    # Status
    is_resolved = Column(Boolean, default=False, nullable=False)
    resolution_date = Column(DateTime, nullable=True)
    
    # Relationships
    risk_limit = relationship("RiskLimit", backref="violations")
    portfolio = relationship("Portfolio", backref="risk_violations")


class RiskScenario(BaseModel):
    """Risk scenario definitions for stress testing."""
    __tablename__ = 'risk_scenarios'
    
    # Scenario identification
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    scenario_type = Column(String(50), nullable=False, index=True)  # MARKET_CRASH, VOLATILITY_SPIKE, etc.
    
    # Scenario parameters
    parameters = Column(JSONB, nullable=False)  # Scenario-specific parameters
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)


class StressTest(BaseModel):
    """Stress test results."""
    __tablename__ = 'stress_tests'
    
    # Foreign keys
    portfolio_id = Column(Integer, ForeignKey('portfolios.id'), nullable=False, index=True)
    risk_scenario_id = Column(Integer, ForeignKey('risk_scenarios.id'), nullable=False, index=True)
    
    # Test results
    portfolio_value_change = Column(Numeric(15, 2), nullable=False)
    portfolio_value_change_pct = Column(Numeric(8, 4), nullable=False)
    max_loss = Column(Numeric(15, 2), nullable=False)
    
    # Test metadata
    test_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    detailed_results = Column(JSONB, nullable=True)
    
    # Relationships
    portfolio = relationship("Portfolio", backref="stress_tests")
    risk_scenario = relationship("RiskScenario", backref="stress_tests")


class PositionRisk(BaseModel):
    """Individual position risk metrics."""
    __tablename__ = 'position_risk'
    
    # Foreign key
    position_id = Column(Integer, ForeignKey('positions.id'), nullable=False, unique=True, index=True)
    
    # Risk metrics
    var_1d = Column(Numeric(15, 2), nullable=True)  # 1-day Value at Risk
    var_5d = Column(Numeric(15, 2), nullable=True)  # 5-day Value at Risk
    beta = Column(Numeric(8, 4), nullable=True)
    correlation_to_market = Column(Numeric(8, 4), nullable=True)
    
    # Concentration risk
    portfolio_weight = Column(Numeric(8, 4), nullable=False)
    sector_concentration = Column(Numeric(8, 4), nullable=True)
    
    # Last updated
    last_calculation = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    position = relationship("Position", backref="risk_metrics")


class RiskAlert(BaseModel):
    """Risk alerts and notifications."""
    __tablename__ = 'risk_alerts'
    
    # Foreign keys
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    portfolio_id = Column(Integer, ForeignKey('portfolios.id'), nullable=True, index=True)
    
    # Alert details
    alert_type = Column(String(50), nullable=False, index=True)
    severity = Column(String(20), nullable=False, index=True)
    message = Column(Text, nullable=False)
    
    # Alert data
    alert_data = Column(JSONB, nullable=True)  # Additional alert context
    
    # Status
    is_acknowledged = Column(Boolean, default=False, nullable=False)
    acknowledged_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", backref="risk_alerts")
    portfolio = relationship("Portfolio", backref="risk_alerts")


class RiskModelConfiguration(BaseModel):
    """Risk model configuration and parameters."""
    __tablename__ = 'risk_model_configurations'
    
    # Configuration identification
    name = Column(String(200), nullable=False)
    model_type = Column(String(50), nullable=False, index=True)  # VAR, MONTE_CARLO, etc.
    version = Column(String(20), default='1.0', nullable=False)
    
    # Configuration parameters
    parameters = Column(JSONB, nullable=False)  # Model-specific parameters
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)