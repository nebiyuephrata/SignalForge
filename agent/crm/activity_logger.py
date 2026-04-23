from agent.briefs.brief_schema import LeadRecord, OutboundMessage


def build_activity_log(lead: LeadRecord, message: OutboundMessage) -> dict[str, str]:
    return {
        "company_name": lead.company_name,
        "channel": message.channel,
        "body": message.body,
        "next_action": message.crm_fields.next_action,
    }
