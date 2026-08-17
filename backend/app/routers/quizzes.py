from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import json

from app.database import get_db
from app.models import Quiz, QuizQuestion, QuizAttempt, UploadedFile, User
from app.schemas import QuizResponse, QuizListResponse, QuizSubmitRequest, QuizAttemptResponse
from app.services.ai_service import generate_quiz
from app.routers.auth import get_current_user

router = APIRouter()

@router.post("/generate/{file_id}", response_model=QuizResponse)
def generate_quiz_endpoint(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate quiz from file"""
    uploaded_file = db.query(UploadedFile).filter(
        UploadedFile.id == file_id,
        UploadedFile.user_id == current_user.id
    ).first()
    
    if not uploaded_file:
        raise HTTPException(status_code=404, detail="File not found")
    
    if not uploaded_file.text_content:
        raise HTTPException(status_code=400, detail="No text content available")
    
    # Generate quiz
    try:
        quiz_data = generate_quiz(uploaded_file.text_content)
        
        quiz = Quiz(
            user_id=current_user.id,
            file_id=file_id,
            title=f"Quiz for {uploaded_file.filename}",
            difficulty="medium"
        )
        
        db.add(quiz)
        db.commit()
        db.refresh(quiz)
        
        # Add questions
        for q_data in quiz_data.get("questions", []):
            question = QuizQuestion(
                quiz_id=quiz.id,
                question=q_data["question"],
                options=q_data["options"],
                correct_answer=q_data["correct_answer"],
                explanation=q_data["explanation"]
            )
            db.add(question)
        
        db.commit()
        db.refresh(quiz)
        
        return quiz
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate quiz: {str(e)}")

@router.get("/file/{file_id}", response_model=QuizListResponse)
def get_file_quizzes(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all quizzes for a file"""
    quizzes = db.query(Quiz).filter(
        Quiz.file_id == file_id,
        Quiz.user_id == current_user.id
    ).all()
    
    return {"quizzes": quizzes}

@router.get("/{quiz_id}", response_model=QuizResponse)
def get_quiz(
    quiz_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific quiz"""
    quiz = db.query(Quiz).filter(
        Quiz.id == quiz_id,
        Quiz.user_id == current_user.id
    ).first()
    
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    return quiz

@router.post("/{quiz_id}/submit", response_model=QuizAttemptResponse)
def submit_quiz(
    quiz_id: int,
    submission: QuizSubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit quiz answers"""
    quiz = db.query(Quiz).filter(
        Quiz.id == quiz_id,
        Quiz.user_id == current_user.id
    ).first()
    
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    questions = db.query(QuizQuestion).filter(QuizQuestion.quiz_id == quiz_id).all()
    
    if len(questions) != len(submission.answers):
        raise HTTPException(status_code=400, detail="Number of answers doesn't match questions")
    
    # Calculate score
    correct = 0
    for i, answer in enumerate(submission.answers):
        if answer == questions[i].correct_answer:
            correct += 1
    
    total = len(questions)
    score = int((correct / total) * 100) if total > 0 else 0
    
    # Create attempt record
    attempt = QuizAttempt(
        user_id=current_user.id,
        quiz_id=quiz_id,
        score=score,
        correct=correct,
        total=total,
        answers=submission.answers
    )
    
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    
    return attempt
