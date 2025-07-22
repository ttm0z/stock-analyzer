"""
Base strategy class for implementing trading strategies.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

@dataclass
class Signal:
    """Trading signal"""
    symbol: str
    signal_type: str  # BUY, SELL, HOLD
    strength: float  # 0-1 confidence level
    price: float
    timestamp: datetime
    quantity: Optional[float] = None
    reason: str = ""
    metadata: Dict = field(default_factory=dict)

@dataclass
class StrategyContext:
    """Context passed to strategy methods"""
    current_date: datetime
    portfolio_value: float
    cash_balance: float
    positions: Dict[str, float]  # symbol -> quantity
    market_data: Dict[str, pd.DataFrame]  # symbol -> OHLCV data
    indicators: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict = field(default_factory=dict)

class BaseStrategy(ABC):
    """Abstract base class for trading strategies"""
    
    def __init__(self, name: str, parameters: Dict = None):
        self.name = name
        self.parameters = parameters or {}
        self.universe = []  # List of symbols to trade
        self.is_initialized = False
        self.lookback_period = 252  # Default 1 year
        self.rebalance_frequency = 'daily'  # daily, weekly, monthly
        self.position_sizer = None
        self.risk_manager = None
        
        # Strategy state
        self.current_signals = {}
        self.last_rebalance_date = None
        self.strategy_state = {}
        
        # Performance tracking
        self.total_signals = 0
        self.signals_generated = []
        
        # Validation
        self._validate_parameters()
    
    @abstractmethod
    def initialize(self, universe: List[str], start_date: datetime, end_date: datetime):
        """Initialize strategy with trading universe and date range"""
        pass
    
    @abstractmethod
    def generate_signals(self, context: StrategyContext) -> List[Signal]:
        """Generate trading signals based on current market data"""
        pass
    
    @abstractmethod
    def get_required_data(self) -> Dict[str, List[str]]:
        """Get required data for strategy (timeframes, indicators, etc.)"""
        pass
    
    def should_rebalance(self, current_date: datetime) -> bool:
        """Check if strategy should rebalance on current date"""
        if not self.last_rebalance_date:
            return True
        
        if self.rebalance_frequency == 'daily':
            return True
        elif self.rebalance_frequency == 'weekly':
            return current_date.weekday() == 0  # Monday
        elif self.rebalance_frequency == 'monthly':
            return current_date.day == 1
        else:
            return False
    
    def calculate_position_size(self, signal: Signal, context: StrategyContext) -> float:
        """Calculate position size for a signal"""
        if self.position_sizer:
            return self.position_sizer.calculate_size(signal, context)
        
        # Default: equal weight among all positions
        max_positions = self.parameters.get('max_positions', 10)
        target_weight = 1.0 / max_positions
        target_value = context.portfolio_value * target_weight
        
        if signal.price > 0:
            return target_value / signal.price
        return 0
    
    def apply_risk_management(self, signals: List[Signal], context: StrategyContext) -> List[Signal]:
        """Apply risk management rules to signals"""
        if self.risk_manager:
            return self.risk_manager.filter_signals(signals, context)
        
        # Basic risk management
        filtered_signals = []
        
        for signal in signals:
            # Basic position size limits
            max_position_value = context.portfolio_value * 0.1  # 10% max per position
            signal_value = signal.quantity * signal.price if signal.quantity else 0
            
            if signal_value <= max_position_value:
                filtered_signals.append(signal)
            else:
                # Reduce position size
                signal.quantity = max_position_value / signal.price
                filtered_signals.append(signal)
        
        return filtered_signals
    
    def get_parameter(self, name: str, default=None):
        """Get strategy parameter with default"""
        return self.parameters.get(name, default)
    
    def set_parameter(self, name: str, value):
        """Set strategy parameter"""
        self.parameters[name] = value
        self._validate_parameters()
    
    def get_strategy_state(self) -> Dict:
        """Get current strategy state for persistence"""
        return {
            'name': self.name,
            'parameters': self.parameters,
            'universe': self.universe,
            'is_initialized': self.is_initialized,
            'lookback_period': self.lookback_period,
            'rebalance_frequency': self.rebalance_frequency,
            'current_signals': self.current_signals,
            'last_rebalance_date': self.last_rebalance_date,
            'strategy_state': self.strategy_state,
            'total_signals': self.total_signals
        }
    
    def set_strategy_state(self, state: Dict):
        """Restore strategy state from persistence"""
        self.name = state.get('name', self.name)
        self.parameters = state.get('parameters', {})
        self.universe = state.get('universe', [])
        self.is_initialized = state.get('is_initialized', False)
        self.lookback_period = state.get('lookback_period', 252)
        self.rebalance_frequency = state.get('rebalance_frequency', 'daily')
        self.current_signals = state.get('current_signals', {})
        self.last_rebalance_date = state.get('last_rebalance_date')
        self.strategy_state = state.get('strategy_state', {})
        self.total_signals = state.get('total_signals', 0)
    
    def _validate_parameters(self):
        """Validate strategy parameters"""
        # Override in subclasses for specific validation
        pass
    
    def calculate_technical_indicators(self, data: pd.DataFrame) -> Dict[str, pd.Series]:
        """Calculate common technical indicators"""
        indicators = {}
        
        try:
            # Simple Moving Averages
            for period in [10, 20, 50, 200]:
                indicators[f'sma_{period}'] = data['close'].rolling(period).mean()
            
            # Exponential Moving Averages
            for period in [12, 26]:
                indicators[f'ema_{period}'] = data['close'].ewm(span=period).mean()
            
            # RSI
            indicators['rsi'] = self._calculate_rsi(data['close'])
            
            # MACD
            macd_line, signal_line, histogram = self._calculate_macd(data['close'])
            indicators['macd'] = macd_line
            indicators['macd_signal'] = signal_line
            indicators['macd_histogram'] = histogram
            
            # Bollinger Bands
            bb_upper, bb_middle, bb_lower = self._calculate_bollinger_bands(data['close'])
            indicators['bb_upper'] = bb_upper
            indicators['bb_middle'] = bb_middle
            indicators['bb_lower'] = bb_lower
            
            # Volume indicators
            indicators['volume_sma'] = data['volume'].rolling(20).mean()
            
        except Exception as e:
            logger.error(f"Error calculating technical indicators: {str(e)}")
        
        return indicators
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index"""
        delta = prices.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.rolling(period).mean()
        avg_loss = loss.rolling(period).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def _calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate MACD"""
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal).mean()
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
    
    def _calculate_bollinger_bands(self, prices: pd.Series, period: int = 20, std_dev: int = 2) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate Bollinger Bands"""
        middle = prices.rolling(period).mean()
        std = prices.rolling(period).std()
        
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        
        return upper, middle, lower
    
    def log_signal(self, signal: Signal):
        """Log generated signal"""
        self.total_signals += 1
        self.signals_generated.append(signal)
        self.current_signals[signal.symbol] = signal
        
        logger.info(f"Strategy {self.name} generated {signal.signal_type} signal for {signal.symbol} "
                   f"at {signal.price} with strength {signal.strength}")

