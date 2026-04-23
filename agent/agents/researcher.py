from agent.briefs.brief_schema import LeadBrief
from agent.signals.confidence_scoring import average_confidence


class ResearcherAgent:
    def run(self, brief: LeadBrief) -> dict[str, str | float]:
        confidence = average_confidence(brief.hiring.signals + brief.compliance.signals)
        return {
            "research_summary": (
                f"Verified signals collected for {brief.lead.company_name}. "
                f"Hiring summary: {brief.hiring.summary} "
                f"Compliance summary: {brief.compliance.summary}"
            ),
            "signal_confidence": confidence,
        }
