from __future__ import annotations

from statistics import mean

from agent.calendar.cal_client import CalClient
from agent.core.confidence import ConfidenceCalibrationLayer
from agent.guards.claim_validator import validate_email_claims
from agent.llm.email_generator import generate_deterministic_fallback_email, generate_outreach_email
from agent.signals.competitor_gap import build_competitor_gap_brief
from agent.signals.hiring_signals import build_hiring_signal_brief
from agent.tools.crunchbase_tool import CrunchbaseTool

SYNTHETIC_COMPANY_NAME = "Northstar Lending"
SYNTHETIC_REPLY = (
    "Yes, that's directionally right. We're adding AI operations capacity this quarter "
    "and would be open to a 20-minute call next week."
)


class SignalForgeOrchestrator:
    def __init__(self) -> None:
        self.crunchbase_tool = CrunchbaseTool()
        self.cal_client = CalClient()
        self.confidence_layer = ConfidenceCalibrationLayer()

    def run_single_prospect(
        self,
        company_name: str = SYNTHETIC_COMPANY_NAME,
        reply_text: str | None = None,
        *,
        contact_email: str | None = None,
    ) -> dict[str, object]:
        company = self.crunchbase_tool.get_company_by_name(company_name) or {
            "company_name": company_name,
            "domain": "unknown",
            "industry": "unknown",
            "location": "unknown",
            "employee_count": 0,
        }

        hiring_signal_brief = build_hiring_signal_brief(company_name, self.crunchbase_tool)
        competitor_gap_brief = build_competitor_gap_brief(company_name, self.crunchbase_tool)
        confidence_assessment = self.confidence_layer.assess(
            hiring_signal_brief=hiring_signal_brief,
            competitor_gap_brief=competitor_gap_brief,
        )
        email_output = generate_outreach_email(
            hiring_signal_brief,
            competitor_gap_brief,
            confidence_level=confidence_assessment.level,
        )
        validation = validate_email_claims(
            email_output,
            hiring_signal_brief,
            competitor_gap_brief,
            regenerate=lambda: generate_outreach_email(
                hiring_signal_brief,
                competitor_gap_brief,
                confidence_level=confidence_assessment.level,
                strict_mode=True,
            ),
        )
        if not validation["valid"] and "regenerated_email" in validation:
            email_output = validation["regenerated_email"]
            validation = validate_email_claims(email_output, hiring_signal_brief, competitor_gap_brief)
            if not validation["valid"]:
                email_output = generate_deterministic_fallback_email(
                    hiring_signal_brief,
                    competitor_gap_brief,
                    confidence_level=confidence_assessment.level,
                    reason="claim_validation_failure",
                )
                validation = validate_email_claims(email_output, hiring_signal_brief, competitor_gap_brief)

        inbound_reply = reply_text or SYNTHETIC_REPLY
        qualification = self.qualify_reply(
            inbound_reply,
            hiring_signal_brief=hiring_signal_brief,
            competitor_gap_brief=competitor_gap_brief,
            confidence_level=confidence_assessment.level,
        )
        booking_url = self.cal_client.booking_link(company_name=company_name, contact_email=contact_email)
        booking = {
            "should_book": qualification["qualification_status"] == "qualified",
            "booking_url": booking_url,
            "booking_reason": qualification["next_action"],
        }

        email = {
            "subject": str(email_output["subject"]),
            "body": self._attach_booking_link(
                body=str(email_output["body"]),
                booking_url=booking_url,
                should_attach=booking["should_book"],
            ),
        }
        return {
            "as_of_date": hiring_signal_brief["as_of_date"],
            "company": company_name,
            "company_profile": company,
            "hiring_signal_brief": hiring_signal_brief,
            "competitor_gap_brief": competitor_gap_brief,
            "email": email,
            "email_debug": {**email_output, "body": email["body"]},
            "confidence": confidence_assessment.level,
            "confidence_assessment": confidence_assessment.model_dump(),
            "trace_id": str(email_output.get("trace_id", "")),
            "trace_url": email_output.get("trace_url"),
            "claim_validation": validation,
            "reply_text": inbound_reply,
            "qualification": qualification,
            "booking": booking,
            "channel_plan": {
                "primary_channel": "email",
                "sms_gate": "requires_recorded_email_reply",
                "voice_gate": "requires_sms_reply_or_manual_operator_decision",
                "allowed_channels_after_reply": ["sms", "calendar"],
            },
        }

    def run_scenario(
        self,
        company_name: str,
        reply_text: str,
        scenario_name: str,
    ) -> dict[str, object]:
        result = self.run_single_prospect(company_name=company_name, reply_text=reply_text)
        result["scenario_name"] = scenario_name
        return result

    def qualify_reply(
        self,
        reply_text: str,
        *,
        hiring_signal_brief: dict[str, object],
        competitor_gap_brief: dict[str, object],
        confidence_level: str,
    ) -> dict[str, object]:
        normalized = reply_text.lower()
        positive_markers = ["yes", "open", "call", "next week", "meeting", "interested"]
        pain_markers = ["hiring", "capacity", "operations", "risk", "compliance", "ai"]

        interest_score = sum(1 for marker in positive_markers if marker in normalized)
        pain_score = sum(1 for marker in pain_markers if marker in normalized)
        signal_confidence = mean(
            [
                float(hiring_signal_brief["overall_confidence"]),
                float(competitor_gap_brief["confidence"]),
            ]
        )

        if interest_score >= 2 and pain_score >= 1 and confidence_level != "low":
            return {
                "qualification_status": "qualified",
                "intent_level": "high",
                "signal_confidence": round(signal_confidence, 2),
                "next_action": "share_booking_link",
                "reasoning": [
                    "Prospect confirmed the premise.",
                    "Prospect referenced an active capacity problem.",
                    "Prospect accepted a follow-up conversation.",
                ],
            }
        if interest_score >= 1:
            return {
                "qualification_status": "partial",
                "intent_level": "medium",
                "signal_confidence": round(signal_confidence, 2),
                "next_action": "send_warm_sms_or_follow_up_email",
                "reasoning": [
                    "Prospect showed some engagement but did not confirm urgency strongly enough for an immediate booking push.",
                ],
            }
        return {
            "qualification_status": "partial",
            "intent_level": "low" if confidence_level == "low" else "medium",
            "signal_confidence": round(signal_confidence, 2),
            "next_action": "ask_follow_up_question",
            "reasoning": [
                "Reply did not clearly confirm both urgency and willingness to meet.",
            ],
        }

    @staticmethod
    def _attach_booking_link(*, body: str, booking_url: str, should_attach: bool) -> str:
        if not should_attach or booking_url in body:
            return body
        return f"{body}\n\nIf a short call is useful, here is my Cal.com link: {booking_url}"
