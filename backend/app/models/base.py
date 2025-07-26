from datetime import datetime, timezone
from ..db import db

def utc_now():
    """Helper function to get current UTC datetime"""
    return datetime.now(timezone.utc)

class TimestampMixin:
    """Mixin for adding timestamp columns to models"""
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now, nullable=False)

class BaseModel(db.Model, TimestampMixin):
    """Base model class with common functionality"""
    __abstract__ = True
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    def to_dict(self):
        """Convert model instance to dictionary"""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
    
    def update(self, **kwargs):
        """Update model attributes"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = utc_now()  # Remove the extra () you had
    
    def __repr__(self):
        return f"<{self.__class__.__name__}(id={self.id})>"