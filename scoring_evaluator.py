from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


"""
Mechanical scorer for Tenacious-Bench v0.1.

Calibration:
- A score near 1.0 means the candidate output satisfies all required hooks for that
  dimension and avoids the known failure patterns.
- A score around 0.5 means the output is partially compliant but misses at least one
  key rubric condition.
- A score of 0.0 means the output violates a hard constraint, is malformed, or
  mismatches the benchmark ground truth.

Example task files that this evaluator is meant to score are committed in:
- tenacious_bench_v0.1/train/tasks.jsonl
- tenacious_bench_v0.1/dev/tasks.jsonl
- tenacious_bench_v0.1/held_out/tasks.jsonl
"""


@dataclass
class DimensionResult:
    name: str
    score: float
    max_score: float
    detail: str


def _coerce_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {}


def _fail_closed(
    task: dict[str, Any],
    detail: str,
    *,
    agent_output: Any = None,
) -> dict[str, Any]:
    return {
        "task_id": task.get("task_id", "unknown-task"),
        "dimension": task.get("dimension", "unknown-dimension"),
        "task_type": task.get("task_type", "unknown-task-type"),
        "score": 0.0,
        "pass_threshold": float(task.get("scoring_rubric", {}).get("pass_threshold", 1.0)),
        "passed": False,
        "error": detail,
        "agent_output_used": agent_output is not None,
        "dimension_results": [],
    }


def load_tasks(path: Path) -> list[dict[str, Any]]:
    if path.suffix == ".jsonl":
        return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    payload = json.loads(path.read_text())
    if isinstance(payload, list):
        return payload
    return [payload]


def evaluate_task(task: dict[str, Any], agent_output: dict[str, Any] | None = None) -> dict[str, Any]:
    try:
        task_type = str(task["task_type"])
        if task_type == "email_grounding":
            return evaluate_email_grounding(task, agent_output=agent_output)
        if task_type == "qualification_decision":
            return evaluate_qualification(task, agent_output=agent_output)
        if task_type == "channel_decision":
            return evaluate_channel(task, agent_output=agent_output)
        return _fail_closed(task, f"Unsupported task_type: {task_type}", agent_output=agent_output)
    except KeyError as exc:
        return _fail_closed(task, f"Missing required task field: {exc}", agent_output=agent_output)
    except Exception as exc:  # pragma: no cover - defensive guard for malformed task rows
        return _fail_closed(task, f"Evaluator exception: {exc}", agent_output=agent_output)


def evaluate_email_grounding(task: dict[str, Any], agent_output: dict[str, Any] | None = None) -> dict[str, Any]:
    output = _coerce_dict(agent_output) or _coerce_dict(task.get("candidate_output"))
    ground_truth = _coerce_dict(task.get("ground_truth"))
    rubric = _coerce_dict(task.get("scoring_rubric"))
    if not output:
        return _fail_closed(task, "Malformed or missing email output.", agent_output=agent_output)

    body = f"{output.get('subject', '')}\n{output.get('body', '')}".lower()

    results: list[DimensionResult] = []
    required_strings = [item.lower() for item in ground_truth.get("required_signal_strings", [])]
    matched_required = sum(1 for item in required_strings if item in body)
    required_score = 1.0 if not required_strings else matched_required / len(required_strings)
    results.append(
        DimensionResult(
            name="grounded_language",
            score=required_score,
            max_score=1.0,
            detail=f"matched {matched_required} of {len(required_strings)} required signal strings",
        )
    )

    banned_phrases = [item.lower() for item in ground_truth.get("banned_phrases", [])]
    banned_hits = [item for item in banned_phrases if item in body]
    banned_score = 1.0 if not banned_hits else 0.0
    results.append(
        DimensionResult(
            name="tone_safety",
            score=banned_score,
            max_score=1.0,
            detail="no banned phrases found" if not banned_hits else f"banned phrases found: {', '.join(banned_hits)}",
        )
    )

    require_question_mark = bool(ground_truth.get("require_question_mark", False))
    require_calendar_link = bool(ground_truth.get("require_calendar_link", False))
    question_ok = ("?" in output.get("body", "")) if require_question_mark else True
    calendar_ok = ("cal.com" in body) if require_calendar_link else ("cal.com" not in body)
    confidence_score = 1.0 if question_ok and calendar_ok else 0.0
    results.append(
        DimensionResult(
            name="confidence_alignment",
            score=confidence_score,
            max_score=1.0,
            detail=f"question_ok={question_ok}, calendar_ok={calendar_ok}",
        )
    )

    allowed_subject_prefixes = [item.lower() for item in ground_truth.get("allowed_subject_prefixes", [])]
    subject = str(output.get("subject", ""))
    subject_lower = subject.lower()
    subject_ok = True if not allowed_subject_prefixes else any(subject_lower.startswith(prefix) for prefix in allowed_subject_prefixes)
    max_body_words = int(ground_truth.get("max_body_words", 10_000))
    body_word_count = len(str(output.get("body", "")).split())
    word_count_ok = body_word_count <= max_body_words
    directness_score = 1.0 if subject_ok and word_count_ok else 0.0
    results.append(
        DimensionResult(
            name="directness_constraints",
            score=directness_score,
            max_score=1.0,
            detail=f"subject_ok={subject_ok}, body_word_count={body_word_count}, max_body_words={max_body_words}",
        )
    )

    require_handoff_phrase = ground_truth.get("require_handoff_phrase")
    require_no_dollar_sign = bool(ground_truth.get("require_no_dollar_sign", False))
    handoff_ok = True if not require_handoff_phrase else str(require_handoff_phrase).lower() in body
    dollar_ok = ("$" not in body) if require_no_dollar_sign else True
    routing_score = 1.0 if handoff_ok and dollar_ok else 0.0
    results.append(
        DimensionResult(
            name="routing_safety",
            score=routing_score,
            max_score=1.0,
            detail=f"handoff_ok={handoff_ok}, dollar_ok={dollar_ok}",
        )
    )

    weighted_score = 0.0
    total_weight = 0.0
    weights = {item["name"]: float(item["weight"]) for item in rubric.get("dimensions", [])}
    for result in results:
        weight = weights.get(result.name, 0.0)
        weighted_score += result.score * weight
        total_weight += weight
    final_score = weighted_score / total_weight if total_weight else 0.0

    return format_result(task, results, final_score, float(rubric.get("pass_threshold", 1.0)))


