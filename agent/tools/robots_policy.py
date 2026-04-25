from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RobotsDecision:
    source: str
    allowed: bool
    public_only: bool
    respects_robots_txt: bool
    reason: str


class PublicPageRobotsPolicy:
    """Static robots/public-page policy for the offline training repository.

    The challenge requires visible robots.txt and public-page-only constraints.
    In this local dataset we model those decisions explicitly instead of making
    live robots requests from a network-restricted environment.
    """

    SOURCE_RULES = {
        "company_careers_page": RobotsDecision(
            source="company_careers_page",
            allowed=True,
            public_only=True,
            respects_robots_txt=True,
            reason="Company careers pages are treated as public fixture-backed pages.",
        ),
        "builtin": RobotsDecision(
            source="builtin",
            allowed=False,
            public_only=True,
            respects_robots_txt=True,
            reason="BuiltIn scraping is disabled in the offline environment until a real public URL and robots decision are recorded.",
        ),
        "wellfound": RobotsDecision(
            source="wellfound",
            allowed=False,
            public_only=True,
            respects_robots_txt=True,
            reason="Wellfound scraping is disabled in the offline environment until a real public URL and robots decision are recorded.",
        ),
        "linkedin_public": RobotsDecision(
            source="linkedin_public",
            allowed=False,
            public_only=True,
            respects_robots_txt=True,
            reason="LinkedIn public-page scraping remains gated pending an explicit recorded robots/public-page review.",
        ),
    }

    def decision_for(self, source_name: str) -> RobotsDecision:
        return self.SOURCE_RULES.get(
            source_name,
            RobotsDecision(
                source=source_name,
                allowed=False,
                public_only=True,
                respects_robots_txt=True,
                reason="Unknown public-page source. Defaulting to no-fetch until policy is recorded.",
            ),
        )
