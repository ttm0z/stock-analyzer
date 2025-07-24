"""
Authentication models
"""
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import jwt
import os
from ..db import db

class User(db.Model):
    """User model for authentication"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # User status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # Profile info
    first_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=True)
    
    # Preferences and settings
    preferences = db.Column(db.Text, nullable=True)
    deactivated_at = db.Column(db.DateTime, nullable=True)
    deactivation_reason = db.Column(db.Text, nullable=True)
    
    # Relationships
    portfolios = db.relationship("Portfolio", back_populates="user", lazy='dynamic')
    
    def __init__(self, email, username, password, first_name=None, last_name=None):
        self.email = email.lower().strip()
        self.username = username.strip()
        self.password_hash = generate_password_hash(password)
        self.first_name = first_name
        self.last_name = last_name
    
    def check_password(self, password):
        """Check if provided password matches hash"""
        return check_password_hash(self.password_hash, password)
    
    def set_password(self, password):
        """Set new password"""
        self.password_hash = generate_password_hash(password)
    
    def generate_jwt_token(self, expires_in=3600):
        """Generate JWT token for user"""
        try:
            secret_key = os.getenv('JWT_SECRET_KEY')
            if not secret_key:
                raise ValueError("JWT_SECRET_KEY environment variable is not set")
            
            payload = {
                'user_id': self.id,
                'username': self.username,
                'email': self.email,
                'exp': datetime.utcnow() + timedelta(seconds=expires_in),
                'iat': datetime.utcnow()
            }
            
            token = jwt.encode(
                payload,
                secret_key,
                algorithm='HS256'
            )
            
            # JWT returns bytes in older versions, string in newer versions
            if isinstance(token, bytes):
                token = token.decode('utf-8')
                
            return token
        except Exception as e:
            print(f"JWT token generation error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod
    def decode_jwt_token(token):
        """Decode JWT token and return user"""
        try:
            payload = jwt.decode(
                token,
                os.getenv('JWT_SECRET_KEY'),
                algorithms=['HS256']
            )
            return User.query.get(payload['user_id'])
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return None
    
    def update_last_login(self):
        """Update last login timestamp"""
        self.last_login = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self):
        """Convert user to dictionary (exclude sensitive data)"""
        return {
            'id': self.id,
            'email': self.email,
            'username': self.username,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
    
    def __repr__(self):
        return f'<User {self.username}>'

class APIKey(db.Model):
    """API Key model for API access"""
    __tablename__ = 'api_keys'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    key_hash = db.Column(db.String(255), nullable=False, unique=True)
    name = db.Column(db.String(100), nullable=False)
    
    # Key status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_used = db.Column(db.DateTime, nullable=True)
    expires_at = db.Column(db.DateTime, nullable=True)
    
    # Usage tracking
    usage_count = db.Column(db.Integer, default=0, nullable=False)
    
    # Relationships
    user = db.relationship('User', backref='api_keys')
    
    def __init__(self, user_id, raw_key, name, expires_at=None):
        self.user_id = user_id
        self.key_hash = generate_password_hash(raw_key)
        self.name = name
        self.expires_at = expires_at
    
    def check_key(self, raw_key):
        """Check if provided key matches hash"""
        return check_password_hash(self.key_hash, raw_key)
    
    def is_valid(self):
        """Check if API key is valid"""
        if not self.is_active:
            return False
        
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False
        
        return True
    
    def record_usage(self):
        """Record API key usage"""
        self.last_used = datetime.utcnow()
        self.usage_count += 1
        db.session.commit()
    
    def to_dict(self):
        """Convert API key to dictionary (exclude sensitive data)"""
        return {
            'id': self.id,
            'name': self.name,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'usage_count': self.usage_count
        }