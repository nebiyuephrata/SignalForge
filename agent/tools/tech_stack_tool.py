from agent.briefs.brief_schema import EvidenceSignal, LeadRecord


class TechStackTool:
    def lookup(self, lead: LeadRecord) -> list[EvidenceSignal]:
        return [
            EvidenceSignal(
                signal="tech_stack",
                value="unknown",
                confidence=0.3,
                evidence=["BuiltWith/Wappalyzer integration is not configured yet."],
            )
        ]
