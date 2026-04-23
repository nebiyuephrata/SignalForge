from fastapi import APIRouter

from agent.briefs.brief_schema import LeadRecord
from backend.services.conversation_service import ConversationService

router = APIRouter(prefix="/webhooks/sms", tags=["sms"])
service = ConversationService()


@router.post("/draft")
async def draft_sms(lead: LeadRecord) -> dict[str, object]:
    message = service.draft_outreach(lead)
    return {"message": message.body, "metadata": message.crm_fields.model_dump()}
