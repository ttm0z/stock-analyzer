"""
Benchmark comparison and analysis service.
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class BenchmarkComparison:
    """Benchmark comparison metrics"""
    # Return comparison
    strategy_return: float = 0.0
    benchmark_return: float = 0.0
    excess_return: float = 0.0
    annualized_excess: float = 0.0
    
    # Risk comparison
    strategy_volatility: float = 0.0
    benchmark_volatility: float = 0.0
    tracking_error: float = 0.0
    
    # Risk-adjusted metrics
    alpha: float = 0.0
    beta: float = 0.0
    correlation: float = 0.0
    information_ratio: float = 0.0
    
    # Performance attribution
    selection_effect: float = 0.0
    timing_effect: float = 0.0
    interaction_effect: float = 0.0
    
    # Drawdown comparison
    strategy_max_dd: float = 0.0
    benchmark_max_dd: float = 0.0
    relative_max_dd: float = 0.0
    
    # Rolling metrics
    rolling_alpha: pd.Series = None
    rolling_beta: pd.Series = None
    rolling_correlation: pd.Series = None

class BenchmarkService:
    """Service for benchmark analysis and comparison"""
    
    def __init__(self, trading_days_per_year: int = 252):
        self.trading_days_per_year = trading_days_per_year
        self.risk_free_rate = 0.02  # 2% annual risk-free rate
        
        # Common benchmark mappings
        self.benchmark_map = {
            'US_EQUITY': 'SPY',
            'US_LARGE_CAP': 'SPY',
            'US_SMALL_CAP': 'IWM',
            'US_MID_CAP': 'MDY',
            'INTERNATIONAL': 'VEA',
            'EMERGING_MARKETS': 'VWO',
            'US_BONDS': 'AGG',
            'REAL_ESTATE': 'VNQ',
            'COMMODITIES': 'DJP',
            'TECHNOLOGY': 'XLK',
            'HEALTHCARE': 'XLV',
            'FINANCIALS': 'XLF'
        }
    
    def compare_to_benchmark(self, strategy_returns: pd.Series,
                           benchmark_returns: pd.Series,
                           rolling_window: int = 63) -> BenchmarkComparison:
        """
        Comprehensive benchmark comparison
        
        Args:
            strategy_returns: Strategy return series
            benchmark_returns: Benchmark return series
            rolling_window: Window for rolling metrics (default 3 months)
        
        Returns:
            BenchmarkComparison object
        """
        comparison = BenchmarkComparison()
        
        if strategy_returns.empty or benchmark_returns.empty:
            logger.warning("Empty return series provided")
            return comparison
        
        try:
            # Align returns
            aligned_strategy, aligned_benchmark = self._align_returns(
                strategy_returns, benchmark_returns
            )
            
            if len(aligned_strategy) < 30:  # Need sufficient data
                logger.warning("Insufficient data for benchmark comparison")
                return comparison
            
            # Basic return comparison
            self._calculate_return_metrics(aligned_strategy, aligned_benchmark, comparison)
            
            # Risk metrics
            self._calculate_risk_metrics(aligned_strategy, aligned_benchmark, comparison)
            
            # Risk-adjusted metrics
            self._calculate_risk_adjusted_metrics(aligned_strategy, aligned_benchmark, comparison)
            
            # Drawdown comparison
            self._calculate_drawdown_metrics(aligned_strategy, aligned_benchmark, comparison)
            
            # Rolling metrics
            if len(aligned_strategy) >= rolling_window:
                self._calculate_rolling_metrics(aligned_strategy, aligned_benchmark, 
                                              comparison, rolling_window)
            
        except Exception as e:
            logger.error(f"Error in benchmark comparison: {str(e)}")
        
        return comparison
    
    def _align_returns(self, strategy_returns: pd.Series, 
                      benchmark_returns: pd.Series) -> Tuple[pd.Series, pd.Series]:
        """Align strategy and benchmark returns"""
        # Find common dates
        common_dates = strategy_returns.index.intersection(benchmark_returns.index)
        
        if len(common_dates) == 0:
            logger.warning("No common dates between strategy and benchmark")
            return pd.Series(), pd.Series()
        
        aligned_strategy = strategy_returns.reindex(common_dates)
        aligned_benchmark = benchmark_returns.reindex(common_dates)
        
        # Remove NaN values
        valid_mask = ~(aligned_strategy.isna() | aligned_benchmark.isna())
        aligned_strategy = aligned_strategy[valid_mask]
        aligned_benchmark = aligned_benchmark[valid_mask]
        
        return aligned_strategy, aligned_benchmark
    
    def _calculate_return_metrics(self, strategy_returns: pd.Series,
                                benchmark_returns: pd.Series,
                                comparison: BenchmarkComparison):
        """Calculate return comparison metrics"""
        # Total returns
        comparison.strategy_return = (1 + strategy_returns).prod() - 1
        comparison.benchmark_return = (1 + benchmark_returns).prod() - 1
        comparison.excess_return = comparison.strategy_return - comparison.benchmark_return
        
        # Annualized excess return
        years = len(strategy_returns) / self.trading_days_per_year
        if years > 0:
            comparison.annualized_excess = (comparison.excess_return / years)
    
    def _calculate_risk_metrics(self, strategy_returns: pd.Series,
                              benchmark_returns: pd.Series,
                              comparison: BenchmarkComparison):
        """Calculate risk comparison metrics"""
        # Volatilities (annualized)
        comparison.strategy_volatility = strategy_returns.std() * np.sqrt(self.trading_days_per_year)
        comparison.benchmark_volatility = benchmark_returns.std() * np.sqrt(self.trading_days_per_year)
        
        # Tracking error
        excess_returns = strategy_returns - benchmark_returns
        comparison.tracking_error = excess_returns.std() * np.sqrt(self.trading_days_per_year)
    
    def _calculate_risk_adjusted_metrics(self, strategy_returns: pd.Series,
                                       benchmark_returns: pd.Series,
                                       comparison: BenchmarkComparison):
        """Calculate risk-adjusted comparison metrics"""
        # Beta
        covariance = strategy_returns.cov(benchmark_returns)
        benchmark_variance = benchmark_returns.var()
        
        if benchmark_variance > 0:
            comparison.beta = covariance / benchmark_variance
        
        # Alpha (annualized)
        strategy_mean = strategy_returns.mean() * self.trading_days_per_year
        benchmark_mean = benchmark_returns.mean() * self.trading_days_per_year
        
        comparison.alpha = strategy_mean - (self.risk_free_rate + 
                                          comparison.beta * (benchmark_mean - self.risk_free_rate))
        
        # Correlation
        comparison.correlation = strategy_returns.corr(benchmark_returns)
        
        # Information Ratio
        if comparison.tracking_error > 0:
            excess_returns = strategy_returns - benchmark_returns
            comparison.information_ratio = (excess_returns.mean() * self.trading_days_per_year) / comparison.tracking_error
    
    def _calculate_drawdown_metrics(self, strategy_returns: pd.Series,
                                  benchmark_returns: pd.Series,
                                  comparison: BenchmarkComparison):
        """Calculate drawdown comparison metrics"""
        # Strategy drawdown
        strategy_cumulative = (1 + strategy_returns).cumprod()
        strategy_running_max = strategy_cumulative.expanding().max()
        strategy_drawdown = (strategy_cumulative - strategy_running_max) / strategy_running_max
        comparison.strategy_max_dd = abs(strategy_drawdown.min())
        
        # Benchmark drawdown
        benchmark_cumulative = (1 + benchmark_returns).cumprod()
        benchmark_running_max = benchmark_cumulative.expanding().max()
        benchmark_drawdown = (benchmark_cumulative - benchmark_running_max) / benchmark_running_max
        comparison.benchmark_max_dd = abs(benchmark_drawdown.min())
        
        # Relative drawdown
        relative_returns = strategy_returns - benchmark_returns
        relative_cumulative = (1 + relative_returns).cumprod()
        relative_running_max = relative_cumulative.expanding().max()
        relative_drawdown = (relative_cumulative - relative_running_max) / relative_running_max
        comparison.relative_max_dd = abs(relative_drawdown.min())
    
    def _calculate_rolling_metrics(self, strategy_returns: pd.Series,
                                 benchmark_returns: pd.Series,
                                 comparison: BenchmarkComparison,
                                 window: int):
        """Calculate rolling comparison metrics"""
        try:
            # Rolling alpha
            rolling_alpha = []
            rolling_beta = []
            rolling_correlation = []
            
            for i in range(window, len(strategy_returns) + 1):
                window_strategy = strategy_returns.iloc[i-window:i]
                window_benchmark = benchmark_returns.iloc[i-window:i]
                
                if len(window_strategy) == window and len(window_benchmark) == window:
                    # Rolling beta
                    covariance = window_strategy.cov(window_benchmark)
                    benchmark_variance = window_benchmark.var()
                    beta = covariance / benchmark_variance if benchmark_variance > 0 else 0
                    
                    # Rolling alpha (annualized)
                    strategy_mean = window_strategy.mean() * self.trading_days_per_year
                    benchmark_mean = window_benchmark.mean() * self.trading_days_per_year
                    alpha = strategy_mean - (self.risk_free_rate + 
                                           beta * (benchmark_mean - self.risk_free_rate))
                    
                    # Rolling correlation
                    correlation = window_strategy.corr(window_benchmark)
                    
                    rolling_alpha.append(alpha)
                    rolling_beta.append(beta)
                    rolling_correlation.append(correlation)
            
            # Create series with proper index
            rolling_dates = strategy_returns.index[window-1:]
            comparison.rolling_alpha = pd.Series(rolling_alpha, index=rolling_dates)
            comparison.rolling_beta = pd.Series(rolling_beta, index=rolling_dates)
            comparison.rolling_correlation = pd.Series(rolling_correlation, index=rolling_dates)
            
        except Exception as e:
            logger.warning(f"Error calculating rolling metrics: {str(e)}")
    
    def analyze_performance_attribution(self, strategy_returns: pd.Series,
                                      benchmark_returns: pd.Series,
                                      strategy_weights: pd.DataFrame = None,
                                      benchmark_weights: pd.DataFrame = None) -> Dict[str, float]:
        """
        Perform performance attribution analysis
        
        Args:
            strategy_returns: Strategy return series
            benchmark_returns: Benchmark return series
            strategy_weights: Strategy position weights over time
            benchmark_weights: Benchmark weights over time
        
        Returns:
            Attribution analysis results
        """
        attribution = {
            'selection_effect': 0.0,
            'allocation_effect': 0.0,
            'interaction_effect': 0.0,
            'total_excess_return': 0.0
        }
        
        try:
            # Basic excess return
            aligned_strategy, aligned_benchmark = self._align_returns(
                strategy_returns, benchmark_returns
            )
            
            if len(aligned_strategy) < 30:
                return attribution
            
            excess_returns = aligned_strategy - aligned_benchmark
            attribution['total_excess_return'] = excess_returns.sum()
            
            # If we have detailed weights, perform more sophisticated attribution
            if strategy_weights is not None and benchmark_weights is not None:
                attribution.update(self._detailed_attribution_analysis(
                    strategy_weights, benchmark_weights, aligned_strategy, aligned_benchmark
                ))
            
        except Exception as e:
            logger.error(f"Error in performance attribution: {str(e)}")
        
        return attribution
    
    def _detailed_attribution_analysis(self, strategy_weights: pd.DataFrame,
                                     benchmark_weights: pd.DataFrame,
                                     strategy_returns: pd.Series,
                                     benchmark_returns: pd.Series) -> Dict[str, float]:
        """Detailed attribution analysis with position weights"""
        # This is a simplified attribution model
        # In practice, you'd need more sophisticated sector/security attribution
        
        attribution = {
            'selection_effect': 0.0,
            'allocation_effect': 0.0,
            'interaction_effect': 0.0
        }
        
        # Placeholder for more detailed implementation
        # Would require position-level returns and weights
        
        return attribution
    
    def get_benchmark_symbol(self, strategy_category: str) -> str:
        """Get appropriate benchmark symbol for strategy category"""
        return self.benchmark_map.get(strategy_category.upper(), 'SPY')
    
    def calculate_tracking_statistics(self, strategy_returns: pd.Series,
                                    benchmark_returns: pd.Series) -> Dict[str, float]:
        """Calculate detailed tracking statistics"""
        stats = {}
        
        try:
            aligned_strategy, aligned_benchmark = self._align_returns(
                strategy_returns, benchmark_returns
            )
            
            if len(aligned_strategy) < 30:
                return stats
            
            excess_returns = aligned_strategy - aligned_benchmark
            
            # Tracking error
            stats['tracking_error'] = excess_returns.std() * np.sqrt(self.trading_days_per_year)
            
            # Up/Down capture ratios
            up_market_mask = aligned_benchmark > 0
            down_market_mask = aligned_benchmark < 0
            
            if up_market_mask.sum() > 0:
                up_strategy = aligned_strategy[up_market_mask].mean()
                up_benchmark = aligned_benchmark[up_market_mask].mean()
                stats['up_capture'] = (up_strategy / up_benchmark) if up_benchmark != 0 else 0
            
            if down_market_mask.sum() > 0:
                down_strategy = aligned_strategy[down_market_mask].mean()
                down_benchmark = aligned_benchmark[down_market_mask].mean()
                stats['down_capture'] = (down_strategy / down_benchmark) if down_benchmark != 0 else 0
            
            # Hit ratio (% of periods beating benchmark)
            stats['hit_ratio'] = (excess_returns > 0).mean()
            
            # Average excess return in winning periods
            winning_excess = excess_returns[excess_returns > 0]
            stats['avg_excess_win'] = winning_excess.mean() if len(winning_excess) > 0 else 0
            
            # Average excess return in losing periods
            losing_excess = excess_returns[excess_returns < 0]
            stats['avg_excess_loss'] = losing_excess.mean() if len(losing_excess) > 0 else 0
            
        except Exception as e:
            logger.error(f"Error calculating tracking statistics: {str(e)}")
        
        return stats
    
    def generate_benchmark_report(self, comparison: BenchmarkComparison,
                                tracking_stats: Dict[str, float] = None) -> str:
        """Generate comprehensive benchmark comparison report"""
        report = f"""
