from __future__ import annotations

from typing import Any

from agent.channels.channel_schema import (
    ChannelPolicyError,
    InboundChannelEvent,
    MalformedWebhookError,
    ProviderSendRequest,
    ProviderSendResult,
    WebhookProcessingResult,
)
from agent.channels.event_router import ChannelEventRouter
from agent.channels.whatsapp.whatsapp_client import WhatsAppClient
from agent.utils.trace_logger import append_jsonl_log


class WhatsAppHandler:
    def __init__(
        self,
        client: WhatsAppClient | None = None,
        event_router: ChannelEventRouter | None = None,
        log_path: str = "logs/whatsapp_events.jsonl",
    ) -> None:
        self.client = client or WhatsAppClient()
        self.event_router = event_router or ChannelEventRouter()
        self.log_path = log_path

    def register_inbound_handler(self, handler) -> None:  # noqa: ANN001
        self.event_router.register(handler)

    def send_warm_follow_up(self, request: ProviderSendRequest, *, prior_email_reply: bool) -> ProviderSendResult:
        if not prior_email_reply:
            raise ChannelPolicyError("WhatsApp warm follow-up requires a prior email reply.")
        result = self.client.send(request)
        append_jsonl_log(self.log_path, {"event": "send", "request": request.model_dump(), "result": result.model_dump()})
        return result

    def handle_provider_webhook(self, payload: dict[str, Any]) -> WebhookProcessingResult:
        if not isinstance(payload, dict):
            raise MalformedWebhookError("WhatsApp webhook payload must be a JSON object.")
        phone_number = str(payload.get("from", "")).strip()
        text = str(payload.get("text", "")).strip()
        if not phone_number or not text:
            raise MalformedWebhookError("WhatsApp webhook payload must include from and text.")

        event = InboundChannelEvent(
            channel="whatsapp",
            provider="whatsapp_stub",
            event_type="reply",
            company_name=str(payload.get("company_name", "")).strip() or None,
            phone_number=phone_number,
            contact_email=str(payload.get("contact_email", "")).strip() or None,
            message_text=text,
            external_id=str(payload.get("id", "")) or None,
            raw_payload=payload,
        )
        routed = self.event_router.emit(event)
        append_jsonl_log(self.log_path, {"event": "webhook", "payload": payload, "mapped_event": event.model_dump()})
        return WebhookProcessingResult(
            status="processed",
            provider="whatsapp_stub",
            channel="whatsapp",
            event_type="reply",
            routed_handlers=len(routed),
            detail="Inbound WhatsApp reply routed to downstream handlers.",
            event=event,
        )
