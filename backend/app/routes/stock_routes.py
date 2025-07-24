# routes/stock_routes.py (Enhanced)
from flask import Blueprint, request, jsonify, current_app
from ..models.models import Trade, db
from ..utils.validation import InputValidator, ValidationError, handle_validation_error
import logging

stock_bp = Blueprint('stock', __name__)
logger = logging.getLogger(__name__)

@stock_bp.route('/search')
@handle_validation_error
def search_stocks():
    """Search for stocks with caching"""
    query = request.args.get('query', '').strip()
    
    if not query:
        return jsonify([])
    
    try:
        # Validate and sanitize search query
        validated_query = InputValidator.validate_search_query(query)
        
        stock_service = current_app.stock_service
        results = stock_service.fetch_search_query(validated_query)
        return jsonify(results)
    except ValidationError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Search error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@stock_bp.route('/quote/<symbol>')
@handle_validation_error
def get_stock_quote(symbol):
    """Get stock quote with caching"""
    try:
        # Validate and sanitize symbol
        validated_symbol = InputValidator.validate_stock_symbol(symbol)
        
        stock_service = current_app.stock_service
        quote = stock_service.fetch_stock_data(validated_symbol)
        
        return jsonify(quote)
    except ValidationError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Quote error for {symbol}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@stock_bp.route('/quotes')
@handle_validation_error
def get_batch_quotes():
    """Get multiple stock quotes with caching"""
    symbols_str = request.args.get('symbols', '')
    
    try:
        # Validate and sanitize symbols list
        validated_symbols = InputValidator.validate_symbols_list(symbols_str)
        
        stock_service = current_app.stock_service
        quotes = stock_service.get_batch_quotes(validated_symbols)
        return jsonify(quotes)
    except ValidationError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Batch quotes error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@stock_bp.route('/historical/<symbol>')
def get_historical_data(symbol):
    """Get historical data with caching"""
    if not symbol:
        return jsonify({'error': 'Symbol is required'}), 400
    
    from_date = request.args.get('from')
    to_date = request.args.get('to')
    
    try:
        stock_service = current_app.stock_service
        data = stock_service.fetch_historical_data(symbol, from_date, to_date)
        return jsonify(data)
    except Exception as e:
        logger.error(f"Historical data error for {symbol}: {e}")
        return jsonify({'error': str(e)}), 500

@stock_bp.route('/profile/<symbol>')
def get_company_profile(symbol):
    """Get company profile with caching"""
    if not symbol:
        return jsonify({'error': 'Symbol is required'}), 400
    
    try:
        stock_service = current_app.stock_service
        profile = stock_service.get_company_profile(symbol)
        return jsonify(profile)
    except Exception as e:
        logger.error(f"Profile error for {symbol}: {e}")
        return jsonify({'error': str(e)}), 500

@stock_bp.route('/financials/<symbol>/<statement_type>')
def get_financial_statements(symbol, statement_type):
    """Get financial statements with caching"""
    if not symbol or statement_type not in ['income-statement', 'balance-sheet-statement', 'cash-flow-statement']:
        return jsonify({'error': 'Invalid symbol or statement type'}), 400
    
    period = request.args.get('period', 'annual')
    limit = request.args.get('limit', 5, type=int)
    
    try:
        stock_service = current_app.stock_service
        data = stock_service.get_financial_statements(symbol, statement_type, period, limit)
        return jsonify(data)
    except Exception as e:
        logger.error(f"Financial statements error for {symbol}: {e}")
        return jsonify({'error': str(e)}), 500

@stock_bp.route('/news')
def get_market_news():
    """Get market news with caching"""
    limit = request.args.get('limit', 50, type=int)
    tickers = request.args.get('tickers')
    
    try:
        stock_service = current_app.stock_service
        news = stock_service.get_market_news(limit, tickers)
        return jsonify(news)
    except Exception as e:
        logger.error(f"Market news error: {e}")
        return jsonify({'error': str(e)}), 500

# Trade Management API
@stock_bp.route('/trades', methods=['POST'])
@handle_validation_error
def create_trade():
    """Create a new trade"""
    from flask import g
    from ..auth.decorators import token_required
    
    @token_required
    def _create_trade():
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        try:
            # Validate required fields
            required_fields = ['ticker', 'price', 'quantity', 'trade_type']
            for field in required_fields:
                if field not in data:
                    return jsonify({'error': f'Missing required field: {field}'}), 400
            
            # Validate trade type
            if data['trade_type'] not in ['BUY', 'SELL']:
                return jsonify({'error': 'trade_type must be BUY or SELL'}), 400
            
            # Validate numeric fields
            try:
                price = float(data['price'])
                quantity = int(data['quantity'])
                if price <= 0 or quantity <= 0:
                    raise ValueError("Price and quantity must be positive")
            except (ValueError, TypeError):
                return jsonify({'error': 'Invalid price or quantity'}), 400
            
            # Validate ticker symbol
            ticker = InputValidator.validate_stock_symbol(data['ticker'])
            
            # Create trade record
            trade = Trade(
                ticker=ticker,
                date=data.get('date', datetime.now().strftime('%Y-%m-%d')),
                price=price,
                quantity=quantity,
                trade_type=data['trade_type']
            )
            
            db.session.add(trade)
            db.session.commit()
            
            logger.info(f"Trade created: {trade.trade_type} {trade.quantity} {trade.ticker} @ {trade.price}")
            
            return jsonify({
                'message': 'Trade created successfully',
                'trade': {
                    'id': trade.id,
                    'ticker': trade.ticker,
                    'date': trade.date,
                    'price': trade.price,
                    'quantity': trade.quantity,
                    'trade_type': trade.trade_type
                }
            }), 201
            
        except ValidationError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            logger.error(f"Trade creation error: {e}")
            return jsonify({'error': 'Failed to create trade'}), 500
    
    return _create_trade()

