from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from datetime import date, datetime


class CrunchbaseTool:
    """Fixture-backed Crunchbase ODM lookup with explicit funding-window logic."""

    def __init__(self, dataset_path: str | None = None) -> None:
        if dataset_path is None:
            dataset_path = str(Path(__file__).resolve().parents[2] / "data" / "crunchbase_sample.json")
        self.dataset_path = dataset_path

    @lru_cache(maxsize=1)
    def load_dataset(self) -> list[dict[str, object]]:
        with open(self.dataset_path, "r", encoding="utf-8") as handle:
            return json.load(handle)

    def list_companies(self) -> list[dict[str, object]]:
        return list(self.load_dataset())

    def lookup_company_record(self, name: str) -> dict[str, object] | None:
        normalized = name.strip().lower()
        for company in self.load_dataset():
            if str(company.get("company_name", "")).strip().lower() == normalized:
                return company
        return None

    def get_company_by_name(self, name: str) -> dict[str, object] | None:
        return self.lookup_company_record(name)

    def lookup_recent_funding_event(
        self,
        company_name: str,
        *,
        lookback_days: int = 180,
        as_of_date: date | None = None,
    ) -> dict[str, object] | None:
        company = self.lookup_company_record(company_name)
        if company is None:
            return None
        funding_date = str(company.get("funding_date", "")).strip()
        funding_round = str(company.get("last_funding_round", "")).strip()
        if not funding_date or not funding_round:
            return None

        as_of = as_of_date or date.today()
        closed_at = datetime.strptime(funding_date, "%Y-%m-%d").date()
        days_since_event = (as_of - closed_at).days
        if days_since_event > lookback_days:
            return None
        return {
            "company_name": company["company_name"],
            "round": funding_round,
            "closed_at": funding_date,
            "days_since_event": days_since_event,
            "source_url": f"https://www.crunchbase.com/organization/{str(company['company_name']).lower().replace(' ', '-')}",
        }
