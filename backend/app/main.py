"""StudyBuddy Flask Backend Application"""
import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from app.config import Config
from app.database import db, init_db
from app.routers.auth import auth_bp
from app.routers.files import files_bp
from app.routers.audio import audio_bp
from app.routers.quizzes import quizzes_bp
from app.routers.chat import chat_bp
from app.routers.progress import progress_bp


def create_app():
    """Application factory for Flask app"""
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = Config.SECRET_KEY
    app.config['JWT_SECRET_KEY'] = Config.JWT_SECRET_KEY
    app.config['SQLALCHEMY_DATABASE_URI'] = Config.DATABASE_URL
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = Config.UPLOAD_FOLDER
    app.config['AUDIO_FOLDER'] = Config.AUDIO_FOLDER
    app.config['MAX_CONTENT_LENGTH'] = Config.MAX_FILE_SIZE
    
    # Initialize extensions
    db.init_app(app)
    
    # Configure JWT
    jwt = JWTManager(app)
    
    # Configure CORS
    CORS(app, 
         origins=Config.ALLOWED_ORIGINS,
         supports_credentials=True,
         allow_headers=['Content-Type', 'Authorization'],
         methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'])
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(files_bp)
    app.register_blueprint(audio_bp)
    app.register_blueprint(quizzes_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(progress_bp)
    
    # Create directories
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(Config.AUDIO_FOLDER, exist_ok=True)
    
    # Root endpoint
    @app.route('/')
    def root():
        return jsonify({
            'message': 'Welcome to StudyBuddy API',
            'version': '1.0.0',
            'docs': '/docs'
        })
    
    # Health check
    @app.route('/health')
    def health():
        return jsonify({'status': 'healthy'})
    
    # API docs placeholder
    @app.route('/docs')
    def docs():
        return jsonify({
            'message': 'API Documentation',
            'endpoints': {
                'auth': '/api/auth',
                'files': '/api/files',
                'audio': '/api/audio',
                'quizzes': '/api/quizzes',
                'chat': '/api/chat',
                'progress': '/api/progress'
            }
        })
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Endpoint not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500
    
    @app.errorhandler(422)
    def validation_error(error):
        return jsonify({'error': 'Validation error'}), 422
    
    # Initialize database
    with app.app_context():
        init_db(app)
    
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=8000, debug=True)
