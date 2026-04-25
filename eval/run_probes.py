from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from agent.briefs.brief_schema import LeadRecord
from agent.channels.channel_schema import InboundChannelEvent, ProviderSendRequest, ProviderSendResult
from agent.channels.email.email_handler import EmailHandler
from agent.channels.sms.sms_handler import SMSHandler
from agent.core.channel_orchestrator import ChannelOrchestrator
from agent.core.confidence import ConfidenceCalibrationLayer
from agent.guards.claim_validator import validate_email_claims
from agent.llm.client import LLMClientResponse
from agent.llm.email_generator import generate_outreach_email
from agent.signals.competitor_gap import build_competitor_gap_brief
from agent.signals.hiring_signals import build_hiring_signal_brief
from agent.tools.crunchbase_tool import CrunchbaseTool
from agent.utils.trace_logger import write_json


REPO_ROOT = Path(__file__).resolve().parents[1]
PROBE_LIBRARY_PATH = REPO_ROOT / "probes" / "probe_library.json"
CRITICAL_CATEGORY_THRESHOLDS = {
    "weak confidence handling": 0.25,
    "coordination failures": 0.10,
}


class ProbeEvalClient:
    def chat_json(self, **kwargs):  # noqa: ANN003
        metadata = kwargs.get("metadata", {})
        company_name = metadata.get("company_name", "This company")
        confidence_level = metadata.get("confidence_level", "medium")
        if confidence_level == "high":
            content = {
                "subject": f"Context: {company_name} hiring signal",
                "body": f"{company_name} moved from 3 to 12 open roles over the last 60 days. Worth comparing notes?",
                "claims_used": ["job_post_velocity"],
            }
        else:
            content = {
                "subject": f"Request: {company_name} capacity check",
                "body": f"{company_name} is clearly expanding and likely needs extra capacity right now.",
                "claims_used": ["job_post_velocity", "capacity_need"],
            }
        return LLMClientResponse(
            content=content,
            model="probe/eval-client",
            usage={"input": 0, "output": 0, "total": 0},
            cost_details={},
            latency_ms=0,
            trace_id="probe-trace",
            trace_url=None,
            cached=False,
            prompt_snapshot=kwargs,
        )


class FakeEmailClient:
    def send(self, request: ProviderSendRequest) -> ProviderSendResult:
        return ProviderSendResult(
            channel="email",
            provider="resend",
            status="queued",
            destination=request.contact_email or "",
            external_id="email-1",
            detail="queued",
        )


class FakeSMSClient:
    def send(self, request: ProviderSendRequest) -> ProviderSendResult:
        return ProviderSendResult(
            channel="sms",
            provider="africas_talking",
            status="queued",
            destination=request.phone_number or "",
            external_id="sms-1",
            detail="queued",
        )


def run_probes(*, fail_on_critical: bool = False) -> dict[str, object]:
    probes = json.loads(PROBE_LIBRARY_PATH.read_text(encoding="utf-8"))
    results: list[dict[str, object]] = []
    for probe in probes:
        simulation = _simulate_probe(probe)
        results.append(
            {
                "id": probe["id"],
                "category": probe["category"],
                "setup": probe["setup"],
                "expected_failure": probe["expected_failure"],
                "triggered": simulation["triggered"],
                "evidence": simulation["evidence"],
                "observed_trigger_rate_reference": probe["observed_trigger_rate"],
                "business_cost_usd": probe["business_cost_usd"],
            }
        )

    category_summary = _category_summary(results)
    threshold_breaches = [
        {
            "category": category,
            "actual_trigger_rate": summary["actual_trigger_rate"],
            "threshold": CRITICAL_CATEGORY_THRESHOLDS[category],
        }
        for category, summary in category_summary.items()
        if category in CRITICAL_CATEGORY_THRESHOLDS and summary["actual_trigger_rate"] > CRITICAL_CATEGORY_THRESHOLDS[category]
    ]
    output = {
        "total_probes": len(results),
        "results": results,
        "category_summary": category_summary,
        "threshold_breaches": threshold_breaches,
    }
    write_json(str(REPO_ROOT / "outputs" / "probe_results.json"), output)
    if fail_on_critical and threshold_breaches:
        raise SystemExit(1)
    return output


