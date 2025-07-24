"""
Trade analysis for portfolio performance evaluation
"""
import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class TradeMetrics:
    """Container for trade analysis metrics"""
    # Basic trade stats
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    
    # P&L metrics
    total_pnl: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    avg_trade_pnl: float = 0.0
    largest_win: float = 0.0
    largest_loss: float = 0.0
    
    # Risk metrics
    profit_factor: float = 0.0  # Ratio of gross profit to gross loss
    expectancy: float = 0.0     # Expected value per trade
    kelly_criterion: float = 0.0
    
    # Duration metrics
    avg_holding_period: float = 0.0  # In days
    avg_win_duration: float = 0.0
    avg_loss_duration: float = 0.0
    
    # Consecutive metrics
    max_consecutive_wins: int = 0
    max_consecutive_losses: int = 0
    
    # Distribution metrics
    trade_pnl_std: float = 0.0
    trade_pnl_skew: float = 0.0
    trade_pnl_kurtosis: float = 0.0

class TradeAnalyzer:
    """Analyzer for individual trade performance"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def analyze_trades(self, trades_df: pd.DataFrame) -> TradeMetrics:
        """
        Analyze trade performance from transaction data
        
        Args:
            trades_df: DataFrame with columns: symbol, entry_date, exit_date, 
                      entry_price, exit_price, quantity, pnl, commission
        
        Returns:
            TradeMetrics object with comprehensive trade statistics
        """
        if trades_df.empty:
            self.logger.warning("No trades provided for analysis")
            return TradeMetrics()
        
        try:
            return self._calculate_trade_metrics(trades_df)
        except Exception as e:
            self.logger.error(f"Error analyzing trades: {e}")
            return TradeMetrics()
    
    def _calculate_trade_metrics(self, trades_df: pd.DataFrame) -> TradeMetrics:
        """Calculate comprehensive trade metrics"""
        
        # Basic trade counts
        total_trades = len(trades_df)
        winning_trades = len(trades_df[trades_df['pnl'] > 0])
        losing_trades = len(trades_df[trades_df['pnl'] < 0])
        
        # Win rate
        win_rate = winning_trades / total_trades if total_trades > 0 else 0.0
        
        # P&L metrics
        total_pnl = trades_df['pnl'].sum()
        avg_trade_pnl = trades_df['pnl'].mean()
        
        # Separate wins and losses
        wins = trades_df[trades_df['pnl'] > 0]['pnl']
        losses = trades_df[trades_df['pnl'] < 0]['pnl']
        
        avg_win = wins.mean() if len(wins) > 0 else 0.0
        avg_loss = losses.mean() if len(losses) > 0 else 0.0
        largest_win = wins.max() if len(wins) > 0 else 0.0
        largest_loss = losses.min() if len(losses) > 0 else 0.0
        
        # Risk metrics
        gross_profit = wins.sum() if len(wins) > 0 else 0.0
        gross_loss = abs(losses.sum()) if len(losses) > 0 else 0.0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Expectancy (expected value per trade)
        expectancy = (win_rate * avg_win) + ((1 - win_rate) * avg_loss)
        
        # Kelly Criterion
        kelly_criterion = self._calculate_kelly_criterion(win_rate, avg_win, abs(avg_loss))
        
        # Duration metrics
        if 'entry_date' in trades_df.columns and 'exit_date' in trades_df.columns:
            trades_df['holding_period'] = (
                pd.to_datetime(trades_df['exit_date']) - 
                pd.to_datetime(trades_df['entry_date'])
            ).dt.days
            
            avg_holding_period = trades_df['holding_period'].mean()
            
            win_trades = trades_df[trades_df['pnl'] > 0]
            loss_trades = trades_df[trades_df['pnl'] < 0]
            
            avg_win_duration = win_trades['holding_period'].mean() if len(win_trades) > 0 else 0.0
            avg_loss_duration = loss_trades['holding_period'].mean() if len(loss_trades) > 0 else 0.0
        else:
            avg_holding_period = avg_win_duration = avg_loss_duration = 0.0
        
        # Consecutive win/loss streaks
        max_consecutive_wins, max_consecutive_losses = self._calculate_streaks(trades_df['pnl'])
        
        # Distribution metrics
        trade_pnl_std = trades_df['pnl'].std()
        trade_pnl_skew = trades_df['pnl'].skew()
        trade_pnl_kurtosis = trades_df['pnl'].kurtosis()
        
        return TradeMetrics(
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            total_pnl=total_pnl,
            avg_win=avg_win,
            avg_loss=avg_loss,
            avg_trade_pnl=avg_trade_pnl,
            largest_win=largest_win,
            largest_loss=largest_loss,
            profit_factor=profit_factor,
            expectancy=expectancy,
            kelly_criterion=kelly_criterion,
            avg_holding_period=avg_holding_period,
            avg_win_duration=avg_win_duration,
            avg_loss_duration=avg_loss_duration,
            max_consecutive_wins=max_consecutive_wins,
            max_consecutive_losses=max_consecutive_losses,
            trade_pnl_std=trade_pnl_std,
            trade_pnl_skew=trade_pnl_skew,
            trade_pnl_kurtosis=trade_pnl_kurtosis
        )
    
    def _calculate_kelly_criterion(self, win_rate: float, avg_win: float, avg_loss: float) -> float:
        """Calculate Kelly Criterion for optimal position sizing"""
        if avg_loss == 0:
            return 0.0
        
        win_loss_ratio = avg_win / avg_loss
        kelly = win_rate - ((1 - win_rate) / win_loss_ratio)
        
        # Cap Kelly at 25% for risk management
        return min(max(kelly, 0.0), 0.25)
    
    def _calculate_streaks(self, pnl_series: pd.Series) -> tuple:
        """Calculate maximum consecutive wins and losses"""
        if len(pnl_series) == 0:
            return 0, 0
        
        win_streak = loss_streak = 0
        max_win_streak = max_loss_streak = 0
        
        for pnl in pnl_series:
            if pnl > 0:
                win_streak += 1
                loss_streak = 0
                max_win_streak = max(max_win_streak, win_streak)
            elif pnl < 0:
                loss_streak += 1
                win_streak = 0
                max_loss_streak = max(max_loss_streak, loss_streak)
            else:
                win_streak = loss_streak = 0
        
        return max_win_streak, max_loss_streak
    
    def analyze_trade_distribution(self, trades_df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze distribution of trade P&L"""
        if trades_df.empty:
            return {}
        
        pnl = trades_df['pnl']
        
        return {
            'percentiles': {
                '5th': pnl.quantile(0.05),
                '25th': pnl.quantile(0.25),
                '50th': pnl.quantile(0.50),
                '75th': pnl.quantile(0.75),
                '95th': pnl.quantile(0.95)
            },
            'outliers': {
                'positive': pnl[pnl > pnl.quantile(0.95)].tolist(),
                'negative': pnl[pnl < pnl.quantile(0.05)].tolist()
            },
            'histogram_data': np.histogram(pnl, bins=20)
        }
    
    def analyze_by_symbol(self, trades_df: pd.DataFrame) -> Dict[str, TradeMetrics]:
        """Analyze trades grouped by symbol"""
        if trades_df.empty or 'symbol' not in trades_df.columns:
            return {}
        
        symbol_analysis = {}
        
        for symbol in trades_df['symbol'].unique():
            symbol_trades = trades_df[trades_df['symbol'] == symbol]
            symbol_analysis[symbol] = self.analyze_trades(symbol_trades)
        
        return symbol_analysis
    
    def analyze_by_timeframe(self, trades_df: pd.DataFrame, 
                           timeframe: str = 'M') -> Dict[str, TradeMetrics]:
        """Analyze trades grouped by time period"""
        if trades_df.empty or 'entry_date' not in trades_df.columns:
            return {}
        
        trades_df['entry_date'] = pd.to_datetime(trades_df['entry_date'])
        trades_df['period'] = trades_df['entry_date'].dt.to_period(timeframe)
        
        period_analysis = {}
        
        for period in trades_df['period'].unique():
            period_trades = trades_df[trades_df['period'] == period]
            period_analysis[str(period)] = self.analyze_trades(period_trades)
        
        return period_analysis