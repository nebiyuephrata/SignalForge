from __future__ import annotations

from agent.tools.crunchbase_tool import CrunchbaseTool


class CompetitorAnalysisTool:
    def __init__(self, crunchbase_tool: CrunchbaseTool | None = None) -> None:
        self.crunchbase_tool = crunchbase_tool or CrunchbaseTool()

    def similar_companies(self, company_name: str, limit: int = 5) -> list[dict[str, object]]:
        target = self.crunchbase_tool.get_company_by_name(company_name)
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
                candidates.append((size_delta, company))

        candidates.sort(key=lambda item: item[0])
        return [company for _, company in candidates[:limit]]
