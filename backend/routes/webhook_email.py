from __future__ import annotations

from fastapi import APIRouter, HTTPException

from agent.briefs.brief_schema import LeadRecord
from agent.channels.channel_schema import MalformedWebhookError
from agent.channels.email.email_handler import EmailHandler
from backend.schemas import ProviderSendResponse, SendEmailRequest, WebhookResponse
from backend.services.conversation_service import ConversationService

router = APIRouter(prefix="/webhooks/email", tags=["email"])
conversation_service = ConversationService()
email_handler = conversation_service.channel_orchestrator.email_handler
email_handler.register_inbound_handler(conversation_service.handle_inbound_event)


@router.post("/draft")
async def draft_email(lead: LeadRecord) -> dict[str, object]:
    message = conversation_service.draft_outreach(lead)
    return {"message": message.body, "metadata": message.crm_fields.model_dump()}


@router.post("/send", response_model=ProviderSendResponse)
async def send_email(request: SendEmailRequest) -> ProviderSendResponse:
    lead = LeadRecord(
        company_name=request.company_name,
        contact_email=request.contact_email,
        contact_name=request.contact_name,
        phone_number=request.phone_number,
        last_email_reply_text=request.reply_text,
    )
    send_result, crm_sync, _ = conversation_service.send_email(
        lead=lead,
        subject=request.subject,
        body=request.body,
    )
    return ProviderSendResponse(**send_result.model_dump(), crm_sync=crm_sync)


@router.post("/resend/events", response_model=WebhookResponse)
async def resend_events(payload: dict[str, object]) -> WebhookResponse:
    try:
        result = email_handler.handle_provider_webhook(payload)
        body = result.model_dump()
        body["event"] = result.event.model_dump() if result.event else None
        return WebhookResponse(**body)
    except MalformedWebhookError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
