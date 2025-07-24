"""
Authentication routes
"""
from flask import Blueprint, request, jsonify, current_app
from ..db import db
from ..auth.models import User, APIKey
from ..auth.decorators import token_required, admin_required
from ..utils.validation import InputValidator, ValidationError, handle_validation_error
import secrets
import logging

auth_bp = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)

@auth_bp.route('/register', methods=['POST'])
@handle_validation_error
def register():
    """Register a new user"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No JSON data provided'}), 400
    
    try:
        # Validate required fields
        email = data.get('email', '').strip().lower()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        
        # Basic validation
        if not email or '@' not in email:
            raise ValidationError("Valid email is required")
        
        if not username or len(username) < 3:
            raise ValidationError("Username must be at least 3 characters")
        
        if not password or len(password) < 8:
            raise ValidationError("Password must be at least 8 characters")
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'Email already registered'}), 409
        
        if User.query.filter_by(username=username).first():
            return jsonify({'error': 'Username already taken'}), 409
        
        # Create new user
        user = User(
            email=email,
            username=username,
            password=password,
            first_name=first_name or None,
            last_name=last_name or None
        )
        
        db.session.add(user)
        db.session.commit()
        
        # Generate JWT token (8 hours for paper trading app)
        token = user.generate_jwt_token(expires_in=28800)  # 8 hours in seconds
        
        logger.info(f"New user registered: {email}")
        
        return jsonify({
            'message': 'User registered successfully',
            'user': user.to_dict(),
            'token': token
        }), 201
        
    except ValidationError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return jsonify({'error': 'Registration failed'}), 500

@auth_bp.route('/login', methods=['POST'])
@handle_validation_error
def login():
    """Login user"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No JSON data provided'}), 400
    
    try:
        # Get credentials
        email_or_username = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not email_or_username or not password:
            return jsonify({'error': 'Email/username and password are required'}), 400
        
        # Find user by email or username
        user = None
        if '@' in email_or_username:
            user = User.query.filter_by(email=email_or_username).first()
        else:
            user = User.query.filter_by(username=email_or_username).first()
        
        if not user or not user.check_password(password):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        if not user.is_active:
            return jsonify({'error': 'Account is deactivated'}), 401
        
        # Update last login
        user.update_last_login()
        
        # Generate JWT token (8 hours for paper trading app)
        token = user.generate_jwt_token(expires_in=28800)  # 8 hours in seconds
        
        logger.info(f"User logged in: {user.email}")
        
        return jsonify({
            'message': 'Login successful',
            'user': user.to_dict(),
            'token': token
        }), 200
        
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({'error': 'Login failed'}), 500

@auth_bp.route('/profile', methods=['GET'])
@token_required
def get_profile():
    """Get current user profile"""
    from flask import g
    return jsonify({
        'user': g.current_user.to_dict()
    }), 200

@auth_bp.route('/profile', methods=['PUT'])
@token_required
@handle_validation_error
def update_profile():
    """Update user profile"""
    from flask import g
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No JSON data provided'}), 400
    
    try:
        user = g.current_user
        
        # Update allowed fields
        if 'first_name' in data:
            user.first_name = data['first_name'].strip() or None
        
        if 'last_name' in data:
            user.last_name = data['last_name'].strip() or None
        
        # Email update requires special handling
        if 'email' in data:
            new_email = data['email'].strip().lower()
            if new_email != user.email:
                if User.query.filter_by(email=new_email).first():
                    return jsonify({'error': 'Email already in use'}), 409
                user.email = new_email
        
        db.session.commit()
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Profile update error: {e}")
        return jsonify({'error': 'Profile update failed'}), 500

@auth_bp.route('/change-password', methods=['POST'])
@token_required
@handle_validation_error
def change_password():
    """Change user password"""
    from flask import g
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No JSON data provided'}), 400
    
    try:
        current_password = data.get('current_password', '')
        new_password = data.get('new_password', '')
        
        if not current_password or not new_password:
            return jsonify({'error': 'Current and new password are required'}), 400
        
        user = g.current_user
        
        # Verify current password
        if not user.check_password(current_password):
            return jsonify({'error': 'Current password is incorrect'}), 401
        
        # Validate new password
        if len(new_password) < 8:
            return jsonify({'error': 'New password must be at least 8 characters'}), 400
        
        # Update password
        user.set_password(new_password)
        db.session.commit()
        
        logger.info(f"Password changed for user: {user.email}")
        
        return jsonify({'message': 'Password changed successfully'}), 200
        
    except Exception as e:
        logger.error(f"Password change error: {e}")
        return jsonify({'error': 'Password change failed'}), 500

@auth_bp.route('/api-keys', methods=['GET'])
@token_required
def get_api_keys():
    """Get user's API keys"""
    from flask import g
    
    api_keys = APIKey.query.filter_by(user_id=g.current_user.id).all()
    
    return jsonify({
        'api_keys': [key.to_dict() for key in api_keys]
    }), 200

@auth_bp.route('/api-keys', methods=['POST'])
@token_required
@handle_validation_error
def create_api_key():
    """Create new API key"""
    from flask import g
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No JSON data provided'}), 400
    
    try:
        name = data.get('name', '').strip()
        if not name:
            return jsonify({'error': 'API key name is required'}), 400
        
        # Generate secure API key
        raw_key = f"sk-{secrets.token_urlsafe(32)}"
        
        # Create API key record
        api_key = APIKey(
            user_id=g.current_user.id,
            raw_key=raw_key,
            name=name
        )
        
        db.session.add(api_key)
        db.session.commit()
        
        logger.info(f"API key created for user: {g.current_user.email}")
        
        return jsonify({
            'message': 'API key created successfully',
            'api_key': {
                **api_key.to_dict(),
                'key': raw_key  # Only show raw key once at creation
            }
        }), 201
        
    except Exception as e:
        logger.error(f"API key creation error: {e}")
        return jsonify({'error': 'API key creation failed'}), 500

@auth_bp.route('/api-keys/<int:key_id>', methods=['DELETE'])
@token_required
def delete_api_key(key_id):
    """Delete API key"""
    from flask import g
    
    try:
        api_key = APIKey.query.filter_by(
            id=key_id, 
            user_id=g.current_user.id
        ).first()
        
        if not api_key:
            return jsonify({'error': 'API key not found'}), 404
        
        db.session.delete(api_key)
        db.session.commit()
        
        logger.info(f"API key deleted for user: {g.current_user.email}")
        
        return jsonify({'message': 'API key deleted successfully'}), 200
        
    except Exception as e:
        logger.error(f"API key deletion error: {e}")
        return jsonify({'error': 'API key deletion failed'}), 500