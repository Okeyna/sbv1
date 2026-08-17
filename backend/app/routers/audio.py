from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import os

from app.database import get_db
from app.models import AudioLesson, UploadedFile, User
from app.schemas import AudioLessonResponse, AudioListResponse, AudioPositionUpdate
from app.services.tts_service import generate_audio
from app.config import Config
from app.routers.auth import get_current_user

router = APIRouter()

@router.post("/generate/{file_id}", response_model=AudioLessonResponse)
def generate_lesson(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate audio lesson from file"""
    uploaded_file = db.query(UploadedFile).filter(
        UploadedFile.id == file_id,
        UploadedFile.user_id == current_user.id
    ).first()
    
    if not uploaded_file:
        raise HTTPException(status_code=404, detail="File not found")
    
    if not uploaded_file.text_content:
        raise HTTPException(status_code=400, detail="No text content available")
    
    # Check if audio already exists
    existing_audio = db.query(AudioLesson).filter(
        AudioLesson.file_id == file_id,
        AudioLesson.user_id == current_user.id
    ).first()
    
    if existing_audio:
        return existing_audio
    
    # Generate audio
    try:
        audio_path, duration = generate_audio(uploaded_file.text_content, file_id)

        audio_lesson = AudioLesson(
            user_id=current_user.id,
            file_id=file_id,
            audio_path=audio_path,
            audio_url=f"{Config.BACKEND_BASE_URL}/static/audio/{os.path.basename(audio_path)}",
            duration=duration,
            voice_type="alloy"
        )
        
        db.add(audio_lesson)
        db.commit()
        db.refresh(audio_lesson)
        
        return audio_lesson
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate audio: {str(e)}")

@router.get("/file/{file_id}", response_model=AudioListResponse)
def get_file_audio(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all audio lessons for a file"""
    audio_lessons = db.query(AudioLesson).filter(
        AudioLesson.file_id == file_id,
        AudioLesson.user_id == current_user.id
    ).all()
    
    return {"audio_lessons": audio_lessons}

@router.get("/{audio_id}", response_model=AudioLessonResponse)
def get_audio(
    audio_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific audio lesson"""
    audio_lesson = db.query(AudioLesson).filter(
        AudioLesson.id == audio_id,
        AudioLesson.user_id == current_user.id
    ).first()
    
    if not audio_lesson:
        raise HTTPException(status_code=404, detail="Audio lesson not found")
    
    return audio_lesson

@router.delete("/{audio_id}")
def delete_audio(
    audio_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an audio lesson"""
    audio_lesson = db.query(AudioLesson).filter(
        AudioLesson.id == audio_id,
        AudioLesson.user_id == current_user.id
    ).first()
    
    if not audio_lesson:
        raise HTTPException(status_code=404, detail="Audio lesson not found")
    
    # Delete physical file
    try:
        if os.path.exists(audio_lesson.audio_path):
            os.remove(audio_lesson.audio_path)
    except Exception:
        pass
    
    db.delete(audio_lesson)
    db.commit()
    
    return {"message": "Audio lesson deleted successfully"}

@router.post("/{audio_id}/position", response_model=AudioLessonResponse)
def update_position(
    audio_id: int,
    position_data: AudioPositionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update playback position"""
    audio_lesson = db.query(AudioLesson).filter(
        AudioLesson.id == audio_id,
        AudioLesson.user_id == current_user.id
    ).first()
    
    if not audio_lesson:
        raise HTTPException(status_code=404, detail="Audio lesson not found")
    
    audio_lesson.position_seconds = position_data.position_seconds
    db.commit()
    db.refresh(audio_lesson)
    
    return audio_lesson
