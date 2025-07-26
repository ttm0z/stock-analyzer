"""
Strategy Management API routes
"""
from flask import Blueprint, request, jsonify, current_app, g
from ..db import db
from ..auth.decorators import token_required
from ..utils.validation import InputValidator, ValidationError, handle_validation_error
from ..services.strategies.strategy_registry import StrategyRegistry
from ..services.strategies.builtins.moving_average import MovingAverageStrategy
from ..services.strategies.builtins.momentum import MomentumStrategy
from ..services.strategies.builtins.buy_hold import BuyHoldStrategy
from ..services.strategies.base_strategy import StrategyContext
import logging
from datetime import datetime, timedelta
import json

strategy_bp = Blueprint('strategy', __name__)
logger = logging.getLogger(__name__)

# Initialize strategy registry
strategy_registry = StrategyRegistry()

# Register built-in strategies
strategy_registry.register_strategy('moving_average', MovingAverageStrategy)
strategy_registry.register_strategy('momentum', MomentumStrategy) 
strategy_registry.register_strategy('buy_hold', BuyHoldStrategy)

@strategy_bp.route('/strategies', methods=['GET'])
@token_required
@handle_validation_error
def get_available_strategies():
    """List available trading strategies"""
    try:
        strategies = []
        
        # Moving Average Strategy
        strategies.append({
            'id': 'moving_average',
            'name': 'Moving Average Crossover',
            'description': 'Simple moving average crossover strategy for trend following',
            'strategy_type': 'Trend Following',
            'risk_level': 'Medium',
            'typical_holding_period': '1-3 months',
            'parameters': [
                {
                    'name': 'fast_period',
                    'type': 'integer',
                    'default': 20,
                    'min': 5,
                    'max': 100,
                    'description': 'Fast moving average period'
                },
                {
                    'name': 'slow_period', 
                    'type': 'integer',
                    'default': 50,
                    'min': 10,
                    'max': 200,
                    'description': 'Slow moving average period'
                },
                {
                    'name': 'position_size',
                    'type': 'float',
                    'default': 0.1,
                    'min': 0.01,
                    'max': 1.0,
                    'description': 'Position size as fraction of portfolio'
                },
                {
                    'name': 'min_volume',
                    'type': 'integer',
                    'default': 100000,
                    'min': 1000,
                    'max': 10000000,
                    'description': 'Minimum daily volume requirement'
                }
            ]
        })
        
        # Momentum Strategy
        strategies.append({
            'id': 'momentum',
            'name': 'Momentum Strategy',
            'description': 'Price momentum strategy based on relative strength',
            'strategy_type': 'Momentum',
            'risk_level': 'High',
            'typical_holding_period': '2-6 weeks',
            'parameters': [
                {
                    'name': 'lookback_period',
                    'type': 'integer',
                    'default': 20,
                    'min': 5,
                    'max': 100,
                    'description': 'Lookback period for momentum calculation'
                },
                {
                    'name': 'top_n_stocks',
                    'type': 'integer',
                    'default': 10,
                    'min': 1,
                    'max': 50,
                    'description': 'Number of top momentum stocks to hold'
                },
                {
                    'name': 'rebalance_frequency',
                    'type': 'string',
                    'default': 'monthly',
                    'options': ['daily', 'weekly', 'monthly'],
                    'description': 'Portfolio rebalancing frequency'
                }
            ]
        })
        
        # Buy and Hold Strategy
        strategies.append({
            'id': 'buy_hold',
            'name': 'Buy and Hold',
            'description': 'Simple buy and hold strategy for long-term investing',
            'strategy_type': 'Passive',
            'risk_level': 'Low',
            'typical_holding_period': '1+ years',
            'parameters': [
                {
                    'name': 'rebalance_frequency',
                    'type': 'string',
                    'default': 'quarterly',
                    'options': ['monthly', 'quarterly', 'yearly'],
                    'description': 'Portfolio rebalancing frequency'
                },
                {
                    'name': 'equal_weight',
                    'type': 'boolean',
                    'default': True,
                    'description': 'Use equal weighting for all positions'
                }
            ]
        })
        
        return jsonify({
            'strategies': strategies,
            'total': len(strategies)
        }), 200
        
    except Exception as e:
        logger.error(f"Get strategies error: {e}")
        return jsonify({'error': 'Failed to retrieve strategies'}), 500

