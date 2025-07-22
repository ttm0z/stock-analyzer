"""
Strategy validation for code quality, performance, and risk checks.
"""

import logging
import ast
import inspect
import sys
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from dataclasses import dataclass

from .base_strategy import BaseStrategy, StrategyContext, Signal

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Strategy validation result"""
    is_valid: bool
    score: float  # 0-100
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]
    performance_metrics: Dict = None
    
    def add_error(self, message: str):
        """Add validation error"""
        self.errors.append(message)
        self.is_valid = False
    
    def add_warning(self, message: str):
        """Add validation warning"""
        self.warnings.append(message)
    
    def add_suggestion(self, message: str):
        """Add improvement suggestion"""
        self.suggestions.append(message)

class StrategyValidator:
    """Comprehensive strategy validation"""
    
    def __init__(self):
        self.forbidden_imports = [
            'os', 'sys', 'subprocess', 'importlib', 'exec', 'eval',
            'open', 'file', 'input', 'raw_input'
        ]
        self.forbidden_functions = [
            'exec', 'eval', 'compile', '__import__', 'globals', 'locals',
            'vars', 'dir', 'getattr', 'setattr', 'delattr', 'hasattr'
        ]
        self.max_execution_time = 30  # seconds
        self.max_memory_mb = 512
    
    def validate_strategy(self, strategy_class: type, 
                         test_data: pd.DataFrame = None,
                         quick_validation: bool = False) -> ValidationResult:
        """
        Comprehensive strategy validation
        
        Args:
            strategy_class: Strategy class to validate
            test_data: Optional test data for performance validation
            quick_validation: Skip expensive tests if True
        """
        result = ValidationResult(
            is_valid=True,
            score=100.0,
            errors=[],
            warnings=[],
            suggestions=[]
        )
        
        try:
            # 1. Structural validation
            self._validate_structure(strategy_class, result)
            
            # 2. Code safety validation
            self._validate_code_safety(strategy_class, result)
            
            # 3. Parameter validation
            self._validate_parameters(strategy_class, result)
            
            # 4. Logic validation
            self._validate_logic(strategy_class, result)
            
            if not quick_validation and test_data is not None:
                # 5. Performance validation
                self._validate_performance(strategy_class, test_data, result)
                
                # 6. Risk validation
                self._validate_risk_characteristics(strategy_class, test_data, result)
            
            # Calculate final score
            result.score = self._calculate_score(result)
            
        except Exception as e:
            result.add_error(f"Validation failed: {str(e)}")
            result.score = 0.0
        
        return result
    
    def _validate_structure(self, strategy_class: type, result: ValidationResult):
        """Validate strategy class structure"""
        # Check inheritance
        if not issubclass(strategy_class, BaseStrategy):
            result.add_error("Strategy must inherit from BaseStrategy")
        
        # Check required methods
        required_methods = ['initialize', 'generate_signals', 'get_required_data']
        for method in required_methods:
            if not hasattr(strategy_class, method):
                result.add_error(f"Missing required method: {method}")
            elif not callable(getattr(strategy_class, method)):
                result.add_error(f"Method {method} is not callable")
        
        # Check method signatures
        try:
            init_sig = inspect.signature(strategy_class.__init__)
            if 'parameters' not in init_sig.parameters:
                result.add_warning("__init__ should accept 'parameters' argument")
            
            generate_sig = inspect.signature(strategy_class.generate_signals)
            if 'context' not in generate_sig.parameters:
                result.add_error("generate_signals must accept 'context' parameter")
        
        except Exception as e:
            result.add_warning(f"Could not validate method signatures: {str(e)}")
        
        # Check class attributes
        if not hasattr(strategy_class, '__doc__') or not strategy_class.__doc__:
            result.add_warning("Strategy should have documentation")
        
        # Check for version attribute
        if not hasattr(strategy_class, '__version__'):
            result.add_suggestion("Consider adding __version__ attribute")
    
    def _validate_code_safety(self, strategy_class: type, result: ValidationResult):
        """Validate code for security issues"""
        try:
            source_code = inspect.getsource(strategy_class)
            
            # Parse AST for dangerous patterns
            tree = ast.parse(source_code)
            
            class SecurityVisitor(ast.NodeVisitor):
                def __init__(self, validator_result):
                    self.result = validator_result
                
                def visit_Import(self, node):
                    for alias in node.names:
                        if alias.name in self.validator.forbidden_imports:
                            self.result.add_error(f"Forbidden import: {alias.name}")
                
                def visit_ImportFrom(self, node):
                    if node.module in self.validator.forbidden_imports:
                        self.result.add_error(f"Forbidden import: {node.module}")
                
                def visit_Call(self, node):
                    if isinstance(node.func, ast.Name):
                        if node.func.id in self.validator.forbidden_functions:
                            self.result.add_error(f"Forbidden function call: {node.func.id}")
                    self.generic_visit(node)
                
                def visit_Attribute(self, node):
                    # Check for dangerous attribute access
                    if isinstance(node.attr, str):
                        if node.attr.startswith('_'):
                            self.result.add_warning(f"Accessing private attribute: {node.attr}")
                    self.generic_visit(node)
            
            visitor = SecurityVisitor(result)
            visitor.validator = self
            visitor.visit(tree)
            
            # Check for other suspicious patterns
            suspicious_patterns = ['__import__', 'globals()', 'locals()', 'exec(', 'eval(']
            for pattern in suspicious_patterns:
                if pattern in source_code:
                    result.add_error(f"Suspicious code pattern: {pattern}")
        
        except Exception as e:
            result.add_warning(f"Could not analyze code safety: {str(e)}")
    
    def _validate_parameters(self, strategy_class: type, result: ValidationResult):
        """Validate strategy parameters"""
        try:
            # Try to instantiate with default parameters
            strategy = strategy_class()
            
            # Check if parameters are accessible
            if not hasattr(strategy, 'parameters'):
                result.add_warning("Strategy should expose 'parameters' attribute")
            
            # Validate parameter types and ranges
            if hasattr(strategy, 'parameters') and strategy.parameters:
                for param_name, param_value in strategy.parameters.items():
                    # Check for reasonable parameter values
                    if isinstance(param_value, (int, float)):
                        if param_value < 0 and 'period' in param_name.lower():
                            result.add_error(f"Negative period parameter: {param_name}")
                        if param_value > 1000 and 'period' in param_name.lower():
                            result.add_warning(f"Very large period parameter: {param_name}")
                    
                    # Check for percentage parameters
                    if 'rate' in param_name.lower() or 'threshold' in param_name.lower():
                        if isinstance(param_value, (int, float)) and param_value > 1:
                            result.add_suggestion(f"Parameter {param_name} might be a percentage (>1)")
        
        except Exception as e:
            result.add_warning(f"Could not validate parameters: {str(e)}")
    
    def _validate_logic(self, strategy_class: type, result: ValidationResult):
        """Validate strategy logic"""
        try:
            # Create test strategy instance
            strategy = strategy_class()
            
            # Check initialization
            test_universe = ['AAPL', 'GOOGL', 'MSFT']
            start_date = datetime.now() - timedelta(days=365)
            end_date = datetime.now()
            
            try:
                strategy.initialize(test_universe, start_date, end_date)
                if not strategy.is_initialized:
                    result.add_error("Strategy initialization failed")
            except Exception as e:
                result.add_error(f"Strategy initialization error: {str(e)}")
            
            # Check required data specification
            try:
                required_data = strategy.get_required_data()
                if not isinstance(required_data, dict):
                    result.add_error("get_required_data must return a dictionary")
                
                # Check for reasonable data requirements
                if 'timeframes' not in required_data:
                    result.add_warning("Should specify required timeframes")
                
                if 'lookback_days' in required_data:
                    lookback = required_data['lookback_days']
                    if lookback > 1000:
                        result.add_warning("Very large lookback period may impact performance")
            
            except Exception as e:
                result.add_error(f"get_required_data error: {str(e)}")
            
            # Test signal generation with dummy data
            try:
                # Create dummy context
                dates = pd.date_range(start=start_date, end=end_date, freq='D')
                dummy_data = pd.DataFrame({
                    'open': np.random.randn(len(dates)).cumsum() + 100,
                    'high': np.random.randn(len(dates)).cumsum() + 102,
                    'low': np.random.randn(len(dates)).cumsum() + 98,
                    'close': np.random.randn(len(dates)).cumsum() + 100,
                    'volume': np.random.randint(1000000, 10000000, len(dates))
                }, index=dates)
                
                context = StrategyContext(
                    current_date=end_date,
                    portfolio_value=100000,
                    cash_balance=50000,
                    positions={'AAPL': 100},
                    market_data={'AAPL': dummy_data}
                )
                
                signals = strategy.generate_signals(context)
                
                if not isinstance(signals, list):
                    result.add_error("generate_signals must return a list")
                
                # Validate signals
                for signal in signals:
                    if not isinstance(signal, Signal):
                        result.add_error("Signals must be Signal objects")
                    else:
                        if signal.strength < 0 or signal.strength > 1:
                            result.add_warning(f"Signal strength should be 0-1: {signal.strength}")
                        if signal.price <= 0:
                            result.add_error(f"Invalid signal price: {signal.price}")
            
            except Exception as e:
                result.add_error(f"Signal generation error: {str(e)}")
        
        except Exception as e:
            result.add_error(f"Logic validation failed: {str(e)}")
    
    def _validate_performance(self, strategy_class: type, test_data: pd.DataFrame, 
                            result: ValidationResult):
        """Validate strategy performance characteristics"""
        try:
            # Run mini backtest
            from ..backtesting.engine import BacktestingEngine, BacktestConfig
            from ..data.data_provider import DataProvider, DataRequest, DataResponse
            
            # Create mock data provider
            class MockDataProvider(DataProvider):
                def __init__(self, data):
                    super().__init__("mock")
                    self.data = data
                
                def get_historical_data(self, request):
                    return DataResponse(
                        data=self.data,
                        symbols=request.symbols,
                        start_date=request.start_date,
                        end_date=request.end_date,
                        timeframe=request.timeframe,
                        source="mock"
                    )
                
                def get_real_time_quote(self, symbols):
                    return {}
                
                def search_symbols(self, query, limit=10):
                    return []
                
                def get_asset_info(self, symbols):
                    return {}
                
                def get_supported_timeframes(self):
                    return ['1d']
                
                def get_supported_asset_types(self):
                    return ['stock']
            
            # Setup test
            strategy = strategy_class()
            data_provider = MockDataProvider(test_data)
            engine = BacktestingEngine(data_provider)
            
            config = BacktestConfig(
                start_date=test_data.index[0],
                end_date=test_data.index[-1],
                initial_capital=100000,
                universe=['TEST']
            )
            
            # Run backtest
            backtest_result = engine.run_backtest(strategy, config)
            
            # Analyze results
            if backtest_result.total_trades == 0:
                result.add_warning("Strategy generated no trades in test period")
            
            if abs(backtest_result.total_return) > 5.0:  # >500% return
                result.add_warning("Extremely high returns may indicate overfitting")
            
            if backtest_result.max_drawdown > 0.5:  # >50% drawdown
                result.add_warning("Very high maximum drawdown")
            
            if backtest_result.sharpe_ratio < -2:
                result.add_warning("Very poor risk-adjusted returns")
            
            # Store performance metrics
            result.performance_metrics = {
                'total_return': backtest_result.total_return,
                'sharpe_ratio': backtest_result.sharpe_ratio,
                'max_drawdown': backtest_result.max_drawdown,
                'total_trades': backtest_result.total_trades,
                'win_rate': backtest_result.win_rate
            }
        
        except Exception as e:
            result.add_warning(f"Performance validation failed: {str(e)}")
    
    def _validate_risk_characteristics(self, strategy_class: type, test_data: pd.DataFrame,
                                     result: ValidationResult):
        """Validate risk management characteristics"""
        try:
            strategy = strategy_class()
            
            # Check for risk management methods
            risk_methods = ['calculate_position_size', 'apply_risk_management']
            for method in risk_methods:
                if not hasattr(strategy, method):
                    result.add_suggestion(f"Consider implementing {method} for better risk management")
            
            # Check parameter reasonableness for risk
            if hasattr(strategy, 'parameters'):
                params = strategy.parameters
                
                # Check stop loss parameters
                stop_loss_params = [k for k in params.keys() if 'stop' in k.lower()]
                for param in stop_loss_params:
                    value = params[param]
                    if isinstance(value, (int, float)) and value > 0.5:
                        result.add_warning(f"Very large stop loss parameter: {param}")
                
                # Check position sizing
                size_params = [k for k in params.keys() if 'size' in k.lower() or 'weight' in k.lower()]
                for param in size_params:
                    value = params[param]
                    if isinstance(value, (int, float)) and value > 1:
                        result.add_warning(f"Position size parameter >100%: {param}")
        
        except Exception as e:
            result.add_warning(f"Risk validation failed: {str(e)}")
    
    def _calculate_score(self, result: ValidationResult) -> float:
        """Calculate overall validation score"""
        score = 100.0
        
        # Deduct for errors (severe)
        score -= len(result.errors) * 20
        
        # Deduct for warnings (moderate)
        score -= len(result.warnings) * 5
        
        # Small deduction for suggestions
        score -= len(result.suggestions) * 1
        
        # Performance bonus/penalty
        if result.performance_metrics:
            metrics = result.performance_metrics
            
            # Bonus for reasonable performance
            if 0 < metrics.get('sharpe_ratio', 0) < 3:
                score += 5
            
            # Bonus for reasonable number of trades
            if 10 <= metrics.get('total_trades', 0) <= 1000:
                score += 5
            
            # Penalty for extreme drawdown
            if metrics.get('max_drawdown', 0) > 0.5:
                score -= 10
        
        return max(0.0, min(100.0, score))
    
    def validate_strategy_code(self, code: str) -> ValidationResult:
        """Validate strategy code string before execution"""
        result = ValidationResult(
            is_valid=True,
            score=100.0,
            errors=[],
            warnings=[],
            suggestions=[]
        )
        
        try:
            # Parse the code
            tree = ast.parse(code)
            
            # Check for security issues
            class CodeSecurityVisitor(ast.NodeVisitor):
                def __init__(self, validator_result, validator):
                    self.result = validator_result
                    self.validator = validator
                
                def visit_Import(self, node):
                    for alias in node.names:
                        if alias.name in self.validator.forbidden_imports:
                            self.result.add_error(f"Forbidden import: {alias.name}")
                
                def visit_ImportFrom(self, node):
                    if node.module and node.module in self.validator.forbidden_imports:
                        self.result.add_error(f"Forbidden import: {node.module}")
                
                def visit_Call(self, node):
                    if isinstance(node.func, ast.Name):
                        if node.func.id in self.validator.forbidden_functions:
                            self.result.add_error(f"Forbidden function call: {node.func.id}")
                    self.generic_visit(node)
                
                def visit_Exec(self, node):
                    self.result.add_error("exec statements are forbidden")
                
                def visit_Eval(self, node):
                    self.result.add_error("eval statements are forbidden")
            
            visitor = CodeSecurityVisitor(result, self)
            visitor.visit(tree)
            
            # Check code complexity
            complexity = self._calculate_complexity(tree)
            if complexity > 20:
                result.add_warning(f"High code complexity: {complexity}")
            elif complexity > 50:
                result.add_error(f"Extremely high code complexity: {complexity}")
            
            # Check for proper structure
            class_found = False
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_found = True
                    # Check if class has proper methods
                    method_names = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                    required_methods = ['__init__', 'generate_signals']
                    for required in required_methods:
                        if required not in method_names:
                            result.add_error(f"Missing required method: {required}")
            
            if not class_found:
                result.add_error("No strategy class found in code")
        
        except SyntaxError as e:
            result.add_error(f"Syntax error: {str(e)}")
        except Exception as e:
            result.add_error(f"Code validation failed: {str(e)}")
        
        return result
    
    def _calculate_complexity(self, tree: ast.AST) -> int:
        """Calculate cyclomatic complexity of code"""
        complexity = 1  # Base complexity
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1
            elif isinstance(node, (ast.And, ast.Or)):
                complexity += 1
        
        return complexity

def validate_strategy_file(file_path: str) -> ValidationResult:
    """Validate strategy from file"""
    validator = StrategyValidator()
    
    try:
        with open(file_path, 'r') as f:
            code = f.read()
        
        return validator.validate_strategy_code(code)
    
    except Exception as e:
        result = ValidationResult(False, 0.0, [], [], [])
        result.add_error(f"Could not read file: {str(e)}")
        return result

def quick_validate_strategy(strategy_class: type) -> bool:
    """Quick validation for basic strategy compliance"""
    validator = StrategyValidator()
    result = validator.validate_strategy(strategy_class, quick_validation=True)
    return result.is_valid and len(result.errors) == 0