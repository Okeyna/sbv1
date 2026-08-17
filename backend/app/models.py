from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Boolean, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


class User(Base):
    """User model for authentication and user data."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="user")
    subscription_type = Column(String, default="free")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    files = relationship("UploadedFile", back_populates="user", cascade="all, delete-orphan")
    audio_lessons = relationship("AudioLesson", back_populates="user", cascade="all, delete-orphan")
    quizzes = relationship("Quiz", back_populates="user", cascade="all, delete-orphan")
    quiz_attempts = relationship("QuizAttempt", back_populates="user", cascade="all, delete-orphan")
    chat_messages = relationship("AIChat", back_populates="user", cascade="all, delete-orphan")
    progress = relationship("StudyProgress", back_populates="user", cascade="all, delete-orphan")
    subscription = relationship("Subscription", back_populates="user", uselist=False, cascade="all, delete-orphan")


class UploadedFile(Base):
    """Model for uploaded PDF files."""
    
    __tablename__ = "uploaded_files"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    text_content = Column(Text)
    summary = Column(Text)
    status = Column(String, default="processing")  # processing, ready, error
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="files")
    audio_lessons = relationship("AudioLesson", back_populates="file", cascade="all, delete-orphan")
    quizzes = relationship("Quiz", back_populates="file", cascade="all, delete-orphan")
    chat_messages = relationship("AIChat", back_populates="file", cascade="all, delete-orphan")
    progress = relationship("StudyProgress", back_populates="file", uselist=False, cascade="all, delete-orphan")


class AudioLesson(Base):
    """Model for generated audio lessons."""
    
    __tablename__ = "audio_lessons"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    file_id = Column(Integer, ForeignKey("uploaded_files.id", ondelete="CASCADE"), nullable=False)
    audio_path = Column(String)
    audio_url = Column(String)
    duration = Column(Float)  # in seconds
    voice_type = Column(String, default="alloy")
    position_seconds = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="audio_lessons")
    file = relationship("UploadedFile", back_populates="audio_lessons")


class Quiz(Base):
    """Model for generated quizzes."""
    
    __tablename__ = "quizzes"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    file_id = Column(Integer, ForeignKey("uploaded_files.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    difficulty = Column(String, default="medium")  # easy, medium, hard
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="quizzes")
    file = relationship("UploadedFile", back_populates="quizzes")
    questions = relationship("QuizQuestion", back_populates="quiz", cascade="all, delete-orphan")
    attempts = relationship("QuizAttempt", back_populates="quiz", cascade="all, delete-orphan")


class QuizQuestion(Base):
    """Model for quiz questions."""
    
    __tablename__ = "quiz_questions"
    
    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False)
    question = Column(String, nullable=False)
    options = Column(String, nullable=False)  # JSON string of 4 options
    correct_answer = Column(Integer, nullable=False)  # Index of correct option (0-3)
    explanation = Column(Text)
    
    # Relationships
    quiz = relationship("Quiz", back_populates="questions")


class QuizAttempt(Base):
    """Model for quiz attempts."""
    
    __tablename__ = "quiz_attempts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    quiz_id = Column(Integer, ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False)
    score = Column(Float)  # Percentage
    correct = Column(Integer)
    total = Column(Integer)
    completed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="quiz_attempts")
    quiz = relationship("Quiz", back_populates="attempts")


class AIChat(Base):
    """Model for AI chat messages."""
    
    __tablename__ = "ai_chats"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    file_id = Column(Integer, ForeignKey("uploaded_files.id", ondelete="CASCADE"), nullable=False)
    message = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="chat_messages")
    file = relationship("UploadedFile", back_populates="chat_messages")


class StudyProgress(Base):
    """Model for tracking study progress per file."""
    
    __tablename__ = "study_progress"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    file_id = Column(Integer, ForeignKey("uploaded_files.id", ondelete="CASCADE"), nullable=False)
    completion = Column(Float, default=0.0)  # Percentage
    listening_time = Column(Float, default=0.0)  # Total seconds
    quiz_avg = Column(Float, default=0.0)  # Average quiz score
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Unique constraint to ensure one progress record per user-file pair
    __table_args__ = (UniqueConstraint('user_id', 'file_id', name='unique_user_file_progress'),)
    
    # Relationships
    user = relationship("User", back_populates="progress")
    file = relationship("UploadedFile", back_populates="progress")


class Subscription(Base):
    """Model for user subscriptions."""
    
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    provider = Column(String, default="stripe")
    status = Column(String, default="active")  # active, cancelled, expired
    renewal_date = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="subscription")
