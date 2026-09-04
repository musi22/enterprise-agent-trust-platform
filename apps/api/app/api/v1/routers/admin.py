"""
Admin/test utility endpoints.
WARNING: These endpoints are for development/testing only.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from apps.api.app.db.database import get_db
from apps.api.app.db.seed_data import seed_database

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.post("/reset-db")
async def reset_and_reseed_database(session: AsyncSession = Depends(get_db)):
    """
    Reset the database to a clean seeded state.
    USE ONLY IN TESTING/DEVELOPMENT. Clears all runtime data and re-seeds.
    """
    counts = await seed_database(session, reset=True)
    return {"status": "reset_complete", "seeded": counts}
