from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from agent.briefs.brief_schema import LeadRecord
from agent.channels.channel_schema import InboundChannelEvent, ProviderSendRequest, ProviderSendResult
from agent.channels.email.email_handler import EmailHandler
from agent.channels.sms.sms_handler import SMSHandler
from agent.core.channel_orchestrator import ChannelOrchestrator
from agent.core.state_manager import ProspectStateStore
from backend.services.conversation_service import ConversationService
from backend.services.crm_service import CRMService
from eval.adversarial_cases import get_adversarial_case


class DemoEmailClient:
    def __init__(self, session_id: str) -> None:
        self.session_id = session_id

    def send(self, request: ProviderSendRequest) -> ProviderSendResult:
        return ProviderSendResult(
            channel="email",
            provider="resend",
            status="queued",
            destination=request.contact_email or "",
            external_id=f"demo-email-{self.session_id}",
            detail="Synthetic Resend send accepted for demo flow.",
            raw_response={
                "session_id": self.session_id,
                "intended_contact_email": request.contact_email,
                "message": "offline demo flow",
            },
        )


class DemoSMSClient:
    def __init__(self, session_id: str) -> None:
        self.session_id = session_id

    def send(self, request: ProviderSendRequest) -> ProviderSendResult:
        return ProviderSendResult(
            channel="sms",
            provider="africas_talking",
            status="queued",
            destination=request.phone_number or "",
            external_id=f"demo-sms-{self.session_id}",
            detail="Synthetic Africa's Talking send accepted for demo flow.",
            raw_response={"session_id": self.session_id, "message": "offline demo flow"},
        )


class DemoHubSpotClient:
    def __init__(self, session_id: str, session_started_at: str) -> None:
        self.session_id = session_id
        self.session_started_at = session_started_at
        self.contact_id = f"demo-contact-{session_id}"
        self.contact_properties: dict[str, object] = {}
        self.activities: list[dict[str, object]] = []

    def upsert_contact(self, *, email: str, properties: dict[str, object]) -> dict[str, object]:
        self.contact_properties.update(properties)
        self.contact_properties["email"] = email
        return {
            "id": self.contact_id,
            "status": "success",
            "properties": dict(self.contact_properties),
            "updatedAt": self.session_started_at,
        }

    def update_contact_properties(self, *, contact_id: str, properties: dict[str, object]) -> dict[str, object]:
        self.contact_properties.update(properties)
        return {
            "id": contact_id,
            "status": "success",
            "properties": dict(self.contact_properties),
            "updatedAt": datetime.now(UTC).isoformat(),
        }

    def create_activity(self, *, contact_id: str, subject: str, body: str, channel: str) -> dict[str, object]:
        activity = {
            "id": f"demo-activity-{len(self.activities) + 1}",
            "contact_id": contact_id,
            "subject": subject,
            "body": body,
            "channel": channel,
            "recorded_at": datetime.now(UTC).isoformat(),
        }
        self.activities.append(activity)
        return activity


