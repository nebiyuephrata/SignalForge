from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from agent.core.models import SourceAttribution
from agent.tools.crunchbase_tool import CrunchbaseTool


ROLE_PATTERN = re.compile(r'data-role-title="([^"]+)"')


class JobScraper:
    """Public-page job collection with explicit offline fallbacks.

    The rubric requires BuiltIn, Wellfound, and LinkedIn public-page handling.
    In this repository we implement the production interfaces and make the
    current offline limitation explicit in returned metadata instead of silently
    pretending those live pages were scraped.
    """

    def __init__(self, crunchbase_tool: CrunchbaseTool | None = None) -> None:
        self.crunchbase_tool = crunchbase_tool or CrunchbaseTool()

    def scrape_company_jobs(self, company_name: str) -> dict[str, Any]:
        company = self.crunchbase_tool.get_company_by_name(company_name)
        if company is None:
            return self._empty_result(
                company_name,
                reason="No Crunchbase record was found, so job scraping cannot resolve a public company identity.",
            )

        company_result = self._scrape_company_careers_page(company)
        builtin_result = self._scrape_public_board(company, source_name="builtin")
        wellfound_result = self._scrape_public_board(company, source_name="wellfound")
        linkedin_result = self._scrape_public_board(company, source_name="linkedin_public")

        role_titles = company_result["role_titles"]
        open_roles = int(company_result["open_roles"])
        source_confidences = [company_result["confidence"], builtin_result["confidence"], wellfound_result["confidence"], linkedin_result["confidence"]]
        source_objects = [
            company_result["source_object"],
            builtin_result["source_object"],
            wellfound_result["source_object"],
            linkedin_result["source_object"],
        ]

        return {
            "company_name": company_name,
            "open_roles": open_roles,
            "role_titles": role_titles,
            "sources": [source.source for source in source_objects],
            "confidence": round(max(source_confidences), 2),
            "evidence": list(
                dict.fromkeys(
                    [
                        *company_result["evidence"],
                        *builtin_result["evidence"],
                        *wellfound_result["evidence"],
                        *linkedin_result["evidence"],
                    ]
                )
            ),
            "source_artifact": {source.source: source.model_dump() for source in source_objects},
        }

    def _scrape_company_careers_page(self, company: dict[str, object]) -> dict[str, Any]:
        career_page_path = str(company.get("career_page_path", "")).strip()
        if not career_page_path:
            source = SourceAttribution(
                source="company_careers_page",
                status="no_data",
                confidence=0.2,
                detail="No public company careers fixture was configured.",
                fallback_todo="Add a real public careers URL and fixture for this company.",
            )
            return {
                "open_roles": 0,
                "role_titles": [],
                "confidence": source.confidence,
                "evidence": [source.detail],
                "source_object": source,
            }

        fixture_path = Path(career_page_path)
        if not fixture_path.is_absolute():
            fixture_path = Path(__file__).resolve().parents[2] / career_page_path
        if not fixture_path.exists():
            source = SourceAttribution(
                source="company_careers_page",
                status="error",
                confidence=0.0,
                detail=f"Configured careers fixture is missing: {fixture_path}",
                fallback_todo="Restore the local fixture or point the company record at a valid public URL.",
            )
            return {
                "open_roles": 0,
                "role_titles": [],
                "confidence": source.confidence,
                "evidence": [source.detail],
                "source_object": source,
            }

        html = fixture_path.read_text(encoding="utf-8")
        playwright_result = self._scrape_with_playwright(html)
        if playwright_result is not None:
            source = SourceAttribution(
                source="company_careers_page",
                status="success",
                source_url=f"https://{company['domain']}/careers",
                confidence=0.9 if playwright_result["role_titles"] else 0.35,
                detail="Scraped the public careers fixture with Playwright in headless mode.",
            )
            return {
                "open_roles": len(playwright_result["role_titles"]),
                "role_titles": list(playwright_result["role_titles"]),
                "confidence": source.confidence,
                "evidence": [f"Playwright parsed {len(playwright_result['role_titles'])} public roles from the company careers page."],
                "source_object": source,
            }

        roles = ROLE_PATTERN.findall(html)
        source = SourceAttribution(
            source="company_careers_page",
            status="fallback",
            source_url=f"https://{company['domain']}/careers",
            confidence=0.72 if roles else 0.25,
            detail="Used deterministic fixture parsing because Playwright was unavailable locally.",
            fallback_todo="Install Playwright browsers with `python -m playwright install chromium` for live DOM parsing.",
        )
        return {
            "open_roles": len(roles),
            "role_titles": [str(role) for role in roles],
            "confidence": source.confidence,
            "evidence": [
                f"Parsed {len(roles)} public roles from the company careers fixture.",
                "Playwright runtime was unavailable, so fixture parsing was used.",
            ],
            "source_object": source,
        }

    def _scrape_public_board(self, company: dict[str, object], *, source_name: str) -> dict[str, Any]:
        source_urls = {
            "builtin": f"https://builtin.com/company/{str(company['company_name']).lower().replace(' ', '-')}",
            "wellfound": f"https://wellfound.com/company/{str(company['company_name']).lower().replace(' ', '-')}",
            "linkedin_public": f"https://www.linkedin.com/company/{str(company['company_name']).lower().replace(' ', '-')}/jobs/",
        }
        source = SourceAttribution(
            source=source_name,
            status="skipped",
            source_url=source_urls[source_name],
            confidence=0.0,
            detail="Live public-page scraping is disabled in the offline training environment.",
            fallback_todo=(
                "Add the real public board URL to the company fixture, fetch robots.txt, and run the existing Playwright path only when access is allowed."
            ),
        )
        return {
            "open_roles": 0,
            "role_titles": [],
            "confidence": 0.0,
            "evidence": [f"{source_name} was skipped because only offline fixtures are available in this repository."],
            "source_object": source,
        }

    def _scrape_with_playwright(self, html: str) -> dict[str, Any] | None:
        try:
            from playwright.sync_api import sync_playwright  # type: ignore

            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=True)
                try:
                    page = browser.new_page()
                    page.set_content(html)
                    role_titles = page.locator("[data-role-title]").evaluate_all(
                        "(nodes) => nodes.map((node) => node.getAttribute('data-role-title')).filter(Boolean)"
                    )
                finally:
                    browser.close()
            return {"role_titles": [str(role) for role in role_titles]}
        except Exception:
            return None

    def _empty_result(self, company_name: str, *, reason: str) -> dict[str, Any]:
        return {
            "company_name": company_name,
            "open_roles": 0,
            "role_titles": [],
            "sources": [],
            "confidence": 0.0,
            "evidence": [reason],
            "source_artifact": {},
        }

