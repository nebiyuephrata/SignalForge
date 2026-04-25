from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from agent.core.confidence import ConfidenceCalibrationLayer, compute_global_confidence
from agent.guards.claim_validator import validate_email_claims
from agent.llm.client import LLMClientResponse
from agent.llm.email_generator import generate_outreach_email
from agent.signals.competitor_gap import build_competitor_gap_brief
from agent.signals.hiring_signals import build_hiring_signal_brief
from agent.tools.crunchbase_tool import CrunchbaseTool
from agent.utils.trace_logger import write_json
from eval.adversarial_cases import ADVERSARIAL_CASES


REPO_ROOT = Path(__file__).resolve().parents[1]
ASSERTIVE_PATTERN = re.compile(r"\b(clearly|definitely|aggressively|certainly|must)\b", re.IGNORECASE)
CAPACITY_PATTERN = re.compile(r"\b(extra capacity|outside capacity|need extra help|likely needs)\b", re.IGNORECASE)


class ConfidenceEvalClient:
    """Controlled offline client for A/B calibration tests.

    The point of this harness is to keep the underlying generator behavior
    stable while changing only the confidence policy. That makes the measured
    delta attributable to calibration, not to provider availability.
    """

    def chat_json(self, **kwargs: Any) -> LLMClientResponse:  # noqa: ANN401
        metadata = kwargs.get("metadata", {})
        company_name = metadata.get("company_name", "This company")
        confidence_level = metadata.get("confidence_level", "medium")
        if confidence_level == "high":
            content = {
                "subject": f"Context: {company_name} hiring signal",
                "body": (
                    f"{company_name} moved from 3 to 12 open roles over the last 60 days after a funding event. "
                    "Would it be useful to compare notes on hiring capacity?"
                ),
                "claims_used": ["job_post_velocity", "funding_event"],
            }
        else:
            content = {
                "subject": f"Request: {company_name} capacity check",
                "body": (
                    f"{company_name} is clearly expanding and likely needs extra capacity right now."
                ),
                "claims_used": ["job_post_velocity", "capacity_need"],
            }
        return LLMClientResponse(
            content=content,
            model="eval/confidence-client",
            usage={"input": 0, "output": 0, "total": 0},
            cost_details={},
            latency_ms=0,
            trace_id="confidence-eval-trace",
            trace_url=None,
            cached=False,
            prompt_snapshot=kwargs,
        )


def run_confidence_comparison() -> dict[str, object]:
    crunchbase = CrunchbaseTool()
    calibration = ConfidenceCalibrationLayer()
    companies = sorted(
        {
            *[case["company_name"] for case in ADVERSARIAL_CASES],
            *[company["company_name"] for company in crunchbase.list_companies()],
        }
    )
    by_mode: dict[str, dict[str, object]] = {}

    for mode in ("calibration_on", "calibration_off"):
        rows: list[dict[str, object]] = []
        for company_name in companies:
            hiring_signal_brief = build_hiring_signal_brief(company_name, crunchbase)
            competitor_gap_brief = build_competitor_gap_brief(company_name, crunchbase)
            if mode == "calibration_on":
                confidence_level = calibration.assess(hiring_signal_brief, competitor_gap_brief).level
            else:
                confidence_level = compute_global_confidence(hiring_signal_brief)
            email = generate_outreach_email(
                hiring_signal_brief,
                competitor_gap_brief,
                confidence_level=confidence_level,
                client=ConfidenceEvalClient(),
            )
            validation = validate_email_claims(email, hiring_signal_brief, competitor_gap_brief)
            overclaim = _detect_overclaim(email=email, hiring_signal_brief=hiring_signal_brief)
            unsupported_assertion = bool(validation["unsupported_claim_ids"] or validation["unexpected_numeric_tokens"])
            rows.append(
                {
                    "company_name": company_name,
                    "confidence_level": confidence_level,
                    "email_model": email["model"],
                    "fallback_occurred": email["model"] == "deterministic-fallback",
                    "overclaim_detected": overclaim,
                    "unsupported_assertion_detected": unsupported_assertion,
                    "validation": validation,
                    "email_preview": email["body"],
                }
            )

        by_mode[mode] = _summarize_rows(rows)
        by_mode[mode]["cases"] = rows

    comparison = {
        "dataset_size": len(companies),
        "comparison": by_mode,
        "delta": {
            "overclaim_rate_change": round(
                by_mode["calibration_off"]["metrics"]["overclaim_rate"]
                - by_mode["calibration_on"]["metrics"]["overclaim_rate"],
                2,
            ),
            "unsupported_assertion_rate_change": round(
                by_mode["calibration_off"]["metrics"]["unsupported_assertion_rate"]
                - by_mode["calibration_on"]["metrics"]["unsupported_assertion_rate"],
                2,
            ),
            "fallback_frequency_change": round(
                by_mode["calibration_on"]["metrics"]["fallback_frequency"]
                - by_mode["calibration_off"]["metrics"]["fallback_frequency"],
                2,
            ),
        },
    }
    write_json(str(REPO_ROOT / "outputs" / "confidence_comparison.json"), comparison)
    return comparison


def _summarize_rows(rows: list[dict[str, object]]) -> dict[str, object]:
    total = len(rows)
    overclaims = sum(1 for row in rows if row["overclaim_detected"])
    unsupported = sum(1 for row in rows if row["unsupported_assertion_detected"])
    fallbacks = sum(1 for row in rows if row["fallback_occurred"])
    return {
        "metrics": {
            "overclaim_rate": round(overclaims / max(total, 1), 2),
            "unsupported_assertion_rate": round(unsupported / max(total, 1), 2),
            "fallback_frequency": round(fallbacks / max(total, 1), 2),
        }
    }


def _detect_overclaim(*, email: dict[str, object], hiring_signal_brief: dict[str, object]) -> bool:
    body = str(email["body"])
    overall_confidence = float(hiring_signal_brief["overall_confidence"])
    return overall_confidence < 0.78 and bool(ASSERTIVE_PATTERN.search(body) or CAPACITY_PATTERN.search(body))


if __name__ == "__main__":
    output = run_confidence_comparison()
    print(output["delta"])
