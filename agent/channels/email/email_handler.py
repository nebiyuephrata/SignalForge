from __future__ import annotations

from typing import Any

from agent.channels.channel_schema import InboundChannelEvent, MalformedWebhookError, ProviderSendRequest, ProviderSendResult, WebhookProcessingResult
from agent.channels.event_router import ChannelEventRouter
from agent.channels.email.resend_client import ResendClient
from agent.utils.trace_logger import append_jsonl_log


class EmailHandler:
    def __init__(
        self,
        client: ResendClient | None = None,
        event_router: ChannelEventRouter | None = None,
        log_path: str = "logs/email_events.jsonl",
    ) -> None:
        self.client = client or ResendClient()
        self.event_router = event_router or ChannelEventRouter()
        self.log_path = log_path

    def register_inbound_handler(self, handler) -> None:  # noqa: ANN001
        self.event_router.register(handler)

    def send(self, request: ProviderSendRequest) -> ProviderSendResult:
        result = self.client.send(request)
        append_jsonl_log(self.log_path, {"event": "send", "request": request.model_dump(), "result": result.model_dump()})
        return result

    def handle_provider_webhook(self, payload: dict[str, Any]) -> WebhookProcessingResult:
        if not isinstance(payload, dict):
            raise MalformedWebhookError("Email webhook payload must be a JSON object.")
        event_type = str(payload.get("type", "")).strip()
        data = payload.get("data")
        if not event_type or not isinstance(data, dict):
            raise MalformedWebhookError("Resend webhook payload must include type and data.")

        mapped_event_type = self._map_event_type(event_type)
        event = InboundChannelEvent(
            channel="email",
            provider="resend",
            event_type=mapped_event_type,
            company_name=self._first_tag_value(data.get("tags"), "company_name"),
            contact_email=str(data.get("to", "")) or None,
            message_text=str(data.get("text", "")) or None,
            external_id=str(data.get("email_id", data.get("id", ""))) or None,
            raw_payload=payload,
        )
        routed = self.event_router.emit(event) if mapped_event_type == "reply" else []
        append_jsonl_log(self.log_path, {"event": "webhook", "payload": payload, "mapped_event": event.model_dump()})
        return WebhookProcessingResult(
            status="processed",
            provider="resend",
            channel="email",
            event_type=mapped_event_type,
            routed_handlers=len(routed),
            detail=self._detail_for_event(mapped_event_type),
            event=event,
        )

    @staticmethod
    def _map_event_type(event_type: str) -> str:
        mapping = {
            "email.sent": "sent",
            "email.delivered": "delivered",
            "email.delivery_delayed": "delivery_delayed",
            "email.bounced": "bounced",
            "email.complained": "complained",
            "email.reply_received": "reply",
            "email.replied": "reply",
        }
        return mapping.get(event_type, "ignored")

    @staticmethod
    def _detail_for_event(event_type: str) -> str:
        if event_type == "reply":
            return "Inbound email reply routed to downstream handlers."
        if event_type == "bounced":
            return "Bounce received and logged."
        if event_type == "ignored":
            return "Webhook accepted but not routed."
        return "Webhook accepted."

    @staticmethod
    def _first_tag_value(tags: Any, name: str) -> str | None:
        if not isinstance(tags, list):
            return None
        for tag in tags:
            if isinstance(tag, dict) and tag.get("name") == name:
                value = str(tag.get("value", "")).strip()
                return value or None
        return None
