from __future__ import annotations

from datetime import date, datetime

from agent.tools.crunchbase_tool import CrunchbaseTool
from agent.tools.layoffs_tool import REFERENCE_DATE


class LeadershipChangeTool:
    def __init__(self, crunchbase_tool: CrunchbaseTool | None = None) -> None:
        self.crunchbase_tool = crunchbase_tool or CrunchbaseTool()

    def get_recent_changes(
        self,
        company_name: str,
        *,
        lookback_days: int = 180,
        as_of_date: date = REFERENCE_DATE,
    ) -> list[dict[str, str]]:
        company = self.crunchbase_tool.get_company_by_name(company_name)
        if company is None:
            return []

        changes = company.get("leadership_changes", [])
        if not isinstance(changes, list):
            return []

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
