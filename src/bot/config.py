from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    bot_token: SecretStr
    llm_api_key: SecretStr
    llm_api_url: str = "https://api.openai.com/v1/chat/completions"
    llm_model: str = "gpt-4o-mini"
    llm_timeout_seconds: float = Field(default=60.0, gt=0)
    llm_max_input_chars: int = Field(default=60_000, gt=0)
    llm_max_chunk_chars: int = Field(default=6_000, gt=0)
    llm_temperature: float = Field(default=0.2, ge=0, le=2)
