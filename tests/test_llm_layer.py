from agent.core.confidence import ConfidenceCalibrationLayer, compute_global_confidence
from agent.guards.claim_validator import validate_email_claims
from agent.llm.client import LLMClientResponse
from agent.llm.email_generator import build_claim_catalog, generate_outreach_email
from agent.signals.competitor_gap import build_competitor_gap_brief
from agent.signals.hiring_signals import build_hiring_signal_brief
from agent.tools.crunchbase_tool import CrunchbaseTool


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


def _briefs() -> tuple[dict[str, object], dict[str, object]]:
    crunchbase = CrunchbaseTool()
    return (
        build_hiring_signal_brief("Northstar Lending", crunchbase),
        build_competitor_gap_brief("Northstar Lending", crunchbase),
    )


def test_compute_global_confidence_is_backward_compatible() -> None:
    hiring_signal_brief, _ = _briefs()
    assert compute_global_confidence(hiring_signal_brief) in {"medium", "high"}

    hiring_signal_brief["overall_confidence"] = 0.81
    assert compute_global_confidence(hiring_signal_brief) == "high"

    hiring_signal_brief["overall_confidence"] = 0.2
    assert compute_global_confidence(hiring_signal_brief) == "low"


def test_confidence_calibration_layer_separates_score_from_behavior() -> None:
    hiring_signal_brief, competitor_gap_brief = _briefs()
    assessment = ConfidenceCalibrationLayer().assess(hiring_signal_brief, competitor_gap_brief)

    assert assessment.numeric_score >= 0.0
    assert assessment.level in {"low", "medium", "high"}
    assert assessment.behavior.max_claims >= 1


def test_build_claim_catalog_is_sorted_and_grounded() -> None:
    hiring_signal_brief, competitor_gap_brief = _briefs()
    claim_catalog = build_claim_catalog(hiring_signal_brief, competitor_gap_brief)

    assert claim_catalog
    assert claim_catalog[0]["confidence"] >= claim_catalog[-1]["confidence"]
    assert any(claim["id"] == "job_post_velocity" for claim in claim_catalog)


def test_generate_outreach_email_uses_llm_output_without_hallucinated_numbers() -> None:
    hiring_signal_brief, competitor_gap_brief = _briefs()
    email = generate_outreach_email(
        hiring_signal_brief,
        competitor_gap_brief,
        confidence_level="medium",
        client=FakeClient(
            {
                "subject": "Request: Northstar hiring context",
                "body": "It looks like Northstar Lending moved from 3 to 12 open roles over the last 60 days.",
                "claims_used": ["job_post_velocity"],
            }
        ),
    )

    assert email["subject"].startswith("Request:")
    report = validate_email_claims(email, hiring_signal_brief, competitor_gap_brief)
    assert report["valid"] is True


def test_validate_email_claims_rejects_tone_mismatch_for_low_confidence() -> None:
    hiring_signal_brief, competitor_gap_brief = _briefs()
    email_output = {
        "subject": "Unsupported claim",
        "body": "Northstar Lending is clearly hiring aggressively.",
        "claims_used": ["job_post_velocity"],
        "confidence_level": "low",
    }

    report = validate_email_claims(email_output, hiring_signal_brief, competitor_gap_brief)

    assert report["valid"] is False
    assert report["confidence_tone_mismatch"] is True


def test_generate_outreach_email_falls_back_on_low_confidence() -> None:
    hiring_signal_brief = build_hiring_signal_brief("Harborline Ledger", CrunchbaseTool())
    competitor_gap_brief = build_competitor_gap_brief("Harborline Ledger", CrunchbaseTool())

    email = generate_outreach_email(hiring_signal_brief, competitor_gap_brief, confidence_level="low")

    assert email["model"] == "deterministic-fallback"
    assert "not confident enough" in email["body"].lower()
