from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agent.utils.config import get_settings
from backend.routes.health import router as health_router
from backend.routes.run_prospect import router as run_prospect_router

settings = get_settings()
app = FastAPI(title=settings.app_name)

allowed_origins = [origin.strip() for origin in settings.frontend_origins.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(run_prospect_router)
