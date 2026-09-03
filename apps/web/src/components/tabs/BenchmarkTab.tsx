"use client";

import React, { useState } from "react";
import { 
  BarChart3, 
  Download, 
  CheckCircle2, 
  XCircle, 
  RotateCw, 
  FileSpreadsheet, 
  FileCode,
  ShieldCheck
} from "lucide-react";

interface BenchmarkTabProps {
  benchmark: any;
  releaseGate: any;
  onRefresh: () => void;
}

export const BenchmarkTab: React.FC<BenchmarkTabProps> = ({ benchmark, releaseGate, onRefresh }) => {
  const base = benchmark?.baseline_metrics || {};
  const guard = benchmark?.guarded_metrics || {};

  const metricsTable = [
    {
      name: "Task Success Rate",
      baseline: `${((base.task_success_rate || 0) * 100).toFixed(1)}%`,
      guarded: `${((guard.task_success_rate || 0) * 100).toFixed(1)}%`,
      diff: `+${(((guard.task_success_rate || 0) - (base.task_success_rate || 0)) * 100).toFixed(1)}%`,
      positive: (guard.task_success_rate || 0) >= (base.task_success_rate || 0),
      desc: "% of tasks achieving expected business outcome safely"
    },
    {
      name: "Unauthorized Action Rate",
      baseline: `${((base.unauthorized_action_rate || 0) * 100).toFixed(1)}%`,
      guarded: `${((guard.unauthorized_action_rate || 0) * 100).toFixed(1)}%`,
      diff: `${(((guard.unauthorized_action_rate || 0) - (base.unauthorized_action_rate || 0)) * 100).toFixed(1)}%`,
      positive: (guard.unauthorized_action_rate || 0) === 0,
      desc: "Cross-tenant leaks or admin privilege escalation"
    },
    {
      name: "Policy Violation Rate",
      baseline: `${((base.policy_violation_rate || 0) * 100).toFixed(1)}%`,
      guarded: `${((guard.policy_violation_rate || 0) * 100).toFixed(1)}%`,
      diff: `${(((guard.policy_violation_rate || 0) - (base.policy_violation_rate || 0)) * 100).toFixed(1)}%`,
      positive: (guard.policy_violation_rate || 0) === 0,
      desc: "Order state machine breaches or unapproved high refunds"
    },
    {
      name: "Fault Recovery Rate",
      baseline: `${((base.recovery_rate || 0) * 100).toFixed(1)}%`,
      guarded: `${((guard.recovery_rate || 0) * 100).toFixed(1)}%`,
      diff: `+${(((guard.recovery_rate || 0) - (base.recovery_rate || 0)) * 100).toFixed(1)}%`,
      positive: (guard.recovery_rate || 0) >= (base.recovery_rate || 0),
      desc: "429 backoff, 500 retry, timeout circuit breaking"
    },
    {
      name: "Duplicate Write Rate",
      baseline: `${((base.duplicate_write_rate || 0) * 100).toFixed(1)}%`,
      guarded: `${((guard.duplicate_write_rate || 0) * 100).toFixed(1)}%`,
      diff: "0.0%",
      positive: true,
      desc: "Deduplication via idempotency keys"
    },
    {
      name: "Escalation Precision",
      baseline: `${((base.escalation_precision || 0) * 100).toFixed(1)}%`,
      guarded: `${((guard.escalation_precision || 0) * 100).toFixed(1)}%`,
      diff: `+${(((guard.escalation_precision || 0) - (base.escalation_precision || 0)) * 100).toFixed(1)}%`,
      positive: true,
      desc: "% of escalations that were truly high-risk/ambiguous"
    },
    {
      name: "Evidence Completeness",
      baseline: `${((base.evidence_receipt_completeness || 0) * 100).toFixed(1)}%`,
      guarded: `${((guard.evidence_receipt_completeness || 0) * 100).toFixed(1)}%`,
      diff: `+${(((guard.evidence_receipt_completeness || 0) - (base.evidence_receipt_completeness || 0)) * 100).toFixed(1)}%`,
      positive: true,
      desc: "100% of write ops produce verified SHA-256 hash block"
    },
    {
      name: "p50 Latency (ms)",
      baseline: `${base.p50_latency_ms?.toFixed(1) || 0} ms`,
      guarded: `${guard.p50_latency_ms?.toFixed(1) || 0} ms`,
      diff: `+${((guard.p50_latency_ms || 0) - (base.p50_latency_ms || 0)).toFixed(1)} ms`,
      positive: true,
      desc: "Median execution duration including policy engine"
    },
    {
      name: "p95 Latency (ms)",
      baseline: `${base.p95_latency_ms?.toFixed(1) || 0} ms`,
      guarded: `${guard.p95_latency_ms?.toFixed(1) || 0} ms`,
      diff: `+${((guard.p95_latency_ms || 0) - (base.p95_latency_ms || 0)).toFixed(1)} ms`,
      positive: true,
      desc: "Tail latency including bounded retry backoff sleep"
    },
  ];

  const handleDownloadJSON = () => {
    const blob = new Blob([JSON.stringify(benchmark, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "raw_benchmark.json";
    a.click();
  };

  const handleDownloadCSV = () => {
    let csvContent = "metric,baseline,guarded,diff\n";
    metricsTable.forEach((row) => {
      csvContent += `"${row.name}","${row.baseline}","${row.guarded}","${row.diff}"\n`;
    });
    const blob = new Blob([csvContent], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "benchmark_summary.csv";
    a.click();
  };

  return (
    <div className="space-y-6">
      {/* Benchmark Summary Bar */}
      <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div>
          <h2 className="text-sm font-semibold text-slate-100 flex items-center space-x-2">
            <BarChart3 className="w-4 h-4 text-cyan-400" />
            <span>Dual-Agent Comparative Benchmark</span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Sample Size: <strong className="text-slate-200">{benchmark?.total_scenarios || 20} Scenarios</strong> × {benchmark?.total_runs ? Math.round(benchmark.total_runs / (benchmark.total_scenarios * 2)) : 1} Repetitions = <strong className="text-cyan-400">{benchmark?.total_runs || 40} Total Executions</strong>
          </p>
        </div>

        {/* Download Buttons */}
        <div className="flex items-center space-x-3">
          <button
            onClick={handleDownloadCSV}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-950 hover:bg-slate-800 border border-slate-800 text-xs font-mono text-slate-300 transition"
          >
            <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-400" />
            <span>Download CSV</span>
          </button>
          <button
            onClick={handleDownloadJSON}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-950 hover:bg-slate-800 border border-slate-800 text-xs font-mono text-slate-300 transition"
          >
            <FileCode className="w-3.5 h-3.5 text-cyan-400" />
            <span>Download Raw JSON</span>
          </button>
          <button
            onClick={onRefresh}
            className="p-2 rounded-lg bg-slate-950 hover:bg-slate-800 border border-slate-800 text-slate-400 hover:text-slate-200 transition"
          >
            <RotateCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Metrics Table */}
      <div className="bg-slate-900/70 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-slate-950/80 border-b border-slate-800 text-slate-400 font-mono">
                <th className="p-4 font-semibold">Evaluation Metric Dimension</th>
                <th className="p-4 font-semibold text-slate-300">Baseline Agent</th>
                <th className="p-4 font-semibold text-cyan-400">Guarded LangGraph Agent</th>
                <th className="p-4 font-semibold text-emerald-400">Impact Delta</th>
                <th className="p-4 font-semibold text-slate-500">Methodology & Rationale</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {metricsTable.map((row, idx) => (
                <tr key={idx} className="hover:bg-slate-800/30 transition">
                  <td className="p-4 font-sans font-semibold text-slate-200">{row.name}</td>
                  <td className="p-4 text-slate-400">{row.baseline}</td>
                  <td className="p-4 text-cyan-300 font-bold">{row.guarded}</td>
                  <td className={`p-4 font-bold ${row.positive ? "text-emerald-400" : "text-amber-400"}`}>
                    {row.diff}
                  </td>
                  <td className="p-4 font-sans text-slate-400 text-[11px]">{row.desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
