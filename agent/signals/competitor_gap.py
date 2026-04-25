from __future__ import annotations

from agent.signals.competitor_gap_service import CompetitorGapService
from agent.tools.crunchbase_tool import CrunchbaseTool


def build_competitor_gap_brief(
    company_name: str,
    crunchbase_tool: CrunchbaseTool,
) -> dict[str, object]:
    return CompetitorGapService(crunchbase_tool).build(company_name)