def _simulate_probe(probe: dict[str, object]) -> dict[str, object]:
    category = str(probe["category"])
    if category in {
        "signal over-claiming",
        "weak confidence handling",
        "gap over-claiming",
        "outsourcing mismatch",
        "outsourcing perception",
        "CTO sensitivity",
        "tone drift",
        "ICP misclassification",
    }:
        return _simulate_content_controls(category)
    if category in {"coordination failures", "multi-thread leakage", "scheduling edge cases (EU/US/Africa)"}:
        return _simulate_state_controls(category)
    if category == "cost issues":
        return _simulate_cost_controls()
    if category == "signal reliability":
        return _simulate_signal_reliability()
    return {"triggered": False, "evidence": "No category simulator was required for this probe."}


def _simulate_content_controls(category: str) -> dict[str, object]:
    company_name = "Harborline Ledger" if category in {"signal over-claiming", "weak confidence handling", "gap over-claiming"} else "Northstar Lending"
    crunchbase = CrunchbaseTool()
    hiring_signal_brief = build_hiring_signal_brief(company_name, crunchbase)
    competitor_gap_brief = build_competitor_gap_brief(company_name, crunchbase)
    confidence_level = ConfidenceCalibrationLayer().assess(hiring_signal_brief, competitor_gap_brief).level
    email = generate_outreach_email(
        hiring_signal_brief,
        competitor_gap_brief,
        confidence_level=confidence_level,
        client=ProbeEvalClient(),
    )
    validation = validate_email_claims(email, hiring_signal_brief, competitor_gap_brief)

    if category == "weak confidence handling":
        triggered = confidence_level == "low" and email["model"] != "deterministic-fallback"
        evidence = f"confidence={confidence_level}, model={email['model']}"
        return {"triggered": triggered, "evidence": evidence}
    if category == "signal over-claiming":
        triggered = not validation["valid"] and bool(validation["confidence_tone_mismatch"])
        evidence = f"validation={validation}"
        return {"triggered": triggered, "evidence": evidence}
    if category == "gap over-claiming":
        triggered = bool(competitor_gap_brief.get("sparse_sector")) and "directional" not in competitor_gap_brief["gap_summary"].lower()
        evidence = competitor_gap_brief["gap_summary"]
        return {"triggered": triggered, "evidence": evidence}
    if category == "outsourcing mismatch":
        triggered = "outside capacity" in email["body"].lower() and confidence_level != "high"
        return {"triggered": triggered, "evidence": email["body"]}
    if category == "outsourcing perception":
        triggered = any(term in email["body"].lower() for term in ("offshore", "cheap", "cost savings"))
        return {"triggered": triggered, "evidence": email["body"]}
    if category == "CTO sensitivity":
        triggered = "behind" in email["body"].lower() and "public signal" not in email["body"].lower()
        return {"triggered": triggered, "evidence": email["body"]}
    if category == "tone drift":
        triggered = any(term in email["body"].lower() for term in ("super excited", "blasting", "huge opportunity"))
        return {"triggered": triggered, "evidence": email["body"]}
    if category == "ICP misclassification":
        triggered = "vp engineering" in email["body"].lower() or "cto" in email["body"].lower()
        return {"triggered": triggered, "evidence": email["body"]}
    return {"triggered": False, "evidence": "content control not triggered"}


