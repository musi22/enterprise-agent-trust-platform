from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from apps.api.app.db.database import get_db

router = APIRouter(tags=["Health"])

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
            "ready": True
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": f"error: {str(e)}",
            "ready": False
        }
