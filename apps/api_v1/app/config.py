"""Application configuration."""
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env", 
        case_sensitive=True,
        extra="ignore"  # Ignore extra fields from .env
    )

    # Application
    APP_NAME: str = "Prompter API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str
    DB_ECHO: bool = False

    # Redis
    REDIS_URL: str

    # JWT & Auth
    JWT_ALGORITHM: str = "RS256"
    JWT_AUDIENCE: str = "prompter-api"
    CLERK_JWKS_URL: str
    CLERK_SECRET_KEY: str
    CLERK_WEBHOOK_SECRET: str = ""

    # CORS - comma-separated list of allowed origins
    CORS_ORIGINS: str = "http://localhost:3005,http://localhost:3000,https://app.prompter.site"

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins into list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    # LLM Providers
    OPENAI_API_KEY: str
    PERPLEXITY_API_KEY: str
    GOOGLE_GENAI_API_KEY: str

    # S3 Storage
    S3_ENDPOINT: str
    S3_BUCKET: str
    S3_REGION: str = "us-east-1"
    S3_ACCESS_KEY: str
    S3_SECRET_KEY: str

    # Stripe
    STRIPE_SECRET_KEY: str
    STRIPE_WEBHOOK_SECRET: str
    STRIPE_STARTER_PRICE_ID: str = ""
    STRIPE_GROWTH_PRICE_ID: str = ""
    STRIPE_ENTERPRISE_PRICE_ID: str = ""

    # Email
    POSTMARK_API_KEY: str = ""
    POSTMARK_FROM_EMAIL: str = "noreply@prompter.site"

    # Observability
    OTEL_EXPORTER_OTLP_ENDPOINT: str = ""
    OTEL_SERVICE_NAME: str = "prompter-api"
    SENTRY_DSN: str = ""
    SENTRY_ENVIRONMENT: str = "development"

    # Application Settings
    BASE_HOSTNAME: str = "prompter.site"
    AUTH_REQUIRED: bool = True  # Set to False for demo/dev mode
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 60
    RATE_LIMIT_BURST: int = 120

    # Feature Flags
    ENABLE_SUBDOMAIN_ROUTING: bool = True
    ENABLE_PAGE_GENERATION: bool = True
    ENABLE_SCAN_SCHEDULING: bool = True


settings = Settings()


# Pricing Plan Quotas (hard caps, no add-ons/overages)
PLAN_QUOTAS = {
    "starter": {
        "brands": 1,
        "prompts": 30,
        "scans": 1000,
        "ai_pages": 3,
        "seats": 3,
        "retention_days": 30,
    },
    "pro": {
        "brands": 3,
        "prompts": 150,
        "scans": 5000,
        "ai_pages": 10,
        "seats": 10,
        "retention_days": 180,
    },
    "business": {
        "brands": 10,
        "prompts": 500,
        "scans": 15000,
        "ai_pages": 25,
        "seats": 25,
        "retention_days": 365,
    },
    "enterprise": {
        "brands": None,  # Unlimited
        "prompts": None,  # Unlimited
        "scans": None,  # Unlimited
        "ai_pages": None,  # Unlimited
        "seats": None,  # Unlimited
        "retention_days": None,  # Custom
    },
}

# Warning threshold (80% of quota)
WARN_THRESHOLD = 0.80

# Model scan credit weights (how many scan credits each model costs)
MODEL_WEIGHTS = {
    "chatgpt": 1,
    "gpt-4": 1,
    "gpt-3.5": 1,
    "gemini": 1,
    "gemini-pro": 1,
    "perplexity_online": 2,  # Online models cost 2x due to real-time search
    "perplexity-sonar": 2,
    "llama-3.1-sonar-large-128k-online": 2,
    "llama-3.1-sonar-small-128k-online": 2,
}

# User-facing copy for quota messages
QUOTA_MESSAGES = {
    "LIMIT_EXCEEDED": "{resource} limit reached. Please upgrade your plan.",
    "APPROACHING_LIMIT": "You're approaching your {resource} limit ({percent}% used). Consider upgrading.",
    "UPGRADE_CTA": "Upgrade to continue",
    "RESET_INFO": "Usage resets on {reset_date}",
}

