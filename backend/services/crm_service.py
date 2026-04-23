from __future__ import annotations

import json
from datetime import datetime, timezone

from agent.briefs.brief_schema import LeadRecord, OutboundMessage
from agent.crm.hubspot_client import HubSpotClient


class CRMService:
    def __init__(self, client: HubSpotClient | None = None) -> None:
        self.client = client or HubSpotClient()

    def sync(self, lead: LeadRecord, message: OutboundMessage) -> dict[str, str]:
        email = lead.contact_email or ""
        if not email:
            return {"status": "skipped", "reason": "missing_contact_email"}
        properties = {
            "email": email,
            "company": lead.company_name,
            "website": lead.domain or "",
            "industry": lead.industry or "",
            "city": lead.location or "",
        }
        contact_response = self.client.upsert_contact(email=email, properties=properties)
        contact_id = str(contact_response.get("id", ""))
        enrichment_payload = {
            "icp_segment": message.crm_fields.icp_segment,
            "signal_confidence": message.crm_fields.signal_confidence,
            "ai_maturity": message.crm_fields.ai_maturity,
            "intent_level": message.crm_fields.intent_level,
            "qualification_status": message.crm_fields.qualification_status,
            "next_action": message.crm_fields.next_action,
            "enrichment_timestamp": datetime.now(timezone.utc).isoformat(),
            "channel": message.channel,
            "message_preview": message.body[:240],
        }
        note_response = self.client.create_note(
            contact_id=contact_id,
            body=json.dumps(enrichment_payload, indent=2),
        ) if contact_id else {"status": "skipped", "reason": "missing_contact_id"}
        return {
            "contact": contact_response,
            "enrichment_note": note_response,
        }

    def sync_signalforge_run(
        self,
        *,
        run_result: dict[str, object],
        contact_email: str,
        contact_name: str | None = None,
    ) -> dict[str, object]:
        properties = {
            "email": contact_email,
            "firstname": contact_name or "",
            "company": str(run_result["company"]),
            "website": str(run_result.get("company_profile", {}).get("domain", "")),
            "industry": str(run_result.get("company_profile", {}).get("industry", "")),
            "city": str(run_result.get("company_profile", {}).get("location", "")),
        }
        contact_response = self.client.upsert_contact(email=contact_email, properties=properties)
        contact_id = str(contact_response.get("id", ""))
        enrichment_note = {
            "icp_segment": self._derive_icp_segment(run_result),
            "signal_confidence": run_result.get("hiring_signal_brief", {}).get("overall_confidence"),
            "ai_maturity": run_result.get("hiring_signal_brief", {}).get("ai_maturity_score", {}).get("value"),
            "enrichment_timestamp": datetime.now(timezone.utc).isoformat(),
            "trace_id": run_result.get("trace_id"),
            "hiring_summary": run_result.get("hiring_signal_brief", {}).get("summary"),
            "competitor_gap": run_result.get("competitor_gap_brief", {}).get("gap_summary"),
            "confidence": run_result.get("confidence"),
        }
        note_response = self.client.create_note(
            contact_id=contact_id,
            body=json.dumps(enrichment_note, indent=2),
        ) if contact_id else {"status": "skipped", "reason": "missing_contact_id"}
        return {"contact": contact_response, "enrichment_note": note_response}

    def sync_booking_completed(
        self,
        *,
        contact_email: str,
        company_name: str,
        booking_id: str,
        booking_url: str,
        meeting_start: str,
    ) -> dict[str, object]:
        contact_response = self.client.upsert_contact(
            email=contact_email,
            properties={
                "email": contact_email,
                "company": company_name,
            },
        )
        contact_id = str(contact_response.get("id", ""))
        booking_note = {
            "booking_id": booking_id,
            "booking_url": booking_url,
            "meeting_start": meeting_start,
            "booking_completed_at": datetime.now(timezone.utc).isoformat(),
        }
        note_response = self.client.create_note(
            contact_id=contact_id,
            body=json.dumps(booking_note, indent=2),
        ) if contact_id else {"status": "skipped", "reason": "missing_contact_id"}
        return {"contact": contact_response, "booking_note": note_response}

    @staticmethod
    def _derive_icp_segment(run_result: dict[str, object]) -> str:
        employee_count = int(run_result.get("company_profile", {}).get("employee_count", 0) or 0)
        if employee_count >= 300:
            return "mid_market_platform"
        if employee_count >= 150:
            return "growth_fintech"
        return "emerging_fintech"
