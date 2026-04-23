from agent.briefs.brief_schema import BriefSection, EvidenceSignal


def build_compliance_brief(signals: list[EvidenceSignal]) -> BriefSection:
    if not signals:
        return BriefSection(
            summary="No verified compliance exposure signal is available yet.",
            gaps=["CFPB or regulatory complaint evidence was not found in the current brief."],
        )
    return BriefSection(summary="Compliance exposure signals were collected for review.", signals=signals)
