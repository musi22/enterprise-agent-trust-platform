"use client";

import React, { useState, useEffect } from "react";
import { ConsoleHeader } from "@/components/ConsoleHeader";
import { OverviewTab } from "@/components/tabs/OverviewTab";
import { ScenarioLabTab } from "@/components/tabs/ScenarioLabTab";
import { TraceExplorerTab } from "@/components/tabs/TraceExplorerTab";
import { ApprovalInboxTab } from "@/components/tabs/ApprovalInboxTab";
import { BenchmarkTab } from "@/components/tabs/BenchmarkTab";
import { EvidenceTab } from "@/components/tabs/EvidenceTab";
import { fetchLatestBenchmark, fetchReleaseGate, fetchScenarios } from "@/lib/api";

export default function ConsoleDashboard() {
  const [activeTab, setActiveTab] = useState<string>("overview");
  const [selectedRunIdForTrace, setSelectedRunIdForTrace] = useState<string | null>(null);
  const [benchmark, setBenchmark] = useState<any | null>(null);
  const [releaseGate, setReleaseGate] = useState<any | null>(null);
  const [scenarios, setScenarios] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  const loadData = async () => {
    try {
      const [benchData, gateData, scData] = await Promise.all([
        fetchLatestBenchmark().catch(() => null),
        fetchReleaseGate().catch(() => null),
        fetchScenarios().catch(() => []),
      ]);
      setBenchmark(benchData);
      setReleaseGate(gateData);
      setScenarios(scData);
    } catch (err) {
      console.error("Dashboard data load error:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleViewTrace = (runId: string) => {
    setSelectedRunIdForTrace(runId);
    setActiveTab("traces");
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#090d16] text-slate-100">
      <ConsoleHeader
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        gatePassed={releaseGate?.release_gate_passed ?? false}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === "overview" && (
          <OverviewTab
            benchmark={benchmark}
            releaseGate={releaseGate}
            onNavigateToScenarios={() => setActiveTab("scenarios")}
          />
        )}

        {activeTab === "scenarios" && (
          <ScenarioLabTab
            scenarios={scenarios}
            onViewTrace={handleViewTrace}
          />
        )}

        {activeTab === "traces" && (
          <TraceExplorerTab
            initialRunId={selectedRunIdForTrace}
          />
        )}

        {activeTab === "approvals" && (
          <ApprovalInboxTab />
        )}

        {activeTab === "benchmark" && (
          <BenchmarkTab
            benchmark={benchmark}
            releaseGate={releaseGate}
            onRefresh={loadData}
          />
        )}

        {activeTab === "evidence" && (
          <EvidenceTab />
        )}
      </main>
    </div>
  );
}
