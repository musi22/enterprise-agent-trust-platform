"use client";

import React from "react";
import { 
  ShieldAlert, 
  ShieldCheck, 
  CheckCircle2, 
  XCircle, 
  AlertTriangle, 
  Cpu, 
  Zap, 
  TrendingUp, 
  Lock,
  ArrowRight
} from "lucide-react";

interface OverviewTabProps {
  benchmark: any;
  releaseGate: any;
  onNavigateToScenarios: () => void;
}

export const OverviewTab: React.FC<OverviewTabProps> = ({ 
  benchmark, 
  releaseGate, 
  onNavigateToScenarios 
}) => {
  const base = benchmark?.baseline_metrics || {};
  const guard = benchmark?.guarded_metrics || {};
  const gates = releaseGate?.critical_gates || {};

  return (
    <div className="space-y-6">
      {/* Release Gate Banner */}
      <div className={`p-5 rounded-xl border flex flex-col md:flex-row items-start md:items-center justify-between gap-4 ${
        releaseGate?.release_gate_passed
          ? "bg-gradient-to-r from-emerald-950/40 via-slate-900 to-slate-900 border-emerald-800/60"
          : "bg-gradient-to-r from-rose-950/40 via-slate-900 to-slate-900 border-rose-800/60"
      }`}>
        <div className="flex items-start space-x-3">
          {releaseGate?.release_gate_passed ? (
            <div className="p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
              <ShieldCheck className="w-6 h-6" />
            </div>
          ) : (
            <div className="p-2 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-400">
              <ShieldAlert className="w-6 h-6" />
            </div>
          )}
          <div>
            <h2 className="text-base font-semibold text-slate-100 flex items-center gap-2">
              <span>Automated Release Gate Status:</span>
              <span className={`px-2 py-0.5 rounded text-xs font-mono font-bold ${
                releaseGate?.release_gate_passed ? "bg-emerald-900/80 text-emerald-300" : "bg-rose-900/80 text-rose-300"
              }`}>
                {releaseGate?.release_gate_passed ? "PASSED - PRODUCTION CANDIDATE" : "BLOCKED"}
              </span>
            </h2>
            <p className="text-xs text-slate-400 mt-1 max-w-2xl">
              All 20 retail operations scenarios were evaluated across Baseline and Guarded modes under seeded faults (HTTP errors, timeouts, stale caches, prompt injection).
            </p>
          </div>
        </div>

        <button
          onClick={onNavigateToScenarios}
          className="flex items-center space-x-1.5 px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-medium transition shadow-sm"
        >
          <span>Open Scenario Lab</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* KPI Comparison Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Metric 1: Task Success */}
        <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-4">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
            <span>Task Success Rate</span>
            <TrendingUp className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="flex items-baseline space-x-2">
            <span className="text-2xl font-bold font-mono text-emerald-400">
              {((guard.task_success_rate || 0) * 100).toFixed(1)}%
            </span>
            <span className="text-xs text-slate-500 font-mono">
              vs {((base.task_success_rate || 0) * 100).toFixed(1)}% base
            </span>
          </div>
          <div className="mt-2 text-[11px] text-emerald-400/90 font-medium">
            +{(Math.max(0, (guard.task_success_rate || 0) - (base.task_success_rate || 0)) * 100).toFixed(1)}% lift with Guardrails
          </div>
        </div>

        {/* Metric 2: Unauthorized Actions */}
        <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-4">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
            <span>Unauthorized Actions</span>
            <Lock className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="flex items-baseline space-x-2">
            <span className="text-2xl font-bold font-mono text-cyan-400">
              {((guard.unauthorized_action_rate || 0) * 100).toFixed(1)}%
            </span>
            <span className="text-xs text-slate-500 font-mono">
              vs {((base.unauthorized_action_rate || 0) * 100).toFixed(1)}% base
            </span>
          </div>
          <div className="mt-2 text-[11px] text-cyan-400/90 font-medium">
            Zero cross-tenant or admin leaks
          </div>
        </div>

        {/* Metric 3: Fault Recovery */}
        <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-4">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
            <span>Fault Recovery Rate</span>
            <Zap className="w-4 h-4 text-amber-400" />
          </div>
          <div className="flex items-baseline space-x-2">
            <span className="text-2xl font-bold font-mono text-amber-400">
              {((guard.recovery_rate || 0) * 100).toFixed(1)}%
            </span>
            <span className="text-xs text-slate-500 font-mono">
              vs {((base.recovery_rate || 0) * 100).toFixed(1)}% base
            </span>
          </div>
          <div className="mt-2 text-[11px] text-amber-400/90 font-medium">
            Bounded exponential backoff
          </div>
        </div>

        {/* Metric 4: Audit Receipt Completeness */}
        <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-4">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
            <span>Evidence Completeness</span>
            <ShieldCheck className="w-4 h-4 text-purple-400" />
          </div>
          <div className="flex items-baseline space-x-2">
            <span className="text-2xl font-bold font-mono text-purple-400">
              {((guard.evidence_receipt_completeness || 0) * 100).toFixed(1)}%
            </span>
            <span className="text-xs text-slate-500 font-mono">
              vs {((base.evidence_receipt_completeness || 0) * 100).toFixed(1)}% base
            </span>
          </div>
          <div className="mt-2 text-[11px] text-purple-400/90 font-medium">
            100% cryptographically chained
          </div>
        </div>
      </div>

      {/* Release Gate Checklist & Architecture Blueprint */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Critical Gate Checks */}
        <div className="lg:col-span-1 bg-slate-900/70 border border-slate-800 rounded-xl p-5">
          <h3 className="text-sm font-semibold text-slate-200 mb-3 flex items-center space-x-2">
            <span>Release Gate Evaluation Checklist</span>
          </h3>
          <div className="space-y-2.5 text-xs">
            {Object.entries(gates).map(([key, val]: [string, any]) => (
              <div key={key} className="flex items-center justify-between p-2.5 rounded-lg bg-slate-950/60 border border-slate-800/80">
                <span className="text-slate-300 font-mono capitalize">
                  {key.replace(/_/g, " ")}
                </span>
                {val ? (
                  <span className="flex items-center text-emerald-400 font-mono font-semibold">
                    <CheckCircle2 className="w-4 h-4 mr-1 text-emerald-400" /> PASS
                  </span>
                ) : (
                  <span className="flex items-center text-rose-400 font-mono font-semibold">
                    <XCircle className="w-4 h-4 mr-1 text-rose-400" /> FAIL
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Failure Taxonomy Breakdown */}
        <div className="lg:col-span-2 bg-slate-900/70 border border-slate-800 rounded-xl p-5">
          <h3 className="text-sm font-semibold text-slate-200 mb-3">
            Observed Failure Taxonomy (Baseline vs. Guarded)
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="p-4 rounded-lg bg-slate-950/60 border border-rose-900/30">
              <div className="text-xs font-semibold text-rose-400 mb-2 flex items-center space-x-1.5">
                <AlertTriangle className="w-4 h-4" />
                <span>Baseline Vulnerabilities Uncovered</span>
              </div>
              <ul className="text-xs text-slate-300 space-y-1.5 list-disc list-inside">
                <li>Cross-tenant order leaks (ord_1003 accessed without check)</li>
                <li>429 Rate Limit unhandled drops</li>
                <li>Price changes committed without user re-quote</li>
                <li>Transient 500 crashes without retry backoff</li>
                <li>Ambiguous $500 dispute executed without supervisor sign-off</li>
              </ul>
            </div>

            <div className="p-4 rounded-lg bg-slate-950/60 border border-emerald-900/30">
              <div className="text-xs font-semibold text-emerald-400 mb-2 flex items-center space-x-1.5">
                <ShieldCheck className="w-4 h-4" />
                <span>Guarded LangGraph Enforcements</span>
              </div>
              <ul className="text-xs text-slate-300 space-y-1.5 list-disc list-inside">
                <li>PolicyEngine strictly validates ownership and RBAC scopes</li>
                <li>Bounded exponential backoff heals transient 429 and 500 faults</li>
                <li>$50 refund threshold enqueues action to Approval Inbox</li>
                <li>Output validation catches silent wrong SKU mutations</li>
                <li>All write actions emit verifiable SHA-256 evidence receipts</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
