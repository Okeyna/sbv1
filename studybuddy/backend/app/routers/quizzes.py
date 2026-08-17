from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import json
from ..database import get_db
from ..models import User, UploadedFile, Quiz, QuizQuestion, QuizAttempt
from ..schemas import (
    QuizResponse, 
    QuizQuestionResponse, 
    QuizSubmitAnswer,
    QuizAttemptResponse
)
from ..auth import get_current_user
from ..services.ai_service import generate_quiz

router = APIRouter(prefix="/quizzes", tags=["Quizzes"])


@router.post("/generate/{file_id}", response_model=QuizResponse)
def generate_quiz_endpoint(
    file_id: int,
    difficulty: str = "medium",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate a quiz from a file."""
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
            detail="No text content available for quiz generation"
        )
    
    # Generate quiz questions
    try:
        questions_data = generate_quiz(
            text=file.text_content,
            difficulty=difficulty,
            num_questions=5
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate quiz: {str(e)}"
        )
    
    # Create quiz
    quiz = Quiz(
        user_id=current_user.id,
        file_id=file_id,
        title=f"Quiz: {file.filename}",
        difficulty=difficulty
    )
    
    db.add(quiz)
    db.commit()
    db.refresh(quiz)
    
    # Create questions
    for q_data in questions_data:
        question = QuizQuestion(
            quiz_id=quiz.id,
            question=q_data["question"],
            options=json.dumps(q_data["options"]),
            correct_answer=q_data["correct_answer"],
            explanation=q_data.get("explanation", "")
        )
        db.add(question)
    
    db.commit()
    db.refresh(quiz)
    
    return quiz


@router.get("/file/{file_id}", response_model=list[QuizResponse])
def get_quizzes_for_file(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all quizzes for a specific file."""
    quizzes = db.query(Quiz).filter(
        Quiz.file_id == file_id,
        Quiz.user_id == current_user.id
    ).order_by(Quiz.created_at.desc()).all()
    
    return quizzes


@router.get("/{quiz_id}", response_model=QuizResponse)
def get_quiz(
    quiz_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific quiz by ID."""
    quiz = db.query(Quiz).filter(
        Quiz.id == quiz_id,
        Quiz.user_id == current_user.id
    ).first()
    
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found"
        )
    
    return quiz


@router.post("/{quiz_id}/submit", response_model=QuizAttemptResponse)
def submit_quiz(
    quiz_id: int,
    submission: QuizSubmitAnswer,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit quiz answers and get results."""
    # Get the quiz
    quiz = db.query(Quiz).filter(
        Quiz.id == quiz_id,
        Quiz.user_id == current_user.id
    ).first()
    
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found"
        )
    
    # Get questions
    questions = db.query(QuizQuestion).filter(
        QuizQuestion.quiz_id == quiz_id
    ).all()
    
    if len(questions) != len(submission.answers):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Number of answers doesn't match number of questions"
        )
    
    # Calculate score
    correct_count = 0
    for i, question in enumerate(questions):
        if submission.answers[i] == question.correct_answer:
            correct_count += 1
    
    total_questions = len(questions)
    score = (correct_count / total_questions) * 100 if total_questions > 0 else 0
    
    # Create attempt record
    attempt = QuizAttempt(
        user_id=current_user.id,
        quiz_id=quiz_id,
        score=score,
        correct=correct_count,
        total=total_questions
    )
    
    db.add(attempt)
    db.commit()
    
    # Return results with questions and explanations
    question_responses = [
        QuizQuestionResponse(
            id=q.id,
            quiz_id=q.quiz_id,
            question=q.question,
            options=json.loads(q.options),
            correct_answer=q.correct_answer,
            explanation=q.explanation
        )
        for q in questions
    ]
    
    return QuizAttemptResponse(
        score=score,
        correct=correct_count,
        total=total_questions,
        completed_at=attempt.completed_at,
        questions=question_responses
    )
