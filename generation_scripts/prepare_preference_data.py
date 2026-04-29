from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
BENCH_ROOT = REPO_ROOT / "tenacious_bench_v0.1"
OUT_PATH = REPO_ROOT / "training_data" / "path_b_preferences.jsonl"

BANNED_STYLE_PHRASES = [
    "clearly scaling aggressively",
    "world-class team",
    "rockstar engineers",
    "you need offshore capacity",
]


def load_tasks(split: str) -> list[dict[str, Any]]:
    path = BENCH_ROOT / split / "tasks.jsonl"
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def build_rejected_email(task: dict[str, Any]) -> dict[str, str]:
    output = task["candidate_output"]
    subject = str(output.get("subject", "Request: Quick chat"))
    body = str(output.get("body", ""))
    mutated = body
    if "?" in mutated:
        mutated = mutated.replace("?", ".")
    if "not confident enough" in mutated.lower():
        mutated = mutated.replace("not confident enough", "clearly")
    if "overstate" in mutated.lower():
        mutated = mutated.replace("don't want to overstate", "we know")
    mutated = f"{mutated} We have world-class engineers and you clearly need offshore capacity."
    return {"subject": subject.replace("Question:", "Quick:").replace("Context:", "Quick:"), "body": mutated}


def build_rejected_structured(task: dict[str, Any]) -> dict[str, Any]:
    output = task["candidate_output"]
    rejected = dict(output)
    if task["task_type"] == "qualification_decision":
        rejected["qualification_status"] = "qualified"
        rejected["intent_level"] = "high"
        rejected["next_action"] = "share_booking_link"
    elif task["task_type"] == "channel_decision":
        rejected["primary_channel"] = "sms"
        rejected["allowed_channels_after_reply"] = ["sms", "whatsapp", "calendar"]
    return rejected


def task_prompt(task: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": "Score and improve Tenacious outbound behavior using only grounded evidence.",
        },
        {
            "role": "user",
            "content": json.dumps(
                {
                    "dimension": task["dimension"],
                    "task_type": task["task_type"],
                    "input": task["input"],
                    "ground_truth": task["ground_truth"],
                },
                sort_keys=True,
            ),
        },
    ]


def main() -> None:
    tasks = load_tasks("train")
    preference_rows = []
    for task in tasks:
        chosen = task["candidate_output"]
        rejected = build_rejected_email(task) if task["task_type"] == "email_grounding" else build_rejected_structured(task)
        preference_rows.append(
            {
                "task_id": task["task_id"],
                "dimension": task["dimension"],
                "task_type": task["task_type"],
                "source_mode": task["source_mode"],
                "prompt": task_prompt(task),
                "chosen": chosen,
                "rejected": rejected,
                "metadata": {
                    "week10_evidence_refs": task["metadata"].get("week10_evidence_refs", []),
                    "probe_refs": task["metadata"].get("probe_refs", []),
                },
            }
        )

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text("\n".join(json.dumps(row, ensure_ascii=True) for row in preference_rows) + "\n")
    print(json.dumps({"preference_pairs": len(preference_rows), "output_path": str(OUT_PATH)}, indent=2))


if __name__ == "__main__":
    main()
