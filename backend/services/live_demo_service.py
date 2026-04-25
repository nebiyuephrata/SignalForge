from __future__ import annotations

from agent.core.orchestrator import SignalForgeOrchestrator
from agent.llm.email_generator import generate_deterministic_fallback_email
from agent.utils.trace_logger import append_jsonl_log


class LiveDemoService:
    """Demo-ready endpoint service for a single live pipeline run."""

    def __init__(self) -> None:
        self.orchestrator = SignalForgeOrchestrator()

    def run(self, *, company_name: str, contact_email: str | None = None, reply_text: str | None = None) -> dict[str, object]:
        try:
            result = self.orchestrator.run_single_prospect(
                company_name=company_name,
                reply_text=reply_text,
                contact_email=contact_email,
            )
        except Exception as exc:  # noqa: BLE001
            hiring_signal_brief = {
                "company_name": company_name,
                "summary": "SignalForge demo fallback executed because the live pipeline did not complete.",
                "signals": [],
                "overall_confidence": 0.0,
            }
            competitor_gap_brief = {
                "prospect_domain": "unknown",
                "gap_summary": "Competitor gap analysis unavailable during demo fallback.",
                "gap_findings": [],
                "confidence": 0.0,
            }
            generated_email = generate_deterministic_fallback_email(
                hiring_signal_brief,
                competitor_gap_brief,
                confidence_level="low",
                reason="demo_service_exception",
                reason_detail={"error": str(exc)},
            )
            fallback = {
                "company": company_name,
                "hiring_signal_brief": hiring_signal_brief,
                "competitor_gap_brief": competitor_gap_brief,
                "generated_email": {
                    "subject": generated_email["subject"],
                    "body": generated_email["body"],
                },
                "channel_plan": {
                    "primary_channel": "email",
                    "sms_gate": "requires_recorded_email_reply_and_confidence_gte_0_6",
                    "whatsapp_gate": "requires_recorded_email_reply_and_confidence_gte_0_6",
                    "voice_gate": "requires_sms_reply_or_manual_operator_decision",
                    "allowed_channels_after_reply": ["email"],
                },
                "confidence_score": 0.0,
                "confidence_level": "low",
                "trace_id": None,
                "trace_url": None,
            }
            append_jsonl_log(
                "logs/demo_runs.jsonl",
                {
                    "company_name": company_name,
                    "contact_email": contact_email,
                    "status": "fallback",
                    "error": str(exc),
                    "response": fallback,
                },
            )
            return fallback
        response = {
            "company": result["company"],
            "hiring_signal_brief": result["hiring_signal_brief"],
            "competitor_gap_brief": result["competitor_gap_brief"],
            "generated_email": result["email"],
            "channel_plan": result["channel_plan"],
            "confidence_score": float(result["confidence_assessment"]["numeric_score"]),
            "confidence_level": result["confidence"],
            "trace_id": result["trace_id"],
            "trace_url": result["trace_url"],
        }
        append_jsonl_log(
            "logs/demo_runs.jsonl",
            {
                "company_name": company_name,
                "contact_email": contact_email,
                "status": "success",
                "confidence_score": response["confidence_score"],
                "generated_email_model": result.get("email_debug", {}).get("model"),
                "response": response,
            },
        )
        return response
