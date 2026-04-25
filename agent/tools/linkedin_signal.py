from __future__ import annotations

from agent.core.models import LinkedInSignalArtifact, SourceAttribution
from agent.tools.crunchbase_tool import CrunchbaseTool


class LinkedInSignalTool:
    """Simulated LinkedIn/public-activity collector backed by deterministic company fixtures."""

    def __init__(self, crunchbase_tool: CrunchbaseTool | None = None) -> None:
        self.crunchbase_tool = crunchbase_tool or CrunchbaseTool()

    def extract_company_signals(self, company_name: str) -> LinkedInSignalArtifact:
        company = self.crunchbase_tool.lookup_company_record(company_name)
        if company is None:
            return LinkedInSignalArtifact(
                hiring_posts=[],
                leadership_changes=[],
                company_activity_signals=[],
                confidence=0.0,
                source_attribution=SourceAttribution(
                    source="linkedin_public",
                    status="no_data",
                    confidence=0.0,
                    detail="No company fixture was available for LinkedIn signal extraction.",
                ),
            )

        hiring_posts = [
            f"LinkedIn hiring signal inferred from {int(company.get('ai_roles_open', 0) or 0)} AI-adjacent open roles."
        ] if int(company.get("ai_roles_open", 0) or 0) > 0 else []
        leadership_changes = [
            f"{change.get('role')}: {change.get('person')} ({change.get('date')})"
            for change in company.get("leadership_changes", [])
            if isinstance(change, dict) and change.get("role") and change.get("person")
        ]
        company_activity_signals = [str(item) for item in company.get("ai_practices", []) if str(item).strip()]

        signal_count = sum(bool(bucket) for bucket in [hiring_posts, leadership_changes, company_activity_signals])
        confidence = 0.82 if signal_count >= 2 else 0.64 if signal_count == 1 else 0.35
        return LinkedInSignalArtifact(
            hiring_posts=hiring_posts,
            leadership_changes=leadership_changes,
            company_activity_signals=company_activity_signals,
            confidence=confidence,
            source_attribution=SourceAttribution(
                source="linkedin_public",
                status="success" if signal_count else "no_data",
                source_url=f"https://www.linkedin.com/company/{str(company['company_name']).lower().replace(' ', '-')}/",
                confidence=confidence,
                detail="LinkedIn/public activity signals were simulated from deterministic company fixtures.",
            ),
        )
