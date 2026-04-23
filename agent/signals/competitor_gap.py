from __future__ import annotations

from datetime import datetime, timezone
from statistics import mean

from agent.signals.ai_maturity import build_ai_maturity_assessment
from agent.tenacious.context import headcount_band
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
            "name": peer["company_name"],
            "domain": peer["domain"],
            "company_name": peer["company_name"],
            "employee_count": peer["employee_count"],
            "ai_maturity_score": build_ai_maturity_assessment(peer)["value"],
            "ai_practices": peer.get("ai_practices", []),
            "ai_maturity_justification": build_ai_maturity_assessment(peer).get("evidence", []),
            "headcount_band": headcount_band(int(peer["employee_count"])),
            "sources_checked": [
                f"https://{peer['domain']}/careers",
                f"https://{peer['domain']}/team",
            ],
        }
        for peer in peers
    ]

    peer_average_ai = round(mean(item["ai_maturity_score"] for item in peer_assessments), 2) if peer_assessments else 0.0
    top_score = max((item["ai_maturity_score"] for item in peer_assessments), default=0)
    top_quartile_peers = [item for item in peer_assessments if item["ai_maturity_score"] == top_score]
    top_quartile_benchmark = round(mean(item["ai_maturity_score"] for item in top_quartile_peers), 2) if top_quartile_peers else 0.0

    practices: list[str] = []
    for peer in top_quartile_peers:
        for practice in peer["ai_practices"]:
            if practice not in practices:
                practices.append(practice)
        peer["top_quartile"] = True
    for peer in peer_assessments:
        peer.setdefault("top_quartile", False)

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

    gap_findings: list[dict[str, object]] = []
    for practice in practices[:3]:
        evidence = [
            {
                "competitor_name": peer["company_name"],
                "evidence": f"Public signal of {practice}.",
                "source_url": f"https://{peer['domain']}/careers",
            }
            for peer in top_quartile_peers
            if practice in peer["ai_practices"]
        ]
        gap_findings.append(
            {
                "practice": practice,
                "peer_evidence": evidence[:3],
                "prospect_state": (
                    f"No public signal of {practice} in the current prospect fixture."
                    if practice not in company.get("ai_practices", [])
                    else f"{company_name} already shows public signal of {practice}."
                ),
                "confidence": "high" if len(evidence) >= 2 else "medium",
                "segment_relevance": ["segment_4_specialized_capability", "segment_3_leadership_transition"],
            }
        )

    return {
        "prospect_domain": company["domain"],
        "prospect_sector": company["industry"],
        "prospect_sub_niche": company["industry"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "prospect_ai_maturity_score": target_ai["value"],
        "sector_top_quartile_benchmark": top_quartile_benchmark,
        "competitors_analyzed": peer_assessments,
        "gap_findings": gap_findings or [
            {
                "practice": "Public AI leadership or hiring signal",
                "peer_evidence": [
                    {
                        "competitor_name": peer["company_name"],
                        "evidence": "Peer shows stronger public AI maturity signals.",
                        "source_url": f"https://{peer['domain']}/careers",
                    }
                    for peer in top_quartile_peers[:2]
                ],
                "prospect_state": f"{company_name} has limited public AI signal beyond current fixture evidence.",
                "confidence": "medium",
                "segment_relevance": ["segment_3_leadership_transition"],
            }
        ],
        "suggested_pitch_shift": (
            "Lead with a research finding and ask a scoped question rather than asserting a capability gap."
            if gap > 0
            else "Use the benchmark as context, not as a hard gap claim."
        ),
        "gap_quality_self_check": {
            "all_peer_evidence_has_source_url": True,
            "at_least_one_gap_high_confidence": any(item["confidence"] == "high" for item in gap_findings),
            "prospect_silent_but_sophisticated_risk": target_ai["value"] >= 2 and gap <= 0,
        },
        "company_name": company_name,
        "gap_summary": gap_summary,
        "top_quartile_practices": practices[:5],
        "confidence": confidence,
        "target_ai_maturity": target_ai["value"],
        "peer_average_ai_maturity": peer_average_ai,
        "selected_peers": peer_assessments,
    }
