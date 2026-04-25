import asyncio

from agent.briefs.brief_schema import LeadRecord
from agent.channels.channel_schema import InboundChannelEvent, ProviderSendRequest, ProviderSendResult
from agent.channels.email.email_handler import EmailHandler
from agent.channels.sms.sms_handler import SMSHandler
from agent.channels.whatsapp.whatsapp_handler import WhatsAppHandler
from agent.core.channel_orchestrator import ChannelOrchestrator
from agent.core.models import LeadLifecycleState, LifecycleStage
from agent.core.state_manager import ProspectStateStore
from agent.signals.hiring_signals import build_hiring_signal_brief
from agent.tools.crunchbase_tool import CrunchbaseTool
from backend.routes import webhook_cal, webhook_email, webhook_sms, webhook_website, webhook_whatsapp
from backend.schemas import (
    BookingWebhookRequest,
    SendEmailRequest,
    SendWarmSmsRequest,
    SendWarmWhatsAppRequest,
    WebsiteVisitRequest,
)
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

    def update_contact_properties(self, *, contact_id: str, properties: dict[str, object]) -> dict[str, object]:
        self.calls.append(("update_contact_properties", {"contact_id": contact_id, **properties}))
        return {"status": "success", "id": contact_id}

    def create_activity(self, *, contact_id: str, subject: str, body: str, channel: str) -> dict[str, object]:
        self.calls.append(
            ("create_activity", {"contact_id": contact_id, "subject": subject, "body": body, "channel": channel})
        )
        return {"id": "note-1", "contact_id": contact_id}


class FallbackHubSpotClient(FakeHubSpotClient):
    def update_contact_properties(self, *, contact_id: str, properties: dict[str, object]) -> dict[str, object]:
        self.calls.append(("update_contact_properties", {"contact_id": contact_id, **properties}))
        return {
            "status": "failed",
            "error": "http_400",
            "path": f"/crm/v3/objects/contacts/{contact_id}",
            "response": {"category": "VALIDATION_ERROR"},
        }


def test_hiring_signal_brief_merges_required_sources() -> None:
    brief = build_hiring_signal_brief("Northstar Lending", CrunchbaseTool())

    signal_names = {signal["signal"] for signal in brief["signals"]}
    checked_sources = {source["source"] for source in brief["data_sources_checked"]}
    assert {"funding_event", "job_post_scrape", "job_post_velocity", "layoffs", "leadership_change"} <= signal_names
    assert {"crunchbase_odm", "layoffs_fyi", "company_careers_page", "builtin", "wellfound", "linkedin_public"} <= checked_sources
    assert brief["hiring_velocity"]["delta"] == 9
    assert brief["ai_maturity"]["score"] >= 1


def test_email_handler_routes_inbound_replies_to_stateful_service() -> None:
    captured: list[InboundChannelEvent] = []
    handler = EmailHandler(client=FakeEmailClient(), log_path="/tmp/test-email-handler.jsonl")
    handler.register_inbound_handler(lambda event: captured.append(event) or {"accepted": True})

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


def test_duplicate_inbound_event_is_idempotent(tmp_path) -> None:
    store = ProspectStateStore(path=str(tmp_path / "state.json"))
    orchestrator = ChannelOrchestrator(
        email_handler=EmailHandler(client=FakeEmailClient(), log_path=str(tmp_path / "email.jsonl")),
        sms_handler=SMSHandler(client=FakeSMSClient(), log_path=str(tmp_path / "sms.jsonl")),
        state_store=store,
    )
    lead = LeadRecord(company_name="Northstar Lending", contact_email="cto@northstar.example", phone_number="+15551234567")
    orchestrator.send_email(
        lead=lead,
        request=ProviderSendRequest(company_name=lead.company_name, contact_email=lead.contact_email, body="hello"),
    )
    event = InboundChannelEvent(
        channel="email",
        provider="resend",
        event_type="reply",
        company_name=lead.company_name,
        contact_email=lead.contact_email,
        phone_number=lead.phone_number,
        message_text="Interested",
        external_id="evt-duplicate-1",
    )

    first = orchestrator.process_inbound_event(event)
    second = orchestrator.process_inbound_event(event)

    assert first.stage == LifecycleStage.REPLIED
    assert second.stage == LifecycleStage.REPLIED
    matching = [
        activity for activity in second.activities
        if activity.channel == "email" and activity.event_type == "reply" and activity.external_id == "evt-duplicate-1"
    ]
    assert len(matching) == 1


