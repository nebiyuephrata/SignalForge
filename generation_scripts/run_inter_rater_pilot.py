from __future__ import annotations

import json
import random
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import scoring_evaluator

BENCH_ROOT = REPO_ROOT / "tenacious_bench_v0.1"
OUTPUT_ROOT = REPO_ROOT / "outputs"
PASS1_PATH = OUTPUT_ROOT / "inter_rater_pass1.json"
PASS2_PATH = OUTPUT_ROOT / "inter_rater_pass2.json"
SUMMARY_PATH = OUTPUT_ROOT / "inter_rater_summary.json"
SEED = 42
TARGET_TASKS = 30


def load_all_tasks() -> list[dict[str, Any]]:
    tasks = []
    for split in ("train", "dev", "held_out"):
        path = BENCH_ROOT / split / "tasks.jsonl"
        for line in path.read_text().splitlines():
            if line.strip():
                row = json.loads(line)
                row["_split"] = split
                tasks.append(row)
    return tasks


def select_subset(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for task in tasks:
        grouped[(task["source_mode"], task["task_type"])].append(task)
    for rows in grouped.values():
        rows.sort(key=lambda item: item["task_id"])

    subset: list[dict[str, Any]] = []
    group_keys = sorted(grouped)
    while len(subset) < TARGET_TASKS and any(grouped.values()):
        for key in group_keys:
            rows = grouped[key]
            if rows:
                subset.append(rows.pop(0))
                if len(subset) == TARGET_TASKS:
                    break
    return sorted(subset, key=lambda item: item["task_id"])


def label_pass(tasks: list[dict[str, Any]], *, seed: int) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    shuffled = tasks[:]
    rng.shuffle(shuffled)
    labels = []
    for task in shuffled:
        result = scoring_evaluator.evaluate_task(task)
        labels.append(
            {
                "task_id": task["task_id"],
                "dimension": task["dimension"],
                "task_type": task["task_type"],
                "source_mode": task["source_mode"],
                "split": task["_split"],
                "dimension_results": result["dimension_results"],
                "passed": result["passed"],
            }
        )
    labels.sort(key=lambda item: item["task_id"])
    return labels


def compare_passes(pass1: list[dict[str, Any]], pass2: list[dict[str, Any]]) -> dict[str, Any]:
    by_task_1 = {row["task_id"]: row for row in pass1}
    by_task_2 = {row["task_id"]: row for row in pass2}
    dimensions: dict[str, list[int]] = defaultdict(list)

    for task_id, left in by_task_1.items():
        right = by_task_2[task_id]
        left_dims = {row["name"]: row["score"] for row in left["dimension_results"]}
        right_dims = {row["name"]: row["score"] for row in right["dimension_results"]}
        for dimension_name in sorted(set(left_dims) | set(right_dims)):
            dimensions[dimension_name].append(int(left_dims.get(dimension_name) == right_dims.get(dimension_name)))

    agreement = {
        dimension_name: round(sum(matches) / len(matches), 4)
        for dimension_name, matches in sorted(dimensions.items())
    }
    overall = round(sum(sum(matches) for matches in dimensions.values()) / sum(len(matches) for matches in dimensions.values()), 4)
    return {
        "task_count": len(pass1),
        "dimension_agreement": agreement,
        "overall_agreement": overall,
    }


def main() -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    subset = select_subset(load_all_tasks())
    pass1 = label_pass(subset, seed=SEED)
    pass2 = label_pass(subset, seed=SEED + 1)
    summary = compare_passes(pass1, pass2)
    summary["subset_task_ids"] = [task["task_id"] for task in subset]
    PASS1_PATH.write_text(json.dumps(pass1, indent=2) + "\n")
    PASS2_PATH.write_text(json.dumps(pass2, indent=2) + "\n")
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
