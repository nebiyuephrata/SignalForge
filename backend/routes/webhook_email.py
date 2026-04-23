from fastapi import APIRouter

from agent.briefs.brief_schema import LeadRecord
from backend.services.conversation_service import ConversationService

router = APIRouter(prefix="/webhooks/email", tags=["email"])
service = ConversationService()


@router.post("/draft")
async def draft_email(lead: LeadRecord) -> dict[str, object]:
    message = service.draft_outreach(lead)
    return {"message": message.body, "metadata": message.crm_fields.model_dump()}
