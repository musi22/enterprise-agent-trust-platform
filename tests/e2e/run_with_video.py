import asyncio, os, httpx
from playwright.async_api import async_playwright

VIDEO_DIR = r'C:\Users\RASHMI\Desktop\ENTERPRISEAI\tests\e2e\videos'
os.makedirs(VIDEO_DIR, exist_ok=True)

BASE_URL = 'http://127.0.0.1:3000'
API_BASE = 'http://127.0.0.1:8000'
RESULTS  = {}

async def run():
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.post(f'{API_BASE}/api/v1/admin/reset-db')
        print('[SETUP] DB reset:', r.json()['status'])

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=400)
        context = await browser.new_context(
            viewport={'width': 1400, 'height': 900},
            record_video_dir=VIDEO_DIR,
            record_video_size={'width': 1400, 'height': 900}
        )
        page = await context.new_page()

        print('[F1] Overview Tab...')
        await page.goto(BASE_URL, wait_until='networkidle')
        await page.wait_for_timeout(1500)
        title = await page.title()
        assert 'Agentic Commerce Reliability' in title
        header_text = await page.inner_text('header')
        assert 'RELEASE GATE: PASSED' in header_text, f'Header: {header_text[:300]}'
        assert await page.is_visible('text=Task Success Rate')
        assert await page.is_visible('text=Unauthorized Actions')
        assert await page.is_visible('text=Fault Recovery Rate')
        assert await page.is_visible('text=Evidence Completeness')
        assert await page.is_visible('text=Release Gate Evaluation Checklist')
        assert await page.is_visible('text=Observed Failure Taxonomy')
        RESULTS['Feature 1: Overview & Release Gate'] = 'PASS'
        print('[F1] PASS')
        await page.wait_for_timeout(1000)

        print('[F2] Scenario Lab...')
        await page.click('button:has-text("Scenario Lab")')
        await page.wait_for_selector('text=Scenarios (20)')
        await page.wait_for_timeout(800)
        await page.click('button:has-text("Cross-Customer Order Access Attempt")')
        await page.wait_for_timeout(800)
        assert await page.is_visible('text=06_cross_customer_access')
        await page.click('button:has-text("Guarded Mode")')
        await page.wait_for_timeout(500)
        await page.click('button:has-text("Execute Guarded Agent")')
        await page.wait_for_selector('text=REJECTED_POLICY', timeout=20000)
        assert await page.is_visible('text=resource_ownership_check')
        assert await page.is_visible('text=Cross-account violation')
        RESULTS['Feature 2: Scenario Lab & Execution'] = 'PASS'
        print('[F2] PASS')
        await page.wait_for_timeout(1200)

        print('[F3] Trace Explorer...')
        await page.click('button:has-text("Explore Full 9-Node Trace")')
        await page.wait_for_selector('text=LangGraph 9-Node Execution Timeline', timeout=12000)
        await page.wait_for_timeout(1000)
        assert await page.is_visible('text=classify_intent')
        assert await page.is_visible('text=create_plan')
        assert await page.is_visible('text=authorize_plan')
        assert await page.is_visible('text=emit_evidence_receipt')
        assert await page.is_visible('text=Tamper-Evident Evidence Chain Block')
        RESULTS['Feature 3: Trace Explorer (9-Node)'] = 'PASS'
        print('[F3] PASS')
        await page.wait_for_timeout(1200)

        print('[F4] Approval Inbox...')
        await page.click('button:has-text("Approval Inbox")')
        await page.wait_for_selector('text=Human Approval Inbox (HITL)')
        await page.wait_for_timeout(1000)
        h2 = await page.inner_text('h2')
        assert 'Human Approval Inbox' in h2
        RESULTS['Feature 4: Approval Inbox (HITL)'] = 'PASS'
        print('[F4] PASS')
        await page.wait_for_timeout(1000)

        print('[F5] Benchmark & Gates...')
        await page.click('button:has-text("Benchmark & Gates")')
        await page.wait_for_selector('text=Dual-Agent Comparative Benchmark')
        await page.wait_for_timeout(1000)
        assert await page.is_visible('text=Baseline Agent')
        assert await page.is_visible('text=Guarded LangGraph Agent')
        assert await page.is_visible('text=Task Success Rate')
        assert await page.is_visible('text=Unauthorized Action Rate')
        assert await page.is_visible('text=Fault Recovery Rate')
        assert await page.is_visible('text=Download CSV')
        assert await page.is_visible('text=Download Raw JSON')
        RESULTS['Feature 5: Benchmark & Release Gate'] = 'PASS'
        print('[F5] PASS')
        await page.wait_for_timeout(1200)

        print('[F6] Evidence Ledger...')
        await page.click('button:has-text("Evidence Ledger")')
        await page.wait_for_selector('text=Tamper-Evident Cryptographic Evidence Ledger')
        await page.wait_for_timeout(800)
        await page.click('button:has-text("Verify Ledger Integrity")')
        await page.wait_for_selector('text=CRYPTOGRAPHIC INTEGRITY CONFIRMED', timeout=12000)
        await page.wait_for_timeout(800)
        assert await page.is_visible('text=100% UNALTERED')
        await page.click('button:has-text("Simulate DB Tampering")')
        await page.wait_for_selector('text=SECURITY ALERT: AUDIT TAMPERING OR CORRUPTION DETECTED!', timeout=12000)
        await page.wait_for_timeout(800)
        assert await page.is_visible('text=Broken at block index')
        await page.click('button:has-text("Verify Ledger Integrity")')
        await page.wait_for_timeout(800)
        assert await page.is_visible('text=SECURITY ALERT: AUDIT TAMPERING')
        RESULTS['Feature 6: Evidence Ledger & Tamper Detect'] = 'PASS'
        print('[F6] PASS')
        await page.wait_for_timeout(1500)

        video_path = await page.video.path()
        print(f'[VIDEO] Saved to: {video_path}')
        await context.close()
        await browser.close()

    print()
    print('=' * 58)
    print('  ENTERPRISE AI - FULL FEATURE TEST RESULTS')
    print('=' * 58)
    all_pass = True
    for feat, status in RESULTS.items():
        icon = '[PASS]' if status == 'PASS' else '[FAIL]'
        print(f'  {icon}  {feat}')
        if status != 'PASS':
            all_pass = False
    print('=' * 58)
    print('  OVERALL:', 'ALL 6 FEATURES PASSED' if all_pass else 'SOME FAILED')
    print('=' * 58)

asyncio.run(run())
