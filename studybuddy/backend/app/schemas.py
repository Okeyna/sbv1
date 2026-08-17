from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


# User schemas
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


class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int


class TokenData(BaseModel):
    user_id: Optional[int] = None
    email: Optional[str] = None


# File schemas
class FileUpload(BaseModel):
    filename: str
    status: str = "processing"


class FileResponse(BaseModel):
    id: int
    user_id: int
    filename: str
    file_path: str
    text_content: Optional[str] = None
    summary: Optional[str] = None
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class FileListResponse(BaseModel):
    files: List[FileResponse]
    total: int


# Audio schemas
class AudioGenerate(BaseModel):
    voice_type: Optional[str] = "alloy"


class AudioResponse(BaseModel):
    id: int
    user_id: int
    file_id: int
    audio_path: Optional[str] = None
    audio_url: Optional[str] = None
    duration: Optional[float] = None
    voice_type: str
    position_seconds: float
    created_at: datetime
    
    class Config:
        from_attributes = True


class AudioPositionUpdate(BaseModel):
    position_seconds: float


# Quiz schemas
class QuizQuestionSchema(BaseModel):
    question: str
    options: List[str]
    correct_answer: int
    explanation: Optional[str] = None


class QuizGenerate(BaseModel):
    difficulty: Optional[str] = "medium"
    num_questions: Optional[int] = 5


class QuizQuestionResponse(BaseModel):
    id: int
    quiz_id: int
    question: str
    options: List[str]
    correct_answer: int
    explanation: Optional[str] = None
    
    class Config:
        from_attributes = True


class QuizResponse(BaseModel):
    id: int
    user_id: int
    file_id: int
    title: str
    difficulty: str
    created_at: datetime
    questions: List[QuizQuestionResponse] = []
    
    class Config:
        from_attributes = True


class QuizSubmitAnswer(BaseModel):
    answers: List[int]  # List of selected option indices


class QuizAttemptResponse(BaseModel):
    score: float
    correct: int
    total: int
    completed_at: datetime
    questions: List[QuizQuestionResponse]


# Chat schemas
class ChatMessage(BaseModel):
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


# Progress schemas
class ProgressListeningUpdate(BaseModel):
    file_id: int
    seconds: float


class ProgressCompletionUpdate(BaseModel):
    file_id: int
    completion: float = Field(..., ge=0, le=100)


class WeakTopic(BaseModel):
    topic: str
    file_id: int
    file_name: str
    quiz_avg: float


class ProgressResponse(BaseModel):
    total_files: int
    total_audio_lessons: int
    total_quizzes: int
    total_quiz_attempts: int
    avg_quiz_score: float
    total_listening_time: float  # in seconds
    study_hours: float
    weak_topics: List[WeakTopic]
