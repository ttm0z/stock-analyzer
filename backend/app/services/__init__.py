import os
from .cache_service import CacheService
from .stock_service import StockService

def init_services(app):
    cache = CacheService.create_instance()
    app.cache_service = cache

    api_key = os.getenv('FMP_API_KEY')
    if not api_key:
        raise ValueError("FMP_API_KEY is required")

    app.stock_service = StockService(api_key, cache)