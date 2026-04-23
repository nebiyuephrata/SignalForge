from __future__ import annotations

from typing import Any

from agent.channels.channel_schema import ChannelPolicyError, InboundChannelEvent, MalformedWebhookError, ProviderSendRequest, ProviderSendResult, WebhookProcessingResult
from agent.channels.event_router import ChannelEventRouter
from agent.channels.sms.africas_talking_client import AfricasTalkingClient
from agent.utils.trace_logger import append_jsonl_log


class SMSHandler:
    def __init__(
        self,
        client: AfricasTalkingClient | None = None,
        event_router: ChannelEventRouter | None = None,
        log_path: str = "logs/sms_events.jsonl",
    ) -> None:
        self.client = client or AfricasTalkingClient()
        self.event_router = event_router or ChannelEventRouter()
        self.log_path = log_path

    def register_inbound_handler(self, handler) -> None:  # noqa: ANN001
        self.event_router.register(handler)

    def send_warm_follow_up(
        self,
        request: ProviderSendRequest,
        *,
        prior_email_reply: bool,
    ) -> ProviderSendResult:
        # SMS is intentionally treated as a warm-lead channel only.
        if not prior_email_reply:
            raise ChannelPolicyError("SMS warm follow-up requires a prior email reply.")
        result = self.client.send(request)
        append_jsonl_log(self.log_path, {"event": "send", "request": request.model_dump(), "result": result.model_dump()})
        return result

    def handle_provider_webhook(self, payload: dict[str, Any]) -> WebhookProcessingResult:
        if not isinstance(payload, dict):
            raise MalformedWebhookError("SMS webhook payload must be a JSON object.")
        phone_number = str(payload.get("from", "")).strip()
        text = str(payload.get("text", "")).strip()
        if not phone_number or not text:
            raise MalformedWebhookError("Africa's Talking webhook payload must include from and text.")

        event = InboundChannelEvent(
            channel="sms",
            provider="africas_talking",
            event_type="reply",
            company_name=str(payload.get("company_name", "")).strip() or None,
            phone_number=phone_number,
            message_text=text,
            external_id=str(payload.get("id", payload.get("linkId", ""))) or None,
            raw_payload=payload,
        )
        routed = self.event_router.emit(event)
        append_jsonl_log(self.log_path, {"event": "webhook", "payload": payload, "mapped_event": event.model_dump()})
        return WebhookProcessingResult(
            status="processed",
            provider="africas_talking",
            channel="sms",
            event_type="reply",
            routed_handlers=len(routed),
            detail="Inbound SMS reply routed to downstream handlers.",
            event=event,
        )
