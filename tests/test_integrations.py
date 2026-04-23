import asyncio

from fastapi import HTTPException

from agent.briefs.brief_schema import CRMFields, LeadRecord, OutboundMessage
from agent.channels.channel_schema import InboundChannelEvent, ProviderSendRequest, ProviderSendResult, WebhookProcessingResult
from agent.channels.email.email_handler import EmailHandler
from agent.channels.event_router import ChannelEventRouter
from agent.channels.sms.sms_handler import SMSHandler
from agent.signals.hiring_signals import build_hiring_signal_brief
from agent.tools.crunchbase_tool import CrunchbaseTool
from backend.routes import webhook_cal, webhook_email, webhook_sms
from backend.schemas import BookingWebhookRequest, SendEmailRequest, SendWarmSmsRequest
from backend.services.crm_service import CRMService


class FakeEmailClient:
    def send(self, request: ProviderSendRequest) -> ProviderSendResult:
        return ProviderSendResult(
            channel="email",
            provider="resend",
            status="queued",
            destination=request.contact_email or "",
            external_id="email-123",
            detail="queued",
        )


class FakeSMSClient:
    def send(self, request: ProviderSendRequest) -> ProviderSendResult:
        return ProviderSendResult(
            channel="sms",
            provider="africas_talking",
            status="queued",
            destination=request.phone_number or "",
            external_id="sms-123",
            detail="queued",
        )


class FakeHubSpotClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, object]]] = []

    def upsert_contact(self, *, email: str, properties: dict[str, object]) -> dict[str, object]:
        self.calls.append(("upsert_contact", {"email": email, **properties}))
        return {"id": "contact-1", "properties": properties}

    def create_note(self, *, contact_id: str, body: str) -> dict[str, object]:
        self.calls.append(("create_note", {"contact_id": contact_id, "body": body}))
        return {"id": "note-1", "contact_id": contact_id}


def test_hiring_signal_brief_merges_all_required_sources() -> None:
    brief = build_hiring_signal_brief("Northstar Lending", CrunchbaseTool())

    signal_names = {signal["signal"] for signal in brief["signals"]}
    assert {"funding_event", "job_post_scrape", "job_post_velocity", "layoffs", "leadership_change"} <= signal_names
    assert brief["source_artifact"]["job_post_scrape"]["confidence"] >= 0.7
    assert brief["source_artifact"]["leadership_change"]["confidence"] >= 0.35


def test_email_handler_routes_inbound_replies_to_downstream_handler() -> None:
    captured: list[InboundChannelEvent] = []
    router = ChannelEventRouter(log_path="/tmp/test-email-events.jsonl")
    router.register(lambda event: captured.append(event) or {"accepted": True})
    handler = EmailHandler(client=FakeEmailClient(), event_router=router, log_path="/tmp/test-email-handler.jsonl")

    result = handler.handle_provider_webhook(
        {
            "type": "email.replied",
            "data": {
                "id": "evt-1",
                "email_id": "email-123",
                "to": "cto@northstar.example",
                "text": "Yes, this is relevant.",
                "tags": [{"name": "company_name", "value": "Northstar Lending"}],
            },
        }
    )

    assert result.status == "processed"
    assert result.routed_handlers == 1
    assert captured[0].message_text == "Yes, this is relevant."


def test_sms_handler_enforces_warm_lead_gating() -> None:
    handler = SMSHandler(client=FakeSMSClient(), log_path="/tmp/test-sms-handler.jsonl")

    try:
        handler.send_warm_follow_up(
            ProviderSendRequest(company_name="Northstar Lending", phone_number="+15551234567", body="Follow up"),
            prior_email_reply=False,
        )
    except Exception as exc:  # noqa: BLE001
        assert "prior email reply" in str(exc)
    else:
        raise AssertionError("Expected SMS policy failure")


def test_email_send_route_syncs_to_crm(monkeypatch) -> None:
    monkeypatch.setattr(webhook_email, "email_handler", EmailHandler(client=FakeEmailClient(), log_path="/tmp/route-email.jsonl"))
    monkeypatch.setattr(
        webhook_email.conversation_service,
        "draft_outreach",
        lambda lead: OutboundMessage(
            channel="email",
            body="Draft body",
            crm_fields=CRMFields(
                icp_segment="growth_fintech",
                signal_confidence=0.72,
                ai_maturity=1,
                intent_level="high",
                qualification_status="qualified",
                next_action="share_booking_link",
            ),
        ),
    )
    monkeypatch.setattr(
        webhook_email.crm_service,
        "sync",
        lambda lead, message: {"contact": {"id": "contact-1"}, "enrichment_note": {"id": "note-1"}},
    )

    response = asyncio.run(
        webhook_email.send_email(
            SendEmailRequest(company_name="Northstar Lending", contact_email="cto@northstar.example"),
        )
    )

    assert response.provider == "resend"
    assert response.status == "queued"
    assert response.crm_sync["contact"]["id"] == "contact-1"


def test_email_webhook_route_rejects_malformed_payload() -> None:
    try:
        asyncio.run(webhook_email.resend_events({"type": "email.replied"}))
    except HTTPException as exc:
        assert exc.status_code == 400
    else:
        raise AssertionError("Expected malformed email webhook to return 400")


def test_sms_webhook_route_processes_inbound_reply(monkeypatch) -> None:
    captured: list[InboundChannelEvent] = []
    router = ChannelEventRouter(log_path="/tmp/route-sms-events.jsonl")
    router.register(lambda event: captured.append(event) or {"accepted": True})
    monkeypatch.setattr(webhook_sms, "sms_handler", SMSHandler(client=FakeSMSClient(), event_router=router, log_path="/tmp/route-sms.jsonl"))

    response = asyncio.run(
        webhook_sms.africas_talking_events(
            {
                "id": "sms-1",
                "from": "+15551234567",
                "text": "Interested, send details",
                "company_name": "Northstar Lending",
            }
        )
    )

    assert response.status == "processed"
    assert response.routed_handlers == 1
    assert captured[0].phone_number == "+15551234567"


def test_booking_webhook_updates_crm_for_same_prospect(monkeypatch) -> None:
    fake_client = FakeHubSpotClient()
    monkeypatch.setattr(webhook_cal, "crm_service", CRMService(client=fake_client))

    response = asyncio.run(
        webhook_cal.booking_completed(
            BookingWebhookRequest(
                company_name="Northstar Lending",
                contact_email="cto@northstar.example",
                booking_id="booking-1",
                booking_url="https://cal.com/signalforge-discovery/booking-1",
                meeting_start="2026-04-24T15:00:00Z",
            )
        )
    )

    assert response["status"] == "processed"
    assert response["crm_sync"]["contact"]["id"] == "contact-1"
    assert any(call[0] == "create_note" for call in fake_client.calls)
