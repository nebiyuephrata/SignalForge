from __future__ import annotations

from typing import Any

from agent.channels.email.email_generator import generate_grounded_email as generate_fallback_email
from agent.core.confidence import compute_global_confidence
from agent.llm.client import LLMClientResponse, OpenRouterClient, OpenRouterClientError
from agent.tenacious.context import load_icp_definition, load_style_guide
from agent.utils.logger import get_logger

logger = get_logger(__name__)


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
    structured_signals = hiring_signal_brief.get("signals", [])
    if not claim_catalog:
        return generate_deterministic_fallback_email(
            hiring_signal_brief,
            competitor_gap_brief,
            confidence_level=confidence,
            reason="no_claims",
        )

    if confidence == "low" and (not isinstance(structured_signals, list) or len(structured_signals) == 0):
        return generate_deterministic_fallback_email(
            hiring_signal_brief,
            competitor_gap_brief,
            confidence_level=confidence,
            reason="no_structured_signals",
        )

    if confidence == "low" and len(claim_catalog) <= 2:
        return generate_deterministic_fallback_email(
            hiring_signal_brief,
            competitor_gap_brief,
            confidence_level=confidence,
            reason="low_value",
        )

    llm_client = client or OpenRouterClient()
    system_prompt = _build_system_prompt(confidence, strict_mode)
    user_prompt = _build_user_prompt(company_name, confidence, claim_catalog)
    try:
        response = llm_client.chat_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            prompt_name="generate_outreach_email_strict" if strict_mode else "generate_outreach_email",
            temperature=0.35 if confidence == "high" else 0.4 if confidence == "medium" else 0.45,
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
        )

    return _normalize_email_output(response, confidence, claim_catalog)


def build_claim_catalog(
    hiring_signal_brief: dict[str, object],
    competitor_gap_brief: dict[str, object],
) -> list[dict[str, Any]]:
    catalog: list[dict[str, Any]] = []
    for signal in hiring_signal_brief.get("signals", []):
        if not isinstance(signal, dict):
            continue
        signal_name = str(signal.get("signal", ""))
        signal_confidence = float(signal.get("confidence", 0.0))
        if signal_name == "leadership_change" and signal_confidence < 0.5:
            continue
        value = signal.get("value", {})
        if signal_name == "funding_event":
            catalog.append(
                {
                    "id": "funding_event",
                    "type": "funding",
                    "confidence": signal_confidence,
                    "statement": f"{value['round']} on {value['date']} ({value['days_since_event']} days ago)",
                }
            )
        elif signal_name == "job_post_velocity":
            catalog.append(
                {
                    "id": "job_post_velocity",
                    "type": "hiring",
                    "confidence": signal_confidence,
                    "statement": (
                        f"Open roles moved from {value['open_roles_60_days_ago']} to "
                        f"{value['open_roles_current']} in 60 days."
                    ),
                }
            )
        elif signal_name == "layoffs":
            evidence = signal.get("evidence", [])
            if evidence:
                catalog.append(
                    {
                        "id": "layoffs",
                        "type": "hiring",
                        "confidence": signal_confidence,
                        "statement": str(evidence[0]),
                    }
                )

    ai_signal = hiring_signal_brief.get("ai_maturity_score", {})
    if isinstance(ai_signal, dict):
        catalog.append(
            {
                "id": "ai_maturity",
                "type": "ai_maturity",
                "confidence": float(ai_signal.get("confidence", 0.0)),
                "statement": f"AI maturity score is {ai_signal.get('value', 0)}.",
            }
        )

    primary_segment_match = str(hiring_signal_brief.get("primary_segment_match", "")).strip()
    segment_confidence = float(hiring_signal_brief.get("segment_confidence", 0.0) or 0.0)
    if primary_segment_match:
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
                "id": "peer_average_ai_maturity",
                "type": "competitor_gap",
                "confidence": float(competitor_gap_brief.get("confidence", 0.0)),
                "statement": (
                    f"Peer average AI maturity is {competitor_gap_brief.get('peer_average_ai_maturity', 0)} "
                    f"while the target is {competitor_gap_brief.get('target_ai_maturity', 0)}."
                ),
            }
        )
        for index, practice in enumerate(competitor_gap_brief.get("top_quartile_practices", [])[:3], start=1):
            catalog.append(
                {
                    "id": f"top_practice_{index}",
                    "type": "competitor_gap",
                    "confidence": float(competitor_gap_brief.get("confidence", 0.0)),
                    "statement": f"Top-quartile practice: {practice}.",
                }
            )
        for index, finding in enumerate(competitor_gap_brief.get("gap_findings", [])[:2], start=1):
            if not isinstance(finding, dict):
                continue
            catalog.append(
                {
                    "id": f"gap_finding_{index}",
                    "type": "competitor_gap",
                    "confidence": 0.8 if finding.get("confidence") == "high" else 0.6,
                    "statement": f"Gap finding: {finding.get('practice')}. Prospect state: {finding.get('prospect_state')}",
                }
            )

    return [claim for claim in catalog if claim["statement"]]


def _build_system_prompt(confidence_level: str, strict_mode: bool) -> str:
    tone_rule = {
        "high": "Use assertive, specific language, but only for claims directly supported by the provided signals.",
        "medium": "Use cautious, suggestive language such as 'it looks like' or 'we may be seeing'.",
        "low": "Use exploratory, question-based language and avoid hard claims.",
    }[confidence_level]
    strict_instruction = (
        "You are in strict repair mode. Use no more than two claims, keep the language conservative, and prefer questions."
        if strict_mode
        else "Keep the note concise and executive-level."
    )
    return (
        "You are generating B2B outreach for Tenacious via SignalForge. "
        "Never fabricate or infer any fact not listed in the provided claims. "
        "Reference only the available structured claims. "
        "If unsure, ask instead of asserting. "
        "Follow the Tenacious style guide: be direct, grounded, honest, professional, and non-condescending. "
        "Subject lines must start with Request, Question, Context, or Follow-up and stay under 60 characters. "
        "Keep the body under 120 words and avoid offshore-vendor cliches. "
        f"{tone_rule} {strict_instruction} "
        "Return JSON with keys: subject, body, claims_used. "
        "claims_used must be a list of claim ids selected from the allowed claims."
    )


def _build_user_prompt(
    company_name: str,
    confidence_level: str,
    claim_catalog: list[dict[str, Any]],
) -> str:
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
        "Write one outreach email under 120 words. "
        "Use only the allowed claims. "
        "If confidence is low, make the body question-led and exploratory. "
        "If segment match is abstain or confidence is below 0.6, avoid a segment-specific pitch."
    )


def _normalize_email_output(
    response: LLMClientResponse,
    confidence_level: str,
    claim_catalog: list[dict[str, Any]],
) -> dict[str, object]:
    content = response.content
    claims_used = content.get("claims_used", [])
    if not isinstance(claims_used, list):
        claims_used = []
    return {
        "subject": str(content.get("subject", "")).strip(),
        "body": str(content.get("body", "")).strip(),
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
) -> dict[str, object]:
    company_name = str(hiring_signal_brief.get("company_name", "this company"))
    confidence = confidence_level or compute_global_confidence(hiring_signal_brief)
    company = {"company_name": company_name}
    fallback = generate_fallback_email(company, hiring_signal_brief, competitor_gap_brief)
    return {
        "subject": fallback["subject"],
        "body": fallback["body"],
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
        "prompt_snapshot": {"fallback_reason": reason},
    }
