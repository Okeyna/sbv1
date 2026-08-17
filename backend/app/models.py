from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default='user')
    subscription_type = Column(String(50), default='free')
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    files = relationship('UploadedFile', back_populates='owner', cascade='all, delete-orphan')
    audio_lessons = relationship('AudioLesson', back_populates='owner', cascade='all, delete-orphan')
    quizzes = relationship('Quiz', back_populates='owner', cascade='all, delete-orphan')
    quiz_attempts = relationship('QuizAttempt', back_populates='owner', cascade='all, delete-orphan')
    chat_messages = relationship('AIChat', back_populates='owner', cascade='all, delete-orphan')
    progress = relationship('StudyProgress', back_populates='owner', cascade='all, delete-orphan')

class UploadedFile(Base):
    __tablename__ = 'uploaded_files'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    text_content = Column(Text)
    summary = Column(Text)
    status = Column(String(50), default='processing')
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    owner = relationship('User', back_populates='files')
    audio_lessons = relationship('AudioLesson', back_populates='file', cascade='all, delete-orphan')
    quizzes = relationship('Quiz', back_populates='file', cascade='all, delete-orphan')
    chat_messages = relationship('AIChat', back_populates='file', cascade='all, delete-orphan')
    progress = relationship('StudyProgress', back_populates='file', uselist=False, cascade='all, delete-orphan')

class AudioLesson(Base):
    __tablename__ = 'audio_lessons'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    file_id = Column(Integer, ForeignKey('uploaded_files.id'), nullable=False)
    audio_path = Column(String(500), nullable=False)
    audio_url = Column(String(500))
    duration = Column(Float, default=0.0)
    voice_type = Column(String(50), default='default')
    position_seconds = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    owner = relationship('User', back_populates='audio_lessons')
    file = relationship('UploadedFile', back_populates='audio_lessons')

class Quiz(Base):
    __tablename__ = 'quizzes'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    file_id = Column(Integer, ForeignKey('uploaded_files.id'), nullable=False)
    title = Column(String(255), nullable=False)
    difficulty = Column(String(50), default='medium')
    created_at = Column(DateTime, default=datetime.utcnow)
    
    owner = relationship('User', back_populates='quizzes')
    file = relationship('UploadedFile', back_populates='quizzes')
    questions = relationship('QuizQuestion', back_populates='quiz', cascade='all, delete-orphan')
    attempts = relationship('QuizAttempt', back_populates='quiz', cascade='all, delete-orphan')

class QuizQuestion(Base):
    __tablename__ = 'quiz_questions'
    
    id = Column(Integer, primary_key=True)
    quiz_id = Column(Integer, ForeignKey('quizzes.id'), nullable=False)
    question = Column(Text, nullable=False)
    options = Column(JSON, nullable=False)
    correct_answer = Column(Integer, nullable=False)
    explanation = Column(Text)
    
    quiz = relationship('Quiz', back_populates='questions')

class QuizAttempt(Base):
    __tablename__ = 'quiz_attempts'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    quiz_id = Column(Integer, ForeignKey('quizzes.id'), nullable=False)
    score = Column(Integer, default=0)
    correct = Column(Integer, default=0)
    total = Column(Integer, default=0)
    answers = Column(JSON)
    completed_at = Column(DateTime, default=datetime.utcnow)
    
    owner = relationship('User', back_populates='quiz_attempts')
    quiz = relationship('Quiz', back_populates='attempts')

class AIChat(Base):
    __tablename__ = 'ai_chats'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    file_id = Column(Integer, ForeignKey('uploaded_files.id'))
    message = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    owner = relationship('User', back_populates='chat_messages')
    file = relationship('UploadedFile', back_populates='chat_messages')

class StudyProgress(Base):
    __tablename__ = 'study_progress'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    file_id = Column(Integer, ForeignKey('uploaded_files.id'), nullable=False)
    completion = Column(Float, default=0.0)
    listening_time = Column(Float, default=0.0)
    quiz_avg = Column(Float, default=0.0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (UniqueConstraint('user_id', 'file_id', name='unique_user_file_progress'),)
    
    owner = relationship('User', back_populates='progress')
    file = relationship('UploadedFile', back_populates='progress')
