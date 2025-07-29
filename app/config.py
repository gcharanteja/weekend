from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Angel One API Configuration
    api_key: str
    username: str  
    password: str
    totp_key: str
    
    # Database Configuration
    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/trading_bot"
    redis_url: str = "redis://localhost:6379/0"
    
    # Application Configuration
    debug: bool = False
    log_level: str = "INFO"
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Security
    secret_key: str = "your-secret-key-change-this"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Trading Configuration
    max_position_size: float = 100000.0
    max_daily_loss: float = 10000.0
    risk_percentage: float = 2.0
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()