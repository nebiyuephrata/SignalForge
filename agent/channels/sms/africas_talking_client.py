from __future__ import annotations

from typing import Any, Callable

import httpx

from agent.channels.channel_schema import ProviderSendRequest, ProviderSendResult
from agent.utils.config import Settings, get_settings


class AfricasTalkingClient:
    def __init__(
        self,
        settings: Settings | None = None,
        http_client_factory: Callable[[], httpx.Client] | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.http_client_factory = http_client_factory or (lambda: httpx.Client(timeout=20.0))

    def send(self, request: ProviderSendRequest) -> ProviderSendResult:
        if not request.phone_number:
            return ProviderSendResult(
                channel="sms",
                provider="africas_talking",
                status="failed",
                destination="",
                detail="Missing phone_number.",
                error_code="missing_destination",
            )
        if not self.settings.africas_talking_api_key:
            return ProviderSendResult(
                channel="sms",
                provider="africas_talking",
                status="failed",
                destination=request.phone_number,
                detail="AFRICAS_TALKING_API_KEY is not configured.",
                error_code="missing_api_key",
            )

        headers = {
            "apiKey": self.settings.africas_talking_api_key,
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {
            "username": self.settings.africas_talking_username,
            "to": request.phone_number,
            "message": request.body,
        }

        try:
            with self.http_client_factory() as client:
                response = client.post(
                    f"{self.settings.africas_talking_base_url}/messaging",
                    headers=headers,
                    data=data,
                )
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            return ProviderSendResult(
                channel="sms",
                provider="africas_talking",
                status="failed",
                destination=request.phone_number,
                detail=f"Africa's Talking rejected the request with status {exc.response.status_code}.",
                error_code=f"http_{exc.response.status_code}",
                raw_response=self._safe_json(exc.response),
            )
        except httpx.HTTPError as exc:
            return ProviderSendResult(
                channel="sms",
                provider="africas_talking",
                status="failed",
                destination=request.phone_number,
                detail=f"Africa's Talking request failed: {exc}",
                error_code="transport_error",
            )

        body = self._safe_json(response)
        recipients = (
            body.get("SMSMessageData", {}).get("Recipients", [])
            if isinstance(body.get("SMSMessageData"), dict)
            else []
        )
        message_id = str(recipients[0].get("messageId", "")) if recipients else None
        return ProviderSendResult(
            channel="sms",
            provider="africas_talking",
            status="queued",
            destination=request.phone_number,
            external_id=message_id or None,
            detail="SMS accepted by Africa's Talking.",
            raw_response=body,
        )

    @staticmethod
    def _safe_json(response: httpx.Response) -> dict[str, Any]:
        try:
            payload = response.json()
            return payload if isinstance(payload, dict) else {"payload": payload}
        except ValueError:
            return {"text": response.text}
