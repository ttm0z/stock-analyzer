"""
Authentication decorators and utilities
"""
from functools import wraps
from flask import request, jsonify, current_app, g
from .models import User, APIKey
import logging

logger = logging.getLogger(__name__)

def token_required(f):
    """Decorator to require JWT token authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Check for token in Authorization header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(' ')[1]  # Bearer <token>
            except IndexError:
                return jsonify({'error': 'Invalid authorization header format'}), 401
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        try:
            # Decode the token
            current_user = User.decode_jwt_token(token)
            if not current_user:
                return jsonify({'error': 'Token is invalid or expired'}), 401
            
            if not current_user.is_active:
                return jsonify({'error': 'User account is deactivated'}), 401
            
            # Store current user in Flask's g object
            g.current_user = current_user
            
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            return jsonify({'error': 'Token validation failed'}), 401
        
        return f(*args, **kwargs)
    
    return decorated

def api_key_required(f):
    """Decorator to require API key authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = None
        
        # Check for API key in headers
        if 'X-API-Key' in request.headers:
            api_key = request.headers['X-API-Key']
        elif 'api_key' in request.args:
            api_key = request.args.get('api_key')
        
        if not api_key:
            return jsonify({'error': 'API key is missing'}), 401
        
        try:
            # Find and validate API key
            api_key_obj = None
            for key_obj in APIKey.query.filter_by(is_active=True).all():
                if key_obj.check_key(api_key):
                    api_key_obj = key_obj
                    break
            
            if not api_key_obj or not api_key_obj.is_valid():
                return jsonify({'error': 'Invalid or expired API key'}), 401
            
            # Record usage
            api_key_obj.record_usage()
            
            # Store current user in Flask's g object
            g.current_user = api_key_obj.user
            g.api_key = api_key_obj
            
        except Exception as e:
            logger.error(f"API key validation error: {e}")
            return jsonify({'error': 'API key validation failed'}), 401
        
        return f(*args, **kwargs)
    
    return decorated

def auth_required(f):
    """Decorator that accepts either JWT token or API key"""
    @wraps(f)
    def decorated(*args, **kwargs):
        # Try JWT token first
        if 'Authorization' in request.headers:
            return token_required(f)(*args, **kwargs)
        
        # Try API key
        if 'X-API-Key' in request.headers or 'api_key' in request.args:
            return api_key_required(f)(*args, **kwargs)
        
        return jsonify({'error': 'Authentication required'}), 401
    
    return decorated

def optional_auth(f):
    """Decorator that makes authentication optional"""
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            # Try to authenticate but don't fail if no auth provided
            if 'Authorization' in request.headers:
                return token_required(f)(*args, **kwargs)
            elif 'X-API-Key' in request.headers or 'api_key' in request.args:
                return api_key_required(f)(*args, **kwargs)
            else:
                # No authentication provided - continue without user
                g.current_user = None
                return f(*args, **kwargs)
        except:
            # Authentication failed - continue without user
            g.current_user = None
            return f(*args, **kwargs)
    
    return decorated

def admin_required(f):
    """Decorator to require admin privileges"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not hasattr(g, 'current_user') or not g.current_user:
            return jsonify({'error': 'Authentication required'}), 401
        
        # For now, check if user is admin by email domain or specific usernames
        # In production, you'd have a proper role-based system
        admin_emails = ['admin@stockanalyzer.com']
        admin_usernames = ['admin', 'administrator']
        
        if (g.current_user.email not in admin_emails and 
            g.current_user.username not in admin_usernames):
            return jsonify({'error': 'Admin privileges required'}), 403
        
        return f(*args, **kwargs)
    
    return decorated

def get_current_user():
    """Get current authenticated user"""
    return getattr(g, 'current_user', None)

def is_authenticated():
    """Check if current request is authenticated"""
    return hasattr(g, 'current_user') and g.current_user is not None