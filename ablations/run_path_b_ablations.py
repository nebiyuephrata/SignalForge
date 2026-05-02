from __future__ import annotations

"""Shared Week 11 ablation harness for Path B.

The current repo already ships an executed local critic run. This harness makes
the comparison interface explicit so Delta A / B / C and cost-pareto reporting
are visible in source code, with paired bootstrap logic and basic failure
handling grouped behind one entrypoint.
"""

import json
import random
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
ABLATION_PATH = REPO_ROOT / "ablations" / "ablation_harness_summary.json"
TRACE_PATH = REPO_ROOT / "ablations" / "held_out_traces.jsonl"
TRAINED_RESULTS_PATH = REPO_ROOT / "ablations" / "ablation_results.json"
SEED = 42
BOOTSTRAP_ROUNDS = 1000
MIN_TRACE_ROWS = 10


@dataclass
class ComparisonResult:
    name: str
    accuracy: float
    latency_ms: float
    cost_usd: float


def load_existing_traces() -> list[dict[str, Any]]:
    return [json.loads(line) for line in TRACE_PATH.read_text().splitlines() if line.strip()]


def bootstrap_delta_ci(rows: list[dict[str, Any]], rounds: int = BOOTSTRAP_ROUNDS) -> dict[str, float]:
    """Paired bootstrap over held-out rows.

    Assumptions:
    - the harness should not report intervals for trivially small samples,
    - 1000 rounds is the current reproducibility/latency compromise for this repo.
    """
    if len(rows) < MIN_TRACE_ROWS:
        raise ValueError(f"Need at least {MIN_TRACE_ROWS} held-out rows for bootstrap reporting.")
    rng = random.Random(SEED)
    deltas: list[float] = []
    n = len(rows)
    for _ in range(rounds):
        sample = [rows[rng.randrange(n)] for _ in range(n)]
        baseline = sum(1 for row in sample if row["baseline_correct"]) / n
        trained = sum(1 for row in sample if row["trained_correct"]) / n
        deltas.append((trained - baseline) * 100.0)
    deltas.sort()
    return {
        "ci_lower": round(deltas[int(0.025 * len(deltas))], 2),
        "ci_upper": round(deltas[int(0.975 * len(deltas))], 2),
        "p_value": round(sum(1 for value in deltas if value <= 0.0) / len(deltas), 4),
    }


def delta_a(rows: list[dict[str, Any]]) -> dict[str, Any]:
    ci = bootstrap_delta_ci(rows)
    baseline_accuracy = sum(1 for row in rows if row["baseline_correct"]) / len(rows)
    trained_accuracy = sum(1 for row in rows if row["trained_correct"]) / len(rows)
    return {
        "description": "Trained Path B critic versus Week 10 heuristic baseline on held-out pairs.",
        "baseline_accuracy": round(baseline_accuracy, 4),
        "trained_accuracy": round(trained_accuracy, 4),
        "delta_accuracy_pp": round((trained_accuracy - baseline_accuracy) * 100.0, 2),
        **ci,
    }


def delta_b(existing_payload: dict[str, Any]) -> dict[str, Any]:
    held_out = existing_payload["splits"]["held_out"]
    return {
        "description": "Same backbone, prompt-engineered heuristic only versus trained critic.",
        "prompt_engineered_baseline_accuracy": held_out["baseline_accuracy"],
        "trained_accuracy": held_out["trained_accuracy"],
        "delta_accuracy_pp": held_out["delta_accuracy_pp"],
    }


def delta_c() -> dict[str, Any]:
    return {
        "description": "Informational reference only: tau2-bench retail is used as an external contrast benchmark and is not rerun inside this repo.",
        "public_reference": "tau2-bench retail",
        "rerun_performed": False,
    }


def cost_pareto(existing_payload: dict[str, Any]) -> dict[str, Any]:
    held_out = existing_payload["splits"]["held_out"]
    return {
        "baseline_latency_ms": held_out["baseline_latency_ms"],
        "trained_latency_ms": held_out["trained_latency_ms"],
        "latency_delta_ms": round(held_out["trained_latency_ms"] - held_out["baseline_latency_ms"], 4),
        "baseline_cost_usd": 0.0,
        "trained_cost_usd": 0.0,
        "cost_delta_usd": 0.0,
    }


def run_all() -> dict[str, Any]:
    start = time.perf_counter()
    try:
        rows = load_existing_traces()
        existing_payload = json.loads(TRAINED_RESULTS_PATH.read_text())
        result = {
            "path": "B",
            "shared_interface": ["delta_a", "delta_b", "delta_c", "cost_pareto"],
            "delta_a": delta_a(rows),
            "delta_b": delta_b(existing_payload),
            "delta_c": delta_c(),
            "cost_pareto": cost_pareto(existing_payload),
            "failure_handling": {"status": "ok", "message": ""},
        }
    except Exception as exc:  # pragma: no cover - explicit failure reporting path
        result = {
            "path": "B",
            "shared_interface": ["delta_a", "delta_b", "delta_c", "cost_pareto"],
            "failure_handling": {"status": "error", "message": str(exc)},
        }
    result["wall_time_ms"] = round((time.perf_counter() - start) * 1000, 4)
    return result


def main() -> None:
    payload = run_all()
    ABLATION_PATH.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
