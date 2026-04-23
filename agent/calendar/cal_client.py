from __future__ import annotations

from urllib.parse import urlencode

from agent.utils.config import Settings, get_settings


class CalClient:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def booking_link(
        self,
        slug: str | None = None,
        *,
        company_name: str | None = None,
        contact_email: str | None = None,
    ) -> str:
        booking_slug = slug or self.settings.calcom_booking_slug
        query = urlencode(
            {
                key: value
                for key, value in {
                    "company": company_name,
                    "email": contact_email,
                }.items()
                if value
            }
        )
        url = f"{self.settings.calcom_base_url.rstrip('/')}/{booking_slug}"
        return f"{url}?{query}" if query else url