BENCHMARK COMPARISON REPORT
{'=' * 50}

RETURN COMPARISON:
Strategy Return:        {comparison.strategy_return:.2%}
Benchmark Return:       {comparison.benchmark_return:.2%}
Excess Return:          {comparison.excess_return:.2%}
Annualized Excess:      {comparison.annualized_excess:.2%}

RISK COMPARISON:
Strategy Volatility:    {comparison.strategy_volatility:.2%}
Benchmark Volatility:   {comparison.benchmark_volatility:.2%}
Tracking Error:         {comparison.tracking_error:.2%}

RISK-ADJUSTED METRICS:
Alpha:                  {comparison.alpha:.2%}
Beta:                   {comparison.beta:.2f}
Correlation:            {comparison.correlation:.3f}
Information Ratio:      {comparison.information_ratio:.2f}

DRAWDOWN COMPARISON:
Strategy Max DD:        {comparison.strategy_max_dd:.2%}
Benchmark Max DD:       {comparison.benchmark_max_dd:.2%}
Relative Max DD:        {comparison.relative_max_dd:.2%}
"""
        
        if tracking_stats:
            report += f"""
TRACKING STATISTICS:
Up Capture:             {tracking_stats.get('up_capture', 0):.1%}
Down Capture:           {tracking_stats.get('down_capture', 0):.1%}
Hit Ratio:              {tracking_stats.get('hit_ratio', 0):.1%}
Avg Excess (Win):       {tracking_stats.get('avg_excess_win', 0):.2%}
Avg Excess (Loss):      {tracking_stats.get('avg_excess_loss', 0):.2%}
"""
        
        return report
    
    def export_comparison_data(self, comparison: BenchmarkComparison) -> pd.DataFrame:
        """Export comparison data to DataFrame"""
        data = {
            'Metric': [
                'Strategy Return', 'Benchmark Return', 'Excess Return',
                'Strategy Volatility', 'Benchmark Volatility', 'Tracking Error',
                'Alpha', 'Beta', 'Correlation', 'Information Ratio',
                'Strategy Max DD', 'Benchmark Max DD', 'Relative Max DD'
            ],
            'Value': [
                comparison.strategy_return, comparison.benchmark_return, comparison.excess_return,
                comparison.strategy_volatility, comparison.benchmark_volatility, comparison.tracking_error,
                comparison.alpha, comparison.beta, comparison.correlation, comparison.information_ratio,
                comparison.strategy_max_dd, comparison.benchmark_max_dd, comparison.relative_max_dd
            ]
        }
        
        return pd.DataFrame(data)