from __future__ import annotations

from statistics import mean

from agent.core.models import CompetitorEntry, CompetitorEvidence, CompetitorGapBrief, DistributionPosition, GapFinding
from agent.signals.ai_maturity import build_ai_maturity_assessment
from agent.tenacious.context import headcount_band
from agent.tools.competitor_analysis import CompetitorAnalysisTool
from agent.tools.crunchbase_tool import CrunchbaseTool


class CompetitorGapService:
    """Generate the challenge-facing competitor gap brief in one place."""

    def __init__(self, crunchbase_tool: CrunchbaseTool | None = None) -> None:
        self.crunchbase_tool = crunchbase_tool or CrunchbaseTool()
        self.competitor_tool = CompetitorAnalysisTool(self.crunchbase_tool)

    def build(self, company_name: str) -> dict[str, object]:
        company = self.crunchbase_tool.lookup_company_record(company_name)
        if company is None:
            payload = _missing_company_brief(company_name).model_dump()
            payload["selected_peers"] = payload["competitors_analyzed"]
            return payload

        peer_pool = self.select_competitor_pool(company_name)
        target_ai = build_ai_maturity_assessment(company)
        peer_entries = [self._peer_entry(peer) for peer in peer_pool]
        distribution_position = self.compute_distribution_position(
            target_score=target_ai.score,
            peer_scores=[entry.ai_maturity_score for entry in peer_entries],
        )
        top_quartile_threshold = _quartile_threshold([entry.ai_maturity_score for entry in peer_entries] + [target_ai.score])
        for entry in peer_entries:
            entry.top_quartile = entry.ai_maturity_score >= top_quartile_threshold

        top_quartile_peers = [entry for entry in peer_entries if entry.top_quartile]
        sector_top_quartile_benchmark = round(mean([entry.ai_maturity_score for entry in top_quartile_peers]), 2) if top_quartile_peers else 0.0
        peer_average_ai = round(mean([entry.ai_maturity_score for entry in peer_entries]), 2) if peer_entries else 0.0
        sparse_sector = len(peer_entries) < 5
        gap_findings = self.extract_gap_findings(company=company, top_quartile_peers=top_quartile_peers)
        confidence = round(0.78 if len(peer_entries) >= 5 else 0.52 if peer_entries else 0.35, 2)

        brief = CompetitorGapBrief(
            prospect_domain=str(company["domain"]),
            prospect_sector=str(company["industry"]),
            prospect_sub_niche=str(company["industry"]),
            prospect_ai_maturity_score=target_ai.score,
            sector_top_quartile_benchmark=sector_top_quartile_benchmark,
            competitors_analyzed=peer_entries,
            distribution_position=distribution_position,
            gap_findings=gap_findings,
            suggested_pitch_shift=(
                "Lead with a benchmark observation, then ask whether internal AI capacity is expanding fast enough."
                if target_ai.score < peer_average_ai
                else "Lead with a calibration question, not a deficit claim."
            ),
            gap_quality_self_check={
                "all_peer_evidence_has_source_url": all(
                    evidence.source_url for finding in gap_findings for evidence in finding.peer_evidence
                ),
                "at_least_one_gap_high_confidence": any(finding.confidence == "high" for finding in gap_findings),
                "prospect_silent_but_sophisticated_risk": target_ai.score >= 2 and not gap_findings,
            },
            confidence=confidence,
            sparse_sector=sparse_sector,
            gap_summary=self._gap_summary(
                company_name=company_name,
                target_ai_score=target_ai.score,
                peer_average_ai=peer_average_ai,
                peer_count=len(peer_entries),
                sparse_sector=sparse_sector,
            ),
            peer_average_ai_maturity=peer_average_ai,
            target_ai_maturity=target_ai.score,
        )
        payload = brief.model_dump()
        for competitor in payload["competitors_analyzed"]:
            competitor["company_name"] = competitor["name"]
        payload["selected_peers"] = payload["competitors_analyzed"]
        return payload

    def select_competitor_pool(self, company_name: str) -> list[dict[str, object]]:
        """Select 5-10 same-sector, similar-size competitors before top-quartile scoring."""
        return self.competitor_tool.similar_companies(company_name, min_candidates=5, max_candidates=10)

    @staticmethod
    def compute_distribution_position(*, target_score: int, peer_scores: list[int]) -> DistributionPosition:
        total_companies = len(peer_scores) + 1
        sorted_scores = sorted(peer_scores + [target_score], reverse=True)
        prospect_rank = sorted_scores.index(target_score) + 1
        percentile = round((total_companies - prospect_rank) / max(total_companies - 1, 1), 2)
        return DistributionPosition(
            prospect_rank=prospect_rank,
            total_companies=total_companies,
            percentile=percentile,
            label=_distribution_label(percentile),
        )

    def extract_gap_findings(
        self,
        *,
        company: dict[str, object],
        top_quartile_peers: list[CompetitorEntry],
    ) -> list[GapFinding]:
        company_practices = {str(item).lower() for item in company.get("ai_practices", [])}
        company_ai_roles = int(company.get("ai_roles_open", 0) or 0)
        practice_index: dict[str, list[CompetitorEntry]] = {}
        for peer in top_quartile_peers:
            for signal in peer.named_signals:
                practice_index.setdefault(signal, []).append(peer)

        candidate_findings: list[GapFinding] = []
        for practice, peers in practice_index.items():
            if len(peers) < 2:
                continue
            normalized = practice.lower()
            if normalized in company_practices:
                continue
            if "public ai roles" in normalized and company_ai_roles > 0:
                continue

            candidate_findings.append(
                GapFinding(
                    practice=practice,
                    peer_evidence=[
                        CompetitorEvidence(
                            competitor_name=peer.name,
                            evidence=f"{peer.name} shows public signal for {practice}.",
                            source_url=peer.sources_checked[0],
                        )
                        for peer in peers[:3]
                    ],
                    prospect_state=(
                        f"No public signal of {practice} exists in the current prospect fixture."
                        if "public ai roles" not in normalized
                        else f"{company_ai_roles} AI-adjacent public roles are currently visible for the prospect."
                    ),
                    confidence="high" if len(peers) >= 3 else "medium",
                    segment_relevance=["segment_3_leadership_transition", "segment_4_specialized_capability"],
                )
            )

        if not candidate_findings:
            candidate_findings.append(
                GapFinding(
                    practice="Named AI operating signal",
                    peer_evidence=[
                        CompetitorEvidence(
                            competitor_name=peer.name,
                            evidence=f"{peer.name} shows stronger public AI operating signals.",
                            source_url=peer.sources_checked[0],
                        )
                        for peer in top_quartile_peers[:2]
                    ],
                    prospect_state="The prospect has limited public AI operating evidence in the current fixture.",
                    confidence="medium" if top_quartile_peers else "low",
                    segment_relevance=["segment_4_specialized_capability"],
                )
            )

        return candidate_findings[:3]

    @staticmethod
    def _peer_entry(peer: dict[str, object]) -> CompetitorEntry:
        ai = build_ai_maturity_assessment(peer)
        return CompetitorEntry(
            name=str(peer["company_name"]),
            domain=str(peer["domain"]),
            ai_maturity_score=ai.score,
            ai_maturity_justification=[justification.status for justification in ai.justifications],
            headcount_band=headcount_band(int(peer["employee_count"])),
            sources_checked=[f"https://{peer['domain']}/careers", f"https://{peer['domain']}/team"],
            named_signals=_named_signals(peer),
        )

    @staticmethod
    def _gap_summary(
        *,
        company_name: str,
        target_ai_score: int,
        peer_average_ai: float,
        peer_count: int,
        sparse_sector: bool,
    ) -> str:
        if sparse_sector:
            return (
                f"{company_name} has only {peer_count} comparable public peers in the local dataset, "
                "so benchmark claims should stay directional."
            )
        if peer_average_ai > target_ai_score:
            return (
                f"{company_name} trails the peer average AI maturity ({target_ai_score} vs {peer_average_ai}). "
                "The cleanest public gaps are in named AI roles, operating practices, and leadership signals."
            )
        return (
            f"{company_name} is at or above the local peer average AI maturity ({target_ai_score} vs {peer_average_ai}). "
            "Benchmarking remains useful, but the outreach should be consultative rather than corrective."
        )


