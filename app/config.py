import os


class Settings:
    API_KEY: str = os.getenv("API_KEY", "dev-key-change-in-production")
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", str(50 * 1024 * 1024)))

    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./documents.db")
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "1000"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "100"))

    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    CHROMA_HOST: str = os.getenv("CHROMA_HOST", "localhost")
    CHROMA_PORT: int = int(os.getenv("CHROMA_PORT", "8000"))


settings = Settings()
