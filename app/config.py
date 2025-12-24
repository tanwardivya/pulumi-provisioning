"""Application configuration."""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings from environment variables."""
    
    # AWS Configuration
    aws_region: str = "us-east-1"
    s3_bucket_name: Optional[str] = None
    
    # Database Configuration
    db_host: Optional[str] = None
    db_port: int = 5432
    db_name: Optional[str] = None
    db_user: str = "admin"
    db_password: Optional[str] = None
    
    # Application Configuration
    app_name: str = "Pulumi Provisioning API"
    app_version: str = "1.0.0"
    debug: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

