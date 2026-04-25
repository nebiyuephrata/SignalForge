from __future__ import annotations

import json
from datetime import datetime, timezone

from agent.briefs.brief_schema import LeadRecord, OutboundMessage
from agent.channels.channel_schema import InboundChannelEvent
from agent.core.models import LeadLifecycleState
from agent.crm.hubspot_client import HubSpotClient


class CRMService:
    def __init__(self, client: HubSpotClient | None = None) -> None:
        self.client = client or HubSpotClient()

    def sync_lifecycle(
        self,
        *,
        lead: LeadRecord,
        run_result: dict[str, object] | None,
        outbound_message: OutboundMessage,
        lifecycle_state: LeadLifecycleState,
        lifecycle_event: str,
    ) -> dict[str, object]:
        email = lead.contact_email or lifecycle_state.contact_email or ""
        if not email:
            return {"status": "skipped", "reason": "missing_contact_email"}

        contact_response = self.client.upsert_contact(
            email=email,
            properties=self._contact_properties(lead=lead, run_result=run_result, lifecycle_state=lifecycle_state),
        )
        contact_id = str(contact_response.get("id", "")) or lifecycle_state.crm_contact_id or ""
        if contact_id:
            lifecycle_state.crm_contact_id = contact_id

        enrichment_properties = self._signalforge_properties(
            run_result=run_result,
            outbound_message=outbound_message,
            lifecycle_state=lifecycle_state,
        )
        enrichment_write = (
            self._write_signalforge_enrichment(
                contact_id=contact_id,
                properties=enrichment_properties,
                fallback_subject="signalforge_enrichment_fields",
            )
            if contact_id
            else {"status": "skipped", "reason": "missing_contact_id"}
        )
        activity_log = (
            self.client.create_activity(
                contact_id=contact_id,
                subject=lifecycle_event,
                body=json.dumps(
                    {
                        "body_preview": outbound_message.body[:240],
                        "next_action": outbound_message.crm_fields.next_action,
                        "lifecycle_stage": lifecycle_state.stage,
                        "booking_url": lifecycle_state.booking_url,
                    },
                    indent=2,
                ),
                channel=outbound_message.channel,
            )
            if contact_id
            else {"status": "skipped", "reason": "missing_contact_id"}
        )
        return {
            "contact": contact_response,
            "enrichment_fields": enrichment_write,
            "activity_log": activity_log,
        }

    def sync_inbound_event(
        self,
        *,
        lead: LeadRecord,
        lifecycle_state: LeadLifecycleState,
        event: InboundChannelEvent,
    ) -> dict[str, object]:
        if not lifecycle_state.crm_contact_id and not lead.contact_email:
            return {"status": "skipped", "reason": "missing_contact_identity"}

        email = lead.contact_email or lifecycle_state.contact_email or ""
        contact_response = self.client.upsert_contact(
            email=email,
            properties={
                "email": email,
                "company": lead.company_name,
            },
        ) if email else {"status": "skipped", "reason": "missing_contact_email"}
        contact_id = str(contact_response.get("id", "")) or lifecycle_state.crm_contact_id or ""
        enrichment_write = (
            self._write_signalforge_enrichment(
                contact_id=contact_id,
                properties={
                    "signalforge_stage": lifecycle_state.stage.value,
                    "signalforge_next_action": lifecycle_state.next_action,
                    "signalforge_qualification_status": lifecycle_state.qualification_status,
                    "signalforge_intent_level": lifecycle_state.intent_level,
                    "signalforge_last_event_at": datetime.now(timezone.utc).isoformat(),
                    "signalforge_last_website_page": lifecycle_state.last_website_page or "",
                    "signalforge_last_website_visit_at": lifecycle_state.last_website_visit_at or "",
                    "signalforge_website_visits_count": lifecycle_state.website_visits_count,
                },
                fallback_subject="signalforge_inbound_fields",
            )
            if contact_id
            else {"status": "skipped", "reason": "missing_contact_id"}
        )
        note = (
            self.client.create_activity(
                contact_id=contact_id,
                subject=f"{event.channel}_{event.event_type}",
                body=event.message_text or event.event_type,
                channel=event.channel,
            )
            if contact_id
            else {"status": "skipped", "reason": "missing_contact_id"}
        )
        return {"contact": contact_response, "enrichment_fields": enrichment_write, "activity_log": note}

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
        enrichment_write = (
            self._write_signalforge_enrichment(
                contact_id=contact_id,
                properties={
                    "signalforge_booking_url": booking_url,
                    "signalforge_booking_event_type": "Tenacious discovery call",
                    "signalforge_last_booking_start": meeting_start,
                    "signalforge_stage": "BOOKED",
                    "signalforge_last_event_at": datetime.now(timezone.utc).isoformat(),
                },
                fallback_subject="signalforge_booking_fields",
            )
            if contact_id
            else {"status": "skipped", "reason": "missing_contact_id"}
        )
        booking_note = {
            "booking_id": booking_id,
            "booking_url": booking_url,
            "meeting_start": meeting_start,
            "booking_completed_at": datetime.now(timezone.utc).isoformat(),
        }
        note_response = (
            self.client.create_activity(
                contact_id=contact_id,
                subject="booking_completed",
                body=json.dumps(booking_note, indent=2),
                channel="calendar",
            )
            if contact_id
            else {"status": "skipped", "reason": "missing_contact_id"}
        )
        return {
            "contact": contact_response,
            "enrichment_fields": enrichment_write,
            "booking_note": note_response,
        }

    def _contact_properties(
        self,
        *,
        lead: LeadRecord,
        run_result: dict[str, object] | None,
        lifecycle_state: LeadLifecycleState,
    ) -> dict[str, object]:
        company_profile = (run_result or {}).get("company_profile", {}) if run_result else {}
        return {
            "email": lead.contact_email or lifecycle_state.contact_email or "",
            "firstname": lead.contact_name or "",
            "company": lead.company_name,
            "website": lead.domain or str(company_profile.get("domain", "")),
            "industry": lead.industry or str(company_profile.get("industry", "")),
            "city": lead.location or str(company_profile.get("location", "")),
            "phone": lead.phone_number or lifecycle_state.phone_number or "",
        }

    @staticmethod
    def _signalforge_properties(
        *,
        run_result: dict[str, object] | None,
        outbound_message: OutboundMessage,
        lifecycle_state: LeadLifecycleState,
    ) -> dict[str, object]:
        company_profile = (run_result or {}).get("company_profile", {}) if run_result else {}
        buying_window_signals = (run_result or {}).get("hiring_signal_brief", {}).get("buying_window_signals", {}) if run_result else {}
        funding_event = buying_window_signals.get("funding_event", {}) if isinstance(buying_window_signals, dict) else {}
        layoff_event = buying_window_signals.get("layoff_event", {}) if isinstance(buying_window_signals, dict) else {}
        leadership_change = buying_window_signals.get("leadership_change", {}) if isinstance(buying_window_signals, dict) else {}
        ai_maturity = (run_result or {}).get("hiring_signal_brief", {}).get("ai_maturity", {}) if run_result else {}

        return {
            "signalforge_signal_confidence": outbound_message.crm_fields.signal_confidence,
            "signalforge_ai_maturity": outbound_message.crm_fields.ai_maturity,
            "signalforge_ai_maturity_confidence": ai_maturity.get("confidence", ""),
            "signalforge_company_size": company_profile.get("employee_count", ""),
            "signalforge_last_funding_round": company_profile.get("last_funding_round", funding_event.get("stage", "")),
            "signalforge_funding_date": company_profile.get("funding_date", funding_event.get("closed_at", "")),
            "signalforge_job_posts_current": company_profile.get("open_roles_current", ""),
            "signalforge_job_posts_60d_ago": company_profile.get("open_roles_60_days_ago", ""),
            "signalforge_recent_layoffs": layoff_event.get("headcount_reduction", 0) if layoff_event else 0,
            "signalforge_recent_layoff_date": layoff_event.get("date", "") if layoff_event else "",
            "signalforge_recent_leadership_change": leadership_change.get("role", "") if leadership_change else "",
            "signalforge_recent_leadership_date": leadership_change.get("started_at", "") if leadership_change else "",
            "signalforge_intent_level": outbound_message.crm_fields.intent_level,
            "signalforge_qualification_status": outbound_message.crm_fields.qualification_status,
            "signalforge_next_action": outbound_message.crm_fields.next_action,
            "signalforge_stage": lifecycle_state.stage.value,
            "signalforge_booking_url": lifecycle_state.booking_url or "",
            "signalforge_last_event_at": datetime.now(timezone.utc).isoformat(),
            "signalforge_last_website_page": lifecycle_state.last_website_page or "",
            "signalforge_last_website_visit_at": lifecycle_state.last_website_visit_at or "",
            "signalforge_website_visits_count": lifecycle_state.website_visits_count,
        }

    def _write_signalforge_enrichment(
        self,
        *,
        contact_id: str,
        properties: dict[str, object],
        fallback_subject: str,
    ) -> dict[str, object]:
        response = self.client.update_contact_properties(contact_id=contact_id, properties=properties)
        if response.get("status") != "failed":
            return response

        fallback_note = self.client.create_activity(
            contact_id=contact_id,
            subject=fallback_subject,
            body=json.dumps(
                {
                    "status": "custom_property_fallback",
                    "properties": properties,
                    "error": response,
                },
                indent=2,
            ),
            channel="system",
        )
        return {
            "status": "fallback_logged",
            "reason": "custom_properties_unavailable",
            "update_error": response,
            "fallback_note": fallback_note,
        }
