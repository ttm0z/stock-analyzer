"""
Main backtesting engine for executing strategy backtests.
"""

import logging
from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
import pandas as pd
from dataclasses import dataclass, field
import numpy as np

from ..strategies.base_strategy import BaseStrategy, Signal, StrategyContext
from .portfolio_manager import PortfolioManager
from .order_manager import OrderManager, Order
from .execution_engine import ExecutionEngine
from ..data.data_provider import DataProvider, DataRequest

logger = logging.getLogger(__name__)

@dataclass
class BacktestConfig:
    """Backtesting configuration"""
    start_date: datetime
    end_date: datetime
    initial_capital: float
    universe: List[str]
    data_frequency: str = '1d'
    commission_rate: float = 0.001  # 0.1%
    slippage_rate: float = 0.0005   # 0.05%
    benchmark_symbol: str = 'SPY'
    currency: str = 'USD'
    
    # Risk management
    max_position_size: float = 0.1  # 10% of portfolio
    max_portfolio_risk: float = 0.02  # 2% max risk per trade
    
    # Execution settings
    execution_delay: int = 0  # Days delay for signal execution
    market_impact: bool = True
    
    # Data settings
    adjust_for_splits: bool = True
    adjust_for_dividends: bool = True

@dataclass
class BacktestResults:
    """Backtesting results container"""
    config: BacktestConfig
    strategy_name: str
    
    # Performance metrics
    total_return: float = 0.0
    annualized_return: float = 0.0
    volatility: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    
    # Trade statistics
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    profit_factor: float = 0.0
    
    # Time series data
    equity_curve: pd.Series = field(default_factory=pd.Series)
    drawdown_series: pd.Series = field(default_factory=pd.Series)
    returns_series: pd.Series = field(default_factory=pd.Series)
    
    # Detailed records
    trades: List[Dict] = field(default_factory=list)
    signals: List[Dict] = field(default_factory=list)
    portfolio_snapshots: List[Dict] = field(default_factory=list)
    
    # Benchmark comparison
    benchmark_return: float = 0.0
    alpha: float = 0.0
    beta: float = 0.0
    
    # Execution metadata
    execution_time: float = 0.0
    start_time: datetime = field(default_factory=datetime.now)
    end_time: datetime = field(default_factory=datetime.now)
    
    # Errors and warnings
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

