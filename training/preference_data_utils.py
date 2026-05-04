from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


NORMALIZED_DIMENSIONS = {
    "CTO_sensitivity": "cto_sensitivity",
    "signal_over-claiming": "signal_over_claiming",
    "gap_over-claiming": "gap_over_claiming",
    "multi_llm_synthesis": "multi-llm-synthesis",
}


def load_tasks(bench_root: Path, split: str) -> list[dict[str, Any]]:
    path = bench_root / split / "tasks.jsonl"
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def normalize_dimension(name: str) -> str:
    if name in NORMALIZED_DIMENSIONS:
        return NORMALIZED_DIMENSIONS[name]
    return name.lower().replace("-", "_")


def output_contract(task_type: str) -> str:
    if task_type == "email_grounding":
        return (
            "Return only the final outbound email in exactly this format: "
            "Subject: <text> newline Body: <text>. Do not include analysis, "
            "scores, bullets, or JSON."
        )
    if task_type == "qualification_decision":
        return "Return only compact JSON with exactly these keys: qualification_status, intent_level, next_action."
    if task_type == "channel_decision":
        return "Return only compact JSON with exactly these keys: primary_channel, allowed_channels_after_reply."
    return "Return only the final answer with no explanation."


def task_prompt(task: dict[str, Any], *, normalize_dimensions: bool) -> list[dict[str, str]]:
    dimension = normalize_dimension(task["dimension"]) if normalize_dimensions else task["dimension"]
    return [
        {
            "role": "system",
            "content": (
                "Using only grounded evidence, produce the best final Tenacious response for this task. "
                "Do not explain your reasoning. "
                f"{output_contract(task['task_type'])}"
            ),
        },
        {
            "role": "user",
            "content": json.dumps(
                {
                    "dimension": dimension,
                    "task_type": task["task_type"],
                    "input": task["input"],
                    "ground_truth": task["ground_truth"],
                },
                sort_keys=True,
            ),
        },
    ]


def _replace_case_insensitive(text: str, old: str, new: str) -> str:
    return re.sub(re.escape(old), new, text, flags=re.IGNORECASE)


def _truncate_at_sentence(text: str, max_words: int) -> str:
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]).rstrip(".,;:") + "."


def _remove_required_signal(body: str, required_signals: list[str]) -> str:
    updated = body
    for signal in required_signals:
        candidate = _replace_case_insensitive(updated, signal, "the account")
        if candidate != updated:
            return candidate
    return updated


def _calibration_flip(text: str) -> str:
    replacements = [
        ("I do not want to", "I can"),
        ("I don't want to", "I can"),
        ("I want to confirm whether", "I can see that"),
        ("I only see directional public evidence", "The public evidence is clear"),
        ("it looks more like", "it is clearly"),
        ("might", "will"),
        ("may", "will"),
        ("could", "will"),
        ("appears", "is"),
        ("seems", "is"),
        ("not confident enough", "confident"),
        ("do not want to overstate", "can say directly"),
        ("don't want to overstate", "can say directly"),
    ]
    updated = text
    for old, new in replacements:
        updated = _replace_case_insensitive(updated, old, new)
    return updated


def _strong_overclaiming_email(chosen: dict[str, str]) -> dict[str, str]:
    subject = str(chosen.get("subject", "Request: Quick chat")).strip()
    body = str(chosen.get("body", "")).strip()
    mutated_body = _calibration_flip(body)
    if "?" in mutated_body:
        mutated_body = mutated_body.replace("?", ".", 1)
    mutated_body = (
        f"{mutated_body} We have world-class engineers and you clearly need offshore capacity."
    ).strip()
    mutated_subject = subject.replace("Question:", "Quick:").replace("Context:", "Quick:")
    if mutated_subject == subject:
        mutated_subject = f"Quick: {subject}"
    return {"subject": mutated_subject, "body": mutated_body}


