from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from training.preference_data_utils import build_preference_rows, load_tasks

BENCH_ROOT = REPO_ROOT / "tenacious_bench_v0.1"
OUT_PATH = REPO_ROOT / "training_data" / "path_b_preferences.jsonl"

SOURCE_SPLITS = ("train", "dev")


def annotated_tasks() -> list[dict]:
    rows = []
    for split in SOURCE_SPLITS:
        for task in load_tasks(BENCH_ROOT, split):
            copied = dict(task)
            copied["benchmark_source_split"] = split
            metadata = dict(task.get("metadata", {}))
            metadata["benchmark_source_split"] = split
            copied["metadata"] = metadata
            rows.append(copied)
    return rows


def main() -> None:
    tasks = annotated_tasks()
    preference_rows = build_preference_rows(
        tasks,
        split=None,
        normalize_dimensions=False,
        render_plain_strings=False,
    )
    source_by_task_id = {task["task_id"]: task["benchmark_source_split"] for task in tasks}
    for row in preference_rows:
        source_split = source_by_task_id[row["task_id"]]
        row["benchmark_source_split"] = source_split
        row["metadata"]["benchmark_source_split"] = source_split

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text("\n".join(json.dumps(row, ensure_ascii=True) for row in preference_rows) + "\n")
    strategy_counts = Counter(row["rejection_strategy"] for row in preference_rows)
    print(
        json.dumps(
            {
                "preference_pairs": len(preference_rows),
                "tasks_used": len(tasks),
                "pairs_per_task": round(len(preference_rows) / len(tasks), 2) if tasks else 0.0,
                "benchmark_source_splits": list(SOURCE_SPLITS),
                "rejection_strategies": strategy_counts,
                "output_path": str(OUT_PATH),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
