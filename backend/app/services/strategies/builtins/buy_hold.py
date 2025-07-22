"""
Buy and Hold Strategy Implementation
"""

from typing import Dict, List
from datetime import datetime
import pandas as pd
import logging

from ..base_strategy import BaseStrategy, Signal, StrategyContext, EqualWeightSizer

logger = logging.getLogger(__name__)

class BuyHoldStrategy(BaseStrategy):
    """
    Simple Buy and Hold Strategy
    
    Purchases equal weights of all symbols at the beginning and holds them
    throughout the entire period. Optional rebalancing at specified intervals.
    """
    
    def __init__(self, parameters: Dict = None):
        default_params = {
            'rebalance_frequency': 'none',  # none, monthly, quarterly, annually
            'equal_weight': True,  # Equal weight vs market cap weight
            'cash_reserve': 0.0,  # Percentage to keep in cash
            'max_positions': None,  # None for no limit
            'rebalance_threshold': 0.05  # 5% deviation triggers rebalance
        }
        
        if parameters:
            default_params.update(parameters)
        
        super().__init__("Buy and Hold", default_params)
        
        # Set rebalance frequency
        self.rebalance_frequency = self.get_parameter('rebalance_frequency')
        if self.rebalance_frequency == 'none':
            self.rebalance_frequency = 'never'
        
        # Position sizer
        max_positions = self.get_parameter('max_positions')
        if max_positions:
            self.position_sizer = EqualWeightSizer(max_positions)
        
        # Track if initial purchase is done
        self.initial_purchase_done = False
        self.last_rebalance_weights = {}
    
    def initialize(self, universe: List[str], start_date: datetime, end_date: datetime):
        """Initialize strategy"""
        self.universe = universe
        self.start_date = start_date
        self.end_date = end_date
        self.is_initialized = True
        self.initial_purchase_done = False
        self.last_rebalance_weights = {}
        
        # Minimal lookback needed
        self.lookback_period = 30
        
        logger.info(f"Initialized Buy and Hold strategy with {len(universe)} symbols")
        logger.info(f"Rebalance frequency: {self.rebalance_frequency}")
    
    def get_required_data(self) -> Dict[str, List[str]]:
        """Get required data specifications"""
        return {
            'timeframes': ['1d'],
            'indicators': [],  # No technical indicators needed
            'lookback_days': self.lookback_period
        }
    
    def generate_signals(self, context: StrategyContext) -> List[Signal]:
        """Generate buy and hold signals"""
        signals = []
        
        if not self.is_initialized:
            logger.warning("Strategy not initialized")
            return signals
        
        try:
            # Initial purchase
            if not self.initial_purchase_done:
                signals.extend(self._generate_initial_purchase_signals(context))
                self.initial_purchase_done = True
                return signals
            
            # Rebalancing
            if self._should_rebalance(context):
                signals.extend(self._generate_rebalance_signals(context))
            
        except Exception as e:
            logger.error(f"Error generating buy and hold signals: {str(e)}")
        
        return signals
    
    def _generate_initial_purchase_signals(self, context: StrategyContext) -> List[Signal]:
        """Generate initial purchase signals"""
        signals = []
        
        equal_weight = self.get_parameter('equal_weight')
        cash_reserve = self.get_parameter('cash_reserve')
        max_positions = self.get_parameter('max_positions')
        
        # Calculate investable cash
        investable_cash = context.cash_balance * (1 - cash_reserve)
        
        # Determine symbols to invest in
        investable_symbols = self._get_investable_symbols(context)
        
        if max_positions:
            investable_symbols = investable_symbols[:max_positions]
        
        if not investable_symbols:
            logger.warning("No investable symbols found")
            return signals
        
        # Calculate weights
        if equal_weight:
            weight_per_symbol = 1.0 / len(investable_symbols)
            target_weights = {symbol: weight_per_symbol for symbol in investable_symbols}
        else:
            # Market cap weighting (simplified - equal weight as fallback)
            target_weights = self._calculate_market_cap_weights(investable_symbols, context)
        
        # Generate buy signals
        for symbol in investable_symbols:
            try:
                if symbol not in context.market_data:
                    continue
                
                current_price = context.market_data[symbol]['close'].iloc[-1]
                target_value = investable_cash * target_weights[symbol]
                quantity = target_value / current_price
                
                if quantity > 0:
                    signal = Signal(
                        symbol=symbol,
                        signal_type="BUY",
                        strength=1.0,  # Maximum conviction for buy and hold
                        price=current_price,
                        timestamp=context.current_date,
                        quantity=quantity,
                        reason=f"Initial buy and hold purchase (weight: {target_weights[symbol]:.2%})",
                        metadata={
                            'target_weight': target_weights[symbol],
                            'strategy_type': 'initial_purchase'
                        }
                    )
                    signals.append(signal)
                    self.log_signal(signal)
            
            except Exception as e:
                logger.error(f"Error generating initial signal for {symbol}: {str(e)}")
        
        # Store weights for future rebalancing
        self.last_rebalance_weights = target_weights
        
        return signals
    
    def _generate_rebalance_signals(self, context: StrategyContext) -> List[Signal]:
        """Generate rebalancing signals"""
        signals = []
        
        try:
            # Calculate current weights
            current_weights = self._calculate_current_weights(context)
            
            # Calculate target weights
            investable_symbols = self._get_investable_symbols(context)
            target_weights = self._calculate_target_weights(investable_symbols, context)
            
            rebalance_threshold = self.get_parameter('rebalance_threshold')
            
            # Generate rebalance signals
            for symbol in set(list(current_weights.keys()) + list(target_weights.keys())):
                current_weight = current_weights.get(symbol, 0.0)
                target_weight = target_weights.get(symbol, 0.0)
                weight_diff = target_weight - current_weight
                
                # Check if rebalancing is needed
                if abs(weight_diff) > rebalance_threshold:
                    try:
                        if symbol not in context.market_data:
                            continue
                        
                        current_price = context.market_data[symbol]['close'].iloc[-1]
                        target_value = context.portfolio_value * target_weight
                        current_position = context.positions.get(symbol, 0)
                        current_value = current_position * current_price
                        
                        value_diff = target_value - current_value
                        quantity_diff = value_diff / current_price
                        
                        if abs(quantity_diff) > 0.01:  # Minimum trade size
                            signal_type = "BUY" if quantity_diff > 0 else "SELL"
                            
                            signal = Signal(
                                symbol=symbol,
                                signal_type=signal_type,
                                strength=0.8,  # High conviction for rebalancing
                                price=current_price,
                                timestamp=context.current_date,
                                quantity=abs(quantity_diff),
                                reason=f"Rebalance: {current_weight:.2%} → {target_weight:.2%}",
                                metadata={
                                    'current_weight': current_weight,
                                    'target_weight': target_weight,
                                    'weight_diff': weight_diff,
                                    'strategy_type': 'rebalance'
                                }
                            )
                            signals.append(signal)
                            self.log_signal(signal)
                    
                    except Exception as e:
                        logger.error(f"Error generating rebalance signal for {symbol}: {str(e)}")
            
            # Update last rebalance weights
            self.last_rebalance_weights = target_weights
            
        except Exception as e:
            logger.error(f"Error generating rebalance signals: {str(e)}")
        
        return signals
    
    def _should_rebalance(self, context: StrategyContext) -> bool:
        """Check if rebalancing is needed"""
        if self.rebalance_frequency == 'never':
            return False
        
        # Check frequency-based rebalancing
        if self.last_rebalance_date:
            days_since_rebalance = (context.current_date - self.last_rebalance_date).days
            
            if self.rebalance_frequency == 'monthly' and days_since_rebalance >= 30:
                return True
            elif self.rebalance_frequency == 'quarterly' and days_since_rebalance >= 90:
                return True
            elif self.rebalance_frequency == 'annually' and days_since_rebalance >= 365:
                return True
        
        # Check threshold-based rebalancing
        if self.get_parameter('rebalance_threshold') > 0:
            current_weights = self._calculate_current_weights(context)
            target_weights = self.last_rebalance_weights
            
            for symbol in target_weights:
                current_weight = current_weights.get(symbol, 0.0)
                target_weight = target_weights[symbol]
                if abs(current_weight - target_weight) > self.get_parameter('rebalance_threshold'):
                    return True
        
        return False
    
    def _get_investable_symbols(self, context: StrategyContext) -> List[str]:
        """Get symbols that can be invested in"""
        investable = []
        
        for symbol in self.universe:
            if symbol in context.market_data:
                data = context.market_data[symbol]
                if not data.empty and data['close'].iloc[-1] > 0:
                    # Basic liquidity check
                    if len(data) >= 10:
                        avg_volume = data['volume'].tail(10).mean()
                        if avg_volume > 1000:  # Minimum volume threshold
                            investable.append(symbol)
        
        return investable
    
    def _calculate_market_cap_weights(self, symbols: List[str], context: StrategyContext) -> Dict[str, float]:
        """Calculate market cap based weights (simplified equal weight for now)"""
        # In a real implementation, you would fetch market cap data
        # For now, return equal weights
        weight = 1.0 / len(symbols)
        return {symbol: weight for symbol in symbols}
    
    def _calculate_current_weights(self, context: StrategyContext) -> Dict[str, float]:
        """Calculate current portfolio weights"""
        weights = {}
        
        if context.portfolio_value <= 0:
            return weights
        
        for symbol, quantity in context.positions.items():
            if symbol in context.market_data and quantity != 0:
                current_price = context.market_data[symbol]['close'].iloc[-1]
                position_value = abs(quantity) * current_price
                weights[symbol] = position_value / context.portfolio_value
        
        return weights
    
    def _calculate_target_weights(self, symbols: List[str], context: StrategyContext) -> Dict[str, float]:
        """Calculate target weights for rebalancing"""
        if self.get_parameter('equal_weight'):
            weight = 1.0 / len(symbols) if symbols else 0.0
            return {symbol: weight for symbol in symbols}
        else:
            return self._calculate_market_cap_weights(symbols, context)
    
    def should_rebalance(self, current_date: datetime) -> bool:
        """Override parent method for buy and hold specific logic"""
        if not self.initial_purchase_done:
            return True
        
        return super().should_rebalance(current_date)

