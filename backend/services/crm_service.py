from agent.briefs.brief_schema import LeadRecord, OutboundMessage
from agent.crm.hubspot_client import HubSpotClient


class CRMService:
    def __init__(self) -> None:
        self.client = HubSpotClient()

    def sync(self, lead: LeadRecord, message: OutboundMessage) -> dict[str, str]:
        return self.client.upsert_contact(lead, message.crm_fields)
