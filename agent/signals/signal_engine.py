from agent.briefs.brief_schema import BriefSection, EvidenceSignal, LeadBrief, LeadRecord
from agent.briefs.compliance_brief import build_compliance_brief
from agent.briefs.competitor_gap_brief import build_competitor_gap_brief
from agent.briefs.hiring_signal_brief import build_hiring_brief


def build_ai_maturity_brief(signals: list[EvidenceSignal]) -> BriefSection:
    if not signals:
        return BriefSection(
            summary="No verified AI maturity evidence is available yet.",
            gaps=["Public tooling, hiring, or leadership evidence for AI maturity is missing."],
        )
    return BriefSection(summary="AI maturity evidence has been collected from public signals.", signals=signals)


class SignalEngine:
    def build_brief(
        self,
        lead: LeadRecord,
        hiring_signals: list[EvidenceSignal] | None = None,
        compliance_signals: list[EvidenceSignal] | None = None,
        ai_signals: list[EvidenceSignal] | None = None,
        competitor_signals: list[EvidenceSignal] | None = None,
    ) -> LeadBrief:
        return LeadBrief(
            lead=lead,
            hiring=build_hiring_brief(hiring_signals or []),
            compliance=build_compliance_brief(compliance_signals or []),
            ai_maturity=build_ai_maturity_brief(ai_signals or []),
            competitor_gap=build_competitor_gap_brief(competitor_signals or []),
        )
