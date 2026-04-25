from __future__ import annotations

from fastapi import APIRouter

from agent.channels.channel_schema import InboundChannelEvent
from agent.core.models import WebsiteVisitEvent
from agent.tools.website_signal import WebsiteSignalStore
from agent.utils.trace_logger import append_jsonl_log, fingerprint_payload
from backend.schemas import WebsiteVisitRequest, WebsiteVisitResponse
from backend.services.conversation_service import ConversationService

router = APIRouter(prefix="/webhooks/website", tags=["website"])
conversation_service = ConversationService()
website_signal_store = WebsiteSignalStore()


@router.post("/visit", response_model=WebsiteVisitResponse)
async def record_website_visit(request: WebsiteVisitRequest) -> WebsiteVisitResponse:
    payload = request.model_dump(by_alias=True)
    append_jsonl_log("logs/webhook_events.jsonl", {"route": "/webhooks/website/visit", "phase": "received", "payload": payload})
    visit = WebsiteVisitEvent(
        company_name=request.company_name,
        page_visited=request.page_visited,
        timestamp=request.timestamp,
        contact_email=request.contact_email,
        session_id=request.session_id,
    )
    website_signal_store.record_visit(visit)
    result = conversation_service.handle_inbound_event(
        InboundChannelEvent(
            channel="website",
            provider="website",
            event_type="visit",
            company_name=request.company_name,
            contact_email=request.contact_email,
            message_text=request.page_visited,
            external_id=fingerprint_payload(payload),
            received_at=request.timestamp,
            raw_payload=payload,
        )
    )
    follow_up_pages = {"/pricing", "/demo", "/book", "/case-studies"}
    response = WebsiteVisitResponse(
        status="ignored" if result.get("duplicate") else "processed",
        lifecycle_stage=str(result["lifecycle_stage"]),
        follow_up_recommended=request.page_visited.lower() in follow_up_pages,
        allowed_next_channels=list(result["allowed_next_channels"]),
        crm_sync=dict(result["crm_sync"]),
    )
    append_jsonl_log(
        "logs/webhook_events.jsonl",
        {
            "route": "/webhooks/website/visit",
            "phase": "processed",
            "status": response.status,
            "lifecycle_stage": response.lifecycle_stage,
            "follow_up_recommended": response.follow_up_recommended,
        },
    )
    return response
