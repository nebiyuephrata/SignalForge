from __future__ import annotations

from agent.briefs.brief_schema import CRMFields, LeadRecord, OutboundMessage
from agent.channels.channel_schema import InboundChannelEvent
from agent.utils.trace_logger import append_jsonl_log
from agent.core.orchestrator import SignalForgeOrchestrator


class ConversationService:
    def __init__(self) -> None:
        self.orchestrator = SignalForgeOrchestrator()

    def draft_outreach(self, lead: LeadRecord) -> OutboundMessage:
        result = self.orchestrator.run_single_prospect(
            company_name=lead.company_name,
            reply_text=lead.last_email_reply_text,
        )
        qualification = result["qualification"]
        crm_fields = CRMFields(
            icp_segment=self._derive_icp_segment(result),
            signal_confidence=float(result["hiring_signal_brief"]["overall_confidence"]),
            ai_maturity=int(result["hiring_signal_brief"]["ai_maturity_score"]["value"]),
            intent_level=str(qualification["intent_level"]),
            qualification_status=str(qualification["qualification_status"]),
            next_action=str(qualification["next_action"]),
        )
        return OutboundMessage(channel="email", body=str(result["email"]["body"]), crm_fields=crm_fields)

    def handle_inbound_event(self, event: InboundChannelEvent) -> dict[str, object]:
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
            },
        )
        return {
            "accepted": True,
            "channel": event.channel,
            "event_type": event.event_type,
        }

    @staticmethod
    def _derive_icp_segment(result: dict[str, object]) -> str:
        employee_count = int(result.get("company_profile", {}).get("employee_count", 0) or 0)
        if employee_count >= 300:
            return "mid_market_platform"
        if employee_count >= 150:
            return "growth_fintech"
        return "emerging_fintech"
