from __future__ import annotations

import re
from typing import Any, Callable

import httpx

from agent.channels.channel_schema import ProviderSendRequest, ProviderSendResult
from agent.utils.config import Settings, get_settings


class ResendClient:
    def __init__(
        self,
        settings: Settings | None = None,
        http_client_factory: Callable[[], httpx.Client] | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.http_client_factory = http_client_factory or (lambda: httpx.Client(timeout=20.0))

    def send(self, request: ProviderSendRequest) -> ProviderSendResult:
        if not request.contact_email:
            return ProviderSendResult(
                channel="email",
                provider="resend",
                status="failed",
                destination="",
                detail="Missing contact_email.",
                error_code="missing_destination",
            )

        delivery_email = self._delivery_email(request.contact_email)
        using_staff_sink = delivery_email.strip().lower() != request.contact_email.strip().lower()
        if not self.settings.resend_api_key:
            return ProviderSendResult(
                channel="email",
                provider="resend",
                status="failed",
                destination=delivery_email,
                detail="RESEND_API_KEY is not configured.",
                error_code="missing_api_key",
            )

        payload = {
            "from": self.settings.resend_from_email,
            "to": [delivery_email],
            "subject": request.subject or f"{request.company_name} talent signal",
            "text": request.body,
            "reply_to": self.settings.resend_reply_to,
            "tags": [
                {"name": "company_name", "value": self._sanitize_tag_value(request.company_name)},
                {"name": "channel", "value": "signalforge-email"},
            ],
            "headers": {
                "X-SignalForge-Company": request.company_name,
                "X-SignalForge-Intended-To": request.contact_email,
            },
        }
        if using_staff_sink:
            payload["tags"].append({"name": "sink_mode", "value": "staff"})
            payload["tags"].append({"name": "intended_to", "value": self._sanitize_tag_value(request.contact_email)})

        headers = {
            "Authorization": f"Bearer {self.settings.resend_api_key}",
            "Content-Type": "application/json",
        }
        try:
            with self.http_client_factory() as client:
                response = client.post(
                    f"{self.settings.resend_api_base_url}/emails",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            return ProviderSendResult(
                channel="email",
                provider="resend",
                status="failed",
                destination=delivery_email,
                detail=f"Resend rejected the request with status {exc.response.status_code}.",
                error_code=f"http_{exc.response.status_code}",
                raw_response=self._safe_json(exc.response),
            )
        except httpx.HTTPError as exc:
            return ProviderSendResult(
                channel="email",
                provider="resend",
                status="failed",
                destination=delivery_email,
                detail=f"Resend request failed: {exc}",
                error_code="transport_error",
            )

        body = self._safe_json(response)
        body["intended_contact_email"] = request.contact_email
        if using_staff_sink:
            body["staff_sink_email"] = delivery_email
        return ProviderSendResult(
            channel="email",
            provider="resend",
            status="queued",
            destination=delivery_email,
            external_id=str(body.get("id", "")) or None,
            detail=(
                "Email accepted by Resend and routed to the configured staff sink."
                if using_staff_sink
                else "Email accepted by Resend."
            ),
            raw_response=body,
        )

    @staticmethod
    def _safe_json(response: httpx.Response) -> dict[str, Any]:
        try:
            payload = response.json()
            return payload if isinstance(payload, dict) else {"payload": payload}
        except ValueError:
            return {"text": response.text}

    @staticmethod
    def _sanitize_tag_value(value: str) -> str:
        normalized = re.sub(r"[^A-Za-z0-9_-]+", "-", value.strip())
        collapsed = re.sub(r"-{2,}", "-", normalized).strip("-")
        return collapsed or "unknown"

    def _delivery_email(self, requested_email: str) -> str:
        sink_email = self.settings.staff_sink_email.strip()
        if sink_email:
            return sink_email
        return requested_email
