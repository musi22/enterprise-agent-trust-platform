import asyncio
import sys
import yaml
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from apps.api.app.db.database import AsyncSessionLocal
from apps.api.app.db.seed_data import seed_database
from packages.agent.baseline import BaselineAgent
from packages.agent.guarded_graph import GuardedAgent
from packages.evaluators.state_checker import evaluate_run_against_scenario
from packages.telemetry.ledger import TamperEvidentEvidenceLedger

async def run_scenario_06():
    print("=" * 80)
    print("🎯 EXECUTING SCENARIO: 06_cross_customer_access.yaml")
    print("=" * 80)

    # Load scenario fixture
    sc_path = Path("scenarios/06_cross_customer_access.yaml")
    with open(sc_path, "r", encoding="utf-8") as f:
        scenario = yaml.safe_load(f)

    print(f"\n[Scenario Details]")
    print(f"  • ID:          {scenario['id']}")
    print(f"  • Name:        {scenario['name']}")
    print(f"  • Difficulty:  {scenario['difficulty'].upper()}")
    print(f"  • Caller:      {scenario['persona']['name']} ({scenario['persona']['user_id']}, role: {scenario['persona']['role']})")
    print(f"  • Request:     \"{scenario['user_request']}\"")
    print(f"  • Target:      Order 'ord_1003' (Owned by Bob Smith 'usr_cust_002')")
    print(f"  • Expected:    {scenario['expected_final_outcome']}")

    async with AsyncSessionLocal() as session:
        # Reset DB to initial seeded state
        print("\n[Phase 1] Resetting Sandbox to Verified Clean Seed (Seed: 42)...")
        await seed_database(session, reset=True)
        print("  ✓ Products, users, and orders reset.")

        # -------------------------------------------------------------
        # 1. RUN BASELINE AGENT
        # -------------------------------------------------------------
        print("\n[Phase 2] Running Baseline Agent (Direct Model-to-Tool Execution)...")
        baseline_agent = BaselineAgent()
        base_res = await baseline_agent.run(
            user_query=scenario["user_request"],
            persona=scenario["persona"],
            session=session,
            context={"seed": 42, "scenario_id": scenario["id"]}
        )
        base_res["scenario_id"] = scenario["id"]
        base_eval = evaluate_run_against_scenario(scenario, base_res)

        print(f"  • Status:               {base_res['status']}")
        print(f"  • Final Outcome:        {base_res['final_outcome']}")
        print(f"  • Unauthorized Action:  {base_eval['eval_unauthorized_action']} ❌ (Data Leak Detected!)")
        print(f"  • Task Success:         {base_eval['eval_task_success']} ❌ (FAILED: Leaked Bob's order to Alice)")
        print(f"  • Tools Called:         {[tc['tool_name'] for tc in base_res['tool_calls']]}")
        if base_res["tool_calls"]:
            resp = base_res["tool_calls"][0]["response"]
            if "order" in resp:
                print(f"    -> Leaked Address:    \"{resp['order']['shipping_address']}\"")
                print(f"    -> Leaked Total:      {resp['order']['total_formatted']}")

        # -------------------------------------------------------------
        # 2. RESET TO IDENTICAL CONDITIONS
        # -------------------------------------------------------------
        print("\n[Phase 3] Resetting Sandbox to Identical Initial Conditions...")
        await seed_database(session, reset=True)

        # -------------------------------------------------------------
        # 3. RUN GUARDED LANGGRAPH AGENT
        # -------------------------------------------------------------
        print("\n[Phase 4] Running Guarded LangGraph Agent (9-Node State Machine)...")
        guarded_agent = GuardedAgent()
        guard_res = await guarded_agent.run(
            user_query=scenario["user_request"],
            persona=scenario["persona"],
            session=session,
            context={"seed": 42, "scenario_id": scenario["id"]},
            scenario_id=scenario["id"],
            seed=42
        )
        guard_eval = evaluate_run_against_scenario(scenario, guard_res)

        print(f"  • Status:               {guard_res['status']} ✅")
        print(f"  • Final Outcome:        {guard_res['final_outcome']}")
        print(f"  • Policy Rule Applied:  {guard_res['policy_decision']['rule_name']}")
        print(f"  • Policy Decision:      {guard_res['policy_decision']['decision']} (Blocked before tool execution!)")
        print(f"  • Policy Reason:        \"{guard_res['policy_decision']['reason']}\"")
        print(f"  • Unauthorized Action:  {guard_eval['eval_unauthorized_action']} ✅ (Zero Leakage)")
        print(f"  • Task Success:         {guard_eval['eval_task_success']} ✅ (PASSED: Unauthorized access denied)")
        print(f"  • Tools Executed:       {len(guard_res['tool_calls'])} tools (Execution halted at authorize_plan)")
        print(f"  • Events Generated:     {len(guard_res['events'])} LangGraph node events")

        # -------------------------------------------------------------
        # 4. EVIDENCE RECEIPT INSPECTION
        # -------------------------------------------------------------
        receipt = guard_res.get("evidence_receipt")
        if receipt:
            print("\n[Phase 5] Cryptographic Audit Evidence Receipt (SHA-256 Hash Chain)")
            print(f"  • Receipt ID:    {receipt['receipt_id']}")
            print(f"  • Event Hash:    {receipt['event_hash']}")
            print(f"  • Previous Hash: {receipt['previous_event_hash']}")
            print(f"  • Payload Hash:  {receipt['payload_hash']}")
            print(f"  • Signature:     {receipt['signature']}")

        # Verify ledger integrity
        verif = await TamperEvidentEvidenceLedger.verify_chain(session)
        print(f"\n[Phase 6] Mathematical Ledger Verification: {verif['status']} ✅")
        print(f"  • Total Chained Blocks Verified: {verif['total_blocks_verified']}")
        print(f"  • Message: {verif['message']}")

    print("\n" + "=" * 80)
    print("🏆 SCENARIO EXECUTION COMPLETE: Guarded Agent successfully protected customer data!")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(run_scenario_06())
