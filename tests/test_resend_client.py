import json

import httpx

from agent.channels.channel_schema import ProviderSendRequest
from agent.channels.email.resend_client import ResendClient
from agent.utils.config import Settings


def test_resend_client_routes_delivery_to_staff_sink_when_configured() -> None:
    captured_payload: dict[str, object] = {}
    captured_headers: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured_payload, captured_headers
        captured_payload = json.loads(request.content.decode("utf-8"))
        captured_headers = dict(request.headers)
        return httpx.Response(200, json={"id": "email-123"}, request=request)

    settings = Settings.model_construct(
        resend_api_key="re_test_key",
        resend_api_base_url="https://api.resend.com",
        resend_from_email="SignalForge <onboarding@resend.dev>",
        resend_reply_to="replies@updates.signalforge.local",
        staff_sink_email="team@example.com",
    )
    client = ResendClient(
        settings=settings,
        http_client_factory=lambda: httpx.Client(transport=httpx.MockTransport(handler)),
    )

    result = client.send(
        ProviderSendRequest(
            company_name="Northstar Lending",
            contact_email="cto@northstar.example",
            subject="Context: Northstar Lending hiring signal",
            body="Grounded Tenacious outreach body.",
        )
    )

    assert captured_payload["to"] == ["team@example.com"]
    assert captured_payload["headers"]["X-SignalForge-Intended-To"] == "cto@northstar.example"
    assert captured_headers["authorization"] == "Bearer re_test_key"
    assert result.status == "queued"
    assert result.destination == "team@example.com"
    assert result.raw_response["intended_contact_email"] == "cto@northstar.example"
    assert "staff sink" in result.detail.lower()
