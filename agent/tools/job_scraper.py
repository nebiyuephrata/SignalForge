from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from agent.tools.crunchbase_tool import CrunchbaseTool


ROLE_PATTERN = re.compile(r'data-role-title="([^"]+)"')


class JobScraper:
    def __init__(self, crunchbase_tool: CrunchbaseTool | None = None) -> None:
        self.crunchbase_tool = crunchbase_tool or CrunchbaseTool()

    def scrape_company_jobs(self, company_name: str) -> dict[str, Any]:
        company = self.crunchbase_tool.get_company_by_name(company_name)
        if company is None:
            raise ValueError(f"Company not found in local dataset: {company_name}")

        career_page_path = str(company.get("career_page_path", "")).strip()
        if not career_page_path:
            return {
                "source": "missing_career_page",
                "open_roles": 0,
                "role_titles": [],
                "confidence": 0.2,
                "evidence": ["No local career page is configured for this company."],
            }

        fixture_path = Path(career_page_path)
        if not fixture_path.is_absolute():
            fixture_path = Path(__file__).resolve().parents[2] / career_page_path
        html = fixture_path.read_text(encoding="utf-8")

        # We intentionally avoid any login or captcha bypass logic here.
        playwright_result = self._scrape_with_playwright(html)
        if playwright_result is not None:
            playwright_result["source"] = "playwright"
            return playwright_result

        roles = ROLE_PATTERN.findall(html)
        return {
            "source": "fixture_fallback",
            "open_roles": len(roles),
            "role_titles": roles,
            "confidence": 0.7 if roles else 0.25,
            "evidence": [
                f"Parsed {len(roles)} role cards from the local career page fixture.",
                "Playwright browser runtime was unavailable, so fixture parsing was used as fallback.",
            ],
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
            roles = [str(role) for role in role_titles]
            return {
                "open_roles": len(roles),
                "role_titles": roles,
                "confidence": 0.88 if roles else 0.3,
                "evidence": [f"Playwright scraped {len(roles)} role cards from the local career page fixture."],
            }
        except Exception:
            return None
