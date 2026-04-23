from __future__ import annotations

from agent.briefs.brief_schema import LeadRecord
from agent.signals.competitor_gap import build_competitor_gap_brief
from agent.signals.hiring_signals import build_hiring_signal_brief
from agent.tools.crunchbase_tool import CrunchbaseTool


class EnrichmentService:
    def __init__(self) -> None:
        self.crunchbase_tool = CrunchbaseTool()

    def enrich(self, lead: LeadRecord) -> dict[str, object]:
        company = self.crunchbase_tool.get_company_by_name(lead.company_name)
        if company is None:
            raise ValueError(f"Company not found in local dataset: {lead.company_name}")
        hiring_signal_brief = build_hiring_signal_brief(lead.company_name, self.crunchbase_tool)
        competitor_gap_brief = build_competitor_gap_brief(lead.company_name, self.crunchbase_tool)
        return {
            "company_name": lead.company_name,
            "company_profile": company,
            "signal_artifact": hiring_signal_brief["source_artifact"],
            "hiring_signal_brief": hiring_signal_brief,
            "competitor_gap_brief": competitor_gap_brief,
        }