class PositionSizer(ABC):
    """Abstract base class for position sizing"""
    
    @abstractmethod
    def calculate_size(self, signal: Signal, context: StrategyContext) -> float:
        """Calculate position size for a signal"""
        pass

class EqualWeightSizer(PositionSizer):
    """Equal weight position sizer"""
    
    def __init__(self, max_positions: int = 10):
        self.max_positions = max_positions
    
    def calculate_size(self, signal: Signal, context: StrategyContext) -> float:
        """Calculate equal weight position size"""
        target_weight = 1.0 / self.max_positions
        target_value = context.portfolio_value * target_weight
        
        if signal.price > 0:
            return target_value / signal.price
        return 0

class VolatilityTargetSizer(PositionSizer):
    """Position sizer based on volatility targeting"""
    
    def __init__(self, target_volatility: float = 0.15, lookback: int = 20):
        self.target_volatility = target_volatility
        self.lookback = lookback
    
    def calculate_size(self, signal: Signal, context: StrategyContext) -> float:
        """Calculate volatility-adjusted position size"""
        try:
            # Get historical data for the symbol
            symbol_data = context.market_data.get(signal.symbol)
            if symbol_data is None or len(symbol_data) < self.lookback:
                return 0
            
            # Calculate historical volatility
            returns = symbol_data['close'].pct_change().dropna()
            if len(returns) < self.lookback:
                return 0
            
            hist_vol = returns.tail(self.lookback).std() * np.sqrt(252)  # Annualized
            
            if hist_vol > 0:
                vol_adjustment = self.target_volatility / hist_vol
                base_weight = 0.1  # 10% base allocation
                adjusted_weight = base_weight * vol_adjustment
                
                # Cap at 20% of portfolio
                adjusted_weight = min(adjusted_weight, 0.2)
                
                target_value = context.portfolio_value * adjusted_weight
                return target_value / signal.price
            
            return 0
            
        except Exception as e:
            logger.error(f"Error in volatility targeting: {str(e)}")
            return 0

class RiskManager(ABC):
    """Abstract base class for risk management"""
    
    @abstractmethod
    def filter_signals(self, signals: List[Signal], context: StrategyContext) -> List[Signal]:
        """Filter signals based on risk rules"""
        pass

class BasicRiskManager(RiskManager):
    """Basic risk management implementation"""
    
    def __init__(self, max_position_weight: float = 0.1, max_portfolio_risk: float = 0.02):
        self.max_position_weight = max_position_weight
        self.max_portfolio_risk = max_portfolio_risk
    
    def filter_signals(self, signals: List[Signal], context: StrategyContext) -> List[Signal]:
        """Apply basic risk filters"""
        filtered_signals = []
        
        for signal in signals:
            # Position size limit
            if signal.quantity:
                position_value = signal.quantity * signal.price
                position_weight = position_value / context.portfolio_value
                
                if position_weight > self.max_position_weight:
                    # Reduce position size
                    signal.quantity = (context.portfolio_value * self.max_position_weight) / signal.price
            
            # Don't trade if already have large position
            current_position = context.positions.get(signal.symbol, 0)
            current_value = abs(current_position * signal.price)
            current_weight = current_value / context.portfolio_value
            
            if current_weight < self.max_position_weight:
                filtered_signals.append(signal)
        
        return filtered_signals