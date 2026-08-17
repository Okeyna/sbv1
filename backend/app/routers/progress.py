from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
import json
from ..database import get_db
from ..models import (
    User, UploadedFile, AudioLesson, Quiz, 
    QuizAttempt, StudyProgress, QuizQuestion
)
from ..schemas import (
    ProgressResponse, 
    ProgressListeningUpdate, 
    ProgressCompletionUpdate,
    WeakTopic
)
from ..auth import get_current_user

router = APIRouter(prefix="/progress", tags=["Progress"])


@router.get("", response_model=ProgressResponse)
def get_progress(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get overall study progress."""
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
    
    # Total quiz attempts
    total_attempts = db.query(QuizAttempt).filter(
        QuizAttempt.user_id == current_user.id
    ).count()
    
    # Average quiz score
    avg_score_result = db.query(func.avg(QuizAttempt.score)).filter(
        QuizAttempt.user_id == current_user.id
    ).scalar()
    avg_quiz_score = float(avg_score_result) if avg_score_result else 0.0
    
    # Total listening time from progress table
    total_listening_result = db.query(func.sum(StudyProgress.listening_time)).filter(
        StudyProgress.user_id == current_user.id
    ).scalar()
    total_listening_time = float(total_listening_result) if total_listening_result else 0.0
    
    # Calculate study hours (listening time in hours)
    study_hours = total_listening_time / 3600
    
    # Get weak topics
    weak_topics = _get_weak_topics(db, current_user.id)
    
    return ProgressResponse(
        total_files=total_files,
        total_audio_lessons=total_audio,
        total_quizzes=total_quizzes,
        total_quiz_attempts=total_attempts,
        avg_quiz_score=avg_quiz_score,
        total_listening_time=total_listening_time,
        study_hours=study_hours,
        weak_topics=weak_topics
    )


@router.post("/listening")
def update_listening_time(
    progress_data: ProgressListeningUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update listening time for a file."""
    # Get or create progress record
    progress = db.query(StudyProgress).filter(
        StudyProgress.user_id == current_user.id,
        StudyProgress.file_id == progress_data.file_id
    ).first()
    
    if not progress:
        progress = StudyProgress(
            user_id=current_user.id,
            file_id=progress_data.file_id,
            listening_time=0.0
        )
        db.add(progress)
    
    # Add listening time
    progress.listening_time += progress_data.seconds
    db.commit()
    db.refresh(progress)
    
    return {"message": "Listening time updated", "total_seconds": progress.listening_time}


@router.post("/completion")
def update_completion(
    progress_data: ProgressCompletionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update completion percentage for a file."""
    # Get or create progress record
    progress = db.query(StudyProgress).filter(
        StudyProgress.user_id == current_user.id,
        StudyProgress.file_id == progress_data.file_id
    ).first()
    
    if not progress:
        progress = StudyProgress(
            user_id=current_user.id,
            file_id=progress_data.file_id,
            completion=0.0
        )
        db.add(progress)
    
    # Update completion
    progress.completion = progress_data.completion
    db.commit()
    db.refresh(progress)
    
    return {"message": "Completion updated", "completion": progress.completion}


@router.get("/weak-topics", response_model=List[WeakTopic])
def get_weak_topics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get weak topics based on quiz performance."""
    weak_topics = _get_weak_topics(db, current_user.id)
    return weak_topics


def _get_weak_topics(db: Session, user_id: int) -> List[WeakTopic]:
    """Helper function to identify weak topics based on quiz performance."""
    weak_topics = []
    
    # Get files with quiz attempts where average score is below 70%
    results = db.query(
        UploadedFile.id,
        UploadedFile.filename,
        func.avg(QuizAttempt.score).label('avg_score')
    ).join(
        Quiz, UploadedFile.id == Quiz.file_id
    ).join(
        QuizAttempt, Quiz.id == QuizAttempt.quiz_id
    ).filter(
        UploadedFile.user_id == user_id
    ).group_by(
        UploadedFile.id,
        UploadedFile.filename
    ).having(
        func.avg(QuizAttempt.score) < 70
    ).all()
    
    for result in results:
        weak_topics.append(WeakTopic(
            topic=f"Content from {result.filename}",
            file_id=result.id,
            file_name=result.filename,
            quiz_avg=float(result.avg_score)
        ))
    
    # Also check for questions that are frequently answered incorrectly
    incorrect_questions = db.query(
        QuizQuestion.id,
        QuizQuestion.question,
        QuizQuestion.explanation,
        UploadedFile.id.label('file_id'),
        UploadedFile.filename.label('file_name')
    ).join(
        Quiz, QuizQuestion.quiz_id == Quiz.id
    ).join(
        UploadedFile, Quiz.file_id == UploadedFile.id
    ).filter(
        UploadedFile.user_id == user_id
    ).limit(5).all()
    
    # If we don't have enough weak topics from low scores, add some from incorrect answers
    if len(weak_topics) < 3 and incorrect_questions:
        for q in incorrect_questions[:3 - len(weak_topics)]:
            weak_topics.append(WeakTopic(
                topic=q.question[:50] + "..." if len(q.question) > 50 else q.question,
                file_id=q.file_id,
                file_name=q.file_name,
                quiz_avg=0.0
            ))
    
    return weak_topics
