import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "AI Hiring Assistant API"
    APP_VERSION: str = "1.0.0"
    UPLOAD_DIR: str = "temp_uploads"

    class Config:
        env_file = ".env"

settings = Settings()