class DemoFlowService:
    def __init__(self, repo_root: Path | None = None) -> None:
        self.repo_root = repo_root or Path(__file__).resolve().parents[2]

    def run(
        self,
        *,
        company_name: str | None = None,
        reply_text: str | None = None,
        scenario_name: str | None = None,
    ) -> dict[str, object]:
        session_started_at = datetime.now(UTC)
        session_id = session_started_at.strftime("%Y%m%d%H%M%S")
        selected_company, selected_reply = self._resolve_inputs(
            company_name=company_name,
            reply_text=reply_text,
            scenario_name=scenario_name,
        )
        lead = self._lead_for_company(selected_company)

        demo_hubspot = DemoHubSpotClient(session_id=session_id, session_started_at=session_started_at.isoformat())
        crm_service = CRMService(client=demo_hubspot)
        state_store = ProspectStateStore(path=str(self.repo_root / "outputs" / f"demo_state_{session_id}.json"))
        orchestrator = ChannelOrchestrator(
            email_handler=EmailHandler(
                client=DemoEmailClient(session_id=session_id),
                log_path=str(self.repo_root / "logs" / f"demo_email_{session_id}.jsonl"),
            ),
            sms_handler=SMSHandler(
                client=DemoSMSClient(session_id=session_id),
                log_path=str(self.repo_root / "logs" / f"demo_sms_{session_id}.jsonl"),
            ),
            state_store=state_store,
        )
        conversation_service = ConversationService(crm_service=crm_service, channel_orchestrator=orchestrator)

        send_result, crm_sync, drafted = conversation_service.send_email(lead=lead)
        reply_state = conversation_service.channel_orchestrator.process_inbound_event(
            InboundChannelEvent(
                channel="email",
                provider="resend",
                event_type="reply",
                company_name=lead.company_name,
                contact_email=lead.contact_email,
                phone_number=lead.phone_number,
                message_text=selected_reply,
                external_id=f"demo-reply-{session_id}",
            )
        )
        reply_crm_sync = crm_service.sync_inbound_event(
            lead=lead,
            lifecycle_state=reply_state,
            event=InboundChannelEvent(
                channel="email",
                provider="resend",
                event_type="reply",
                company_name=lead.company_name,
                contact_email=lead.contact_email,
                phone_number=lead.phone_number,
                message_text=selected_reply,
                external_id=f"demo-reply-{session_id}",
            ),
        )

        sms_body = (
            "Thanks for the quick reply. I pulled a short discovery step so we can compare "
            "AI operations capacity, bench fit, and the next hiring window."
        )
        sms_result, sms_crm_sync = conversation_service.send_warm_sms(lead=lead, body=sms_body)

        meeting_start = self._meeting_start(session_started_at)
        booked_state = conversation_service.channel_orchestrator.process_inbound_event(
            InboundChannelEvent(
                channel="calendar",
                provider="calcom",
                event_type="booking_completed",
                company_name=lead.company_name,
                contact_email=lead.contact_email,
                phone_number=lead.phone_number,
                message_text=reply_state.booking_url,
                external_id=f"demo-booking-{session_id}",
            )
        )
        booking_sync = crm_service.sync_booking_completed(
            contact_email=lead.contact_email or "",
            company_name=lead.company_name,
            booking_id=f"demo-booking-{session_id}",
            booking_url=reply_state.booking_url or "",
            meeting_start=meeting_start,
        )

        qualification = {
            "qualification_status": reply_state.qualification_status,
            "intent_level": reply_state.intent_level,
            "next_action": reply_state.next_action,
            "allowed_next_channels_after_reply": orchestrator.allowed_next_channels(reply_state),
        }

        lifecycle_state = state_store.get(
            orchestrator.lead_key(lead.company_name, lead.contact_email, lead.phone_number),
            company_name=lead.company_name,
            contact_email=lead.contact_email,
            phone_number=lead.phone_number,
        )
        return {
            "session_id": session_id,
            "session_started_at": session_started_at.isoformat(),
            "prospect_identity": {
                "company_name": lead.company_name,
                "contact_name": lead.contact_name,
                "contact_email": lead.contact_email,
                "phone_number": lead.phone_number,
                "conversation_id": lifecycle_state.lead_key,
            },
            "qualification": qualification,
            "email_send": {
                **send_result.model_dump(),
                "subject": "Signal-grounded outreach",
                "body": drafted.body,
                "crm_contact_id": crm_sync.get("contact", {}).get("id"),
            },
            "reply_event": {
                "channel": "email",
                "provider": "resend",
                "event_type": "reply",
                "message_text": selected_reply,
                "allowed_next_channels": orchestrator.allowed_next_channels(reply_state),
                "crm_activity_id": reply_crm_sync.get("activity_log", {}).get("id"),
            },
            "sms_follow_up": {
                **sms_result.model_dump(),
                "body": sms_body if reply_state.booking_url in sms_body else f"{sms_body} Book here if useful: {reply_state.booking_url}",
                "crm_activity_id": sms_crm_sync.get("activity_log", {}).get("id"),
            },
            "lifecycle": {
                "current_stage": booked_state.stage,
                "booking_completed": booked_state.booking_completed,
                "allowed_next_channels": orchestrator.allowed_next_channels(booked_state),
                "activities": [activity.model_dump() for activity in booked_state.activities],
            },
            "hubspot_record": self._hubspot_record_snapshot(
                lead=lead,
                crm_properties=demo_hubspot.contact_properties,
                crm_activities=demo_hubspot.activities,
                crm_contact_id=demo_hubspot.contact_id,
            ),
            "calcom_booking": {
                "booking_id": f"demo-booking-{session_id}",
                "booking_url": reply_state.booking_url,
                "event_type": "Tenacious discovery call with delivery lead",
                "attendee_name": lead.contact_name,
                "attendee_email": lead.contact_email,
                "confirmed_at": datetime.now(UTC).isoformat(),
                "meeting_start": meeting_start,
                "booking_note_id": booking_sync.get("booking_note", {}).get("id"),
            },
            "crm_sync": {
                "email_send": crm_sync,
                "reply": reply_crm_sync,
                "sms_follow_up": sms_crm_sync,
                "booking": booking_sync,
            },
        }

    @staticmethod
    def _resolve_inputs(
        *,
        company_name: str | None,
        reply_text: str | None,
        scenario_name: str | None,
    ) -> tuple[str, str]:
        if scenario_name:
            scenario = get_adversarial_case(scenario_name)
            if scenario is None:
                raise ValueError(f"Unknown scenario: {scenario_name}")
            return (
                str(scenario["company_name"]),
                reply_text or str(scenario["reply_text"]),
            )
        return company_name or "Northstar Lending", reply_text or (
            "Yes, that's directionally right. We're adding AI operations capacity this quarter "
            "and would be open to a 20-minute call next week."
        )

    @staticmethod
    def _lead_for_company(company_name: str) -> LeadRecord:
        slug = company_name.strip().lower().replace(" ", ".")
        return LeadRecord(
            company_name=company_name,
            contact_name="Jordan Avery",
            contact_email=f"{slug}@example.com",
            phone_number="+15551234567",
        )

    @staticmethod
    def _meeting_start(session_started_at: datetime) -> str:
        base = session_started_at + timedelta(days=3)
        meeting_start = base.replace(hour=15, minute=0, second=0, microsecond=0)
        return meeting_start.isoformat()

    @staticmethod
    def _hubspot_record_snapshot(
        *,
        lead: LeadRecord,
        crm_properties: dict[str, object],
        crm_activities: list[dict[str, object]],
        crm_contact_id: str,
    ) -> dict[str, object]:
        properties = {
            "email": lead.contact_email,
            "firstname": lead.contact_name,
            "company": lead.company_name,
            "industry": crm_properties.get("industry") or "Fintech",
            "signalforge_company_size": crm_properties.get("signalforge_company_size") or 240,
            "signalforge_last_funding_round": crm_properties.get("signalforge_last_funding_round") or "Series B",
            "signalforge_funding_date": crm_properties.get("signalforge_funding_date") or "2026-02-14",
            "signalforge_job_posts_current": crm_properties.get("signalforge_job_posts_current") or 12,
            "signalforge_job_posts_60d_ago": crm_properties.get("signalforge_job_posts_60d_ago") or 3,
            "signalforge_recent_layoffs": crm_properties.get("signalforge_recent_layoffs") or 18,
            "signalforge_recent_layoff_date": crm_properties.get("signalforge_recent_layoff_date") or "2025-12-10",
            "signalforge_recent_leadership_change": crm_properties.get("signalforge_recent_leadership_change") or "vp_engineering",
            "signalforge_recent_leadership_date": crm_properties.get("signalforge_recent_leadership_date") or "2026-03-10",
            "signalforge_ai_maturity": crm_properties.get("signalforge_ai_maturity") or 2,
            "signalforge_ai_maturity_confidence": crm_properties.get("signalforge_ai_maturity_confidence") or 0.58,
            "signalforge_signal_confidence": crm_properties.get("signalforge_signal_confidence") or 0.79,
            "signalforge_intent_level": crm_properties.get("signalforge_intent_level") or "high",
            "signalforge_qualification_status": crm_properties.get("signalforge_qualification_status") or "qualified",
            "signalforge_next_action": crm_properties.get("signalforge_next_action") or "share_booking_link",
            "signalforge_stage": crm_properties.get("signalforge_stage") or "booked",
            "signalforge_booking_url": crm_properties.get("signalforge_booking_url") or "",
            "signalforge_booking_event_type": crm_properties.get("signalforge_booking_event_type") or "Tenacious discovery call",
            "signalforge_last_booking_start": crm_properties.get("signalforge_last_booking_start") or "",
            "signalforge_last_event_at": crm_properties.get("signalforge_last_event_at") or "",
        }
        return {
            "contact_id": crm_contact_id,
            "properties": properties,
            "activities": crm_activities,
        }
