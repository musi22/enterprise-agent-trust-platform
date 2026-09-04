"use client";

import React, { useState } from "react";
import { 
  Play, 
  RotateCcw, 
  CheckCircle2, 
  XCircle, 
  AlertCircle, 
  Clock, 
  ShieldAlert, 
  Tag, 
  ExternalLink,
  Loader2
} from "lucide-react";
import { executeAgentRun } from "@/lib/api";

interface ScenarioLabTabProps {
  scenarios: any[];
  onViewTrace: (runId: string) => void;
}

export const ScenarioLabTab: React.FC<ScenarioLabTabProps> = ({ scenarios, onViewTrace }) => {
  const [selectedScenarioId, setSelectedScenarioId] = useState<string>("01_catalog_search");
  const [agentMode, setAgentMode] = useState<"baseline" | "guarded">("guarded");
  const [providerName, setProviderName] = useState<"deterministic_mock" | "gemini">("deterministic_mock");
  const [useCustomQuery, setUseCustomQuery] = useState<boolean>(false);
  const [customQuery, setCustomQuery] = useState<string>("");
  const [seed, setSeed] = useState<number>(42);
  const [loading, setLoading] = useState<boolean>(false);
  const [lastRunResult, setLastRunResult] = useState<any | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const currentScenario = scenarios.find((s) => s.id === selectedScenarioId) || scenarios[0];

  const handleRun = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const res = await executeAgentRun({
        scenario_id: useCustomQuery ? undefined : selectedScenarioId,
        query: useCustomQuery ? customQuery : undefined,
        agent_mode: agentMode,
        provider_name: providerName,
        seed: Number(seed),
      });
      setLastRunResult(res);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to execute scenario");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Left Column: Scenario Catalog */}
      <div className="lg:col-span-1 bg-slate-900/70 border border-slate-800 rounded-xl p-4 flex flex-col h-[760px]">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <h3 className="text-sm font-semibold text-slate-100">Scenarios ({scenarios.length})</h3>
          <span className="text-[11px] text-slate-400 font-mono">Deterministic Ground-Truth</span>
        </div>

        <div className="overflow-y-auto flex-1 mt-3 space-y-1.5 pr-1">
          {scenarios.map((sc) => {
            const isSelected = sc.id === selectedScenarioId;
            return (
              <button
                key={sc.id}
                onClick={() => {
                  setSelectedScenarioId(sc.id);
                  setLastRunResult(null);
                }}
                className={`w-full text-left p-2.5 rounded-lg text-xs transition border ${
                  isSelected
                    ? "bg-cyan-950/50 border-cyan-700/80 text-cyan-200 shadow-sm"
                    : "bg-slate-950/40 border-slate-800/60 text-slate-400 hover:bg-slate-800/50 hover:text-slate-200"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono text-[11px] text-slate-500 font-semibold">{sc.id}</span>
                  <span className={`text-[10px] px-1.5 py-0.2 rounded font-mono uppercase ${
                    sc.difficulty === "critical" ? "bg-rose-950 text-rose-400 border border-rose-800" :
                    sc.difficulty === "hard" ? "bg-amber-950 text-amber-400 border border-amber-800" :
                    "bg-slate-800 text-slate-400"
                  }`}>
                    {sc.difficulty}
                  </span>
                </div>
                <div className="font-medium text-slate-200 mt-1 truncate">{sc.name}</div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Right Column: Execution Workbench & Outcome Inspector */}
      <div className="lg:col-span-2 space-y-6">
        {/* Scenario Config & Execution Panel */}
        <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-800">
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-base font-semibold text-slate-100">{currentScenario?.name}</h2>
                <span className="text-xs font-mono text-cyan-400 bg-cyan-950 border border-cyan-800 px-2 py-0.5 rounded">
                  {currentScenario?.id}
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-1">{currentScenario?.description}</p>
            </div>

            {/* Persona Tag */}
            <div className="px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-xs font-mono">
              <span className="text-slate-500">Persona: </span>
              <span className="text-slate-200 font-semibold">{currentScenario?.persona?.name}</span>
              <span className="text-cyan-400 ml-1">({currentScenario?.persona?.role})</span>
            </div>
          </div>

          {/* Prompt Mode Switcher & User Request Input Box */}
          <div className="mt-4 p-3.5 rounded-lg bg-slate-950 border border-slate-800/80">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider block">
                {useCustomQuery ? "Interactive Real User Input" : "Synthetic Scenario Query"}
              </span>
              <button
                type="button"
                onClick={() => setUseCustomQuery(!useCustomQuery)}
                className="text-[11px] font-mono text-cyan-400 hover:text-cyan-300 underline"
              >
                {useCustomQuery ? "← Switch to Pre-packaged Scenario" : "⚡ Real User Custom Prompt Mode"}
              </button>
            </div>

            {useCustomQuery ? (
              <input
                type="text"
                value={customQuery}
                onChange={(e) => setCustomQuery(e.target.value)}
                placeholder="Type real user natural language query (e.g. 'Cancel order ord_1002 and refund me $20')"
                className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded text-sm text-cyan-200 font-mono focus:outline-none focus:border-cyan-500"
              />
            ) : (
              <p className="text-sm font-mono text-cyan-300">"{currentScenario?.user_request}"</p>
            )}
          </div>

          {/* Controls Bar */}
          <div className="mt-5 flex flex-wrap items-center justify-between gap-4 pt-4 border-t border-slate-800">
            <div className="flex flex-wrap items-center gap-3">
              {/* Agent Mode Toggle */}
              <div className="flex items-center space-x-1 bg-slate-950 border border-slate-800 p-1 rounded-lg">
                <button
                  type="button"
                  onClick={() => setAgentMode("baseline")}
                  className={`px-3 py-1 text-xs font-medium rounded transition ${
                    agentMode === "baseline"
                      ? "bg-slate-800 text-slate-100 shadow"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  Baseline Mode
                </button>
                <button
                  type="button"
                  onClick={() => setAgentMode("guarded")}
                  className={`px-3 py-1 text-xs font-medium rounded transition ${
                    agentMode === "guarded"
                      ? "bg-cyan-600 text-white shadow"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  Guarded Mode
                </button>
              </div>

              {/* Provider Selector */}
              <div className="flex items-center space-x-1.5 text-xs font-mono">
                <span className="text-slate-400">LLM Provider:</span>
                <select
                  value={providerName}
                  onChange={(e: any) => setProviderName(e.target.value)}
                  className="bg-slate-950 border border-slate-800 text-slate-200 px-2 py-1 rounded text-xs focus:outline-none focus:border-cyan-500"
                >
                  <option value="deterministic_mock">Deterministic Mock</option>
                  <option value="gemini">Google Gemini LLM</option>
                </select>
              </div>

              {/* Seed input */}
              <div className="flex items-center space-x-1.5 text-xs font-mono">
                <span className="text-slate-400">Seed:</span>
                <input
                  type="number"
                  value={seed}
                  onChange={(e) => setSeed(Number(e.target.value))}
                  className="w-16 px-2 py-1 bg-slate-950 border border-slate-800 rounded text-slate-200 text-center font-mono focus:outline-none focus:border-cyan-500"
                />
              </div>
            </div>

            {/* Run Button */}
            <button
              onClick={handleRun}
              disabled={loading}
              className={`flex items-center space-x-2 px-5 py-2 rounded-lg text-xs font-semibold text-white transition shadow-lg ${
                loading
                  ? "bg-slate-700 cursor-not-allowed"
                  : agentMode === "guarded"
                  ? "bg-cyan-600 hover:bg-cyan-500 shadow-cyan-600/20"
                  : "bg-slate-700 hover:bg-slate-600 shadow-slate-700/20"
              }`}
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Executing Pipeline...</span>
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 fill-white" />
                  <span>Execute {agentMode === "guarded" ? "Guarded Agent" : "Baseline Agent"}</span>
                </>
              )}
            </button>
          </div>

          {errorMsg && (
            <div className="mt-3 p-3 rounded bg-rose-950/50 border border-rose-800 text-rose-300 text-xs">
              {errorMsg}
            </div>
          )}
        </div>

        {/* Live Execution Output Inspector */}
        {lastRunResult && (
          <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5 space-y-4 animate-fadeIn">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center space-x-2">
                <span className="text-xs font-semibold text-slate-300">Run Result</span>
                <span className={`text-[11px] font-mono font-bold px-2 py-0.5 rounded uppercase ${
                  lastRunResult.status === "SUCCESS" ? "bg-emerald-950 text-emerald-400 border border-emerald-800" :
                  lastRunResult.status === "APPROVAL_PENDING" ? "bg-amber-950 text-amber-400 border border-amber-800" :
                  lastRunResult.status === "ESCALATED" ? "bg-blue-950 text-blue-400 border border-blue-800" :
                  lastRunResult.status === "REJECTED_POLICY" ? "bg-purple-950 text-purple-400 border border-purple-800" :
                  "bg-rose-950 text-rose-400 border border-rose-800"
                }`}>
                  {lastRunResult.status}
                </span>
                <span className="text-xs text-slate-500 font-mono">
                  ({lastRunResult.latency_ms?.toFixed(1)} ms)
                </span>
              </div>

              <button
                onClick={() => onViewTrace(lastRunResult.run_id)}
                className="flex items-center space-x-1 text-xs text-cyan-400 hover:text-cyan-300 font-medium"
              >
                <span>Explore Full 9-Node Trace</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </button>
            </div>

            {/* Structured Decision / Outcome text */}
            <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
              <div className="text-[11px] font-mono text-slate-400 mb-1">Final Outcome:</div>
              <div className="text-xs text-slate-200 font-mono">{lastRunResult.final_outcome}</div>
            </div>

            {/* Policy Decision badge if present */}
            {lastRunResult.policy_decision && (
              <div className="p-3 rounded-lg bg-slate-950/80 border border-slate-800 flex items-start justify-between text-xs">
                <div>
                  <span className="text-slate-400">Policy Evaluation: </span>
                  <span className="font-mono text-cyan-400 font-semibold">{lastRunResult.policy_decision.rule_name}</span>
                  <p className="text-slate-400 mt-0.5">{lastRunResult.policy_decision.reason}</p>
                </div>
                <span className={`px-2 py-0.5 rounded font-mono font-bold ${
                  lastRunResult.policy_decision.decision === "ALLOW" ? "bg-emerald-950 text-emerald-400" :
                  lastRunResult.policy_decision.decision === "REQUIRE_APPROVAL" ? "bg-amber-950 text-amber-400" :
                  "bg-rose-950 text-rose-400"
                }`}>
                  {lastRunResult.policy_decision.decision}
                </span>
              </div>
            )}

            {/* Tool Calls List */}
            <div>
              <div className="text-xs font-semibold text-slate-400 mb-2">
                Tools Executed ({lastRunResult.tool_calls?.length || 0})
              </div>
              <div className="space-y-2">
                {lastRunResult.tool_calls?.map((tc: any, idx: number) => (
                  <div key={idx} className="p-2.5 rounded bg-slate-950 border border-slate-800 text-xs font-mono">
                    <div className="flex items-center justify-between text-cyan-400">
                      <span>{tc.tool_name}()</span>
                      <span className="text-slate-500 text-[10px]">{tc.latency_ms?.toFixed(1)}ms</span>
                    </div>
                    <div className="text-[11px] text-slate-400 mt-1 truncate">
                      args: {JSON.stringify(tc.arguments)}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Cryptographic Receipt preview */}
            {lastRunResult.evidence_receipt && (
              <div className="p-3 rounded-lg bg-slate-950 border border-emerald-900/40 text-xs">
                <div className="flex items-center justify-between text-emerald-400 font-mono mb-1">
                  <span>Cryptographic Evidence Receipt Chained</span>
                  <span className="text-[10px] bg-emerald-950 px-1.5 py-0.5 rounded">SHA-256</span>
                </div>
                <div className="font-mono text-[10px] text-slate-400 truncate">
                  Hash: {lastRunResult.evidence_receipt.event_hash}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
