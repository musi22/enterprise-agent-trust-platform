import pytest
import copy
from packages.telemetry.ledger import TamperEvidentEvidenceLedger, GENESIS_HASH, canonical_json, compute_sha256
from apps.api.app.db.models import EvidenceReceipt

@pytest.mark.asyncio
async def test_hash_chain_creation_and_tamper_detection(db_session):
    # 1. Create block 0 (genesis linked)
    block_0 = TamperEvidentEvidenceLedger.create_block(
        run_id="run_test_001",
        scenario_id="01_catalog_search",
        previous_event_hash=GENESIS_HASH,
        event_data={"order_id": "ord_test_001", "total_cents": 5000, "status": "confirmed"}
    )
    receipt_0 = EvidenceReceipt(
        id=block_0["receipt_id"],
        run_id=block_0["run_id"],
        scenario_id=block_0["scenario_id"],
        final_outcome="SUCCESS",
        previous_event_hash=block_0["previous_event_hash"],
        event_hash=block_0["event_hash"],
        payload_hash=block_0["payload_hash"],
        receipt_data=block_0["receipt_data"],
        signature=block_0["signature"]
    )
    db_session.add(receipt_0)
    await db_session.commit()

    # 2. Create block 1 (chained to block 0)
    block_1 = TamperEvidentEvidenceLedger.create_block(
        run_id="run_test_002",
        scenario_id="02_out_of_stock",
        previous_event_hash=block_0["event_hash"],
        event_data={"order_id": "ord_test_002", "total_cents": 12000, "status": "rejected"}
    )
    receipt_1 = EvidenceReceipt(
        id=block_1["receipt_id"],
        run_id=block_1["run_id"],
        scenario_id=block_1["scenario_id"],
        final_outcome="SUCCESS",
        previous_event_hash=block_1["previous_event_hash"],
        event_hash=block_1["event_hash"],
        payload_hash=block_1["payload_hash"],
        receipt_data=block_1["receipt_data"],
        signature=block_1["signature"]
    )
    db_session.add(receipt_1)
    await db_session.commit()

    # 3. Verify clean chain
    verification = await TamperEvidentEvidenceLedger.verify_chain(db_session)
    assert verification["valid"] is True
    assert verification["tamper_detected"] is False

    # 4. Tamper with block 0 payload (simulate malicious DB update)
    tampered_data = copy.deepcopy(receipt_0.receipt_data)
    tampered_data["total_cents"] = 99999999  # Attacker modified order amount
    receipt_0.receipt_data = tampered_data
    await db_session.commit()

    # 5. Verify tampering is detected
    tamper_check = await TamperEvidentEvidenceLedger.verify_chain(db_session)
    assert tamper_check["valid"] is False
    assert tamper_check["tamper_detected"] is True
    assert tamper_check["error_code"] == "CORRUPTED_PAYLOAD"
    assert "Tampering detected" in tamper_check["message"]
