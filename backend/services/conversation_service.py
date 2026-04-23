from agent.briefs.brief_schema import LeadRecord, OutboundMessage
from agent.core.orchestrator import SignalForgeOrchestrator


class ConversationService:
    def __init__(self) -> None:
        self.orchestrator = SignalForgeOrchestrator()

    def draft_outreach(self, lead: LeadRecord) -> OutboundMessage:
        return self.orchestrator.run(lead)
