"""
Performance analysis for backtesting results.
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import scipy.stats as stats
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Container for performance metrics"""
    # Return metrics
    total_return: float = 0.0
    annualized_return: float = 0.0
    cumulative_return: float = 0.0
    
    # Risk metrics
    volatility: float = 0.0
    downside_deviation: float = 0.0
    max_drawdown: float = 0.0
    max_drawdown_duration: int = 0
    
    # Risk-adjusted returns
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0
    omega_ratio: float = 0.0
    
    # Trade statistics
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    largest_win: float = 0.0
    largest_loss: float = 0.0
    profit_factor: float = 0.0
    
    # Distribution metrics
    skewness: float = 0.0
    kurtosis: float = 0.0
    var_95: float = 0.0
    cvar_95: float = 0.0
    
    # Benchmark comparison
    alpha: float = 0.0
    beta: float = 0.0
    correlation: float = 0.0
    information_ratio: float = 0.0
    tracking_error: float = 0.0

class PerformanceAnalyzer:
    """Analyze backtest performance and calculate metrics"""
    
    def __init__(self, risk_free_rate: float = 0.02):
        self.risk_free_rate = risk_free_rate  # Annual risk-free rate
        self.trading_days_per_year = 252
        
    def analyze_performance(self, equity_curve: pd.Series, trades: List[Dict] = None,
                          benchmark_returns: pd.Series = None) -> PerformanceMetrics:
        """
        Comprehensive performance analysis
        
        Args:
            equity_curve: Portfolio value over time
            trades: List of trade dictionaries
            benchmark_returns: Benchmark return series for comparison
        
        Returns:
            PerformanceMetrics object
        """
        metrics = PerformanceMetrics()
        
        if equity_curve.empty:
            logger.warning("Empty equity curve provided")
            return metrics
        
        try:
            # Calculate returns
            returns = equity_curve.pct_change().dropna()
            
            # Basic return metrics
            metrics.total_return = self._calculate_total_return(equity_curve)
            metrics.annualized_return = self._calculate_annualized_return(equity_curve)
            metrics.cumulative_return = metrics.total_return
            
            # Risk metrics
            metrics.volatility = self._calculate_volatility(returns)
            metrics.downside_deviation = self._calculate_downside_deviation(returns)
            metrics.max_drawdown, metrics.max_drawdown_duration = self._calculate_drawdown_metrics(equity_curve)
            
            # Risk-adjusted returns
            metrics.sharpe_ratio = self._calculate_sharpe_ratio(returns)
            metrics.sortino_ratio = self._calculate_sortino_ratio(returns)
            metrics.calmar_ratio = self._calculate_calmar_ratio(metrics.annualized_return, metrics.max_drawdown)
            metrics.omega_ratio = self._calculate_omega_ratio(returns)
            
            # Distribution metrics
            metrics.skewness = self._calculate_skewness(returns)
            metrics.kurtosis = self._calculate_kurtosis(returns)
            metrics.var_95 = self._calculate_var(returns, confidence=0.95)
            metrics.cvar_95 = self._calculate_cvar(returns, confidence=0.95)
            
            # Trade statistics
            if trades:
                trade_metrics = self._analyze_trades(trades)
                metrics.total_trades = trade_metrics['total_trades']
                metrics.winning_trades = trade_metrics['winning_trades']
                metrics.losing_trades = trade_metrics['losing_trades']
                metrics.win_rate = trade_metrics['win_rate']
                metrics.avg_win = trade_metrics['avg_win']
                metrics.avg_loss = trade_metrics['avg_loss']
                metrics.largest_win = trade_metrics['largest_win']
                metrics.largest_loss = trade_metrics['largest_loss']
                metrics.profit_factor = trade_metrics['profit_factor']
            
            # Benchmark comparison
            if benchmark_returns is not None:
                benchmark_metrics = self._compare_to_benchmark(returns, benchmark_returns)
                metrics.alpha = benchmark_metrics['alpha']
                metrics.beta = benchmark_metrics['beta']
                metrics.correlation = benchmark_metrics['correlation']
                metrics.information_ratio = benchmark_metrics['information_ratio']
                metrics.tracking_error = benchmark_metrics['tracking_error']
            
        except Exception as e:
            logger.error(f"Error in performance analysis: {str(e)}")
        
        return metrics
    
    def _calculate_total_return(self, equity_curve: pd.Series) -> float:
        """Calculate total return"""
        if len(equity_curve) < 2:
            return 0.0
        return (equity_curve.iloc[-1] / equity_curve.iloc[0]) - 1
    
    def _calculate_annualized_return(self, equity_curve: pd.Series) -> float:
        """Calculate annualized return"""
        if len(equity_curve) < 2:
            return 0.0
        
        total_return = self._calculate_total_return(equity_curve)
        days = (equity_curve.index[-1] - equity_curve.index[0]).days
        years = days / 365.25
        
        if years <= 0:
            return 0.0
        
        return (1 + total_return) ** (1 / years) - 1
    
    def _calculate_volatility(self, returns: pd.Series) -> float:
        """Calculate annualized volatility"""
        if len(returns) < 2:
            return 0.0
        return returns.std() * np.sqrt(self.trading_days_per_year)
    
    def _calculate_downside_deviation(self, returns: pd.Series, target_return: float = 0.0) -> float:
        """Calculate downside deviation"""
        if len(returns) < 2:
            return 0.0
        
        downside_returns = returns[returns < target_return]
        if len(downside_returns) == 0:
            return 0.0
        
        return downside_returns.std() * np.sqrt(self.trading_days_per_year)
    
    def _calculate_drawdown_metrics(self, equity_curve: pd.Series) -> Tuple[float, int]:
        """Calculate maximum drawdown and duration"""
        if equity_curve.empty:
            return 0.0, 0
        
        # Calculate running maximum
        running_max = equity_curve.expanding().max()
        
        # Calculate drawdown
        drawdown = (equity_curve - running_max) / running_max
        max_drawdown = drawdown.min()
        
        # Calculate maximum drawdown duration
        max_duration = 0
        current_duration = 0
        
        for dd in drawdown:
            if dd < 0:
                current_duration += 1
                max_duration = max(max_duration, current_duration)
            else:
                current_duration = 0
        
        return abs(max_drawdown), max_duration
    
    def _calculate_sharpe_ratio(self, returns: pd.Series) -> float:
        """Calculate Sharpe ratio"""
        if len(returns) < 2:
            return 0.0
        
        excess_returns = returns - (self.risk_free_rate / self.trading_days_per_year)
        
        if excess_returns.std() == 0:
            return 0.0
        
        return excess_returns.mean() / excess_returns.std() * np.sqrt(self.trading_days_per_year)
    
    def _calculate_sortino_ratio(self, returns: pd.Series) -> float:
        """Calculate Sortino ratio"""
        if len(returns) < 2:
            return 0.0
        
        excess_returns = returns - (self.risk_free_rate / self.trading_days_per_year)
        downside_std = self._calculate_downside_deviation(returns) / np.sqrt(self.trading_days_per_year)
        
        if downside_std == 0:
            return 0.0
        
        return excess_returns.mean() * np.sqrt(self.trading_days_per_year) / downside_std
    
    def _calculate_calmar_ratio(self, annualized_return: float, max_drawdown: float) -> float:
        """Calculate Calmar ratio"""
        if max_drawdown == 0:
            return 0.0
        return annualized_return / abs(max_drawdown)
    
    def _calculate_omega_ratio(self, returns: pd.Series, threshold: float = 0.0) -> float:
        """Calculate Omega ratio"""
        if len(returns) < 2:
            return 0.0
        
        excess_returns = returns - threshold
        positive_returns = excess_returns[excess_returns > 0].sum()
        negative_returns = abs(excess_returns[excess_returns < 0].sum())
        
        if negative_returns == 0:
            return float('inf') if positive_returns > 0 else 0.0
        
        return positive_returns / negative_returns
    
    def _calculate_skewness(self, returns: pd.Series) -> float:
        """Calculate skewness"""
        if len(returns) < 3:
            return 0.0
        return stats.skew(returns)
    
    def _calculate_kurtosis(self, returns: pd.Series) -> float:
        """Calculate excess kurtosis"""
        if len(returns) < 4:
            return 0.0
        return stats.kurtosis(returns)
    
    def _calculate_var(self, returns: pd.Series, confidence: float = 0.95) -> float:
        """Calculate Value at Risk"""
        if len(returns) < 2:
            return 0.0
        return np.percentile(returns, (1 - confidence) * 100)
    
    def _calculate_cvar(self, returns: pd.Series, confidence: float = 0.95) -> float:
        """Calculate Conditional Value at Risk (Expected Shortfall)"""
        if len(returns) < 2:
            return 0.0
        
        var = self._calculate_var(returns, confidence)
        return returns[returns <= var].mean()
    
    def _analyze_trades(self, trades: List[Dict]) -> Dict:
        """Analyze individual trades"""
        trade_metrics = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0.0,
            'avg_win': 0.0,
            'avg_loss': 0.0,
            'largest_win': 0.0,
            'largest_loss': 0.0,
            'profit_factor': 0.0
        }
        
        if not trades:
            return trade_metrics
        
        # Filter for completed trades with P&L
        completed_trades = [t for t in trades if 'pnl' in t and t.get('side') == 'SELL']
        
        if not completed_trades:
            return trade_metrics
        
        pnl_values = [t['pnl'] for t in completed_trades]
        winning_trades = [pnl for pnl in pnl_values if pnl > 0]
        losing_trades = [pnl for pnl in pnl_values if pnl < 0]
        
        trade_metrics['total_trades'] = len(completed_trades)
        trade_metrics['winning_trades'] = len(winning_trades)
        trade_metrics['losing_trades'] = len(losing_trades)
        trade_metrics['win_rate'] = len(winning_trades) / len(completed_trades) if completed_trades else 0
        
        if winning_trades:
            trade_metrics['avg_win'] = np.mean(winning_trades)
            trade_metrics['largest_win'] = max(winning_trades)
        
        if losing_trades:
            trade_metrics['avg_loss'] = np.mean(losing_trades)
            trade_metrics['largest_loss'] = min(losing_trades)
        
        # Profit factor
        gross_profit = sum(winning_trades)
        gross_loss = abs(sum(losing_trades))
        trade_metrics['profit_factor'] = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        return trade_metrics
    
    def _compare_to_benchmark(self, returns: pd.Series, benchmark_returns: pd.Series) -> Dict:
        """Compare strategy returns to benchmark"""
        benchmark_metrics = {
            'alpha': 0.0,
            'beta': 0.0,
            'correlation': 0.0,
            'information_ratio': 0.0,
            'tracking_error': 0.0
        }
        
        # Align returns
        common_dates = returns.index.intersection(benchmark_returns.index)
        if len(common_dates) < 10:  # Need sufficient data
            return benchmark_metrics
        
        aligned_returns = returns.reindex(common_dates)
        aligned_benchmark = benchmark_returns.reindex(common_dates)
        
        # Remove any NaN values
        valid_mask = ~(aligned_returns.isna() | aligned_benchmark.isna())
        aligned_returns = aligned_returns[valid_mask]
        aligned_benchmark = aligned_benchmark[valid_mask]
        
        if len(aligned_returns) < 10:
            return benchmark_metrics
        
        # Calculate beta
        covariance = aligned_returns.cov(aligned_benchmark)
        benchmark_variance = aligned_benchmark.var()
        beta = covariance / benchmark_variance if benchmark_variance > 0 else 0
        
        # Calculate alpha (annualized)
        strategy_return = aligned_returns.mean() * self.trading_days_per_year
        benchmark_return = aligned_benchmark.mean() * self.trading_days_per_year
        risk_free_return = self.risk_free_rate
        
        alpha = strategy_return - (risk_free_return + beta * (benchmark_return - risk_free_return))
        
        # Calculate correlation
        correlation = aligned_returns.corr(aligned_benchmark)
        
        # Calculate tracking error and information ratio
        excess_returns = aligned_returns - aligned_benchmark
        tracking_error = excess_returns.std() * np.sqrt(self.trading_days_per_year)
        information_ratio = excess_returns.mean() * np.sqrt(self.trading_days_per_year) / tracking_error if tracking_error > 0 else 0
        
        benchmark_metrics.update({
            'alpha': alpha,
            'beta': beta,
            'correlation': correlation,
            'information_ratio': information_ratio,
            'tracking_error': tracking_error
        })
        
        return benchmark_metrics
    
    def calculate_rolling_metrics(self, equity_curve: pd.Series, window_days: int = 252) -> pd.DataFrame:
        """Calculate rolling performance metrics"""
        if len(equity_curve) < window_days:
            return pd.DataFrame()
        
        returns = equity_curve.pct_change().dropna()
        
        rolling_metrics = pd.DataFrame(index=equity_curve.index[window_days:])
        
        # Rolling returns
        rolling_metrics['rolling_return'] = equity_curve.rolling(window_days).apply(
            lambda x: (x.iloc[-1] / x.iloc[0]) - 1
        )
        
        # Rolling volatility
        rolling_metrics['rolling_volatility'] = returns.rolling(window_days).std() * np.sqrt(self.trading_days_per_year)
        
        # Rolling Sharpe ratio
        rolling_metrics['rolling_sharpe'] = returns.rolling(window_days).apply(
            lambda x: (x.mean() - self.risk_free_rate / self.trading_days_per_year) / x.std() * np.sqrt(self.trading_days_per_year)
        )
        
        # Rolling max drawdown
        rolling_metrics['rolling_max_drawdown'] = equity_curve.rolling(window_days).apply(
            lambda x: ((x - x.expanding().max()) / x.expanding().max()).min()
        )
        
        return rolling_metrics
    
    def generate_performance_report(self, metrics: PerformanceMetrics) -> str:
        """Generate a formatted performance report"""
        report = f"""
PERFORMANCE ANALYSIS REPORT
{'=' * 50}

RETURN METRICS:
Total Return:           {metrics.total_return:.2%}
Annualized Return:      {metrics.annualized_return:.2%}

RISK METRICS:
Volatility:             {metrics.volatility:.2%}
Downside Deviation:     {metrics.downside_deviation:.2%}
Maximum Drawdown:       {metrics.max_drawdown:.2%}
Max DD Duration:        {metrics.max_drawdown_duration} days

RISK-ADJUSTED RETURNS:
Sharpe Ratio:           {metrics.sharpe_ratio:.2f}
Sortino Ratio:          {metrics.sortino_ratio:.2f}
Calmar Ratio:           {metrics.calmar_ratio:.2f}
Omega Ratio:            {metrics.omega_ratio:.2f}

TRADE STATISTICS:
Total Trades:           {metrics.total_trades}
Winning Trades:         {metrics.winning_trades}
Losing Trades:          {metrics.losing_trades}
Win Rate:               {metrics.win_rate:.2%}
Average Win:            ${metrics.avg_win:.2f}
Average Loss:           ${metrics.avg_loss:.2f}
Largest Win:            ${metrics.largest_win:.2f}
Largest Loss:           ${metrics.largest_loss:.2f}
Profit Factor:          {metrics.profit_factor:.2f}

DISTRIBUTION METRICS:
Skewness:               {metrics.skewness:.2f}
Kurtosis:               {metrics.kurtosis:.2f}
VaR (95%):              {metrics.var_95:.2%}
CVaR (95%):             {metrics.cvar_95:.2%}

BENCHMARK COMPARISON:
Alpha:                  {metrics.alpha:.2%}
Beta:                   {metrics.beta:.2f}
Correlation:            {metrics.correlation:.2f}
Information Ratio:      {metrics.information_ratio:.2f}
Tracking Error:         {metrics.tracking_error:.2%}
"""
        return report