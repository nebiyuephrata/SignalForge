from __future__ import annotations

from fastapi import APIRouter

from backend.schemas import BookingWebhookRequest
from backend.services.crm_service import CRMService

router = APIRouter(prefix="/webhooks/cal", tags=["calendar"])
crm_service = CRMService()


@router.post("/booking-completed")
async def booking_completed(request: BookingWebhookRequest) -> dict[str, object]:
    crm_result = crm_service.sync_booking_completed(
        contact_email=request.contact_email,
        company_name=request.company_name,
        booking_id=request.booking_id,
        booking_url=request.booking_url,
        meeting_start=request.meeting_start,
    )
    return {
        "status": "processed",
        "provider": "calcom",
        "channel": "calendar",
        "event_type": "booking_completed",
        "crm_sync": crm_result,
    }
