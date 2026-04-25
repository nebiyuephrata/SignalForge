from __future__ import annotations

from pathlib import Path

from agent.core.orchestrator import SignalForgeOrchestrator
from agent.utils.trace_logger import write_json


REPO_ROOT = Path(__file__).resolve().parents[1]


def run_verified_execution(
    *,
    company_name: str = "Northstar Lending",
    reply_text: str | None = None,
) -> dict[str, object]:
    orchestrator = SignalForgeOrchestrator()
    result = orchestrator.run_single_prospect(company_name=company_name, reply_text=reply_text)
    email_debug = result["email_debug"]
    prompt_snapshot = email_debug.get("prompt_snapshot", {})
    fallback_reason = prompt_snapshot.get("fallback_reason")
    fallback_reason_detail = prompt_snapshot.get("fallback_reason_detail", {})
    attempted_trace_id = fallback_reason_detail.get("trace_id") or result.get("trace_id")
    attempted_trace_url = fallback_reason_detail.get("trace_url") or result.get("trace_url")
    model_attempts = fallback_reason_detail.get("model_attempts", [])

    artifact = {
        "executed_at": result["hiring_signal_brief"]["generated_at"],
        "input": {
            "company_name": company_name,
            "reply_text": reply_text,
        },
        "signals": {
            "summary": result["hiring_signal_brief"]["summary"],
            "overall_confidence": result["hiring_signal_brief"]["overall_confidence"],
            "uncertainty_flags": result["hiring_signal_brief"].get("uncertainty_flags", []),
            "data_sources_checked": result["hiring_signal_brief"]["data_sources_checked"],
        },
        "confidence": result["confidence_assessment"],
        "generated_message": result["email"],
        "fallback": {
            "occurred": email_debug.get("model") == "deterministic-fallback",
            "reason": fallback_reason,
            "explanation": _fallback_explanation(
                email_debug=email_debug,
                fallback_reason=fallback_reason,
                fallback_reason_detail=fallback_reason_detail,
            ),
        },
        "trace": {
            "final_model": email_debug.get("model"),
            "trace_id": result.get("trace_id"),
            "trace_url": result.get("trace_url"),
            "attempted_trace_id": attempted_trace_id,
            "attempted_trace_url": attempted_trace_url,
            "prompt_name": fallback_reason_detail.get("prompt_name"),
            "model_attempts": model_attempts,
            "transport_attempted": bool(model_attempts),
        },
        "validation": result["claim_validation"],
        "channel_plan": result["channel_plan"],
    }
    write_json(str(REPO_ROOT / "outputs" / "verified_run.json"), artifact)
    return artifact


def _fallback_explanation(
    *,
    email_debug: dict[str, object],
    fallback_reason: str | None,
    fallback_reason_detail: dict[str, object],
) -> str:
    if email_debug.get("model") != "deterministic-fallback":
        return "No fallback occurred because the live model response completed successfully."
    if fallback_reason == "llm_error":
        error = fallback_reason_detail.get("error", "unknown LLM error")
        if fallback_reason_detail.get("model_attempts"):
            return f"Fallback occurred after live OpenRouter transport attempts failed: {error}"
        return f"Fallback occurred before transport because the OpenRouter client could not start a live request: {error}"
    if fallback_reason == "weak_confidence_default":
        return "Fallback occurred by design because the confidence calibration layer marked the prospect as low confidence."
    return f"Fallback occurred for deterministic safety with reason `{fallback_reason}`."


if __name__ == "__main__":
    artifact = run_verified_execution()
    print(f"verified_run.json written with fallback={artifact['fallback']['occurred']}")
