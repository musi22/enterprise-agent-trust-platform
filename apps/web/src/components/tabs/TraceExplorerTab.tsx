"use client";

import React, { useState, useEffect } from "react";
import { 
  GitCommit, 
  Clock, 
  ShieldCheck, 
  ShieldAlert, 
  AlertTriangle, 
  RotateCw, 
  CheckCircle2, 
  Layers,
  ChevronDown,
  ChevronRight,
  Loader2
} from "lucide-react";
import { fetchRunTrace } from "@/lib/api";

interface TraceExplorerTabProps {
  initialRunId?: string | null;
}

export const TraceExplorerTab: React.FC<TraceExplorerTabProps> = ({ initialRunId }) => {
  const [runId, setRunId] = useState<string>(initialRunId || "");
  const [trace, setTrace] = useState<any | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [expandedNodes, setExpandedNodes] = useState<Record<number, boolean>>({});

  const loadTrace = async (idToLoad: string) => {
    if (!idToLoad) return;
    setLoading(true);
    setErrorMsg(null);
    try {
      const data = await fetchRunTrace(idToLoad);
      setTrace(data);
      // Auto-expand all nodes by default
      const exp: Record<number, boolean> = {};
      data.events?.forEach((_: any, idx: number) => { exp[idx] = true; });
      setExpandedNodes(exp);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to load trace");
      setTrace(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (initialRunId) {
      setRunId(initialRunId);
      loadTrace(initialRunId);
    }
  }, [initialRunId]);

  const toggleNode = (idx: number) => {
    setExpandedNodes(prev => ({ ...prev, [idx]: !prev[idx] }));
  };

  return (
    <div className="space-y-6">
      {/* Search / Run ID Input Bar */}
      <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-4 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center space-x-2 w-full sm:w-auto flex-1">
          <span className="text-xs text-slate-400 font-mono">Run ID:</span>
          <input
            type="text"
            value={runId}
            onChange={(e) => setRunId(e.target.value)}
            placeholder="Enter UUID run identifier..."
            className="flex-1 max-w-lg px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-xs font-mono text-slate-200 focus:outline-none focus:border-cyan-500"
          />
          <button
            onClick={() => loadTrace(runId)}
            disabled={loading || !runId}
            className="px-4 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-medium transition"
          >
            {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : "Load Trace"}
          </button>
        </div>

        {trace && (
          <div className="flex items-center space-x-3 text-xs font-mono">
            <span className="text-slate-400">Mode: <strong className="text-cyan-400">{trace.agent_mode}</strong></span>
            <span className="text-slate-400">Latency: <strong className="text-emerald-400">{trace.latency_ms?.toFixed(1)}ms</strong></span>
            <span className={`px-2 py-0.5 rounded uppercase font-bold text-[10px] ${
              trace.status === "success" ? "bg-emerald-950 text-emerald-400 border border-emerald-800" :
              trace.status === "rejected_policy" ? "bg-purple-950 text-purple-400 border border-purple-800" :
              "bg-amber-950 text-amber-400 border border-amber-800"
            }`}>
              {trace.status}
            </span>
          </div>
        )}
      </div>

      {errorMsg && (
        <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-800 text-rose-300 text-xs">
          {errorMsg}
        </div>
      )}

      {/* Main Trace Timeline */}
      {trace && (
        <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between pb-4 mb-6 border-b border-slate-800">
            <div>
              <h3 className="text-sm font-semibold text-slate-100 flex items-center space-x-2">
                <Layers className="w-4 h-4 text-cyan-400" />
                <span>LangGraph 9-Node Execution Timeline</span>
              </h3>
              <p className="text-xs text-slate-400 font-mono mt-0.5">
                Query: "{trace.user_query}"
              </p>
            </div>
            <span className="text-xs font-mono text-slate-400">
              {trace.events?.length || 0} Transition Events Recorded
            </span>
          </div>

          {/* Timeline Nodes */}
          <div className="relative border-l-2 border-slate-800 ml-4 pl-6 space-y-6">
            {trace.events?.map((ev: any, idx: number) => {
              const isExpanded = !!expandedNodes[idx];
              const isPolicy = ev.node_name === "authorize_plan";
              const isTool = ev.node_name === "execute_tool";
              const isReceipt = ev.node_name === "emit_evidence_receipt";

              return (
                <div key={idx} className="relative group">
                  {/* Timeline Dot */}
                  <div className={`absolute -left-[31px] top-1.5 w-3.5 h-3.5 rounded-full border-2 bg-slate-950 ${
                    isPolicy ? "border-cyan-400 group-hover:scale-110" :
                    isReceipt ? "border-purple-400 group-hover:scale-110" :
                    isTool ? "border-emerald-400 group-hover:scale-110" :
                    "border-slate-500 group-hover:scale-110"
                  } transition`} />

                  {/* Event Card */}
                  <div className="bg-slate-950/80 border border-slate-800 rounded-lg p-3 hover:border-slate-700 transition">
                    <div 
                      onClick={() => toggleNode(idx)}
                      className="flex items-center justify-between cursor-pointer select-none"
                    >
                      <div className="flex items-center space-x-2">
                        <span className="text-xs font-mono text-cyan-400 font-bold">
                          Step {ev.step_index}: {ev.node_name}
                        </span>
                        <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-slate-800 text-slate-300">
                          {ev.event_type}
                        </span>
                      </div>
                      {isExpanded ? (
                        <ChevronDown className="w-4 h-4 text-slate-500" />
                      ) : (
                        <ChevronRight className="w-4 h-4 text-slate-500" />
                      )}
                    </div>

                    {/* Payload Details */}
                    {isExpanded && (
                      <div className="mt-3 pt-3 border-t border-slate-900 font-mono text-[11px] text-slate-300">
                        <pre className="bg-slate-900/60 p-2.5 rounded border border-slate-800/60 overflow-x-auto">
                          {JSON.stringify(ev.payload, null, 2)}
                        </pre>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Cryptographic Receipt Footer Card */}
          {trace.evidence_receipt && (
            <div className="mt-8 p-4 rounded-lg bg-purple-950/20 border border-purple-800/40 text-xs font-mono">
              <div className="flex items-center justify-between text-purple-400 font-semibold mb-2">
                <span>Tamper-Evident Evidence Chain Block</span>
                <span className="text-[10px] bg-purple-950 px-2 py-0.5 rounded border border-purple-800">
                  SHA-256 Chained
                </span>
              </div>
              <div className="space-y-1 text-[11px] text-slate-400">
                <div><span className="text-slate-500">Event Hash: </span>{trace.evidence_receipt.event_hash}</div>
                <div><span className="text-slate-500">Prev Hash:  </span>{trace.evidence_receipt.previous_event_hash}</div>
                <div><span className="text-slate-500">Signature:  </span>{trace.evidence_receipt.signature}</div>
              </div>
            </div>
          )}
        </div>
      )}

      {!trace && !loading && (
        <div className="p-12 text-center text-slate-500 text-xs font-mono border border-dashed border-slate-800 rounded-xl">
          Enter a Run ID or select a scenario from the Scenario Lab to inspect structured state machine traces.
        </div>
      )}
    </div>
  );
};
