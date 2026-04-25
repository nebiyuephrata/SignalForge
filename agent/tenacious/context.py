from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
TENACIOUS_ROOT = REPO_ROOT / "tenacious_sales_data" / "tenacious_sales_data"
DEFAULT_BENCH_SUMMARY: dict[str, object] = {
    "stacks": {
        "python": {"available_engineers": 4},
        "data": {"available_engineers": 3},
        "ml": {"available_engineers": 2},
        "frontend": {"available_engineers": 2},
        "infra": {"available_engineers": 2},
    }
}
DEFAULT_STYLE_GUIDE = """
Tenacious outreach should be grounded, concise, and respectful.
Lead with observed signals, avoid inflated certainty, and use calibration questions when confidence is mixed.
Do not use generic outsourcing language or imply a prospect is behind without evidence.
Keep emails executive-readable, concrete, and under roughly 120 words.
""".strip()
DEFAULT_ICP_DEFINITION = """
Tenacious focuses on growth and mid-market companies where engineering demand, AI maturity, or operating change creates delivery pressure.
Strong fits include teams with visible hiring velocity, leadership transition, restructuring, or a need for specialized capability.
Messages should connect public signals to delivery timing, team capacity, and practical next steps.
""".strip()


def _read_text_or_default(path: Path, default: str) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8")
    return default


def _read_json_or_default(path: Path, default: dict[str, object]) -> dict[str, object]:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return default


@lru_cache(maxsize=1)
def load_bench_summary() -> dict[str, object]:
    path = TENACIOUS_ROOT / "seed" / "bench_summary.json"
    return _read_json_or_default(path, DEFAULT_BENCH_SUMMARY)


@lru_cache(maxsize=1)
def load_style_guide() -> str:
    return _read_text_or_default(TENACIOUS_ROOT / "seed" / "style_guide.md", DEFAULT_STYLE_GUIDE)


@lru_cache(maxsize=1)
def load_icp_definition() -> str:
    return _read_text_or_default(TENACIOUS_ROOT / "seed" / "icp_definition.md", DEFAULT_ICP_DEFINITION)


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
