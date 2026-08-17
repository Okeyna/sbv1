from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.database import db
from app.models import AIChat, UploadedFile
from app.schemas import chat_schema, chats_schema
from app.services.ai_service import answer_question

chat_bp = Blueprint('chat', __name__, url_prefix='/api/chat')

@chat_bp.route('/message', methods=['POST'])
@jwt_required()
def send_message():
    """Send a message to AI tutor"""
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data or 'message' not in data or 'file_id' not in data:
        return jsonify({'error': 'Message and file_id required'}), 400
    
    message = data['message']
    file_id = data['file_id']
    
    # Get file context
    uploaded_file = UploadedFile.query.filter_by(id=file_id, user_id=current_user_id).first()
    if not uploaded_file:
        return jsonify({'error': 'File not found'}), 404
    
    if not uploaded_file.text_content:
        return jsonify({'error': 'No text content available for this file'}), 400
    
    try:
        # Get AI response with file context
        response = answer_question(message, uploaded_file.text_content)
        
        # Store chat message
        chat_message = AIChat(
            user_id=current_user_id,
            file_id=file_id,
            message=message,
            response=response
        )
        
        db.session.add(chat_message)
        db.session.commit()
        
        return jsonify({
            'message': message,
            'response': response,
            'id': chat_message.id,
            'created_at': chat_message.created_at.isoformat() if chat_message.created_at else None
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get AI response: {str(e)}'}), 500


@chat_bp.route('/<int:file_id>', methods=['GET'])
@jwt_required()
def get_chat_history(file_id):
    """Get chat history for a specific file"""
    current_user_id = get_jwt_identity()
    chats = AIChat.query.filter_by(file_id=file_id, user_id=current_user_id).order_by(AIChat.created_at.asc()).all()
    return jsonify({'chats': chats_schema.dump(chats)})


@chat_bp.route('/history', methods=['GET'])
@jwt_required()
def get_all_chat_history():
    """Get all chat history for current user"""
    current_user_id = get_jwt_identity()
    chats = AIChat.query.filter_by(user_id=current_user_id).order_by(AIChat.created_at.desc()).limit(50).all()
    return jsonify({'chats': chats_schema.dump(chats)})


@chat_bp.route('/<int:chat_id>', methods=['DELETE'])
@jwt_required()
def delete_chat(chat_id):
    """Delete a chat message"""
    current_user_id = get_jwt_identity()
    chat = AIChat.query.filter_by(id=chat_id, user_id=current_user_id).first()
    
    if not chat:
        return jsonify({'error': 'Chat not found'}), 404
    
    db.session.delete(chat)
    db.session.commit()
    
    return jsonify({'message': 'Chat deleted successfully'})
