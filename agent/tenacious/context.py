from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
TENACIOUS_ROOT = REPO_ROOT / "tenacious_sales_data" / "tenacious_sales_data"


@lru_cache(maxsize=1)
def load_bench_summary() -> dict[str, object]:
    path = TENACIOUS_ROOT / "seed" / "bench_summary.json"
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_style_guide() -> str:
    return (TENACIOUS_ROOT / "seed" / "style_guide.md").read_text(encoding="utf-8")


@lru_cache(maxsize=1)
def load_icp_definition() -> str:
    return (TENACIOUS_ROOT / "seed" / "icp_definition.md").read_text(encoding="utf-8")


def headcount_band(employee_count: int) -> str:
    if employee_count < 80:
        return "15_to_80"
    if employee_count < 200:
        return "80_to_200"
    if employee_count < 500:
        return "200_to_500"
    if employee_count < 2000:
        return "500_to_2000"
    return "2000_plus"
