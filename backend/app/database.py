"""
Database session management utilities
"""
from flask import current_app, g
from contextlib import contextmanager


def get_db_session():
    """Get database session from Flask app context"""
    if 'db_session' not in g:
        Session = current_app.config['SESSION_FACTORY']
        g.db_session = Session()
    return g.db_session


@contextmanager
def db_session_scope():
    """Provide a transactional scope around database operations"""
    session = get_db_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def close_db_session(error):
    """Close database session at end of request"""
    session = g.pop('db_session', None)
    if session is not None:
        session.close()


def init_db_session_handlers(app):
    """Initialize database session handlers"""
    app.teardown_appcontext(close_db_session)