@strategy_bp.route('/strategies/run', methods=['POST'])
@token_required
@handle_validation_error
def run_strategy():
    """Execute strategy on portfolio data"""
    from flask import g
    from ..models.portfolio_models import Portfolio
    
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No JSON data provided'}), 400
    
    try:
        # Validate required fields
        required_fields = ['strategy_id', 'universe']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        strategy_id = data['strategy_id']
        universe = data['universe']
        parameters = data.get('parameters', {})
        portfolio_id = data.get('portfolio_id')
        
        # Validate strategy exists
        if strategy_id not in ['moving_average', 'momentum', 'buy_hold']:
            return jsonify({'error': 'Invalid strategy_id'}), 400
        
        # Validate universe
        if not isinstance(universe, list) or len(universe) == 0:
            return jsonify({'error': 'Universe must be a non-empty list of symbols'}), 400
        
        # Validate symbols
        validated_universe = []
        for symbol in universe:
            try:
                validated_symbol = InputValidator.validate_stock_symbol(symbol)
                validated_universe.append(validated_symbol)
            except ValidationError:
                return jsonify({'error': f'Invalid symbol: {symbol}'}), 400
        
        # Get portfolio if specified
        portfolio = None
        if portfolio_id:
            portfolio = Portfolio.query.filter_by(
                id=portfolio_id,
                user_id=g.current_user.id
            ).first()
            if not portfolio:
                return jsonify({'error': 'Portfolio not found'}), 404
        
        # Create strategy instance
        if strategy_id == 'moving_average':
            strategy = MovingAverageStrategy(parameters)
        elif strategy_id == 'momentum':
            strategy = MomentumStrategy(parameters)
        elif strategy_id == 'buy_hold':
            strategy = BuyHoldStrategy(parameters)
        
        # Set strategy universe
        strategy.universe = validated_universe
        
        # Get market data for the universe
        stock_service = current_app.stock_service
        market_data = {}
        current_date = datetime.now()
        
        # Fetch historical data for each symbol (last 1 year for indicators)
        end_date = current_date
        start_date = current_date - timedelta(days=365)
        
        for symbol in validated_universe:
            try:
                historical_data = stock_service.fetch_historical_data(
                    symbol, 
                    start_date.strftime('%Y-%m-%d'),
                    end_date.strftime('%Y-%m-%d')
                )
                
                # Convert to DataFrame-like structure
                if 'historical' in historical_data and historical_data['historical']:
                    import pandas as pd
                    df_data = []
                    
                    for record in historical_data['historical']:
                        df_data.append({
                            'date': record['date'],
                            'open': record['open'],
                            'high': record['high'], 
                            'low': record['low'],
                            'close': record['close'],
                            'volume': record['volume']
                        })
                    
                    df = pd.DataFrame(df_data)
                    df['date'] = pd.to_datetime(df['date'])
                    df.set_index('date', inplace=True)
                    df.sort_index(inplace=True)
                    
                    market_data[symbol] = df
                    
            except Exception as e:
                logger.warning(f"Failed to fetch data for {symbol}: {e}")
                continue
        
        if not market_data:
            return jsonify({'error': 'No market data available for specified universe'}), 400
        
        # Create strategy context
        portfolio_value = portfolio.total_value if portfolio else 100000.0  # Default $100k
        cash_balance = portfolio.cash_balance if portfolio else portfolio_value
        positions = {}
        
        if portfolio:
            for position in portfolio.positions:
                if position.is_open:
                    positions[position.symbol] = position.quantity
        
        context = StrategyContext(
            current_date=current_date,
            portfolio_value=portfolio_value,
            cash_balance=cash_balance,
            positions=positions,
            market_data=market_data
        )
        
        # Initialize strategy
        strategy.initialize(validated_universe, start_date, end_date)
        
        # Generate signals
        signals = strategy.generate_signals(context)
        
        # Format signals for response
        signals_data = []
        for signal in signals:
            signals_data.append({
                'symbol': signal.symbol,
                'signal_type': signal.signal_type,
                'strength': signal.strength,
                'price': signal.price,
                'quantity': signal.quantity,
                'timestamp': signal.timestamp.isoformat(),
                'reason': signal.reason,
                'metadata': signal.metadata
            })
        
        logger.info(f"Strategy {strategy_id} generated {len(signals)} signals for user {g.current_user.id}")
        
        return jsonify({
            'strategy_run': {
                'strategy_id': strategy_id,
                'strategy_name': strategy.name,
                'universe': validated_universe,
                'parameters': parameters,
                'execution_time': current_date.isoformat(),
                'portfolio_id': portfolio_id,
                'signals_generated': len(signals)
            },
            'signals': signals_data,
            'context': {
                'portfolio_value': portfolio_value,
                'cash_balance': cash_balance,
                'current_positions': len(positions),
                'data_symbols': list(market_data.keys())
            }
        }), 200
        
    except ValidationError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Strategy execution error: {e}")
        return jsonify({'error': 'Failed to execute strategy'}), 500

