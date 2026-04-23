from __future__ import annotations

from agent.calendar.booking_flow import BookingFlow
from backend.services.crm_service import CRMService


class BookingService:
    def __init__(self, crm_service: CRMService | None = None) -> None:
        self.booking_flow = BookingFlow()
        self.crm_service = crm_service or CRMService()

    def booking_link(self, *, company_name: str | None = None, contact_email: str | None = None) -> dict[str, str]:
        return self.booking_flow.next_step(company_name=company_name, contact_email=contact_email)

    def complete_booking(
        self,
        *,
        company_name: str,
        contact_email: str,
        booking_id: str,
        booking_url: str,
        meeting_start: str,
    ) -> dict[str, object]:
        return self.crm_service.sync_booking_completed(
            contact_email=contact_email,
            company_name=company_name,
            booking_id=booking_id,
            booking_url=booking_url,
            meeting_start=meeting_start,
        )
