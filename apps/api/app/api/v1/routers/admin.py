"""
Admin/test utility endpoints.
Protected by administrative authorization.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from apps.api.app.db.database import get_db
from apps.api.app.db.seed_data import seed_database
from apps.api.app.core.config import settings

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.post("/reset-db")
async def reset_and_reseed_database(
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
    session: AsyncSession = Depends(get_db)
):
    """
    Reset the database to a clean seeded state.
    Protected: In production, requires valid X-Admin-Key matching JWT_SECRET_KEY.
    """
    if settings.ENVIRONMENT == "production":
        if not x_admin_key or x_admin_key != settings.JWT_SECRET_KEY:
            raise HTTPException(status_code=403, detail="Forbidden: Valid administrative key required.")

    counts = await seed_database(session, reset=True)
    return {"status": "reset_complete", "seeded": counts}
