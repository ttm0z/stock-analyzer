"""
Risk analysis for portfolio and strategy risk assessment.
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import scipy.stats as stats
from scipy.optimize import minimize

logger = logging.getLogger(__name__)

@dataclass
class RiskMetrics:
    """Container for risk analysis metrics"""
    # Value at Risk metrics
    var_1d_95: float = 0.0
    var_1d_99: float = 0.0
    var_10d_95: float = 0.0
    cvar_1d_95: float = 0.0  # Conditional VaR (Expected Shortfall)
    cvar_1d_99: float = 0.0
    
    # Volatility metrics
    realized_volatility: float = 0.0
    garch_volatility: float = 0.0
    volatility_forecast: float = 0.0
    
    # Drawdown metrics
    current_drawdown: float = 0.0
    max_drawdown_1y: float = 0.0
    drawdown_duration: int = 0
    
    # Correlation and concentration
    portfolio_correlation: float = 0.0
    concentration_hhi: float = 0.0  # Herfindahl-Hirschman Index
    effective_positions: float = 0.0
    
    # Factor exposures
    market_beta: float = 0.0
    sector_concentration: Dict[str, float] = None
    
    # Stress testing
    stress_test_scenarios: Dict[str, float] = None
    
    # Tail risk
    skewness: float = 0.0
    kurtosis: float = 0.0
    tail_ratio: float = 0.0

class RiskAnalyzer:
    """Comprehensive risk analysis for portfolios and strategies"""
    
    def __init__(self, confidence_levels: List[float] = None):
        self.confidence_levels = confidence_levels or [0.95, 0.99]
        self.trading_days_per_year = 252
        self.risk_free_rate = 0.02  # 2% annual risk-free rate
        
    def analyze_portfolio_risk(self, returns: pd.Series, 
                              positions: Dict[str, float] = None,
                              market_data: Dict[str, pd.DataFrame] = None,
                              benchmark_returns: pd.Series = None) -> RiskMetrics:
        """
        Comprehensive portfolio risk analysis
        
        Args:
            returns: Portfolio return series
            positions: Current position weights
            market_data: Individual asset price data
            benchmark_returns: Benchmark return series
        
        Returns:
            RiskMetrics object
        """
        metrics = RiskMetrics()
        
        if returns.empty:
            logger.warning("Empty returns series provided")
            return metrics
        
        try:
            # Basic risk metrics
            self._calculate_var_metrics(returns, metrics)
            self._calculate_volatility_metrics(returns, metrics)
            self._calculate_drawdown_metrics(returns, metrics)
            self._calculate_distribution_metrics(returns, metrics)
            
            # Portfolio-specific metrics
            if positions and market_data:
                self._calculate_concentration_metrics(positions, metrics)
                self._calculate_correlation_metrics(positions, market_data, metrics)
            
            # Benchmark comparison
            if benchmark_returns is not None:
                self._calculate_market_risk_metrics(returns, benchmark_returns, metrics)
            
            # Stress testing
            self._perform_stress_tests(returns, metrics)
            
        except Exception as e:
            logger.error(f"Error in risk analysis: {str(e)}")
        
        return metrics
    
    def _calculate_var_metrics(self, returns: pd.Series, metrics: RiskMetrics):
        """Calculate Value at Risk metrics"""
        if len(returns) < 30:  # Need sufficient data
            return
        
        # Historical VaR
        for confidence in self.confidence_levels:
            var_value = np.percentile(returns, (1 - confidence) * 100)
            
            if confidence == 0.95:
                metrics.var_1d_95 = abs(var_value)
                # CVaR (Expected Shortfall)
                tail_returns = returns[returns <= var_value]
                if len(tail_returns) > 0:
                    metrics.cvar_1d_95 = abs(tail_returns.mean())
            
            elif confidence == 0.99:
                metrics.var_1d_99 = abs(var_value)
                tail_returns = returns[returns <= var_value]
                if len(tail_returns) > 0:
                    metrics.cvar_1d_99 = abs(tail_returns.mean())
        
        # Multi-day VaR (10-day)
        if len(returns) >= 10:
            # Using square root of time scaling
            metrics.var_10d_95 = metrics.var_1d_95 * np.sqrt(10)
    
    def _calculate_volatility_metrics(self, returns: pd.Series, metrics: RiskMetrics):
        """Calculate volatility metrics"""
        if len(returns) < 2:
            return
        
        # Realized volatility (annualized)
        metrics.realized_volatility = returns.std() * np.sqrt(self.trading_days_per_year)
        
        # GARCH volatility forecast
        try:
            garch_vol = self._calculate_garch_volatility(returns)
            metrics.garch_volatility = garch_vol
            metrics.volatility_forecast = garch_vol
        except Exception as e:
            logger.warning(f"GARCH calculation failed: {str(e)}")
            metrics.volatility_forecast = metrics.realized_volatility
    
    def _calculate_garch_volatility(self, returns: pd.Series, 
                                   alpha: float = 0.1, beta: float = 0.85) -> float:
        """Calculate GARCH(1,1) volatility forecast"""
        if len(returns) < 50:
            return returns.std() * np.sqrt(self.trading_days_per_year)
        
        # Simple GARCH(1,1) implementation
        returns_clean = returns.dropna()
        
        # Initialize
        long_term_var = returns_clean.var()
        garch_var = long_term_var
        
        # Iterate through returns
        for ret in returns_clean[-50:]:  # Use last 50 observations
            garch_var = (1 - alpha - beta) * long_term_var + alpha * (ret ** 2) + beta * garch_var
        
        return np.sqrt(garch_var * self.trading_days_per_year)
    
    def _calculate_drawdown_metrics(self, returns: pd.Series, metrics: RiskMetrics):
        """Calculate drawdown metrics"""
        if len(returns) < 2:
            return
        
        # Convert returns to cumulative wealth
        cumulative_returns = (1 + returns).cumprod()
        
        # Calculate running maximum
        running_max = cumulative_returns.expanding().max()
        
        # Calculate drawdown
        drawdown = (cumulative_returns - running_max) / running_max
        
        # Current drawdown
        metrics.current_drawdown = abs(drawdown.iloc[-1])
        
        # Maximum drawdown in last year
        if len(returns) >= self.trading_days_per_year:
            recent_drawdown = drawdown.tail(self.trading_days_per_year)
            metrics.max_drawdown_1y = abs(recent_drawdown.min())
        else:
            metrics.max_drawdown_1y = abs(drawdown.min())
        
        # Drawdown duration (days in current drawdown)
        current_dd_duration = 0
        for i in range(len(drawdown) - 1, -1, -1):
            if drawdown.iloc[i] < 0:
                current_dd_duration += 1
            else:
                break
        
        metrics.drawdown_duration = current_dd_duration
    
    def _calculate_distribution_metrics(self, returns: pd.Series, metrics: RiskMetrics):
        """Calculate return distribution metrics"""
        if len(returns) < 4:
            return
        
        # Skewness and kurtosis
        metrics.skewness = stats.skew(returns)
        metrics.kurtosis = stats.kurtosis(returns)
        
        # Tail ratio (95th percentile / 5th percentile)
        p95 = np.percentile(returns, 95)
        p5 = np.percentile(returns, 5)
        if p5 != 0:
            metrics.tail_ratio = abs(p95 / p5)
    
    def _calculate_concentration_metrics(self, positions: Dict[str, float], 
                                       metrics: RiskMetrics):
        """Calculate portfolio concentration metrics"""
        if not positions:
            return
        
        weights = np.array(list(positions.values()))
        weights = np.abs(weights)  # Use absolute values
        
        if weights.sum() == 0:
            return
        
        # Normalize weights
        weights = weights / weights.sum()
        
        # Herfindahl-Hirschman Index
        metrics.concentration_hhi = np.sum(weights ** 2)
        
        # Effective number of positions
        metrics.effective_positions = 1 / metrics.concentration_hhi if metrics.concentration_hhi > 0 else 0
    
    def _calculate_correlation_metrics(self, positions: Dict[str, float],
                                     market_data: Dict[str, pd.DataFrame],
                                     metrics: RiskMetrics):
        """Calculate correlation-based risk metrics"""
        if len(positions) < 2:
            return
        
        try:
            # Get return series for each position
            return_series = {}
            
            for symbol, weight in positions.items():
                if abs(weight) < 0.001:  # Skip very small positions
                    continue
                
                if symbol in market_data:
                    data = market_data[symbol]
                    if len(data) > 30:
                        returns = data['close'].pct_change().dropna()
                        if len(returns) > 30:
                            return_series[symbol] = returns
            
            if len(return_series) < 2:
                return
            
            # Create returns dataframe
            returns_df = pd.DataFrame(return_series)
            returns_df = returns_df.dropna()
            
            if len(returns_df) < 30:
                return
            
            # Calculate correlation matrix
            corr_matrix = returns_df.corr()
            
            # Portfolio average correlation
            n_assets = len(corr_matrix)
            if n_assets > 1:
                # Average pairwise correlation (excluding diagonal)
                total_corr = 0
                count = 0
                for i in range(n_assets):
                    for j in range(i + 1, n_assets):
                        total_corr += corr_matrix.iloc[i, j]
                        count += 1
                
                if count > 0:
                    metrics.portfolio_correlation = total_corr / count
        
        except Exception as e:
            logger.warning(f"Error calculating correlation metrics: {str(e)}")
    
    def _calculate_market_risk_metrics(self, returns: pd.Series, 
                                     benchmark_returns: pd.Series,
                                     metrics: RiskMetrics):
        """Calculate market risk metrics"""
        try:
            # Align returns
            common_dates = returns.index.intersection(benchmark_returns.index)
            if len(common_dates) < 30:
                return
            
            aligned_returns = returns.reindex(common_dates)
            aligned_benchmark = benchmark_returns.reindex(common_dates)
            
            # Remove NaN values
            valid_mask = ~(aligned_returns.isna() | aligned_benchmark.isna())
            aligned_returns = aligned_returns[valid_mask]
            aligned_benchmark = aligned_benchmark[valid_mask]
            
            if len(aligned_returns) < 30:
                return
            
            # Calculate beta
            covariance = aligned_returns.cov(aligned_benchmark)
            benchmark_variance = aligned_benchmark.var()
            
            if benchmark_variance > 0:
                metrics.market_beta = covariance / benchmark_variance
        
        except Exception as e:
            logger.warning(f"Error calculating market risk metrics: {str(e)}")
    
    def _perform_stress_tests(self, returns: pd.Series, metrics: RiskMetrics):
        """Perform stress testing scenarios"""
        stress_scenarios = {}
        
        if len(returns) < 30:
            metrics.stress_test_scenarios = stress_scenarios
            return
        
        try:
            current_volatility = returns.std()
            mean_return = returns.mean()
            
            # Scenario 1: Market crash (-20% shock)
            crash_scenario = mean_return - 3 * current_volatility
            stress_scenarios['market_crash'] = crash_scenario
            
            # Scenario 2: Volatility spike (2x normal volatility)
            vol_spike_scenario = mean_return - 2 * (2 * current_volatility)
            stress_scenarios['volatility_spike'] = vol_spike_scenario
            
            # Scenario 3: Historical worst case (based on actual data)
            worst_case = returns.min()
            stress_scenarios['historical_worst'] = worst_case
            
            # Scenario 4: Tail risk (99.5th percentile loss)
            tail_risk = np.percentile(returns, 0.5)
            stress_scenarios['tail_risk'] = tail_risk
            
            metrics.stress_test_scenarios = stress_scenarios
        
        except Exception as e:
            logger.warning(f"Error in stress testing: {str(e)}")
            metrics.stress_test_scenarios = stress_scenarios
    
    def calculate_risk_adjusted_metrics(self, returns: pd.Series, 
                                      benchmark_returns: pd.Series = None) -> Dict[str, float]:
        """Calculate risk-adjusted performance metrics"""
        metrics = {}
        
        if len(returns) < 30:
            return metrics
        
        try:
            # Basic metrics
            mean_return = returns.mean() * self.trading_days_per_year
            volatility = returns.std() * np.sqrt(self.trading_days_per_year)
            
            # Sharpe ratio
            excess_return = mean_return - self.risk_free_rate
            metrics['sharpe_ratio'] = excess_return / volatility if volatility > 0 else 0
            
            # Sortino ratio
            downside_returns = returns[returns < 0]
            if len(downside_returns) > 0:
                downside_deviation = downside_returns.std() * np.sqrt(self.trading_days_per_year)
                metrics['sortino_ratio'] = excess_return / downside_deviation if downside_deviation > 0 else 0
            
            # Calmar ratio
            cumulative_returns = (1 + returns).cumprod()
            running_max = cumulative_returns.expanding().max()
            drawdown = (cumulative_returns - running_max) / running_max
            max_drawdown = abs(drawdown.min())
            
            metrics['calmar_ratio'] = mean_return / max_drawdown if max_drawdown > 0 else 0
            
            # Information ratio (vs benchmark)
            if benchmark_returns is not None:
                common_dates = returns.index.intersection(benchmark_returns.index)
                if len(common_dates) > 30:
                    aligned_returns = returns.reindex(common_dates)
                    aligned_benchmark = benchmark_returns.reindex(common_dates)
                    
                    excess_returns = aligned_returns - aligned_benchmark
                    tracking_error = excess_returns.std() * np.sqrt(self.trading_days_per_year)
                    
                    if tracking_error > 0:
                        metrics['information_ratio'] = (excess_returns.mean() * self.trading_days_per_year) / tracking_error
            
            # Omega ratio
            threshold = 0  # Use 0% as threshold
            gains = returns[returns > threshold].sum()
            losses = abs(returns[returns <= threshold].sum())
            metrics['omega_ratio'] = gains / losses if losses > 0 else float('inf')
            
        except Exception as e:
            logger.error(f"Error calculating risk-adjusted metrics: {str(e)}")
        
        return metrics
    
    def calculate_portfolio_var(self, positions: Dict[str, float],
                               market_data: Dict[str, pd.DataFrame],
                               confidence: float = 0.95,
                               time_horizon: int = 1) -> float:
        """
        Calculate portfolio VaR using Monte Carlo simulation
        
        Args:
            positions: Portfolio positions (symbol -> weight)
            market_data: Historical price data
            confidence: Confidence level (0.95 for 95% VaR)
            time_horizon: Time horizon in days
        
        Returns:
            Portfolio VaR
        """
        try:
            if not positions or not market_data:
                return 0.0
            
            # Get return series for each asset
            return_series = {}
            for symbol, weight in positions.items():
                if abs(weight) < 0.001:  # Skip tiny positions
                    continue
                
                if symbol in market_data:
                    data = market_data[symbol]
                    if len(data) > 100:
                        returns = data['close'].pct_change().dropna()
                        if len(returns) > 100:
                            return_series[symbol] = returns.tail(252)  # Use last year
            
            if len(return_series) < 2:
                return 0.0
            
            # Create returns dataframe
            returns_df = pd.DataFrame(return_series)
            returns_df = returns_df.dropna()
            
            if len(returns_df) < 100:
                return 0.0
            
            # Calculate portfolio returns
            weights = np.array([positions.get(symbol, 0) for symbol in returns_df.columns])
            weights = weights / np.sum(np.abs(weights))  # Normalize
            
            portfolio_returns = returns_df.dot(weights)
            
            # Scale for time horizon
            if time_horizon > 1:
                portfolio_returns = portfolio_returns * np.sqrt(time_horizon)
            
            # Calculate VaR
            var_value = np.percentile(portfolio_returns, (1 - confidence) * 100)
            
            return abs(var_value)
        
        except Exception as e:
            logger.error(f"Error calculating portfolio VaR: {str(e)}")
            return 0.0
    
    def generate_risk_report(self, metrics: RiskMetrics) -> str:
        """Generate comprehensive risk report"""
        report = f"""
