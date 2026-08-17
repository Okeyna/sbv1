from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from app.database import db
from app.models import Quiz, QuizQuestion, QuizAttempt, UploadedFile
from app.schemas import quiz_schema, quizzes_schema, quiz_submit_schema, attempt_schema
from app.services.ai_service import generate_quiz

quizzes_bp = Blueprint('quizzes', __name__, url_prefix='/api/quizzes')

@quizzes_bp.route('/generate/<int:file_id>', methods=['POST'])
@jwt_required()
def generate_quiz_route(file_id):
    """Generate quiz from file"""
    current_user_id = get_jwt_identity()
    
    uploaded_file = UploadedFile.query.filter_by(id=file_id, user_id=current_user_id).first()
    if not uploaded_file:
        return jsonify({'error': 'File not found'}), 404
    
    if not uploaded_file.text_content:
        return jsonify({'error': 'No text content available'}), 400
    
    try:
        # Generate quiz questions
        questions_data = generate_quiz(uploaded_file.text_content)
        
        if not questions_data or len(questions_data) == 0:
            return jsonify({'error': 'Failed to generate quiz questions'}), 500
        
        # Create quiz
        quiz = Quiz(
            user_id=current_user_id,
            file_id=file_id,
            title=f"Quiz: {uploaded_file.filename}",
            difficulty='medium'
        )
        
        db.session.add(quiz)
        db.session.flush()  # Get quiz ID before commit
        
        # Create questions
        for q_data in questions_data:
            question = QuizQuestion(
                quiz_id=quiz.id,
                question=q_data['question'],
                options=q_data['options'],
                correct_answer=q_data['correct_answer'],
                explanation=q_data.get('explanation', '')
            )
            db.session.add(question)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Quiz generated successfully',
            'quiz': quiz_schema.dump(quiz)
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to generate quiz: {str(e)}'}), 500


@quizzes_bp.route('/file/<int:file_id>', methods=['GET'])
@jwt_required()
def get_quizzes_for_file(file_id):
    """Get all quizzes for a specific file"""
    current_user_id = get_jwt_identity()
    quizzes = Quiz.query.filter_by(file_id=file_id, user_id=current_user_id).order_by(Quiz.created_at.desc()).all()
    return jsonify({'quizzes': quizzes_schema.dump(quizzes)})


@quizzes_bp.route('/<int:quiz_id>', methods=['GET'])
@jwt_required()
def get_quiz(quiz_id):
    """Get specific quiz with questions"""
    current_user_id = get_jwt_identity()
    quiz = Quiz.query.filter_by(id=quiz_id, user_id=current_user_id).first()
    
    if not quiz:
        return jsonify({'error': 'Quiz not found'}), 404
    
    return jsonify({'quiz': quiz_schema.dump(quiz)})


@quizzes_bp.route('/<int:quiz_id>/submit', methods=['POST'])
@jwt_required()
def submit_quiz(quiz_id):
    """Submit quiz answers"""
    current_user_id = get_jwt_identity()
    
    quiz = Quiz.query.filter_by(id=quiz_id, user_id=current_user_id).first()
    if not quiz:
        return jsonify({'error': 'Quiz not found'}), 404
    
    data = request.get_json()
    if not data or 'answers' not in data:
        return jsonify({'error': 'Answers required'}), 400
    
    user_answers = data['answers']
    questions = QuizQuestion.query.filter_by(quiz_id=quiz_id).all()
    
    if len(user_answers) != len(questions):
        return jsonify({'error': 'Number of answers does not match number of questions'}), 400
    
    # Calculate score
    correct_count = 0
    total = len(questions)
    
    for i, question in enumerate(questions):
        if i < len(user_answers) and user_answers[i] == question.correct_answer:
            correct_count += 1
    
    score = int((correct_count / total) * 100) if total > 0 else 0
    
    # Create attempt record
    attempt = QuizAttempt(
        user_id=current_user_id,
        quiz_id=quiz_id,
        score=score,
        correct=correct_count,
        total=total,
        answers=user_answers
    )
    
    db.session.add(attempt)
    
    # Update progress average
    from app.models import StudyProgress
    progress = StudyProgress.query.filter_by(user_id=current_user_id, file_id=quiz.file_id).first()
    if progress:
        # Recalculate average quiz score
        all_attempts = QuizAttempt.query.join(Quiz).filter(
            Quiz.user_id == current_user_id,
            Quiz.file_id == quiz.file_id
        ).all()
        
        if all_attempts:
            avg_score = sum(a.score for a in all_attempts) / len(all_attempts)
            progress.quiz_avg = avg_score
    
    db.session.commit()
    
    # Build results with explanations
    results = []
    for i, question in enumerate(questions):
        results.append({
            'question': question.question,
            'your_answer': user_answers[i] if i < len(user_answers) else None,
            'correct_answer': question.correct_answer,
            'options': question.options,
            'is_correct': i < len(user_answers) and user_answers[i] == question.correct_answer,
            'explanation': question.explanation
        })
    
    return jsonify({
        'score': score,
        'correct': correct_count,
        'total': total,
        'results': results
    })


@quizzes_bp.route('/<int:quiz_id>', methods=['DELETE'])
@jwt_required()
def delete_quiz(quiz_id):
    """Delete a quiz"""
    current_user_id = get_jwt_identity()
    quiz = Quiz.query.filter_by(id=quiz_id, user_id=current_user_id).first()
    
    if not quiz:
        return jsonify({'error': 'Quiz not found'}), 404
    
    db.session.delete(quiz)
    db.session.commit()
    
    return jsonify({'message': 'Quiz deleted successfully'})
