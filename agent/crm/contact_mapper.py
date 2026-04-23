from agent.briefs.brief_schema import CRMFields, LeadRecord


def map_contact_payload(lead: LeadRecord, fields: CRMFields) -> dict[str, str | int | float]:
    return {
        "company_name": lead.company_name,
        "domain": lead.domain or "",
        "employee_count": lead.employee_count or 0,
        "industry": lead.industry or "",
        "icp_segment": fields.icp_segment,
        "signal_confidence": fields.signal_confidence,
        "ai_maturity": fields.ai_maturity,
        "intent_level": fields.intent_level,
        "qualification_status": fields.qualification_status,
        "next_action": fields.next_action,
    }