def test_channel_orchestrator_enforces_sms_gate_from_state(tmp_path) -> None:
    store = ProspectStateStore(path=str(tmp_path / "state.json"))
    orchestrator = ChannelOrchestrator(
        email_handler=EmailHandler(client=FakeEmailClient(), log_path=str(tmp_path / "email.jsonl")),
        sms_handler=SMSHandler(client=FakeSMSClient(), log_path=str(tmp_path / "sms.jsonl")),
        state_store=store,
    )
    lead = LeadRecord(company_name="Northstar Lending", contact_email="cto@northstar.example", phone_number="+15551234567")

    try:
        orchestrator.send_sms(
            lead=lead,
            request=ProviderSendRequest(company_name=lead.company_name, phone_number=lead.phone_number, body="Follow up"),
        )
    except Exception as exc:  # noqa: BLE001
        assert "recorded email reply" in str(exc)
    else:
        raise AssertionError("Expected SMS gate to block send without email reply")

    state = store.get(
        orchestrator.lead_key(lead.company_name, lead.contact_email, lead.phone_number),
        company_name=lead.company_name,
        contact_email=lead.contact_email,
        phone_number=lead.phone_number,
    )
    state.email_reply_received = True
    state.confidence_score = 0.72
    state.stage = LifecycleStage.REPLIED
    store.save(state)
    result, updated_state = orchestrator.send_sms(
        lead=lead,
        request=ProviderSendRequest(company_name=lead.company_name, phone_number=lead.phone_number, body="Follow up"),
    )

    assert result.status == "queued"
    assert updated_state.stage == LifecycleStage.REPLIED


def test_email_send_route_syncs_to_crm(monkeypatch, tmp_path) -> None:
    fake_client = FakeHubSpotClient()
    service = webhook_email.conversation_service
    service.crm_service = CRMService(client=fake_client)
    service.channel_orchestrator = ChannelOrchestrator(
        email_handler=EmailHandler(client=FakeEmailClient(), log_path=str(tmp_path / "route-email.jsonl")),
        sms_handler=SMSHandler(client=FakeSMSClient(), log_path=str(tmp_path / "route-sms.jsonl")),
        state_store=ProspectStateStore(path=str(tmp_path / "state.json")),
    )
    webhook_email.email_handler = service.channel_orchestrator.email_handler
    webhook_email.email_handler.register_inbound_handler(service.handle_inbound_event)

    response = asyncio.run(
        webhook_email.send_email(
            SendEmailRequest(company_name="Northstar Lending", contact_email="cto@northstar.example"),
        )
    )

    assert response.provider == "resend"
    assert response.status == "queued"
    assert response.crm_sync["contact"]["id"] == "contact-1"
    assert any(call[0] == "create_activity" for call in fake_client.calls)


def test_route_level_email_reply_unblocks_sms_handoff(tmp_path) -> None:
    fake_client = FakeHubSpotClient()
    shared_orchestrator = ChannelOrchestrator(
        email_handler=EmailHandler(client=FakeEmailClient(), log_path=str(tmp_path / "route-email.jsonl")),
        sms_handler=SMSHandler(client=FakeSMSClient(), log_path=str(tmp_path / "route-sms.jsonl")),
        state_store=ProspectStateStore(path=str(tmp_path / "state.json")),
    )
    shared_crm = CRMService(client=fake_client)

    webhook_email.conversation_service.crm_service = shared_crm
    webhook_email.conversation_service.channel_orchestrator = shared_orchestrator
    webhook_email.email_handler = shared_orchestrator.email_handler
    webhook_email.email_handler.register_inbound_handler(webhook_email.conversation_service.handle_inbound_event)

    webhook_sms.conversation_service.crm_service = shared_crm
    webhook_sms.conversation_service.channel_orchestrator = shared_orchestrator
    webhook_sms.sms_handler = shared_orchestrator.sms_handler
    webhook_sms.sms_handler.register_inbound_handler(webhook_sms.conversation_service.handle_inbound_event)

    send_response = asyncio.run(
        webhook_email.send_email(
            SendEmailRequest(
                company_name="Northstar Lending",
                contact_email="cto@northstar.example",
                contact_name="Maya",
                phone_number="+15551234567",
            )
        )
    )
    reply_response = asyncio.run(
        webhook_email.resend_events(
            {
                "type": "email.reply_received",
                "data": {
                    "id": "evt-1",
                    "email_id": "email-123",
                    "to": "cto@northstar.example",
                    "text": "Yes, send the link.",
                    "tags": [{"name": "company_name", "value": "Northstar Lending"}],
                },
            }
        )
    )
    sms_response = asyncio.run(
        webhook_sms.send_warm_sms(
            SendWarmSmsRequest(
                company_name="Northstar Lending",
                contact_email="cto@northstar.example",
                phone_number="+15551234567",
                body="Thanks for the reply. Here is the shortest next step.",
            )
        )
    )

    assert send_response.status == "queued"
    assert reply_response.event_type == "reply"
    assert reply_response.routed_handlers == 1
    assert sms_response.status == "queued"
    assert sms_response.provider == "africas_talking"


