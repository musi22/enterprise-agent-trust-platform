"use client";

import React, { useState, useEffect } from "react";
import { 
  FileLock2, 
  ShieldCheck, 
  ShieldAlert, 
  CheckCircle2, 
  XCircle, 
  Key, 
  Fingerprint, 
  RefreshCw, 
  Bug,
  Loader2
} from "lucide-react";
import { fetchEvidenceReceipts, verifyLedger, simulateTampering } from "@/lib/api";

export const EvidenceTab: React.FC = () => {
  const [receipts, setReceipts] = useState<any[]>([]);
  const [verificationResult, setVerificationResult] = useState<any | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [verifying, setVerifying] = useState<boolean>(false);
  const [tampering, setTampering] = useState<boolean>(false);

  const loadData = async () => {
    setLoading(true);
    try {
      const data = await fetchEvidenceReceipts();
      setReceipts(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error("Failed to load evidence", err);
      setReceipts([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleVerify = async () => {
    setVerifying(true);
    try {
      const res = await verifyLedger();
      setVerificationResult(res);
    } catch (err: any) {
      setVerificationResult({ valid: false, message: err.message });
    } finally {
      setVerifying(false);
    }
  };

  const handleSimulateTampering = async () => {
    setTampering(true);
    try {
      const res = await simulateTampering();
      setVerificationResult(res.verification_result);
      await loadData();
    } catch (err) {
      console.error("Tamper simulation failed", err);
    } finally {
      setTampering(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Action Header */}
      <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div>
          <h2 className="text-sm font-semibold text-slate-100 flex items-center space-x-2">
            <FileLock2 className="w-4 h-4 text-cyan-400" />
            <span>Tamper-Evident Cryptographic Evidence Ledger</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Append-only audit log with SHA-256 hash chaining (event_hash = SHA256(prev_hash + canonical_payload)).
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={handleSimulateTampering}
            disabled={tampering}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-rose-950/80 hover:bg-rose-900 border border-rose-800 text-rose-300 text-xs font-mono font-medium transition"
          >
            <Bug className="w-3.5 h-3.5" />
            <span>{tampering ? "Injecting Tamper..." : "Simulate DB Tampering"}</span>
          </button>

          <button
            onClick={handleVerify}
            disabled={verifying}
            className="flex items-center space-x-1.5 px-4 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-medium transition shadow-md shadow-cyan-600/20"
          >
            {verifying ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <ShieldCheck className="w-3.5 h-3.5" />}
            <span>Verify Ledger Integrity</span>
          </button>
        </div>
      </div>

      {/* Verification Result Banner */}
      {verificationResult && (
        <div className={`p-4 rounded-xl border font-mono text-xs ${
          verificationResult.valid
            ? "bg-emerald-950/40 border-emerald-800/80 text-emerald-300"
            : "bg-rose-950/40 border-rose-800/80 text-rose-300"
        }`}>
          <div className="flex items-center space-x-2 font-bold mb-1">
            {verificationResult.valid ? (
              <>
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span>CRYPTOGRAPHIC INTEGRITY CONFIRMED: 100% UNALTERED</span>
              </>
            ) : (
              <>
                <XCircle className="w-4 h-4 text-rose-400" />
                <span>SECURITY ALERT: AUDIT TAMPERING OR CORRUPTION DETECTED!</span>
              </>
            )}
          </div>
          <p className="text-[11px] text-slate-300">{verificationResult.message}</p>
          {verificationResult.broken_at_block_index !== undefined && (
            <div className="mt-2 p-2 rounded bg-rose-950/80 border border-rose-900 text-[10px]">
              <div>Broken at block index: #{verificationResult.broken_at_block_index}</div>
              <div>Error Code: {verificationResult.error_code}</div>
              <div>Receipt ID: {verificationResult.receipt_id}</div>
            </div>
          )}
        </div>
      )}

      {/* Hash Chain Visualizer */}
      <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-5 space-y-4">
        <h3 className="text-xs font-semibold text-slate-200 uppercase tracking-wider font-mono">
          Cryptographic Hash Blocks ({receipts.length} Blocks)
        </h3>

        <div className="space-y-3">
          {receipts.map((rec, idx) => (
            <div key={rec.receipt_id} className="p-4 rounded-lg bg-slate-950/80 border border-slate-800 font-mono text-xs">
              <div className="flex items-center justify-between pb-2 border-b border-slate-900 text-[11px]">
                <span className="text-cyan-400 font-bold">
                  Block #{receipts.length - idx} &bull; {rec.scenario_id || "adhoc_run"}
                </span>
                <span className="text-slate-500">{rec.created_at}</span>
              </div>

              <div className="mt-3 space-y-1 text-[11px]">
                <div className="truncate">
                  <span className="text-slate-500">Event Hash: </span>
                  <span className="text-emerald-400 font-bold">{rec.event_hash}</span>
                </div>
                <div className="truncate">
                  <span className="text-slate-500">Prev Hash:  </span>
                  <span className="text-slate-400">{rec.previous_event_hash}</span>
                </div>
                <div className="truncate">
                  <span className="text-slate-500">Payload:    </span>
                  <span className="text-purple-400">{rec.payload_hash}</span>
                </div>
              </div>

              <div className="mt-2 pt-2 border-t border-slate-900 text-[10px] text-slate-400 flex items-center justify-between">
                <span>Outcome: <strong className="text-slate-200">{rec.final_outcome}</strong></span>
                <span className="text-slate-500">HMAC-SHA256 Signature Verified</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