class BacktestingEngine:
    """Main backtesting engine"""
    
    def __init__(self, data_provider: DataProvider):
        self.data_provider = data_provider
        self.portfolio_manager = None
        self.order_manager = None
        self.execution_engine = None
        
        # Progress tracking
        self.progress_callback: Optional[Callable[[float], None]] = None
        self.is_running = False
        self.should_stop = False
        
        # Cache for market data
        self.market_data_cache = {}
        
    def run_backtest(self, strategy: BaseStrategy, config: BacktestConfig) -> BacktestResults:
        """Run a complete backtest"""
        logger.info(f"Starting backtest for strategy '{strategy.name}'")
        logger.info(f"Period: {config.start_date} to {config.end_date}")
        logger.info(f"Universe: {len(config.universe)} symbols")
        
        start_time = datetime.now()
        results = BacktestResults(
            config=config,
            strategy_name=strategy.name,
            start_time=start_time
        )
        
        try:
            self.is_running = True
            self.should_stop = False
            
            # Initialize components
            self._initialize_components(config)
            
            # Initialize strategy
            strategy.initialize(config.universe, config.start_date, config.end_date)
            
            # Load market data
            self._load_market_data(config)
            
            # Run the backtest simulation
            self._run_simulation(strategy, config, results)
            
            # Calculate final performance metrics
            self._calculate_performance_metrics(results, config)
            
            # Load benchmark data and calculate relative metrics
            self._calculate_benchmark_metrics(results, config)
            
            logger.info(f"Backtest completed successfully")
            logger.info(f"Total Return: {results.total_return:.2%}")
            logger.info(f"Sharpe Ratio: {results.sharpe_ratio:.2f}")
            logger.info(f"Max Drawdown: {results.max_drawdown:.2%}")
            logger.info(f"Total Trades: {results.total_trades}")
            
        except Exception as e:
            logger.error(f"Backtest failed: {str(e)}")
            results.errors.append(f"Backtest failed: {str(e)}")
            raise
        
        finally:
            self.is_running = False
            end_time = datetime.now()
            results.end_time = end_time
            results.execution_time = (end_time - start_time).total_seconds()
        
        return results
    
    def _initialize_components(self, config: BacktestConfig):
        """Initialize backtesting components"""
        self.portfolio_manager = PortfolioManager(
            initial_capital=config.initial_capital,
            currency=config.currency
        )
        
        self.order_manager = OrderManager(
            commission_rate=config.commission_rate,
            slippage_rate=config.slippage_rate
        )
        
        self.execution_engine = ExecutionEngine(
            portfolio_manager=self.portfolio_manager,
            order_manager=self.order_manager,
            execution_delay=config.execution_delay,
            market_impact=config.market_impact
        )
    
    def _load_market_data(self, config: BacktestConfig):
        """Load market data for all symbols"""
        logger.info("Loading market data...")
        
        # Add some buffer for indicators
        buffer_days = 252  # 1 year buffer
        start_date = config.start_date - timedelta(days=buffer_days)
        
        request = DataRequest(
            symbols=config.universe + [config.benchmark_symbol],
            start_date=start_date,
            end_date=config.end_date,
            timeframe=config.data_frequency,
            adjust_for_splits=config.adjust_for_splits,
            adjust_for_dividends=config.adjust_for_dividends
        )
        
        response = self.data_provider.get_historical_data(request)
        
        if response.errors:
            logger.warning(f"Data loading errors: {response.errors}")
        
        if response.missing_symbols:
            logger.warning(f"Missing data for symbols: {response.missing_symbols}")
        
        # Organize data by symbol
        if not response.data.empty:
            for symbol in response.data['symbol'].unique():
                symbol_data = response.data[response.data['symbol'] == symbol].copy()
                symbol_data = symbol_data.drop('symbol', axis=1)
                symbol_data = symbol_data.sort_index()
                self.market_data_cache[symbol] = symbol_data
        
        logger.info(f"Loaded data for {len(self.market_data_cache)} symbols")
    
    def _run_simulation(self, strategy: BaseStrategy, config: BacktestConfig, results: BacktestResults):
        """Run the main simulation loop"""
        logger.info("Running simulation...")
        
        # Get trading dates
        trading_dates = self._get_trading_dates(config)
        total_days = len(trading_dates)
        
        for i, current_date in enumerate(trading_dates):
            if self.should_stop:
                break
            
            try:
                # Update progress
                progress = (i + 1) / total_days * 100
                if self.progress_callback:
                    self.progress_callback(progress)
                
                # Update portfolio with current prices
                self._update_portfolio_prices(current_date)
                
                # Create strategy context
                context = self._create_strategy_context(current_date, strategy)
                
                # Generate signals
                if strategy.should_rebalance(current_date):
                    signals = strategy.generate_signals(context)
                    
                    # Process signals
                    for signal in signals:
                        self._process_signal(signal, current_date, results)
                
                # Execute pending orders
                self.execution_engine.execute_orders(current_date, self.market_data_cache)
                
                # Record portfolio snapshot
                self._record_portfolio_snapshot(current_date, results)
                
                if i % 50 == 0:  # Log progress every 50 days
                    logger.debug(f"Processed {i+1}/{total_days} days ({progress:.1f}%)")
            
            except Exception as e:
                logger.error(f"Error on {current_date}: {str(e)}")
                results.warnings.append(f"Error on {current_date}: {str(e)}")
                continue
    
    def _get_trading_dates(self, config: BacktestConfig) -> List[datetime]:
        """Get list of trading dates"""
        # For simplicity, use business days. In production, you'd use market calendar
        dates = pd.bdate_range(start=config.start_date, end=config.end_date)
        return dates.tolist()
    
    def _update_portfolio_prices(self, current_date: datetime):
        """Update portfolio with current market prices"""
        current_prices = {}
        
        for symbol in self.portfolio_manager.get_positions():
            if symbol in self.market_data_cache:
                symbol_data = self.market_data_cache[symbol]
                # Find the closest date
                available_dates = symbol_data.index
                closest_date = available_dates[available_dates <= current_date]
                
                if len(closest_date) > 0:
                    price_date = closest_date[-1]
                    current_prices[symbol] = symbol_data.loc[price_date, 'close']
        
        self.portfolio_manager.update_prices(current_prices, current_date)
    
    def _create_strategy_context(self, current_date: datetime, strategy: BaseStrategy) -> StrategyContext:
        """Create strategy context for current date"""
        # Get market data up to current date
        context_market_data = {}
        
        for symbol in strategy.universe:
            if symbol in self.market_data_cache:
                symbol_data = self.market_data_cache[symbol]
                # Only include data up to current date
                available_data = symbol_data[symbol_data.index <= current_date]
                if not available_data.empty:
                    context_market_data[symbol] = available_data
        
        # Get portfolio state
        portfolio_value = self.portfolio_manager.get_total_value()
        cash_balance = self.portfolio_manager.get_cash_balance()
        positions = self.portfolio_manager.get_positions()
        
        return StrategyContext(
            current_date=current_date,
            portfolio_value=portfolio_value,
            cash_balance=cash_balance,
            positions=positions,
            market_data=context_market_data
        )
    
    def _process_signal(self, signal: Signal, current_date: datetime, results: BacktestResults):
        """Process a trading signal"""
        try:
            # Record signal
            signal_record = {
                'date': current_date,
                'symbol': signal.symbol,
                'signal_type': signal.signal_type,
                'price': signal.price,
                'quantity': signal.quantity,
                'strength': signal.strength,
                'reason': signal.reason
            }
            results.signals.append(signal_record)
            
            # Convert signal to order
            if signal.signal_type in ['BUY', 'SELL']:
                order = Order(
                    symbol=signal.symbol,
                    order_type='MARKET',
                    side=signal.signal_type,
                    quantity=abs(signal.quantity),
                    timestamp=current_date,
                    metadata={'signal_strength': signal.strength, 'signal_reason': signal.reason}
                )
                
                # Submit order
                self.order_manager.submit_order(order)
                
        except Exception as e:
            logger.error(f"Error processing signal: {str(e)}")
            results.warnings.append(f"Error processing signal for {signal.symbol}: {str(e)}")
    
    def _record_portfolio_snapshot(self, current_date: datetime, results: BacktestResults):
        """Record portfolio snapshot"""
        portfolio_value = self.portfolio_manager.get_total_value()
        cash_balance = self.portfolio_manager.get_cash_balance()
        positions = self.portfolio_manager.get_positions()
        
        snapshot = {
            'date': current_date,
            'portfolio_value': portfolio_value,
            'cash_balance': cash_balance,
            'invested_value': portfolio_value - cash_balance,
            'num_positions': len(positions),
            'positions': positions.copy()
        }
        
        results.portfolio_snapshots.append(snapshot)
    
    def _calculate_performance_metrics(self, results: BacktestResults, config: BacktestConfig):
        """Calculate performance metrics from portfolio snapshots"""
        if not results.portfolio_snapshots:
            return
        
        # Create equity curve
        dates = [snap['date'] for snap in results.portfolio_snapshots]
        values = [snap['portfolio_value'] for snap in results.portfolio_snapshots]
        
        results.equity_curve = pd.Series(values, index=dates)
        
        # Calculate returns
        returns = results.equity_curve.pct_change().dropna()
        results.returns_series = returns
        
        if len(returns) == 0:
            return
        
        # Basic performance metrics
        total_return = (results.equity_curve.iloc[-1] / config.initial_capital) - 1
        results.total_return = total_return
        
        # Annualized return
        days = (config.end_date - config.start_date).days
        years = days / 365.25
        results.annualized_return = (1 + total_return) ** (1 / years) - 1 if years > 0 else 0
        
        # Volatility (annualized)
        results.volatility = returns.std() * np.sqrt(252) if len(returns) > 1 else 0
        
        # Sharpe ratio (assuming 0% risk-free rate)
        results.sharpe_ratio = results.annualized_return / results.volatility if results.volatility > 0 else 0
        
        # Maximum drawdown
        running_max = results.equity_curve.expanding().max()
        drawdown = (results.equity_curve - running_max) / running_max
        results.drawdown_series = drawdown
        results.max_drawdown = drawdown.min()
        
        # Trade statistics
        trades = self.execution_engine.get_completed_trades()
        results.trades = trades
        results.total_trades = len(trades)
        
        if trades:
            winning_trades = [t for t in trades if t['pnl'] > 0]
            losing_trades = [t for t in trades if t['pnl'] < 0]
            
            results.winning_trades = len(winning_trades)
            results.losing_trades = len(losing_trades)
            results.win_rate = len(winning_trades) / len(trades) if trades else 0
            
            if winning_trades:
                results.avg_win = np.mean([t['pnl'] for t in winning_trades])
            if losing_trades:
                results.avg_loss = np.mean([t['pnl'] for t in losing_trades])
                
            # Profit factor
            gross_profit = sum(t['pnl'] for t in winning_trades)
            gross_loss = abs(sum(t['pnl'] for t in losing_trades))
            results.profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
    
    def _calculate_benchmark_metrics(self, results: BacktestResults, config: BacktestConfig):
        """Calculate benchmark comparison metrics"""
        try:
            benchmark_symbol = config.benchmark_symbol
            if benchmark_symbol not in self.market_data_cache:
                logger.warning(f"Benchmark data not available for {benchmark_symbol}")
                return
            
            benchmark_data = self.market_data_cache[benchmark_symbol]
            
            # Filter benchmark data to backtest period
            mask = (benchmark_data.index >= config.start_date) & (benchmark_data.index <= config.end_date)
            benchmark_data = benchmark_data[mask]
            
            if benchmark_data.empty:
                return
            
            # Calculate benchmark return
            benchmark_start = benchmark_data['close'].iloc[0]
            benchmark_end = benchmark_data['close'].iloc[-1]
            results.benchmark_return = (benchmark_end / benchmark_start) - 1
            
            # Calculate beta and alpha
            benchmark_returns = benchmark_data['close'].pct_change().dropna()
            
            # Align returns with strategy returns
            common_dates = results.returns_series.index.intersection(benchmark_returns.index)
            if len(common_dates) > 10:  # Need sufficient data points
                strategy_aligned = results.returns_series.reindex(common_dates)
                benchmark_aligned = benchmark_returns.reindex(common_dates)
                
                # Calculate beta
                covariance = strategy_aligned.cov(benchmark_aligned)
                benchmark_variance = benchmark_aligned.var()
                results.beta = covariance / benchmark_variance if benchmark_variance > 0 else 0
                
                # Calculate alpha (annualized excess return)
                results.alpha = results.annualized_return - (results.beta * (results.benchmark_return * (252 / len(benchmark_aligned))))
        
        except Exception as e:
            logger.error(f"Error calculating benchmark metrics: {str(e)}")
            results.warnings.append(f"Benchmark calculation error: {str(e)}")
    
    def stop_backtest(self):
        """Stop the running backtest"""
        self.should_stop = True
        logger.info("Backtest stop requested")
    
    def set_progress_callback(self, callback: Callable[[float], None]):
        """Set progress callback function"""
        self.progress_callback = callback
    
    def get_status(self) -> Dict:
        """Get current backtest status"""
        return {
            'is_running': self.is_running,
            'should_stop': self.should_stop,
            'portfolio_value': self.portfolio_manager.get_total_value() if self.portfolio_manager else 0,
            'cash_balance': self.portfolio_manager.get_cash_balance() if self.portfolio_manager else 0,
            'num_positions': len(self.portfolio_manager.get_positions()) if self.portfolio_manager else 0
        }

