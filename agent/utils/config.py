from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "SignalForge"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    base_url: str = Field(default="http://0.0.0.0:10000", validation_alias=AliasChoices("BASE_URL"))
    log_level: str = "INFO"
    frontend_origins: str = "http://127.0.0.1:5173,http://localhost:5173"

    openai_api_key: str = ""
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = "deepseek/deepseek-chat"
    openrouter_fallback_model: str = "qwen/qwen3-32b"
    openrouter_timeout_seconds: int = 20
    openrouter_max_tokens: int = 220
    anthropic_api_key: str = ""
    resend_api_key: str = ""
    resend_api_base_url: str = "https://api.resend.com"
    resend_from_email: str = "SignalForge <signals@updates.signalforge.local>"
    resend_reply_to: str = "replies@updates.signalforge.local"
    staff_sink_email: str = ""
    resend_webhook_secret: str = ""
    africas_talking_api_key: str = ""
    africas_talking_username: str = "sandbox"
    africas_talking_base_url: str = "https://api.africastalking.com/version1"
    africas_talking_webhook_secret: str = ""
    whatsapp_api_key: str = ""
    whatsapp_base_url: str = "https://api.twilio.com/whatsapp"
    whatsapp_webhook_secret: str = ""
    hubspot_api_key: str = Field(default="", validation_alias=AliasChoices("HUBSPOT_API_KEY"))
    hubspot_access_token: str = ""
    hubspot_base_url: str = "https://api.hubapi.com"
    calcom_api_key: str = Field(default="", validation_alias=AliasChoices("CALCOM_API_KEY", "CAL_API_KEY"))
    calcom_base_url: str = "https://cal.com"
    calcom_booking_slug: str = "signalforge-discovery"
    calcom_webhook_secret: str = ""
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = Field(
        default="http://localhost:3001",
        validation_alias=AliasChoices("LANGFUSE_HOST", "LANGFUSE_BASE_URL"),
    )

    redis_url: str = "redis://localhost:6379/0"
    database_url: str = "postgresql://signalforge:signalforge@localhost:5432/signalforge"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def public_base_url(self) -> str:
        return self.base_url.rstrip("/")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
