from __future__ import annotations

from datetime import date, datetime

from agent.tools.layoffs_tool import REFERENCE_DATE


def classify_primary_segment(
    *,
    company: dict[str, object],
    funding_days: int,
    recent_layoffs: list[dict[str, str]],
    recent_leadership_changes: list[dict[str, str]],
    ai_maturity_score: int,
    open_roles_current: int,
    as_of_date: date = REFERENCE_DATE,
) -> tuple[str, float]:
    employee_count = int(company.get("employee_count", 0) or 0)
    stage = str(company.get("last_funding_round", "")).strip().lower()
    location = str(company.get("location", "")).lower()

    if recent_layoffs and funding_days <= 180:
        return "segment_2_mid_market_restructure", 0.74

    recent_transition = any(
        (as_of_date - datetime.strptime(change["date"], "%Y-%m-%d").date()).days <= 90
        for change in recent_leadership_changes
        if "date" in change
    )
    if recent_transition and 50 <= employee_count <= 500:
        return "segment_3_leadership_transition", 0.82

    if ai_maturity_score >= 2 and open_roles_current >= 3:
        return "segment_4_specialized_capability", 0.67

    if (
        funding_days <= 180
        and stage in {"series a", "series b"}
        and 15 <= employee_count <= 80
        and open_roles_current >= 5
        and any(region in location for region in ("tx", "ca", "ny", "il", "wa", "ga", "nc", "tn", "co"))
    ):
        return "segment_1_series_a_b", 0.78

    return "abstain", 0.45
