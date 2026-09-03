import pytest
from packages.fault_injection.rules import FaultType, FaultConfig
from packages.fault_injection.proxy import FaultInjectionProxy
from packages.sandbox_tools.context import ToolContext

@pytest.mark.asyncio
async def test_fault_injection_401(db_session):
    proxy = FaultInjectionProxy()
    proxy.register_fault(FaultConfig(
        fault_type=FaultType.HTTP_401,
        target_tool="search_catalog",
        probability=1.0,
        invocation_count=1
    ))
    ctx = ToolContext(user_id="usr_cust_001")
    res = await proxy.execute("search_catalog", {"query": "headphones"}, db_session, ctx)
    assert res["status"] == "error"
    assert res["error_code"] == "HTTP_401_UNAUTHORIZED"
    assert res["status_code"] == 401

@pytest.mark.asyncio
async def test_fault_injection_429_invocation_strike(db_session):
    proxy = FaultInjectionProxy()
    # Strike on invocation 1 only; invocation 2 should succeed normally
    proxy.register_fault(FaultConfig(
        fault_type=FaultType.HTTP_429,
        target_tool="search_catalog",
        probability=1.0,
        invocation_count=1
    ))
    ctx = ToolContext(user_id="usr_cust_001")

    # 1st invocation fails with 429
    res1 = await proxy.execute("search_catalog", {"query": "headphones"}, db_session, ctx)
    assert res1["status"] == "error"
    assert res1["error_code"] == "HTTP_429_TOO_MANY_REQUESTS"

    # 2nd invocation succeeds
    res2 = await proxy.execute("search_catalog", {"query": "headphones"}, db_session, ctx)
    assert res2["status"] == "success"
    assert res2["total_found"] > 0

@pytest.mark.asyncio
async def test_fault_injection_stale_inventory(db_session):
    proxy = FaultInjectionProxy()
    proxy.register_fault(FaultConfig(
        fault_type=FaultType.STALE_INVENTORY,
        target_tool="check_inventory",
        probability=1.0,
        invocation_count=1
    ))
    ctx = ToolContext(user_id="usr_cust_001")
    res = await proxy.execute("check_inventory", {"product_id": "prod_elec_010"}, db_session, ctx)
    assert res["status"] == "success"
    assert res["stale_cache_injected"] is True
    assert res["available_stock"] == 15  # Injected fake stock
