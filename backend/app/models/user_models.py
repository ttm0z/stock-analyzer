# Import optimized User model from new location
from ...models.user import User, UserPreferences
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import uuid

from .base import BaseModel

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