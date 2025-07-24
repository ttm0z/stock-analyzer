"""
Settings and User Preferences API routes
"""
from flask import Blueprint, request, jsonify, current_app
from ..db import db
from ..auth.models import User
from ..auth.decorators import token_required
from ..utils.validation import InputValidator, ValidationError, handle_validation_error
import json
import logging
from datetime import datetime

settings_bp = Blueprint('settings', __name__)
logger = logging.getLogger(__name__)

@settings_bp.route('/preferences', methods=['GET'])
@token_required
def get_user_preferences():
    """Get user preferences"""
    from flask import g
    
    try:
        user = g.current_user
        
        # For now, we'll store preferences in a JSON field
        # In production, you might want a separate preferences table
        preferences = getattr(user, 'preferences', None)
        
        if not preferences:
            # Return default preferences
            preferences = {
                'theme': 'light',
                'notifications': {
                    'email': True,
                    'push': False,
                    'portfolio': True,
                    'alerts': True,
                    'news': False
                },
                'trading': {
                    'defaultPortfolioType': 'paper',
                    'confirmTrades': True,
                    'autoSave': True,
                    'riskWarnings': True
                },
                'display': {
                    'currency': 'USD',
                    'dateFormat': 'MM/DD/YYYY',
                    'timeFormat': '12h',
                    'language': 'en'
                }
            }
        else:
            if isinstance(preferences, str):
                preferences = json.loads(preferences)
        
        return jsonify({
            'preferences': preferences
        }), 200
        
    except Exception as e:
        logger.error(f"Get preferences error: {e}")
        return jsonify({'error': 'Failed to get preferences'}), 500

@settings_bp.route('/preferences', methods=['PUT'])
@token_required
@handle_validation_error
def update_user_preferences():
    """Update user preferences"""
    from flask import g
    
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No JSON data provided'}), 400
    
    try:
        user = g.current_user
        preferences = data.get('preferences', {})
        
        # Validate preferences structure
        valid_themes = ['light', 'dark']
        valid_currencies = ['USD', 'EUR', 'GBP', 'JPY']
        valid_date_formats = ['MM/DD/YYYY', 'DD/MM/YYYY', 'YYYY-MM-DD']
        valid_time_formats = ['12h', '24h']
        valid_languages = ['en', 'es', 'fr', 'de']
        
        if 'theme' in preferences and preferences['theme'] not in valid_themes:
            return jsonify({'error': 'Invalid theme selection'}), 400
            
        if 'display' in preferences:
            display = preferences['display']
            if 'currency' in display and display['currency'] not in valid_currencies:
                return jsonify({'error': 'Invalid currency selection'}), 400
            if 'dateFormat' in display and display['dateFormat'] not in valid_date_formats:
                return jsonify({'error': 'Invalid date format selection'}), 400
            if 'timeFormat' in display and display['timeFormat'] not in valid_time_formats:
                return jsonify({'error': 'Invalid time format selection'}), 400
            if 'language' in display and display['language'] not in valid_languages:
                return jsonify({'error': 'Invalid language selection'}), 400
        
        # Store preferences as JSON
        # Note: In production, consider adding a preferences column to the user table
        # or creating a separate user_preferences table
        user.preferences = json.dumps(preferences)
        db.session.commit()
        
        logger.info(f"Preferences updated for user: {user.email}")
        
        return jsonify({
            'message': 'Preferences updated successfully',
            'preferences': preferences
        }), 200
        
    except Exception as e:
        logger.error(f"Update preferences error: {e}")
        return jsonify({'error': 'Failed to update preferences'}), 500

@settings_bp.route('/notifications/test', methods=['POST'])
@token_required
def test_notifications():
    """Test notification settings"""
    from flask import g
    
    data = request.get_json()
    notification_type = data.get('type', 'email')
    
    try:
        user = g.current_user
        
        if notification_type == 'email':
            # In production, you would send an actual test email
            logger.info(f"Test email notification sent to: {user.email}")
            return jsonify({
                'message': f'Test email sent to {user.email}'
            }), 200
        elif notification_type == 'push':
            # In production, you would send an actual push notification
            logger.info(f"Test push notification sent to user: {user.id}")
            return jsonify({
                'message': 'Test push notification sent'
            }), 200
        else:
            return jsonify({'error': 'Invalid notification type'}), 400
            
    except Exception as e:
        logger.error(f"Test notification error: {e}")
        return jsonify({'error': 'Failed to send test notification'}), 500

