from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from apps.api.app.db.database import get_db
from apps.api.app.db.models import EvidenceReceipt
from packages.telemetry.ledger import TamperEvidentEvidenceLedger

router = APIRouter(prefix="/evidence", tags=["Tamper-Evident Evidence Ledger"])

@router.get("")
async def list_recent_evidence_receipts(limit: int = 50, session: AsyncSession = Depends(get_db)):
    """List recent tamper-evident cryptographic evidence receipts."""
    stmt = select(EvidenceReceipt).order_by(EvidenceReceipt.created_at.desc()).limit(limit)
    res = await session.execute(stmt)
    receipts = res.scalars().all()

    return [
        {
            "receipt_id": r.id,
            "run_id": r.run_id,
            "scenario_id": r.scenario_id,
            "final_outcome": r.final_outcome,
            "previous_event_hash": r.previous_event_hash,
            "event_hash": r.event_hash,
            "payload_hash": r.payload_hash,
            "signature": r.signature,
            "receipt_data": r.receipt_data,
            "created_at": r.created_at.isoformat() if r.created_at else None
        }
        for r in receipts
    ]

@router.get("/{run_id}")
async def get_run_evidence(run_id: str, session: AsyncSession = Depends(get_db)):
    """Retrieve cryptographic evidence receipt for a specific agent execution."""
    stmt = select(EvidenceReceipt).where(EvidenceReceipt.run_id == run_id)
    res = await session.execute(stmt)
    receipt = res.scalar_one_or_none()

    if not receipt:
        raise HTTPException(status_code=404, detail=f"No evidence receipt found for run '{run_id}'.")

    return {
        "receipt_id": receipt.id,
        "run_id": receipt.run_id,
        "scenario_id": receipt.scenario_id,
        "final_outcome": receipt.final_outcome,
        "previous_event_hash": receipt.previous_event_hash,
        "event_hash": receipt.event_hash,
        "payload_hash": receipt.payload_hash,
        "signature": receipt.signature,
        "receipt_data": receipt.receipt_data,
        "created_at": receipt.created_at.isoformat() if receipt.created_at else None
    }

@router.post("/verify")
async def verify_entire_ledger(session: AsyncSession = Depends(get_db)):
    """Cryptographically verify the mathematical integrity of the entire append-only hash chain."""
    result = await TamperEvidentEvidenceLedger.verify_chain(session)
    return result

@router.post("/{run_id}/verify")
async def verify_run_evidence(run_id: str, session: AsyncSession = Depends(get_db)):
    """Verify hash continuity and payload integrity for an individual run's evidence receipt."""
    result = await TamperEvidentEvidenceLedger.verify_chain(session, run_id=run_id)
    return result

@router.post("/tamper-test")
async def simulate_tampering_test(session: AsyncSession = Depends(get_db)):
    """
    Test helper endpoint: Deliberately mutates a payload in the database to demonstrate
    that the hash-chain verification mathematically catches tampering.
    """
    stmt = select(EvidenceReceipt).order_by(EvidenceReceipt.created_at.desc()).limit(1)
    res = await session.execute(stmt)
    receipt = res.scalar_one_or_none()

    if not receipt:
        raise HTTPException(status_code=400, detail="No evidence blocks available to test tampering.")

    # Mutate data
    data = dict(receipt.receipt_data)
    data["_TAMPERED_BY_TEST"] = "Malicious unauthorized modification"
    receipt.receipt_data = data
    await session.commit()

    # Re-verify
    verification = await TamperEvidentEvidenceLedger.verify_chain(session)
    return {
        "tamper_injected": True,
        "tampered_receipt_id": receipt.id,
        "verification_result": verification
    }
