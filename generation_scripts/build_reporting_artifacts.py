from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import scoring_evaluator as evaluator

BENCH_ROOT = REPO_ROOT / "tenacious_bench_v0.1"
REPORTS_ROOT = REPO_ROOT / "reports"
INTER_RATER_PATH = REPO_ROOT / "outputs" / "inter_rater_summary.json"

SPLITS = ["train", "dev", "held_out"]
SOURCE_MODES = ["trace-derived", "programmatic", "multi-llm-synthesis", "hand-authored"]
WORKED_EXAMPLE_IDS = {
    "programmatic": "tb-p-002-v01",
    "trace-derived": "tb-trace-email-001",
    "adversarial": "tb-hand-001",
}


def load_tasks(split: str) -> list[dict[str, Any]]:
    path = BENCH_ROOT / split / "tasks.jsonl"
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def load_all_tasks() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for split in SPLITS:
        rows.extend(load_tasks(split))
    return rows


def build_composition_payload(tasks: list[dict[str, Any]]) -> dict[str, Any]:
    cube: dict[str, dict[str, Counter[str]]] = defaultdict(lambda: defaultdict(Counter))
    row_totals: Counter[str] = Counter()
    split_totals: Counter[str] = Counter()
    source_mode_totals: Counter[str] = Counter()

    for task in tasks:
        dimension = task["dimension"]
        split = task["split"]
        source_mode = task["source_mode"]
        cube[dimension][split][source_mode] += 1
        row_totals[dimension] += 1
        split_totals[split] += 1
        source_mode_totals[source_mode] += 1

    total_tasks = len(tasks)
    source_mode_targets = {
        "trace-derived": round(total_tasks * 0.30),
        "programmatic": round(total_tasks * 0.30),
        "multi-llm-synthesis": round(total_tasks * 0.25),
        "hand-authored": round(total_tasks * 0.15),
    }
    partition_targets = {
        "train": round(total_tasks * 0.50),
        "dev": round(total_tasks * 0.30),
        "held_out": total_tasks - round(total_tasks * 0.50) - round(total_tasks * 0.30),
    }

    cross_tab_rows = []
    for dimension in sorted(cube):
        row: dict[str, Any] = {"dimension": dimension, "total": row_totals[dimension]}
        for split in SPLITS:
            for mode in SOURCE_MODES:
                row[f"{split}:{mode}"] = cube[dimension][split].get(mode, 0)
        cross_tab_rows.append(row)

    return {
        "total_tasks": total_tasks,
        "partition_actuals": dict(split_totals),
        "partition_targets": partition_targets,
        "source_mode_actuals": dict(source_mode_totals),
        "source_mode_targets": source_mode_targets,
        "cross_tab_rows": cross_tab_rows,
    }


def composition_markdown(payload: dict[str, Any]) -> str:
    headers = ["Dimension"] + [f"{split}:{mode}" for split in SPLITS for mode in SOURCE_MODES] + ["Total"]
    lines = [
        "| " + " | ".join(headers) + " |",
        "|" + "|".join([" --- "] * len(headers)) + "|",
    ]
    for row in payload["cross_tab_rows"]:
        values = [row["dimension"]]
        for split in SPLITS:
            for mode in SOURCE_MODES:
                values.append(str(row[f"{split}:{mode}"]))
        values.append(str(row["total"]))
        lines.append("| " + " | ".join(values) + " |")

    total_row = ["Total"]
    for split in SPLITS:
        for mode in SOURCE_MODES:
            total_row.append(str(sum(row[f"{split}:{mode}"] for row in payload["cross_tab_rows"])))
    total_row.append(str(payload["total_tasks"]))
    lines.append("| " + " | ".join(total_row) + " |")
    return "\n".join(lines) + "\n"


def build_worked_examples(tasks: list[dict[str, Any]]) -> dict[str, Any]:
    by_id = {task["task_id"]: task for task in tasks}
    programmatic = by_id[WORKED_EXAMPLE_IDS["programmatic"]]
    trace_derived = by_id[WORKED_EXAMPLE_IDS["trace-derived"]]
    adversarial_base = by_id[WORKED_EXAMPLE_IDS["adversarial"]]

    adversarial_failure_output = {
        "subject": f"Quick: {adversarial_base['input']['company_name']} signal check",
        "body": "You are clearly scaling aggressively and should book time here: https://cal.com/tenacious/discovery",
    }

    examples = {
        "programmatic": {
            "task": programmatic,
            "evaluation": evaluator.evaluate_task(programmatic, agent_output=programmatic["candidate_output"]),
        },
        "trace-derived": {
            "task": trace_derived,
            "evaluation": evaluator.evaluate_task(trace_derived, agent_output=trace_derived["candidate_output"]),
        },
        "adversarial_failure": {
            "task": adversarial_base,
            "agent_output": adversarial_failure_output,
            "evaluation": evaluator.evaluate_task(adversarial_base, agent_output=adversarial_failure_output),
        },
    }
    return examples


def build_inter_rater_payload() -> dict[str, Any]:
    summary = json.loads(INTER_RATER_PATH.read_text())
    return {
        "metric": "exact-match agreement by rubric dimension across a blind two-pass, 30-task subset",
        "protocol": [
            "sample 30 tasks spanning source modes and task types",
            "label pass 1",
            "blind reshuffle",
            "label pass 2",
            "compute per-dimension exact-match agreement",
        ],
        **summary,
    }


def main() -> None:
    REPORTS_ROOT.mkdir(parents=True, exist_ok=True)
    tasks = load_all_tasks()
    composition = build_composition_payload(tasks)
    worked_examples = build_worked_examples(tasks)
    inter_rater = build_inter_rater_payload()

    (REPORTS_ROOT / "bench_composition.json").write_text(json.dumps(composition, indent=2) + "\n")
    (REPORTS_ROOT / "bench_composition_table.md").write_text(composition_markdown(composition))
    (REPORTS_ROOT / "worked_examples.json").write_text(json.dumps(worked_examples, indent=2) + "\n")
    (REPORTS_ROOT / "inter_rater_report.json").write_text(json.dumps(inter_rater, indent=2) + "\n")

    print(
        json.dumps(
            {
                "reports_root": str(REPORTS_ROOT),
                "artifacts": [
                    "bench_composition.json",
                    "bench_composition_table.md",
                    "worked_examples.json",
                    "inter_rater_report.json",
                ],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
