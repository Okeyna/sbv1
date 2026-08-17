from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.database import db
from app.models import StudyProgress, UploadedFile, AudioLesson, Quiz, QuizAttempt, QuizQuestion
from app.schemas import progress_schema, progresses_schema

progress_bp = Blueprint('progress', __name__, url_prefix='/api/progress')

@progress_bp.route('', methods=['GET'])
@jwt_required()
def get_progress():
    """Get overall study progress for current user"""
    current_user_id = get_jwt_identity()
    
    # Get all files
    total_files = UploadedFile.query.filter_by(user_id=current_user_id).count()
    
    # Get all audio lessons
    total_audio = AudioLesson.query.filter_by(user_id=current_user_id).count()
    
    # Get all quizzes
    total_quizzes = Quiz.query.filter_by(user_id=current_user_id).count()
    
    # Get quiz attempts
    quiz_attempts = QuizAttempt.query.filter_by(user_id=current_user_id).all()
    total_attempts = len(quiz_attempts)
    
    # Calculate average quiz score
    avg_score = 0.0
    if quiz_attempts:
        avg_score = sum(a.score for a in quiz_attempts) / len(quiz_attempts)
    
    # Get total listening time
    all_progress = StudyProgress.query.filter_by(user_id=current_user_id).all()
    total_listening_time = sum(p.listening_time for p in all_progress) if all_progress else 0.0
    
    # Convert to hours
    study_hours = total_listening_time / 3600.0
    
    # Get weak topics
    weak_topics = get_weak_topics(current_user_id)
    
    return jsonify({
        'total_files': total_files,
        'total_audio_lessons': total_audio,
        'total_quizzes': total_quizzes,
        'total_quiz_attempts': total_attempts,
        'average_quiz_score': round(avg_score, 2),
        'total_listening_time_seconds': round(total_listening_time, 2),
        'study_hours': round(study_hours, 2),
        'weak_topics': weak_topics
    })


@progress_bp.route('/listening', methods=['POST'])
@jwt_required()
def update_listening_time():
    """Update listening time for a file"""
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data or 'file_id' not in data or 'seconds' not in data:
        return jsonify({'error': 'file_id and seconds required'}), 400
    
    file_id = data['file_id']
    seconds = float(data['seconds'])
    
    # Verify file belongs to user
    uploaded_file = UploadedFile.query.filter_by(id=file_id, user_id=current_user_id).first()
    if not uploaded_file:
        return jsonify({'error': 'File not found'}), 404
    
    # Get or create progress record
    progress = StudyProgress.query.filter_by(user_id=current_user_id, file_id=file_id).first()
    
    if not progress:
        progress = StudyProgress(
            user_id=current_user_id,
            file_id=file_id,
            completion=0.0,
            listening_time=seconds,
            quiz_avg=0.0
        )
        db.session.add(progress)
    else:
        progress.listening_time += seconds
    
    db.session.commit()
    
    return jsonify({
        'message': 'Listening time updated',
        'total_listening_time': progress.listening_time
    })


@progress_bp.route('/completion', methods=['POST'])
@jwt_required()
def update_completion():
    """Update completion percentage for a file"""
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data or 'file_id' not in data or 'percentage' not in data:
        return jsonify({'error': 'file_id and percentage required'}), 400
    
    file_id = data['file_id']
    percentage = float(data['percentage'])
    
    if percentage < 0 or percentage > 100:
        return jsonify({'error': 'Percentage must be between 0 and 100'}), 400
    
    # Verify file belongs to user
    uploaded_file = UploadedFile.query.filter_by(id=file_id, user_id=current_user_id).first()
    if not uploaded_file:
        return jsonify({'error': 'File not found'}), 404
    
    # Get or create progress record
    progress = StudyProgress.query.filter_by(user_id=current_user_id, file_id=file_id).first()
    
    if not progress:
        progress = StudyProgress(
            user_id=current_user_id,
            file_id=file_id,
            completion=percentage,
            listening_time=0.0,
            quiz_avg=0.0
        )
        db.session.add(progress)
    else:
        progress.completion = percentage
    
    db.session.commit()
    
    return jsonify({
        'message': 'Completion updated',
        'completion': progress.completion
    })


@progress_bp.route('/weak-topics', methods=['GET'])
@jwt_required()
def get_weak_topics_route():
    """Get weak topics based on quiz performance"""
    current_user_id = get_jwt_identity()
    weak_topics = get_weak_topics(current_user_id)
    return jsonify({'weak_topics': weak_topics})


def get_weak_topics(user_id):
    """Helper function to identify weak topics from quiz performance"""
    weak_topics = []
    
    # Get all incorrect answers
    failed_attempts = QuizAttempt.query.join(Quiz).filter(
        Quiz.user_id == user_id,
        QuizAttempt.score < 80  # Consider scores below 80% as weak areas
    ).all()
    
    if not failed_attempts:
        return weak_topics
    
    # Analyze which questions were answered incorrectly
    incorrect_questions = []
    for attempt in failed_attempts:
        questions = QuizQuestion.query.filter_by(quiz_id=attempt.quiz_id).all()
        for i, q in enumerate(questions):
            if i < len(attempt.answers) and attempt.answers[i] != q.correct_answer:
                incorrect_questions.append({
                    'question': q.question[:100],  # Truncate for display
                    'topic': extract_topic(q.question),
                    'explanation': q.explanation
                })
    
    # Group by topic and return unique topics
    seen_topics = set()
    for q in incorrect_questions[:5]:  # Limit to 5 weak topics
        topic = q['topic']
        if topic and topic not in seen_topics:
            seen_topics.add(topic)
            weak_topics.append({
                'topic': topic,
                'recommendation': f"Review: {q['explanation'][:150]}" if q.get('explanation') else "Review the related material"
            })
    
    return weak_topics


def extract_topic(question_text):
    """Extract a simple topic from question text"""
    # Simple heuristic: first few words or key terms
    words = question_text.split()[:5]
    return ' '.join(words) + '...' if len(words) >= 3 else question_text[:50]
