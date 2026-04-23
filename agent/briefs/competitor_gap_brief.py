from agent.briefs.brief_schema import BriefSection, EvidenceSignal


def build_competitor_gap_brief(signals: list[EvidenceSignal]) -> BriefSection:
    if not signals:
        return BriefSection(
            summary="Competitor-gap analysis is still exploratory.",
            gaps=["Peer benchmark inputs are missing or below confidence threshold."],
        )
    return BriefSection(summary="Peer comparison highlights signal-backed performance gaps.", signals=signals)
