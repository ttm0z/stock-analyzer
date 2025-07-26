from datetime import datetime
from .base import BaseModel
from ..db import db
# ApiKey model is now in auth.models to avoid conflicts

class UserSession(BaseModel):
    """User session tracking for active sessions."""
    __tablename__ = 'user_sessions'
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    session_token = db.Column(db.String(255), nullable=False, unique=True, index=True)
    
    # Session metadata
    ip_address = db.Column(db.String(45), nullable=True)  # Support IPv6
    user_agent = db.Column(db.String(500), nullable=True)
    device_info = db.Column(db.JSON, nullable=True)  # Device fingerprint data
    
    # Session status
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=False, index=True)
    
    # Security tracking
    login_method = db.Column(db.String(20), default='password', nullable=False)  # password, api_key, oauth
    two_factor_verified = db.Column(db.Boolean, default=False, nullable=False)
    location_data = db.Column(db.JSON, nullable=True)  # Geolocation info
    
    # Relationships
    user = db.relationship("User", backref="sessions")
    
    # Indexes and constraints
    __table_args__ = (
        db.Index('idx_user_session_active', 'user_id', 'is_active', 'last_activity'),
        db.Index('idx_session_token_expires', 'session_token', 'expires_at'),
        db.CheckConstraint('login_method IN (\'password\', \'api_key\', \'oauth\')', name='ck_login_method_valid'),
        db.CheckConstraint('expires_at > created_at', name='ck_expires_after_created'),
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
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    
    # Display preferences
    theme = db.Column(db.String(20), default='light', nullable=False)
    language = db.Column(db.String(10), default='en', nullable=False)
    timezone = db.Column(db.String(50), default='UTC', nullable=False)
    currency = db.Column(db.String(3), default='USD', nullable=False)
    
    # Trading preferences
    default_order_type = db.Column(db.String(20), default='MARKET', nullable=False)
    confirmations_enabled = db.Column(db.Boolean, default=True, nullable=False)
    
    # Notification preferences
    email_notifications = db.Column(db.Boolean, default=True, nullable=False)
    price_alerts = db.Column(db.Boolean, default=True, nullable=False)
    portfolio_alerts = db.Column(db.Boolean, default=True, nullable=False)
    
    # Dashboard preferences
    dashboard_layout = db.Column(db.JSON, nullable=True)
    favorite_symbols = db.Column(db.JSON, nullable=True)  # List of favorite stock symbols
    watchlist_settings = db.Column(db.JSON, nullable=True)
    
    # Risk preferences
    risk_tolerance = db.Column(db.String(20), default='moderate', nullable=False)  # conservative, moderate, aggressive
    max_position_size_pct = db.Column(db.Integer, default=10, nullable=False)  # Max % of portfolio per position
    
    # Relationships
    user = db.relationship("User", back_populates="user_preferences")
    
    # Constraints
    __table_args__ = (
        db.CheckConstraint('theme IN (\'light\', \'dark\')', name='ck_theme_valid'),
        db.CheckConstraint('risk_tolerance IN (\'conservative\', \'moderate\', \'aggressive\')', name='ck_risk_tolerance_valid'),
        db.CheckConstraint('max_position_size_pct BETWEEN 1 AND 100', name='ck_max_position_size_valid'),
        db.CheckConstraint('length(currency) = 3', name='ck_currency_length'),
    )