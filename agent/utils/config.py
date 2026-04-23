from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "SignalForge"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"

    openai_api_key: str = ""
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = "deepseek/deepseek-chat"
    openrouter_fallback_model: str = "qwen/qwen3-32b"
    openrouter_timeout_seconds: int = 20
    openrouter_max_tokens: int = 220
    anthropic_api_key: str = ""
    resend_api_key: str = ""
    africas_talking_api_key: str = ""
    africas_talking_username: str = "sandbox"
    hubspot_api_key: str = ""
    calcom_api_key: str = ""
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "http://localhost:3001"

    redis_url: str = "redis://localhost:6379/0"
    database_url: str = "postgresql://signalforge:signalforge@localhost:5432/signalforge"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
