from agent.briefs.brief_schema import LeadRecord
from agent.core.orchestrator import SignalForgeOrchestrator


def main() -> None:
    lead = LeadRecord(company_name="Northstar Lending", domain="northstar.example", employee_count=240, industry="Fintech")
    orchestrator = SignalForgeOrchestrator()
    brief = orchestrator.enrich_lead(lead)
    print(brief.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
