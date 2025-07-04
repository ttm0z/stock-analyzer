# routes/admin_routes.py (New file for cache management)
from flask import Blueprint, jsonify, current_app
import logging

admin_bp = Blueprint('admin', __name__)
logger = logging.getLogger(__name__)

@admin_bp.route('/cache/stats')
def get_cache_stats():
    """Get comprehensive cache and service statistics"""
    try:
        stock_service = current_app.stock_service
        stats = stock_service.get_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Cache stats error: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/cache/clear', methods=['POST'])
def clear_cache():
    """Clear all cache entries"""
    try:
        cache_service = current_app.cache_service
        
        if not cache_service or not cache_service.redis:
            return jsonify({'error': 'Cache not available'}), 503
        
        # Clear cache patterns
        patterns = [
            f'{cache_service.key_prefix}:*',
        ]
        
        total_deleted = 0
        for pattern in patterns:
            deleted = cache_service.delete_pattern(pattern)
            total_deleted += deleted
        
        # Reset statistics
        cache_service.clear_stats()
        current_app.stock_service.api_call_count = 0
        current_app.stock_service.cache_hit_count = 0
        
        return jsonify({
            'message': f'Cache cleared successfully',
            'entries_deleted': total_deleted
        })
    except Exception as e:
        logger.error(f"Cache clear error: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/health')
def health_check():
    """Application health check"""
    try:
        cache_service = current_app.cache_service
        
        # Test Redis connection
        redis_status = 'connected' if cache_service and cache_service.redis else 'disconnected'
        if cache_service and cache_service.redis:
            try:
                cache_service.redis.ping()
                redis_status = 'connected'
            except:
                redis_status = 'connection_error'
        
        return jsonify({
            'status': 'healthy',
            'redis_status': redis_status,
            'cache_stats': cache_service.get_stats() if cache_service else None
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500