from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    
    # API
    API_V2_STR: str = "/api/v2"
    PROJECT_NAME: str = "Prompter"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Clerk
    CLERK_PUBLISHABLE_KEY: Optional[str] = None
    CLERK_SECRET_KEY: Optional[str] = None
    CLERK_JWT_VERIFICATION_KEY: Optional[str] = None
    CLERK_JWKS_URL: Optional[str] = None
    CLERK_WEBHOOK_SECRET: Optional[str] = None
    
    # CORS
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    
    # Stripe
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None

    # LLM
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"

    # Topic limits (per plan)
    TOPIC_LIMIT_FREE: int = 3
    TOPIC_LIMIT_BASIC: int = 10
    TOPIC_LIMIT_PRO: int = 50
    TOPIC_LIMIT_ENTERPRISE: int = -1  # unlimited
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
