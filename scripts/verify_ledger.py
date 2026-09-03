import asyncio
import sys
from apps.api.app.db.database import AsyncSessionLocal
from packages.telemetry.ledger import TamperEvidentEvidenceLedger

async def run_verification():
    async with AsyncSessionLocal() as session:
        print("Running cryptographic verification on evidence ledger...")
        result = await TamperEvidentEvidenceLedger.verify_chain(session)
        print("Status:", result["status"])
        print("Total blocks verified:", result.get("total_blocks_verified", 0))
        print("Message:", result["message"])

        if not result["valid"]:
            print("CRITICAL: Ledger tampering detected!", file=sys.stderr)
            sys.exit(1)
        else:
            print("Cryptographic integrity confirmed: 0 altered or omitted blocks.")
            sys.exit(0)

if __name__ == "__main__":
    asyncio.run(run_verification())