def evaluate_qualification(task: dict[str, Any], agent_output: dict[str, Any] | None = None) -> dict[str, Any]:
    output = _coerce_dict(agent_output) or _coerce_dict(task.get("candidate_output"))
    expected = _coerce_dict(task.get("ground_truth"))
    rubric = _coerce_dict(task.get("scoring_rubric"))
    if not output:
        return _fail_closed(task, "Malformed or missing qualification output.", agent_output=agent_output)

    results = [
        DimensionResult(
            name="qualification_status_match",
            score=1.0 if output.get("qualification_status") == expected.get("qualification_status") else 0.0,
            max_score=1.0,
            detail=f"observed={output.get('qualification_status')} expected={expected.get('qualification_status')}",
        ),
        DimensionResult(
            name="intent_match",
            score=1.0 if output.get("intent_level") == expected.get("intent_level") else 0.0,
            max_score=1.0,
            detail=f"observed={output.get('intent_level')} expected={expected.get('intent_level')}",
        ),
        DimensionResult(
            name="action_match",
            score=1.0 if output.get("next_action") == expected.get("next_action") else 0.0,
            max_score=1.0,
            detail=f"observed={output.get('next_action')} expected={expected.get('next_action')}",
        ),
    ]
    weights = {item["name"]: float(item["weight"]) for item in rubric.get("dimensions", [])}
    final_score = sum(result.score * weights.get(result.name, 0.0) for result in results)
    return format_result(task, results, final_score, float(rubric.get("pass_threshold", 1.0)))


def evaluate_channel(task: dict[str, Any], agent_output: dict[str, Any] | None = None) -> dict[str, Any]:
    output = _coerce_dict(agent_output) or _coerce_dict(task.get("candidate_output"))
    expected = _coerce_dict(task.get("ground_truth"))
    rubric = _coerce_dict(task.get("scoring_rubric"))
    if not output:
        return _fail_closed(task, "Malformed or missing channel output.", agent_output=agent_output)

    results = [
        DimensionResult(
            name="primary_channel_match",
            score=1.0 if output.get("primary_channel") == expected.get("primary_channel") else 0.0,
            max_score=1.0,
            detail=f"observed={output.get('primary_channel')} expected={expected.get('primary_channel')}",
        ),
        DimensionResult(
            name="allowed_channels_match",
            score=1.0 if output.get("allowed_channels_after_reply") == expected.get("allowed_channels_after_reply") else 0.0,
            max_score=1.0,
            detail="exact list match required",
        ),
    ]
    weights = {item["name"]: float(item["weight"]) for item in rubric.get("dimensions", [])}
    final_score = sum(result.score * weights.get(result.name, 0.0) for result in results)
    return format_result(task, results, final_score, float(rubric.get("pass_threshold", 1.0)))


def format_result(
    task: dict[str, Any],
    results: list[DimensionResult],
    final_score: float,
    pass_threshold: float,
) -> dict[str, Any]:
    return {
        "task_id": task["task_id"],
        "dimension": task["dimension"],
        "task_type": task["task_type"],
        "score": round(final_score, 4),
        "pass_threshold": pass_threshold,
        "passed": final_score >= pass_threshold,
        "dimension_results": [
            {
                "name": item.name,
                "score": item.score,
                "max_score": item.max_score,
                "detail": item.detail,
            }
            for item in results
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Score Tenacious-Bench tasks with a machine-verifiable evaluator.")
    parser.add_argument("--tasks", type=Path, required=True, help="Path to a task JSON or JSONL file.")
    args = parser.parse_args()

    tasks = load_tasks(args.tasks)
    results = [evaluate_task(task, agent_output=task.get("candidate_output")) for task in tasks]
    passed = sum(1 for result in results if result["passed"])
    payload = {
        "task_count": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "results": results,
    }
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
