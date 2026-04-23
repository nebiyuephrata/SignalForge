from agent.briefs.brief_schema import BriefSection, EvidenceSignal


def build_hiring_brief(signals: list[EvidenceSignal]) -> BriefSection:
    if not signals:
        return BriefSection(
            summary="No verified hiring signal is available yet.",
            gaps=["Funding recency, hiring-velocity, or leadership-change evidence is missing."],
        )
    return BriefSection(summary="Hiring-related activity has been enriched for this lead.", signals=signals)
