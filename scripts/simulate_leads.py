from agent.briefs.brief_schema import LeadRecord


def sample_leads() -> list[LeadRecord]:
    return [
        LeadRecord(company_name="Northstar Lending", domain="northstar.example", employee_count=240, industry="Fintech"),
        LeadRecord(company_name="Verity Health", domain="verity.example", employee_count=870, industry="Healthcare"),
    ]


if __name__ == "__main__":
    for lead in sample_leads():
        print(lead.model_dump())