def _constraint_break_email(task: dict[str, Any], chosen: dict[str, str]) -> dict[str, str]:
    ground_truth = task.get("ground_truth", {})
    subject = str(chosen.get("subject", "Request: Quick chat")).strip()
    body = str(chosen.get("body", "")).strip()
    mutated_subject = subject
    mutated_body = body

    if ground_truth.get("required_signal_strings"):
        mutated_body = _remove_required_signal(mutated_body, list(ground_truth["required_signal_strings"]))
    elif ground_truth.get("require_question_mark"):
        mutated_body = mutated_body.replace("?", ".", 1)
    elif ground_truth.get("require_no_dollar_sign"):
        mutated_body = f"{mutated_body} A $45k pilot should be easy to approve."
    elif ground_truth.get("max_body_words"):
        padding = (
            " I can also send a quick pricing outline, benchmark notes, and a draft rollout plan "
            "so we can move faster if the team wants an external partner."
        )
        mutated_body = f"{mutated_body}{padding}"
    else:
        mutated_body = _calibration_flip(mutated_body)

    if ground_truth.get("allowed_subject_prefixes"):
        allowed = tuple(prefix.lower() for prefix in ground_truth["allowed_subject_prefixes"])
        if mutated_subject.lower().startswith(allowed):
            mutated_subject = mutated_subject.replace("Question:", "Quick:").replace("Context:", "Quick:")
            mutated_subject = mutated_subject.replace("Request:", "Quick:").replace("Follow-up:", "Quick:")
            if mutated_subject == subject:
                mutated_subject = f"Quick: {subject}"

    return {"subject": mutated_subject.strip(), "body": mutated_body.strip()}


def _wordy_confident_email(task: dict[str, Any], chosen: dict[str, str]) -> dict[str, str]:
    ground_truth = task.get("ground_truth", {})
    subject = str(chosen.get("subject", "Request: Quick chat")).strip()
    body = str(chosen.get("body", "")).strip()
    mutated_body = _calibration_flip(body)
    mutated_body = _remove_required_signal(mutated_body, list(ground_truth.get("required_signal_strings", [])))
    if ground_truth.get("require_question_mark") and "?" in mutated_body:
        mutated_body = mutated_body.replace("?", ".", 1)
    max_words = int(ground_truth.get("max_body_words", 120))
    padding = (
        " I can also outline the likely delivery model, hiring benchmark, migration path, "
        "and near-term operating cadence because the need already looks established."
    )
    mutated_body = _truncate_at_sentence(f"{mutated_body}{padding}", max(max_words + 20, max_words))
    if ground_truth.get("require_no_dollar_sign"):
        mutated_body = f"{mutated_body} A $25k starter engagement would be reasonable."
    mutated_subject = subject.replace("Question:", "Request:").replace("Context:", "Request:")
    return {"subject": mutated_subject.strip(), "body": mutated_body.strip()}


def _qualification_negative_candidates(chosen: dict[str, Any]) -> list[dict[str, Any]]:
    status = chosen.get("qualification_status")
    is_partial = status == "partial"
    candidates = [
        {
            "rejection_strategy": "qualification_aggressive",
            "rejected": {
                "qualification_status": "qualified",
                "intent_level": "high",
                "next_action": "share_booking_link",
            },
        },
        {
            "rejection_strategy": "qualification_conservative",
            "rejected": (
                {
                    "qualification_status": "partial",
                    "intent_level": "high",
                    "next_action": "share_booking_link",
                }
                if is_partial
                else {
                    "qualification_status": "partial",
                    "intent_level": "medium",
                    "next_action": "ask_follow_up_question",
                }
            ),
        },
        {
            "rejection_strategy": "qualification_mixed_signal",
            "rejected": (
                {
                    "qualification_status": "qualified",
                    "intent_level": "medium",
                    "next_action": "ask_follow_up_question",
                }
                if is_partial
                else {
                    "qualification_status": "partial",
                    "intent_level": "high",
                    "next_action": "share_booking_link",
                }
            ),
        },
    ]
    return candidates


def _channel_negative_candidates(chosen: dict[str, Any]) -> list[dict[str, Any]]:
    allowed = list(chosen.get("allowed_channels_after_reply", []))
    broadened = list(allowed)
    for candidate in ["sms", "whatsapp", "calendar"]:
        if candidate not in broadened:
            broadened.append(candidate)
    narrowed = ["calendar"] if allowed == ["email"] else ["email"]
    candidates = [
        {
            "rejection_strategy": "channel_primary_mismatch",
            "rejected": {
                "primary_channel": "sms",
                "allowed_channels_after_reply": broadened,
            },
        },
        {
            "rejection_strategy": "channel_over_broad_followup",
            "rejected": {
                "primary_channel": chosen.get("primary_channel", "email"),
                "allowed_channels_after_reply": broadened,
            },
        },
        {
            "rejection_strategy": "channel_over_narrow_followup",
            "rejected": {
                "primary_channel": chosen.get("primary_channel", "email"),
                "allowed_channels_after_reply": narrowed,
            },
        },
    ]
    return candidates


