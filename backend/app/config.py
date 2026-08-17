from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    database_url: str = "sqlite:///./studybuddy.db"
    
    # JWT
    secret_key: str = "change-this-in-production-use-a-secure-random-string"
    access_token_expire_minutes: int = 1440
    algorithm: str = "HS256"
    
    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    
    # TTS
    tts_provider: str = "mock"
    
    # CORS
    frontend_origin: str = "http://localhost:5173"
    allowed_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    
    # File upload
    max_file_size: int = 20 * 1024 * 1024  # 20 MB
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    def get_allowed_origins(self) -> List[str]:
        """Parse allowed origins from comma-separated string."""
        return [origin.strip() for origin in self.allowed_origins.split(",")]


settings = Settings()
