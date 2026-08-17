from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import User, UploadedFile, AIChat
from ..schemas import ChatMessage, ChatMessageResponse, ChatHistoryResponse
from ..auth import get_current_user
from ..services.ai_service import answer_question

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/message", response_model=ChatMessageResponse)
def send_message(
    message_data: ChatMessage,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a chat message and get AI response."""
    # Get the file for context
    file = db.query(UploadedFile).filter(
        UploadedFile.id == message_data.file_id,
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
            detail="No text content available for chat"
        )
    
    # Generate AI response
    try:
        response_text = answer_question(
            question=message_data.message,
            context=file.text_content
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate response: {str(e)}"
        )
    
    # Save chat message
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


@router.get("/{file_id}", response_model=ChatHistoryResponse)
def get_chat_history(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get chat history for a specific file."""
    messages = db.query(AIChat).filter(
        AIChat.file_id == file_id,
        AIChat.user_id == current_user.id
    ).order_by(AIChat.created_at.asc()).all()
    
    return ChatHistoryResponse(messages=messages)
