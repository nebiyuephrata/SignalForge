from __future__ import annotations

from agent.channels.channel_schema import ProviderSendRequest, ProviderSendResult


class WhatsAppClient:
    """Twilio-ready WhatsApp stub.

    The repository keeps this deterministic for local use while preserving the
    provider boundary expected by the orchestrator.
    """

    def send(self, request: ProviderSendRequest) -> ProviderSendResult:
        if not request.phone_number:
            return ProviderSendResult(
                channel="whatsapp",
                provider="whatsapp_stub",
                status="failed",
                destination="",
                detail="Missing phone_number for WhatsApp send.",
                error_code="missing_destination",
            )
        return ProviderSendResult(
            channel="whatsapp",
            provider="whatsapp_stub",
            status="queued",
            destination=request.phone_number,
            external_id=f"wa-{request.company_name.lower().replace(' ', '-')}",
            detail="WhatsApp stub accepted the warm follow-up.",
            raw_response={"provider_mode": "stub"},
        )
