from __future__ import annotations

from datetime import date, datetime

from agent.tools.crunchbase_tool import CrunchbaseTool
from agent.tools.layoffs_tool import REFERENCE_DATE


class LeadershipChangeTool:
    """Detect leadership changes from fixture-backed Crunchbase/public-press records."""

    def __init__(self, crunchbase_tool: CrunchbaseTool | None = None) -> None:
        self.crunchbase_tool = crunchbase_tool or CrunchbaseTool()

    def get_recent_changes(
        self,
        company_name: str,
        *,
        lookback_days: int = 180,
        as_of_date: date = REFERENCE_DATE,
    ) -> list[dict[str, str]]:
        company = self.crunchbase_tool.lookup_company_record(company_name)
        if company is None:
            return []

        changes = self.detect_public_leadership_changes(company)

        recent: list[dict[str, str]] = []
        for change in changes:
            if not isinstance(change, dict) or "date" not in change:
                continue
            event_date = datetime.strptime(str(change["date"]), "%Y-%m-%d").date()
            if (as_of_date - event_date).days <= lookback_days:
                serialized = {str(key): str(value) for key, value in change.items()}
                serialized["source_url"] = f"https://{company.get('domain', 'example.com')}/team"
                serialized["confidence"] = "0.78"
                recent.append(serialized)
        return recent

    @staticmethod
    def detect_public_leadership_changes(company: dict[str, object]) -> list[dict[str, object]]:
        crunchbase_records = company.get("leadership_changes", [])
        press_records = company.get("leadership_press_mentions", [])
        merged: list[dict[str, object]] = []
        for source_name, source_records in (
            ("crunchbase_record", crunchbase_records),
            ("public_press", press_records),
        ):
            if not isinstance(source_records, list):
                continue
            for change in source_records:
                if not isinstance(change, dict):
                    continue
                enriched = dict(change)
                enriched.setdefault("source", source_name)
                merged.append(enriched)
        return merged
