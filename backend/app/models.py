from datetime import datetime
from app.database import db

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    hashed_password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default='user')
    subscription_type = db.Column(db.String(50), default='free')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    files = db.relationship('UploadedFile', backref='owner', cascade='all, delete-orphan')
    audio_lessons = db.relationship('AudioLesson', backref='owner', cascade='all, delete-orphan')
    quizzes = db.relationship('Quiz', backref='owner', cascade='all, delete-orphan')
    quiz_attempts = db.relationship('QuizAttempt', backref='owner', cascade='all, delete-orphan')
    chat_messages = db.relationship('AIChat', backref='owner', cascade='all, delete-orphan')
    progress = db.relationship('StudyProgress', backref='owner', cascade='all, delete-orphan')
    subscriptions = db.relationship('Subscription', backref='owner', cascade='all, delete-orphan')


class UploadedFile(db.Model):
    __tablename__ = 'uploaded_files'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    text_content = db.Column(db.Text)
    summary = db.Column(db.Text)
    status = db.Column(db.String(50), default='processing')  # processing, ready, error
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    audio_lessons = db.relationship('AudioLesson', backref='file', cascade='all, delete-orphan')
    quizzes = db.relationship('Quiz', backref='file', cascade='all, delete-orphan')
    chat_messages = db.relationship('AIChat', backref='file', cascade='all, delete-orphan')
    progress = db.relationship('StudyProgress', backref='file', uselist=False, cascade='all, delete-orphan')


class AudioLesson(db.Model):
    __tablename__ = 'audio_lessons'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    file_id = db.Column(db.Integer, db.ForeignKey('uploaded_files.id'), nullable=False)
    audio_path = db.Column(db.String(500), nullable=False)
    audio_url = db.Column(db.String(500))
    duration = db.Column(db.Float, default=0.0)
    voice_type = db.Column(db.String(50), default='default')
    position_seconds = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Quiz(db.Model):
    __tablename__ = 'quizzes'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    file_id = db.Column(db.Integer, db.ForeignKey('uploaded_files.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    difficulty = db.Column(db.String(50), default='medium')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    questions = db.relationship('QuizQuestion', backref='quiz', cascade='all, delete-orphan')
    attempts = db.relationship('QuizAttempt', backref='quiz', cascade='all, delete-orphan')


class QuizQuestion(db.Model):
    __tablename__ = 'quiz_questions'
    
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    question = db.Column(db.Text, nullable=False)
    options = db.Column(db.JSON, nullable=False)  # List of 4 options
    correct_answer = db.Column(db.Integer, nullable=False)  # Index of correct option (0-3)
    explanation = db.Column(db.Text)


class QuizAttempt(db.Model):
    __tablename__ = 'quiz_attempts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    score = db.Column(db.Integer, default=0)
    correct = db.Column(db.Integer, default=0)
    total = db.Column(db.Integer, default=0)
    answers = db.Column(db.JSON)  # Store user's answers
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)


class AIChat(db.Model):
    __tablename__ = 'ai_chats'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    file_id = db.Column(db.Integer, db.ForeignKey('uploaded_files.id'))
    message = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class StudyProgress(db.Model):
    __tablename__ = 'study_progress'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    file_id = db.Column(db.Integer, db.ForeignKey('uploaded_files.id'), nullable=False)
    completion = db.Column(db.Float, default=0.0)  # Percentage 0-100
    listening_time = db.Column(db.Float, default=0.0)  # In seconds
    quiz_avg = db.Column(db.Float, default=0.0)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'file_id', name='unique_user_file_progress'),)


class Subscription(db.Model):
    __tablename__ = 'subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    provider = db.Column(db.String(100))
    status = db.Column(db.String(50), default='active')
    renewal_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
