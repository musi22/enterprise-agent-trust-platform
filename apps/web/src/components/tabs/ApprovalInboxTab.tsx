"use client";

import React, { useState, useEffect } from "react";
import { 
  Inbox, 
  Check, 
  X, 
  Clock, 
  AlertCircle, 
  UserCheck, 
  RefreshCw,
  Loader2
} from "lucide-react";
import { fetchApprovals, decideApproval } from "@/lib/api";

export const ApprovalInboxTab: React.FC = () => {
  const [approvals, setApprovals] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const data = await fetchApprovals();
      setApprovals(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error("Failed to load approvals", err);
      setApprovals([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleDecision = async (approvalId: string, decision: "approved" | "rejected") => {
    setActionLoading(approvalId);
    try {
      await decideApproval(approvalId, decision);
      await loadData();
    } catch (err) {
      console.error("Decision failed", err);
    } finally {
      setActionLoading(null);
    }
  };

  const pendingCount = approvals.filter(a => a.status === "pending").length;

  return (
    <div className="space-y-6">
      {/* Header Bar */}
      <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-4 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="p-2 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-400">
            <Inbox className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-slate-100 flex items-center space-x-2">
              <span>Human Approval Inbox (HITL)</span>
              <span className="px-2 py-0.5 rounded-full text-xs font-mono font-bold bg-amber-950 text-amber-400 border border-amber-800">
                {pendingCount} Pending
              </span>
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Actions exceeding policy thresholds ($50+ refunds, hazardous claims) automatically pause for supervisor sign-off.
            </p>
          </div>
        </div>

        <button
          onClick={loadData}
          className="p-2 rounded-lg bg-slate-950 hover:bg-slate-800 border border-slate-800 text-slate-400 hover:text-slate-200 transition"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {/* Approvals List */}
      <div className="space-y-4">
        {approvals.map((appr) => {
          const isPending = appr.status === "pending";
          const isActing = actionLoading === appr.approval_id;

          return (
            <div 
              key={appr.approval_id} 
              className={`p-5 rounded-xl border transition ${
                isPending 
                  ? "bg-slate-900/90 border-amber-800/60 shadow-lg shadow-amber-950/10"
                  : "bg-slate-900/40 border-slate-800/60 opacity-80"
              }`}
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-800">
                <div className="flex items-center space-x-2">
                  <span className="font-mono text-xs font-bold text-slate-200 uppercase">
                    {appr.action_type.replace(/_/g, " ")}
                  </span>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-mono uppercase font-bold ${
                    appr.status === "pending" ? "bg-amber-950 text-amber-400 border border-amber-800" :
                    appr.status === "approved" ? "bg-emerald-950 text-emerald-400 border border-emerald-800" :
                    "bg-rose-950 text-rose-400 border border-rose-800"
                  }`}>
                    {appr.status}
                  </span>
                </div>

                <div className="text-xs font-mono text-slate-400">
                  Run ID: <span className="text-cyan-400">{appr.run_id.slice(0, 8)}...</span>
                </div>
              </div>

              {/* Rationale & Payload */}
              <div className="mt-3 space-y-2 text-xs">
                <div>
                  <span className="text-slate-400">Policy Trigger Reason: </span>
                  <span className="text-amber-300 font-medium">{appr.reason}</span>
                </div>

                <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800 font-mono text-[11px] text-slate-300 overflow-x-auto">
                  <span className="text-slate-500 block mb-1 text-[10px] uppercase">Proposed Action Payload:</span>
                  {JSON.stringify(appr.proposed_payload, null, 2)}
                </div>
              </div>

              {/* Action Buttons for Pending items */}
              {isPending && (
                <div className="mt-4 flex items-center justify-end space-x-3 pt-3 border-t border-slate-800">
                  <button
                    onClick={() => handleDecision(appr.approval_id, "rejected")}
                    disabled={isActing}
                    className="flex items-center space-x-1.5 px-4 py-1.5 rounded-lg bg-rose-950/70 hover:bg-rose-900 border border-rose-800 text-rose-300 text-xs font-semibold transition"
                  >
                    <X className="w-3.5 h-3.5" />
                    <span>Reject Action</span>
                  </button>
                  <button
                    onClick={() => handleDecision(appr.approval_id, "approved")}
                    disabled={isActing}
                    className="flex items-center space-x-1.5 px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold transition shadow-md shadow-emerald-600/20"
                  >
                    {isActing ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Check className="w-3.5 h-3.5" />}
                    <span>Approve & Authorize</span>
                  </button>
                </div>
              )}
            </div>
          );
        })}

        {approvals.length === 0 && !loading && (
          <div className="p-12 text-center text-slate-500 text-xs font-mono border border-dashed border-slate-800 rounded-xl">
            No approval requests recorded. Execute Scenario 08 ($120 refund) or Scenario 20 to trigger human approval!
          </div>
        )}
      </div>
    </div>
  );
};