def test_route_level_email_reply_unblocks_whatsapp_handoff(tmp_path) -> None:
    fake_client = FakeHubSpotClient()
    shared_orchestrator = ChannelOrchestrator(
        email_handler=EmailHandler(client=FakeEmailClient(), log_path=str(tmp_path / "route-email.jsonl")),
        sms_handler=SMSHandler(client=FakeSMSClient(), log_path=str(tmp_path / "route-sms.jsonl")),
        whatsapp_handler=WhatsAppHandler(log_path=str(tmp_path / "route-whatsapp.jsonl")),
        state_store=ProspectStateStore(path=str(tmp_path / "state.json")),
    )
    shared_crm = CRMService(client=fake_client)

    webhook_email.conversation_service.crm_service = shared_crm
    webhook_email.conversation_service.channel_orchestrator = shared_orchestrator
    webhook_email.email_handler = shared_orchestrator.email_handler
    webhook_email.email_handler.register_inbound_handler(webhook_email.conversation_service.handle_inbound_event)

    webhook_whatsapp.conversation_service.crm_service = shared_crm
    webhook_whatsapp.conversation_service.channel_orchestrator = shared_orchestrator
    webhook_whatsapp.whatsapp_handler = shared_orchestrator.whatsapp_handler
    webhook_whatsapp.whatsapp_handler.register_inbound_handler(webhook_whatsapp.conversation_service.handle_inbound_event)

    asyncio.run(
        webhook_email.send_email(
            SendEmailRequest(
                company_name="Northstar Lending",
                contact_email="cto@northstar.example",
                contact_name="Maya",
                phone_number="+15551234567",
            )
        )
    )
    asyncio.run(
        webhook_email.resend_events(
            {
                "type": "email.reply_received",
                "data": {
                    "id": "evt-1",
                    "email_id": "email-123",
                    "to": "cto@northstar.example",
                    "text": "Yes, send the link.",
                    "tags": [{"name": "company_name", "value": "Northstar Lending"}],
                },
            }
        )
    )
    whatsapp_response = asyncio.run(
        webhook_whatsapp.send_warm_whatsapp(
            SendWarmWhatsAppRequest(
                company_name="Northstar Lending",
                contact_email="cto@northstar.example",
                phone_number="+15551234567",
                body="Thanks for the reply. Happy to share the short next step here.",
            )
        )
    )

    assert whatsapp_response.status == "queued"
    assert whatsapp_response.provider == "whatsapp_stub"


def test_crm_service_logs_fallback_note_when_custom_fields_unavailable() -> None:
    fake_client = FallbackHubSpotClient()
    crm_service = CRMService(client=fake_client)

    result = crm_service.sync_booking_completed(
        contact_email="cto@northstar.example",
        company_name="Northstar Lending",
        booking_id="booking-1",
        booking_url="https://cal.com/signalforge-discovery/booking-1",
        meeting_start="2026-04-24T15:00:00Z",
    )

    assert result["contact"]["id"] == "contact-1"
    assert result["enrichment_fields"]["status"] == "fallback_logged"
    assert result["enrichment_fields"]["fallback_note"]["id"] == "note-1"
    assert any(
        call[0] == "create_activity" and call[1]["subject"] == "signalforge_booking_fields"
        for call in fake_client.calls
    )


def test_sms_webhook_route_processes_inbound_reply(monkeypatch, tmp_path) -> None:
    service = webhook_sms.conversation_service
    service.channel_orchestrator = ChannelOrchestrator(
        email_handler=EmailHandler(client=FakeEmailClient(), log_path=str(tmp_path / "email.jsonl")),
        sms_handler=SMSHandler(client=FakeSMSClient(), log_path=str(tmp_path / "sms.jsonl")),
        state_store=ProspectStateStore(path=str(tmp_path / "state.json")),
    )
    webhook_sms.sms_handler = service.channel_orchestrator.sms_handler
    webhook_sms.sms_handler.register_inbound_handler(service.handle_inbound_event)

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


def test_website_visit_route_records_behavioral_signal(tmp_path) -> None:
    fake_client = FakeHubSpotClient()
    shared_orchestrator = ChannelOrchestrator(
        email_handler=EmailHandler(client=FakeEmailClient(), log_path=str(tmp_path / "email.jsonl")),
        sms_handler=SMSHandler(client=FakeSMSClient(), log_path=str(tmp_path / "sms.jsonl")),
        state_store=ProspectStateStore(path=str(tmp_path / "state.json")),
    )
    webhook_website.conversation_service.crm_service = CRMService(client=fake_client)
    webhook_website.conversation_service.channel_orchestrator = shared_orchestrator
    webhook_website.website_signal_store = webhook_website.WebsiteSignalStore(path=str(tmp_path / "website_visits.jsonl"))

    response = asyncio.run(
        webhook_website.record_website_visit(
            WebsiteVisitRequest(
                company="Northstar Lending",
                contact_email="cto@northstar.example",
                page_visited="/pricing",
                timestamp="2026-04-25T12:30:00Z",
            )
        )
    )

    assert response.status == "processed"
    assert response.follow_up_recommended is True
    assert response.lifecycle_stage == "NEW"
    assert any(call[0] == "create_activity" and call[1]["channel"] == "website" for call in fake_client.calls)


def test_booking_webhook_updates_crm_and_lifecycle(monkeypatch, tmp_path) -> None:
    fake_client = FakeHubSpotClient()
    webhook_cal.crm_service = CRMService(client=fake_client)
    webhook_cal.conversation_service.crm_service = webhook_cal.crm_service
    webhook_cal.conversation_service.channel_orchestrator = ChannelOrchestrator(
        state_store=ProspectStateStore(path=str(tmp_path / "state.json"))
    )

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
    assert response["lifecycle_stage"] == "BOOKED"
