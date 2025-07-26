from flask.cli import with_appcontext
import click
from flask import current_app
from sqlalchemy import create_engine
from .db import db

def register_cli_commands(app):

    @app.cli.command("init-db")
    @with_appcontext
    def init_db():
        """Initialize the database."""
        database_url = current_app.config.get('DATABASE_URL', 'postgresql://user:pass@localhost:5432/stockdb')
        engine = create_engine(database_url)
        db.metadata.create_all(engine)
        click.echo("✅ Initialized the database.")

    @app.cli.command("drop-db")
    @with_appcontext
    def drop_db():
        """Drop all tables."""
        database_url = current_app.config.get('DATABASE_URL', 'postgresql://user:pass@localhost:5432/stockdb')
        engine = create_engine(database_url)
        db.metadata.drop_all(engine)
        click.echo("🗑 Dropped the database.")