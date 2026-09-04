"use client";

import React from "react";
import { 
  ShieldCheck, 
  Activity, 
  FlaskConical, 
  GitCommit, 
  Inbox, 
  BarChart3, 
  FileLock2, 
  Server
} from "lucide-react";

interface HeaderProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  gatePassed: boolean;
  providerMode?: string;
}

export const ConsoleHeader: React.FC<HeaderProps> = ({ activeTab, setActiveTab, gatePassed, providerMode }) => {
  const navItems = [
    { id: "overview", label: "Overview", icon: Activity },
    { id: "scenarios", label: "Scenario Lab", icon: FlaskConical },
    { id: "traces", label: "Trace Explorer", icon: GitCommit },
    { id: "approvals", label: "Approval Inbox", icon: Inbox },
    { id: "benchmark", label: "Benchmark & Gates", icon: BarChart3 },
    { id: "evidence", label: "Evidence Ledger", icon: FileLock2 },
  ];

  return (
    <header className="border-b border-slate-800 bg-slate-950/80 backdrop-blur sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Title */}
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
              <ShieldCheck className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-semibold text-slate-100 text-sm tracking-wide">
                  Agentic Commerce Reliability & Recovery Lab
                </span>
                <span className="text-[10px] font-mono uppercase bg-cyan-950 text-cyan-400 border border-cyan-800 px-1.5 py-0.5 rounded">
                  v1.0.0
                </span>
              </div>
              <p className="text-[11px] text-slate-400">
                Enterprise Agent Trust & Evaluation Platform (Amazon-Inspired Retail Sandbox)
              </p>
            </div>
          </div>

          {/* Release Gate Pill */}
          <div className="hidden md:flex items-center space-x-2">
            <div className={`flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-mono font-medium border ${
              gatePassed 
                ? "bg-emerald-950/70 border-emerald-800/80 text-emerald-400"
                : "bg-rose-950/70 border-rose-800/80 text-rose-400"
            }`}>
              <span className={`w-2 h-2 rounded-full ${gatePassed ? "bg-emerald-400 animate-pulse" : "bg-rose-400"}`} />
              <span>RELEASE GATE: {gatePassed ? "PASSED" : "FAILED"}</span>
            </div>

            {/* Provider Mode Badge */}
            {providerMode && (
              <div className={`flex items-center space-x-1.5 px-2.5 py-1 rounded text-xs font-mono font-medium border ${
                providerMode.startsWith("LIVE")
                  ? "bg-green-950/70 border-green-700/60 text-green-400"
                  : "bg-blue-950/70 border-blue-700/60 text-blue-400"
              }`}>
                <span className={`w-1.5 h-1.5 rounded-full ${
                  providerMode.startsWith("LIVE") ? "bg-green-400 animate-pulse" : "bg-blue-400"
                }`} />
                <span>{providerMode.startsWith("LIVE") ? "🟢" : "🔵"} {providerMode}</span>
              </div>
            )}

            <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded bg-slate-900 border border-slate-800 text-xs text-slate-400 font-mono">
              <Server className="w-3.5 h-3.5 text-cyan-400" />
              <span>LOCAL SEED: 42</span>
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <nav className="flex space-x-1 overflow-x-auto pb-2 -mb-px">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`flex items-center space-x-2 px-3.5 py-2 text-xs font-medium rounded-md transition-all whitespace-nowrap ${
                  isActive
                    ? "bg-slate-800 text-cyan-400 border-b-2 border-cyan-400 shadow-sm"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-900/60"
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? "text-cyan-400" : "text-slate-400"}`} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>
    </header>
  );
};
