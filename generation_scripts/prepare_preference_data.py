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


def main() -> None:
    tasks = load_tasks(BENCH_ROOT, "train")
    preference_rows = build_preference_rows(
        tasks,
        split=None,
        normalize_dimensions=False,
        render_plain_strings=False,
    )

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text("\n".join(json.dumps(row, ensure_ascii=True) for row in preference_rows) + "\n")
    strategy_counts = Counter(row["rejection_strategy"] for row in preference_rows)
    print(
        json.dumps(
            {
                "preference_pairs": len(preference_rows),
                "tasks_used": len(tasks),
                "pairs_per_task": round(len(preference_rows) / len(tasks), 2) if tasks else 0.0,
                "rejection_strategies": strategy_counts,
                "output_path": str(OUT_PATH),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
