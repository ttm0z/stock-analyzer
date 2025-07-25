from sqlalchemy import Column, Integer, DateTime, CheckConstraint
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class BaseModel(Base):
    """Base model class with common fields and methods for all models."""
    __abstract__ = True
    
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        """Convert model instance to dictionary."""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                result[column.name] = value.isoformat()
            elif hasattr(value, '__float__') and hasattr(value, 'is_finite'):
                # Handle Decimal/Numeric types
                result[column.name] = float(value) if value is not None else None
            else:
                result[column.name] = value
        return result
    
    def update(self, **kwargs):
        """Update model instance with keyword arguments."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.utcnow()
    
    @classmethod
    def create(cls, **kwargs):
        """Create new instance of the model."""
        instance = cls(**kwargs)
        return instance
    
    def __repr__(self):
        return f"<{self.__class__.__name__}(id={self.id})>"