import os
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from apps.api.app.db.database import get_db

router = APIRouter(tags=["Health"])

def _get_provider_mode() -> str:
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    provider = os.getenv("DEFAULT_MODEL_PROVIDER", "deterministic_mock").lower()
    if provider in ("gemini", "google") and gemini_key:
        return "LIVE: Gemini"
    return "DEMO (Mock)"

@router.get("/health/live")
async def liveness_probe():
    """Liveness probe returning basic process uptime."""
    return {"status": "ok", "service": "agentic-commerce-reliability-lab", "live": True}

@router.get("/health/ready")
async def readiness_probe(session: AsyncSession = Depends(get_db)):
    """Readiness probe checking database connectivity and schema readiness."""
    try:
        await session.execute(text("SELECT 1"))
        return {
            "status": "ready",
            "service": "agentic-commerce-reliability-lab",
            "database": "connected",
            "ready": True,
            "provider_mode": _get_provider_mode(),
        }
    except Exception:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "ready": False,
            "provider_mode": _get_provider_mode(),
        }