def _simulate_state_controls(category: str) -> dict[str, object]:
    with TemporaryDirectory() as tempdir:
        orchestrator = ChannelOrchestrator(
            email_handler=EmailHandler(client=FakeEmailClient(), log_path=str(Path(tempdir) / "email.jsonl")),
            sms_handler=SMSHandler(client=FakeSMSClient(), log_path=str(Path(tempdir) / "sms.jsonl")),
        )
        orchestrator.state_store.path = Path(tempdir) / "state.json"

        if category == "multi-thread leakage":
            lead_one = LeadRecord(company_name="Northstar Lending", contact_email="one@northstar.example", phone_number="+15550000001")
            lead_two = LeadRecord(company_name="Northstar Lending", contact_email="two@northstar.example", phone_number="+15550000002")
            orchestrator.process_inbound_event(
                InboundChannelEvent(
                    channel="email",
                    provider="resend",
                    event_type="reply",
                    company_name=lead_one.company_name,
                    contact_email=lead_one.contact_email,
                    message_text="Interested.",
                )
            )
            state_two = orchestrator.state_store.get(
                orchestrator.lead_key(lead_two.company_name, lead_two.contact_email, lead_two.phone_number),
                company_name=lead_two.company_name,
                contact_email=lead_two.contact_email,
                phone_number=lead_two.phone_number,
            )
            triggered = state_two.email_reply_received
            return {"triggered": triggered, "evidence": state_two.model_dump()}

        lead = LeadRecord(company_name="Northstar Lending", contact_email="cto@northstar.example", phone_number="+15550000003")
        orchestrator.send_email(
            lead=lead,
            request=ProviderSendRequest(company_name=lead.company_name, contact_email=lead.contact_email, body="test"),
        )
        orchestrator.process_inbound_event(
            InboundChannelEvent(
                channel="email",
                provider="resend",
                event_type="reply",
                company_name=lead.company_name,
                contact_email=lead.contact_email,
                phone_number=lead.phone_number,
                message_text="Interested",
            )
        )
        state = orchestrator.state_store.get(
            orchestrator.lead_key(lead.company_name, lead.contact_email, lead.phone_number),
            company_name=lead.company_name,
            contact_email=lead.contact_email,
            phone_number=lead.phone_number,
        )
        if category == "coordination failures":
            triggered = state.stage != "email_replied" or "sms" not in orchestrator.allowed_next_channels(state)
            return {"triggered": triggered, "evidence": state.model_dump()}
        if category == "scheduling edge cases (EU/US/Africa)":
            orchestrator.process_inbound_event(
                InboundChannelEvent(
                    channel="calendar",
                    provider="calcom",
                    event_type="booking_completed",
                    company_name=lead.company_name,
                    contact_email=lead.contact_email,
                    phone_number=lead.phone_number,
                    message_text="2026-04-24T15:00:00Z",
                )
            )
            booked_state = orchestrator.state_store.get(
                orchestrator.lead_key(lead.company_name, lead.contact_email, lead.phone_number),
                company_name=lead.company_name,
                contact_email=lead.contact_email,
                phone_number=lead.phone_number,
            )
            triggered = booked_state.stage != "booked" or "tomorrow" in (booked_state.last_inbound_message or "").lower()
            return {"triggered": triggered, "evidence": booked_state.model_dump()}
    return {"triggered": False, "evidence": "state control not triggered"}


def _simulate_cost_controls() -> dict[str, object]:
    class CountingClient:
        def __init__(self) -> None:
            self.calls = 0

        def chat_json(self, **kwargs):  # noqa: ANN003
            self.calls += 1
            return LLMClientResponse(
                content={"subject": "x", "body": "x", "claims_used": []},
                model="counting",
                usage={},
                cost_details={},
                latency_ms=0,
                trace_id="count",
                trace_url=None,
                cached=False,
                prompt_snapshot=kwargs,
            )

    client = CountingClient()
    crunchbase = CrunchbaseTool()
    hiring_signal_brief = build_hiring_signal_brief("Harborline Ledger", crunchbase)
    competitor_gap_brief = build_competitor_gap_brief("Harborline Ledger", crunchbase)
    email = generate_outreach_email(
        hiring_signal_brief,
        competitor_gap_brief,
        confidence_level="low",
        client=client,
    )
    triggered = client.calls > 0 or email["model"] != "deterministic-fallback"
    return {"triggered": triggered, "evidence": {"client_calls": client.calls, "model": email["model"]}}


def _simulate_signal_reliability() -> dict[str, object]:
    crunchbase = CrunchbaseTool()
    missing = build_hiring_signal_brief("Does Not Exist LLC", crunchbase)
    current = build_hiring_signal_brief("Northstar Lending", crunchbase)
    sources = {source["source"]: source for source in current["data_sources_checked"]}
    triggered = (
        missing["primary_segment_match"] != "abstain"
        or "missing_crunchbase_record" not in missing["uncertainty_flags"]
        or sources["company_careers_page"]["status"] not in {"success", "fallback"}
    )
    return {
        "triggered": triggered,
        "evidence": {
            "missing_company_flags": missing["uncertainty_flags"],
            "company_careers_page_status": sources["company_careers_page"]["status"],
        },
    }


def _category_summary(results: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    categories = sorted({result["category"] for result in results})
    summary: dict[str, dict[str, object]] = {}
    for category in categories:
        category_results = [result for result in results if result["category"] == category]
        triggered = sum(1 for result in category_results if result["triggered"])
        summary[category] = {
            "total_probes": len(category_results),
            "triggered_probes": triggered,
            "actual_trigger_rate": round(triggered / max(len(category_results), 1), 2),
        }
    return summary


if __name__ == "__main__":
    output = run_probes()
    print(output["category_summary"])
