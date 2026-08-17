from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from .config import settings
from .database import engine, Base, get_db
from .routers import auth, files, audio, quizzes, chat, progress

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="StudyBuddy API",
    description="AI-powered study assistant API",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create static directories
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
AUDIO_DIR = os.path.join(os.path.dirname(__file__), "audio")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)

# Mount static files
app.mount("/static/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
app.mount("/static/audio", StaticFiles(directory=AUDIO_DIR), name="audio")


# Include routers
app.include_router(auth.router)
app.include_router(files.router)
app.include_router(audio.router)
app.include_router(quizzes.router)
app.include_router(chat.router)
app.include_router(progress.router)


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "message": "Welcome to StudyBuddy API",
        "docs": "/docs",
        "version": "1.0.0"
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
