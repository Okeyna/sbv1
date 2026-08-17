import os
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import List
import time

from app.database import get_db
from app.models import UploadedFile, StudyProgress, User
from app.schemas import FileResponse, FileListResponse, SummaryResponse
from app.services.pdf_service import extract_text_from_pdf
from app.services.ai_service import generate_summary
from app.config import Config
from app.routers.auth import get_current_user

router = APIRouter()

ALLOWED_EXTENSIONS = {'pdf'}
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB

def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@router.post("/upload", response_model=FileResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload a PDF file"""
    if not allowed_file(file.filename):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Read file content
    content = await file.read()
    file_size = len(content)
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 20MB")
    
    if file_size == 0:
        raise HTTPException(status_code=400, detail="File is empty")
    
    # Save file
    filename = f"{int(time.time())}_{file.filename}"
    filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    
    with open(filepath, "wb") as f:
        f.write(content)
    
    # Extract text from PDF
    try:
        text_content = extract_text_from_pdf(filepath)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to extract text from PDF: {str(e)}")
    
    if not text_content or len(text_content.strip()) == 0:
        raise HTTPException(status_code=400, detail="PDF appears to be empty or unreadable")
    
    # Create database record
    uploaded_file = UploadedFile(
        user_id=current_user.id,
        filename=filename,
        file_path=filepath,
        text_content=text_content,
        status='processing'
    )
    
    db.add(uploaded_file)
    db.commit()
    db.refresh(uploaded_file)
    
    # Generate summary
    try:
        summary = generate_summary(text_content)
        uploaded_file.summary = summary
        uploaded_file.status = 'ready'
        db.commit()
    except Exception:
        uploaded_file.status = 'error'
        db.commit()
    
    # Create progress record
    progress = StudyProgress(
        user_id=current_user.id,
        file_id=uploaded_file.id,
        completion=0.0,
        listening_time=0.0,
        quiz_avg=0.0
    )
    db.add(progress)
    db.commit()
    
    return uploaded_file

@router.get("", response_model=FileListResponse)
def get_files(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all files for current user"""
    files = db.query(UploadedFile).filter(
        UploadedFile.user_id == current_user.id
    ).order_by(UploadedFile.created_at.desc()).all()
    return {"files": files}

@router.get("/{file_id}", response_model=FileResponse)
def get_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific file"""
    uploaded_file = db.query(UploadedFile).filter(
        UploadedFile.id == file_id,
        UploadedFile.user_id == current_user.id
    ).first()
    
    if not uploaded_file:
        raise HTTPException(status_code=404, detail="File not found")
    
    return uploaded_file

@router.delete("/{file_id}")
def delete_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a file"""
    uploaded_file = db.query(UploadedFile).filter(
        UploadedFile.id == file_id,
        UploadedFile.user_id == current_user.id
    ).first()
    
    if not uploaded_file:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Delete physical file
    try:
        if os.path.exists(uploaded_file.file_path):
            os.remove(uploaded_file.file_path)
    except Exception:
        pass
    
    db.delete(uploaded_file)
    db.commit()
    
    return {"message": "File deleted successfully"}

@router.post("/{file_id}/summary", response_model=SummaryResponse)
def regenerate_summary(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Regenerate summary for a file"""
    uploaded_file = db.query(UploadedFile).filter(
        UploadedFile.id == file_id,
        UploadedFile.user_id == current_user.id
    ).first()
    
    if not uploaded_file:
        raise HTTPException(status_code=404, detail="File not found")
    
    if not uploaded_file.text_content:
        raise HTTPException(status_code=400, detail="No text content available")
    
    try:
        summary = generate_summary(uploaded_file.text_content)
        uploaded_file.summary = summary
        uploaded_file.status = 'ready'
        db.commit()
        
        return {"message": "Summary regenerated successfully", "summary": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate summary: {str(e)}")
