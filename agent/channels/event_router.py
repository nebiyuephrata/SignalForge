from __future__ import annotations

from typing import Any

from agent.channels.channel_schema import InboundChannelEvent, InboundHandler
from agent.utils.logger import get_logger
from agent.utils.trace_logger import append_jsonl_log

logger = get_logger(__name__)


class ChannelEventRouter:
    def __init__(self, log_path: str = "logs/channel_events.jsonl") -> None:
        self._handlers: list[InboundHandler] = []
        self.log_path = log_path

    def register(self, handler: InboundHandler) -> None:
        self._handlers.append(handler)

    def emit(self, event: InboundChannelEvent) -> list[dict[str, Any]]:
        append_jsonl_log(self.log_path, event.model_dump())
        responses: list[dict[str, Any]] = []
        for handler in self._handlers:
            try:
                response = handler(event)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Inbound handler failed for channel=%s event=%s: %s", event.channel, event.event_type, exc)
                responses.append({"handler_error": str(exc)})
                continue
            if response is not None:
                responses.append(response)
        return responses
