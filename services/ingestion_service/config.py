"""
Configuration settings for Ingestion Service.
"""
import os


class Settings:
    """Application settings loaded from environment variables."""

    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./documents.db")

    # Chunking settings
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "1000"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "100"))

    # Service info
    SERVICE_NAME: str = "ingestion-service"
    SERVICE_VERSION: str = "0.1.0"


settings = Settings()