@settings_bp.route('/data-export', methods=['POST'])
@token_required
def export_user_data():
    """Export user data"""
    from flask import g
    
    data = request.get_json()
    export_type = data.get('type', 'json')
    include_portfolios = data.get('include_portfolios', True)
    include_trades = data.get('include_trades', True)
    include_preferences = data.get('include_preferences', True)
    
    try:
        user = g.current_user
        export_data = {
            'user_info': user.to_dict(),
            'export_date': datetime.utcnow().isoformat(),
            'export_type': export_type
        }
        
        if include_preferences:
            preferences = getattr(user, 'preferences', None)
            if preferences:
                if isinstance(preferences, str):
                    preferences = json.loads(preferences)
                export_data['preferences'] = preferences
        
        if include_portfolios:
            # Get user's portfolios
            portfolios = user.portfolios.all()
            export_data['portfolios'] = [portfolio.to_dict() for portfolio in portfolios]
        
        if include_trades:
            # In production, you would get actual trade data
            export_data['trades'] = []
        
        logger.info(f"Data export generated for user: {user.email}")
        
        return jsonify({
            'message': 'Data export generated successfully',
            'data': export_data,
            'download_url': f'/api/settings/download/{user.id}',  # In production, generate a secure download link
            'expires_in': 3600  # 1 hour
        }), 200
        
    except Exception as e:
        logger.error(f"Data export error: {e}")
        return jsonify({'error': 'Failed to export data'}), 500

@settings_bp.route('/account/deactivate', methods=['POST'])
@token_required
def deactivate_account():
    """Deactivate user account"""
    from flask import g
    
    data = request.get_json()
    confirmation = data.get('confirmation', '')
    reason = data.get('reason', '')
    
    if confirmation.lower() != 'deactivate':
        return jsonify({'error': 'Invalid confirmation'}), 400
    
    try:
        user = g.current_user
        
        # Deactivate account instead of deleting
        user.is_active = False
        user.deactivated_at = datetime.utcnow()
        user.deactivation_reason = reason
        
        db.session.commit()
        
        logger.info(f"Account deactivated for user: {user.email}")
        
        return jsonify({
            'message': 'Account deactivated successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Account deactivation error: {e}")
        return jsonify({'error': 'Failed to deactivate account'}), 500

@settings_bp.route('/security/sessions', methods=['GET'])
@token_required
def get_active_sessions():
    """Get active user sessions"""
    from flask import g
    
    try:
        user = g.current_user
        
        # In production, you would track actual sessions
        # For now, return mock session data
        sessions = [
            {
                'id': 'current',
                'device': 'Web Browser',
                'location': 'Unknown',
                'ip_address': request.remote_addr,
                'last_active': datetime.utcnow().isoformat(),
                'is_current': True
            }
        ]
        
        return jsonify({
            'sessions': sessions
        }), 200
        
    except Exception as e:
        logger.error(f"Get sessions error: {e}")
        return jsonify({'error': 'Failed to get sessions'}), 500

@settings_bp.route('/security/sessions/<session_id>', methods=['DELETE'])
@token_required
def revoke_session(session_id):
    """Revoke a specific session"""
    from flask import g
    
    if session_id == 'current':
        return jsonify({'error': 'Cannot revoke current session'}), 400
    
    try:
        user = g.current_user
        
        # In production, you would revoke the actual session
        logger.info(f"Session {session_id} revoked for user: {user.email}")
        
        return jsonify({
            'message': 'Session revoked successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Revoke session error: {e}")
        return jsonify({'error': 'Failed to revoke session'}), 500

@settings_bp.route('/security/login-history', methods=['GET'])
@token_required
def get_login_history():
    """Get user login history"""
    from flask import g
    
    try:
        user = g.current_user
        
        # In production, you would track actual login history
        # For now, return mock data
        history = [
            {
                'timestamp': datetime.utcnow().isoformat(),
                'ip_address': request.remote_addr,
                'device': 'Web Browser',
                'location': 'Unknown',
                'status': 'success'
            }
        ]
        
        return jsonify({
            'login_history': history
        }), 200
        
    except Exception as e:
        logger.error(f"Get login history error: {e}")
        return jsonify({'error': 'Failed to get login history'}), 500