from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import os
from ..database import get_db
from ..models import User, UploadedFile, AudioLesson
from ..schemas import AudioResponse, AudioPositionUpdate
from ..auth import get_current_user
from ..services.tts_service import generate_audio_from_text

router = APIRouter(prefix="/audio", tags=["Audio"])

AUDIO_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "audio")


@router.post("/generate/{file_id}", response_model=AudioResponse)
def generate_audio(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate audio lesson from a file."""
    # Get the file
    file = db.query(UploadedFile).filter(
        UploadedFile.id == file_id,
        UploadedFile.user_id == current_user.id
    ).first()
    
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    if not file.text_content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No text content available for audio generation"
        )
    
    # Check if audio already exists
    existing_audio = db.query(AudioLesson).filter(
        AudioLesson.file_id == file_id,
        AudioLesson.user_id == current_user.id
    ).first()
    
    if existing_audio:
        return existing_audio
    
    # Create audio directory if it doesn't exist
    os.makedirs(AUDIO_DIR, exist_ok=True)
    
    # Generate audio filename
    audio_filename = f"audio_{file_id}.wav"
    audio_path = os.path.join(AUDIO_DIR, audio_filename)
    
    # Generate audio from text
    try:
        generated_path, duration = generate_audio_from_text(
            text=file.text_content,
            output_path=audio_path,
            voice_type="alloy"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate audio: {str(e)}"
        )
    
    # Create database record
    audio_lesson = AudioLesson(
        user_id=current_user.id,
        file_id=file_id,
        audio_path=audio_path,
        audio_url=f"/static/audio/{audio_filename}",
        duration=duration,
        voice_type="alloy"
    )
    
    db.add(audio_lesson)
    db.commit()
    db.refresh(audio_lesson)
    
    return audio_lesson


@router.get("/file/{file_id}", response_model=AudioResponse)
def get_audio_for_file(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get audio lesson for a specific file."""
    audio = db.query(AudioLesson).filter(
        AudioLesson.file_id == file_id,
        AudioLesson.user_id == current_user.id
    ).first()
    
    if not audio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio lesson not found. Generate it first."
        )
    
    return audio


@router.get("/{audio_id}", response_model=AudioResponse)
def get_audio(
    audio_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific audio lesson by ID."""
    audio = db.query(AudioLesson).filter(
        AudioLesson.id == audio_id,
        AudioLesson.user_id == current_user.id
    ).first()
    
    if not audio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio lesson not found"
        )
    
    return audio


@router.delete("/{audio_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_audio(
    audio_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an audio lesson."""
    audio = db.query(AudioLesson).filter(
        AudioLesson.id == audio_id,
        AudioLesson.user_id == current_user.id
    ).first()
    
    if not audio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio lesson not found"
        )
    
    # Delete physical file
    if audio.audio_path and os.path.exists(audio.audio_path):
        os.remove(audio.audio_path)
    
    # Delete from database
    db.delete(audio)
    db.commit()
    
    return None


@router.post("/{audio_id}/position", response_model=AudioResponse)
def update_audio_position(
    audio_id: int,
    position_data: AudioPositionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Save playback position for an audio lesson."""
    audio = db.query(AudioLesson).filter(
        AudioLesson.id == audio_id,
        AudioLesson.user_id == current_user.id
    ).first()
    
    if not audio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio lesson not found"
        )
    
    # Update position
    audio.position_seconds = position_data.position_seconds
    db.commit()
    db.refresh(audio)
    
    return audio
