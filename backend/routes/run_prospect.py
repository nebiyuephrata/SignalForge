from fastapi import APIRouter, HTTPException

from backend.schemas import AvailableScenariosResponse, BatchRunResponse, ProspectRunResponse, RunProspectRequest
from backend.services.prospect_run_service import ProspectRunService

router = APIRouter(tags=["prospect"])
service = ProspectRunService()


@router.get("/run-prospect/scenarios", response_model=AvailableScenariosResponse)
async def list_run_prospect_scenarios() -> AvailableScenariosResponse:
    return AvailableScenariosResponse(scenarios=service.available_scenarios())


@router.get("/run-prospect/batch", response_model=BatchRunResponse)
async def run_prospect_batch() -> BatchRunResponse:
    return BatchRunResponse(**service.run_batch())


@router.post("/run-prospect", response_model=ProspectRunResponse)
async def run_prospect(request: RunProspectRequest | None = None) -> ProspectRunResponse:
    payload = request or RunProspectRequest()
    try:
        return ProspectRunResponse(**service.run(
            company_name=payload.company_name,
            reply_text=payload.reply_text,
            scenario_name=payload.scenario_name,
        ))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
