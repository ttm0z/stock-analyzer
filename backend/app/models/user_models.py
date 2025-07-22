from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import uuid

from .base import BaseModel

class User(BaseModel):
    """User model for authentication and user management"""
    __tablename__ = 'users'
    
    username = Column(String(80), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(50), nullable=True)
    last_name = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    email_verified = Column(Boolean, default=False, nullable=False)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    strategies = relationship("Strategy", back_populates="user", cascade="all, delete-orphan")
    backtests = relationship("Backtest", back_populates="user", cascade="all, delete-orphan")
    portfolios = relationship("Portfolio", back_populates="user", cascade="all, delete-orphan")
    api_keys = relationship("ApiKey", back_populates="user", cascade="all, delete-orphan")
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if password matches hash"""
        return check_password_hash(self.password_hash, password)
    
    def get_full_name(self):
        """Get user's full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    def to_dict(self, include_sensitive=False):
        """Convert to dictionary, optionally excluding sensitive data"""
        data = super().to_dict()
        if not include_sensitive:
            data.pop('password_hash', None)
        return data

class ApiKey(BaseModel):
    """API key model for programmatic access"""
    __tablename__ = 'api_keys'
    
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    key_name = Column(String(100), nullable=False)
    key_hash = Column(String(255), nullable=False, unique=True)
    key_prefix = Column(String(10), nullable=False)  # First few chars for identification
    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    last_used = Column(DateTime, nullable=True)
    permissions = Column(Text, nullable=True)  # JSON string of permissions
    
    # Relationships
    user = relationship("User", back_populates="api_keys")
    
    @classmethod
    def generate_key(cls):
        """Generate a new API key"""
        key = f"bt_{uuid.uuid4().hex}"
        return key
    
    def is_expired(self):
        """Check if API key is expired"""
        if self.expires_at:
            return datetime.utcnow() > self.expires_at
        return False
    
    def is_valid(self):
        """Check if API key is valid"""
        return self.is_active and not self.is_expired()

class UserSession(BaseModel):
    """User session model for tracking active sessions"""
    __tablename__ = 'user_sessions'
    
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    session_token = Column(String(255), nullable=False, unique=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(Text, nullable=True)
    expires_at = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    user = relationship("User")
    
    def is_expired(self):
        """Check if session is expired"""
        return datetime.utcnow() > self.expires_at
    
    def is_valid(self):
        """Check if session is valid"""
        return self.is_active and not self.is_expired()

class UserPreferences(BaseModel):
    """User preferences and settings"""
    __tablename__ = 'user_preferences'
    
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, unique=True)
    theme = Column(String(20), default='light', nullable=False)  # light, dark
    timezone = Column(String(50), default='UTC', nullable=False)
    currency = Column(String(10), default='USD', nullable=False)
    date_format = Column(String(20), default='YYYY-MM-DD', nullable=False)
    number_format = Column(String(20), default='US', nullable=False)
    default_commission = Column(String(20), default='0.001', nullable=False)  # 0.1%
    default_slippage = Column(String(20), default='0.0005', nullable=False)  # 0.05%
    email_notifications = Column(Boolean, default=True, nullable=False)
    backtest_notifications = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    user = relationship("User")
    
    def to_dict(self):
        """Convert to dictionary with proper type conversion"""
        data = super().to_dict()
        # Convert string percentages to floats
        data['default_commission'] = float(data['default_commission'])
        data['default_slippage'] = float(data['default_slippage'])
        return data