from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def init_db(app):
    """Initialize database with Flask app"""
    # db.init_app is called in create_app already
    with app.app_context():
        db.create_all()
