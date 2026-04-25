from pathlib import Path

from agent.briefs.brief_schema import LeadRecord
from agent.channels.channel_schema import InboundChannelEvent, ProviderSendRequest, ProviderSendResult
from agent.channels.email.email_handler import EmailHandler
from agent.channels.sms.sms_handler import SMSHandler
from agent.core.channel_orchestrator import ChannelOrchestrator
from agent.core.models import LifecycleStage
from agent.core.state_manager import ProspectStateStore
from backend.services.conversation_service import ConversationService
from backend.services.crm_service import CRMService


class FakeEmailClient:
    def send(self, request: ProviderSendRequest) -> ProviderSendResult:
        return ProviderSendResult(
            channel="email",
            provider="resend",
            status="queued",
            destination=request.contact_email or "",
            external_id="email-e2e",
            detail="queued",
        )


class FakeSMSClient:
    def send(self, request: ProviderSendRequest) -> ProviderSendResult:
        return ProviderSendResult(
            channel="sms",
            provider="africas_talking",
            status="queued",
            destination=request.phone_number or "",
            external_id="sms-e2e",
            detail="queued",
        )


class FakeHubSpotClient:
    def __init__(self) -> None:
        self.upserts: list[dict[str, object]] = []
        self.updates: list[dict[str, object]] = []
        self.activities: list[dict[str, object]] = []

    def upsert_contact(self, *, email: str, properties: dict[str, object]) -> dict[str, object]:
        self.upserts.append({"email": email, "properties": properties})
        return {"id": "contact-e2e", "properties": properties}

    def update_contact_properties(self, *, contact_id: str, properties: dict[str, object]) -> dict[str, object]:
        self.updates.append({"contact_id": contact_id, "properties": properties})
        return {"status": "success", "id": contact_id}

    def create_activity(self, *, contact_id: str, subject: str, body: str, channel: str) -> dict[str, object]:
        self.activities.append(
            {"contact_id": contact_id, "subject": subject, "body": body, "channel": channel}
        )
        return {"id": f"activity-{len(self.activities)}"}


def test_end_to_end_flow(tmp_path) -> None:
    fake_hubspot = FakeHubSpotClient()
    crm_service = CRMService(client=fake_hubspot)
    state_store = ProspectStateStore(path=str(tmp_path / "prospect_state.json"))
    channel_orchestrator = ChannelOrchestrator(
        email_handler=EmailHandler(client=FakeEmailClient(), log_path=str(tmp_path / "email.jsonl")),
        sms_handler=SMSHandler(client=FakeSMSClient(), log_path=str(tmp_path / "sms.jsonl")),
        state_store=state_store,
    )
    service = ConversationService(crm_service=crm_service, channel_orchestrator=channel_orchestrator)

    lead = LeadRecord(
        company_name="Northstar Lending",
        contact_email="cto@northstar.example",
        contact_name="Maya",
        phone_number="+15551234567",
    )

    send_result, crm_sync, drafted = service.send_email(lead=lead)

    assert send_result.status == "queued"
    assert drafted.crm_fields.ai_maturity >= 0
    assert crm_sync["contact"]["id"] == "contact-e2e"
    assert fake_hubspot.updates[-1]["properties"]["signalforge_stage"] == "EMAILED"

    inbound_response = service.handle_inbound_event(
        InboundChannelEvent(
            channel="email",
            provider="resend",
            event_type="reply",
            company_name=lead.company_name,
            contact_email=lead.contact_email,
            phone_number=lead.phone_number,
            message_text=(
                "Yes, that's directionally right. We're adding AI operations capacity this quarter "
                "and would be open to a 20-minute call next week."
            ),
        )
    )
    inbound_state = service.channel_orchestrator.state_store.get(
        service.channel_orchestrator.lead_key(lead.company_name, lead.contact_email, lead.phone_number),
        company_name=lead.company_name,
        contact_email=lead.contact_email,
        phone_number=lead.phone_number,
    )

    assert inbound_response["lifecycle_stage"] == "QUALIFIED"
    assert inbound_state.stage == LifecycleStage.QUALIFIED
    assert inbound_state.booking_url

    sms_result, sms_crm_sync = service.send_warm_sms(
        lead=lead,
        body="Thanks for the reply. Here is the shortest next step.",
    )

    assert sms_result.status == "queued"
    assert fake_hubspot.updates[-1]["properties"]["signalforge_stage"] == "QUALIFIED"
    assert "booking_url" in sms_crm_sync["activity_log"]["id"] or sms_crm_sync["activity_log"]["id"].startswith("activity-")

    booked_state = service.channel_orchestrator.process_inbound_event(
        InboundChannelEvent(
            channel="calendar",
            provider="calcom",
            event_type="booking_completed",
            company_name=lead.company_name,
            contact_email=lead.contact_email,
            phone_number=lead.phone_number,
            message_text=inbound_state.booking_url,
            external_id="booking-e2e",
        )
    )
    booking_sync = crm_service.sync_booking_completed(
        contact_email=lead.contact_email,
        company_name=lead.company_name,
        booking_id="booking-e2e",
        booking_url=inbound_state.booking_url or "",
        meeting_start="2026-04-24T15:00:00Z",
    )

    assert booked_state.stage == LifecycleStage.BOOKED
    assert booking_sync["contact"]["id"] == "contact-e2e"
    assert any(activity["channel"] == "email" for activity in fake_hubspot.activities)
    assert any(activity["channel"] == "sms" for activity in fake_hubspot.activities)
    assert any(activity["channel"] == "calendar" for activity in fake_hubspot.activities)
    assert any(
        "signalforge_signal_confidence" in update["properties"]
        for update in fake_hubspot.updates
    )
    assert any(
        update["properties"].get("signalforge_booking_url")
        for update in fake_hubspot.updates
    )
