from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

# User Schemas
class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=6)

class UserResponse(UserBase):
    id: int
    role: str
    subscription_type: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# File Schemas
class FileBase(BaseModel):
    filename: Optional[str] = None
    status: Optional[str] = None

class FileCreate(FileBase):
    user_id: int
    file_path: str
    text_content: str

class FileResponse(FileBase):
    id: int
    user_id: int
    file_path: str
    text_content: str
    summary: Optional[str] = None
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class FileListResponse(BaseModel):
    files: List[FileResponse]

class SummaryResponse(BaseModel):
    message: str
    summary: str

# Audio Schemas
class AudioLessonBase(BaseModel):
    file_id: int
    voice_type: Optional[str] = "alloy"

class AudioLessonResponse(AudioLessonBase):
    id: int
    user_id: int
    audio_path: str
    audio_url: str
    duration: Optional[float] = None
    position_seconds: Optional[float] = 0.0
    created_at: datetime
    
    class Config:
        from_attributes = True

class AudioPositionUpdate(BaseModel):
    position_seconds: float

class AudioListResponse(BaseModel):
    audio_lessons: List[AudioLessonResponse]

# Quiz Schemas
class QuizQuestionBase(BaseModel):
    question: str
    options: List[str]
    correct_answer: int
    explanation: str

class QuizQuestionResponse(QuizQuestionBase):
    id: int
    
    class Config:
        from_attributes = True

class QuizBase(BaseModel):
    file_id: int
    title: Optional[str] = None
    difficulty: Optional[str] = "medium"

class QuizResponse(QuizBase):
    id: int
    user_id: int
    created_at: datetime
    questions: List[QuizQuestionResponse] = []
    
    class Config:
        from_attributes = True

class QuizSubmitRequest(BaseModel):
    answers: List[int]  # List of selected option indices

class QuizAttemptResponse(BaseModel):
    id: int
    user_id: int
    quiz_id: int
    score: int
    correct: int
    total: int
    answers: List[int]
    completed_at: datetime
    
    class Config:
        from_attributes = True

class QuizListResponse(BaseModel):
    quizzes: List[QuizResponse]

# Chat Schemas
class ChatMessageRequest(BaseModel):
    file_id: int
    message: str

class ChatMessageResponse(BaseModel):
    id: int
    user_id: int
    file_id: int
    message: str
    response: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class ChatHistoryResponse(BaseModel):
    messages: List[ChatMessageResponse]

# Progress Schemas
class StudyProgressBase(BaseModel):
    completion: float = 0.0
    listening_time: float = 0.0
    quiz_avg: float = 0.0

class StudyProgressResponse(StudyProgressBase):
    id: int
    user_id: int
    file_id: int
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ListeningTimeUpdate(BaseModel):
    file_id: int
    seconds: float

class CompletionUpdate(BaseModel):
    file_id: int
    percentage: float = Field(..., ge=0, le=100)

class WeakTopic(BaseModel):
    file_id: int
    filename: str
    quiz_count: int
    avg_score: float

class ProgressSummary(BaseModel):
    total_files: int
    total_audio_lessons: int
    total_quizzes: int
    total_quiz_attempts: int
    avg_quiz_score: float
    total_listening_time: float
    study_hours: float
    weak_topics: List[WeakTopic]
