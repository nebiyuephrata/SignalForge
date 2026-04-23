from __future__ import annotations

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
        if not self.settings.resend_api_key:
            return ProviderSendResult(
                channel="email",
                provider="resend",
                status="failed",
                destination=request.contact_email,
                detail="RESEND_API_KEY is not configured.",
                error_code="missing_api_key",
            )

        payload = {
            "from": self.settings.resend_from_email,
            "to": [request.contact_email],
            "subject": request.subject or f"{request.company_name} talent signal",
            "text": request.body,
            "reply_to": self.settings.resend_reply_to,
            "tags": [
                {"name": "company_name", "value": request.company_name},
                {"name": "channel", "value": "signalforge-email"},
            ],
            "headers": {
                "X-SignalForge-Company": request.company_name,
            },
        }

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
                destination=request.contact_email,
                detail=f"Resend rejected the request with status {exc.response.status_code}.",
                error_code=f"http_{exc.response.status_code}",
                raw_response=self._safe_json(exc.response),
            )
        except httpx.HTTPError as exc:
            return ProviderSendResult(
                channel="email",
                provider="resend",
                status="failed",
                destination=request.contact_email,
                detail=f"Resend request failed: {exc}",
                error_code="transport_error",
            )

        body = self._safe_json(response)
        return ProviderSendResult(
            channel="email",
            provider="resend",
            status="queued",
            destination=request.contact_email,
            external_id=str(body.get("id", "")) or None,
            detail="Email accepted by Resend.",
            raw_response=body,
        )

    @staticmethod
    def _safe_json(response: httpx.Response) -> dict[str, Any]:
        try:
            payload = response.json()
            return payload if isinstance(payload, dict) else {"payload": payload}
        except ValueError:
            return {"text": response.text}
