"""
Moving Average Crossover Strategy
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime

from ..base_strategy import BaseStrategy, StrategyContext, Signal

class MovingAverageStrategy(BaseStrategy):
    """Simple Moving Average Crossover Strategy"""
    
    def __init__(self, parameters: Dict = None):
        default_params = {
            'fast_period': 20,
            'slow_period': 50,  
            'min_volume': 100000,  # Minimum daily volume
            'position_size': 0.1   # 10% of portfolio per position
        }
        
        if parameters:
            default_params.update(parameters)
        
        super().__init__("Moving Average Crossover", default_params)
        
        self.fast_period = self.parameters['fast_period']
        self.slow_period = self.parameters['slow_period'] 
        self.min_volume = self.parameters['min_volume']
        self.position_size = self.parameters['position_size']
        
        # Validation
        if self.fast_period >= self.slow_period:
            raise ValueError("Fast period must be less than slow period")
        
        # Set lookback period to accommodate slow MA + buffer
        self.lookback_period = self.slow_period + 50
    
    def initialize(self, context: StrategyContext) -> bool:
        """Initialize strategy with market data"""
        try:
            # Verify we have sufficient data for all symbols
            for symbol in self.universe:
                if symbol not in context.market_data:
                    self.logger.warning(f"No data available for {symbol}")
                    continue
                
                data = context.market_data[symbol]
                if len(data) < self.slow_period:
                    self.logger.warning(f"Insufficient data for {symbol}: {len(data)} < {self.slow_period}")
            
            self.is_initialized = True
            self.logger.info(f"Moving Average strategy initialized with {len(self.universe)} symbols")
            return True
            
        except Exception as e:
            self.logger.error(f"Strategy initialization failed: {e}")
            return False
    
    def generate_signals(self, context: StrategyContext) -> List[Signal]:
        """Generate trading signals based on moving average crossover"""
        signals = []
        
        if not self.is_initialized:
            return signals
        
        try:
            for symbol in self.universe:
                signal = self._analyze_symbol(symbol, context)
                if signal:
                    signals.append(signal)
            
            return signals
            
        except Exception as e:
            self.logger.error(f"Signal generation failed: {e}")
            return []
    
    def _analyze_symbol(self, symbol: str, context: StrategyContext) -> Optional[Signal]:
        """Analyze individual symbol for trading signals"""
        
        if symbol not in context.market_data:
            return None
        
        data = context.market_data[symbol]
        
        # Ensure we have enough data
        if len(data) < self.slow_period:
            return None
        
        # Calculate moving averages
        data = data.copy()
        data['fast_ma'] = data['close'].rolling(window=self.fast_period).mean()
        data['slow_ma'] = data['close'].rolling(window=self.slow_period).mean()
        
        # Get current and previous values
        current_idx = -1
        prev_idx = -2
        
        if len(data) < abs(prev_idx):
            return None
        
        current_fast = data['fast_ma'].iloc[current_idx]
        current_slow = data['slow_ma'].iloc[current_idx]
        prev_fast = data['fast_ma'].iloc[prev_idx]
        prev_slow = data['slow_ma'].iloc[prev_idx]
        
        current_price = data['close'].iloc[current_idx]
        current_volume = data['volume'].iloc[current_idx] if 'volume' in data.columns else 0
        
        # Skip if insufficient volume
        if current_volume < self.min_volume:
            return None
        
        # Check for crossover signals
        signal_type = None
        reason = ""
        strength = 0.0
        
        # Bullish crossover: fast MA crosses above slow MA
        if (prev_fast <= prev_slow and current_fast > current_slow):
            signal_type = "BUY"
            reason = f"Fast MA ({self.fast_period}) crossed above Slow MA ({self.slow_period})"
            
            # Calculate signal strength based on:
            # 1. Distance between MAs
            # 2. Slope of fast MA
            # 3. Volume relative to average
            ma_separation = abs(current_fast - current_slow) / current_slow
            fast_ma_slope = (current_fast - prev_fast) / prev_fast
            
            strength = min(1.0, (ma_separation * 10) + (fast_ma_slope * 2))
            strength = max(0.1, strength)  # Minimum 10% confidence
        
        # Bearish crossover: fast MA crosses below slow MA  
        elif (prev_fast >= prev_slow and current_fast < current_slow):
            signal_type = "SELL"
            reason = f"Fast MA ({self.fast_period}) crossed below Slow MA ({self.slow_period})"
            
            ma_separation = abs(current_fast - current_slow) / current_slow
            fast_ma_slope = abs(current_fast - prev_fast) / prev_fast
            
            strength = min(1.0, (ma_separation * 10) + (fast_ma_slope * 2))
            strength = max(0.1, strength)
        
        # No signal
        if not signal_type:
            return None
        
        # Calculate position size
        portfolio_allocation = self.position_size * strength
        
        return Signal(
            symbol=symbol,
            signal_type=signal_type,
            strength=strength,
            price=current_price,
            timestamp=context.current_date,
            quantity=portfolio_allocation,  # Portfolio percentage
            reason=reason,
            metadata={
                'fast_ma': current_fast,
                'slow_ma': current_slow,
                'fast_period': self.fast_period,
                'slow_period': self.slow_period,
                'volume': current_volume,
                'ma_separation': abs(current_fast - current_slow) / current_slow
            }
        )
    
    def should_rebalance(self, context: StrategyContext) -> bool:
        """Determine if portfolio should be rebalanced"""
        # For MA crossover, we rebalance on every signal
        return True
    
    def get_required_data_fields(self) -> List[str]:
        """Return list of required data fields"""
        return ['open', 'high', 'low', 'close', 'volume']
    
    def get_lookback_period(self) -> int:
        """Return required lookback period in days"""
        return self.lookback_period
    
    def validate_parameters(self) -> bool:
        """Validate strategy parameters"""
        required_params = ['fast_period', 'slow_period', 'position_size']
        
        for param in required_params:
            if param not in self.parameters:
                self.logger.error(f"Missing required parameter: {param}")
                return False
        
        if self.parameters['fast_period'] >= self.parameters['slow_period']:
            self.logger.error("Fast period must be less than slow period")
            return False
        
        if not (0 < self.parameters['position_size'] <= 1):
            self.logger.error("Position size must be between 0 and 1")
            return False
        
        return True
    
    def get_strategy_info(self) -> Dict:
        """Return strategy information"""
        return {
            'name': self.name,
            'description': 'Simple Moving Average Crossover Strategy',
            'parameters': self.parameters,
            'universe_size': len(self.universe),
            'lookback_period': self.lookback_period,
            'rebalance_frequency': self.rebalance_frequency,
            'strategy_type': 'Trend Following',
            'risk_level': 'Medium',
            'typical_holding_period': '1-3 months'
        }

# Factory function for easy instantiation
def create_moving_average_strategy(fast_period: int = 20, slow_period: int = 50, 
                                 position_size: float = 0.1) -> MovingAverageStrategy:
    """Factory function to create Moving Average strategy with custom parameters"""
    parameters = {
        'fast_period': fast_period,
        'slow_period': slow_period,
        'position_size': position_size
    }
    return MovingAverageStrategy(parameters)