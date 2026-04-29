from __future__ import annotations

import re
from typing import Any

from agent.channels.email.email_generator import generate_grounded_email as generate_fallback_email
from agent.core.confidence import compute_global_confidence
from agent.llm.client import LLMClientResponse, OpenRouterClient, OpenRouterClientError
from agent.tenacious.context import load_icp_definition, load_style_guide
from agent.utils.logger import get_logger

logger = get_logger(__name__)
VIDEO_DEMO_RECIPIENT_NAME = "Ephrata"


CLAIM_LIMITS = {
    "high": 3,
    "medium": 2,
    "low": 1,
}


def generate_outreach_email(
    hiring_signal_brief: dict[str, object],
    competitor_gap_brief: dict[str, object],
    *,
    confidence_level: str | None = None,
    strict_mode: bool = False,
    client: OpenRouterClient | None = None,
) -> dict[str, object]:
    company_name = str(hiring_signal_brief.get("company_name", "this company"))
    confidence = confidence_level or compute_global_confidence(hiring_signal_brief)
    claim_catalog = build_claim_catalog(hiring_signal_brief, competitor_gap_brief)
    allowed_claims = claim_catalog[: CLAIM_LIMITS[confidence]]

    if not allowed_claims:
        return generate_deterministic_fallback_email(
            hiring_signal_brief,
            competitor_gap_brief,
            confidence_level=confidence,
            reason="no_grounded_claims",
        )

    if confidence == "low":
        return generate_deterministic_fallback_email(
            hiring_signal_brief,
            competitor_gap_brief,
            confidence_level=confidence,
            reason="weak_confidence_default",
        )

    llm_client = client or OpenRouterClient()
    system_prompt = _build_system_prompt(confidence, strict_mode)
    user_prompt = _build_user_prompt(company_name, confidence, allowed_claims)
    try:
        response = llm_client.chat_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            prompt_name="generate_outreach_email_strict" if strict_mode else "generate_outreach_email",
            temperature=0.32 if confidence == "high" else 0.38,
            metadata={"company_name": company_name, "confidence_level": confidence},
            strict_mode=strict_mode,
        )
    except OpenRouterClientError as exc:
        logger.warning("Falling back to deterministic email due to LLM error: %s", exc)
        return generate_deterministic_fallback_email(
            hiring_signal_brief,
            competitor_gap_brief,
            confidence_level=confidence,
            reason="llm_error",
            reason_detail={
                "error": str(exc),
                "trace_id": exc.trace_id,
                "trace_url": exc.trace_url,
                "prompt_name": exc.prompt_name,
                "model_attempts": exc.model_attempts,
            },
        )

    return _normalize_email_output(response=response, confidence_level=confidence, claim_catalog=allowed_claims)


