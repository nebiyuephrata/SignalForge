from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from training.preference_data_utils import build_preference_rows, load_tasks

BENCH_ROOT = REPO_ROOT / "tenacious_bench_v0.1"
OUT_ROOT = REPO_ROOT / "training_data" / "unsloth"
NON_HELDOUT_SOURCE_SPLITS = ("train", "dev")
EXPORT_DEV_FRACTION = 0.2


def annotate_source_split(tasks: list[dict[str, Any]], source_split: str) -> list[dict[str, Any]]:
    annotated = []
    for task in tasks:
        copied = dict(task)
        copied["benchmark_source_split"] = source_split
        metadata = dict(task.get("metadata", {}))
        metadata["benchmark_source_split"] = source_split
        copied["metadata"] = metadata
        annotated.append(copied)
    return annotated


def load_non_heldout_tasks() -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    for split in NON_HELDOUT_SOURCE_SPLITS:
        tasks.extend(annotate_source_split(load_tasks(BENCH_ROOT, split), split))
    return tasks


def split_non_heldout_tasks(tasks: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for task in tasks:
        grouped[(task["task_type"], task["dimension"])].append(task)

    export_train: list[dict[str, Any]] = []
    export_dev: list[dict[str, Any]] = []
    split_rank = {"train": 0, "dev": 1}

    for key in sorted(grouped):
        bucket = sorted(
            grouped[key],
            key=lambda task: (
                split_rank.get(task.get("benchmark_source_split", "train"), 99),
                task["task_id"],
            ),
        )
        if len(bucket) == 1:
            export_train.extend(bucket)
            continue

        dev_count = max(1, round(len(bucket) * EXPORT_DEV_FRACTION))
        dev_count = min(dev_count, len(bucket) - 1)
        export_train.extend(bucket[:-dev_count])
        export_dev.extend(bucket[-dev_count:])

    return export_train, export_dev


def build_export_rows(tasks: list[dict[str, Any]], export_split: str) -> list[dict[str, Any]]:
    rows = build_preference_rows(
        tasks,
        split=export_split,
        normalize_dimensions=True,
        render_plain_strings=True,
    )
    for row in rows:
        source_split = ""
        for task in tasks:
            if task["task_id"] == row["task_id"]:
                source_split = str(task.get("benchmark_source_split", task.get("split", "")))
                break
        row["benchmark_source_split"] = source_split
        row["metadata"]["benchmark_source_split"] = source_split
    return rows


def write_rows(export_split: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    out_path = OUT_ROOT / f"preferences_{export_split}.jsonl"
    out_path.write_text("\n".join(json.dumps(row, ensure_ascii=True) for row in rows) + "\n")
    task_type_counts = Counter(row["task_type"] for row in rows)
    source_split_counts = Counter(row.get("benchmark_source_split", "") for row in rows)
    return {
        "split": export_split,
        "rows": len(rows),
        "task_type_counts": dict(task_type_counts),
        "benchmark_source_split_counts": dict(source_split_counts),
        "output_path": str(out_path),
    }


def export_tuning_bundle() -> list[dict[str, Any]]:
    non_heldout_tasks = load_non_heldout_tasks()
    export_train_tasks, export_dev_tasks = split_non_heldout_tasks(non_heldout_tasks)
    held_out_tasks = annotate_source_split(load_tasks(BENCH_ROOT, "held_out"), "held_out")

    return [
        write_rows("train", build_export_rows(export_train_tasks, "train")),
        write_rows("dev", build_export_rows(export_dev_tasks, "dev")),
        write_rows("held_out", build_export_rows(held_out_tasks, "held_out")),
    ]


def main() -> None:
    manifest = {
        "format": "unsloth_preference_bundle_v2",
        "source_pool": {
            "train": "combined_non_heldout_benchmark_tasks",
            "benchmark_splits_used_for_train_dev": list(NON_HELDOUT_SOURCE_SPLITS),
            "held_out_policy": "held_out rows remain exported separately for final sealed evaluation only",
        },
        "splits": export_tuning_bundle(),
        "notes": [
            "prompt/chosen/rejected are plain strings for DPO/ORPO/SimPO trainers.",
            "sft_text is a ChatML-style text field for optional warm-start SFT on chosen responses.",
            "train/dev are re-split from the combined non-held-out pool so all task types appear during tuning.",
            "held_out export exists for final sealed evaluation and should stay untouched during tuning.",
        ],
    }
    manifest_path = OUT_ROOT / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
