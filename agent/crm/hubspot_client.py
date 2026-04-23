from agent.briefs.brief_schema import CRMFields, LeadRecord


class HubSpotClient:
    def upsert_contact(self, lead: LeadRecord, fields: CRMFields) -> dict[str, str]:
        return {
            "status": "stubbed",
            "company_name": lead.company_name,
            "qualification_status": fields.qualification_status,
        }