@strategy_bp.route('/strategies/<strategy_id>/signals', methods=['GET'])
@token_required
@handle_validation_error  
def get_strategy_signals(strategy_id):
    """Get current signals for a strategy"""
    from flask import g
    
    try:
        # Validate strategy exists
        if strategy_id not in ['moving_average', 'momentum', 'buy_hold']:
            return jsonify({'error': 'Invalid strategy_id'}), 404
        
        # Get query parameters
        symbols = request.args.get('symbols', '').split(',') if request.args.get('symbols') else []
        lookback_days = request.args.get('lookback_days', 30, type=int)
        
        # For this MVP, we'll return mock signals since we don't have a signal storage system yet
        # In a production system, you'd query stored signals from the database
        
        signals_data = []
        
        # Mock response for demonstration
        if strategy_id == 'moving_average':
            mock_signals = [
                {
                    'symbol': 'AAPL',
                    'signal_type': 'BUY',
                    'strength': 0.75,
                    'price': 150.25,
                    'timestamp': datetime.now().isoformat(),
                    'reason': 'Fast MA (20) crossed above Slow MA (50)',
                    'metadata': {
                        'fast_ma': 149.8,
                        'slow_ma': 148.5,
                        'fast_period': 20,
                        'slow_period': 50
                    }
                }
            ]
            signals_data = mock_signals
        
        return jsonify({
            'strategy_id': strategy_id,
            'signals': signals_data,
            'query_params': {
                'symbols': symbols,
                'lookback_days': lookback_days
            },
            'note': 'This is a mock response for MVP. Implement signal storage for production.'
        }), 200
        
    except Exception as e:
        logger.error(f"Get strategy signals error: {e}")
        return jsonify({'error': 'Failed to retrieve strategy signals'}), 500