class BuyHoldWithDividends(BuyHoldStrategy):
    """
    Buy and Hold strategy that reinvests dividends
    """
    
    def __init__(self, parameters: Dict = None):
        default_params = {
            'reinvest_dividends': True,
            'dividend_reinvest_threshold': 100,  # Minimum $ amount to reinvest
        }
        
        if parameters:
            default_params.update(parameters)
        
        super().__init__(default_params)
        self.name = "Buy and Hold with Dividends"
        self.dividend_cash = 0.0
    
    def process_dividend(self, symbol: str, dividend_amount: float, context: StrategyContext):
        """Process dividend payment"""
        if self.get_parameter('reinvest_dividends'):
            self.dividend_cash += dividend_amount
            
            # Reinvest if threshold is met
            threshold = self.get_parameter('dividend_reinvest_threshold')
            if self.dividend_cash >= threshold:
                return self._generate_dividend_reinvestment_signal(symbol, context)
        
        return None
    
    def _generate_dividend_reinvestment_signal(self, symbol: str, context: StrategyContext) -> Signal:
        """Generate signal to reinvest dividends"""
        if symbol not in context.market_data:
            return None
        
        current_price = context.market_data[symbol]['close'].iloc[-1]
        quantity = self.dividend_cash / current_price
        
        signal = Signal(
            symbol=symbol,
            signal_type="BUY",
            strength=1.0,
            price=current_price,
            timestamp=context.current_date,
            quantity=quantity,
            reason=f"Dividend reinvestment: ${self.dividend_cash:.2f}",
            metadata={
                'dividend_amount': self.dividend_cash,
                'strategy_type': 'dividend_reinvestment'
            }
        )
        
        self.dividend_cash = 0.0  # Reset dividend cash
        return signal