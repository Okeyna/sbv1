"""StudyBuddy FastAPI Backend Application"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.config import Config
from app.database import engine, Base
from app.routers import auth, files, audio, quizzes, chat, progress

# Create database tables
Base.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(
    title="StudyBuddy API",
    description="AI-powered study assistant backend",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create directories
os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
os.makedirs(Config.AUDIO_FOLDER, exist_ok=True)

# Mount static files
app.mount("/static/uploads", StaticFiles(directory=Config.UPLOAD_FOLDER), name="uploads")
app.mount("/static/audio", StaticFiles(directory=Config.AUDIO_FOLDER), name="audio")

# Register routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(files.router, prefix="/files", tags=["Files"])
app.include_router(audio.router, prefix="/audio", tags=["Audio"])
app.include_router(quizzes.router, prefix="/quizzes", tags=["Quizzes"])
app.include_router(chat.router, prefix="/chat", tags=["Chat"])
app.include_router(progress.router, prefix="/progress", tags=["Progress"])

# Root endpoint
@app.get("/")
def root():
    return {
        "message": "Welcome to StudyBuddy API",
        "version": "1.0.0",
        "docs": "/docs"
    }

# Health check
@app.get("/health")
def health():
    return {"status": "healthy"}
