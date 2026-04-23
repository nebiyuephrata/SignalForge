from agent.briefs.brief_schema import CRMFields, LeadBrief, OutboundMessage
from agent.signals.confidence_scoring import confidence_phrase


class CloserAgent:
    def run(self, brief: LeadBrief, crm_fields: CRMFields) -> OutboundMessage:
        phrasing = confidence_phrase(crm_fields.signal_confidence)
        company = brief.lead.company_name
        if phrasing == "question":
            body = (
                f"We're seeing a few early signals around {company}, but not enough to make a hard claim. "
                "Is hiring velocity or compliance workload a live priority for the team right now?"
            )
        elif phrasing == "hedged":
            body = (
                f"It looks like there may be movement around hiring or operational pressure at {company}. "
                "If that is directionally right, I can share a short benchmark on how similar teams are handling it."
            )
        else:
            body = (
                f"We found verified signals that suggest a timely operational shift at {company}. "
                "Happy to walk through the evidence and compare it with what top-quartile peers are doing."
            )
        return OutboundMessage(channel="email", body=body, crm_fields=crm_fields)
