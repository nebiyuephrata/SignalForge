from agent.briefs.brief_schema import EvidenceSignal, LeadRecord


class CFPBTool:
    def lookup(self, lead: LeadRecord) -> list[EvidenceSignal]:
        return [
            EvidenceSignal(
                signal="cfpb_activity",
                value="unknown",
                confidence=0.2,
                evidence=[f"No live CFPB lookup executed for {lead.company_name} in scaffold mode."],
            )
        ]
