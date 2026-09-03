import asyncio
import os
from pathlib import Path
from playwright.async_api import async_playwright

BASE_URL = "http://127.0.0.1:3005"
OUT_DIR = Path("results/screenshots")

async def capture_all_screenshots():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1400, "height": 900})
        page = await context.new_page()

        print("[Playwright] Capturing screenshot: 01_overview.png...")
        await page.goto(BASE_URL, wait_until="networkidle")
        await page.screenshot(path=str(OUT_DIR / "01_overview.png"), full_page=True)

        print("[Playwright] Capturing screenshot: 02_scenario_lab.png...")
        await page.click("button:has-text('Scenario Lab')")
        await page.wait_for_selector("text=Scenarios (20)")
        await page.click("button:has-text('Cross-Customer Order Access Attempt')")
        await page.click("button:has-text('Guarded Mode')")
        await page.click("button:has-text('Execute Guarded Agent')")
        await page.wait_for_selector("text=REJECTED_POLICY", timeout=15000)
        await page.screenshot(path=str(OUT_DIR / "02_scenario_lab.png"), full_page=True)

        print("[Playwright] Capturing screenshot: 03_trace_explorer.png...")
        await page.click("button:has-text('Explore Full 9-Node Trace')")
        await page.wait_for_selector("text=LangGraph 9-Node Execution Timeline", timeout=10000)
        await page.screenshot(path=str(OUT_DIR / "03_trace_explorer.png"), full_page=True)

        print("[Playwright] Capturing screenshot: 04_approval_inbox.png...")
        await page.click("button:has-text('Approval Inbox')")
        await page.wait_for_selector("text=Human Approval Inbox (HITL)")
        await page.screenshot(path=str(OUT_DIR / "04_approval_inbox.png"), full_page=True)

        print("[Playwright] Capturing screenshot: 05_benchmark_comparison.png...")
        await page.click("button:has-text('Benchmark & Gates')")
        await page.wait_for_selector("text=Dual-Agent Comparative Benchmark")
        await page.screenshot(path=str(OUT_DIR / "05_benchmark_comparison.png"), full_page=True)

        print("[Playwright] Capturing screenshot: 06_evidence_ledger_verified.png...")
        await page.click("button:has-text('Evidence Ledger')")
        await page.wait_for_selector("text=Tamper-Evident Cryptographic Evidence Ledger")
        await page.click("button:has-text('Verify Ledger Integrity')")
        await page.wait_for_selector("text=CRYPTOGRAPHIC INTEGRITY CONFIRMED", timeout=10000)
        await page.screenshot(path=str(OUT_DIR / "06_evidence_ledger_verified.png"), full_page=True)

        print("[Playwright] Capturing screenshot: 07_evidence_ledger_tampered.png...")
        await page.click("button:has-text('Simulate DB Tampering')")
        await page.wait_for_selector("text=SECURITY ALERT: AUDIT TAMPERING OR CORRUPTION DETECTED!", timeout=10000)
        await page.screenshot(path=str(OUT_DIR / "07_evidence_ledger_tampered.png"), full_page=True)

        print(f"[Playwright] Successfully captured 7 high-resolution screenshots in {OUT_DIR}!")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(capture_all_screenshots())
