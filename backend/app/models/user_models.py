from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Index, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from .base import BaseModel
# ApiKey model is now in auth.models to avoid conflicts

class UserSession(BaseModel):
    """User session tracking for active sessions."""
    __tablename__ = 'user_sessions'
    
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    session_token = Column(String(255), nullable=False, unique=True, index=True)
    
    # Session metadata
    ip_address = Column(String(45), nullable=True)  # Support IPv6
    user_agent = Column(String(500), nullable=True)
    device_info = Column(JSONB, nullable=True)  # Device fingerprint data
    
    # Session status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    last_activity = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    
    # Security tracking
    login_method = Column(String(20), default='password', nullable=False)  # password, api_key, oauth
    two_factor_verified = Column(Boolean, default=False, nullable=False)
    location_data = Column(JSONB, nullable=True)  # Geolocation info
    
    # Relationships
    user = relationship("User", backref="sessions")
    
    # Indexes and constraints
    __table_args__ = (
        Index('idx_user_session_active', 'user_id', 'is_active', 'last_activity'),
        Index('idx_session_token_expires', 'session_token', 'expires_at'),
        CheckConstraint('login_method IN (\'password\', \'api_key\', \'oauth\')', name='ck_login_method_valid'),
        CheckConstraint('expires_at > created_at', name='ck_expires_after_created'),
    )
    
    def is_expired(self):
        """Check if session is expired."""
        return datetime.utcnow() > self.expires_at
    
    def is_valid(self):
        """Check if session is valid (active and not expired)."""
        return self.is_active and not self.is_expired()
    
    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity = datetime.utcnow()

# User model is now imported from auth.models to avoid conflicts

class UserPreferences(BaseModel):
    """User preferences and settings."""
    __tablename__ = 'user_preferences'
    
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, unique=True)
    
    # Display preferences
    theme = Column(String(20), default='light', nullable=False)
    language = Column(String(10), default='en', nullable=False)
    timezone = Column(String(50), default='UTC', nullable=False)
    currency = Column(String(3), default='USD', nullable=False)
    
    # Trading preferences
    default_order_type = Column(String(20), default='MARKET', nullable=False)
    confirmations_enabled = Column(Boolean, default=True, nullable=False)
    
    # Notification preferences
    email_notifications = Column(Boolean, default=True, nullable=False)
    price_alerts = Column(Boolean, default=True, nullable=False)
    portfolio_alerts = Column(Boolean, default=True, nullable=False)
    
    # Dashboard preferences
    dashboard_layout = Column(JSONB, nullable=True)
    favorite_symbols = Column(JSONB, nullable=True)  # List of favorite stock symbols
    watchlist_settings = Column(JSONB, nullable=True)
    
    # Risk preferences
    risk_tolerance = Column(String(20), default='moderate', nullable=False)  # conservative, moderate, aggressive
    max_position_size_pct = Column(Integer, default=10, nullable=False)  # Max % of portfolio per position
    
    # Relationships
    user = relationship("User", back_populates="user_preferences")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('theme IN (\'light\', \'dark\')', name='ck_theme_valid'),
        CheckConstraint('risk_tolerance IN (\'conservative\', \'moderate\', \'aggressive\')', name='ck_risk_tolerance_valid'),
        CheckConstraint('max_position_size_pct BETWEEN 1 AND 100', name='ck_max_position_size_valid'),
        CheckConstraint('length(currency) = 3', name='ck_currency_length'),
    )