@stock_bp.route('/trades', methods=['GET'])
@handle_validation_error
def get_trades():
    """Get user trades with filtering"""
    from flask import g
    from ..auth.decorators import token_required
    
    @token_required
    def _get_trades():
        try:
            # Get query parameters
            ticker = request.args.get('ticker')
            trade_type = request.args.get('trade_type')
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            limit = request.args.get('limit', 100, type=int)
            offset = request.args.get('offset', 0, type=int)
            
            # Build query
            query = Trade.query
            
            # Apply filters
            if ticker:
                query = query.filter(Trade.ticker.ilike(f'%{ticker}%'))
            if trade_type:
                query = query.filter(Trade.trade_type == trade_type.upper())
            if start_date:
                query = query.filter(Trade.date >= start_date)
            if end_date:
                query = query.filter(Trade.date <= end_date)
            
            # Apply pagination and ordering
            query = query.order_by(Trade.date.desc(), Trade.id.desc())
            total_count = query.count()
            trades = query.offset(offset).limit(min(limit, 1000)).all()
            
            # Format response
            trades_data = []
            for trade in trades:
                trades_data.append({
                    'id': trade.id,
                    'ticker': trade.ticker,
                    'date': trade.date,
                    'price': trade.price,
                    'quantity': trade.quantity,
                    'trade_type': trade.trade_type,
                    'value': trade.price * trade.quantity
                })
            
            return jsonify({
                'trades': trades_data,
                'pagination': {
                    'total': total_count,
                    'offset': offset,
                    'limit': limit,
                    'has_more': (offset + limit) < total_count
                }
            }), 200
            
        except Exception as e:
            logger.error(f"Get trades error: {e}")
            return jsonify({'error': 'Failed to retrieve trades'}), 500
    
    return _get_trades()

@stock_bp.route('/trades/<int:trade_id>', methods=['PUT'])
@handle_validation_error
def update_trade(trade_id):
    """Update an existing trade"""
    from flask import g
    from ..auth.decorators import token_required
    
    @token_required
    def _update_trade():
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        try:
            # Find trade
            trade = Trade.query.get(trade_id)
            if not trade:
                return jsonify({'error': 'Trade not found'}), 404
            
            # Update allowed fields
            if 'price' in data:
                try:
                    price = float(data['price'])
                    if price <= 0:
                        raise ValueError("Price must be positive")
                    trade.price = price
                except (ValueError, TypeError):
                    return jsonify({'error': 'Invalid price'}), 400
            
            if 'quantity' in data:
                try:
                    quantity = int(data['quantity'])
                    if quantity <= 0:
                        raise ValueError("Quantity must be positive")
                    trade.quantity = quantity
                except (ValueError, TypeError):
                    return jsonify({'error': 'Invalid quantity'}), 400
            
            if 'trade_type' in data:
                if data['trade_type'] not in ['BUY', 'SELL']:
                    return jsonify({'error': 'trade_type must be BUY or SELL'}), 400
                trade.trade_type = data['trade_type']
            
            if 'date' in data:
                trade.date = data['date']
            
            db.session.commit()
            
            logger.info(f"Trade updated: ID {trade_id}")
            
            return jsonify({
                'message': 'Trade updated successfully',
                'trade': {
                    'id': trade.id,
                    'ticker': trade.ticker,
                    'date': trade.date,
                    'price': trade.price,
                    'quantity': trade.quantity,
                    'trade_type': trade.trade_type
                }
            }), 200
            
        except Exception as e:
            logger.error(f"Trade update error: {e}")
            return jsonify({'error': 'Failed to update trade'}), 500
    
    return _update_trade()

@stock_bp.route('/trades/<int:trade_id>', methods=['DELETE'])
@handle_validation_error
def delete_trade(trade_id):
    """Delete a trade"""
    from flask import g
    from ..auth.decorators import token_required
    
    @token_required
    def _delete_trade():
        try:
            # Find trade
            trade = Trade.query.get(trade_id)
            if not trade:
                return jsonify({'error': 'Trade not found'}), 404
            
            # Delete trade
            db.session.delete(trade)
            db.session.commit()
            
            logger.info(f"Trade deleted: ID {trade_id}")
            
            return jsonify({'message': 'Trade deleted successfully'}), 200
            
        except Exception as e:
            logger.error(f"Trade deletion error: {e}")
            return jsonify({'error': 'Failed to delete trade'}), 500
    
    return _delete_trade()