def build_rejected_candidates(task: dict[str, Any]) -> list[dict[str, Any]]:
    chosen = dict(task["candidate_output"])
    if task["task_type"] == "email_grounding":
        candidates = [
            {
                "rejection_strategy": "strong_overclaiming",
                "rejected": _strong_overclaiming_email(chosen),
            },
            {
                "rejection_strategy": "constraint_break",
                "rejected": _constraint_break_email(task, chosen),
            },
            {
                "rejection_strategy": "wordy_overconfident",
                "rejected": _wordy_confident_email(task, chosen),
            },
        ]
    else:
        if task["task_type"] == "qualification_decision":
            candidates = _qualification_negative_candidates(chosen)
        elif task["task_type"] == "channel_decision":
            candidates = _channel_negative_candidates(chosen)
        else:
            candidates = []

    unique: list[dict[str, Any]] = []
    seen: set[str] = set()
    chosen_key = json.dumps(chosen, ensure_ascii=True, sort_keys=True)
    for candidate in candidates:
        rejected = candidate["rejected"]
        rejected_key = json.dumps(rejected, ensure_ascii=True, sort_keys=True)
        if rejected_key == chosen_key or rejected_key in seen:
            continue
        seen.add(rejected_key)
        unique.append(candidate)
    return unique


def build_rejected_email(task: dict[str, Any]) -> dict[str, str]:
    chosen = dict(task["candidate_output"])
    return _strong_overclaiming_email(chosen)


def build_rejected_structured(task: dict[str, Any]) -> dict[str, Any]:
    candidates = build_rejected_candidates(task)
    if not candidates:
        return dict(task["candidate_output"])
    return dict(candidates[0]["rejected"])


def build_preference_rows(
    tasks: list[dict[str, Any]],
    *,
    split: str | None = None,
    normalize_dimensions: bool,
    render_plain_strings: bool,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for task in tasks:
        dimension = normalize_dimension(task["dimension"]) if normalize_dimensions else task["dimension"]
        messages = task_prompt(task, normalize_dimensions=normalize_dimensions)
        chosen = dict(task["candidate_output"])
        for index, candidate in enumerate(build_rejected_candidates(task), start=1):
            row = {
                "task_id": task["task_id"],
                "preference_pair_id": f"{task['task_id']}::{candidate['rejection_strategy']}::{index}",
                "dimension": dimension,
                "task_type": task["task_type"],
                "source_mode": task["source_mode"],
                "rejection_strategy": candidate["rejection_strategy"],
                "prompt_messages": messages,
                "chosen_structured": chosen,
                "rejected_structured": candidate["rejected"],
                "metadata": {
                    "week10_evidence_refs": task["metadata"].get("week10_evidence_refs", []),
                    "probe_refs": task["metadata"].get("probe_refs", []),
                },
            }
            if split is not None:
                row["split"] = split
            if render_plain_strings:
                row["prompt"] = render_messages(messages)
                row["chosen"] = render_output(task["task_type"], chosen)
                row["rejected"] = render_output(task["task_type"], candidate["rejected"])
                row["sft_text"] = render_chatml(messages, row["chosen"])
                row["chosen_chatml"] = render_chatml(messages, row["chosen"])
                row["rejected_chatml"] = render_chatml(messages, row["rejected"])
            else:
                row["prompt"] = messages
                row["chosen"] = chosen
                row["rejected"] = candidate["rejected"]
            rows.append(row)
    return dedupe_preference_rows(rows)


def dedupe_preference_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in rows:
        key = json.dumps(
            {
                "task_id": row["task_id"],
                "prompt": row["prompt"],
                "chosen": row["chosen"],
                "rejected": row["rejected"],
            },
            ensure_ascii=True,
            sort_keys=True,
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    return deduped


def render_messages(messages: list[dict[str, str]]) -> str:
    blocks = []
    for message in messages:
        role = str(message["role"]).strip().upper()
        content = str(message["content"]).strip()
        blocks.append(f"{role}:\n{content}")
    return "\n\n".join(blocks)


def render_output(task_type: str, output: dict[str, Any]) -> str:
    if task_type == "email_grounding":
        subject = str(output.get("subject", "")).strip()
        body = str(output.get("body", "")).strip()
        return f"Subject: {subject}\nBody: {body}".strip()
    return json.dumps(output, ensure_ascii=True, sort_keys=True)


def render_chatml(messages: list[dict[str, str]], assistant_text: str) -> str:
    parts = []
    for message in messages:
        parts.append(f"<|im_start|>{message['role']}\n{message['content']}<|im_end|>")
    parts.append(f"<|im_start|>assistant\n{assistant_text}<|im_end|>")
    return "\n".join(parts)
