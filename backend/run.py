import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    # Only enable debug in development environment
    debug_mode = os.getenv('FLASK_ENV') == 'development'
    app.run(
        debug=debug_mode,
        host=os.getenv('FLASK_HOST', '127.0.0.1'),  # Secure default
        port=int(os.getenv('FLASK_PORT', 5000))
    )
