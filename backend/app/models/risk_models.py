from datetime import datetime
from .base import BaseModel
from ..db import db

class RiskProfile(BaseModel):
    """Risk profile model for user risk management with PostgreSQL optimizations."""
    __tablename__ = 'risk_profiles'
    
    # Foreign key
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Profile identification
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    profile_type = db.Column(db.String(20), default='custom', nullable=False, index=True)
    
    # Risk tolerance settings
    risk_tolerance = db.Column(db.String(20), nullable=False, index=True)  # conservative, moderate, aggressive
    time_horizon = db.Column(db.String(20), nullable=False)  # short, medium, long
    investment_experience = db.Column(db.String(20), nullable=False)  # beginner, intermediate, expert
    
    # Position sizing rules - Using Numeric for precision
    max_position_size_pct = db.Column(db.Numeric(5, 2), default=10.0, nullable=False)  # % of portfolio
    max_sector_exposure_pct = db.Column(db.Numeric(5, 2), default=25.0, nullable=False)  # % of portfolio
    max_single_stock_pct = db.Column(db.Numeric(5, 2), default=5.0, nullable=False)   # % of portfolio
    max_correlation_threshold = db.Column(db.Numeric(5, 4), default=0.7, nullable=False)
    
    # Risk limits - Using Numeric for precision
    max_portfolio_var = db.Column(db.Numeric(8, 4), default=5.0, nullable=False)  # Value at Risk %
    max_expected_shortfall = db.Column(db.Numeric(8, 4), default=7.5, nullable=False)  # Expected Shortfall %
    max_drawdown_limit = db.Column(db.Numeric(8, 4), default=20.0, nullable=False)  # Max allowable drawdown %
    
    # Volatility constraints
    max_portfolio_volatility = db.Column(db.Numeric(8, 4), default=15.0, nullable=False)  # Annual volatility %
    target_sharpe_ratio = db.Column(db.Numeric(8, 4), default=1.0, nullable=False)
    
    # Leverage and margin settings
    max_leverage = db.Column(db.Numeric(5, 2), default=1.0, nullable=False)  # 1.0 = no leverage
    allow_margin = db.Column(db.Boolean, default=False, nullable=False)
    allow_short_selling = db.Column(db.Boolean, default=False, nullable=False)
    allow_options = db.Column(db.Boolean, default=False, nullable=False)
    
    # Asset class restrictions
    allowed_asset_classes = db.Column(db.JSON, nullable=False)  # List of allowed asset classes
    forbidden_assets = db.Column(db.JSON, nullable=True)       # List of forbidden symbols/sectors
    geographic_restrictions = db.Column(db.JSON, nullable=True) # Geographic investment restrictions
    
    # Rebalancing rules
    rebalancing_frequency = db.Column(db.String(20), default='monthly', nullable=False)
    rebalancing_threshold = db.Column(db.Numeric(5, 2), default=5.0, nullable=False)  # % deviation trigger
    drift_tolerance = db.Column(db.Numeric(5, 2), default=2.0, nullable=False)  # % tolerance before rebalancing
    
    # Stop-loss and take-profit rules
    default_stop_loss_pct = db.Column(db.Numeric(5, 2), nullable=True)      # Default stop-loss %
    default_take_profit_pct = db.Column(db.Numeric(5, 2), nullable=True)    # Default take-profit %
    trailing_stop_enabled = db.Column(db.Boolean, default=False, nullable=False)
    
    # Profile status
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)
    is_default = db.Column(db.Boolean, default=False, nullable=False)
    last_review_date = db.Column(db.DateTime, nullable=True)
    next_review_date = db.Column(db.DateTime, nullable=True)
    
    # Advanced risk settings stored as JSON
    advanced_settings = db.Column(db.JSON, nullable=True)
    custom_constraints = db.Column(db.JSON, nullable=True)
    
    # Relationships
    user = db.relationship("User", back_populates="risk_profiles")
    risk_metrics = db.relationship("RiskMetrics", back_populates="risk_profile", cascade="all, delete-orphan")
    
    # Indexes for performance
    __table_args__ = (
        db.Index('idx_risk_profile_user_active', 'user_id', 'is_active'),
        db.Index('idx_risk_profile_type_tolerance', 'profile_type', 'risk_tolerance'),
        db.CheckConstraint('risk_tolerance IN (\'conservative\', \'moderate\', \'aggressive\')', name='ck_risk_tolerance_valid'),
        db.CheckConstraint('time_horizon IN (\'short\', \'medium\', \'long\')', name='ck_time_horizon_valid'),
        db.CheckConstraint('investment_experience IN (\'beginner\', \'intermediate\', \'expert\')', name='ck_investment_experience_valid'),
        db.CheckConstraint('profile_type IN (\'conservative\', \'moderate\', \'aggressive\', \'custom\')', name='ck_profile_type_valid'),
        db.CheckConstraint('max_position_size_pct > 0 AND max_position_size_pct <= 100', name='ck_max_position_size_valid'),
        db.CheckConstraint('max_sector_exposure_pct > 0 AND max_sector_exposure_pct <= 100', name='ck_max_sector_exposure_valid'),
        db.CheckConstraint('max_single_stock_pct > 0 AND max_single_stock_pct <= 100', name='ck_max_single_stock_valid'),
        db.CheckConstraint('max_correlation_threshold >= 0 AND max_correlation_threshold <= 1', name='ck_max_correlation_valid'),
        db.CheckConstraint('max_portfolio_var > 0 AND max_portfolio_var <= 100', name='ck_max_var_valid'),
        db.CheckConstraint('max_expected_shortfall > 0 AND max_expected_shortfall <= 100', name='ck_max_es_valid'),
        db.CheckConstraint('max_drawdown_limit > 0 AND max_drawdown_limit <= 100', name='ck_max_drawdown_valid'),
        db.CheckConstraint('max_portfolio_volatility > 0', name='ck_max_volatility_positive'),
        db.CheckConstraint('target_sharpe_ratio >= 0', name='ck_target_sharpe_non_negative'),
        db.CheckConstraint('max_leverage >= 1.0', name='ck_max_leverage_valid'),
        db.CheckConstraint('rebalancing_frequency IN (\'daily\', \'weekly\', \'monthly\', \'quarterly\', \'annual\')', name='ck_rebalancing_frequency_valid'),
        db.CheckConstraint('rebalancing_threshold > 0 AND rebalancing_threshold <= 100', name='ck_rebalancing_threshold_valid'),
        db.CheckConstraint('drift_tolerance > 0 AND drift_tolerance <= 100', name='ck_drift_tolerance_valid'),
    )

