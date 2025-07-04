# routes/stock_routes.py (Enhanced)
from flask import Blueprint, request, jsonify, current_app
from ..models import Trade, db
import logging

stock_bp = Blueprint('stock', __name__)
logger = logging.getLogger(__name__)

@stock_bp.route('/search')
def search_stocks():
    """Search for stocks with caching"""
    query = request.args.get('query', '').strip()
    
    if not query or len(query) < 1:
        return jsonify([])
    
    try:
        stock_service = current_app.stock_service
        results = stock_service.fetch_search_query(query)
        return jsonify(results)
    except Exception as e:
        logger.error(f"Search error: {e}")
        return jsonify({'error': str(e)}), 500

@stock_bp.route('/quote/<symbol>')
def get_stock_quote(symbol):
    """Get stock quote with caching"""
    if not symbol:
        return jsonify({'error': 'Symbol is required'}), 400
    
    try:
        stock_service = current_app.stock_service
        
        quote = stock_service.fetch_stock_data(symbol)
        
        return jsonify(quote)
    except Exception as e:
        logger.error(f"Quote error for {symbol}: {e}")
        return jsonify({'error': str(e)}), 500

@stock_bp.route('/quotes')
def get_batch_quotes():
    """Get multiple stock quotes with caching"""
    symbols = request.args.get('symbols', '').split(',')
    symbols = [s.strip() for s in symbols if s.strip()]
    
    if not symbols:
        return jsonify({'error': 'Symbols are required'}), 400
    
    try:
        stock_service = current_app.stock_service
        quotes = stock_service.get_batch_quotes(symbols)
        return jsonify(quotes)
    except Exception as e:
        logger.error(f"Batch quotes error: {e}")
        return jsonify({'error': str(e)}), 500

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

# Keep your existing trade-related routes
@stock_bp.route('/trades', methods=['POST'])
def create_trade():
    """Your existing trade creation endpoint"""
    # Your existing implementation
    pass
