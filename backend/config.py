import os
from pathlib import Path

from dataclasses import dataclass, field

# Load .env from backend/ so GEMINI_API_KEY etc. work when running locally
try:
    from dotenv import load_dotenv

    _env_path = Path(__file__).resolve().parent / ".env"
    if _env_path.exists():
        load_dotenv(_env_path)
    else:
        # Fallback: project root .env (e.g. when running from repo root)
        _root_env = Path(__file__).resolve().parent.parent / ".env"
        if _root_env.exists():
            load_dotenv(_root_env)
except ImportError:
    pass


def _split_csv_env(name: str, default: list[str]) -> list[str]:
    raw = os.getenv(name)
    if not raw:
        return default
    parts = [item.strip() for item in raw.split(",")]
    return [p for p in parts if p]


# A dataclass is a cleaner way to define classes that mainly store data.

# Without dataclass:
# class Settings:
#    def __init__(self, environment):
#        self.environment = environment
#
# With dataclass:
# @dataclass
# class Settings:
#    environment: str
# Much shorter and cleaner.
#


@dataclass
class Settings:
    """Application configuration loaded from environment variables."""

    environment: str = os.getenv(
        "APP_ENV", "development"
    )  # development is the fallback value if the APP_ENV environment variable is not set

    # CORS
    cors_origins: list[str] = field(
        default_factory=lambda: (
            _split_csv_env(  # default_factory is a function that returns default value if the environment variable is not set and each time a new instance of the Settings class is created, the default value is returned
                "BACKEND_CORS_ORIGINS",
                [
                    "http://127.0.0.1:5173",
                    "http://localhost:5173",
                    "http://localhost:3000",
                    "http://127.0.0.1:3000",
                ],
            )
        )
    )

    # LLM / AI provider
    llm_provider: str = os.getenv("LLM_PROVIDER", "ollama")
    ollama_url: str = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
    ollama_model: str = os.getenv("OLLAMA_MODEL_NAME", "phi3")

    # Groq / OpenAI-compatible hosted providers
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY") or None
    openai_api_base: str | None = os.getenv("OPENAI_API_BASE") or None
    openai_model: str | None = os.getenv("OPENAI_MODEL") or None

    # Google AI Studio (Gemini)
    gemini_api_key: str | None = os.getenv("GEMINI_API_KEY") or None
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

    # Query safety
    default_query_limit: int = int(os.getenv("DEFAULT_QUERY_LIMIT", "100"))

    # App database (PostgreSQL for metadata)
    database_url: str = os.getenv(
        "DATABASE_URL", "postgresql://explorer:explorer_secret@localhost:5433/data_explorer"
    )

    # Auth / JWT
    secret_key: str = os.getenv("SECRET_KEY", "dev-secret-change-in-production")
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = int(
        os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    )
    jwt_refresh_token_expire_days: int = int(
        os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7")
    )

    # OAuth2 providers
    oauth_google_client_id: str | None = os.getenv("OAUTH_GOOGLE_CLIENT_ID") or None
    oauth_google_client_secret: str | None = os.getenv("OAUTH_GOOGLE_CLIENT_SECRET") or None
    oauth_github_client_id: str | None = os.getenv("OAUTH_GITHUB_CLIENT_ID") or None
    oauth_github_client_secret: str | None = os.getenv("OAUTH_GITHUB_CLIENT_SECRET") or None
    oauth_microsoft_client_id: str | None = os.getenv("OAUTH_MICROSOFT_CLIENT_ID") or None
    oauth_microsoft_client_secret: str | None = os.getenv("OAUTH_MICROSOFT_CLIENT_SECRET") or None

    # Encryption key for stored credentials (derived from secret_key if not set)
    encryption_key: str | None = os.getenv("ENCRYPTION_KEY") or None


settings = Settings()
