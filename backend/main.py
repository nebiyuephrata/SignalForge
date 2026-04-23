from fastapi import FastAPI

from agent.utils.config import get_settings
from backend.routes.health import router as health_router
from backend.routes.run_prospect import router as run_prospect_router

settings = get_settings()
app = FastAPI(title=settings.app_name)

app.include_router(health_router)
app.include_router(run_prospect_router)
