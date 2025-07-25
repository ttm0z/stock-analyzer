from .stock_routes import stock_bp
from .auth_routes import auth_bp
from .portfolio_routes import portfolio_bp
from .strategy_routes import strategy_bp
from .backtest_routes import backtest_bp
from .trading_routes import trading_bp
from .settings_routes import settings_bp
from .market_routes import market_bp
from .admin_routes import admin_bp


def register_blueprints(app):
    app.register_blueprint(stock_bp, url_prefix='/api')
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(portfolio_bp, url_prefix='/api')
    app.register_blueprint(strategy_bp, url_prefix='/api')
    app.register_blueprint(backtest_bp, url_prefix='/api')
    app.register_blueprint(trading_bp, url_prefix='/api/trading')
    app.register_blueprint(settings_bp, url_prefix='/api/settings')
    app.register_blueprint(market_bp, url_prefix='/api/market')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')