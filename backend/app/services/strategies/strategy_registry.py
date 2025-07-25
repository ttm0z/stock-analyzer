"""
Strategy registry for managing and discovering trading strategies.
"""

import logging
import importlib
import inspect
from typing import Dict, List, Optional, Type, Any
from pathlib import Path
import json

from .base_strategy import BaseStrategy

logger = logging.getLogger(__name__)

class StrategyRegistry:
    """Registry for managing trading strategies"""
    
    def __init__(self):
        self.strategies: Dict[str, Type[BaseStrategy]] = {}
        self.strategy_metadata: Dict[str, Dict] = {}
        self.categories: Dict[str, List[str]] = {}
        
        # Auto-register built-in strategies
        self._register_builtin_strategies()
    
    def register_strategy(self, strategy_name: str, strategy_class: Type[BaseStrategy], 
                         category: str = "custom", 
                         metadata: Dict = None) -> bool:
        """
        Register a strategy class
        
        Args:
            strategy_name: Name to register the strategy under
            strategy_class: Strategy class to register
            category: Strategy category (trend, mean_reversion, momentum, etc.)
            metadata: Additional strategy metadata
        
        Returns:
            True if registration successful
        """
        try:
            # Handle case where strategy_class might be a string (error condition)
            if isinstance(strategy_class, str):
                logger.error(f"Strategy class for {strategy_name} is a string, not a class: {strategy_class}")
                return False
                
            # Validate strategy class
            if not self._validate_strategy_class(strategy_class):
                logger.error(f"Invalid strategy class: {strategy_class.__name__}")
                return False
            
            # Check if already registered
            if strategy_name in self.strategies:
                logger.warning(f"Strategy {strategy_name} already registered, overwriting")
            
            # Register strategy
            self.strategies[strategy_name] = strategy_class
            
            # Store metadata
            self.strategy_metadata[strategy_name] = {
                'name': strategy_name,
                'category': category,
                'description': getattr(strategy_class, '__doc__', ''),
                'module': strategy_class.__module__,
                'parameters': self._extract_parameters(strategy_class),
                'created_at': None,
                'version': getattr(strategy_class, '__version__', '1.0.0'),
                **(metadata or {})
            }
            
            # Update categories
            if category not in self.categories:
                self.categories[category] = []
            if strategy_name not in self.categories[category]:
                self.categories[category].append(strategy_name)
            
            logger.info(f"Registered strategy: {strategy_name} in category {category}")
            return True
            
        except Exception as e:
            logger.error(f"Error registering strategy {strategy_class.__name__}: {str(e)}")
            return False
    
    def unregister_strategy(self, strategy_name: str) -> bool:
        """Unregister a strategy"""
        try:
            if strategy_name not in self.strategies:
                logger.warning(f"Strategy {strategy_name} not found")
                return False
            
            # Remove from categories
            additional_metadata = self.strategy_metadata.get(strategy_name, {})
            category = additional_metadata.get('category')
            if category and category in self.categories:
                if strategy_name in self.categories[category]:
                    self.categories[category].remove(strategy_name)
                if not self.categories[category]:
                    del self.categories[category]
            
            # Remove from registry
            del self.strategies[strategy_name]
            del self.strategy_metadata[strategy_name]
            
            logger.info(f"Unregistered strategy: {strategy_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error unregistering strategy {strategy_name}: {str(e)}")
            return False
    
    def get_strategy_class(self, strategy_name: str) -> Optional[Type[BaseStrategy]]:
        """Get strategy class by name"""
        return self.strategies.get(strategy_name)
    
    def create_strategy(self, strategy_name: str, parameters: Dict = None) -> Optional[BaseStrategy]:
        """Create strategy instance"""
        try:
            strategy_class = self.get_strategy_class(strategy_name)
            if not strategy_class:
                logger.error(f"Strategy {strategy_name} not found")
                return None
            
            return strategy_class(parameters=parameters)
            
        except Exception as e:
            logger.error(f"Error creating strategy {strategy_name}: {str(e)}")
            return None
    
    def list_strategies(self, category: str = None) -> List[str]:
        """List available strategies"""
        if category:
            return self.categories.get(category, [])
        return list(self.strategies.keys())
    
    def list_categories(self) -> List[str]:
        """List strategy categories"""
        return list(self.categories.keys())
    
    def get_strategy_metadata(self, strategy_name: str) -> Optional[Dict]:
        """Get strategy metadata"""
        return self.strategy_metadata.get(strategy_name)
    
    def get_strategies_by_category(self, category: str) -> Dict[str, Type[BaseStrategy]]:
        """Get all strategies in a category"""
        if category not in self.categories:
            return {}
        
        return {
            name: self.strategies[name] 
            for name in self.categories[category] 
            if name in self.strategies
        }
    
    def search_strategies(self, query: str) -> List[str]:
        """Search strategies by name or description"""
        query = query.lower()
        matches = []
        
        for name, metadata in self.strategy_metadata.items():
            if (query in name.lower() or 
                query in metadata.get('description', '').lower() or
                query in metadata.get('category', '').lower()):
                matches.append(name)
        
        return matches
    
    def get_strategy_info(self, strategy_name: str) -> Optional[Dict]:
        """Get comprehensive strategy information"""
        if strategy_name not in self.strategies:
            return None
        
        strategy_class = self.strategies[strategy_name]
        additional_metadata = self.strategy_metadata[strategy_name]
        
        return {
            'name': strategy_name,
            'class': strategy_class.__name__,
            'module': strategy_class.__module__,
            'description': additional_metadata.get('description', ''),
            'category': additional_metadata.get('category', 'unknown'),
            'parameters': additional_metadata.get('parameters', {}),
            'version': additional_metadata.get('version', '1.0.0'),
            'is_builtin': additional_metadata.get('category') in ['trend', 'mean_reversion', 'momentum', 'arbitrage'],
            'dependencies': self._get_strategy_dependencies(strategy_class)
        }
    
    def validate_strategy_parameters(self, strategy_name: str, parameters: Dict) -> Dict:
        """
        Validate strategy parameters
        
        Returns:
            Dict with 'valid' boolean and 'errors' list
        """
        result = {'valid': True, 'errors': []}
        
        try:
            strategy_class = self.get_strategy_class(strategy_name)
            if not strategy_class:
                result['valid'] = False
                result['errors'].append(f"Strategy {strategy_name} not found")
                return result
            
            # Get expected parameters
            additional_metadata = self.strategy_metadata.get(strategy_name, {})
            expected_params = additional_metadata.get('parameters', {})
            
            # Check required parameters
            for param_name, param_info in expected_params.items():
                if param_info.get('required', False) and param_name not in parameters:
                    result['valid'] = False
                    result['errors'].append(f"Required parameter missing: {param_name}")
            
            # Validate parameter types and ranges
            for param_name, param_value in parameters.items():
                if param_name in expected_params:
                    param_info = expected_params[param_name]
                    
                    # Type validation
                    expected_type = param_info.get('type', str)
                    if not isinstance(param_value, expected_type):
                        try:
                            # Try to convert
                            if expected_type == int:
                                param_value = int(param_value)
                            elif expected_type == float:
                                param_value = float(param_value)
                            elif expected_type == bool:
                                param_value = bool(param_value)
                        except (ValueError, TypeError):
                            result['valid'] = False
                            result['errors'].append(f"Invalid type for {param_name}: expected {expected_type.__name__}")
                            continue
                    
                    # Range validation
                    if 'min_value' in param_info and param_value < param_info['min_value']:
                        result['valid'] = False
                        result['errors'].append(f"Parameter {param_name} below minimum: {param_info['min_value']}")
                    
                    if 'max_value' in param_info and param_value > param_info['max_value']:
                        result['valid'] = False
                        result['errors'].append(f"Parameter {param_name} above maximum: {param_info['max_value']}")
        
        except Exception as e:
            result['valid'] = False
            result['errors'].append(f"Validation error: {str(e)}")
        
        return result
    
    def export_registry(self) -> Dict:
        """Export registry to dictionary"""
        return {
            'strategies': {
                name: {
                    'class_name': cls.__name__,
                    'module': cls.__module__,
                    'metadata': self.strategy_metadata.get(name, {})
                }
                for name, cls in self.strategies.items()
            },
            'categories': self.categories.copy()
        }
    
    def _register_builtin_strategies(self):
        """Register built-in strategies"""
        try:
            # Import and register built-in strategies
            builtin_strategies = [
                ('builtins.buy_hold', 'BuyHoldStrategy', 'trend'),
                ('builtins.moving_average', 'MovingAverageStrategy', 'trend'),
                ('builtins.momentum', 'MomentumStrategy', 'momentum'),
                ('builtins.momentum', 'RelativeStrengthStrategy', 'momentum'),
                ('builtins.momentum', 'MeanReversionMomentumStrategy', 'momentum'),
            ]
            
            for module_name, class_name, category in builtin_strategies:
                try:
                    module = importlib.import_module(f'.{module_name}', package='app.services.strategies')
                    strategy_class = getattr(module, class_name)
                    self.register_strategy(class_name, strategy_class, category)
                except (ImportError, AttributeError) as e:
                    logger.warning(f"Could not import {class_name} from {module_name}: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error registering builtin strategies: {str(e)}")
    
    def _validate_strategy_class(self, strategy_class: Type) -> bool:
        """Validate that class is a proper strategy"""
        try:
            # Check if it's a class
            if not inspect.isclass(strategy_class):
                return False
            
            # Check if it inherits from BaseStrategy
            if not issubclass(strategy_class, BaseStrategy):
                return False
            
            # Check required methods
            required_methods = ['initialize', 'generate_signals', 'get_required_data']
            for method in required_methods:
                if not hasattr(strategy_class, method):
                    return False
            
            return True
            
        except Exception:
            return False
    
    def _extract_parameters(self, strategy_class: Type[BaseStrategy]) -> Dict:
        """Extract parameter information from strategy class"""
        parameters = {}
        
        try:
            # Try to get parameters from __init__ method
            init_signature = inspect.signature(strategy_class.__init__)
            
            for param_name, param in init_signature.parameters.items():
                if param_name in ['self', 'parameters']:
                    continue
                
                param_info = {
                    'name': param_name,
                    'type': param.annotation if param.annotation != inspect.Parameter.empty else str,
                    'default': param.default if param.default != inspect.Parameter.empty else None,
                    'required': param.default == inspect.Parameter.empty
                }
                
                parameters[param_name] = param_info
            
            # Try to get additional parameter info from class attributes
            if hasattr(strategy_class, '_parameter_definitions'):
                param_defs = strategy_class._parameter_definitions
                for param_name, param_def in param_defs.items():
                    if param_name in parameters:
                        parameters[param_name].update(param_def)
                    else:
                        parameters[param_name] = param_def
        
        except Exception as e:
            logger.warning(f"Could not extract parameters from {strategy_class.__name__}: {str(e)}")
        
        return parameters
    
    def _get_strategy_dependencies(self, strategy_class: Type[BaseStrategy]) -> List[str]:
        """Get strategy dependencies"""
        dependencies = []
        
        try:
            # Check for common dependencies
            source = inspect.getsource(strategy_class)
            
            common_deps = ['pandas', 'numpy', 'scipy', 'sklearn', 'ta', 'yfinance']
            for dep in common_deps:
                if f'import {dep}' in source or f'from {dep}' in source:
                    dependencies.append(dep)
        
        except Exception:
            pass
        
        return dependencies

# Global strategy registry instance
strategy_registry = StrategyRegistry()

def register_strategy(category: str = "custom", metadata: Dict = None):
    """Decorator for registering strategies"""
    def decorator(strategy_class):
        strategy_registry.register_strategy(strategy_class, category, metadata)
        return strategy_class
    return decorator