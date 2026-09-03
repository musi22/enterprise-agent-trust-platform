// API_BASE is empty string on Vercel (no backend), so all fetches will fail gracefully
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

// Determine if we're running in demo/offline mode (no backend configured)
export const IS_DEMO_MODE = !API_BASE || API_BASE === "";

async function safeFetch(url: string, options?: RequestInit) {
  if (IS_DEMO_MODE) {
    throw new Error("DEMO_MODE");
  }
  try {
    const res = await fetch(url, { ...options, cache: "no-store" });
    return res;
  } catch {
    throw new Error("BACKEND_OFFLINE");
  }
}

export async function fetchHealth() {
  if (IS_DEMO_MODE) return { status: "demo", version: "1.0.0" };
  try {
    const res = await fetch(`${API_BASE}/health/ready`, { cache: "no-store" });
    return res.json();
  } catch {
    return { status: "offline" };
  }
}

export async function fetchScenarios() {
  const res = await safeFetch(`${API_BASE}/api/v1/scenarios`);
  if (!res.ok) throw new Error("Failed to load scenarios");
  return res.json();
}

export async function fetchLatestBenchmark() {
  const res = await safeFetch(`${API_BASE}/api/v1/benchmarks/latest`);
  if (!res.ok) throw new Error("Failed to load benchmark metrics");
  return res.json();
}

export async function fetchReleaseGate() {
  const res = await safeFetch(`${API_BASE}/api/v1/release-gate`);
  if (!res.ok) throw new Error("Failed to load release gate");
  return res.json();
}

export async function executeAgentRun(payload: {
  scenario_id?: string;
  query?: string;
  agent_mode: string;
  seed: number;
}) {
  const res = await safeFetch(`${API_BASE}/api/v1/runs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Execution failed" }));
    throw new Error(err.detail || "Agent execution failed");
  }
  return res.json();
}

export async function fetchRunTrace(runId: string) {
  const res = await safeFetch(`${API_BASE}/api/v1/runs/${runId}/trace`);
  if (!res.ok) throw new Error(`Failed to load trace for run ${runId}`);
  return res.json();
}

export async function fetchApprovals() {
  const res = await safeFetch(`${API_BASE}/api/v1/approvals`);
  if (!res.ok) throw new Error("Failed to load approvals");
  return res.json();
}

export async function decideApproval(approvalId: string, decision: "approved" | "rejected") {
  const res = await safeFetch(`${API_BASE}/api/v1/approvals/${approvalId}/decision`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ decision }),
  });
  if (!res.ok) throw new Error("Approval decision failed");
  return res.json();
}

export async function fetchEvidenceReceipts() {
  const res = await safeFetch(`${API_BASE}/api/v1/evidence`);
  if (!res.ok) throw new Error("Failed to load evidence receipts");
  return res.json();
}

export async function verifyLedger() {
  const res = await safeFetch(`${API_BASE}/api/v1/evidence/verify`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Ledger verification call failed");
  return res.json();
}

export async function simulateTampering() {
  const res = await safeFetch(`${API_BASE}/api/v1/evidence/tamper-test`, {
    method: "POST",
  });
  return res.json();
}
