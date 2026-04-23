from agent.briefs.brief_schema import BriefSection, EvidenceSignal
from agent.signals.confidence_scoring import average_confidence


def merge_sections(*sections: BriefSection) -> BriefSection:
    signals: list[EvidenceSignal] = []
    gaps: list[str] = []
    summaries: list[str] = []
    for section in sections:
        signals.extend(section.signals)
        gaps.extend(section.gaps)
        if section.summary:
            summaries.append(section.summary)

    confidence = average_confidence(signals)
    summary = " ".join(summaries).strip()
    if confidence and summary:
        summary = f"{summary} Overall confidence: {confidence:.2f}."

    return BriefSection(summary=summary, signals=signals, gaps=gaps)
