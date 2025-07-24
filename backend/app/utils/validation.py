"""
Input validation and sanitization utilities
"""
import re
from typing import Optional, List, Any, Dict
from flask import abort
import bleach

class ValidationError(Exception):
    """Custom validation error"""
    pass

class InputValidator:
    """Input validation and sanitization"""
    
    # Stock symbol regex - allows A-Z, numbers, and common symbols
    STOCK_SYMBOL_PATTERN = re.compile(r'^[A-Z0-9\.\-]{1,10}$')
    
    # Date patterns
    DATE_PATTERN = re.compile(r'^\d{4}-\d{2}-\d{2}$')
    
    # Safe characters for search queries
    SEARCH_ALLOWED_CHARS = re.compile(r'^[a-zA-Z0-9\s\.\-&\(\)]+$')

    @staticmethod
    def validate_stock_symbol(symbol: str) -> str:
        """Validate and sanitize stock symbol"""
        if not symbol:
            raise ValidationError("Stock symbol is required")
        
        # Clean and uppercase
        cleaned_symbol = symbol.strip().upper()
        
        if not InputValidator.STOCK_SYMBOL_PATTERN.match(cleaned_symbol):
            raise ValidationError(f"Invalid stock symbol format: {symbol}")
        
        if len(cleaned_symbol) > 10:
            raise ValidationError("Stock symbol too long")
            
        return cleaned_symbol

    @staticmethod
    def validate_search_query(query: str) -> str:
        """Validate and sanitize search query"""
        if not query:
            raise ValidationError("Search query is required")
        
        # Clean the query
        cleaned_query = query.strip()
        
        if len(cleaned_query) < 1:
            raise ValidationError("Search query too short")
        
        if len(cleaned_query) > 100:
            raise ValidationError("Search query too long")
        
        # Check for safe characters
        if not InputValidator.SEARCH_ALLOWED_CHARS.match(cleaned_query):
            raise ValidationError("Search query contains invalid characters")
        
        # Use bleach to sanitize HTML/script tags
        sanitized = bleach.clean(cleaned_query, tags=[], attributes={})
        
        return sanitized

    @staticmethod
    def validate_date(date_str: str) -> str:
        """Validate date format YYYY-MM-DD"""
        if not date_str:
            return date_str
        
        cleaned_date = date_str.strip()
        
        if not InputValidator.DATE_PATTERN.match(cleaned_date):
            raise ValidationError(f"Invalid date format. Use YYYY-MM-DD: {date_str}")
        
        return cleaned_date

    @staticmethod
    def validate_limit(limit: Any, max_limit: int = 1000) -> int:
        """Validate and sanitize limit parameter"""
        try:
            limit_int = int(limit) if limit else 50
        except (ValueError, TypeError):
            raise ValidationError("Limit must be a number")
        
        if limit_int < 1:
            raise ValidationError("Limit must be positive")
        
        if limit_int > max_limit:
            raise ValidationError(f"Limit cannot exceed {max_limit}")
        
        return limit_int

    @staticmethod
    def validate_symbols_list(symbols_str: str, max_symbols: int = 50) -> List[str]:
        """Validate list of stock symbols"""
        if not symbols_str:
            raise ValidationError("Symbols list is required")
        
        symbols = [s.strip() for s in symbols_str.split(',') if s.strip()]
        
        if len(symbols) == 0:
            raise ValidationError("No valid symbols provided")
        
        if len(symbols) > max_symbols:
            raise ValidationError(f"Cannot request more than {max_symbols} symbols at once")
        
        validated_symbols = []
        for symbol in symbols:
            validated_symbols.append(InputValidator.validate_stock_symbol(symbol))
        
        return validated_symbols

    @staticmethod
    def sanitize_message_content(content: str) -> str:
        """Sanitize message content for database storage"""
        if not content:
            raise ValidationError("Message content is required")
        
        # Limit length
        if len(content) > 1000:
            raise ValidationError("Message too long (max 1000 characters)")
        
        # Clean HTML tags and dangerous content
        cleaned = bleach.clean(
            content, 
            tags=['b', 'i', 'em', 'strong'],  # Allow basic formatting
            attributes={},
            strip=True
        )
        
        return cleaned.strip()

def validate_required_fields(data: Dict, required_fields: List[str]) -> None:
    """Validate that required fields are present in data"""
    missing_fields = []
    for field in required_fields:
        if field not in data or data[field] is None or str(data[field]).strip() == '':
            missing_fields.append(field)
    
    if missing_fields:
        raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")

def handle_validation_error(func):
    """Decorator to handle validation errors"""
    from functools import wraps
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValidationError as e:
            return {'error': str(e)}, 400
        except Exception as e:
            # Log the error for debugging
            import logging
            logging.error(f"Unexpected error in {func.__name__}: {e}")
            return {'error': 'Internal server error'}, 500
    
    return wrapper