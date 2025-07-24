"""
Portfolio Management API routes
"""
from flask import Blueprint, request, jsonify, current_app
from ..db import db
from ..models.portfolio_models import Portfolio, Position, Transaction
from ..auth.decorators import token_required
from ..utils.validation import InputValidator, ValidationError, handle_validation_error
import logging
from datetime import datetime

portfolio_bp = Blueprint('portfolio', __name__)
logger = logging.getLogger(__name__)

@portfolio_bp.route('/portfolios', methods=['POST'])
@token_required
@handle_validation_error
def create_portfolio():
    """Create a new portfolio"""
    from flask import g
    
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No JSON data provided'}), 400
    
    try:
        # Validate required fields
        required_fields = ['name', 'initial_capital']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Validate initial capital
        try:
            initial_capital = float(data['initial_capital'])
            if initial_capital <= 0:
                raise ValueError("Initial capital must be positive")
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid initial capital'}), 400
        
        # Validate portfolio type
        portfolio_type = data.get('portfolio_type', 'paper')
        if portfolio_type not in ['paper', 'live', 'backtest']:
            return jsonify({'error': 'portfolio_type must be paper, live, or backtest'}), 400
        
        # Create portfolio
        portfolio = Portfolio(
            user_id=g.current_user.id,
            name=data['name'].strip(),
            description=data.get('description'),
            portfolio_type=portfolio_type,
            initial_capital=initial_capital,
            current_capital=initial_capital,
            cash_balance=initial_capital,
            total_value=initial_capital,
            currency=data.get('currency', 'USD')
        )
        
        db.session.add(portfolio)
        db.session.commit()
        
        logger.info(f"Portfolio created: {portfolio.name} for user {g.current_user.id}")
        
        return jsonify({
            'message': 'Portfolio created successfully',
            'portfolio': {
                'id': portfolio.id,
                'name': portfolio.name,
                'description': portfolio.description,
                'portfolio_type': portfolio.portfolio_type,
                'initial_capital': portfolio.initial_capital,
                'current_capital': portfolio.current_capital,
                'cash_balance': portfolio.cash_balance,
                'total_value': portfolio.total_value,
                'total_return': portfolio.total_return,
                'currency': portfolio.currency,
                'is_active': portfolio.is_active,
                'created_at': portfolio.created_at.isoformat()
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Portfolio creation error: {e}")
        return jsonify({'error': 'Failed to create portfolio'}), 500

@portfolio_bp.route('/portfolios', methods=['GET'])
@token_required
@handle_validation_error
def get_portfolios():
    """Get user portfolios"""
    from flask import g
    
    try:
        # Get query parameters
        portfolio_type = request.args.get('portfolio_type')
        is_active = request.args.get('is_active')
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Build query
        query = Portfolio.query.filter_by(user_id=g.current_user.id)
        
        # Apply filters
        if portfolio_type:
            query = query.filter(Portfolio.portfolio_type == portfolio_type)
        if is_active is not None:
            active_flag = is_active.lower() == 'true'
            query = query.filter(Portfolio.is_active == active_flag)
        
        # Apply pagination and ordering
        query = query.order_by(Portfolio.created_at.desc())
        total_count = query.count()
        portfolios = query.offset(offset).limit(min(limit, 100)).all()
        
        # Format response
        portfolios_data = []
        for portfolio in portfolios:
            portfolios_data.append({
                'id': portfolio.id,
                'name': portfolio.name,
                'description': portfolio.description,
                'portfolio_type': portfolio.portfolio_type,
                'initial_capital': portfolio.initial_capital,
                'current_capital': portfolio.current_capital,
                'cash_balance': portfolio.cash_balance,
                'total_value': portfolio.total_value,
                'total_return': portfolio.total_return,
                'unrealized_pnl': portfolio.unrealized_pnl,
                'realized_pnl': portfolio.realized_pnl,
                'currency': portfolio.currency,
                'is_active': portfolio.is_active,
                'num_positions': len([p for p in portfolio.positions if p.is_open]),
                'last_updated': portfolio.last_updated.isoformat(),
                'created_at': portfolio.created_at.isoformat()
            })
        
        return jsonify({
            'portfolios': portfolios_data,
            'pagination': {
                'total': total_count,
                'offset': offset,
                'limit': limit,
                'has_more': (offset + limit) < total_count
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get portfolios error: {e}")
        return jsonify({'error': 'Failed to retrieve portfolios'}), 500

@portfolio_bp.route('/portfolios/<int:portfolio_id>', methods=['GET'])
@token_required
@handle_validation_error
def get_portfolio_details(portfolio_id):
    """Get portfolio details with holdings"""
    from flask import g
    
    try:
        # Find portfolio
        portfolio = Portfolio.query.filter_by(
            id=portfolio_id, 
            user_id=g.current_user.id
        ).first()
        
        if not portfolio:
            return jsonify({'error': 'Portfolio not found'}), 404
        
        # Get positions
        positions_data = []
        for position in portfolio.positions:
            if position.is_open:
                positions_data.append({
                    'id': position.id,
                    'symbol': position.symbol,
                    'side': position.side,
                    'quantity': position.quantity,
                    'avg_entry_price': position.avg_entry_price,
                    'current_price': position.current_price,
                    'cost_basis': position.cost_basis,
                    'market_value': position.market_value,
                    'unrealized_pnl': position.unrealized_pnl,
                    'unrealized_pnl_pct': position.unrealized_pnl_pct,
                    'position_weight': position.position_weight,
                    'first_entry_date': position.first_entry_date.isoformat(),
                    'last_update_date': position.last_update_date.isoformat()
                })
        
        # Calculate portfolio metrics
        portfolio.calculate_portfolio_value()
        
        return jsonify({
            'portfolio': {
                'id': portfolio.id,
                'name': portfolio.name,
                'description': portfolio.description,
                'portfolio_type': portfolio.portfolio_type,
                'initial_capital': portfolio.initial_capital,
                'current_capital': portfolio.current_capital,
                'cash_balance': portfolio.cash_balance,
                'invested_value': portfolio.invested_value,
                'total_value': portfolio.total_value,
                'total_return': portfolio.total_return,
                'unrealized_pnl': portfolio.unrealized_pnl,
                'realized_pnl': portfolio.realized_pnl,
                'max_drawdown': portfolio.max_drawdown,
                'volatility': portfolio.volatility,
                'sharpe_ratio': portfolio.sharpe_ratio,
                'currency': portfolio.currency,
                'is_active': portfolio.is_active,
                'last_updated': portfolio.last_updated.isoformat(),
                'created_at': portfolio.created_at.isoformat()
            },
            'positions': positions_data,
            'summary': {
                'total_positions': len(positions_data),
                'cash_percentage': (portfolio.cash_balance / portfolio.total_value * 100) if portfolio.total_value > 0 else 0,
                'invested_percentage': (portfolio.invested_value / portfolio.total_value * 100) if portfolio.total_value > 0 else 0
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get portfolio details error: {e}")
        return jsonify({'error': 'Failed to retrieve portfolio details'}), 500

@portfolio_bp.route('/portfolios/<int:portfolio_id>', methods=['PUT'])
@token_required
@handle_validation_error
def update_portfolio(portfolio_id):
    """Update portfolio"""
    from flask import g
    
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No JSON data provided'}), 400
    
    try:
        # Find portfolio
        portfolio = Portfolio.query.filter_by(
            id=portfolio_id, 
            user_id=g.current_user.id
        ).first()
        
        if not portfolio:
            return jsonify({'error': 'Portfolio not found'}), 404
        
        # Update allowed fields
        if 'name' in data:
            portfolio.name = data['name'].strip()
        
        if 'description' in data:
            portfolio.description = data['description']
        
        if 'is_active' in data:
            portfolio.is_active = bool(data['is_active'])
        
        portfolio.last_updated = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"Portfolio updated: ID {portfolio_id}")
        
        return jsonify({
            'message': 'Portfolio updated successfully',
            'portfolio': {
                'id': portfolio.id,
                'name': portfolio.name,
                'description': portfolio.description,
                'portfolio_type': portfolio.portfolio_type,
                'initial_capital': portfolio.initial_capital,
                'current_capital': portfolio.current_capital,
                'cash_balance': portfolio.cash_balance,
                'total_value': portfolio.total_value,
                'total_return': portfolio.total_return,
                'currency': portfolio.currency,
                'is_active': portfolio.is_active,
                'last_updated': portfolio.last_updated.isoformat()
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Portfolio update error: {e}")
        return jsonify({'error': 'Failed to update portfolio'}), 500

@portfolio_bp.route('/portfolios/<int:portfolio_id>', methods=['DELETE'])
@token_required
@handle_validation_error
def delete_portfolio(portfolio_id):
    """Delete portfolio"""
    from flask import g
    
    try:
        # Find portfolio
        portfolio = Portfolio.query.filter_by(
            id=portfolio_id, 
            user_id=g.current_user.id
        ).first()
        
        if not portfolio:
            return jsonify({'error': 'Portfolio not found'}), 404
        
        # Check if portfolio has open positions
        open_positions = [p for p in portfolio.positions if p.is_open]
        if open_positions:
            return jsonify({
                'error': 'Cannot delete portfolio with open positions',
                'open_positions': len(open_positions)
            }), 400
        
        # Delete portfolio (cascade will handle related records)
        db.session.delete(portfolio)
        db.session.commit()
        
        logger.info(f"Portfolio deleted: ID {portfolio_id}")
        
        return jsonify({'message': 'Portfolio deleted successfully'}), 200
        
    except Exception as e:
        logger.error(f"Portfolio deletion error: {e}")
        return jsonify({'error': 'Failed to delete portfolio'}), 500

@portfolio_bp.route('/portfolios/<int:portfolio_id>/positions', methods=['GET'])
@token_required
@handle_validation_error
def get_portfolio_positions(portfolio_id):
    """Get detailed portfolio positions"""
    from flask import g
    
    try:
        # Find portfolio
        portfolio = Portfolio.query.filter_by(
            id=portfolio_id, 
            user_id=g.current_user.id
        ).first()
        
        if not portfolio:
            return jsonify({'error': 'Portfolio not found'}), 404
        
        # Get query parameters
        include_closed = request.args.get('include_closed', 'false').lower() == 'true'
        
        # Get positions
        query = Position.query.filter_by(portfolio_id=portfolio_id)
        if not include_closed:
            query = query.filter(Position.is_open == True)
        
        positions = query.order_by(Position.market_value.desc()).all()
        
        positions_data = []
        for position in positions:
            positions_data.append({
                'id': position.id,
                'symbol': position.symbol,
                'side': position.side,
                'quantity': position.quantity,
                'avg_entry_price': position.avg_entry_price,
                'current_price': position.current_price,
                'cost_basis': position.cost_basis,
                'market_value': position.market_value,
                'unrealized_pnl': position.unrealized_pnl,
                'unrealized_pnl_pct': position.unrealized_pnl_pct,
                'realized_pnl': position.realized_pnl,
                'position_weight': position.position_weight,
                'max_position_value': position.max_position_value,
                'max_adverse_excursion': position.max_adverse_excursion,
                'max_favorable_excursion': position.max_favorable_excursion,
                'first_entry_date': position.first_entry_date.isoformat(),
                'last_update_date': position.last_update_date.isoformat(),
                'is_open': position.is_open
            })
        
        return jsonify({
            'positions': positions_data,
            'summary': {
                'total_positions': len(positions_data),
                'open_positions': len([p for p in positions if p.is_open]),
                'closed_positions': len([p for p in positions if not p.is_open])
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get portfolio positions error: {e}")
        return jsonify({'error': 'Failed to retrieve portfolio positions'}), 500

@portfolio_bp.route('/portfolios/<int:portfolio_id>/performance', methods=['GET'])
@token_required
@handle_validation_error
def get_portfolio_performance(portfolio_id):
    """Get portfolio performance metrics"""
    from flask import g
    
    try:
        # Find portfolio
        portfolio = Portfolio.query.filter_by(
            id=portfolio_id, 
            user_id=g.current_user.id
        ).first()
        
        if not portfolio:
            return jsonify({'error': 'Portfolio not found'}), 404
        
        # Calculate current performance metrics
        portfolio.calculate_portfolio_value()
        
        # Get recent snapshots for performance history
        recent_snapshots = portfolio.snapshots[-30:]  # Last 30 snapshots
        
        snapshot_data = []
        for snapshot in recent_snapshots:
            snapshot_data.append({
                'date': snapshot.snapshot_date.isoformat(),
                'total_value': snapshot.total_value,
                'cash_balance': snapshot.cash_balance,
                'invested_value': snapshot.invested_value,
                'daily_return': snapshot.daily_return,
                'cumulative_return': snapshot.cumulative_return,
                'unrealized_pnl': snapshot.unrealized_pnl,
                'realized_pnl': snapshot.realized_pnl,
                'drawdown': snapshot.drawdown
            })
        
        return jsonify({
            'performance': {
                'initial_capital': portfolio.initial_capital,
                'current_value': portfolio.total_value,
                'total_return': portfolio.total_return,
                'total_return_pct': ((portfolio.total_value - portfolio.initial_capital) / portfolio.initial_capital * 100) if portfolio.initial_capital > 0 else 0,
                'unrealized_pnl': portfolio.unrealized_pnl,
                'realized_pnl': portfolio.realized_pnl,
                'max_drawdown': portfolio.max_drawdown,
                'volatility': portfolio.volatility,
                'sharpe_ratio': portfolio.sharpe_ratio,
                'cash_balance': portfolio.cash_balance,
                'invested_value': portfolio.invested_value
            },
            'history': snapshot_data
        }), 200
        
    except Exception as e:
        logger.error(f"Get portfolio performance error: {e}")
        return jsonify({'error': 'Failed to retrieve portfolio performance'}), 500