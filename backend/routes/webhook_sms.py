from __future__ import annotations

from fastapi import APIRouter, HTTPException

from agent.briefs.brief_schema import LeadRecord
from agent.channels.channel_schema import ChannelPolicyError, MalformedWebhookError
from backend.schemas import ProviderSendResponse, SendWarmSmsRequest, WebhookResponse
from backend.services.conversation_service import ConversationService

router = APIRouter(prefix="/webhooks/sms", tags=["sms"])
conversation_service = ConversationService()
sms_handler = conversation_service.channel_orchestrator.sms_handler
sms_handler.register_inbound_handler(conversation_service.handle_inbound_event)


@router.post("/send-warm", response_model=ProviderSendResponse)
async def send_warm_sms(request: SendWarmSmsRequest) -> ProviderSendResponse:
    try:
        lead = LeadRecord(
            company_name=request.company_name,
            contact_email=request.contact_email,
            phone_number=request.phone_number,
        )
        result, crm_sync = conversation_service.send_warm_sms(lead=lead, body=request.body)
        return ProviderSendResponse(**result.model_dump(), crm_sync=crm_sync)
    except ChannelPolicyError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/africas-talking/events", response_model=WebhookResponse)
async def africas_talking_events(payload: dict[str, object]) -> WebhookResponse:
    try:
        result = sms_handler.handle_provider_webhook(payload)
        body = result.model_dump()
        body["event"] = result.event.model_dump() if result.event else None
        return WebhookResponse(**body)
    except MalformedWebhookError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

