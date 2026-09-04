"use client";

import React, { useState } from "react";
import { 
  ShieldCheck, 
  Activity, 
  FlaskConical, 
  GitCommit, 
  Inbox, 
  BarChart3, 
  FileLock2, 
  Server,
  Play,
  X
} from "lucide-react";

interface HeaderProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  gatePassed: boolean;
  providerMode?: string;
}

export const ConsoleHeader: React.FC<HeaderProps> = ({ activeTab, setActiveTab, gatePassed, providerMode }) => {
  const [showVideoModal, setShowVideoModal] = useState(false);
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

            {/* Watch Demo Button */}
            <button
              onClick={() => setShowVideoModal(true)}
              className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-xs text-white font-medium shadow-md shadow-blue-500/20 transition-all cursor-pointer"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              <span>Watch Demo</span>
            </button>
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

      {/* Interactive Video Demo Modal */}
      {showVideoModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-in fade-in duration-200">
          <div className="bg-slate-900 border border-slate-700 rounded-xl max-w-4xl w-full overflow-hidden shadow-2xl">
            <div className="flex items-center justify-between px-5 py-3.5 border-b border-slate-800 bg-slate-950">
              <div className="flex items-center space-x-2">
                <div className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-pulse" />
                <span className="text-sm font-semibold text-slate-100">Enterprise AI Platform — End-to-End Walkthrough</span>
              </div>
              <button 
                onClick={() => setShowVideoModal(false)}
                className="text-slate-400 hover:text-white p-1 rounded-md hover:bg-slate-800 transition-colors"
                title="Close video"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-3 bg-black">
              <video 
                controls 
                autoPlay 
                playsInline
                className="w-full rounded-lg max-h-[70vh] shadow-inner"
              >
                <source src="/demo_walkthrough.mp4" type="video/mp4" />
                <source src="/demo_walkthrough.webm" type="video/webm" />
                Your browser does not support HTML5 video.
              </video>
            </div>
            <div className="px-5 py-3 bg-slate-950/80 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
              <span>Covers: Release Gates &bull; Scenario Lab &bull; Trace Explorer &bull; HITL Approvals &bull; Chaos Benchmarks &bull; Evidence Ledger</span>
              <button
                onClick={() => setShowVideoModal(false)}
                className="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded font-medium transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </header>
  );
};
