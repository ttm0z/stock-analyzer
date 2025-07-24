"""
Market Data API routes
"""
from flask import Blueprint, request, jsonify, current_app
from ..auth.decorators import token_required
import logging
import random
from datetime import datetime, timedelta

market_bp = Blueprint('market', __name__)
logger = logging.getLogger(__name__)

@market_bp.route('/indices', methods=['GET'])
@token_required
def get_market_indices():
    """Get major market indices data"""
    try:
        # Mock data - in production, you would fetch from a real market data API
        base_indices = [
            { 'name': 'S&P 500', 'symbol': 'SPX', 'base_value': 4756.50 },
            { 'name': 'NASDAQ', 'symbol': 'IXIC', 'base_value': 14845.12 },
            { 'name': 'Dow Jones', 'symbol': 'DJI', 'base_value': 37689.54 },
            { 'name': 'Russell 2000', 'symbol': 'RUT', 'base_value': 2089.23 },
            { 'name': 'VIX', 'symbol': 'VIX', 'base_value': 18.45 },
            { 'name': 'FTSE 100', 'symbol': 'UKX', 'base_value': 7420.30 }
        ]
        
        indices = []
        for index in base_indices:
            change_percent = (random.random() - 0.5) * 4  # -2% to +2%
            change = (index['base_value'] * change_percent) / 100
            value = index['base_value'] + change
            
            indices.append({
                'name': index['name'],
                'symbol': index['symbol'],
                'value': round(value, 2),
                'change': round(change, 2),
                'change_percent': round(change_percent, 2),
                'volume': random.randint(500000000, 1500000000),
                'day_high': round(value + abs(change) * 0.5, 2),
                'day_low': round(value - abs(change) * 0.5, 2),
                'last_updated': datetime.utcnow().isoformat()
            })
        
        return jsonify({
            'indices': indices,
            'last_updated': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Get indices error: {e}")
        return jsonify({'error': 'Failed to get market indices'}), 500

@market_bp.route('/sectors', methods=['GET'])
@token_required
def get_sector_performance():
    """Get sector performance data"""
    try:
        sectors = [
            'Technology', 'Healthcare', 'Financials', 'Energy', 
            'Consumer Discretionary', 'Industrials', 'Materials', 
            'Utilities', 'Real Estate', 'Communication Services', 
            'Consumer Staples'
        ]
        
        sector_data = []
        for name in sectors:
            change = (random.random() - 0.5) * 6  # -3% to +3%
            performance = 'strong' if change > 1 else 'moderate' if change > -1 else 'weak'
            market_cap = f"{random.randint(500, 2500)}B"
            companies = random.randint(50, 150)
            
            sector_data.append({
                'name': name,
                'change': round(change, 2),
                'performance': performance,
                'market_cap': market_cap,
                'companies': companies,
                'last_updated': datetime.utcnow().isoformat()
            })
        
        return jsonify({
            'sectors': sector_data,
            'last_updated': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Get sectors error: {e}")
        return jsonify({'error': 'Failed to get sector performance'}), 500

@market_bp.route('/movers', methods=['GET'])
@token_required
def get_market_movers():
    """Get top gainers, losers, and most active stocks"""
    try:
        mover_type = request.args.get('type', 'all')  # gainers, losers, active, all
        limit = min(int(request.args.get('limit', 10)), 50)
        
        # Mock stock data
        def generate_stocks(symbols, min_change, max_change):
            stocks = []
            for symbol in symbols:
                price = random.uniform(20, 500)
                change_percent = random.uniform(min_change, max_change)
                change = (price * change_percent) / 100
                
                stocks.append({
                    'symbol': symbol,
                    'name': f"{symbol} Corp",
                    'price': round(price, 2),
                    'change': round(change, 2),
                    'change_percent': round(change_percent, 2),
                    'volume': random.randint(1000000, 50000000),
                    'last_updated': datetime.utcnow().isoformat()
                })
            return stocks
        
        result = {}
        
        if mover_type in ['gainers', 'all']:
            gainer_symbols = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX', 'CRM', 'ADBE']
            gainers = generate_stocks(gainer_symbols, 2, 15)
            gainers = sorted(gainers, key=lambda x: x['change_percent'], reverse=True)[:limit]
            result['gainers'] = gainers
        
        if mover_type in ['losers', 'all']:
            loser_symbols = ['F', 'GE', 'BAC', 'WFC', 'C', 'JPM', 'PFE', 'XOM', 'CVX', 'KO']
            losers = generate_stocks(loser_symbols, -15, -1)
            losers = sorted(losers, key=lambda x: x['change_percent'])[:limit]
            result['losers'] = losers
        
        if mover_type in ['active', 'all']:
            active_symbols = ['SPY', 'QQQ', 'AMD', 'INTC', 'BABA', 'NIO', 'PLTR', 'SOFI', 'HOOD', 'AMC']
            active = generate_stocks(active_symbols, -8, 8)
            # Sort by volume for most active
            for stock in active:
                stock['volume'] = random.randint(10000000, 100000000)  # Higher volumes for active stocks
            active = sorted(active, key=lambda x: x['volume'], reverse=True)[:limit]
            result['most_active'] = active
        
        result['last_updated'] = datetime.utcnow().isoformat()
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Get movers error: {e}")
        return jsonify({'error': 'Failed to get market movers'}), 500

@market_bp.route('/currencies', methods=['GET'])
@token_required
def get_currency_rates():
    """Get currency exchange rates"""
    try:
        base_rates = [
            { 'pair': 'EUR/USD', 'base_rate': 1.0875 },
            { 'pair': 'GBP/USD', 'base_rate': 1.2634 },
            { 'pair': 'USD/JPY', 'base_rate': 148.45 },
            { 'pair': 'USD/CAD', 'base_rate': 1.3456 },
            { 'pair': 'AUD/USD', 'base_rate': 0.6789 },
            { 'pair': 'USD/CHF', 'base_rate': 0.9123 },
            { 'pair': 'NZD/USD', 'base_rate': 0.6234 }
        ]
        
        currencies = []
        for currency in base_rates:
            fluctuation = (random.random() - 0.5) * 0.02  # Small fluctuation
            rate = currency['base_rate'] + fluctuation
            change = fluctuation
            
            currencies.append({
                'pair': currency['pair'],
                'rate': round(rate, 4),
                'change': round(change, 4),
                'change_percent': round((change / currency['base_rate']) * 100, 2),
                'last_updated': datetime.utcnow().isoformat()
            })
        
        return jsonify({
            'currencies': currencies,
            'last_updated': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Get currencies error: {e}")
        return jsonify({'error': 'Failed to get currency rates'}), 500

@market_bp.route('/commodities', methods=['GET'])
@token_required
def get_commodities():
    """Get commodity prices"""
    try:
        base_commodities = [
            { 'name': 'Gold', 'base_price': 2034.50, 'unit': '/oz' },
            { 'name': 'Silver', 'base_price': 24.78, 'unit': '/oz' },
            { 'name': 'Crude Oil', 'base_price': 78.34, 'unit': '/bbl' },
            { 'name': 'Natural Gas', 'base_price': 2.87, 'unit': '/MMBtu' },
            { 'name': 'Copper', 'base_price': 3.85, 'unit': '/lb' },
            { 'name': 'Platinum', 'base_price': 1012.45, 'unit': '/oz' },
            { 'name': 'Palladium', 'base_price': 1245.67, 'unit': '/oz' }
        ]
        
        commodities = []
        for commodity in base_commodities:
            change_percent = (random.random() - 0.5) * 6  # -3% to +3%
            change = (commodity['base_price'] * change_percent) / 100
            price = commodity['base_price'] + change
            
            commodities.append({
                'name': commodity['name'],
                'price': round(price, 2),
                'change': round(change, 2),
                'change_percent': round(change_percent, 2),
                'unit': commodity['unit'],
                'last_updated': datetime.utcnow().isoformat()
            })
        
        return jsonify({
            'commodities': commodities,
            'last_updated': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Get commodities error: {e}")
        return jsonify({'error': 'Failed to get commodity prices'}), 500

@market_bp.route('/sentiment', methods=['GET'])
@token_required
def get_market_sentiment():
    """Get market sentiment data"""
    try:
        sentiments = ['Bullish', 'Bearish', 'Neutral']
        overall_sentiment = random.choice(sentiments)
        score = random.randint(20, 80)
        fear_greed_index = random.randint(0, 100)
        
        # Generate some sentiment indicators
        indicators = [
            { 'name': 'VIX Level', 'value': random.randint(12, 35), 'status': 'normal' },
            { 'name': 'Put/Call Ratio', 'value': round(random.uniform(0.7, 1.3), 2), 'status': 'normal' },
            { 'name': 'High-Low Index', 'value': random.randint(30, 70), 'status': 'normal' },
            { 'name': 'Safe Haven Demand', 'value': random.randint(20, 80), 'status': 'normal' }
        ]
        
        sentiment_data = {
            'overall': overall_sentiment,
            'score': score,
            'fear_greed_index': fear_greed_index,
            'description': f"Market sentiment is currently {overall_sentiment.lower()} based on recent trading activity and economic indicators.",
            'indicators': indicators,
            'last_updated': datetime.utcnow().isoformat()
        }
        
        return jsonify(sentiment_data), 200
        
    except Exception as e:
        logger.error(f"Get sentiment error: {e}")
        return jsonify({'error': 'Failed to get market sentiment'}), 500

@market_bp.route('/economic-indicators', methods=['GET'])
@token_required
def get_economic_indicators():
    """Get economic indicators"""
    try:
        indicators = [
            { 
                'name': 'Unemployment Rate', 
                'value': '3.7%', 
                'change': round(random.uniform(-0.3, 0.3), 1), 
                'period': 'Dec 2024',
                'category': 'employment'
            },
            { 
                'name': 'Inflation Rate', 
                'value': '3.2%', 
                'change': round(random.uniform(-0.5, 0.5), 1), 
                'period': 'Dec 2024',
                'category': 'inflation'
            },
            { 
                'name': 'GDP Growth', 
                'value': '2.4%', 
                'change': round(random.uniform(-0.3, 0.3), 1), 
                'period': 'Q4 2024',
                'category': 'growth'
            },
            { 
                'name': 'Federal Funds Rate', 
                'value': '5.25%', 
                'change': 0, 
                'period': 'Current',
                'category': 'monetary'
            },
            { 
                'name': 'Consumer Confidence', 
                'value': str(random.randint(90, 120)), 
                'change': round(random.uniform(-5, 5), 1), 
                'period': 'Dec 2024',
                'category': 'sentiment'
            },
            { 
                'name': 'Manufacturing PMI', 
                'value': str(round(random.uniform(45, 55), 1)), 
                'change': round(random.uniform(-2, 2), 1), 
                'period': 'Dec 2024',
                'category': 'manufacturing'
            }
        ]
        
        return jsonify({
            'indicators': indicators,
            'last_updated': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Get economic indicators error: {e}")
        return jsonify({'error': 'Failed to get economic indicators'}), 500

@market_bp.route('/status', methods=['GET'])
@token_required
def get_market_status():
    """Get current market status"""
    try:
        now = datetime.utcnow()
        # Adjust for EST (market timezone)
        est_hour = (now.hour - 5) % 24  # Rough EST conversion
        is_weekend = now.weekday() >= 5  # Saturday = 5, Sunday = 6
        
        if is_weekend:
            status = {
                'status': 'Closed',
                'message': 'Markets closed for weekend',
                'color': 'red',
                'next_open': 'Monday 9:30 AM EST'
            }
        elif 9 <= est_hour < 16:
            status = {
                'status': 'Open',
                'message': 'Markets are open',
                'color': 'green',
                'next_close': '4:00 PM EST'
            }
        elif 4 <= est_hour < 9:
            status = {
                'status': 'Pre-Market',
                'message': 'Pre-market trading',
                'color': 'yellow',
                'next_open': '9:30 AM EST'
            }
        elif 16 <= est_hour < 20:
            status = {
                'status': 'After-Hours',
                'message': 'After-hours trading',
                'color': 'yellow',
                'next_open': 'Tomorrow 9:30 AM EST'
            }
        else:
            status = {
                'status': 'Closed',
                'message': 'Markets closed',
                'color': 'red',
                'next_open': '9:30 AM EST'
            }
        
        status['last_updated'] = now.isoformat()
        status['timezone'] = 'EST'
        
        return jsonify(status), 200
        
    except Exception as e:
        logger.error(f"Get market status error: {e}")
        return jsonify({'error': 'Failed to get market status'}), 500