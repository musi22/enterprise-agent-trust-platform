import os
from typing import List, Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Agentic Commerce Reliability & Recovery Lab"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./commerce_lab.db")
    
    # Security
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "super-secret-enterprise-agent-lab-jwt-token-key-32chars")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Model Provider Configuration
    DEFAULT_MODEL_PROVIDER: str = "deterministic_mock"  # deterministic_mock, gemini, openai, ollama
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY", None)
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY", None)
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    # Commerce & Policy Constraints
    REFUND_APPROVAL_THRESHOLD_CENTS: int = 5000  # $50.00 triggers human-in-the-loop approval
    MAX_RECOVERY_RETRIES: int = 3
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 3
    CIRCUIT_BREAKER_RECOVERY_TIMEOUT_SECONDS: int = 15

    # Event Streaming / Outbox
    KAFKA_BOOTSTRAP_SERVERS: Optional[str] = os.getenv("KAFKA_BOOTSTRAP_SERVERS", None)
    EVENT_OUTBOX_POLL_INTERVAL_MS: int = 500

    # Seed
    GLOBAL_RANDOM_SEED: int = 42

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
