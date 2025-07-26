"""
Paper Trading API routes
"""
from flask import Blueprint, request, jsonify, current_app, g
from ..models.portfolio_models import Portfolio, Position, Transaction
from ..auth.decorators import token_required
from ..utils.validation import InputValidator, ValidationError, handle_validation_error
from ..db import db
import logging
from datetime import datetime
from decimal import Decimal

trading_bp = Blueprint('trading', __name__)
logger = logging.getLogger(__name__)

@trading_bp.route('/trade', methods=['POST'])
@token_required
@handle_validation_error
def execute_trade():
    """Execute a paper trade"""
    from flask import g
    
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No JSON data provided'}), 400
    
    try:
        # Validate required fields
        required_fields = ['portfolio_id', 'symbol', 'side', 'quantity']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        portfolio_id = data['portfolio_id']
        symbol = data['symbol'].strip().upper()
        side = data['side'].upper()
        quantity = float(data['quantity'])
        order_type = data.get('order_type', 'MARKET').upper()
        limit_price = data.get('limit_price')
        
        # Validate inputs
        if side not in ['BUY', 'SELL']:
            return jsonify({'error': 'side must be BUY or SELL'}), 400
        
        if quantity <= 0:
            return jsonify({'error': 'quantity must be positive'}), 400
        
        if order_type not in ['MARKET', 'LIMIT']:
            return jsonify({'error': 'order_type must be MARKET or LIMIT'}), 400
        
        if order_type == 'LIMIT' and not limit_price:
            return jsonify({'error': 'limit_price required for LIMIT orders'}), 400
        
        # Validate symbol
        try:
            validated_symbol = InputValidator.validate_stock_symbol(symbol)
        except ValidationError:
            return jsonify({'error': f'Invalid symbol: {symbol}'}), 400
        
        # Find portfolio
        portfolio = Portfolio.query.filter_by(
            id=portfolio_id,
            user_id=g.current_user.id,
            is_active=True
        ).first()
        
        if not portfolio:
            return jsonify({'error': 'Portfolio not found or inactive'}), 404
        
        # Get current stock price
        stock_service = current_app.stock_service
        try:
            quote_data = stock_service.fetch_stock_data(validated_symbol)
            
            # Handle different possible field names for price
            current_price = None
            if quote_data:
                if 'price' in quote_data:
                    current_price = float(quote_data['price'])
                elif 'c' in quote_data:
                    current_price = float(quote_data['c'])
                elif 'close' in quote_data:
                    current_price = float(quote_data['close'])
            
            if not current_price:
                return jsonify({'error': f'Unable to get current price for {validated_symbol}'}), 400
            
            # For market orders, use current price. For limit orders, use limit price
            execution_price = current_price if order_type == 'MARKET' else float(limit_price)
            
            # For limit orders, check if they would execute immediately
            if order_type == 'LIMIT':
                if (side == 'BUY' and limit_price < current_price) or \
                   (side == 'SELL' and limit_price > current_price):
                    return jsonify({
                        'error': f'Limit order would not execute immediately. Current price: ${current_price:.2f}, Limit price: ${limit_price:.2f}'
                    }), 400
            
        except Exception as e:
            logger.error(f"Failed to get quote for {validated_symbol}: {e}")
            return jsonify({'error': f'Failed to get current price for {validated_symbol}'}), 500
        
        # Calculate trade value
        trade_value = quantity * execution_price
        commission = trade_value * 0.001  # 0.1% commission
        total_cost = trade_value + commission if side == 'BUY' else trade_value - commission
        
        # Check if it's a BUY order and user has enough cash
        if side == 'BUY':
            if portfolio.cash_balance < total_cost:
                return jsonify({
                    'error': f'Insufficient funds. Required: ${total_cost:.2f}, Available: ${portfolio.cash_balance:.2f}'
                }), 400
        
        # For SELL orders, check if user has enough shares
        if side == 'SELL':
            existing_position = Position.query.filter_by(
                portfolio_id=portfolio_id,
                symbol=validated_symbol,
                is_open=True
            ).first()
            
            current_quantity = existing_position.quantity if existing_position else 0
            if current_quantity < quantity:
                return jsonify({
                    'error': f'Insufficient shares. Trying to sell {quantity}, but only have {current_quantity}'
                }), 400
        
        # Execute the trade
        transaction = Transaction(
            portfolio_id=portfolio_id,
            symbol=validated_symbol,
            transaction_type=side,
            quantity=quantity,
            price=execution_price,
            total_value=trade_value,
            commission=commission,
            transaction_date=datetime.utcnow(),
            cash_impact=total_cost if side == 'BUY' else -(trade_value - commission),
            status='FILLED'
        )
        
        try:
            db.session.add(transaction)
        
            # Update portfolio cash balance
            if side == 'BUY':
                portfolio.cash_balance -= total_cost
            else:  # SELL
                portfolio.cash_balance += (trade_value - commission)
        
            # Update or create position
            position = Position.query.filter_by(
                portfolio_id=portfolio_id,
                symbol=validated_symbol,
                is_open=True
            ).first()
            
            if not position:
                # Create new position for BUY orders
                if side == 'BUY':
                    position = Position(
                        portfolio_id=portfolio_id,
                        symbol=validated_symbol,
                        side='LONG',
                        quantity=quantity,
                        avg_entry_price=execution_price,
                        cost_basis=trade_value,
                        current_price=current_price,
                        market_value=quantity * current_price,
                        unrealized_pnl=(current_price - execution_price) * quantity,
                        first_entry_date=datetime.utcnow(),
                        last_update_date=datetime.utcnow(),
                        is_open=True
                    )
                    db.session.add(position)
            else:
                # Update existing position
                if side == 'BUY':
                    # Add to existing position
                    new_total_cost = position.cost_basis + trade_value
                    new_quantity = position.quantity + quantity
                    position.avg_entry_price = new_total_cost / new_quantity
                    position.quantity = new_quantity
                    position.cost_basis = new_total_cost
                else:  # SELL
                    # Reduce position
                    position.quantity -= quantity
                    
                    # Calculate realized P&L
                    realized_pnl = (execution_price - position.avg_entry_price) * quantity
                    position.realized_pnl = (position.realized_pnl or 0) + realized_pnl
                    portfolio.realized_pnl += realized_pnl
                    
                    # If position is fully closed, mark as closed
                    if position.quantity <= 0:
                        position.is_open = False
                    else:
                        # Update cost basis for remaining shares
                        position.cost_basis = position.avg_entry_price * position.quantity
                
                # Update current market values
                position.current_price = current_price
                position.market_value = position.quantity * current_price if position.is_open else 0
                position.unrealized_pnl = (current_price - position.avg_entry_price) * position.quantity if position.is_open else 0
                position.last_update_date = datetime.utcnow()
        
            # Update portfolio totals
            portfolio.calculate_portfolio_value()
            portfolio.last_updated = datetime.utcnow()
        
            db.session.commit()
        except Exception as db_error:
            db.session.rollback()
            logger.error(f"Database error during trade execution: {db_error}")
            return jsonify({'error': 'Failed to execute trade'}), 500
        
        logger.info(f"Trade executed: {side} {quantity} {validated_symbol} @ ${execution_price:.2f} for user {g.current_user.id}")
        
        return jsonify({
            'message': 'Trade executed successfully',
            'transaction': {
                'id': transaction.id,
                'symbol': validated_symbol,
                'side': side,
                'quantity': quantity,
                'price': execution_price,
                'total_value': trade_value,
                'commission': commission,
                'net_amount': total_cost if side == 'BUY' else (trade_value - commission),
                'executed_at': transaction.transaction_date.isoformat(),
                'status': transaction.status
            },
            'portfolio_update': {
                'cash_balance': portfolio.cash_balance,
                'total_value': portfolio.total_value,
                'realized_pnl': portfolio.realized_pnl
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Trade execution error: {e}")
        return jsonify({'error': 'Failed to execute trade'}), 500

@trading_bp.route('/portfolios/<int:portfolio_id>/transactions', methods=['GET'])
@token_required
@handle_validation_error
def get_portfolio_transactions(portfolio_id):
    """Get portfolio transaction history"""
    from flask import g
    
    try:
        # Verify portfolio ownership
        portfolio = Portfolio.query.filter_by(
            id=portfolio_id,
            user_id=g.current_user.id
        ).first()
        
        if not portfolio:
            return jsonify({'error': 'Portfolio not found'}), 404
        
        # Get query parameters
        symbol = request.args.get('symbol')
        side = request.args.get('side')
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Build query
        query = Transaction.query.filter_by(portfolio_id=portfolio_id)
        
        if symbol:
            query = query.filter(Transaction.symbol == symbol.upper())
        if side:
            query = query.filter(Transaction.transaction_type == side.upper())
        
        # Apply pagination and ordering
        query = query.order_by(Transaction.transaction_date.desc())
        total_count = query.count()
        transactions = query.offset(offset).limit(min(limit, 100)).all()
        
        # Format response
        transactions_data = []
        for transaction in transactions:
            transactions_data.append({
                'id': transaction.id,
                'symbol': transaction.symbol,
                'side': transaction.transaction_type,
                'quantity': transaction.quantity,
                'price': transaction.price,
                'total_value': transaction.total_value,
                'commission': transaction.commission,
                'net_amount': transaction.total_value + transaction.commission if transaction.transaction_type == 'BUY' else transaction.total_value - transaction.commission,
                'status': transaction.status,
                'executed_at': transaction.transaction_date.isoformat() if transaction.transaction_date else None
            })
        
        return jsonify({
            'transactions': transactions_data,
            'pagination': {
                'total': total_count,
                'offset': offset,
                'limit': limit,
                'has_more': (offset + limit) < total_count
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get portfolio transactions error: {e}")
        return jsonify({'error': 'Failed to retrieve transactions'}), 500

@trading_bp.route('/portfolios/<int:portfolio_id>/orders', methods=['GET'])
@token_required
@handle_validation_error
def get_portfolio_orders(portfolio_id):
    """Get portfolio order history (for limit orders, pending orders, etc.)"""
    from flask import g
    
    try:
        # Verify portfolio ownership
        portfolio = Portfolio.query.filter_by(
            id=portfolio_id,
            user_id=g.current_user.id
        ).first()
        
        if not portfolio:
            return jsonify({'error': 'Portfolio not found'}), 404
        
        # Get query parameters
        status = request.args.get('status')  # PENDING, FILLED, CANCELLED
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Build query
        query = Transaction.query.filter_by(portfolio_id=portfolio_id)
        
        if status:
            query = query.filter(Transaction.status == status.upper())
        
        # Apply pagination and ordering
        query = query.order_by(Transaction.transaction_date.desc())
        total_count = query.count()
        orders = query.offset(offset).limit(min(limit, 100)).all()
        
        # Format response
        orders_data = []
        for order in orders:
            orders_data.append({
                'id': order.id,
                'symbol': order.symbol,
                'side': order.transaction_type,
                'quantity': order.quantity,
                'status': order.status,
                'created_at': order.created_at.isoformat(),
                'executed_at': order.transaction_date.isoformat() if order.transaction_date else None,
                'total_value': order.total_value if order.status == 'FILLED' else None,
                'commission': order.commission if order.status == 'FILLED' else None
            })
        
        return jsonify({
            'orders': orders_data,
            'pagination': {
                'total': total_count,
                'offset': offset,
                'limit': limit,
                'has_more': (offset + limit) < total_count
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get portfolio orders error: {e}")
        return jsonify({'error': 'Failed to retrieve orders'}), 500

@trading_bp.route('/quote/<symbol>', methods=['GET'])
@token_required
@handle_validation_error
def get_trading_quote(symbol):
    """Get real-time quote for trading"""
    try:
        # Validate symbol
        try:
            validated_symbol = InputValidator.validate_stock_symbol(symbol)
        except ValidationError:
            return jsonify({'error': f'Invalid symbol: {symbol}'}), 400
        
        # Get quote from stock service
        stock_service = current_app.stock_service
        quote_data = stock_service.fetch_stock_data(validated_symbol)
        
        if not quote_data:
            return jsonify({'error': f'Quote not available for {validated_symbol}'}), 404
        
        # Calculate estimated commission (0.1% of trade value)
        # Handle different possible field names for price
        price = 0
        if 'price' in quote_data:
            price = float(quote_data['price'])
        elif 'c' in quote_data:
            price = float(quote_data['c'])
        elif 'close' in quote_data:
            price = float(quote_data['close'])
        estimated_commission_rate = 0.001
        
        return jsonify({
            'symbol': validated_symbol,
            'price': price,
            'bid': quote_data.get('bid', price),
            'ask': quote_data.get('ask', price),
            'volume': quote_data.get('volume', 0),
            'change': quote_data.get('change', 0),
            'change_percent': quote_data.get('change_percent', 0),
            'timestamp': quote_data.get('timestamp', datetime.utcnow().isoformat()),
            'trading_info': {
                'estimated_commission_rate': estimated_commission_rate,
                'market_hours': True,  # Simplified - in reality you'd check market hours
                'tradable': True
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get trading quote error: {e}")
        return jsonify({'error': 'Failed to get quote'}), 500

@trading_bp.route('/portfolios/<int:portfolio_id>/buying-power', methods=['GET'])
@token_required
@handle_validation_error
def get_buying_power(portfolio_id):
    """Get available buying power for a portfolio"""
    from flask import g
    
    try:
        # Find portfolio
        portfolio = Portfolio.query.filter_by(
            id=portfolio_id,
            user_id=g.current_user.id
        ).first()
        
        if not portfolio:
            return jsonify({'error': 'Portfolio not found'}), 404
        
        # For paper trading, buying power = cash balance
        # In real trading, you might have margin, etc.
        buying_power = portfolio.cash_balance
        
        return jsonify({
            'portfolio_id': portfolio_id,
            'cash_balance': portfolio.cash_balance,
            'buying_power': buying_power,
            'total_value': portfolio.total_value,
            'invested_value': portfolio.invested_value,
            'available_percentage': (buying_power / portfolio.total_value * 100) if portfolio.total_value > 0 else 0
        }), 200
        
    except Exception as e:
        logger.error(f"Get buying power error: {e}")
        return jsonify({'error': 'Failed to get buying power'}), 500