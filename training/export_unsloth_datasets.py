from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
BENCH_ROOT = REPO_ROOT / "tenacious_bench_v0.1"
OUT_ROOT = REPO_ROOT / "training_data" / "unsloth"

NORMALIZED_DIMENSIONS = {
    "CTO_sensitivity": "cto_sensitivity",
    "signal_over-claiming": "signal_over_claiming",
    "gap_over-claiming": "gap_over_claiming",
    "multi_llm_synthesis": "multi-llm-synthesis",
}


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
    output = dict(task["candidate_output"])
    if task["task_type"] == "qualification_decision":
        output["qualification_status"] = "qualified"
        output["intent_level"] = "high"
        output["next_action"] = "share_booking_link"
    elif task["task_type"] == "channel_decision":
        output["primary_channel"] = "sms"
        output["allowed_channels_after_reply"] = ["sms", "whatsapp", "calendar"]
    return output


def task_prompt(task: dict[str, Any], *, normalize_dimensions: bool) -> list[dict[str, str]]:
    dimension = normalize_dimension(task["dimension"]) if normalize_dimensions else task["dimension"]
    return [
        {
            "role": "system",
            "content": "Score and improve Tenacious outbound behavior using only grounded evidence.",
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


def normalize_dimension(name: str) -> str:
    if name in NORMALIZED_DIMENSIONS:
        return NORMALIZED_DIMENSIONS[name]
    return name.lower().replace("-", "_")


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


def export_split(split: str, *, normalize_dimensions: bool) -> dict[str, Any]:
    rows = []
    for task in load_tasks(split):
        messages = task_prompt(task, normalize_dimensions=normalize_dimensions)
        chosen = task["candidate_output"]
        rejected = build_rejected_email(task) if task["task_type"] == "email_grounding" else build_rejected_structured(task)
        dimension = normalize_dimension(task["dimension"]) if normalize_dimensions else task["dimension"]
        prompt_text = render_messages(messages)
        chosen_text = render_output(task["task_type"], chosen)
        rejected_text = render_output(task["task_type"], rejected)
        rows.append(
            {
                "task_id": task["task_id"],
                "split": split,
                "dimension": dimension,
                "task_type": task["task_type"],
                "source_mode": task["source_mode"],
                "prompt": prompt_text,
                "prompt_messages": messages,
                "chosen": chosen_text,
                "rejected": rejected_text,
                "chosen_structured": chosen,
                "rejected_structured": rejected,
                "sft_text": render_chatml(messages, chosen_text),
                "chosen_chatml": render_chatml(messages, chosen_text),
                "rejected_chatml": render_chatml(messages, rejected_text),
                "metadata": {
                    "week10_evidence_refs": task["metadata"].get("week10_evidence_refs", []),
                    "probe_refs": task["metadata"].get("probe_refs", []),
                },
            }
        )

    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    out_path = OUT_ROOT / f"preferences_{split}.jsonl"
    out_path.write_text("\n".join(json.dumps(row, ensure_ascii=True) for row in rows) + "\n")
    return {"split": split, "rows": len(rows), "output_path": str(out_path)}


def main() -> None:
    manifest = {
        "format": "unsloth_preference_bundle_v1",
        "splits": [
            export_split("train", normalize_dimensions=True),
            export_split("dev", normalize_dimensions=True),
            export_split("held_out", normalize_dimensions=True),
        ],
        "notes": [
            "prompt/chosen/rejected are plain strings for DPO/ORPO/SimPO trainers.",
            "sft_text is a ChatML-style text field for optional warm-start SFT on chosen responses.",
            "held_out export exists for final sealed evaluation and should stay untouched during tuning.",
        ],
    }
    manifest_path = OUT_ROOT / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