def build_claim_catalog(
    hiring_signal_brief: dict[str, object],
    competitor_gap_brief: dict[str, object],
) -> list[dict[str, Any]]:
    catalog: list[dict[str, Any]] = []
    signals = hiring_signal_brief.get("signals", [])
    for signal in signals:
        if not isinstance(signal, dict):
            continue
        signal_name = str(signal.get("signal", ""))
        signal_confidence = float(signal.get("confidence", 0.0))
        value = signal.get("value", {})
        if signal_name == "funding_event" and signal_confidence >= 0.5:
            catalog.append(
                {
                    "id": "funding_event",
                    "type": "funding",
                    "confidence": signal_confidence,
                    "statement": f"{value['round']} on {value['date']} ({value['days_since_event']} days ago).",
                }
            )
        if signal_name == "job_post_velocity" and signal_confidence >= 0.55:
            catalog.append(
                {
                    "id": "job_post_velocity",
                    "type": "hiring",
                    "confidence": signal_confidence,
                    "statement": (
                        f"Open roles moved from {value['open_roles_60_days_ago']} to {value['open_roles_current']} over the last 60 days."
                    ),
                }
            )
        if signal_name == "leadership_change" and signal_confidence >= 0.6 and signal.get("evidence"):
            catalog.append(
                {
                    "id": "leadership_change",
                    "type": "leadership",
                    "confidence": signal_confidence,
                    "statement": str(signal["evidence"][0]),
                }
            )
        if signal_name == "layoffs" and signal_confidence >= 0.7 and signal.get("evidence"):
            catalog.append(
                {
                    "id": "layoffs",
                    "type": "restructure",
                    "confidence": signal_confidence,
                    "statement": str(signal["evidence"][0]),
                }
            )

    ai_signal = hiring_signal_brief.get("ai_maturity", {})
    if isinstance(ai_signal, dict):
        catalog.append(
            {
                "id": "ai_maturity",
                "type": "ai_maturity",
                "confidence": float(ai_signal.get("confidence", 0.0)),
                "statement": f"AI maturity score is {ai_signal.get('score', 0)}.",
            }
        )

    primary_segment_match = str(hiring_signal_brief.get("primary_segment_match", "")).strip()
    segment_confidence = float(hiring_signal_brief.get("segment_confidence", 0.0) or 0.0)
    if primary_segment_match and primary_segment_match != "abstain":
        catalog.append(
            {
                "id": "primary_segment_match",
                "type": "segment",
                "confidence": segment_confidence,
                "statement": f"Primary Tenacious segment match is {primary_segment_match}.",
            }
        )

    bench_match = hiring_signal_brief.get("bench_to_brief_match", {})
    if isinstance(bench_match, dict):
        catalog.append(
            {
                "id": "bench_to_brief_match",
                "type": "bench",
                "confidence": 0.9,
                "statement": (
                    f"Bench availability for required stacks is {bench_match.get('bench_available', False)} "
                    f"with gaps: {', '.join(bench_match.get('gaps', [])) or 'none'}."
                ),
            }
        )

    if competitor_gap_brief:
        catalog.append(
            {
                "id": "competitor_gap",
                "type": "competitor_gap",
                "confidence": float(competitor_gap_brief.get("confidence", 0.0)),
                "statement": str(competitor_gap_brief.get("gap_summary", "")),
            }
        )
        catalog.append(
            {
                "id": "distribution_position",
                "type": "competitor_gap",
                "confidence": float(competitor_gap_brief.get("confidence", 0.0)),
                "statement": (
                    f"Prospect distribution position is {competitor_gap_brief.get('distribution_position', {}).get('label', 'unknown')} "
                    f"with peer average AI maturity {competitor_gap_brief.get('peer_average_ai_maturity', 0)}."
                ),
            }
        )
        for index, finding in enumerate(competitor_gap_brief.get("gap_findings", [])[:3], start=1):
            if not isinstance(finding, dict):
                continue
            catalog.append(
                {
                    "id": f"gap_finding_{index}",
                    "type": "competitor_gap",
                    "confidence": 0.85 if finding.get("confidence") == "high" else 0.65,
                    "statement": f"Gap finding: {finding.get('practice')}. Prospect state: {finding.get('prospect_state')}",
                }
            )

    catalog = [claim for claim in catalog if str(claim["statement"]).strip()]
    catalog.sort(key=lambda claim: float(claim["confidence"]), reverse=True)
    return catalog


def _build_system_prompt(confidence_level: str, strict_mode: bool) -> str:
    tone_rule = {
        "high": "Use precise, direct assertions, but never move beyond the listed claims.",
        "medium": "Use cautious phrasing such as 'it looks like' or 'it may be' and avoid hard certainty.",
        "low": "Use exploratory, question-led language and avoid declarative claims.",
    }[confidence_level]
    strict_instruction = (
        "You are repairing a previous draft. Use at most one claim and prefer a calibration question."
        if strict_mode
        else "Keep the note concise and executive-level."
    )
    return (
        "You are generating B2B outreach for Tenacious via SignalForge. "
        "Never fabricate or infer facts beyond the listed claims. "
        "Reference only the allowed claim ids. "
        "If uncertainty is visible, preserve it instead of smoothing it away. "
        "Subject lines must start with Request, Question, Context, or Follow-up and stay under 60 characters. "
        "Keep the body under 120 words and avoid generic outsourcing language. "
        f"{tone_rule} {strict_instruction} "
        "Return JSON with keys: subject, body, claims_used."
    )