@strategy_bp.route('/strategies/<strategy_id>/validate', methods=['POST'])
@token_required
@handle_validation_error
def validate_strategy_parameters(strategy_id):
    """Validate strategy parameters"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No JSON data provided'}), 400
    
    try:
        # Validate strategy exists
        if strategy_id not in ['moving_average', 'momentum', 'buy_hold']:
            return jsonify({'error': 'Invalid strategy_id'}), 404
        
        parameters = data.get('parameters', {})
        validation_errors = []
        
        # Validate parameters based on strategy type
        if strategy_id == 'moving_average':
            # Validate moving average parameters
            fast_period = parameters.get('fast_period', 20)
            slow_period = parameters.get('slow_period', 50)
            position_size = parameters.get('position_size', 0.1)
            
            if not isinstance(fast_period, int) or fast_period < 5 or fast_period > 100:
                validation_errors.append('fast_period must be an integer between 5 and 100')
            
            if not isinstance(slow_period, int) or slow_period < 10 or slow_period > 200:
                validation_errors.append('slow_period must be an integer between 10 and 200')
            
            if fast_period >= slow_period:
                validation_errors.append('fast_period must be less than slow_period')
            
            if not isinstance(position_size, (int, float)) or position_size <= 0 or position_size > 1:
                validation_errors.append('position_size must be a number between 0 and 1')
        
        elif strategy_id == 'momentum':
            # Validate momentum parameters
            lookback_period = parameters.get('lookback_period', 20)
            top_n_stocks = parameters.get('top_n_stocks', 10)
            
            if not isinstance(lookback_period, int) or lookback_period < 5 or lookback_period > 100:
                validation_errors.append('lookback_period must be an integer between 5 and 100')
            
            if not isinstance(top_n_stocks, int) or top_n_stocks < 1 or top_n_stocks > 50:
                validation_errors.append('top_n_stocks must be an integer between 1 and 50')
        
        elif strategy_id == 'buy_hold':
            # Validate buy and hold parameters
            rebalance_frequency = parameters.get('rebalance_frequency', 'quarterly')
            
            if rebalance_frequency not in ['monthly', 'quarterly', 'yearly']:
                validation_errors.append('rebalance_frequency must be monthly, quarterly, or yearly')
        
        is_valid = len(validation_errors) == 0
        
        return jsonify({
            'valid': is_valid,
            'errors': validation_errors,
            'parameters': parameters
        }), 200 if is_valid else 400
        
    except Exception as e:
        logger.error(f"Parameter validation error: {e}")
        return jsonify({'error': 'Failed to validate parameters'}), 500

# Additional CRUD routes for user strategy management
@strategy_bp.route('/strategies/user', methods=['GET'])
@token_required
@handle_validation_error
def get_user_strategies():
    """Get user's created strategy instances"""
    from flask import g
    from ..models.strategy_models import Strategy, StrategyPerformance
    
    try:
        strategies = Strategy.query.filter_by(user_id=g.current_user.id).all()
        
        strategies_data = []
        for strategy in strategies:
            # Calculate performance metrics if available
            return_percent = 0.0
            total_trades = 0
            win_rate = 0.0
            
            if strategy.performance:
                return_percent = float(strategy.performance.total_return or 0.0)
                total_trades = strategy.performance.total_trades or 0
                win_rate = float(strategy.performance.win_rate or 0.0)
            
            strategies_data.append({
                'id': strategy.id,
                'name': strategy.name,
                'description': strategy.description,
                'strategy_type': strategy.strategy_type,
                'status': 'active' if strategy.is_active else 'paused',
                'return_percent': return_percent,
                'total_trades': total_trades,
                'win_rate': win_rate,
                'created_at': strategy.created_at.isoformat(),
                'parameters': strategy.parameters
            })
        
        return jsonify({
            'strategies': strategies_data,
            'total': len(strategies_data)
        }), 200
        
    except Exception as e:
        logger.error(f"Get user strategies error: {e}")
        return jsonify({'error': 'Failed to retrieve user strategies'}), 500

