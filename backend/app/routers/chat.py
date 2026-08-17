from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import AIChat, UploadedFile, User
from app.schemas import ChatMessageRequest, ChatMessageResponse, ChatHistoryResponse
from app.services.ai_service import answer_question
from app.routers.auth import get_current_user

router = APIRouter()

@router.post("/message", response_model=ChatMessageResponse)
def send_message(
    message_data: ChatMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send a chat message"""
    uploaded_file = db.query(UploadedFile).filter(
        UploadedFile.id == message_data.file_id,
        UploadedFile.user_id == current_user.id
    ).first()
    
    if not uploaded_file:
        raise HTTPException(status_code=404, detail="File not found")
    
    if not uploaded_file.text_content:
        raise HTTPException(status_code=400, detail="No text content available")
    
    # Get AI response
    try:
        response_text = answer_question(uploaded_file.text_content, message_data.message)
        
        chat_message = AIChat(
            user_id=current_user.id,
            file_id=message_data.file_id,
            message=message_data.message,
            response=response_text
        )
        
        db.add(chat_message)
        db.commit()
        db.refresh(chat_message)
        
        return chat_message
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get AI response: {str(e)}")

@router.get("/{file_id}", response_model=ChatHistoryResponse)
def get_chat_history(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get chat history for a file"""
    messages = db.query(AIChat).filter(
        AIChat.file_id == file_id,
        AIChat.user_id == current_user.id
    ).order_by(AIChat.created_at.asc()).all()
    
    return {"messages": messages}
