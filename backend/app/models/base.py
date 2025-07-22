from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class TimestampMixin:
    """Mixin for adding timestamp columns to models"""
    created_at = Column(DateTime, default=datetime.astimezone.utc, nullable=False)
    updated_at = Column(DateTime, default=datetime.astimezone.utc, onupdate=datetime.astimezone.utc, nullable=False)

class BaseModel(Base, TimestampMixin):
    """Base model class with common functionality"""
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
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
        self.updated_at = datetime.astimezone.utc()
    
    def __repr__(self):
        return f"<{self.__class__.__name__}(id={self.id})>"