@strategy_bp.route('/strategies/user', methods=['POST'])
@token_required
@handle_validation_error
def create_user_strategy():
    """Create a new user strategy instance"""
    from flask import g
    from ..models.strategy_models import Strategy
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No JSON data provided'}), 400
    
    try:
        # Validate required fields
        required_fields = ['name', 'strategy_type', 'parameters']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Validate strategy type
        valid_types = ['moving_average', 'momentum', 'buy_hold']
        if data['strategy_type'] not in valid_types:
            return jsonify({'error': 'Invalid strategy_type'}), 400
        
        # Create strategy instance
        strategy = Strategy(
            user_id=g.current_user.id,
            name=data['name'],
            description=data.get('description', ''),
            strategy_type=data['strategy_type'],
            category=data.get('category', 'equity'),
            complexity=data.get('complexity', 'intermediate'),
            parameters=data['parameters'],
            entry_rules=data.get('entry_rules', {}),
            exit_rules=data.get('exit_rules', {}),
            risk_rules=data.get('risk_rules', {}),
            is_active=data.get('is_active', True),
            tags=data.get('tags', [])
        )
        
        try:
            db.session.add(strategy)
            db.session.commit()
        except Exception as db_error:
            db.session.rollback()
            logger.error(f"Database error during strategy creation: {db_error}")
            return jsonify({'error': 'Failed to create strategy'}), 500
        
        logger.info(f"Created strategy {strategy.id} for user {g.current_user.id}")
        
        return jsonify({
            'strategy': {
                'id': strategy.id,
                'name': strategy.name,
                'description': strategy.description,
                'strategy_type': strategy.strategy_type,
                'status': 'active' if strategy.is_active else 'paused',
                'created_at': strategy.created_at.isoformat(),
                'parameters': strategy.parameters
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Create strategy error: {e}")
        return jsonify({'error': 'Failed to create strategy'}), 500

@strategy_bp.route('/strategies/user/<int:strategy_id>', methods=['PUT'])
@token_required
@handle_validation_error
def update_user_strategy(strategy_id):
    """Update user strategy (toggle status, update parameters, etc.)"""
    from flask import g
    from ..models.strategy_models import Strategy
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No JSON data provided'}), 400
    
    try:
        strategy = Strategy.query.filter_by(
            id=strategy_id,
            user_id=g.current_user.id
        ).first()
        
        if not strategy:
            return jsonify({'error': 'Strategy not found'}), 404
        
        # Update allowed fields
        if 'name' in data:
            strategy.name = data['name']
        if 'description' in data:
            strategy.description = data['description']
        if 'parameters' in data:
            strategy.parameters = data['parameters']
        if 'status' in data:
            strategy.is_active = data['status'] == 'active'
        if 'is_active' in data:
            strategy.is_active = data['is_active']
            
        strategy.updated_at = datetime.utcnow()
        try:
            db.session.commit()
        except Exception as db_error:
            db.session.rollback()
            logger.error(f"Database error during strategy update: {db_error}")
            return jsonify({'error': 'Failed to update strategy'}), 500
        
        logger.info(f"Updated strategy {strategy_id} for user {g.current_user.id}")
        
        return jsonify({
            'strategy': {
                'id': strategy.id,
                'name': strategy.name,
                'description': strategy.description,
                'strategy_type': strategy.strategy_type,
                'status': 'active' if strategy.is_active else 'paused',
                'updated_at': strategy.updated_at.isoformat(),
                'parameters': strategy.parameters
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Update strategy error: {e}")
        return jsonify({'error': 'Failed to update strategy'}), 500

@strategy_bp.route('/strategies/user/<int:strategy_id>', methods=['DELETE'])
@token_required
@handle_validation_error
def delete_user_strategy(strategy_id):
    """Delete user strategy"""
    from flask import g
    from ..models.strategy_models import Strategy
    
    try:
        strategy = Strategy.query.filter_by(
            id=strategy_id,
            user_id=g.current_user.id
        ).first()
        
        if not strategy:
            return jsonify({'error': 'Strategy not found'}), 404
        
        db.session.delete(strategy)
        db.session.commit()
        
        logger.info(f"Deleted strategy {strategy_id} for user {g.current_user.id}")
        
        return jsonify({'message': 'Strategy deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Delete strategy error: {e}")
        return jsonify({'error': 'Failed to delete strategy'}), 500

@strategy_bp.route('/strategies/user/<int:strategy_id>/execute', methods=['POST'])
@token_required
@handle_validation_error
def execute_user_strategy(strategy_id):
    """Execute a user's created strategy"""
    from flask import g
    from ..models.strategy_models import Strategy
    from ..models.portfolio_models import Portfolio
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No JSON data provided'}), 400
    
    try:
        strategy = Strategy.query.filter_by(
            id=strategy_id,
            user_id=g.current_user.id
        ).first()
        
        if not strategy:
            return jsonify({'error': 'Strategy not found'}), 404
        
        if not strategy.is_active:
            return jsonify({'error': 'Strategy is not active'}), 400
        
        # Get required fields from request
        universe = data.get('universe', [])
        portfolio_id = data.get('portfolio_id')
        
        if not universe or not isinstance(universe, list):
            return jsonify({'error': 'Universe must be a non-empty list of symbols'}), 400
        
        # Validate symbols
        validated_universe = []
        for symbol in universe:
            try:
                validated_symbol = InputValidator.validate_stock_symbol(symbol)
                validated_universe.append(validated_symbol)
            except ValidationError:
                return jsonify({'error': f'Invalid symbol: {symbol}'}), 400
        
        # Get portfolio if specified
        portfolio = None
        if portfolio_id:
            portfolio = Portfolio.query.filter_by(
                id=portfolio_id,
                user_id=g.current_user.id
            ).first()
            if not portfolio:
                return jsonify({'error': 'Portfolio not found'}), 404
        
        # Create strategy instance based on strategy type
        strategy_parameters = strategy.parameters or {}
        
        if strategy.strategy_type == 'moving_average':
            strategy_instance = MovingAverageStrategy(strategy_parameters)
        elif strategy.strategy_type == 'momentum':
            strategy_instance = MomentumStrategy(strategy_parameters)
        elif strategy.strategy_type == 'buy_hold':
            strategy_instance = BuyHoldStrategy(strategy_parameters)
        else:
            return jsonify({'error': f'Unsupported strategy type: {strategy.strategy_type}'}), 400
        
        # Set strategy universe
        strategy_instance.universe = validated_universe
        
        # Get market data for the universe
        stock_service = current_app.stock_service
        market_data = {}
        current_date = datetime.now()
        
        # Fetch historical data for each symbol (last 1 year for indicators)
        end_date = current_date
        start_date = current_date - timedelta(days=365)
        
        for symbol in validated_universe:
            try:
                historical_data = stock_service.fetch_historical_data(
                    symbol, 
                    start_date.strftime('%Y-%m-%d'),
                    end_date.strftime('%Y-%m-%d')
                )
                
                # Convert to DataFrame-like structure
                if 'historical' in historical_data and historical_data['historical']:
                    import pandas as pd
                    df_data = []
                    
                    for record in historical_data['historical']:
                        df_data.append({
                            'date': record['date'],
                            'open': record['open'],
                            'high': record['high'], 
                            'low': record['low'],
                            'close': record['close'],
                            'volume': record['volume']
                        })
                    
                    df = pd.DataFrame(df_data)
                    df['date'] = pd.to_datetime(df['date'])
                    df.set_index('date', inplace=True)
                    df.sort_index(inplace=True)
                    
                    market_data[symbol] = df
                    
            except Exception as e:
                logger.warning(f"Failed to fetch data for {symbol}: {e}")
                continue
        
        if not market_data:
            return jsonify({'error': 'No market data available for specified universe'}), 400
        
        # Create strategy context
        portfolio_value = portfolio.total_value if portfolio else 100000.0  # Default $100k
        cash_balance = portfolio.cash_balance if portfolio else portfolio_value
        positions = {}
        
        if portfolio:
            for position in portfolio.positions:
                if position.is_open:
                    positions[position.symbol] = position.quantity
        
        context = StrategyContext(
            current_date=current_date,
            portfolio_value=portfolio_value,
            cash_balance=cash_balance,
            positions=positions,
            market_data=market_data
        )
        
        # Initialize strategy
        strategy_instance.initialize(validated_universe, start_date, end_date)
        
        # Generate signals
        signals = strategy_instance.generate_signals(context)
        
        # Update strategy statistics
        strategy.total_backtests += 1
        if len(signals) > 0:
            strategy.successful_backtests += 1
        
        db.session.commit()
        
        # Format signals for response
        signals_data = []
        for signal in signals:
            signals_data.append({
                'symbol': signal.symbol,
                'signal_type': signal.signal_type,
                'strength': signal.strength,
                'price': signal.price,
                'quantity': signal.quantity,
                'timestamp': signal.timestamp.isoformat(),
                'reason': signal.reason,
                'metadata': signal.metadata
            })
        
        logger.info(f"Executed user strategy {strategy_id} for user {g.current_user.id}, generated {len(signals)} signals")
        
        return jsonify({
            'strategy_execution': {
                'strategy_id': strategy_id,
                'strategy_name': strategy.name,
                'strategy_type': strategy.strategy_type,
                'universe': validated_universe,
                'parameters': strategy_parameters,
                'execution_time': current_date.isoformat(),
                'portfolio_id': portfolio_id,
                'signals_generated': len(signals)
            },
            'signals': signals_data,
            'context': {
                'portfolio_value': portfolio_value,
                'cash_balance': cash_balance,
                'current_positions': len(positions),
                'data_symbols': list(market_data.keys())
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Strategy execution error: {e}")
        return jsonify({'error': 'Failed to execute strategy'}), 500

@strategy_bp.route('/strategies/user/<int:strategy_id>/performance', methods=['GET'])
@token_required
@handle_validation_error
def get_strategy_performance(strategy_id):
    """Get performance metrics for a user strategy"""
    from flask import g
    from ..models.strategy_models import Strategy, StrategyPerformance
    
    try:
        strategy = Strategy.query.filter_by(
            id=strategy_id,
            user_id=g.current_user.id
        ).first()
        
        if not strategy:
            return jsonify({'error': 'Strategy not found'}), 404
        
        # Get performance record if it exists
        performance_data = {
            'strategy_id': strategy_id,
            'strategy_name': strategy.name,
            'total_backtests': strategy.total_backtests,
            'successful_backtests': strategy.successful_backtests,
            'success_rate': strategy.success_rate,
            'performance_metrics': {}
        }
        
        if strategy.performance:
            perf = strategy.performance
            performance_data['performance_metrics'] = {
                'total_return': float(perf.total_return) if perf.total_return else None,
                'annualized_return': float(perf.annualized_return) if perf.annualized_return else None,
                'volatility': float(perf.volatility) if perf.volatility else None,
                'sharpe_ratio': float(perf.sharpe_ratio) if perf.sharpe_ratio else None,
                'max_drawdown': float(perf.max_drawdown) if perf.max_drawdown else None,
                'win_rate': float(perf.win_rate) if perf.win_rate else None,
                'total_trades': perf.total_trades or 0,
                'last_updated': perf.updated_at.isoformat() if perf.updated_at else None
            }
        
        return jsonify(performance_data), 200
        
    except Exception as e:
        logger.error(f"Get strategy performance error: {e}")
        return jsonify({'error': 'Failed to retrieve strategy performance'}), 500

@strategy_bp.route('/strategies/templates', methods=['GET'])
@token_required
@handle_validation_error
def get_strategy_templates():
    """Get available strategy templates for creating new strategies"""
    try:
        templates = []
        
        # Moving Average Template
        templates.append({
            'id': 'moving_average_template',
            'name': 'Moving Average Crossover',
            'description': 'Classic trend-following strategy using moving average crossovers',
            'strategy_type': 'moving_average',
            'category': 'equity',
            'complexity': 'beginner',
            'risk_level': 'Medium',
            'typical_holding_period': '1-3 months',
            'default_parameters': {
                'fast_period': 20,
                'slow_period': 50,
                'position_size': 0.1,
                'min_volume': 100000
            },
            'parameter_definitions': [
                {
                    'name': 'fast_period',
                    'type': 'integer',
                    'min': 5,
                    'max': 100,
                    'description': 'Fast moving average period'
                },
                {
                    'name': 'slow_period',
                    'type': 'integer',
                    'min': 10,
                    'max': 200,
                    'description': 'Slow moving average period'
                },
                {
                    'name': 'position_size',
                    'type': 'float',
                    'min': 0.01,
                    'max': 1.0,
                    'description': 'Position size as fraction of portfolio'
                },
                {
                    'name': 'min_volume',
                    'type': 'integer',
                    'min': 1000,
                    'max': 10000000,
                    'description': 'Minimum daily volume requirement'
                }
            ],
            'entry_rules': {
                'description': 'Buy when fast MA crosses above slow MA',
                'conditions': ['fast_ma > slow_ma', 'previous_fast_ma <= previous_slow_ma']
            },
            'exit_rules': {
                'description': 'Sell when fast MA crosses below slow MA',
                'conditions': ['fast_ma < slow_ma', 'previous_fast_ma >= previous_slow_ma']
            }
        })
        
        # Momentum Template
        templates.append({
            'id': 'momentum_template',
            'name': 'Momentum Strategy',
            'description': 'Momentum-based strategy that buys top-performing stocks',
            'strategy_type': 'momentum',
            'category': 'equity',
            'complexity': 'intermediate',
            'risk_level': 'High',
            'typical_holding_period': '2-6 weeks',
            'default_parameters': {
                'lookback_period': 20,
                'top_n_stocks': 10,
                'rebalance_frequency': 'monthly'
            },
            'parameter_definitions': [
                {
                    'name': 'lookback_period',
                    'type': 'integer',
                    'min': 5,
                    'max': 100,
                    'description': 'Lookback period for momentum calculation'
                },
                {
                    'name': 'top_n_stocks',
                    'type': 'integer',
                    'min': 1,
                    'max': 50,
                    'description': 'Number of top momentum stocks to hold'
                },
                {
                    'name': 'rebalance_frequency',
                    'type': 'string',
                    'options': ['daily', 'weekly', 'monthly'],
                    'description': 'Portfolio rebalancing frequency'
                }
            ],
            'entry_rules': {
                'description': 'Buy stocks with highest momentum scores',
                'conditions': ['momentum_rank <= top_n_stocks']
            },
            'exit_rules': {
                'description': 'Sell stocks that fall out of top momentum rankings',
                'conditions': ['momentum_rank > top_n_stocks']
            }
        })
        
        # Buy and Hold Template
        templates.append({
            'id': 'buy_hold_template',
            'name': 'Buy and Hold',
            'description': 'Simple long-term investment strategy',
            'strategy_type': 'buy_hold',
            'category': 'equity',
            'complexity': 'beginner',
            'risk_level': 'Low',
            'typical_holding_period': '1+ years',
            'default_parameters': {
                'rebalance_frequency': 'quarterly',
                'equal_weight': True
            },
            'parameter_definitions': [
                {
                    'name': 'rebalance_frequency',
                    'type': 'string',
                    'options': ['monthly', 'quarterly', 'yearly'],
                    'description': 'Portfolio rebalancing frequency'
                },
                {
                    'name': 'equal_weight',
                    'type': 'boolean',
                    'description': 'Use equal weighting for all positions'
                }
            ],
            'entry_rules': {
                'description': 'Buy and hold selected assets',
                'conditions': ['initial_purchase_or_rebalance']
            },
            'exit_rules': {
                'description': 'Only sell during rebalancing',
                'conditions': ['rebalance_date']
            }
        })
        
        return jsonify({
            'templates': templates,
            'total': len(templates)
        }), 200
        
    except Exception as e:
        logger.error(f"Get strategy templates error: {e}")
        return jsonify({'error': 'Failed to retrieve strategy templates'}), 500

@strategy_bp.route('/strategies/from-template/<template_id>', methods=['POST'])
@token_required
@handle_validation_error
def create_strategy_from_template(template_id):
    """Create a new strategy from a template"""
    from flask import g
    from ..models.strategy_models import Strategy
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No JSON data provided'}), 400
    
    try:
        # Template mapping
        template_mapping = {
            'moving_average_template': {
                'strategy_type': 'moving_average',
                'default_parameters': {
                    'fast_period': 20,
                    'slow_period': 50,
                    'position_size': 0.1,
                    'min_volume': 100000
                }
            },
            'momentum_template': {
                'strategy_type': 'momentum',
                'default_parameters': {
                    'lookback_period': 20,
                    'top_n_stocks': 10,
                    'rebalance_frequency': 'monthly'
                }
            },
            'buy_hold_template': {
                'strategy_type': 'buy_hold',
                'default_parameters': {
                    'rebalance_frequency': 'quarterly',
                    'equal_weight': True
                }
            }
        }
        
        if template_id not in template_mapping:
            return jsonify({'error': 'Invalid template ID'}), 400
        
        template = template_mapping[template_id]
        
        # Get strategy name (required)
        if 'name' not in data or not data['name'].strip():
            return jsonify({'error': 'Strategy name is required'}), 400
        
        # Merge parameters (user parameters override defaults)
        parameters = template['default_parameters'].copy()
        if 'parameters' in data:
            parameters.update(data['parameters'])
        
        # Create strategy from template
        strategy = Strategy(
            user_id=g.current_user.id,
            name=data['name'].strip(),
            description=data.get('description', f'Strategy created from {template_id}'),
            strategy_type=template['strategy_type'],
            category=data.get('category', 'equity'),
            complexity=data.get('complexity', 'intermediate'),
            parameters=parameters,
            entry_rules=data.get('entry_rules', {}),
            exit_rules=data.get('exit_rules', {}),
            risk_rules=data.get('risk_rules', {}),
            is_active=data.get('is_active', True),
            tags=data.get('tags', [])
        )
        
        try:
            db.session.add(strategy)
            db.session.commit()
        except Exception as db_error:
            db.session.rollback()
            logger.error(f"Database error during strategy creation from template: {db_error}")
            return jsonify({'error': 'Failed to create strategy from template'}), 500
        
        logger.info(f"Created strategy from template {template_id} for user {g.current_user.id}")
        
        return jsonify({
            'strategy': {
                'id': strategy.id,
                'name': strategy.name,
                'description': strategy.description,
                'strategy_type': strategy.strategy_type,
                'parameters': strategy.parameters,
                'status': 'active' if strategy.is_active else 'paused',
                'created_at': strategy.created_at.isoformat()
            },
            'template_used': template_id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Create strategy from template error: {e}")
        return jsonify({'error': 'Failed to create strategy from template'}), 500