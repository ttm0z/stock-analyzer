from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Index, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from .base import BaseModel

class User(BaseModel):
    """User model for authentication and profile management."""
    __tablename__ = 'users'
    
    # Basic user information
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    
    # Authentication
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    last_login = Column(DateTime, nullable=True)
    password_changed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    portfolios = relationship("Portfolio", back_populates="user", cascade="all, delete-orphan")
    strategies = relationship("Strategy", back_populates="user", cascade="all, delete-orphan")
    preferences = relationship("UserPreferences", back_populates="user", uselist=False, cascade="all, delete-orphan")
    risk_profiles = relationship("RiskProfile", back_populates="user", cascade="all, delete-orphan")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_user_email_active', 'email', 'is_active'),
        Index('idx_user_username_active', 'username', 'is_active'),
        CheckConstraint('length(username) >= 3', name='ck_username_length'),
        CheckConstraint('email ~* \'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$\'', name='ck_email_format'),
    )
    
    def check_password(self, password):
        """Check if provided password matches the hash."""
        # This would typically use a password hashing library like bcrypt
        from passlib.hash import pbkdf2_sha256
        return pbkdf2_sha256.verify(password, self.password_hash)
    
    def set_password(self, password):
        """Set password hash."""
        from passlib.hash import pbkdf2_sha256
        self.password_hash = pbkdf2_sha256.hash(password)
        self.password_changed_at = datetime.utcnow()
    
    @property
    def full_name(self):
        """Get user's full name."""
        return f"{self.first_name} {self.last_name}"
    
    def to_dict(self, include_sensitive=False):
        """Convert to dictionary, optionally excluding sensitive data."""
        data = super().to_dict()
        if not include_sensitive:
            data.pop('password_hash', None)
        return data

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
    user = relationship("User", back_populates="preferences")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('theme IN (\'light\', \'dark\')', name='ck_theme_valid'),
        CheckConstraint('risk_tolerance IN (\'conservative\', \'moderate\', \'aggressive\')', name='ck_risk_tolerance_valid'),
        CheckConstraint('max_position_size_pct BETWEEN 1 AND 100', name='ck_max_position_size_valid'),
        CheckConstraint('length(currency) = 3', name='ck_currency_length'),
    )