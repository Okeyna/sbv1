from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.database import db
from app.models import AudioLesson, UploadedFile
from app.schemas import audio_schema, audios_schema, audio_position_schema
from app.services.tts_service import generate_audio
from app.config import Config

audio_bp = Blueprint('audio', __name__, url_prefix='/api/audio')

@audio_bp.route('/generate/<int:file_id>', methods=['POST'])
@jwt_required()
def generate_audio_route(file_id):
    """Generate audio lesson from file"""
    current_user_id = get_jwt_identity()
    
    uploaded_file = UploadedFile.query.filter_by(id=file_id, user_id=current_user_id).first()
    if not uploaded_file:
        return jsonify({'error': 'File not found'}), 404
    
    if not uploaded_file.text_content:
        return jsonify({'error': 'No text content available'}), 400
    
    # Check if audio already exists
    existing_audio = AudioLesson.query.filter_by(file_id=file_id, user_id=current_user_id).first()
    if existing_audio:
        return jsonify({
            'message': 'Audio already exists',
            'audio': audio_schema.dump(existing_audio)
        })
    
    try:
        # Generate audio
        audio_path, duration = generate_audio(uploaded_file.text_content, file_id)
        
        audio_lesson = AudioLesson(
            user_id=current_user_id,
            file_id=file_id,
            audio_path=audio_path,
            audio_url=f'/static/audio/{audio_path.split("/")[-1]}',
            duration=duration,
            voice_type='default'
        )
        
        db.session.add(audio_lesson)
        db.session.commit()
        
        return jsonify({
            'message': 'Audio generated successfully',
            'audio': audio_schema.dump(audio_lesson)
        }), 201
        
    except Exception as e:
        return jsonify({'error': f'Failed to generate audio: {str(e)}'}), 500


@audio_bp.route('/file/<int:file_id>', methods=['GET'])
@jwt_required()
def get_audio_for_file(file_id):
    """Get audio lesson for a specific file"""
    current_user_id = get_jwt_identity()
    audio = AudioLesson.query.filter_by(file_id=file_id, user_id=current_user_id).first()
    
    if not audio:
        return jsonify({'error': 'Audio not found'}), 404
    
    return jsonify({'audio': audio_schema.dump(audio)})


@audio_bp.route('/<int:audio_id>', methods=['GET'])
@jwt_required()
def get_audio(audio_id):
    """Get specific audio lesson"""
    current_user_id = get_jwt_identity()
    audio = AudioLesson.query.filter_by(id=audio_id, user_id=current_user_id).first()
    
    if not audio:
        return jsonify({'error': 'Audio not found'}), 404
    
    return jsonify({'audio': audio_schema.dump(audio)})


@audio_bp.route('/<int:audio_id>', methods=['DELETE'])
@jwt_required()
def delete_audio(audio_id):
    """Delete audio lesson"""
    current_user_id = get_jwt_identity()
    audio = AudioLesson.query.filter_by(id=audio_id, user_id=current_user_id).first()
    
    if not audio:
        return jsonify({'error': 'Audio not found'}), 404
    
    # Delete physical file
    try:
        import os
        if os.path.exists(audio.audio_path):
            os.remove(audio.audio_path)
    except Exception:
        pass
    
    db.session.delete(audio)
    db.session.commit()
    
    return jsonify({'message': 'Audio deleted successfully'})


@audio_bp.route('/<int:audio_id>/position', methods=['POST'])
@jwt_required()
def update_position(audio_id):
    """Update playback position"""
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data or 'position_seconds' not in data:
        return jsonify({'error': 'Position required'}), 400
    
    audio = AudioLesson.query.filter_by(id=audio_id, user_id=current_user_id).first()
    if not audio:
        return jsonify({'error': 'Audio not found'}), 404
    
    audio.position_seconds = float(data['position_seconds'])
    db.session.commit()
    
    return jsonify({
        'message': 'Position updated',
        'position_seconds': audio.position_seconds
    })
