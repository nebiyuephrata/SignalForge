from __future__ import annotations

from fastapi import APIRouter, HTTPException

from agent.channels.channel_schema import ChannelPolicyError, MalformedWebhookError, ProviderSendRequest
from agent.channels.sms.sms_handler import SMSHandler
from backend.schemas import ProviderSendResponse, SendWarmSmsRequest, WebhookResponse
from backend.services.conversation_service import ConversationService

router = APIRouter(prefix="/webhooks/sms", tags=["sms"])
sms_handler = SMSHandler()

conversation_service = ConversationService()
sms_handler.register_inbound_handler(conversation_service.handle_inbound_event)


@router.post("/send-warm", response_model=ProviderSendResponse)
async def send_warm_sms(request: SendWarmSmsRequest) -> ProviderSendResponse:
    try:
        result = sms_handler.send_warm_follow_up(
            ProviderSendRequest(
                company_name=request.company_name,
                phone_number=request.phone_number,
                contact_email=request.contact_email,
                body=request.body,
                metadata={"channel": "sms", "warm_lead": True},
            ),
            prior_email_reply=request.prior_email_reply,
        )
        return ProviderSendResponse(**result.model_dump())
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
