from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

class ToolContext(BaseModel):
    user_id: str
    user_role: str = "customer"
    run_id: Optional[str] = None
    idempotency_key: Optional[str] = None
    session_metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True
