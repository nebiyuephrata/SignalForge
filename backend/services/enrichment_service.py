from agent.briefs.brief_schema import LeadBrief, LeadRecord
from agent.core.orchestrator import SignalForgeOrchestrator


class EnrichmentService:
    def __init__(self) -> None:
        self.orchestrator = SignalForgeOrchestrator()

    def enrich(self, lead: LeadRecord) -> LeadBrief:
        return self.orchestrator.enrich_lead(lead)