class RiskMetrics(BaseModel):
    """Risk metrics model for portfolio risk analysis with PostgreSQL optimizations."""
    __tablename__ = 'risk_metrics'
    
    # Foreign keys
    risk_profile_id = db.Column(db.Integer, db.ForeignKey('risk_profiles.id'), nullable=False, index=True)
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolios.id'), nullable=True, index=True)
    
    # Calculation metadata
    calculation_date = db.Column(db.DateTime, nullable=False, index=True)
    data_start_date = db.Column(db.DateTime, nullable=False)
    data_end_date = db.Column(db.DateTime, nullable=False)
    lookback_days = db.Column(db.Integer, default=252, nullable=False)  # Trading days
    
    # Basic risk metrics - Using Numeric for precision
    portfolio_value = db.Column(db.Numeric(15, 2), nullable=False)
    daily_volatility = db.Column(db.Numeric(8, 6), nullable=True)
    annual_volatility = db.Column(db.Numeric(8, 4), nullable=True)
    
    # Value at Risk (VaR) metrics
    var_1d_95 = db.Column(db.Numeric(15, 2), nullable=True)   # 1-day 95% VaR
    var_1d_99 = db.Column(db.Numeric(15, 2), nullable=True)   # 1-day 99% VaR
    var_10d_95 = db.Column(db.Numeric(15, 2), nullable=True)  # 10-day 95% VaR
    var_10d_99 = db.Column(db.Numeric(15, 2), nullable=True)  # 10-day 99% VaR
    
    # Expected Shortfall (Conditional VaR)
    es_1d_95 = db.Column(db.Numeric(15, 2), nullable=True)    # 1-day 95% Expected Shortfall
    es_1d_99 = db.Column(db.Numeric(15, 2), nullable=True)    # 1-day 99% Expected Shortfall
    
    # Drawdown analysis - Using Numeric for precision
    current_drawdown = db.Column(db.Numeric(8, 4), default=0.0, nullable=False)
    max_drawdown = db.Column(db.Numeric(8, 4), default=0.0, nullable=False)
    max_drawdown_duration = db.Column(db.Integer, default=0, nullable=False)  # Days
    high_water_mark = db.Column(db.Numeric(15, 2), nullable=False)
    
    # Beta and correlation analysis
    market_beta = db.Column(db.Numeric(8, 4), nullable=True)
    market_correlation = db.Column(db.Numeric(8, 4), nullable=True)
    benchmark_correlation = db.Column(db.Numeric(8, 4), nullable=True)
    
    # Portfolio concentration metrics
    concentration_hhi = db.Column(db.Numeric(8, 4), nullable=True)  # Herfindahl-Hirschman Index
    effective_positions = db.Column(db.Numeric(8, 2), nullable=True)  # 1/HHI
    largest_position_weight = db.Column(db.Numeric(5, 2), nullable=True)
    top_5_concentration = db.Column(db.Numeric(5, 2), nullable=True)  # Weight of top 5 positions
    top_10_concentration = db.Column(db.Numeric(5, 2), nullable=True) # Weight of top 10 positions
    
    # Sector and geographic concentration
    sector_concentration = db.Column(db.JSON, nullable=True)    # Sector weights and concentration
    geographic_concentration = db.Column(db.JSON, nullable=True) # Geographic exposure breakdown
    
    # Risk factor exposures
    size_factor_exposure = db.Column(db.Numeric(8, 4), nullable=True)    # Small vs Large cap exposure
    value_factor_exposure = db.Column(db.Numeric(8, 4), nullable=True)   # Value vs Growth exposure
    momentum_factor_exposure = db.Column(db.Numeric(8, 4), nullable=True) # Momentum factor exposure
    quality_factor_exposure = db.Column(db.Numeric(8, 4), nullable=True)  # Quality factor exposure
    
    # Liquidity risk metrics
    avg_daily_volume_ratio = db.Column(db.Numeric(8, 4), nullable=True)  # Portfolio volume / market volume
    liquidity_score = db.Column(db.Numeric(5, 2), nullable=True)         # Composite liquidity score (1-10)
    days_to_liquidate = db.Column(db.Numeric(8, 2), nullable=True)       # Estimated days to liquidate 50%
    
    # Tail risk metrics
    skewness = db.Column(db.Numeric(8, 4), nullable=True)
    kurtosis = db.Column(db.Numeric(8, 4), nullable=True)
    downside_deviation = db.Column(db.Numeric(8, 4), nullable=True)
    upside_capture = db.Column(db.Numeric(8, 4), nullable=True)
    downside_capture = db.Column(db.Numeric(8, 4), nullable=True)
    
    # Stress test results stored as JSON
    stress_test_results = db.Column(db.JSON, nullable=True)  # Scenario analysis results
    monte_carlo_results = db.Column(db.JSON, nullable=True)  # Monte Carlo simulation results
    
    # Risk limit violations
    risk_violations = db.Column(db.JSON, nullable=True)      # List of current risk limit violations
    warning_flags = db.Column(db.JSON, nullable=True)        # Risk warning flags
    
    # Calculation metadata
    calculation_method = db.Column(db.String(50), default='historical', nullable=False)
    confidence_level = db.Column(db.Numeric(5, 4), default=0.95, nullable=False)
    
    # Relationships
    risk_profile = db.relationship("RiskProfile", back_populates="risk_metrics")
    portfolio = db.relationship("Portfolio")
    
    # Indexes for performance
    __table_args__ = (
        db.Index('idx_risk_metrics_profile_date', 'risk_profile_id', 'calculation_date'),
        db.Index('idx_risk_metrics_portfolio_date', 'portfolio_id', 'calculation_date'),
        db.Index('idx_risk_metrics_var', 'var_1d_95', 'var_1d_99'),
        db.Index('idx_risk_metrics_drawdown', 'current_drawdown', 'max_drawdown'),
        db.CheckConstraint('portfolio_value > 0', name='ck_portfolio_value_positive'),
        db.CheckConstraint('lookback_days > 0', name='ck_lookback_days_positive'),
        db.CheckConstraint('daily_volatility >= 0 OR daily_volatility IS NULL', name='ck_daily_volatility_non_negative'),
        db.CheckConstraint('annual_volatility >= 0 OR annual_volatility IS NULL', name='ck_annual_volatility_non_negative'),
        db.CheckConstraint('current_drawdown >= 0', name='ck_current_drawdown_non_negative'),
        db.CheckConstraint('max_drawdown >= 0', name='ck_max_drawdown_non_negative'),
        db.CheckConstraint('max_drawdown_duration >= 0', name='ck_max_drawdown_duration_non_negative'),
        db.CheckConstraint('market_beta >= -5 AND market_beta <= 5 OR market_beta IS NULL', name='ck_market_beta_reasonable'),
        db.CheckConstraint('market_correlation >= -1 AND market_correlation <= 1 OR market_correlation IS NULL', name='ck_market_correlation_valid'),
        db.CheckConstraint('concentration_hhi >= 0 AND concentration_hhi <= 1 OR concentration_hhi IS NULL', name='ck_hhi_valid'),
        db.CheckConstraint('largest_position_weight >= 0 AND largest_position_weight <= 100 OR largest_position_weight IS NULL', name='ck_largest_position_valid'),
        db.CheckConstraint('confidence_level > 0 AND confidence_level < 1', name='ck_confidence_level_valid'),
        db.CheckConstraint('calculation_method IN (\'historical\', \'parametric\', \'monte_carlo\')', name='ck_calculation_method_valid'),
        db.CheckConstraint('data_end_date >= data_start_date', name='ck_data_dates_valid'),
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
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolios.id'), nullable=True, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Limit definition
    limit_type = db.Column(db.String(50), nullable=False, index=True)  # MAX_POSITION_SIZE, MAX_DRAWDOWN, etc.
    limit_value = db.Column(db.Numeric(15, 2), nullable=False)
    limit_unit = db.Column(db.String(20), nullable=False)  # PERCENT, DOLLAR, SHARES
    
    # Scope
    symbol = db.Column(db.String(20), nullable=True, index=True)  # NULL for portfolio-wide limits
    
    # Status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Relationships
    portfolio = db.relationship("Portfolio", backref="risk_limits")
    user = db.relationship("User", backref="risk_limits")


class RiskViolation(BaseModel):
    """Risk limit violations."""
    __tablename__ = 'risk_violations'
    
    # Foreign keys  
    risk_limit_id = db.Column(db.Integer, db.ForeignKey('risk_limits.id'), nullable=False, index=True)
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolios.id'), nullable=True, index=True)
    
    # Violation details
    violation_type = db.Column(db.String(50), nullable=False, index=True)
    violation_value = db.Column(db.Numeric(15, 2), nullable=False)
    limit_value = db.Column(db.Numeric(15, 2), nullable=False)
    severity = db.Column(db.String(20), default='MEDIUM', nullable=False)
    
    # Status
    is_resolved = db.Column(db.Boolean, default=False, nullable=False)
    resolution_date = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    risk_limit = db.relationship("RiskLimit", backref="violations")
    portfolio = db.relationship("Portfolio", backref="risk_violations")


class RiskScenario(BaseModel):
    """Risk scenario definitions for stress testing."""
    __tablename__ = 'risk_scenarios'
    
    # Scenario identification
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    scenario_type = db.Column(db.String(50), nullable=False, index=True)  # MARKET_CRASH, VOLATILITY_SPIKE, etc.
    
    # Scenario parameters
    parameters = db.Column(db.JSON, nullable=False)  # Scenario-specific parameters
    
    # Status
    is_active = db.Column(db.Boolean, default=True, nullable=False)


class StressTest(BaseModel):
    """Stress test results."""
    __tablename__ = 'stress_tests'
    
    # Foreign keys
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolios.id'), nullable=False, index=True)
    risk_scenario_id = db.Column(db.Integer, db.ForeignKey('risk_scenarios.id'), nullable=False, index=True)
    
    # Test results
    portfolio_value_change = db.Column(db.Numeric(15, 2), nullable=False)
    portfolio_value_change_pct = db.Column(db.Numeric(8, 4), nullable=False)
    max_loss = db.Column(db.Numeric(15, 2), nullable=False)
    
    # Test metadata
    test_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    detailed_results = db.Column(db.JSON, nullable=True)
    
    # Relationships
    portfolio = db.relationship("Portfolio", backref="stress_tests")
    risk_scenario = db.relationship("RiskScenario", backref="stress_tests")


class PositionRisk(BaseModel):
    """Individual position risk metrics."""
    __tablename__ = 'position_risk'
    
    # Foreign key
    position_id = db.Column(db.Integer, db.ForeignKey('positions.id'), nullable=False, unique=True, index=True)
    
    # Risk metrics
    var_1d = db.Column(db.Numeric(15, 2), nullable=True)  # 1-day Value at Risk
    var_5d = db.Column(db.Numeric(15, 2), nullable=True)  # 5-day Value at Risk
    beta = db.Column(db.Numeric(8, 4), nullable=True)
    correlation_to_market = db.Column(db.Numeric(8, 4), nullable=True)
    
    # Concentration risk
    portfolio_weight = db.Column(db.Numeric(8, 4), nullable=False)
    sector_concentration = db.Column(db.Numeric(8, 4), nullable=True)
    
    # Last updated
    last_calculation = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    position = db.relationship("Position", backref="risk_metrics")


class RiskAlert(BaseModel):
    """Risk alerts and notifications."""
    __tablename__ = 'risk_alerts'
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolios.id'), nullable=True, index=True)
    
    # Alert details
    alert_type = db.Column(db.String(50), nullable=False, index=True)
    severity = db.Column(db.String(20), nullable=False, index=True)
    message = db.Column(db.Text, nullable=False)
    
    # Alert data
    alert_data = db.Column(db.JSON, nullable=True)  # Additional alert context
    
    # Status
    is_acknowledged = db.Column(db.Boolean, default=False, nullable=False)
    acknowledged_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    user = db.relationship("User", backref="risk_alerts")
    portfolio = db.relationship("Portfolio", backref="risk_alerts")


class RiskModelConfiguration(BaseModel):
    """Risk model configuration and parameters."""
    __tablename__ = 'risk_model_configurations'
    
    # Configuration identification
    name = db.Column(db.String(200), nullable=False)
    model_type = db.Column(db.String(50), nullable=False, index=True)  # VAR, MONTE_CARLO, etc.
    version = db.Column(db.String(20), default='1.0', nullable=False)
    
    # Configuration parameters
    parameters = db.Column(db.JSON, nullable=False)  # Model-specific parameters
    
    # Status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_default = db.Column(db.Boolean, default=False, nullable=False)