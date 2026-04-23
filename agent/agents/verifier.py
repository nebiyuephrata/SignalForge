from agent.briefs.brief_schema import LeadBrief, OutboundMessage


class VerifierAgent:
    def run(self, brief: LeadBrief, message: OutboundMessage) -> OutboundMessage:
        if message.crm_fields.signal_confidence < 0.4 and "verified signals" in message.body.lower():
            message.body = (
                f"We have incomplete evidence on {brief.lead.company_name} so far. "
                "Can I sanity-check whether hiring, compliance, or AI capacity is the bigger issue?"
            )
        return message
