from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PROBE_LIBRARY_PATH = REPO_ROOT / "probes" / "probe_library.json"


def load_probe_library(path: Path | None = None) -> list[dict[str, object]]:
    target = path or PROBE_LIBRARY_PATH
    return json.loads(target.read_text(encoding="utf-8"))


def summarize_by_category(probes: list[dict[str, object]] | None = None) -> list[dict[str, object]]:
    probes = probes or load_probe_library()
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for probe in probes:
        grouped[str(probe["category"])].append(probe)

    summaries: list[dict[str, object]] = []
    for category, category_probes in sorted(grouped.items()):
        avg_trigger_rate = round(
            sum(float(probe["observed_trigger_rate"]) for probe in category_probes) / len(category_probes),
            2,
        )
        avg_business_cost = round(
            sum(float(probe["business_cost_usd"]) for probe in category_probes) / len(category_probes),
            2,
        )
        summaries.append(
            {
                "category": category,
                "probe_count": len(category_probes),
                "average_trigger_rate": avg_trigger_rate,
                "average_business_cost_usd": avg_business_cost,
                "expected_loss_index": round(avg_trigger_rate * avg_business_cost, 2),
                "probe_ids": [str(probe["id"]) for probe in category_probes],
            }
        )
    return summaries


def select_target_failure_mode(probes: list[dict[str, object]] | None = None) -> dict[str, object]:
    probes = probes or load_probe_library()
    summaries = summarize_by_category(probes)
    lookup = {summary["category"]: summary for summary in summaries}
    target = lookup["weak confidence handling"]
    alternatives = [lookup["gap over-claiming"], lookup["coordination failures"]]
    return {
        "target_category": target,
        "alternatives": alternatives,
    }

