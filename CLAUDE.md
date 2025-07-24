# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Frontend (React + Vite)
```bash
cd frontend
npm run dev          # Start development server
npm run build        # Build for production
npm run lint         # Run ESLint
npm run preview      # Preview production build
```

### Backend (Flask + Python)
```bash
cd backend
python run.py                    # Start Flask development server
python start_secure.py          # Start with security checks and Redis
python quick_security_setup.py  # Initial security setup
pip install -r requirements.txt # Install dependencies
```

### Redis Setup
```bash
cd backend
redis-server app/redis.conf  # Start Redis with project config
python test_redis.py         # Test Redis connection
```

## Architecture Overview

This is a full-stack stock analysis application with JWT-based authentication, Redis caching, and real-time market data.

### Backend Architecture
- **Flask Application Factory Pattern**: Main app created in `backend/app/__init__.py:create_app()`
- **Blueprint-based Routing**: Routes organized by domain (auth, portfolio, market, etc.) in `backend/app/routes/`
- **Service Layer**: Business logic in `backend/app/services/` with caching via Redis
- **Database**: SQLAlchemy models in `backend/app/models/` with PostgreSQL backend
- **Authentication**: JWT tokens with secure session management in `backend/app/auth/`
- **Caching**: Redis-based caching service in `backend/app/services/cache_service.py`

### Frontend Architecture
- **React with React Router**: SPA architecture with protected routes
- **Context-based State**: Authentication state managed via `frontend/src/contexts/AuthContext.jsx`
- **Service Layer**: API calls organized in `frontend/src/services/` (authAPI, stockAPI, portfolioAPI, etc.)
- **Component Structure**: Feature-based organization under `frontend/src/components/`

### Key Integrations
- **Financial Data**: Financial Modeling Prep API (FMP_API_KEY required)
- **Market Data**: Yahoo Finance via yfinance library
- **Caching**: Redis for performance optimization with intelligent TTL
- **Security**: CSRF protection, secure cookies, environment-based configuration

## Environment Requirements

### Required Environment Variables (.env in backend/)
```
FLASK_SECRET_KEY=<64-char-hex-key>
JWT_SECRET_KEY=<64-char-hex-key>
FMP_API_KEY=<financial-modeling-prep-api-key>
REDIS_PASSWORD=<redis-password>
DATABASE_URL=postgresql://stockuser:password@localhost:5432/stockdb
```

### Setup Scripts
- `backend/quick_security_setup.py` - Generates secure keys and sets up environment
- `backend/setup_security.py` - Enhanced security configuration
- `backend/start_secure.py` - Production-ready startup with pre-flight checks

## Database & Services

### Database Models
- User authentication: `backend/app/auth/models.py`
- Portfolio management: `backend/app/models/portfolio_models.py`
- Market data: `backend/app/models/market_data.py`
- Backtesting: `backend/app/models/backtest_models.py`
- Trading strategies: `backend/app/models/strategy_models.py`

### Cache Configuration
- Real-time quotes: 60 seconds TTL
- Company profiles: 1 hour TTL
- Historical data: 1 hour TTL
- Search results: 5 minutes TTL
- Market news: 5 minutes TTL

## Security Features

- JWT authentication with secure token handling
- CSRF protection via Flask-WTF
- Redis password authentication
- Environment-based configuration
- Secure cookie settings for production
- Input validation and sanitization

## Common Development Patterns

- All API routes are prefixed with `/api/`
- Frontend uses axios with interceptors for auth tokens
- Error handling follows consistent patterns across services
- Database operations use SQLAlchemy ORM
- Cache keys follow pattern: `{CACHE_KEY_PREFIX}:{domain}:{identifier}`

## Testing

- Frontend: ESLint for code quality
- Backend: Test files in `backend/app/tests/` (run with pytest when configured)
- Redis: `backend/test_redis.py` for connection testing
- Security: `backend/test_security.py` for security validation