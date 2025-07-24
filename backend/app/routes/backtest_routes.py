"""
Backtest API routes
"""
from flask import Blueprint, request, jsonify, current_app
from ..db import db
from ..models.backtest_models import Backtest, BacktestPerformance
from ..auth.decorators import token_required
from ..utils.validation import InputValidator, ValidationError, handle_validation_error
from ..services.backtesting.engine import BacktestingEngine, BacktestConfig, BacktestResults
from ..services.data.data_provider import StockServiceDataProvider
from ..services.strategies.builtins.moving_average import MovingAverageStrategy
from ..services.strategies.builtins.momentum import MomentumStrategy
from ..services.strategies.builtins.buy_hold import BuyHoldStrategy
import logging
from datetime import datetime, timedelta
import json
import threading
import uuid

backtest_bp = Blueprint('backtest', __name__)
logger = logging.getLogger(__name__)

# Global dictionary to track running backtests
running_backtests = {}

@backtest_bp.route('/backtests', methods=['POST'])
@token_required
@handle_validation_error
def create_backtest():
    """Run a new backtest"""
    from flask import g
    
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No JSON data provided'}), 400
    
    try:
        # Validate required fields
        required_fields = ['name', 'strategy_id', 'start_date', 'end_date', 'initial_capital', 'universe']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Validate dates
        try:
            start_date = datetime.strptime(data['start_date'], '%Y-%m-%d')
            end_date = datetime.strptime(data['end_date'], '%Y-%m-%d')
            
            if start_date >= end_date:
                return jsonify({'error': 'start_date must be before end_date'}), 400
            
            if end_date > datetime.now():
                return jsonify({'error': 'end_date cannot be in the future'}), 400
                
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        # Validate initial capital
        try:
            initial_capital = float(data['initial_capital'])
            if initial_capital <= 0:
                raise ValueError("Initial capital must be positive")
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid initial capital'}), 400
        
        # Validate strategy
        strategy_id = data['strategy_id']
        if strategy_id not in ['moving_average', 'momentum', 'buy_hold']:
            return jsonify({'error': 'Invalid strategy_id'}), 400
        
        # Validate universe
        universe = data['universe']
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
        
        # Get optional parameters
        strategy_parameters = data.get('strategy_parameters', {})
        commission_rate = float(data.get('commission_rate', 0.001))
        slippage_rate = float(data.get('slippage_rate', 0.0005))
        benchmark_symbol = data.get('benchmark_symbol', 'SPY')
        
        # Create backtest record
        backtest = Backtest(
            user_id=g.current_user.id,
            strategy_id=1,  # We'll use a fixed strategy_id for now since strategies table doesn't exist
            name=data['name'].strip(),
            description=data.get('description'),
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
            commission_rate=commission_rate,
            slippage_rate=slippage_rate,
            benchmark_symbol=benchmark_symbol,
            strategy_parameters=json.dumps(strategy_parameters) if strategy_parameters else None,
            status='pending'
        )
        
        db.session.add(backtest)
        db.session.commit()
        
        # Start backtest in background thread
        backtest_thread = threading.Thread(
            target=_run_backtest_async,
            args=(backtest.id, strategy_id, validated_universe, strategy_parameters)
        )
        backtest_thread.daemon = True
        backtest_thread.start()
        
        logger.info(f"Backtest created: {backtest.name} for user {g.current_user.id}")
        
        return jsonify({
            'message': 'Backtest started successfully',
            'backtest': {
                'id': backtest.id,
                'name': backtest.name,
                'description': backtest.description,
                'strategy_id': strategy_id,
                'start_date': backtest.start_date.isoformat(),
                'end_date': backtest.end_date.isoformat(),
                'initial_capital': backtest.initial_capital,
                'universe': validated_universe,
                'status': backtest.status,
                'created_at': backtest.created_at.isoformat()
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Backtest creation error: {e}")
        return jsonify({'error': 'Failed to create backtest'}), 500

def _run_backtest_async(backtest_id, strategy_id, universe, strategy_parameters):
    """Run backtest asynchronously"""
    try:
        with current_app.app_context():
            # Get backtest from database
            backtest = Backtest.query.get(backtest_id)
            if not backtest:
                return
            
            # Update status to running
            backtest.status = 'running'
            backtest.started_at = datetime.utcnow()
            db.session.commit()
            
            # Create strategy instance
            if strategy_id == 'moving_average':
                strategy = MovingAverageStrategy(strategy_parameters)
            elif strategy_id == 'momentum':
                strategy = MomentumStrategy(strategy_parameters)
            elif strategy_id == 'buy_hold':
                strategy = BuyHoldStrategy(strategy_parameters)
            else:
                raise ValueError(f"Unknown strategy: {strategy_id}")
            
            # Create backtest configuration
            config = BacktestConfig(
                start_date=backtest.start_date,
                end_date=backtest.end_date,
                initial_capital=backtest.initial_capital,
                universe=universe,
                commission_rate=backtest.commission_rate,
                slippage_rate=backtest.slippage_rate,
                benchmark_symbol=backtest.benchmark_symbol or 'SPY'
            )
            
            # Create data provider (using current stock service)
            stock_service = current_app.stock_service
            data_provider = StockServiceDataProvider(stock_service)
            
            # Create and run backtest engine
            engine = BacktestingEngine(data_provider)
            
            # Set progress callback
            def progress_callback(progress):
                backtest.progress = progress
                db.session.commit()
            
            engine.set_progress_callback(progress_callback)
            
            # Run backtest
            results = engine.run_backtest(strategy, config)
            
            # Update backtest with results
            backtest.status = 'completed'
            backtest.completed_at = datetime.utcnow()
            backtest.execution_time = results.execution_time
            backtest.progress = 100.0
            
            # Store performance metrics
            backtest.total_return = results.total_return
            backtest.annualized_return = results.annualized_return
            backtest.volatility = results.volatility
            backtest.sharpe_ratio = results.sharpe_ratio
            backtest.max_drawdown = results.max_drawdown
            backtest.total_trades = results.total_trades
            backtest.win_rate = results.win_rate
            
            # Create detailed performance record
            performance = BacktestPerformance(
                backtest_id=backtest.id,
                total_return=results.total_return,
                annualized_return=results.annualized_return,
                volatility=results.volatility,
                sharpe_ratio=results.sharpe_ratio,
                max_drawdown=results.max_drawdown,
                total_trades=results.total_trades,
                winning_trades=results.winning_trades,
                losing_trades=results.losing_trades,
                win_rate=results.win_rate,
                avg_win=results.avg_win,
                avg_loss=results.avg_loss,
                profit_factor=results.profit_factor,
                benchmark_return=results.benchmark_return,
                alpha=results.alpha,
                beta=results.beta
            )
            
            db.session.add(performance)
            db.session.commit()
            
            logger.info(f"Backtest completed: {backtest.id}")
            
    except Exception as e:
        logger.error(f"Backtest execution error: {e}")
        
        # Update backtest status to failed
        try:
            with current_app.app_context():
                backtest = Backtest.query.get(backtest_id)
                if backtest:
                    backtest.status = 'failed'
                    backtest.error_message = str(e)
                    backtest.completed_at = datetime.utcnow()
                    db.session.commit()
        except:
            pass

@backtest_bp.route('/backtests', methods=['GET'])
@token_required
@handle_validation_error
def get_backtests():
    """Get user backtests"""
    from flask import g
    
    try:
        # Get query parameters
        status = request.args.get('status')
        strategy_id = request.args.get('strategy_id')
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Build query
        query = Backtest.query.filter_by(user_id=g.current_user.id)
        
        # Apply filters
        if status:
            query = query.filter(Backtest.status == status)
        if strategy_id:
            # For now, we'll filter by strategy parameters since we don't have a strategies table
            pass
        
        # Apply pagination and ordering
        query = query.order_by(Backtest.created_at.desc())
        total_count = query.count()
        backtests = query.offset(offset).limit(min(limit, 100)).all()
        
        # Format response
        backtests_data = []
        for backtest in backtests:
            backtests_data.append({
                'id': backtest.id,
                'name': backtest.name,
                'description': backtest.description,
                'start_date': backtest.start_date.isoformat(),
                'end_date': backtest.end_date.isoformat(),
                'initial_capital': backtest.initial_capital,
                'status': backtest.status,
                'progress': backtest.progress,
                'total_return': backtest.total_return,
                'sharpe_ratio': backtest.sharpe_ratio,
                'max_drawdown': backtest.max_drawdown,
                'total_trades': backtest.total_trades,
                'win_rate': backtest.win_rate,
                'execution_time': backtest.execution_time,
                'created_at': backtest.created_at.isoformat(),
                'started_at': backtest.started_at.isoformat() if backtest.started_at else None,
                'completed_at': backtest.completed_at.isoformat() if backtest.completed_at else None
            })
        
        return jsonify({
            'backtests': backtests_data,
            'pagination': {
                'total': total_count,
                'offset': offset,
                'limit': limit,
                'has_more': (offset + limit) < total_count
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get backtests error: {e}")
        return jsonify({'error': 'Failed to retrieve backtests'}), 500

@backtest_bp.route('/backtests/<int:backtest_id>', methods=['GET'])
@token_required
@handle_validation_error
def get_backtest_results(backtest_id):
    """Get detailed backtest results"""
    from flask import g
    
    try:
        # Find backtest
        backtest = Backtest.query.filter_by(
            id=backtest_id,
            user_id=g.current_user.id
        ).first()
        
        if not backtest:
            return jsonify({'error': 'Backtest not found'}), 404
        
        # Get performance details
        performance = BacktestPerformance.query.filter_by(backtest_id=backtest_id).first()
        
        # Parse strategy parameters
        strategy_parameters = {}
        if backtest.strategy_parameters:
            try:
                strategy_parameters = json.loads(backtest.strategy_parameters) if isinstance(backtest.strategy_parameters, str) else backtest.strategy_parameters
            except:
                pass
        
        # Build response
        response_data = {
            'backtest': {
                'id': backtest.id,
                'name': backtest.name,
                'description': backtest.description,
                'start_date': backtest.start_date.isoformat(),
                'end_date': backtest.end_date.isoformat(),
                'initial_capital': backtest.initial_capital,
                'commission_rate': backtest.commission_rate,
                'slippage_rate': backtest.slippage_rate,
                'benchmark_symbol': backtest.benchmark_symbol,
                'strategy_parameters': strategy_parameters,
                'status': backtest.status,
                'progress': backtest.progress,
                'execution_time': backtest.execution_time,
                'error_message': backtest.error_message,
                'created_at': backtest.created_at.isoformat(),
                'started_at': backtest.started_at.isoformat() if backtest.started_at else None,
                'completed_at': backtest.completed_at.isoformat() if backtest.completed_at else None
            }
        }
        
        # Add performance metrics if available
        if performance:
            response_data['performance'] = {
                'returns': {
                    'total_return': performance.total_return,
                    'annualized_return': performance.annualized_return,
                    'benchmark_return': performance.benchmark_return,
                    'alpha': performance.alpha,
                    'beta': performance.beta
                },
                'risk': {
                    'volatility': performance.volatility,
                    'max_drawdown': performance.max_drawdown,
                    'sharpe_ratio': performance.sharpe_ratio,
                    'sortino_ratio': performance.sortino_ratio,
                    'calmar_ratio': performance.calmar_ratio
                },
                'trades': {
                    'total_trades': performance.total_trades,
                    'winning_trades': performance.winning_trades,
                    'losing_trades': performance.losing_trades,
                    'win_rate': performance.win_rate,
                    'avg_win': performance.avg_win,
                    'avg_loss': performance.avg_loss,
                    'profit_factor': performance.profit_factor,
                    'avg_holding_period': performance.avg_holding_period
                }
            }
        else:
            # Use basic metrics from backtest table
            response_data['performance'] = {
                'returns': {
                    'total_return': backtest.total_return,
                    'annualized_return': backtest.annualized_return
                },
                'risk': {
                    'volatility': backtest.volatility,
                    'max_drawdown': backtest.max_drawdown,
                    'sharpe_ratio': backtest.sharpe_ratio
                },
                'trades': {
                    'total_trades': backtest.total_trades,
                    'win_rate': backtest.win_rate
                }
            }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Get backtest results error: {e}")
        return jsonify({'error': 'Failed to retrieve backtest results'}), 500

@backtest_bp.route('/backtests/<int:backtest_id>/status', methods=['GET'])
@token_required
@handle_validation_error
def get_backtest_status(backtest_id):
    """Get backtest status and progress"""
    from flask import g
    
    try:
        # Find backtest
        backtest = Backtest.query.filter_by(
            id=backtest_id,
            user_id=g.current_user.id
        ).first()
        
        if not backtest:
            return jsonify({'error': 'Backtest not found'}), 404
        
        return jsonify({
            'id': backtest.id,
            'status': backtest.status,
            'progress': backtest.progress,
            'started_at': backtest.started_at.isoformat() if backtest.started_at else None,
            'completed_at': backtest.completed_at.isoformat() if backtest.completed_at else None,
            'execution_time': backtest.execution_time,
            'error_message': backtest.error_message
        }), 200
        
    except Exception as e:
        logger.error(f"Get backtest status error: {e}")
        return jsonify({'error': 'Failed to retrieve backtest status'}), 500

@backtest_bp.route('/backtests/<int:backtest_id>', methods=['DELETE'])
@token_required
@handle_validation_error
def delete_backtest(backtest_id):
    """Delete a backtest"""
    from flask import g
    
    try:
        # Find backtest
        backtest = Backtest.query.filter_by(
            id=backtest_id,
            user_id=g.current_user.id
        ).first()
        
        if not backtest:
            return jsonify({'error': 'Backtest not found'}), 404
        
        # Don't allow deletion of running backtests
        if backtest.status == 'running':
            return jsonify({'error': 'Cannot delete running backtest'}), 400
        
        # Delete backtest (cascade will handle related records)
        db.session.delete(backtest)
        db.session.commit()
        
        logger.info(f"Backtest deleted: ID {backtest_id}")
        
        return jsonify({'message': 'Backtest deleted successfully'}), 200
        
    except Exception as e:
        logger.error(f"Backtest deletion error: {e}")
        return jsonify({'error': 'Failed to delete backtest'}), 500

@backtest_bp.route('/backtests/compare', methods=['POST'])
@token_required
@handle_validation_error
def compare_backtests():
    """Compare multiple backtests"""
    from flask import g
    
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No JSON data provided'}), 400
    
    try:
        backtest_ids = data.get('backtest_ids', [])
        
        if not isinstance(backtest_ids, list) or len(backtest_ids) < 2:
            return jsonify({'error': 'Must provide at least 2 backtest IDs for comparison'}), 400
        
        # Get backtests
        backtests = Backtest.query.filter(
            Backtest.id.in_(backtest_ids),
            Backtest.user_id == g.current_user.id,
            Backtest.status == 'completed'
        ).all()
        
        if len(backtests) != len(backtest_ids):
            return jsonify({'error': 'Some backtests not found or not completed'}), 400
        
        # Get performance data
        performance_data = BacktestPerformance.query.filter(
            BacktestPerformance.backtest_id.in_(backtest_ids)
        ).all()
        
        performance_map = {p.backtest_id: p for p in performance_data}
        
        # Build comparison data
        comparison_data = []
        for backtest in backtests:
            performance = performance_map.get(backtest.id)
            
            comparison_data.append({
                'backtest_id': backtest.id,
                'name': backtest.name,
                'total_return': performance.total_return if performance else backtest.total_return,
                'annualized_return': performance.annualized_return if performance else backtest.annualized_return,
                'volatility': performance.volatility if performance else backtest.volatility,
                'sharpe_ratio': performance.sharpe_ratio if performance else backtest.sharpe_ratio,
                'max_drawdown': performance.max_drawdown if performance else backtest.max_drawdown,
                'total_trades': performance.total_trades if performance else backtest.total_trades,
                'win_rate': performance.win_rate if performance else backtest.win_rate,
                'profit_factor': performance.profit_factor if performance else None
            })
        
        # Find best performer (by Sharpe ratio)
        best_performer = max(comparison_data, key=lambda x: x['sharpe_ratio'] or -999)
        
        return jsonify({
            'comparison': comparison_data,
            'best_performer': best_performer,
            'metrics': {
                'comparison_date': datetime.utcnow().isoformat(),
                'comparison_criteria': 'sharpe_ratio',
                'total_backtests': len(comparison_data)
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Backtest comparison error: {e}")
        return jsonify({'error': 'Failed to compare backtests'}), 500