"""
Report generation service for backtesting results and analysis.
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import base64
from io import StringIO, BytesIO
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from dataclasses import asdict

from .performance_analyzer import PerformanceMetrics
from .trade_analyzer import TradeMetrics
from .risk_analyzer import RiskMetrics
from .benchmark_service import BenchmarkComparison

logger = logging.getLogger(__name__)

class ReportGenerator:
    """Generate comprehensive reports for backtesting results"""
    
    def __init__(self):
        self.report_templates = {
            'executive_summary': self._generate_executive_summary,
            'detailed_performance': self._generate_detailed_performance,
            'risk_analysis': self._generate_risk_analysis,
            'trade_analysis': self._generate_trade_analysis,
            'benchmark_comparison': self._generate_benchmark_comparison,
            'strategy_analysis': self._generate_strategy_analysis
        }
        
        # Configure matplotlib for report generation
        plt.style.use('default')
        plt.rcParams['figure.figsize'] = (12, 8)
        plt.rcParams['font.size'] = 10
    
    def generate_comprehensive_report(self, 
                                    performance_metrics: PerformanceMetrics,
                                    trade_metrics: TradeMetrics = None,
                                    risk_metrics: RiskMetrics = None,
                                    benchmark_comparison: BenchmarkComparison = None,
                                    equity_curve: pd.Series = None,
                                    trades: List[Dict] = None,
                                    strategy_config: Dict = None,
                                    include_charts: bool = True) -> Dict[str, Any]:
        """
        Generate comprehensive backtest report
        
        Args:
            performance_metrics: Performance analysis results
            trade_metrics: Trade analysis results
            risk_metrics: Risk analysis results
            benchmark_comparison: Benchmark comparison results
            equity_curve: Portfolio equity curve
            trades: Trade data
            strategy_config: Strategy configuration
            include_charts: Whether to include charts
        
        Returns:
            Dictionary containing report sections and metadata
        """
        report = {
            'metadata': self._generate_report_metadata(strategy_config),
            'executive_summary': self._generate_executive_summary(performance_metrics, trade_metrics),
            'performance_analysis': self._generate_detailed_performance(performance_metrics),
            'sections': {}
        }
        
        try:
            # Add optional sections based on available data
            if trade_metrics:
                report['sections']['trade_analysis'] = self._generate_trade_analysis(trade_metrics)
            
            if risk_metrics:
                report['sections']['risk_analysis'] = self._generate_risk_analysis(risk_metrics)
            
            if benchmark_comparison:
                report['sections']['benchmark_comparison'] = self._generate_benchmark_comparison(benchmark_comparison)
            
            if strategy_config:
                report['sections']['strategy_analysis'] = self._generate_strategy_analysis(strategy_config)
            
            # Generate charts if requested
            if include_charts:
                charts = self._generate_charts(
                    equity_curve, trades, performance_metrics, trade_metrics
                )
                report['charts'] = charts
            
            # Generate conclusions and recommendations
            report['conclusions'] = self._generate_conclusions(
                performance_metrics, trade_metrics, risk_metrics, benchmark_comparison
            )
            
        except Exception as e:
            logger.error(f"Error generating comprehensive report: {str(e)}")
            report['errors'] = [str(e)]
        
        return report
    
    def _generate_report_metadata(self, strategy_config: Dict = None) -> Dict[str, Any]:
        """Generate report metadata"""
        metadata = {
            'generated_at': datetime.now().isoformat(),
            'report_version': '1.0',
            'generator': 'Backtesting Engine Report Generator'
        }
        
        if strategy_config:
            metadata.update({
                'strategy_name': strategy_config.get('strategy_name', 'Unknown'),
                'backtest_period': {
                    'start_date': strategy_config.get('start_date'),
                    'end_date': strategy_config.get('end_date')
                },
                'initial_capital': strategy_config.get('initial_capital'),
                'universe_size': len(strategy_config.get('universe', []))
            })
        
        return metadata
    
    def _generate_executive_summary(self, performance_metrics: PerformanceMetrics,
                                  trade_metrics: TradeMetrics = None) -> Dict[str, Any]:
        """Generate executive summary section"""
        summary = {
            'title': 'Executive Summary',
            'key_metrics': {
                'Total Return': f"{performance_metrics.total_return:.2%}",
                'Annualized Return': f"{performance_metrics.annualized_return:.2%}",
                'Volatility': f"{performance_metrics.volatility:.2%}",
                'Sharpe Ratio': f"{performance_metrics.sharpe_ratio:.2f}",
                'Maximum Drawdown': f"{performance_metrics.max_drawdown:.2%}"
            },
            'performance_grade': self._calculate_performance_grade(performance_metrics),
            'highlights': [],
            'concerns': []
        }
        
        # Add trade metrics if available
        if trade_metrics:
            summary['key_metrics'].update({
                'Total Trades': str(trade_metrics.total_trades),
                'Win Rate': f"{trade_metrics.win_rate:.1%}",
                'Profit Factor': f"{trade_metrics.profit_factor:.2f}"
            })
        
        # Generate highlights and concerns
        summary['highlights'] = self._generate_highlights(performance_metrics, trade_metrics)
        summary['concerns'] = self._generate_concerns(performance_metrics, trade_metrics)
        
        return summary
    
    def _calculate_performance_grade(self, metrics: PerformanceMetrics) -> str:
        """Calculate overall performance grade"""
        score = 0
        
        # Sharpe ratio scoring
        if metrics.sharpe_ratio >= 2.0:
            score += 25
        elif metrics.sharpe_ratio >= 1.5:
            score += 20
        elif metrics.sharpe_ratio >= 1.0:
            score += 15
        elif metrics.sharpe_ratio >= 0.5:
            score += 10
        
        # Return scoring
        if metrics.annualized_return >= 0.20:
            score += 25
        elif metrics.annualized_return >= 0.15:
            score += 20
        elif metrics.annualized_return >= 0.10:
            score += 15
        elif metrics.annualized_return >= 0.05:
            score += 10
        
        # Drawdown scoring (inverse)
        if metrics.max_drawdown <= 0.05:
            score += 25
        elif metrics.max_drawdown <= 0.10:
            score += 20
        elif metrics.max_drawdown <= 0.15:
            score += 15
        elif metrics.max_drawdown <= 0.25:
            score += 10
        
        # Volatility scoring (inverse)
        if metrics.volatility <= 0.10:
            score += 25
        elif metrics.volatility <= 0.15:
            score += 20
        elif metrics.volatility <= 0.20:
            score += 15
        elif metrics.volatility <= 0.30:
            score += 10
        
        # Convert score to grade
        if score >= 90:
            return 'A+'
        elif score >= 85:
            return 'A'
        elif score >= 80:
            return 'A-'
        elif score >= 75:
            return 'B+'
        elif score >= 70:
            return 'B'
        elif score >= 65:
            return 'B-'
        elif score >= 60:
            return 'C+'
        elif score >= 55:
            return 'C'
        elif score >= 50:
            return 'C-'
        else:
            return 'D'
    
    def _generate_highlights(self, performance_metrics: PerformanceMetrics,
                           trade_metrics: TradeMetrics = None) -> List[str]:
        """Generate performance highlights"""
        highlights = []
        
        # Performance highlights
        if performance_metrics.sharpe_ratio > 1.5:
            highlights.append(f"Excellent risk-adjusted returns with Sharpe ratio of {performance_metrics.sharpe_ratio:.2f}")
        
        if performance_metrics.annualized_return > 0.15:
            highlights.append(f"Strong annualized returns of {performance_metrics.annualized_return:.1%}")
        
        if performance_metrics.max_drawdown < 0.10:
            highlights.append(f"Low maximum drawdown of {performance_metrics.max_drawdown:.1%}")
        
        if performance_metrics.sortino_ratio > 2.0:
            highlights.append(f"Excellent downside risk management with Sortino ratio of {performance_metrics.sortino_ratio:.2f}")
        
        # Trade highlights
        if trade_metrics:
            if trade_metrics.win_rate > 0.6:
                highlights.append(f"High win rate of {trade_metrics.win_rate:.1%}")
            
            if trade_metrics.profit_factor > 2.0:
                highlights.append(f"Strong profit factor of {trade_metrics.profit_factor:.2f}")
            
            if trade_metrics.max_consecutive_losses <= 3:
                highlights.append("Good streak management with limited consecutive losses")
        
        return highlights
    
    def _generate_concerns(self, performance_metrics: PerformanceMetrics,
                         trade_metrics: TradeMetrics = None) -> List[str]:
        """Generate performance concerns"""
        concerns = []
        
        # Performance concerns
        if performance_metrics.sharpe_ratio < 0.5:
            concerns.append(f"Low Sharpe ratio of {performance_metrics.sharpe_ratio:.2f} indicates poor risk-adjusted returns")
        
        if performance_metrics.max_drawdown > 0.25:
            concerns.append(f"High maximum drawdown of {performance_metrics.max_drawdown:.1%} indicates significant risk")
        
        if performance_metrics.volatility > 0.30:
            concerns.append(f"High volatility of {performance_metrics.volatility:.1%} may indicate unstable performance")
        
        if abs(performance_metrics.skewness) > 2.0:
            concerns.append("Highly skewed returns distribution may indicate tail risk")
        
        if performance_metrics.kurtosis > 5.0:
            concerns.append("High kurtosis indicates fat-tailed return distribution")
        
        # Trade concerns
        if trade_metrics:
            if trade_metrics.win_rate < 0.4:
                concerns.append(f"Low win rate of {trade_metrics.win_rate:.1%} may indicate poor signal quality")
            
            if trade_metrics.profit_factor < 1.2:
                concerns.append(f"Low profit factor of {trade_metrics.profit_factor:.2f} indicates marginal profitability")
            
            if trade_metrics.max_consecutive_losses > 10:
                concerns.append(f"High consecutive losses ({trade_metrics.max_consecutive_losses}) may indicate strategy breakdown")
            
            if trade_metrics.total_trades < 30:
                concerns.append("Low number of trades may indicate insufficient statistical significance")
        
        return concerns
    
    def _generate_detailed_performance(self, metrics: PerformanceMetrics) -> Dict[str, Any]:
        """Generate detailed performance analysis section"""
        return {
            'title': 'Detailed Performance Analysis',
            'return_metrics': {
                'Total Return': f"{metrics.total_return:.2%}",
                'Annualized Return': f"{metrics.annualized_return:.2%}",
                'Cumulative Return': f"{metrics.cumulative_return:.2%}"
            },
            'risk_metrics': {
                'Volatility': f"{metrics.volatility:.2%}",
                'Downside Deviation': f"{metrics.downside_deviation:.2%}",
                'Maximum Drawdown': f"{metrics.max_drawdown:.2%}",
                'Max DD Duration': f"{metrics.max_drawdown_duration} days"
            },
            'risk_adjusted_returns': {
                'Sharpe Ratio': f"{metrics.sharpe_ratio:.2f}",
                'Sortino Ratio': f"{metrics.sortino_ratio:.2f}",
                'Calmar Ratio': f"{metrics.calmar_ratio:.2f}",
                'Omega Ratio': f"{metrics.omega_ratio:.2f}"
            },
            'distribution_metrics': {
                'Skewness': f"{metrics.skewness:.3f}",
                'Kurtosis': f"{metrics.kurtosis:.3f}",
                'VaR (95%)': f"{metrics.var_95:.2%}",
                'CVaR (95%)': f"{metrics.cvar_95:.2%}"
            },
            'benchmark_comparison': {
                'Alpha': f"{metrics.alpha:.2%}",
                'Beta': f"{metrics.beta:.2f}",
                'Correlation': f"{metrics.correlation:.3f}",
                'Information Ratio': f"{metrics.information_ratio:.2f}",
                'Tracking Error': f"{metrics.tracking_error:.2%}"
            }
        }
    
    def _generate_trade_analysis(self, metrics: TradeMetrics) -> Dict[str, Any]:
        """Generate trade analysis section"""
        return {
            'title': 'Trade Analysis',
            'trade_statistics': {
                'Total Trades': metrics.total_trades,
                'Winning Trades': f"{metrics.winning_trades} ({metrics.win_rate:.1%})",
                'Losing Trades': f"{metrics.losing_trades} ({1-metrics.win_rate:.1%})",
                'Break-even Trades': metrics.break_even_trades
            },
            'profit_loss': {
                'Total P&L': f"${metrics.total_pnl:,.2f}",
                'Gross Profit': f"${metrics.gross_profit:,.2f}",
                'Gross Loss': f"${metrics.gross_loss:,.2f}",
                'Net Profit': f"${metrics.net_profit:,.2f}"
            },
            'average_trades': {
                'Average Trade': f"${metrics.avg_trade_pnl:,.2f}",
                'Average Winner': f"${metrics.avg_winning_trade:,.2f}",
                'Average Loser': f"${metrics.avg_losing_trade:,.2f}"
            },
            'best_worst': {
                'Largest Win': f"${metrics.largest_win:,.2f} ({metrics.best_trade_symbol})",
                'Largest Loss': f"${metrics.largest_loss:,.2f} ({metrics.worst_trade_symbol})"
            },
            'ratios': {
                'Profit Factor': f"{metrics.profit_factor:.2f}",
                'Payoff Ratio': f"{metrics.payoff_ratio:.2f}",
                'Expectancy': f"${metrics.expectancy:,.2f}"
            },
            'holding_periods': {
                'Average Holding': f"{metrics.avg_holding_period:.1f} days",
                'Avg Winning Hold': f"{metrics.avg_winning_holding_period:.1f} days",
                'Avg Losing Hold': f"{metrics.avg_losing_holding_period:.1f} days"
            },
            'streaks': {
                'Max Consecutive Wins': metrics.max_consecutive_wins,
                'Max Consecutive Losses': metrics.max_consecutive_losses,
                'Current Streak': f"{metrics.current_streak} {metrics.current_streak_type}"
            }
        }
    
    def _generate_risk_analysis(self, metrics: RiskMetrics) -> Dict[str, Any]:
        """Generate risk analysis section"""
        return {
            'title': 'Risk Analysis',
            'value_at_risk': {
                '1-Day VaR (95%)': f"{metrics.var_1d_95:.2%}",
                '1-Day VaR (99%)': f"{metrics.var_1d_99:.2%}",
                '10-Day VaR (95%)': f"{metrics.var_10d_95:.2%}",
                'CVaR (95%)': f"{metrics.cvar_1d_95:.2%}",
                'CVaR (99%)': f"{metrics.cvar_1d_99:.2%}"
            },
            'volatility_metrics': {
                'Realized Volatility': f"{metrics.realized_volatility:.2%}",
                'GARCH Volatility': f"{metrics.garch_volatility:.2%}",
                'Volatility Forecast': f"{metrics.volatility_forecast:.2%}"
            },
            'drawdown_analysis': {
                'Current Drawdown': f"{metrics.current_drawdown:.2%}",
                'Max Drawdown (1Y)': f"{metrics.max_drawdown_1y:.2%}",
                'Drawdown Duration': f"{metrics.drawdown_duration} days"
            },
            'concentration_risk': {
                'Portfolio Correlation': f"{metrics.portfolio_correlation:.3f}",
                'HHI Concentration': f"{metrics.concentration_hhi:.3f}",
                'Effective Positions': f"{metrics.effective_positions:.1f}"
            },
            'market_risk': {
                'Market Beta': f"{metrics.market_beta:.2f}"
            },
            'tail_risk': {
                'Skewness': f"{metrics.skewness:.3f}",
                'Kurtosis': f"{metrics.kurtosis:.3f}",
                'Tail Ratio': f"{metrics.tail_ratio:.2f}"
            }
        }
    
    def _generate_benchmark_comparison(self, comparison: BenchmarkComparison) -> Dict[str, Any]:
        """Generate benchmark comparison section"""
        return {
            'title': 'Benchmark Comparison',
            'return_comparison': {
                'Strategy Return': f"{comparison.strategy_return:.2%}",
                'Benchmark Return': f"{comparison.benchmark_return:.2%}",
                'Excess Return': f"{comparison.excess_return:.2%}",
                'Annualized Excess': f"{comparison.annualized_excess:.2%}"
            },
            'risk_comparison': {
                'Strategy Volatility': f"{comparison.strategy_volatility:.2%}",
                'Benchmark Volatility': f"{comparison.benchmark_volatility:.2%}",
                'Tracking Error': f"{comparison.tracking_error:.2%}"
            },
            'risk_adjusted_metrics': {
                'Alpha': f"{comparison.alpha:.2%}",
                'Beta': f"{comparison.beta:.2f}",
                'Correlation': f"{comparison.correlation:.3f}",
                'Information Ratio': f"{comparison.information_ratio:.2f}"
            },
            'drawdown_comparison': {
                'Strategy Max DD': f"{comparison.strategy_max_dd:.2%}",
                'Benchmark Max DD': f"{comparison.benchmark_max_dd:.2%}",
                'Relative Max DD': f"{comparison.relative_max_dd:.2%}"
            }
        }
    
    def _generate_strategy_analysis(self, config: Dict) -> Dict[str, Any]:
        """Generate strategy analysis section"""
        return {
            'title': 'Strategy Analysis',
            'configuration': {
                'Strategy Name': config.get('strategy_name', 'Unknown'),
                'Strategy Type': config.get('strategy_type', 'Custom'),
                'Universe Size': len(config.get('universe', [])),
                'Rebalance Frequency': config.get('rebalance_frequency', 'Unknown')
            },
            'parameters': config.get('strategy_parameters', {}),
            'backtest_settings': {
                'Start Date': config.get('start_date'),
                'End Date': config.get('end_date'),
                'Initial Capital': f"${config.get('initial_capital', 0):,.2f}",
                'Commission Rate': f"{config.get('commission_rate', 0):.3%}",
                'Slippage Rate': f"{config.get('slippage_rate', 0):.3%}"
            }
        }
    
    def _generate_charts(self, equity_curve: pd.Series = None,
                        trades: List[Dict] = None,
                        performance_metrics: PerformanceMetrics = None,
                        trade_metrics: TradeMetrics = None) -> Dict[str, str]:
        """Generate charts for the report"""
        charts = {}
        
        try:
            # Equity curve chart
            if equity_curve is not None and not equity_curve.empty:
                charts['equity_curve'] = self._create_equity_curve_chart(equity_curve)
            
            # Drawdown chart
            if equity_curve is not None and not equity_curve.empty:
                charts['drawdown'] = self._create_drawdown_chart(equity_curve)
            
            # Trade distribution chart
            if trades and len(trades) > 10:
                charts['trade_distribution'] = self._create_trade_distribution_chart(trades)
            
            # Monthly returns heatmap
            if equity_curve is not None and not equity_curve.empty:
                charts['monthly_returns'] = self._create_monthly_returns_heatmap(equity_curve)
            
        except Exception as e:
            logger.error(f"Error generating charts: {str(e)}")
            charts['error'] = str(e)
        
        return charts
    
    def _create_equity_curve_chart(self, equity_curve: pd.Series) -> str:
        """Create equity curve chart"""
        fig, ax = plt.subplots(figsize=(12, 6))
        
        ax.plot(equity_curve.index, equity_curve.values, linewidth=2, color='blue')
        ax.set_title('Portfolio Equity Curve', fontsize=14, fontweight='bold')
        ax.set_xlabel('Date')
        ax.set_ylabel('Portfolio Value ($)')
        ax.grid(True, alpha=0.3)
        
        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
        plt.xticks(rotation=45)
        
        # Format y-axis
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        
        plt.tight_layout()
        
        # Convert to base64 string
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        chart_data = base64.b64encode(buffer.read()).decode()
        plt.close()
        
        return f"data:image/png;base64,{chart_data}"
    
    def _create_drawdown_chart(self, equity_curve: pd.Series) -> str:
        """Create drawdown chart"""
        # Calculate drawdown
        running_max = equity_curve.expanding().max()
        drawdown = (equity_curve - running_max) / running_max
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        ax.fill_between(drawdown.index, drawdown.values, 0, alpha=0.3, color='red')
        ax.plot(drawdown.index, drawdown.values, linewidth=1, color='red')
        ax.set_title('Portfolio Drawdown', fontsize=14, fontweight='bold')
        ax.set_xlabel('Date')
        ax.set_ylabel('Drawdown (%)')
        ax.grid(True, alpha=0.3)
        
        # Format axes
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.1%}'))
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        
        # Convert to base64 string
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        chart_data = base64.b64encode(buffer.read()).decode()
        plt.close()
        
        return f"data:image/png;base64,{chart_data}"
    
    def _create_trade_distribution_chart(self, trades: List[Dict]) -> str:
        """Create trade P&L distribution chart"""
        # Extract P&L values
        pnl_values = [trade.get('pnl', 0) for trade in trades if 'pnl' in trade]
        
        if not pnl_values:
            return ""
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
        
        # Histogram
        ax1.hist(pnl_values, bins=30, alpha=0.7, color='blue', edgecolor='black')
        ax1.set_title('Trade P&L Distribution')
        ax1.set_xlabel('P&L ($)')
        ax1.set_ylabel('Frequency')
        ax1.grid(True, alpha=0.3)
        ax1.axvline(x=0, color='red', linestyle='--', alpha=0.7)
        
        # Box plot
        ax2.boxplot(pnl_values, vert=True)
        ax2.set_title('Trade P&L Box Plot')
        ax2.set_ylabel('P&L ($)')
        ax2.grid(True, alpha=0.3)
        ax2.axhline(y=0, color='red', linestyle='--', alpha=0.7)
        
        plt.tight_layout()
        
        # Convert to base64 string
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        chart_data = base64.b64encode(buffer.read()).decode()
        plt.close()
        
        return f"data:image/png;base64,{chart_data}"
    
    def _create_monthly_returns_heatmap(self, equity_curve: pd.Series) -> str:
        """Create monthly returns heatmap"""
        try:
            # Calculate monthly returns
            monthly_returns = equity_curve.resample('M').last().pct_change().dropna()
            
            if len(monthly_returns) < 12:
                return ""
            
            # Create pivot table for heatmap
            monthly_data = monthly_returns.to_frame('returns')
            monthly_data['year'] = monthly_data.index.year
            monthly_data['month'] = monthly_data.index.month
            
            pivot_table = monthly_data.pivot_table(
                values='returns', index='year', columns='month', aggfunc='first'
            )
            
            fig, ax = plt.subplots(figsize=(12, 8))
            
            # Create heatmap
            im = ax.imshow(pivot_table.values, cmap='RdYlGn', aspect='auto')
            
            # Set ticks and labels
            ax.set_xticks(range(12))
            ax.set_xticklabels(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                               'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])
            ax.set_yticks(range(len(pivot_table.index)))
            ax.set_yticklabels(pivot_table.index)
            
            # Add colorbar
            cbar = plt.colorbar(im, ax=ax)
            cbar.set_label('Monthly Return (%)')
            
            # Add text annotations
            for i in range(len(pivot_table.index)):
                for j in range(12):
                    value = pivot_table.iloc[i, j]
                    if not pd.isna(value):
                        text = ax.text(j, i, f'{value:.1%}', ha='center', va='center',
                                     color='white' if abs(value) > 0.05 else 'black')
            
            ax.set_title('Monthly Returns Heatmap', fontsize=14, fontweight='bold')
            plt.tight_layout()
            
            # Convert to base64 string
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            chart_data = base64.b64encode(buffer.read()).decode()
            plt.close()
            
            return f"data:image/png;base64,{chart_data}"
            
        except Exception as e:
            logger.error(f"Error creating monthly returns heatmap: {str(e)}")
            return ""
    
    def _generate_conclusions(self, performance_metrics: PerformanceMetrics,
                            trade_metrics: TradeMetrics = None,
                            risk_metrics: RiskMetrics = None,
                            benchmark_comparison: BenchmarkComparison = None) -> Dict[str, Any]:
        """Generate conclusions and recommendations"""
        conclusions = {
            'overall_assessment': '',
            'strengths': [],
            'weaknesses': [],
            'recommendations': [],
            'risk_assessment': ''
        }
        
        try:
            # Overall assessment
            if performance_metrics.sharpe_ratio > 1.5 and performance_metrics.max_drawdown < 0.15:
                conclusions['overall_assessment'] = "The strategy demonstrates strong risk-adjusted performance with acceptable drawdown levels."
            elif performance_metrics.sharpe_ratio > 1.0:
                conclusions['overall_assessment'] = "The strategy shows decent performance but may benefit from optimization."
            else:
                conclusions['overall_assessment'] = "The strategy requires significant improvement in risk-adjusted returns."
            
            # Strengths
            if performance_metrics.sharpe_ratio > 1.2:
                conclusions['strengths'].append("Good risk-adjusted returns")
            if performance_metrics.max_drawdown < 0.12:
                conclusions['strengths'].append("Low maximum drawdown")
            if trade_metrics and trade_metrics.win_rate > 0.55:
                conclusions['strengths'].append("High win rate")
            if benchmark_comparison and benchmark_comparison.alpha > 0.02:
                conclusions['strengths'].append("Positive alpha generation")
            
            # Weaknesses
            if performance_metrics.volatility > 0.25:
                conclusions['weaknesses'].append("High volatility")
            if trade_metrics and trade_metrics.profit_factor < 1.3:
                conclusions['weaknesses'].append("Low profit factor")
            if abs(performance_metrics.skewness) > 1.5:
                conclusions['weaknesses'].append("Skewed return distribution")
            
            # Recommendations
            recommendations = self._generate_recommendations(
                performance_metrics, trade_metrics, risk_metrics
            )
            conclusions['recommendations'] = recommendations
            
            # Risk assessment
            if risk_metrics:
                if risk_metrics.var_1d_95 > 0.03:
                    conclusions['risk_assessment'] = "High risk strategy requiring careful position sizing"
                elif risk_metrics.var_1d_95 > 0.02:
                    conclusions['risk_assessment'] = "Moderate risk strategy suitable for most investors"
                else:
                    conclusions['risk_assessment'] = "Low risk strategy with conservative risk profile"
        
        except Exception as e:
            logger.error(f"Error generating conclusions: {str(e)}")
            conclusions['error'] = str(e)
        
        return conclusions
    
    def _generate_recommendations(self, performance_metrics: PerformanceMetrics,
                                trade_metrics: TradeMetrics = None,
                                risk_metrics: RiskMetrics = None) -> List[str]:
        """Generate strategy improvement recommendations"""
        recommendations = []
        
        # Performance-based recommendations
        if performance_metrics.sharpe_ratio < 1.0:
            recommendations.append("Consider improving signal quality or risk management to increase Sharpe ratio")
        
        if performance_metrics.max_drawdown > 0.20:
            recommendations.append("Implement stronger position sizing or stop-loss mechanisms to reduce drawdown")
        
        if performance_metrics.volatility > 0.30:
            recommendations.append("Consider volatility targeting or position sizing based on realized volatility")
        
        # Trade-based recommendations
        if trade_metrics:
            if trade_metrics.win_rate < 0.45:
                recommendations.append("Analyze and improve signal generation to increase win rate")
            
            if trade_metrics.profit_factor < 1.5:
                recommendations.append("Focus on improving average win size or reducing average loss size")
            
            if trade_metrics.max_consecutive_losses > 8:
                recommendations.append("Implement streak-breaking mechanisms or position sizing adjustments")
        
        # Risk-based recommendations
        if risk_metrics:
            if risk_metrics.concentration_hhi > 0.3:
                recommendations.append("Consider diversification to reduce concentration risk")
            
            if abs(risk_metrics.skewness) > 2.0:
                recommendations.append("Address tail risk through hedging or position limits")
        
        return recommendations
    
    def export_report_to_html(self, report: Dict[str, Any]) -> str:
        """Export report to HTML format"""
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Backtest Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .header { text-align: center; margin-bottom: 30px; }
                .section { margin-bottom: 30px; }
                .metric-table { width: 100%; border-collapse: collapse; }
                .metric-table th, .metric-table td { 
                    border: 1px solid #ddd; padding: 8px; text-align: left; 
                }
                .metric-table th { background-color: #f2f2f2; }
                .chart { text-align: center; margin: 20px 0; }
                .highlight { background-color: #e8f5e8; }
                .concern { background-color: #ffe8e8; }
            </style>
        </head>
        <body>
            {content}
        </body>
        </html>
        """
        
        # Generate HTML content
        content = self._generate_html_content(report)
        
        return html_template.format(content=content)
    
    def _generate_html_content(self, report: Dict[str, Any]) -> str:
        """Generate HTML content from report data"""
        html_parts = []
        
        # Header
        html_parts.append('<div class="header">')
        html_parts.append('<h1>Backtesting Report</h1>')
        if 'metadata' in report:
            metadata = report['metadata']
            html_parts.append(f"<p>Generated: {metadata.get('generated_at', '')}</p>")
            html_parts.append(f"<p>Strategy: {metadata.get('strategy_name', 'Unknown')}</p>")
        html_parts.append('</div>')
        
        # Executive Summary
        if 'executive_summary' in report:
            html_parts.append(self._section_to_html('Executive Summary', report['executive_summary']))
        
        # Other sections
        if 'sections' in report:
            for section_name, section_data in report['sections'].items():
                html_parts.append(self._section_to_html(section_data.get('title', section_name), section_data))
        
        # Charts
        if 'charts' in report:
            html_parts.append('<div class="section"><h2>Charts</h2>')
            for chart_name, chart_data in report['charts'].items():
                if chart_data.startswith('data:image'):
                    html_parts.append(f'<div class="chart"><h3>{chart_name.replace("_", " ").title()}</h3>')
                    html_parts.append(f'<img src="{chart_data}" alt="{chart_name}" style="max-width: 100%;"></div>')
            html_parts.append('</div>')
        
        return '\n'.join(html_parts)
    
    def _section_to_html(self, title: str, section_data: Dict) -> str:
        """Convert section data to HTML"""
        html_parts = [f'<div class="section"><h2>{title}</h2>']
        
        for key, value in section_data.items():
            if key == 'title':
                continue
            elif isinstance(value, dict):
                html_parts.append(f'<h3>{key.replace("_", " ").title()}</h3>')
                html_parts.append('<table class="metric-table">')
                for metric, metric_value in value.items():
                    html_parts.append(f'<tr><td>{metric}</td><td>{metric_value}</td></tr>')
                html_parts.append('</table>')
            elif isinstance(value, list):
                html_parts.append(f'<h3>{key.replace("_", " ").title()}</h3>')
                html_parts.append('<ul>')
                for item in value:
                    css_class = 'highlight' if 'highlight' in key else ('concern' if 'concern' in key else '')
                    html_parts.append(f'<li class="{css_class}">{item}</li>')
                html_parts.append('</ul>')
        
        html_parts.append('</div>')
        return '\n'.join(html_parts)