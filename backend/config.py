import os
from dataclasses import dataclass, field
from typing import List # List is a type alias for a list of strings


def _split_csv_env(name: str, default: List[str]) -> List[str]:
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
#With dataclass:
# @dataclass
# class Settings:
#    environment: str
# Much shorter and cleaner.
#

@dataclass
class Settings:
    """Application configuration loaded from environment variables."""

    environment: str = os.getenv("APP_ENV", "development") # development is the fallback value if the APP_ENV environment variable is not set

    # CORS
    cors_origins: List[str] = field(
        default_factory=lambda: _split_csv_env( # default_factory is a function that returns default value if the environment variable is not set and each time a new instance of the Settings class is created, the default value is returned
            "BACKEND_CORS_ORIGINS",
            [
                "http://127.0.0.1:5173",
                "http://localhost:5173",
                "http://localhost:3000",
                "http://127.0.0.1:3000",
            ],
        )
    )

    # LLM / AI provider
    llm_provider: str = os.getenv("LLM_PROVIDER", "ollama")
    ollama_url: str = os.getenv(
        "OLLAMA_URL", "http://localhost:11434/api/generate"
    )
    ollama_model: str = os.getenv("OLLAMA_MODEL_NAME", "phi3")

    # Optional: placeholders for future hosted providers (kept here for clarity).
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY") or None
    openai_api_base: str | None = os.getenv("OPENAI_API_BASE") or None

    # Query safety
    default_query_limit: int = int(os.getenv("DEFAULT_QUERY_LIMIT", "100"))


settings = Settings()

