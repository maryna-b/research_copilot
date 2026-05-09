from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    API_KEY: str = "dev-key-change-in-production"  # NOSONAR
    MAX_FILE_SIZE: int = 50 * 1024 * 1024

    DATABASE_URL: str = "sqlite:///./documents.db"
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 100

    OPENAI_API_KEY: str = ""
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8000


settings = Settings()
