from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import List
import json

from app.database import get_db
from app.models import StudyProgress, UploadedFile, AudioLesson, Quiz, QuizAttempt, User
from app.schemas import ProgressSummary, ListeningTimeUpdate, CompletionUpdate, WeakTopic
from app.routers.auth import get_current_user

router = APIRouter()

@router.get("", response_model=ProgressSummary)
def get_progress_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get overall progress summary"""
    # Total files
    total_files = db.query(UploadedFile).filter(
        UploadedFile.user_id == current_user.id
    ).count()
    
    # Total audio lessons
    total_audio = db.query(AudioLesson).filter(
        AudioLesson.user_id == current_user.id
    ).count()
    
    # Total quizzes
    total_quizzes = db.query(Quiz).filter(
        Quiz.user_id == current_user.id
    ).count()
    
    # Quiz attempts and average score
    attempts = db.query(QuizAttempt).filter(
        QuizAttempt.user_id == current_user.id
    ).all()
    
    total_attempts = len(attempts)
    avg_score = 0.0
    if total_attempts > 0:
        avg_score = sum(a.score for a in attempts) / total_attempts
    
    # Total listening time
    progress_records = db.query(StudyProgress).filter(
        StudyProgress.user_id == current_user.id
    ).all()
    
    total_listening_time = sum(p.listening_time for p in progress_records)
    study_hours = total_listening_time / 3600.0
    
    # Weak topics (files with low quiz performance)
    weak_topics = []
    file_progress = db.query(StudyProgress).filter(
        StudyProgress.user_id == current_user.id,
        StudyProgress.quiz_avg < 70.0
    ).all()
    
    for prog in file_progress:
        uploaded_file = db.query(UploadedFile).filter(UploadedFile.id == prog.file_id).first()
        if uploaded_file:
            quiz_count = db.query(Quiz).filter(Quiz.file_id == prog.file_id).count()
            if quiz_count > 0:
                weak_topics.append(WeakTopic(
                    file_id=prog.file_id,
                    filename=uploaded_file.filename,
                    quiz_count=quiz_count,
                    avg_score=prog.quiz_avg
                ))
    
    return ProgressSummary(
        total_files=total_files,
        total_audio_lessons=total_audio,
        total_quizzes=total_quizzes,
        total_quiz_attempts=total_attempts,
        avg_quiz_score=avg_score,
        total_listening_time=total_listening_time,
        study_hours=study_hours,
        weak_topics=weak_topics
    )

@router.post("/listening")
def update_listening_time(
    data: ListeningTimeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update listening time for a file"""
    progress = db.query(StudyProgress).filter(
        StudyProgress.user_id == current_user.id,
        StudyProgress.file_id == data.file_id
    ).first()
    
    if not progress:
        raise HTTPException(status_code=404, detail="Progress record not found")
    
    progress.listening_time += data.seconds
    db.commit()
    db.refresh(progress)
    
    return {"message": "Listening time updated", "total_seconds": progress.listening_time}

@router.post("/completion")
def update_completion(
    data: CompletionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update completion percentage for a file"""
    progress = db.query(StudyProgress).filter(
        StudyProgress.user_id == current_user.id,
        StudyProgress.file_id == data.file_id
    ).first()
    
    if not progress:
        raise HTTPException(status_code=404, detail="Progress record not found")
    
    progress.completion = data.percentage
    db.commit()
    db.refresh(progress)
    
    return {"message": "Completion updated", "completion": progress.completion}

@router.get("/weak-topics", response_model=List[WeakTopic])
def get_weak_topics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get weak topics based on quiz performance"""
    weak_topics = []
    file_progress = db.query(StudyProgress).filter(
        StudyProgress.user_id == current_user.id,
        StudyProgress.quiz_avg < 70.0
    ).all()
    
    for prog in file_progress:
        uploaded_file = db.query(UploadedFile).filter(UploadedFile.id == prog.file_id).first()
        if uploaded_file:
            quiz_count = db.query(Quiz).filter(Quiz.file_id == prog.file_id).count()
            if quiz_count > 0:
                weak_topics.append(WeakTopic(
                    file_id=prog.file_id,
                    filename=uploaded_file.filename,
                    quiz_count=quiz_count,
                    avg_score=prog.quiz_avg
                ))
    
    return weak_topics
