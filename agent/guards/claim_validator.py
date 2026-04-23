from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Callable

from agent.llm.email_generator import build_claim_catalog
from agent.utils.trace_logger import append_jsonl_log

NUMERIC_TOKEN_PATTERN = re.compile(r"\b\d+(?:\.\d+)?(?:-\d+-\d+)?\b")


def validate_email_claims(
    email_output: dict[str, Any],
    hiring_signal_brief: dict[str, object],
    competitor_gap_brief: dict[str, object] | None = None,
    regenerate: Callable[[], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    claim_catalog = build_claim_catalog(hiring_signal_brief, competitor_gap_brief or {})
    allowed_claim_ids = {claim["id"] for claim in claim_catalog}
    allowed_numeric_tokens = _extract_numeric_tokens(" ".join(claim["statement"] for claim in claim_catalog))

    claims_used = email_output.get("claims_used", [])
    if not isinstance(claims_used, list):
        claims_used = []
    unsupported_claim_ids = [claim_id for claim_id in claims_used if claim_id not in allowed_claim_ids]

    body = str(email_output.get("body", ""))
    unexpected_numeric_tokens = sorted(token for token in _extract_numeric_tokens(body) if token not in allowed_numeric_tokens)
    valid = not unsupported_claim_ids and not unexpected_numeric_tokens

    report: dict[str, Any] = {
        "valid": valid,
        "unsupported_claim_ids": unsupported_claim_ids,
        "unexpected_numeric_tokens": unexpected_numeric_tokens,
        "claims_used": claims_used,
    }
    if valid:
        return report

    _log_validation_failure(email_output, report)
    if regenerate is not None:
        report["regenerated_email"] = regenerate()
    return report


def _extract_numeric_tokens(text: str) -> set[str]:
    return set(NUMERIC_TOKEN_PATTERN.findall(text))


def _log_validation_failure(email_output: dict[str, Any], report: dict[str, Any]) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    append_jsonl_log(
        str(repo_root / "logs" / "claim_validation_failures.jsonl"),
        {
            "email_output": email_output,
            "validation_report": report,
        },
    )
