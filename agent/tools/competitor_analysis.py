from __future__ import annotations

from agent.tools.crunchbase_tool import CrunchbaseTool


class CompetitorAnalysisTool:
    """Select 5-10 same-sector comparable companies before peer rescoring."""

    def __init__(self, crunchbase_tool: CrunchbaseTool | None = None) -> None:
        self.crunchbase_tool = crunchbase_tool or CrunchbaseTool()

    def similar_companies(
        self,
        company_name: str,
        *,
        min_candidates: int = 5,
        max_candidates: int = 10,
    ) -> list[dict[str, object]]:
        target = self.crunchbase_tool.lookup_company_record(company_name)
        if target is None:
            raise ValueError(f"Company not found in local dataset: {company_name}")

        industry = target["industry"]
        employee_count = int(target["employee_count"])
        candidates = []
        for company in self.crunchbase_tool.list_companies():
            if company["company_name"] == company_name:
                continue
            if company["industry"] != industry:
                continue
            size_delta = abs(int(company["employee_count"]) - employee_count)
            if size_delta <= 200:
                ai_signal_strength = int(company.get("ai_roles_open", 0) or 0)
                candidates.append((size_delta, -ai_signal_strength, company))

        candidates.sort(key=lambda item: (item[0], item[1], str(item[2]["company_name"])))
        selected = [company for _, _, company in candidates[:max_candidates]]
        if len(selected) >= min_candidates:
            return selected
        return [company for _, _, company in candidates]
