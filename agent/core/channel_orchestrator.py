from __future__ import annotations

from agent.briefs.brief_schema import LeadRecord
from agent.channels.channel_schema import ChannelPolicyError, InboundChannelEvent, ProviderSendRequest, ProviderSendResult
from agent.channels.email.email_handler import EmailHandler
from agent.channels.sms.sms_handler import SMSHandler
from agent.channels.voice.voice_handler import VoiceHandler
from agent.channels.whatsapp.whatsapp_handler import WhatsAppHandler
from agent.core.models import LeadLifecycleState, LifecycleActivity, LifecycleStage
from agent.core.state_manager import ProspectStateStore
from agent.utils.trace_logger import append_jsonl_log


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
        whatsapp_handler: WhatsAppHandler | None = None,
        voice_handler: VoiceHandler | None = None,
        state_store: ProspectStateStore | None = None,
    ) -> None:
        self.email_handler = email_handler or EmailHandler()
        self.sms_handler = sms_handler or SMSHandler()
        self.whatsapp_handler = whatsapp_handler or WhatsAppHandler()
        self.voice_handler = voice_handler or VoiceHandler()
        self.state_store = state_store or ProspectStateStore()

    def hydrate_state(
        self,
        *,
        lead: LeadRecord,
        qualification_status: str,
        intent_level: str,
        next_action: str,
        confidence_score: float = 0.0,
        booking_url: str | None = None,
    ) -> LeadLifecycleState:
        state = self.state_store.get(
            self.lead_key(lead.company_name, lead.contact_email, lead.phone_number),
            company_name=lead.company_name,
            contact_email=lead.contact_email,
            phone_number=lead.phone_number,
        )
        state.qualification_status = qualification_status
        state.intent_level = intent_level
        state.next_action = next_action
        state.confidence_score = confidence_score
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
            self._transition(state, LifecycleStage.EMAILED)
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
        append_jsonl_log(
            "logs/channel_decisions.jsonl",
            {
                "decision_type": "send_email",
                "lead_key": state.lead_key,
                "stage": state.stage.value,
                "provider_result": result.model_dump(),
                "allowed_next_channels": self.allowed_next_channels(state),
            },
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
            raise ChannelPolicyError("SMS warm follow-up requires a recorded email reply and confidence >= 0.6 in lifecycle state.")
        result = self.sms_handler.send_warm_follow_up(request, prior_email_reply=True)
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
        append_jsonl_log(
            "logs/channel_decisions.jsonl",
            {
                "decision_type": "send_sms",
                "lead_key": state.lead_key,
                "stage": state.stage.value,
                "provider_result": result.model_dump(),
                "allowed_next_channels": self.allowed_next_channels(state),
            },
        )
        return result, state

    def send_whatsapp(self, *, lead: LeadRecord, request: ProviderSendRequest) -> tuple[ProviderSendResult, LeadLifecycleState]:
        state = self.state_store.get(
            self.lead_key(lead.company_name, lead.contact_email, lead.phone_number),
            company_name=lead.company_name,
            contact_email=lead.contact_email,
            phone_number=lead.phone_number,
        )
        if not state.whatsapp_allowed:
            raise ChannelPolicyError("WhatsApp warm follow-up requires a recorded email reply and confidence >= 0.6 in lifecycle state.")
        result = self.whatsapp_handler.send_warm_follow_up(request, prior_email_reply=True)
        state = self.state_store.append_activity(
            state,
            LifecycleActivity(
                channel="whatsapp",
                direction="outbound",
                event_type=result.status,
                detail=result.detail,
                provider=result.provider,
                external_id=result.external_id,
            ),
        )
        append_jsonl_log(
            "logs/channel_decisions.jsonl",
            {
                "decision_type": "send_whatsapp",
                "lead_key": state.lead_key,
                "stage": state.stage.value,
                "provider_result": result.model_dump(),
                "allowed_next_channels": self.allowed_next_channels(state),
            },
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
        if self._is_duplicate_event(state, event):
            append_jsonl_log(
                "logs/channel_decisions.jsonl",
                {
                    "decision_type": "duplicate_inbound_ignored",
                    "lead_key": state.lead_key,
                    "stage": state.stage.value,
                    "event": event.model_dump(),
                },
            )
            return state
        if event.channel == "email" and event.event_type == "reply":
            self._transition(state, LifecycleStage.REPLIED)
            state.email_reply_received = True
            state.next_action = "sms_or_booking_follow_up"
        elif event.channel == "sms" and event.event_type == "reply":
            self._transition(state, LifecycleStage.REPLIED)
            state.sms_reply_received = True
            state.next_action = "voice_or_booking_follow_up"
        elif event.channel == "whatsapp" and event.event_type == "reply":
            self._transition(state, LifecycleStage.REPLIED)
            state.next_action = "voice_or_booking_follow_up"
        elif event.channel == "calendar" and event.event_type == "booking_completed":
            self._transition(state, LifecycleStage.BOOKED)
            state.booking_completed = True
            state.next_action = "crm_handoff"
        elif event.channel == "website" and event.event_type == "visit":
            state.website_visits_count += 1
            state.last_website_page = event.message_text
            state.last_website_visit_at = event.received_at
            if event.message_text and event.message_text.lower() in {"/pricing", "/demo", "/book", "/case-studies"}:
                state.next_action = "send_behavior_follow_up"

        state.last_inbound_message = event.message_text or state.last_inbound_message
        updated_state = self.state_store.append_activity(
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
        append_jsonl_log(
            "logs/channel_decisions.jsonl",
            {
                "decision_type": "process_inbound_event",
                "lead_key": updated_state.lead_key,
                "stage": updated_state.stage.value,
                "event": event.model_dump(),
                "allowed_next_channels": self.allowed_next_channels(updated_state),
            },
        )
        return updated_state

    def is_duplicate_event(self, event: InboundChannelEvent) -> bool:
        lead_key = self.lead_key(event.company_name or "unknown", event.contact_email, event.phone_number)
        state = self.state_store.get(
            lead_key,
            company_name=event.company_name or "unknown",
            contact_email=event.contact_email,
            phone_number=event.phone_number,
        )
        return self._is_duplicate_event(state, event)

    def record_qualification(
        self,
        *,
        lead: LeadRecord,
        qualification_status: str,
        intent_level: str,
        next_action: str,
        confidence_score: float,
    ) -> LeadLifecycleState:
        state = self.state_store.get(
            self.lead_key(lead.company_name, lead.contact_email, lead.phone_number),
            company_name=lead.company_name,
            contact_email=lead.contact_email,
            phone_number=lead.phone_number,
        )
        state.qualification_status = qualification_status
        state.intent_level = intent_level
        state.next_action = next_action
        state.confidence_score = confidence_score
        if qualification_status == "qualified":
            self._transition(state, LifecycleStage.QUALIFIED)
        return self.state_store.append_activity(
            state,
            LifecycleActivity(
                channel="system",
                direction="system",
                event_type="qualification_updated",
                detail=f"Qualification set to {qualification_status} with intent {intent_level}.",
                provider="signalforge",
            ),
        )

    def close_lead(self, *, lead: LeadRecord, reason: str) -> LeadLifecycleState:
        state = self.state_store.get(
            self.lead_key(lead.company_name, lead.contact_email, lead.phone_number),
            company_name=lead.company_name,
            contact_email=lead.contact_email,
            phone_number=lead.phone_number,
        )
        self._transition(state, LifecycleStage.CLOSED)
        state.next_action = reason
        return self.state_store.append_activity(
            state,
            LifecycleActivity(
                channel="system",
                direction="system",
                event_type="lead_closed",
                detail=reason,
                provider="signalforge",
            ),
        )

    def allowed_next_channels(self, state: LeadLifecycleState) -> list[str]:
        if state.stage in {LifecycleStage.BOOKED, LifecycleStage.CLOSED}:
            return []
        if state.stage == LifecycleStage.NEW:
            return ["email"]
        if state.stage == LifecycleStage.EMAILED:
            return ["email"]
        if state.stage == LifecycleStage.REPLIED:
            channels = ["calendar"] if state.booking_ready else ["email"]
            if state.sms_allowed:
                channels.append("sms")
                channels.append("whatsapp")
            return channels
        if state.stage == LifecycleStage.QUALIFIED:
            channels = ["calendar"]
            if state.sms_allowed:
                channels.extend(["sms", "whatsapp"])
            channels.append("voice")
            return list(dict.fromkeys(channels))
        return []

    @staticmethod
    def _is_duplicate_event(state: LeadLifecycleState, event: InboundChannelEvent) -> bool:
        if not event.external_id:
            return False
        return any(
            activity.external_id == event.external_id
            and activity.channel == event.channel
            and activity.event_type == event.event_type
            for activity in state.activities
        )

    @staticmethod
    def _transition(state: LeadLifecycleState, target_stage: LifecycleStage) -> None:
        stage_order = {
            LifecycleStage.NEW: 0,
            LifecycleStage.EMAILED: 1,
            LifecycleStage.REPLIED: 2,
            LifecycleStage.QUALIFIED: 3,
            LifecycleStage.BOOKED: 4,
            LifecycleStage.CLOSED: 5,
        }
        allowed_transitions = {
            LifecycleStage.NEW: {LifecycleStage.EMAILED, LifecycleStage.REPLIED, LifecycleStage.BOOKED, LifecycleStage.CLOSED},
            LifecycleStage.EMAILED: {LifecycleStage.REPLIED, LifecycleStage.BOOKED, LifecycleStage.CLOSED},
            LifecycleStage.REPLIED: {LifecycleStage.QUALIFIED, LifecycleStage.BOOKED, LifecycleStage.CLOSED},
            LifecycleStage.QUALIFIED: {LifecycleStage.BOOKED, LifecycleStage.CLOSED},
            LifecycleStage.BOOKED: {LifecycleStage.CLOSED},
            LifecycleStage.CLOSED: set(),
        }
        current = state.stage
        if current == target_stage:
            return
        if stage_order[current] > stage_order[target_stage]:
            return
        if target_stage not in allowed_transitions[current]:
            raise ChannelPolicyError(f"Invalid lifecycle transition: {current.value} -> {target_stage.value}")
        state.stage = target_stage

    @staticmethod
    def lead_key(company_name: str, contact_email: str | None = None, phone_number: str | None = None) -> str:
        return "|".join([company_name.strip().lower(), (contact_email or "").strip().lower(), (phone_number or "").strip()])
