from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apps.api.app.core.config import settings
from apps.api.app.db.database import engine, Base
from apps.api.app.api.v1.routers.health import router as health_router
from apps.api.app.api.v1.routers.runs import router as runs_router
from apps.api.app.api.v1.routers.evaluations import router as eval_router
from apps.api.app.api.v1.routers.policies import router as policies_router
from apps.api.app.api.v1.routers.approvals import router as approvals_router
from apps.api.app.api.v1.routers.evidence import router as evidence_router
from apps.api.app.api.v1.routers.scenarios import router as scenarios_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure database schema is initialized on startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown resources
    await engine.dispose()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Enterprise Agent Trust & Evaluation Platform - Independently built Amazon-inspired agent reliability sandbox.",
    openapi_url="/api/v1/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS Configuration for Engineering Console
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Health routes at root and API v1
app.include_router(health_router)
app.include_router(health_router, prefix=settings.API_V1_PREFIX)

# Mount API v1 Feature Routers
app.include_router(runs_router, prefix=settings.API_V1_PREFIX)
app.include_router(eval_router, prefix=settings.API_V1_PREFIX)
app.include_router(policies_router, prefix=settings.API_V1_PREFIX)
app.include_router(approvals_router, prefix=settings.API_V1_PREFIX)
app.include_router(evidence_router, prefix=settings.API_V1_PREFIX)
app.include_router(scenarios_router, prefix=settings.API_V1_PREFIX)

@app.get("/")
async def root():
    return {
        "platform": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs_url": "/docs",
        "api_v1": settings.API_V1_PREFIX,
        "status": "online"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("apps.api.app.main:app", host="0.0.0.0", port=8000, reload=True)
