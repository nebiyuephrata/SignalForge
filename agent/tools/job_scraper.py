from agent.briefs.brief_schema import EvidenceSignal, LeadRecord


class JobScraper:
    def scrape(self, lead: LeadRecord) -> list[EvidenceSignal]:
        return [
            EvidenceSignal(
                signal="job_velocity",
                value="unknown",
                confidence=0.3,
                evidence=[f"No live career-site scrape executed for {lead.company_name} in scaffold mode."],
            )
        ]
