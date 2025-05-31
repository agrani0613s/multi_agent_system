import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Redis Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # External Services (Simulation)
    CRM_API_URL: str = "http://localhost:8001/crm"
    RISK_API_URL: str = "http://localhost:8001/risk"
    
    # LLM Configuration (Optional - for advanced classification)
    OPENAI_API_KEY: str = ""
    
    # File Upload Configuration
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    UPLOAD_DIR: str = "uploads"
    
    class Config:
        env_file = ".env"

settings = Settings()