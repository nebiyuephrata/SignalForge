from __future__ import annotations

import csv
from datetime import date, datetime
from functools import lru_cache
from pathlib import Path

REFERENCE_DATE = date(2026, 4, 23)


class LayoffsTool:
    def __init__(self, dataset_path: str | None = None) -> None:
        if dataset_path is None:
            dataset_path = str(Path(__file__).resolve().parents[2] / "data" / "layoffs.csv")
        self.dataset_path = dataset_path

    @lru_cache(maxsize=1)
    def load_dataset(self) -> list[dict[str, str]]:
        with open(self.dataset_path, "r", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))

    def get_recent_layoffs(
        self,
        company_name: str,
        lookback_days: int = 180,
        as_of_date: date = REFERENCE_DATE,
    ) -> list[dict[str, str]]:
        matches: list[dict[str, str]] = []
        normalized = company_name.strip().lower()
        for row in self.load_dataset():
            if row["company_name"].strip().lower() != normalized:
                continue
            reported_at = datetime.strptime(row["reported_at"], "%Y-%m-%d").date()
            if (as_of_date - reported_at).days <= lookback_days:
                matches.append(row)
        return matches
