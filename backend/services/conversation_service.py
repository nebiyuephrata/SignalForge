from __future__ import annotations

from agent.briefs.brief_schema import CRMFields, LeadRecord, OutboundMessage
from agent.channels.channel_schema import InboundChannelEvent, ProviderSendRequest, ProviderSendResult
from agent.core.channel_orchestrator import ChannelOrchestrator
from agent.core.orchestrator import SignalForgeOrchestrator
from agent.utils.trace_logger import append_jsonl_log
from backend.services.crm_service import CRMService


class ConversationService:
    def __init__(self, crm_service: CRMService | None = None, channel_orchestrator: ChannelOrchestrator | None = None) -> None:
        self.orchestrator = SignalForgeOrchestrator()
        self.crm_service = crm_service or CRMService()
        self.channel_orchestrator = channel_orchestrator or ChannelOrchestrator()

    def draft_outreach(self, lead: LeadRecord) -> OutboundMessage:
        result = self.orchestrator.run_single_prospect(
            company_name=lead.company_name,
            reply_text=lead.last_email_reply_text,
            contact_email=lead.contact_email,
        )
        return self._draft_outreach_from_result(lead=lead, result=result)

    def _draft_outreach_from_result(self, *, lead: LeadRecord, result: dict[str, object]) -> OutboundMessage:
        qualification = result["qualification"]
        self.channel_orchestrator.hydrate_state(
            lead=lead,
            qualification_status=str(qualification["qualification_status"]),
            intent_level=str(qualification["intent_level"]),
            next_action=str(qualification["next_action"]),
            confidence_score=float(result["confidence_assessment"]["numeric_score"]),
            booking_url=result["booking"]["booking_url"],
        )
        crm_fields = CRMFields(
            icp_segment=self._derive_icp_segment(result),
            signal_confidence=float(result["confidence_assessment"]["numeric_score"]),
            ai_maturity=int(result["hiring_signal_brief"]["ai_maturity"]["score"]),
            intent_level=str(qualification["intent_level"]),
            qualification_status=str(qualification["qualification_status"]),
            next_action=str(qualification["next_action"]),
        )
        return OutboundMessage(channel="email", body=str(result["email"]["body"]), crm_fields=crm_fields)

    def send_email(
        self,
        *,
        lead: LeadRecord,
        subject: str | None = None,
        body: str | None = None,
    ) -> tuple[ProviderSendResult, dict[str, object], OutboundMessage]:
        result = self.orchestrator.run_single_prospect(
            company_name=lead.company_name,
            reply_text=lead.last_email_reply_text,
            contact_email=lead.contact_email,
        )
        drafted = self._draft_outreach_from_result(lead=lead, result=result)
        provider_request = ProviderSendRequest(
            company_name=lead.company_name,
            contact_email=lead.contact_email,
            contact_name=lead.contact_name,
            subject=subject or result["email"]["subject"],
            body=body or result["email"]["body"],
            metadata={
                "channel": "email",
                "booking_url": result["booking"]["booking_url"],
            },
        )
        send_result, state = self.channel_orchestrator.send_email(lead=lead, request=provider_request)
        crm_sync = self.crm_service.sync_lifecycle(
            lead=lead,
            run_result=result,
            outbound_message=drafted,
            lifecycle_state=state,
            lifecycle_event="email_sent",
        )
        return send_result, crm_sync, drafted

    def send_warm_sms(
        self,
        *,
        lead: LeadRecord,
        body: str,
    ) -> tuple[ProviderSendResult, dict[str, object]]:
        state = self.channel_orchestrator.state_store.get(
            self.channel_orchestrator.lead_key(lead.company_name, lead.contact_email, lead.phone_number),
            company_name=lead.company_name,
            contact_email=lead.contact_email,
            phone_number=lead.phone_number,
        )
        sms_body = body
        if state.booking_url and state.booking_url not in sms_body:
            sms_body = f"{body} Book here if useful: {state.booking_url}"
        send_result, updated_state = self.channel_orchestrator.send_sms(
            lead=lead,
            request=ProviderSendRequest(
                company_name=lead.company_name,
                contact_email=lead.contact_email,
                phone_number=lead.phone_number,
                body=sms_body,
                metadata={"channel": "sms", "booking_url": state.booking_url},
            ),
        )
        crm_sync = self.crm_service.sync_lifecycle(
            lead=lead,
            run_result=None,
            outbound_message=OutboundMessage(channel="sms", body=sms_body, crm_fields=self._crm_fields_from_state(updated_state)),
            lifecycle_state=updated_state,
            lifecycle_event="sms_sent",
        )
        return send_result, crm_sync

    def send_warm_whatsapp(
        self,
        *,
        lead: LeadRecord,
        body: str,
    ) -> tuple[ProviderSendResult, dict[str, object]]:
        state = self.channel_orchestrator.state_store.get(
            self.channel_orchestrator.lead_key(lead.company_name, lead.contact_email, lead.phone_number),
            company_name=lead.company_name,
            contact_email=lead.contact_email,
            phone_number=lead.phone_number,
        )
        whatsapp_body = body
        if state.booking_url and state.booking_url not in whatsapp_body:
            whatsapp_body = f"{body} Book here if useful: {state.booking_url}"
        send_result, updated_state = self.channel_orchestrator.send_whatsapp(
            lead=lead,
            request=ProviderSendRequest(
                company_name=lead.company_name,
                contact_email=lead.contact_email,
                phone_number=lead.phone_number,
                body=whatsapp_body,
                metadata={"channel": "whatsapp", "booking_url": state.booking_url},
            ),
        )
        crm_sync = self.crm_service.sync_lifecycle(
            lead=lead,
            run_result=None,
            outbound_message=OutboundMessage(channel="whatsapp", body=whatsapp_body, crm_fields=self._crm_fields_from_state(updated_state)),
            lifecycle_state=updated_state,
            lifecycle_event="whatsapp_sent",
        )
        return send_result, crm_sync

    def handle_inbound_event(self, event: InboundChannelEvent) -> dict[str, object]:
        if self.channel_orchestrator.is_duplicate_event(event):
            state = self.channel_orchestrator.state_store.get(
                self.channel_orchestrator.lead_key(event.company_name or "unknown", event.contact_email, event.phone_number),
                company_name=event.company_name or "unknown",
                contact_email=event.contact_email,
                phone_number=event.phone_number,
            )
            append_jsonl_log(
                "logs/conversation_events.jsonl",
                {
                    "channel": event.channel,
                    "provider": event.provider,
                    "event_type": event.event_type,
                    "company_name": event.company_name,
                    "contact_email": event.contact_email,
                    "phone_number": event.phone_number,
                    "message_text": event.message_text,
                    "duplicate": True,
                    "lifecycle_stage": state.stage.value,
                },
            )
            return {
                "accepted": True,
                "duplicate": True,
                "channel": event.channel,
                "event_type": event.event_type,
                "lifecycle_stage": state.stage.value,
                "qualification_status": state.qualification_status,
                "allowed_next_channels": self.channel_orchestrator.allowed_next_channels(state),
                "crm_sync": {"status": "skipped", "reason": "duplicate_event"},
            }
        state = self.channel_orchestrator.process_inbound_event(event)
        qualification_confidence_score: float | None = None
        if event.channel in {"email", "sms", "whatsapp"} and event.event_type == "reply":
            qualification_result = self.orchestrator.run_single_prospect(
                company_name=state.company_name,
                reply_text=event.message_text,
                contact_email=state.contact_email,
            )
            qualification_confidence_score = float(qualification_result["confidence_assessment"]["numeric_score"])
            state = self.channel_orchestrator.record_qualification(
                lead=LeadRecord(
                    company_name=state.company_name,
                    contact_email=state.contact_email,
                    phone_number=state.phone_number,
                ),
                qualification_status=str(qualification_result["qualification"]["qualification_status"]),
                intent_level=str(qualification_result["qualification"]["intent_level"]),
                next_action=str(qualification_result["qualification"]["next_action"]),
                confidence_score=qualification_confidence_score,
            )
        append_jsonl_log(
            "logs/conversation_events.jsonl",
            {
                "channel": event.channel,
                "provider": event.provider,
                "event_type": event.event_type,
                "company_name": event.company_name,
                "contact_email": event.contact_email,
                "phone_number": event.phone_number,
                "message_text": event.message_text,
                "qualification_confidence_score": qualification_confidence_score,
                "lifecycle_stage": state.stage.value,
            },
        )
        lead = LeadRecord(
            company_name=state.company_name,
            contact_email=state.contact_email,
            phone_number=state.phone_number,
        )
        crm_sync = self.crm_service.sync_inbound_event(lead=lead, lifecycle_state=state, event=event)
        return {
            "accepted": True,
            "channel": event.channel,
            "event_type": event.event_type,
            "lifecycle_stage": state.stage.value,
            "qualification_status": state.qualification_status,
            "allowed_next_channels": self.channel_orchestrator.allowed_next_channels(state),
            "crm_sync": crm_sync,
        }

    @staticmethod
    def _derive_icp_segment(result: dict[str, object]) -> str:
        employee_count = int(result.get("company_profile", {}).get("employee_count", 0) or 0)
        if employee_count >= 300:
            return "mid_market_platform"
        if employee_count >= 150:
            return "growth_fintech"
        return "emerging_fintech"

    @staticmethod
    def _crm_fields_from_state(state) -> CRMFields:  # noqa: ANN001
        return CRMFields(
            icp_segment="growth_fintech",
            signal_confidence=0.5,
            ai_maturity=0,
            intent_level=state.intent_level if state.intent_level in {"low", "medium", "high"} else "medium",
            qualification_status=state.qualification_status,
            next_action=state.next_action,
        )
