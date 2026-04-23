from __future__ import annotations

from statistics import mean

from agent.signals.ai_maturity import build_ai_maturity_assessment
from agent.tools.competitor_analysis import CompetitorAnalysisTool
from agent.tools.crunchbase_tool import CrunchbaseTool


def build_competitor_gap_brief(
    company_name: str,
    crunchbase_tool: CrunchbaseTool,
) -> dict[str, object]:
    company = crunchbase_tool.get_company_by_name(company_name)
    if company is None:
        raise ValueError(f"Company not found in local dataset: {company_name}")

    competitor_tool = CompetitorAnalysisTool(crunchbase_tool)
    peers = competitor_tool.similar_companies(company_name, limit=5)
    target_ai = build_ai_maturity_assessment(company)
    peer_assessments = [
        {
            "company_name": peer["company_name"],
            "employee_count": peer["employee_count"],
            "ai_maturity_score": build_ai_maturity_assessment(peer)["value"],
            "ai_practices": peer.get("ai_practices", []),
        }
        for peer in peers
    ]

    peer_average_ai = round(mean(item["ai_maturity_score"] for item in peer_assessments), 2) if peer_assessments else 0.0
    top_score = max((item["ai_maturity_score"] for item in peer_assessments), default=0)
    top_quartile_peers = [item for item in peer_assessments if item["ai_maturity_score"] == top_score]

    practices: list[str] = []
    for peer in top_quartile_peers:
        for practice in peer["ai_practices"]:
            if practice not in practices:
                practices.append(practice)

    confidence = 0.6 if len(peer_assessments) >= 5 else 0.45
    gap = round(peer_average_ai - int(target_ai["value"]), 2)
    if gap > 0:
        gap_summary = (
            f"Against five similar fintech companies, {company_name} trails the peer average AI maturity "
            f"({target_ai['value']} vs {peer_average_ai}). The clearest gap is consistent AI hiring and operating practices."
        )
    else:
        gap_summary = (
            f"{company_name} is roughly in line with the peer average AI maturity ({target_ai['value']} vs {peer_average_ai}). "
            "Benchmarking is still useful, but the gap is not yet decisive."
        )

    return {
        "company_name": company_name,
        "gap_summary": gap_summary,
        "top_quartile_practices": practices[:5],
        "confidence": confidence,
        "target_ai_maturity": target_ai["value"],
        "peer_average_ai_maturity": peer_average_ai,
        "selected_peers": peer_assessments,
    }
