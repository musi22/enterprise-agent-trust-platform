import pytest
from playwright.async_api import async_playwright, Page, expect

BASE_URL = "http://127.0.0.1:3005"

@pytest.mark.asyncio
async def test_all_features_e2e():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1280, "height": 800})
        page = await context.new_page()

        # -------------------------------------------------------------
        # Feature 1: Overview Tab & Release Gate
        # -------------------------------------------------------------
        print("\n[Playwright] Testing Feature 1: Overview Dashboard...")
        await page.goto(BASE_URL, wait_until="networkidle")

        # Check Title & Header
        title = await page.title()
        assert "Agentic Commerce Reliability & Recovery Lab" in title
        header_text = await page.inner_text("header")
        assert "Agentic Commerce Reliability & Recovery Lab" in header_text
        assert "RELEASE GATE: PASSED" in header_text

        # Check KPI Cards
        assert await page.is_visible("text=Task Success Rate")
        assert await page.is_visible("text=Unauthorized Actions")
        assert await page.is_visible("text=Fault Recovery Rate")
        assert await page.is_visible("text=Evidence Completeness")

        # Check Release Gate Checklist
        assert await page.is_visible("text=Release Gate Evaluation Checklist")
        assert await page.is_visible("text=zero unauthorized actions")

        # Check Failure Taxonomy
        assert await page.is_visible("text=Observed Failure Taxonomy")

        # -------------------------------------------------------------
        # Feature 2: Scenario Lab Tab & Execution
        # -------------------------------------------------------------
        print("[Playwright] Testing Feature 2: Scenario Lab & Execution...")
        await page.click("button:has-text('Scenario Lab')")
        await page.wait_for_selector("text=Scenarios (20)")

        # Select Scenario 06: Cross-Customer Access
        await page.click("button:has-text('Cross-Customer Order Access Attempt')")
        assert await page.is_visible("text=06_cross_customer_access")
        assert await page.is_visible("text=Show me the details and shipping address for order ord_1003")

        # Toggle to Guarded Mode & Click Execute
        await page.click("button:has-text('Guarded Mode')")
        await page.click("button:has-text('Execute Guarded Agent')")

        # Wait for execution output
        await page.wait_for_selector("text=REJECTED_POLICY", timeout=15000)
        assert await page.is_visible("text=resource_ownership_check")
        assert await page.is_visible("text=Cross-account violation")

        # -------------------------------------------------------------
        # Feature 3: Trace Explorer Tab & 9-Node Timeline
        # -------------------------------------------------------------
        print("[Playwright] Testing Feature 3: Trace Explorer...")
        await page.click("button:has-text('Explore Full 9-Node Trace')")
        await page.wait_for_selector("text=LangGraph 9-Node Execution Timeline", timeout=10000)

        # Verify steps in timeline
        assert await page.is_visible("text=classify_intent")
        assert await page.is_visible("text=create_plan")
        assert await page.is_visible("text=authorize_plan")
        assert await page.is_visible("text=emit_evidence_receipt")
        assert await page.is_visible("text=Tamper-Evident Evidence Chain Block")

        # -------------------------------------------------------------
        # Feature 4: Approval Inbox Tab
        # -------------------------------------------------------------
        print("[Playwright] Testing Feature 4: Approval Inbox...")
        await page.click("button:has-text('Approval Inbox')")
        await page.wait_for_selector("text=Human Approval Inbox (HITL)")

        # Check if approval items or empty state renders cleanly
        approval_header = await page.inner_text("h2")
        assert "Human Approval Inbox" in approval_header

        # -------------------------------------------------------------
        # Feature 5: Benchmark & Release Gate Tab
        # -------------------------------------------------------------
        print("[Playwright] Testing Feature 5: Benchmark & Release Gate Comparison...")
        await page.click("button:has-text('Benchmark & Gates')")
        await page.wait_for_selector("text=Dual-Agent Comparative Benchmark")

        # Check Table Metrics
        assert await page.is_visible("text=Baseline Agent")
        assert await page.is_visible("text=Guarded LangGraph Agent")
        assert await page.is_visible("text=Task Success Rate")
        assert await page.is_visible("text=Unauthorized Action Rate")
        assert await page.is_visible("text=Fault Recovery Rate")
        assert await page.is_visible("text=Download CSV")
        assert await page.is_visible("text=Download Raw JSON")

        # -------------------------------------------------------------
        # Feature 6: Evidence Ledger Tab & Cryptographic Tamper Test
        # -------------------------------------------------------------
        print("[Playwright] Testing Feature 6: Evidence Ledger & Tamper Verification...")
        await page.click("button:has-text('Evidence Ledger')")
        await page.wait_for_selector("text=Tamper-Evident Cryptographic Evidence Ledger")

        # Click Verify Ledger Integrity
        await page.click("button:has-text('Verify Ledger Integrity')")
        await page.wait_for_selector("text=CRYPTOGRAPHIC INTEGRITY CONFIRMED", timeout=10000)
        assert await page.is_visible("text=100% UNALTERED")

        # Click Simulate DB Tampering
        await page.click("button:has-text('Simulate DB Tampering')")
        await page.wait_for_selector("text=SECURITY ALERT: AUDIT TAMPERING OR CORRUPTION DETECTED!", timeout=10000)
        assert await page.is_visible("text=Broken at block index")

        # Re-verify shows detected tampering
        await page.click("button:has-text('Verify Ledger Integrity')")
        assert await page.is_visible("text=SECURITY ALERT: AUDIT TAMPERING")

        print("\n[Playwright] ✓ ALL 6 ENGINEERING CONSOLE FEATURES VERIFIED SUCCESSFULLY!")
        await browser.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_all_features_e2e())
