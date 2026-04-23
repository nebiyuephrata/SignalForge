from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class ProviderSendRequest(BaseModel):
    company_name: str
    subject: str | None = None
    body: str
    contact_email: str | None = None
    phone_number: str | None = None
    contact_name: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProviderSendResult(BaseModel):
    channel: Literal["email", "sms"]
    provider: str
    status: Literal["queued", "sent", "failed", "skipped"]
    destination: str
    external_id: str | None = None
    detail: str = ""
    error_code: str | None = None
    raw_response: dict[str, Any] = Field(default_factory=dict)


class InboundChannelEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: uuid4().hex)
    channel: Literal["email", "sms", "calendar"]
    provider: str
    event_type: str
    company_name: str | None = None
    contact_email: str | None = None
    phone_number: str | None = None
    message_text: str | None = None
    external_id: str | None = None
    raw_payload: dict[str, Any] = Field(default_factory=dict)
    received_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class WebhookProcessingResult(BaseModel):
    status: Literal["processed", "ignored", "error"]
    provider: str
    channel: Literal["email", "sms", "calendar"]
    event_type: str
    routed_handlers: int = 0
    detail: str = ""
    event: InboundChannelEvent | None = None


InboundHandler = Callable[[InboundChannelEvent], dict[str, Any] | None]


class ChannelPolicyError(RuntimeError):
    """Raised when a channel is used outside policy."""


class MalformedWebhookError(ValueError):
    """Raised when a webhook payload does not match the expected provider shape."""
