from agent.core.confidence import compute_global_confidence
from agent.guards.claim_validator import validate_email_claims
from agent.llm.client import LLMClientResponse
from agent.llm.email_generator import generate_outreach_email


class FakeClient:
    def __init__(self, content: dict[str, object]) -> None:
        self.content = content

    def chat_json(self, **kwargs):  # noqa: ANN003
        return LLMClientResponse(
            content=self.content,
            model="fake/model",
            usage={"input": 10, "output": 20, "total": 30},
            cost_details={},
            latency_ms=12,
            trace_id="trace-123",
            trace_url="http://trace.local/trace-123",
            cached=False,
            prompt_snapshot=kwargs,
        )


def _high_conf_brief() -> tuple[dict[str, object], dict[str, object]]:
    hiring_signal_brief = {
        "company_name": "Northstar Lending",
        "summary": "Northstar Lending shows mixed but timely hiring intent.",
        "overall_confidence": 0.72,
        "signals": [
            {
                "signal": "funding_event",
                "confidence": 0.95,
                "value": {"round": "Series B", "date": "2026-02-14", "days_since_event": 68},
                "evidence": ["Series B on 2026-02-14"],
            },
            {
                "signal": "job_post_velocity",
                "confidence": 0.85,
                "value": {"open_roles_current": 12, "open_roles_60_days_ago": 3, "delta": 9, "ratio": 4.0},
                "evidence": ["3 roles -> 12 roles in 60 days"],
            },
            {
                "signal": "layoffs",
                "confidence": 0.8,
                "value": [{"reported_at": "2025-12-10", "employees_impacted": "18"}],
                "evidence": ["18 employees impacted on 2025-12-10"],
            },
        ],
        "ai_maturity_score": {"value": 1, "confidence": 0.8},
    }
    competitor_gap_brief = {
        "company_name": "Northstar Lending",
        "gap_summary": "Peer average AI maturity is higher than Northstar Lending.",
        "top_quartile_practices": ["AI governance council", "retrieval workflows"],
        "confidence": 0.6,
        "target_ai_maturity": 1,
        "peer_average_ai_maturity": 1.4,
    }
    return hiring_signal_brief, competitor_gap_brief


def test_compute_global_confidence_shifts_by_signal_strength() -> None:
    hiring_signal_brief, _ = _high_conf_brief()
    assert compute_global_confidence(hiring_signal_brief) == "medium"

    hiring_signal_brief["overall_confidence"] = 0.81
    assert compute_global_confidence(hiring_signal_brief) == "high"

    hiring_signal_brief["overall_confidence"] = 0.2
    assert compute_global_confidence(hiring_signal_brief) == "low"


def test_generate_outreach_email_uses_llm_output_without_hallucinated_claim_ids() -> None:
    hiring_signal_brief, competitor_gap_brief = _high_conf_brief()
    email = generate_outreach_email(
        hiring_signal_brief,
        competitor_gap_brief,
        confidence_level="medium",
        client=FakeClient(
            {
                "subject": "Request: Northstar hiring context",
                "body": "It looks like Northstar Lending moved from 3 to 12 open roles after a Series B.",
                "claims_used": ["funding_event", "job_post_velocity"],
            }
        ),
    )

    assert email["subject"].startswith("Request:")
    assert email["confidence_level"] == "medium"
    report = validate_email_claims(email, hiring_signal_brief, competitor_gap_brief)
    assert report["valid"] is True


def test_validate_email_claims_rejects_unsupported_numbers() -> None:
    hiring_signal_brief, competitor_gap_brief = _high_conf_brief()
    email_output = {
        "subject": "Unsupported claim",
        "body": "Northstar Lending moved from 3 to 19 open roles after funding.",
        "claims_used": ["funding_event", "job_post_velocity"],
    }

    report = validate_email_claims(email_output, hiring_signal_brief, competitor_gap_brief)

    assert report["valid"] is False
    assert "19" in report["unexpected_numeric_tokens"]


def test_generate_outreach_email_falls_back_on_empty_signals() -> None:
    hiring_signal_brief = {
        "company_name": "Empty Co",
        "summary": "No useful signals available.",
        "overall_confidence": 0.1,
        "signals": [],
        "ai_maturity_score": {"value": 0, "confidence": 0.0},
    }
    competitor_gap_brief = {
        "company_name": "Empty Co",
        "gap_summary": "",
        "top_quartile_practices": [],
        "confidence": 0.0,
        "target_ai_maturity": 0,
        "peer_average_ai_maturity": 0,
    }

    email = generate_outreach_email(hiring_signal_brief, competitor_gap_brief, confidence_level="low")

    assert email["model"] == "deterministic-fallback"
    assert "not confident enough" in email["body"].lower()
