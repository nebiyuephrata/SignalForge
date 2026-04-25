from __future__ import annotations

from fastapi import APIRouter, HTTPException

from agent.briefs.brief_schema import LeadRecord
from agent.channels.channel_schema import ChannelPolicyError, MalformedWebhookError
from agent.utils.trace_logger import append_jsonl_log
from backend.schemas import ProviderSendResponse, SendWarmWhatsAppRequest, WebhookResponse
from backend.services.conversation_service import ConversationService

router = APIRouter(prefix="/webhooks/whatsapp", tags=["whatsapp"])
conversation_service = ConversationService()
whatsapp_handler = conversation_service.channel_orchestrator.whatsapp_handler
whatsapp_handler.register_inbound_handler(conversation_service.handle_inbound_event)


@router.post("/send-warm", response_model=ProviderSendResponse)
async def send_warm_whatsapp(request: SendWarmWhatsAppRequest) -> ProviderSendResponse:
    try:
        lead = LeadRecord(
            company_name=request.company_name,
            contact_email=request.contact_email,
            phone_number=request.phone_number,
        )
        result, crm_sync = conversation_service.send_warm_whatsapp(lead=lead, body=request.body)
        return ProviderSendResponse(**result.model_dump(), crm_sync=crm_sync)
    except ChannelPolicyError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/events", response_model=WebhookResponse)
async def whatsapp_events(payload: dict[str, object]) -> WebhookResponse:
    append_jsonl_log("logs/webhook_events.jsonl", {"route": "/webhooks/whatsapp/events", "phase": "received", "payload": payload})
    try:
        result = whatsapp_handler.handle_provider_webhook(payload)
        body = result.model_dump()
        body["event"] = result.event.model_dump() if result.event else None
        append_jsonl_log(
            "logs/webhook_events.jsonl",
            {
                "route": "/webhooks/whatsapp/events",
                "phase": "processed",
                "status": result.status,
                "detail": result.detail,
                "event": body.get("event"),
            },
        )
        return WebhookResponse(**body)
    except MalformedWebhookError as exc:
        append_jsonl_log(
            "logs/webhook_events.jsonl",
            {"route": "/webhooks/whatsapp/events", "phase": "validation_error", "error": str(exc), "payload": payload},
        )
        raise HTTPException(status_code=400, detail=str(exc)) from exc