def _named_signals(peer: dict[str, object]) -> list[str]:
    signals: list[str] = []
    ai_roles_open = int(peer.get("ai_roles_open", 0) or 0)
    if ai_roles_open:
        signals.append(f"{ai_roles_open} public AI roles")
    for practice in peer.get("ai_practices", []):
        practice_text = str(practice).strip()
        if practice_text:
            signals.append(practice_text)
    for change in peer.get("leadership_changes", []):
        if not isinstance(change, dict):
            continue
        role = str(change.get("role", "")).strip()
        person = str(change.get("person", "")).strip()
        if role and person:
            signals.append(f"{role}: {person}")
    return signals[:5]


def _quartile_threshold(scores: list[int]) -> int:
    if not scores:
        return 0
    ordered = sorted(scores, reverse=True)
    index = max(int(len(ordered) * 0.25) - 1, 0)
    return ordered[index]


def _distribution_label(percentile: float) -> str:
    if percentile >= 0.75:
        return "top_quartile"
    if percentile >= 0.5:
        return "upper_mid"
    if percentile >= 0.25:
        return "lower_mid"
    return "bottom_quartile"


def _missing_company_brief(company_name: str) -> CompetitorGapBrief:
    return CompetitorGapBrief(
        prospect_domain="unknown",
        prospect_sector="unknown",
        prospect_sub_niche="unknown",
        prospect_ai_maturity_score=0,
        sector_top_quartile_benchmark=0.0,
        competitors_analyzed=[],
        distribution_position=DistributionPosition(prospect_rank=1, total_companies=1, percentile=0.0, label="bottom_quartile"),
        gap_findings=[
            GapFinding(
                practice="No peer comparison available",
                peer_evidence=[],
                prospect_state=f"No Crunchbase record was found for {company_name}.",
                confidence="low",
                segment_relevance=[],
            )
        ],
        suggested_pitch_shift="Do not mention peers until the prospect company can be resolved.",
        gap_quality_self_check={
            "all_peer_evidence_has_source_url": True,
            "at_least_one_gap_high_confidence": False,
            "prospect_silent_but_sophisticated_risk": False,
        },
        confidence=0.0,
        sparse_sector=True,
        gap_summary="No competitor benchmark is available because the prospect record is missing.",
        peer_average_ai_maturity=0.0,
        target_ai_maturity=0,
    )