def _build_user_prompt(company_name: str, confidence_level: str, claim_catalog: list[dict[str, Any]]) -> str:
    claim_lines = "\n".join(
        f"- {claim['id']} (confidence={claim['confidence']:.2f}): {claim['statement']}" for claim in claim_catalog
    )
    return (
        f"Company: {company_name}\n"
        f"Confidence level: {confidence_level}\n"
        f"Tenacious ICP reference:\n{load_icp_definition()[:2200]}\n\n"
        f"Tenacious style reference:\n{load_style_guide()[:2200]}\n\n"
        "Allowed claims:\n"
        f"{claim_lines}\n\n"
        "Write one email using only the allowed claims. "
        "Do not mention unnamed competitors. "
        "If the confidence is medium, keep the tone careful and avoid saying the prospect 'clearly' needs anything. "
        "If the confidence is high, you may use direct but grounded assertions."
    )


def _normalize_email_output(
    *,
    response: LLMClientResponse,
    confidence_level: str,
    claim_catalog: list[dict[str, Any]],
) -> dict[str, object]:
    content = response.content
    claims_used = content.get("claims_used", [])
    if not isinstance(claims_used, list):
        claims_used = []
    return {
        "subject": _replace_unresolved_name_tokens(str(content.get("subject", "")).strip()),
        "body": _replace_unresolved_name_tokens(str(content.get("body", "")).strip()),
        "confidence_level": confidence_level,
        "claims_used": [str(claim_id) for claim_id in claims_used],
        "available_claims": [claim["id"] for claim in claim_catalog],
        "model": response.model,
        "trace_id": response.trace_id,
        "trace_url": response.trace_url,
        "usage": response.usage,
        "cost_details": response.cost_details,
        "latency_ms": response.latency_ms,
        "cached": response.cached,
        "prompt_snapshot": response.prompt_snapshot,
    }


def generate_deterministic_fallback_email(
    hiring_signal_brief: dict[str, object],
    competitor_gap_brief: dict[str, object],
    *,
    confidence_level: str | None = None,
    reason: str,
    reason_detail: dict[str, object] | None = None,
) -> dict[str, object]:
    company_name = str(hiring_signal_brief.get("company_name", "this company"))
    confidence = confidence_level or compute_global_confidence(hiring_signal_brief)
    if confidence == "low":
        fallback = {
            "subject": f"Question: {company_name} signal check",
            "body": (
                f"I'm not confident enough to make a hard claim about {company_name} from the available data. "
                "Is hiring capacity, compliance workload, or AI operations a live priority right now?"
            ),
        }
    else:
        company = {"company_name": company_name}
        fallback = generate_fallback_email(company, hiring_signal_brief, competitor_gap_brief)
    return {
        "subject": _replace_unresolved_name_tokens(str(fallback["subject"])),
        "body": _replace_unresolved_name_tokens(str(fallback["body"])),
        "confidence_level": confidence,
        "claims_used": [],
        "available_claims": [claim["id"] for claim in build_claim_catalog(hiring_signal_brief, competitor_gap_brief)],
        "model": "deterministic-fallback",
        "trace_id": "",
        "trace_url": None,
        "usage": {},
        "cost_details": {},
        "latency_ms": 0,
        "cached": False,
        "prompt_snapshot": {"fallback_reason": reason, "fallback_reason_detail": reason_detail or {}},
    }


def _replace_unresolved_name_tokens(value: str) -> str:
    if not value:
        return value
    patterns = [
        r"\{\{\s*first_?name\s*\}\}",
        r"\{\s*first_?name\s*\}",
        r"<\s*first_?name\s*>",
        r"\[\s*first\s*name\s*\]",
        r"\[\s*name\s*\]",
    ]
    normalized = value
    for pattern in patterns:
        normalized = re.sub(pattern, VIDEO_DEMO_RECIPIENT_NAME, normalized, flags=re.IGNORECASE)
    return normalized