RISK ANALYSIS REPORT
{'=' * 50}

VALUE AT RISK:
1-Day VaR (95%):        {metrics.var_1d_95:.2%}
1-Day VaR (99%):        {metrics.var_1d_99:.2%}
10-Day VaR (95%):       {metrics.var_10d_95:.2%}
CVaR (95%):             {metrics.cvar_1d_95:.2%}
CVaR (99%):             {metrics.cvar_1d_99:.2%}

VOLATILITY METRICS:
Realized Volatility:    {metrics.realized_volatility:.2%}
GARCH Volatility:       {metrics.garch_volatility:.2%}
Volatility Forecast:    {metrics.volatility_forecast:.2%}

DRAWDOWN ANALYSIS:
Current Drawdown:       {metrics.current_drawdown:.2%}
Max Drawdown (1Y):      {metrics.max_drawdown_1y:.2%}
Drawdown Duration:      {metrics.drawdown_duration} days

CONCENTRATION RISK:
Portfolio Correlation: {metrics.portfolio_correlation:.3f}
HHI Concentration:      {metrics.concentration_hhi:.3f}
Effective Positions:    {metrics.effective_positions:.1f}

MARKET RISK:
Market Beta:            {metrics.market_beta:.2f}

DISTRIBUTION METRICS:
Skewness:               {metrics.skewness:.3f}
Kurtosis:               {metrics.kurtosis:.3f}
Tail Ratio:             {metrics.tail_ratio:.2f}

STRESS TEST SCENARIOS:"""
        
        if metrics.stress_test_scenarios:
            for scenario, loss in metrics.stress_test_scenarios.items():
                report += f"\n{scenario.replace('_', ' ').title()}: {loss:.2%}"
        
        if metrics.sector_concentration:
            report += "\n\nSECTOR CONCENTRATION:\n"
            for sector, weight in metrics.sector_concentration.items():
                report += f"{sector}: {weight:.1%}\n"
        
        return report