class BacktestOptimizer:
    """Optimizer for strategy parameters"""
    
    def __init__(self, engine: BacktestingEngine):
        self.engine = engine
    
    def optimize_parameters(self, strategy_class, base_config: BacktestConfig, 
                          parameter_ranges: Dict, optimization_metric: str = 'sharpe_ratio',
                          max_iterations: int = 100) -> Dict:
        """
        Optimize strategy parameters using grid search
        
        Args:
            strategy_class: Strategy class to optimize
            base_config: Base backtest configuration
            parameter_ranges: Dict of parameter names to ranges/values to test
            optimization_metric: Metric to optimize ('sharpe_ratio', 'total_return', etc.)
            max_iterations: Maximum number of parameter combinations to test
        
        Returns:
            Dict with best parameters and results
        """
        logger.info(f"Starting parameter optimization for {strategy_class.__name__}")
        
        # Generate parameter combinations
        param_combinations = self._generate_parameter_combinations(parameter_ranges, max_iterations)
        
        best_result = None
        best_params = None
        best_metric = float('-inf')
        
        results_summary = []
        
        for i, params in enumerate(param_combinations):
            try:
                logger.info(f"Testing combination {i+1}/{len(param_combinations)}: {params}")
                
                # Create strategy with parameters
                strategy = strategy_class(parameters=params)
                
                # Run backtest
                result = self.engine.run_backtest(strategy, base_config)
                
                # Get optimization metric value
                metric_value = getattr(result, optimization_metric, 0)
                
                # Record result
                results_summary.append({
                    'parameters': params.copy(),
                    'metric_value': metric_value,
                    'total_return': result.total_return,
                    'sharpe_ratio': result.sharpe_ratio,
                    'max_drawdown': result.max_drawdown,
                    'total_trades': result.total_trades
                })
                
                # Check if this is the best result
                if metric_value > best_metric:
                    best_metric = metric_value
                    best_params = params.copy()
                    best_result = result
                
                logger.info(f"Result: {optimization_metric}={metric_value:.4f}")
                
            except Exception as e:
                logger.error(f"Error testing parameters {params}: {str(e)}")
                continue
        
        logger.info(f"Optimization complete. Best {optimization_metric}: {best_metric:.4f}")
        logger.info(f"Best parameters: {best_params}")
        
        return {
            'best_parameters': best_params,
            'best_result': best_result,
            'best_metric_value': best_metric,
            'all_results': results_summary,
            'optimization_metric': optimization_metric
        }
    
    def _generate_parameter_combinations(self, parameter_ranges: Dict, max_combinations: int) -> List[Dict]:
        """Generate parameter combinations for testing"""
        import itertools
        
        # Convert ranges to lists of values
        param_lists = {}
        for param_name, param_range in parameter_ranges.items():
            if isinstance(param_range, list):
                param_lists[param_name] = param_range
            elif isinstance(param_range, tuple) and len(param_range) == 3:
                # (start, stop, step) tuple
                start, stop, step = param_range
                param_lists[param_name] = list(range(start, stop + 1, step))
            else:
                param_lists[param_name] = [param_range]  # Single value
        
        # Generate all combinations
        param_names = list(param_lists.keys())
        param_values = list(param_lists.values())
        
        combinations = list(itertools.product(*param_values))
        
        # Limit number of combinations
        if len(combinations) > max_combinations:
            # Sample random combinations
            import random
            combinations = random.sample(combinations, max_combinations)
        
        # Convert to list of parameter dictionaries
        param_combinations = []
        for combination in combinations:
            param_dict = dict(zip(param_names, combination))
            param_combinations.append(param_dict)
        
        return param_combinations