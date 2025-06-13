from flask import Flask
from flask_cors import CORS
from .db import db

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}})

    from .routes import api_bp
    app.register_blueprint(api_bp)

    with app.app_context():
        db.create_all()

    return app
