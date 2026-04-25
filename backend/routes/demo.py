from __future__ import annotations

from fastapi import APIRouter

from backend.schemas import DemoRunLiveRequest, DemoRunLiveResponse
from backend.services.live_demo_service import LiveDemoService

router = APIRouter(prefix="/demo", tags=["demo"])
service = LiveDemoService()


@router.post("/run-live", response_model=DemoRunLiveResponse)
async def run_live_demo(request: DemoRunLiveRequest) -> DemoRunLiveResponse:
    return DemoRunLiveResponse(**service.run(
        company_name=request.company_name,
        contact_email=request.contact_email,
        reply_text=request.reply_text,
    ))
