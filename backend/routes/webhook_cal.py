from __future__ import annotations

from fastapi import APIRouter

from agent.channels.channel_schema import InboundChannelEvent
from agent.utils.trace_logger import append_jsonl_log
from backend.schemas import BookingWebhookRequest
from backend.services.conversation_service import ConversationService
from backend.services.crm_service import CRMService

router = APIRouter(prefix="/webhooks/cal", tags=["calendar"])
crm_service = CRMService()
conversation_service = ConversationService(crm_service=crm_service)


@router.post("/booking-completed")
async def booking_completed(request: BookingWebhookRequest) -> dict[str, object]:
    payload = request.model_dump()
    append_jsonl_log("logs/webhook_events.jsonl", {"route": "/webhooks/cal/booking-completed", "phase": "received", "payload": payload})
    event = InboundChannelEvent(
        channel="calendar",
        provider="calcom",
        event_type="booking_completed",
        company_name=request.company_name,
        contact_email=request.contact_email,
        external_id=request.booking_id,
        message_text=request.booking_url,
    )
    duplicate = conversation_service.channel_orchestrator.is_duplicate_event(event)
    state = conversation_service.channel_orchestrator.process_inbound_event(event)
    crm_result = (
        {"status": "skipped", "reason": "duplicate_event"}
        if duplicate
        else crm_service.sync_booking_completed(
            contact_email=request.contact_email,
            company_name=request.company_name,
            booking_id=request.booking_id,
            booking_url=request.booking_url,
            meeting_start=request.meeting_start,
        )
    )
    response = {
        "status": "ignored" if duplicate else "processed",
        "provider": "calcom",
        "channel": "calendar",
        "event_type": "booking_completed",
        "crm_sync": crm_result,
        "lifecycle_stage": state.stage.value,
    }
    append_jsonl_log(
        "logs/webhook_events.jsonl",
        {
            "route": "/webhooks/cal/booking-completed",
            "phase": "processed",
            "status": response["status"],
            "lifecycle_stage": response["lifecycle_stage"],
            "booking_id": request.booking_id,
        },
    )
    return response
