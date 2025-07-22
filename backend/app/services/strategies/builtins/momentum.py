"""
Momentum Strategy Implementations
"""

from typing import Dict, List, Tuple
from datetime import datetime
import pandas as pd
import numpy as np
import logging

from ..base_strategy import BaseStrategy, Signal, StrategyContext, EqualWeightSizer

logger = logging.getLogger(__name__)

class MomentumStrategy(BaseStrategy):
    """
    Price Momentum Strategy
    
    Buys assets with strong recent performance and sells those with weak performance.
    Uses multiple timeframes for momentum calculation.
    """
    
    def __init__(self, parameters: Dict = None):
        default_params = {
            'momentum_periods': [21, 63, 126],  # 1, 3, 6 months
            'momentum_weights': [0.5, 0.3, 0.2],  # Weights for each period
            'top_percentile': 0.2,  # Top 20% for long positions
            'bottom_percentile': 0.2,  # Bottom 20% for short positions
            'min_momentum_threshold': 0.05,  # 5% minimum momentum
            'max_positions': 10,
            'rebalance_frequency': 'monthly',
            'volatility_adjustment': True,
            'sector_neutral': False,
            'skip_threshold': 0.01  # Skip if momentum change < 1%
        }
        
        if parameters:
            default_params.update(parameters)
        
        super().__init__("Momentum Strategy", default_params)
        self.position_sizer = EqualWeightSizer(self.get_parameter('max_positions'))
        self.rebalance_frequency = self.get_parameter('rebalance_frequency')
        
        # Momentum tracking
        self.last_momentum_scores = {}
        self.last_rankings = {}
    
    def initialize(self, universe: List[str], start_date: datetime, end_date: datetime):
        """Initialize strategy"""
        self.universe = universe
        self.start_date = start_date
        self.end_date = end_date
        self.is_initialized = True
        
        # Set lookback period to accommodate longest momentum period
        max_period = max(self.get_parameter('momentum_periods'))
        self.lookback_period = max_period + 50  # Extra buffer
        
        logger.info(f"Initialized Momentum strategy with {len(universe)} symbols")
        logger.info(f"Momentum periods: {self.get_parameter('momentum_periods')}")
    
    def get_required_data(self) -> Dict[str, List[str]]:
        """Get required data specifications"""
        return {
            'timeframes': ['1d'],
            'indicators': ['volatility'],
            'lookback_days': self.lookback_period
        }
    
    def generate_signals(self, context: StrategyContext) -> List[Signal]:
        """Generate momentum-based signals"""
        signals = []
        
        if not self.is_initialized:
            return signals
        
        try:
            # Calculate momentum scores for all symbols
            momentum_scores = self._calculate_momentum_scores(context)
            
            if not momentum_scores:
                return signals
            
            # Rank symbols by momentum
            ranked_symbols = self._rank_symbols_by_momentum(momentum_scores)
            
            # Generate position signals
            signals.extend(self._generate_position_signals(ranked_symbols, context))
            
            # Store current rankings for next period
            self.last_momentum_scores = momentum_scores
            self.last_rankings = {symbol: rank for rank, (symbol, _) in enumerate(ranked_symbols)}
            
        except Exception as e:
            logger.error(f"Error generating momentum signals: {str(e)}")
        
        return signals
    
    def _calculate_momentum_scores(self, context: StrategyContext) -> Dict[str, float]:
        """Calculate momentum scores for all symbols"""
        momentum_scores = {}
        
        periods = self.get_parameter('momentum_periods')
        weights = self.get_parameter('momentum_weights')
        volatility_adjustment = self.get_parameter('volatility_adjustment')
        
        for symbol in self.universe:
            try:
                if symbol not in context.market_data:
                    continue
                
                data = context.market_data[symbol]
                if len(data) < max(periods) + 1:
                    continue
                
                # Calculate momentum for each period
                momentum_components = []
                for period, weight in zip(periods, weights):
                    momentum = self._calculate_period_momentum(data, period)
                    
                    if volatility_adjustment:
                        volatility = self._calculate_volatility(data, period)
                        if volatility > 0:
                            momentum = momentum / volatility
                    
                    momentum_components.append(momentum * weight)
                
                # Weighted average momentum score
                total_momentum = sum(momentum_components)
                momentum_scores[symbol] = total_momentum
                
            except Exception as e:
                logger.error(f"Error calculating momentum for {symbol}: {str(e)}")
                continue
        
        return momentum_scores
    
    def _calculate_period_momentum(self, data: pd.DataFrame, period: int) -> float:
        """Calculate momentum for a specific period"""
        if len(data) < period + 1:
            return 0.0
        
        current_price = data['close'].iloc[-1]
        past_price = data['close'].iloc[-period-1]
        
        if past_price <= 0:
            return 0.0
        
        return (current_price / past_price) - 1
    
    def _calculate_volatility(self, data: pd.DataFrame, period: int) -> float:
        """Calculate volatility for risk adjustment"""
        if len(data) < period:
            return 0.0
        
        returns = data['close'].pct_change().dropna()
        if len(returns) < period:
            return 0.0
        
        return returns.tail(period).std() * np.sqrt(252)  # Annualized
    
    def _rank_symbols_by_momentum(self, momentum_scores: Dict[str, float]) -> List[Tuple[str, float]]:
        """Rank symbols by momentum score"""
        return sorted(momentum_scores.items(), key=lambda x: x[1], reverse=True)
    
    def _generate_position_signals(self, ranked_symbols: List[Tuple[str, float]], 
                                 context: StrategyContext) -> List[Signal]:
        """Generate position signals based on momentum rankings"""
        signals = []
        
        if not ranked_symbols:
            return signals
        
        top_percentile = self.get_parameter('top_percentile')
        bottom_percentile = self.get_parameter('bottom_percentile')
        min_momentum = self.get_parameter('min_momentum_threshold')
        max_positions = self.get_parameter('max_positions')
        skip_threshold = self.get_parameter('skip_threshold')
        
        total_symbols = len(ranked_symbols)
        
        # Calculate number of long and short positions
        num_long = min(int(total_symbols * top_percentile), max_positions // 2)
        num_short = min(int(total_symbols * bottom_percentile), max_positions // 2)
        
        # Generate long signals (top momentum)
        for i in range(num_long):
            symbol, momentum_score = ranked_symbols[i]
            
            if momentum_score < min_momentum:
                continue
            
            # Check if we should skip this signal
            if self._should_skip_signal(symbol, momentum_score, skip_threshold):
                continue
            
            signal = self._create_momentum_signal(
                symbol, "BUY", momentum_score, context, 
                f"Top momentum rank {i+1}/{total_symbols}"
            )
            
            if signal:
                signals.append(signal)
        
        # Generate short signals (bottom momentum) if enabled
        if self._shorts_enabled():
            start_idx = total_symbols - num_short
            for i in range(start_idx, total_symbols):
                symbol, momentum_score = ranked_symbols[i]
                
                if momentum_score > -min_momentum:
                    continue
                
                if self._should_skip_signal(symbol, momentum_score, skip_threshold):
                    continue
                
                signal = self._create_momentum_signal(
                    symbol, "SELL", momentum_score, context,
                    f"Bottom momentum rank {i+1}/{total_symbols}"
                )
                
                if signal:
                    signals.append(signal)
        
        # Generate exit signals for existing positions not in target list
        exit_signals = self._generate_exit_signals(ranked_symbols, context)
        signals.extend(exit_signals)
        
        return signals
    
    def _should_skip_signal(self, symbol: str, current_momentum: float, skip_threshold: float) -> bool:
        """Check if signal should be skipped due to minimal change"""
        if symbol not in self.last_momentum_scores:
            return False
        
        last_momentum = self.last_momentum_scores[symbol]
        momentum_change = abs(current_momentum - last_momentum)
        
        return momentum_change < skip_threshold
    
    def _create_momentum_signal(self, symbol: str, signal_type: str, momentum_score: float,
                              context: StrategyContext, reason: str) -> Signal:
        """Create momentum signal"""
        try:
            if symbol not in context.market_data:
                return None
            
            current_price = context.market_data[symbol]['close'].iloc[-1]
            
            # Calculate signal strength based on momentum magnitude
            strength = min(1.0, abs(momentum_score) / 0.5)  # Max strength at 50% momentum
            strength = max(0.5, strength)  # Minimum 50% strength
            
            # Calculate position size
            signal = Signal(
                symbol=symbol,
                signal_type=signal_type,
                strength=strength,
                price=current_price,
                timestamp=context.current_date,
                reason=reason,
                metadata={
                    'momentum_score': momentum_score,
                    'strategy_type': 'momentum',
                    'signal_strength_raw': abs(momentum_score)
                }
            )
            
            # Calculate quantity
            signal.quantity = self.calculate_position_size(signal, context)
            
            if signal.quantity > 0:
                self.log_signal(signal)
                return signal
        
        except Exception as e:
            logger.error(f"Error creating momentum signal for {symbol}: {str(e)}")
        
        return None
    
    def _generate_exit_signals(self, target_symbols: List[Tuple[str, float]], 
                             context: StrategyContext) -> List[Signal]:
        """Generate exit signals for positions not in target list"""
        signals = []
        target_symbol_set = {symbol for symbol, _ in target_symbols}
        
        for symbol, position in context.positions.items():
            if symbol not in target_symbol_set and position != 0:
                try:
                    if symbol not in context.market_data:
                        continue
                    
                    current_price = context.market_data[symbol]['close'].iloc[-1]
                    signal_type = "SELL" if position > 0 else "BUY"
                    
                    signal = Signal(
                        symbol=symbol,
                        signal_type=signal_type,
                        strength=0.8,
                        price=current_price,
                        timestamp=context.current_date,
                        quantity=abs(position),
                        reason="Exit: No longer in momentum target list",
                        metadata={
                            'strategy_type': 'momentum_exit',
                            'exit_reason': 'not_in_target_list'
                        }
                    )
                    
                    signals.append(signal)
                    self.log_signal(signal)
                
                except Exception as e:
                    logger.error(f"Error creating exit signal for {symbol}: {str(e)}")
        
        return signals
    
    def _shorts_enabled(self) -> bool:
        """Check if short selling is enabled"""
        return self.get_parameter('bottom_percentile', 0) > 0

class RelativeStrengthStrategy(BaseStrategy):
    """
    Relative Strength Strategy
    
    Compares price performance relative to a benchmark or peer group.
    Goes long on outperforming assets and short on underperforming ones.
    """
    
    def __init__(self, parameters: Dict = None):
        default_params = {
            'lookback_period': 126,  # 6 months
            'benchmark_symbol': 'SPY',
            'relative_strength_threshold': 0.05,  # 5% outperformance
            'max_positions': 8,
            'rebalance_frequency': 'monthly',
            'use_peer_relative': True,  # Compare to peer average vs benchmark
            'min_relative_strength': 0.02  # 2% minimum relative strength
        }
        
        if parameters:
            default_params.update(parameters)
        
        super().__init__("Relative Strength", default_params)
        self.position_sizer = EqualWeightSizer(self.get_parameter('max_positions'))
        self.rebalance_frequency = self.get_parameter('rebalance_frequency')
    
    def initialize(self, universe: List[str], start_date: datetime, end_date: datetime):
        """Initialize strategy"""
        self.universe = universe
        self.start_date = start_date
        self.end_date = end_date
        self.is_initialized = True
        
        self.lookback_period = self.get_parameter('lookback_period') + 50
        
        logger.info(f"Initialized Relative Strength strategy with {len(universe)} symbols")
    
    def get_required_data(self) -> Dict[str, List[str]]:
        """Get required data specifications"""
        required_symbols = self.universe.copy()
        benchmark = self.get_parameter('benchmark_symbol')
        if benchmark and benchmark not in required_symbols:
            required_symbols.append(benchmark)
        
        return {
            'timeframes': ['1d'],
            'symbols': required_symbols,
            'lookback_days': self.lookback_period
        }
    
    def generate_signals(self, context: StrategyContext) -> List[Signal]:
        """Generate relative strength signals"""
        signals = []
        
        if not self.is_initialized:
            return signals
        
        try:
            # Calculate relative strength scores
            rs_scores = self._calculate_relative_strength_scores(context)
            
            if not rs_scores:
                return signals
            
            # Generate signals based on relative strength
            signals.extend(self._generate_relative_strength_signals(rs_scores, context))
            
        except Exception as e:
            logger.error(f"Error generating relative strength signals: {str(e)}")
        
        return signals
    
    def _calculate_relative_strength_scores(self, context: StrategyContext) -> Dict[str, float]:
        """Calculate relative strength scores"""
        rs_scores = {}
        lookback = self.get_parameter('lookback_period')
        benchmark_symbol = self.get_parameter('benchmark_symbol')
        use_peer_relative = self.get_parameter('use_peer_relative')
        
        # Get benchmark performance
        benchmark_return = 0.0
        if benchmark_symbol and benchmark_symbol in context.market_data:
            benchmark_data = context.market_data[benchmark_symbol]
            if len(benchmark_data) > lookback:
                benchmark_return = self._calculate_return(benchmark_data, lookback)
        
        # Calculate peer average if using peer relative
        peer_returns = []
        if use_peer_relative:
            for symbol in self.universe:
                if symbol in context.market_data:
                    data = context.market_data[symbol]
                    if len(data) > lookback:
                        symbol_return = self._calculate_return(data, lookback)
                        peer_returns.append(symbol_return)
            
            peer_average = np.mean(peer_returns) if peer_returns else 0.0
        else:
            peer_average = benchmark_return
        
        # Calculate relative strength for each symbol
        for symbol in self.universe:
            try:
                if symbol not in context.market_data:
                    continue
                
                data = context.market_data[symbol]
                if len(data) <= lookback:
                    continue
                
                symbol_return = self._calculate_return(data, lookback)
                
                # Calculate relative strength
                if use_peer_relative:
                    rs_score = symbol_return - peer_average
                else:
                    rs_score = symbol_return - benchmark_return
                
                rs_scores[symbol] = rs_score
                
            except Exception as e:
                logger.error(f"Error calculating relative strength for {symbol}: {str(e)}")
        
        return rs_scores
    
    def _calculate_return(self, data: pd.DataFrame, period: int) -> float:
        """Calculate return over specified period"""
        if len(data) <= period:
            return 0.0
        
        current_price = data['close'].iloc[-1]
        past_price = data['close'].iloc[-period-1]
        
        if past_price <= 0:
            return 0.0
        
        return (current_price / past_price) - 1
    
    def _generate_relative_strength_signals(self, rs_scores: Dict[str, float], 
                                          context: StrategyContext) -> List[Signal]:
        """Generate signals based on relative strength"""
        signals = []
        
        rs_threshold = self.get_parameter('relative_strength_threshold')
        min_rs = self.get_parameter('min_relative_strength')
        max_positions = self.get_parameter('max_positions')
        
        # Sort by relative strength
        sorted_rs = sorted(rs_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Generate long signals for top performers
        long_candidates = [(symbol, score) for symbol, score in sorted_rs 
                          if score > max(rs_threshold, min_rs)]
        
        for i, (symbol, rs_score) in enumerate(long_candidates[:max_positions//2]):
            signal = self._create_rs_signal(symbol, "BUY", rs_score, context,
                                          f"Relative strength outperformer: {rs_score:.2%}")
            if signal:
                signals.append(signal)
        
        # Generate short signals for bottom performers (if enabled)
        short_candidates = [(symbol, score) for symbol, score in sorted_rs 
                           if score < -max(rs_threshold, min_rs)]
        
        for i, (symbol, rs_score) in enumerate(short_candidates[-max_positions//2:]):
            signal = self._create_rs_signal(symbol, "SELL", rs_score, context,
                                          f"Relative strength underperformer: {rs_score:.2%}")
            if signal:
                signals.append(signal)
        
        return signals
    
    def _create_rs_signal(self, symbol: str, signal_type: str, rs_score: float,
                         context: StrategyContext, reason: str) -> Signal:
        """Create relative strength signal"""
        try:
            if symbol not in context.market_data:
                return None
            
            current_price = context.market_data[symbol]['close'].iloc[-1]
            
            # Signal strength based on magnitude of relative strength
            strength = min(1.0, abs(rs_score) / 0.2)  # Max strength at 20% relative performance
            strength = max(0.6, strength)
            
            signal = Signal(
                symbol=symbol,
                signal_type=signal_type,
                strength=strength,
                price=current_price,
                timestamp=context.current_date,
                reason=reason,
                metadata={
                    'relative_strength_score': rs_score,
                    'strategy_type': 'relative_strength'
                }
            )
            
            signal.quantity = self.calculate_position_size(signal, context)
            
            if signal.quantity > 0:
                self.log_signal(signal)
                return signal
        
        except Exception as e:
            logger.error(f"Error creating RS signal for {symbol}: {str(e)}")
        
        return None

class MeanReversionMomentumStrategy(BaseStrategy):
    """
    Combined Mean Reversion and Momentum Strategy
    
    Uses short-term mean reversion and long-term momentum signals.
    Short-term reversals with long-term trend confirmation.
    """
    
    def __init__(self, parameters: Dict = None):
        default_params = {
            'short_term_period': 5,   # For mean reversion
            'long_term_period': 63,   # For momentum
            'momentum_threshold': 0.1,  # 10% long-term momentum required
            'reversion_threshold': 0.03,  # 3% short-term reversion
            'rsi_period': 14,
            'rsi_oversold': 30,
            'rsi_overbought': 70,
            'max_positions': 6,
            'rebalance_frequency': 'weekly'
        }
        
        if parameters:
            default_params.update(parameters)
        
        super().__init__("Mean Reversion Momentum", default_params)
        self.position_sizer = EqualWeightSizer(self.get_parameter('max_positions'))
        self.rebalance_frequency = self.get_parameter('rebalance_frequency')
    
    def initialize(self, universe: List[str], start_date: datetime, end_date: datetime):
        """Initialize strategy"""
        self.universe = universe
        self.start_date = start_date
        self.end_date = end_date
        self.is_initialized = True
        
        long_period = self.get_parameter('long_term_period')
        self.lookback_period = long_period + 50
        
        logger.info(f"Initialized Mean Reversion Momentum strategy with {len(universe)} symbols")
    
    def get_required_data(self) -> Dict[str, List[str]]:
        """Get required data specifications"""
        return {
            'timeframes': ['1d'],
            'indicators': ['rsi'],
            'lookback_days': self.lookback_period
        }
    
    def generate_signals(self, context: StrategyContext) -> List[Signal]:
        """Generate combined mean reversion and momentum signals"""
        signals = []
        
        if not self.is_initialized:
            return signals
        
        try:
            for symbol in self.universe:
                if symbol not in context.market_data:
                    continue
                
                data = context.market_data[symbol]
                long_period = self.get_parameter('long_term_period')
                
                if len(data) <= long_period:
                    continue
                
                # Calculate indicators
                long_term_momentum = self._calculate_period_momentum(data, long_period)
                short_term_momentum = self._calculate_period_momentum(data, self.get_parameter('short_term_period'))
                rsi = self._calculate_rsi(data['close'], self.get_parameter('rsi_period')).iloc[-1]
                
                # Generate signals based on combined conditions
                signal = self._evaluate_combined_signal(
                    symbol, data, long_term_momentum, short_term_momentum, rsi, context
                )
                
                if signal:
                    signals.append(signal)
        
        except Exception as e:
            logger.error(f"Error generating combined signals: {str(e)}")
        
        return signals
    
    def _evaluate_combined_signal(self, symbol: str, data: pd.DataFrame, 
                                 long_momentum: float, short_momentum: float, 
                                 rsi: float, context: StrategyContext) -> Signal:
        """Evaluate combined signal conditions"""
        momentum_threshold = self.get_parameter('momentum_threshold')
        reversion_threshold = self.get_parameter('reversion_threshold')
        rsi_oversold = self.get_parameter('rsi_oversold')
        rsi_overbought = self.get_parameter('rsi_overbought')
        
        current_price = data['close'].iloc[-1]
        signal_type = None
        reason = ""
        strength = 0.0
        
        # Long signal: Strong long-term momentum + short-term pullback + oversold RSI
        if (long_momentum > momentum_threshold and 
            short_momentum < -reversion_threshold and 
            rsi < rsi_oversold):
            
            signal_type = "BUY"
            reason = f"Long momentum + pullback: LT={long_momentum:.2%}, ST={short_momentum:.2%}, RSI={rsi:.1f}"
            strength = 0.8
        
        # Short signal: Strong negative long-term momentum + short-term bounce + overbought RSI
        elif (long_momentum < -momentum_threshold and 
              short_momentum > reversion_threshold and 
              rsi > rsi_overbought):
            
            signal_type = "SELL"
            reason = f"Short momentum + bounce: LT={long_momentum:.2%}, ST={short_momentum:.2%}, RSI={rsi:.1f}"
            strength = 0.8
        
        if signal_type:
            signal = Signal(
                symbol=symbol,
                signal_type=signal_type,
                strength=strength,
                price=current_price,
                timestamp=context.current_date,
                reason=reason,
                metadata={
                    'long_term_momentum': long_momentum,
                    'short_term_momentum': short_momentum,
                    'rsi': rsi,
                    'strategy_type': 'mean_reversion_momentum'
                }
            )
            
            signal.quantity = self.calculate_position_size(signal, context)
            
            if signal.quantity > 0:
                self.log_signal(signal)
                return signal
        
        return None
    
    def _calculate_period_momentum(self, data: pd.DataFrame, period: int) -> float:
        """Calculate momentum for a specific period"""
        if len(data) < period + 1:
            return 0.0
        
        current_price = data['close'].iloc[-1]
        past_price = data['close'].iloc[-period-1]
        
        if past_price <= 0:
            return 0.0
        
        return (current_price / past_price) - 1
    
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