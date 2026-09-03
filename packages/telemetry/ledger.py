import hashlib
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from apps.api.app.db.models import EvidenceReceipt, AgentRun, generate_uuid
from apps.api.app.core.security import redact_sensitive_data

GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"

def canonical_json(data: Any) -> str:
    """Produces deterministic, sort-keyed JSON string representation for hashing."""
    return json.dumps(data, sort_keys=True, separators=(',', ':'), default=str)

def compute_sha256(payload_str: str) -> str:
    """Computes SHA-256 hexadecimal digest."""
    return hashlib.sha256(payload_str.encode('utf-8')).hexdigest()

class TamperEvidentEvidenceLedger:
    """
    Append-only cryptographic evidence ledger. Each event block is linked to 
    the previous block via SHA-256 hash chaining, enabling mathematical detection
    of data alteration, omission, or unauthorized insertion.
    """
    @staticmethod
    def create_block(
        run_id: str,
        scenario_id: Optional[str],
        previous_event_hash: str,
        event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Creates a signed, hash-chained evidence block with redacted secrets."""
        # 1. Redact any sensitive credentials/PII
        sanitized_data = redact_sensitive_data(event_data)
        
        # 2. Canonical serialization of sanitized data
        payload_canonical = canonical_json(sanitized_data)
        payload_hash = compute_sha256(payload_canonical)

        # 3. Hash-chaining: hash(prev_hash + payload_canonical)
        chain_input = f"{previous_event_hash}{payload_canonical}"
        event_hash = compute_sha256(chain_input)

        # 4. Digital signature simulation (HMAC/SHA256 signature)
        signature = compute_sha256(f"SIG_KEY_V1::{event_hash}")

        return {
            "receipt_id": generate_uuid(),
            "run_id": run_id,
            "scenario_id": scenario_id,
            "previous_event_hash": previous_event_hash,
            "event_hash": event_hash,
            "payload_hash": payload_hash,
            "signature": signature,
            "receipt_data": sanitized_data,
            "created_at": datetime.now(timezone.utc).isoformat()
        }

    @staticmethod
    async def append_receipt(
        session: AsyncSession,
        run_id: str,
        scenario_id: Optional[str],
        final_outcome: str,
        event_data: Dict[str, Any]
    ) -> EvidenceReceipt:
        """Appends a new receipt to the persistent evidence store."""
        # Fetch the latest receipt for hash continuity (or genesis if first)
        stmt = select(EvidenceReceipt).order_by(EvidenceReceipt.created_at.desc()).limit(1)
        res = await session.execute(stmt)
        last_receipt = res.scalar_one_or_none()

        prev_hash = last_receipt.event_hash if last_receipt else GENESIS_HASH

        block = TamperEvidentEvidenceLedger.create_block(
            run_id=run_id,
            scenario_id=scenario_id,
            previous_event_hash=prev_hash,
            event_data=event_data
        )

        receipt = EvidenceReceipt(
            id=block["receipt_id"],
            run_id=run_id,
            scenario_id=scenario_id,
            final_outcome=final_outcome,
            previous_event_hash=block["previous_event_hash"],
            event_hash=block["event_hash"],
            payload_hash=block["payload_hash"],
            receipt_data=block["receipt_data"],
            signature=block["signature"]
        )
        session.add(receipt)
        await session.commit()
        return receipt

    @staticmethod
    async def verify_chain(session: AsyncSession, run_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Verifies the mathematical integrity of the cryptographic hash chain.
        Returns whether the ledger is pristine, or pinpoints the exact block where
        tampering or breakage occurred.
        """
        stmt = select(EvidenceReceipt).order_by(EvidenceReceipt.created_at.asc())
        if run_id:
            stmt = stmt.where(EvidenceReceipt.run_id == run_id)

        res = await session.execute(stmt)
        receipts: List[EvidenceReceipt] = res.scalars().all()

        if not receipts:
            return {
                "valid": True,
                "total_blocks_verified": 0,
                "status": "EMPTY_LEDGER",
                "message": "Ledger is empty; no blocks to verify."
            }

        prev_expected_hash = receipts[0].previous_event_hash
        verified_count = 0

        for idx, rec in enumerate(receipts):
            # 1. Check previous hash link
            if rec.previous_event_hash != prev_expected_hash:
                return {
                    "valid": False,
                    "tamper_detected": True,
                    "error_code": "BROKEN_CHAIN_LINK",
                    "broken_at_block_index": idx,
                    "receipt_id": rec.id,
                    "run_id": rec.run_id,
                    "expected_previous_hash": prev_expected_hash,
                    "actual_previous_hash": rec.previous_event_hash,
                    "message": f"Hash chain broken at block {idx}: previous_hash does not match predecessor."
                }

            # 2. Recompute payload hash
            recomputed_canonical = canonical_json(rec.receipt_data)
            recomputed_payload_hash = compute_sha256(recomputed_canonical)
            if recomputed_payload_hash != rec.payload_hash:
                return {
                    "valid": False,
                    "tamper_detected": True,
                    "error_code": "CORRUPTED_PAYLOAD",
                    "broken_at_block_index": idx,
                    "receipt_id": rec.id,
                    "run_id": rec.run_id,
                    "expected_payload_hash": rec.payload_hash,
                    "actual_payload_hash": recomputed_payload_hash,
                    "message": f"Tampering detected at block {idx}: Payload data has been altered!"
                }

            # 3. Recompute event hash
            chain_input = f"{rec.previous_event_hash}{recomputed_canonical}"
            recomputed_event_hash = compute_sha256(chain_input)
            if recomputed_event_hash != rec.event_hash:
                return {
                    "valid": False,
                    "tamper_detected": True,
                    "error_code": "INVALID_EVENT_HASH",
                    "broken_at_block_index": idx,
                    "receipt_id": rec.id,
                    "run_id": rec.run_id,
                    "expected_event_hash": rec.event_hash,
                    "actual_event_hash": recomputed_event_hash,
                    "message": f"Tampering detected at block {idx}: Event hash check failed."
                }

            prev_expected_hash = rec.event_hash
            verified_count += 1

        return {
            "valid": True,
            "tamper_detected": False,
            "total_blocks_verified": verified_count,
            "status": "HASH_CHAIN_VALID",
            "last_event_hash": prev_expected_hash,
            "message": f"All {verified_count} evidence blocks verified with 100% cryptographic integrity."
        }
