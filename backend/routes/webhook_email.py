from __future__ import annotations

from fastapi import APIRouter, HTTPException

from agent.briefs.brief_schema import LeadRecord
from agent.channels.channel_schema import MalformedWebhookError, ProviderSendRequest
from agent.channels.email.email_handler import EmailHandler
from backend.schemas import ProviderSendResponse, SendEmailRequest, WebhookResponse
from backend.services.conversation_service import ConversationService
from backend.services.crm_service import CRMService

router = APIRouter(prefix="/webhooks/email", tags=["email"])
conversation_service = ConversationService()
crm_service = CRMService()
email_handler = EmailHandler()
email_handler.register_inbound_handler(conversation_service.handle_inbound_event)


@router.post("/draft")
async def draft_email(lead: LeadRecord) -> dict[str, object]:
    try:
        message = conversation_service.draft_outreach(lead)
        return {"message": message.body, "metadata": message.crm_fields.model_dump()}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/send", response_model=ProviderSendResponse)
async def send_email(request: SendEmailRequest) -> ProviderSendResponse:
    try:
        lead = LeadRecord(
            company_name=request.company_name,
            contact_email=request.contact_email,
            contact_name=request.contact_name,
            last_email_reply_text=request.reply_text,
        )
        drafted = conversation_service.draft_outreach(lead)
        send_request = ProviderSendRequest(
            company_name=request.company_name,
            contact_email=request.contact_email,
            contact_name=request.contact_name,
            subject=request.subject or f"{request.company_name} talent signal",
            body=request.body or drafted.body,
            metadata={"channel": "email"},
        )
        result = email_handler.send(send_request)
        crm_sync = None
        if request.sync_to_crm and result.status in {"queued", "sent"}:
            crm_sync = crm_service.sync(lead, drafted)
        return ProviderSendResponse(**result.model_dump(), crm_sync=crm_sync)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/resend/events", response_model=WebhookResponse)
async def resend_events(payload: dict[str, object]) -> WebhookResponse:
    try:
        result = email_handler.handle_provider_webhook(payload)
        body = result.model_dump()
        body["event"] = result.event.model_dump() if result.event else None
        return WebhookResponse(**body)
    except MalformedWebhookError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
