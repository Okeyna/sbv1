import os
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from app.database import db
from app.models import UploadedFile, StudyProgress
from app.schemas import file_schema, files_schema
from app.services.pdf_service import extract_text_from_pdf
from app.services.ai_service import generate_summary
from app.config import Config

files_bp = Blueprint('files', __name__, url_prefix='/api/files')

ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@files_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_file():
    """Upload a PDF file"""
    current_user_id = get_jwt_identity()
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Only PDF files are allowed'}), 400
    
    # Check file size
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    
    if file_size > Config.MAX_FILE_SIZE:
        return jsonify({'error': 'File too large. Maximum size is 20MB'}), 400
    
    # Save file
    filename = secure_filename(file.filename)
    # Add timestamp to avoid conflicts
    import time
    timestamp = int(time.time())
    filename = f"{timestamp}_{filename}"
    
    filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    file.save(filepath)
    
    # Extract text from PDF
    try:
        text_content = extract_text_from_pdf(filepath)
    except Exception as e:
        return jsonify({'error': f'Failed to extract text from PDF: {str(e)}'}), 500
    
    if not text_content or len(text_content.strip()) == 0:
        return jsonify({'error': 'PDF appears to be empty or unreadable'}), 400
    
    # Create database record
    uploaded_file = UploadedFile(
        user_id=current_user_id,
        filename=filename,
        file_path=filepath,
        text_content=text_content,
        status='processing'
    )
    
    db.session.add(uploaded_file)
    db.session.commit()
    
    # Generate summary asynchronously (in real app, use background task)
    try:
        summary = generate_summary(text_content)
        uploaded_file.summary = summary
        uploaded_file.status = 'ready'
        db.session.commit()
    except Exception as e:
        uploaded_file.status = 'error'
        db.session.commit()
        # Still return the file, just without summary
    
    # Create progress record
    progress = StudyProgress(
        user_id=current_user_id,
        file_id=uploaded_file.id,
        completion=0.0,
        listening_time=0.0,
        quiz_avg=0.0
    )
    db.session.add(progress)
    db.session.commit()
    
    return jsonify({
        'message': 'File uploaded successfully',
        'file': file_schema.dump(uploaded_file)
    }), 201


@files_bp.route('', methods=['GET'])
@jwt_required()
def get_files():
    """Get all files for current user"""
    current_user_id = get_jwt_identity()
    files = UploadedFile.query.filter_by(user_id=current_user_id).order_by(UploadedFile.created_at.desc()).all()
    return jsonify({'files': files_schema.dump(files)})


@files_bp.route('/<int:file_id>', methods=['GET'])
@jwt_required()
def get_file(file_id):
    """Get a specific file"""
    current_user_id = get_jwt_identity()
    uploaded_file = UploadedFile.query.filter_by(id=file_id, user_id=current_user_id).first()
    
    if not uploaded_file:
        return jsonify({'error': 'File not found'}), 404
    
    return jsonify({'file': file_schema.dump(uploaded_file)})


@files_bp.route('/<int:file_id>', methods=['DELETE'])
@jwt_required()
def delete_file(file_id):
    """Delete a file"""
    current_user_id = get_jwt_identity()
    uploaded_file = UploadedFile.query.filter_by(id=file_id, user_id=current_user_id).first()
    
    if not uploaded_file:
        return jsonify({'error': 'File not found'}), 404
    
    # Delete physical file
    try:
        if os.path.exists(uploaded_file.file_path):
            os.remove(uploaded_file.file_path)
    except Exception:
        pass  # Continue even if file deletion fails
    
    db.session.delete(uploaded_file)
    db.session.commit()
    
    return jsonify({'message': 'File deleted successfully'})


@files_bp.route('/<int:file_id>/summary', methods=['POST'])
@jwt_required()
def regenerate_summary(file_id):
    """Regenerate summary for a file"""
    current_user_id = get_jwt_identity()
    uploaded_file = UploadedFile.query.filter_by(id=file_id, user_id=current_user_id).first()
    
    if not uploaded_file:
        return jsonify({'error': 'File not found'}), 404
    
    if not uploaded_file.text_content:
        return jsonify({'error': 'No text content available'}), 400
    
    try:
        summary = generate_summary(uploaded_file.text_content)
        uploaded_file.summary = summary
        uploaded_file.status = 'ready'
        db.session.commit()
        
        return jsonify({
            'message': 'Summary regenerated successfully',
            'summary': summary
        })
    except Exception as e:
        return jsonify({'error': f'Failed to generate summary: {str(e)}'}), 500
