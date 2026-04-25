from __future__ import annotations

from agent.briefs.brief_schema import LeadRecord
from agent.channels.channel_schema import ChannelPolicyError, InboundChannelEvent, ProviderSendRequest, ProviderSendResult
from agent.channels.email.email_handler import EmailHandler
from agent.channels.sms.sms_handler import SMSHandler
from agent.channels.voice.voice_handler import VoiceHandler
from agent.core.models import LeadLifecycleState, LifecycleActivity
from agent.core.state_manager import ProspectStateStore


class ChannelOrchestrator:
    """Own the channel handoff policy in one place.

    Handlers should only talk to providers and parse provider payloads. They
    must not decide whether SMS is allowed or whether voice is the next step.
    """

    def __init__(
        self,
        *,
        email_handler: EmailHandler | None = None,
        sms_handler: SMSHandler | None = None,
        voice_handler: VoiceHandler | None = None,
        state_store: ProspectStateStore | None = None,
    ) -> None:
        self.email_handler = email_handler or EmailHandler()
        self.sms_handler = sms_handler or SMSHandler()
        self.voice_handler = voice_handler or VoiceHandler()
        self.state_store = state_store or ProspectStateStore()

    def hydrate_state(
        self,
        *,
        lead: LeadRecord,
        qualification_status: str,
        intent_level: str,
        next_action: str,
        booking_url: str | None = None,
    ) -> LeadLifecycleState:
        state = self.state_store.get(
            self.lead_key(lead.company_name, lead.contact_email, lead.phone_number),
            company_name=lead.company_name,
            contact_email=lead.contact_email,
            phone_number=lead.phone_number,
        )
        state.stage = "enriched" if state.stage == "new" else state.stage
        state.qualification_status = qualification_status
        state.intent_level = intent_level
        state.next_action = next_action
        state.booking_url = booking_url or state.booking_url
        return self.state_store.append_activity(
            state,
            LifecycleActivity(
                channel="system",
                direction="system",
                event_type="enrichment_completed",
                detail="Deterministic enrichment and routing completed.",
                provider="signalforge",
            ),
        )

    def send_email(self, *, lead: LeadRecord, request: ProviderSendRequest) -> tuple[ProviderSendResult, LeadLifecycleState]:
        state = self.state_store.get(
            self.lead_key(lead.company_name, lead.contact_email, lead.phone_number),
            company_name=lead.company_name,
            contact_email=lead.contact_email,
            phone_number=lead.phone_number,
        )
        result = self.email_handler.send(request)
        state.contact_email = lead.contact_email or state.contact_email
        if result.status in {"queued", "sent"}:
            state.stage = "email_sent"
        state = self.state_store.append_activity(
            state,
            LifecycleActivity(
                channel="email",
                direction="outbound",
                event_type=result.status,
                detail=result.detail,
                provider=result.provider,
                external_id=result.external_id,
            ),
        )
        return result, state

    def send_sms(self, *, lead: LeadRecord, request: ProviderSendRequest) -> tuple[ProviderSendResult, LeadLifecycleState]:
        state = self.state_store.get(
            self.lead_key(lead.company_name, lead.contact_email, lead.phone_number),
            company_name=lead.company_name,
            contact_email=lead.contact_email,
            phone_number=lead.phone_number,
        )
        if not state.sms_allowed:
            raise ChannelPolicyError("SMS warm follow-up requires a recorded email reply in lifecycle state.")
        result = self.sms_handler.send_warm_follow_up(request, prior_email_reply=True)
        if result.status in {"queued", "sent"}:
            state.stage = "sms_sent"
        state = self.state_store.append_activity(
            state,
            LifecycleActivity(
                channel="sms",
                direction="outbound",
                event_type=result.status,
                detail=result.detail,
                provider=result.provider,
                external_id=result.external_id,
            ),
        )
        return result, state

    def queue_voice(self, *, lead: LeadRecord, body: str) -> tuple[dict[str, str], LeadLifecycleState]:
        state = self.state_store.get(
            self.lead_key(lead.company_name, lead.contact_email, lead.phone_number),
            company_name=lead.company_name,
            contact_email=lead.contact_email,
            phone_number=lead.phone_number,
        )
        result = self.voice_handler.enqueue(lead.phone_number or lead.contact_email or lead.company_name, body)  # type: ignore[arg-type]
        state.stage = "voice_queued"
        state = self.state_store.append_activity(
            state,
            LifecycleActivity(
                channel="voice",
                direction="outbound",
                event_type="queued",
                detail="Voice escalation queued after prior channels.",
                provider="voice_stub",
            ),
        )
        return result, state

    def process_inbound_event(self, event: InboundChannelEvent) -> LeadLifecycleState:
        lead_key = self.lead_key(event.company_name or "unknown", event.contact_email, event.phone_number)
        state = self.state_store.get(
            lead_key,
            company_name=event.company_name or "unknown",
            contact_email=event.contact_email,
            phone_number=event.phone_number,
        )
        if event.channel == "email" and event.event_type == "reply":
            state.stage = "email_replied"
            state.email_reply_received = True
            state.next_action = "sms_or_booking_follow_up"
        elif event.channel == "sms" and event.event_type == "reply":
            state.stage = "sms_replied"
            state.sms_reply_received = True
            state.next_action = "voice_or_booking_follow_up"
        elif event.channel == "calendar" and event.event_type == "booking_completed":
            state.stage = "booked"
            state.booking_completed = True
            state.next_action = "crm_handoff"

        state.last_inbound_message = event.message_text or state.last_inbound_message
        return self.state_store.append_activity(
            state,
            LifecycleActivity(
                channel=event.channel,
                direction="inbound" if event.channel != "calendar" else "system",
                event_type=event.event_type,
                detail=event.message_text or event.event_type,
                provider=event.provider,
                external_id=event.external_id,
            ),
        )

    def allowed_next_channels(self, state: LeadLifecycleState) -> list[str]:
        if state.booking_completed:
            return []
        if state.sms_reply_received:
            return ["voice", "calendar"]
        if state.email_reply_received:
            return ["sms", "calendar"]
        if state.stage in {"new", "enriched"}:
            return ["email"]
        if state.stage == "email_sent":
            return ["email"]
        return ["calendar"]

    @staticmethod
    def lead_key(company_name: str, contact_email: str | None = None, phone_number: str | None = None) -> str:
        return "|".join([company_name.strip().lower(), (contact_email or "").strip().lower(), (phone_number or "").strip()])
