"use client";

import { useState } from "react";

// Tab component
function TabButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
        active
          ? "bg-blue-600 text-white"
          : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
      }`}
    >
      {children}
    </button>
  );
}

interface DashboardClientProps {
  overview: React.ReactNode;
  roiAnalytics: React.ReactNode;
}

export function DashboardClient({
  overview,
  roiAnalytics,
}: DashboardClientProps) {
  const [activeTab, setActiveTab] = useState<"overview" | "roi">("overview");

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-6">
        <div className="text-center mb-6">
          <h1 className="text-3xl font-bold text-slate-900 tracking-tight mb-2">
            Dashboard
          </h1>
          <p className="text-lg text-slate-600 max-w-2xl mx-auto">
            Strategic insights and key performance indicators designed for
            decision-making
          </p>
        </div>

        {/* Navigation Tabs */}
        <div className="flex items-center justify-center space-x-2">
          <TabButton
            active={activeTab === "overview"}
            onClick={() => setActiveTab("overview")}
          >
            Dashboard Overview
          </TabButton>
          <TabButton
            active={activeTab === "roi"}
            onClick={() => setActiveTab("roi")}
          >
            ROI Analytics
          </TabButton>
        </div>
      </div>

      {/* Content */}
      {activeTab === "overview" && overview}
      {activeTab === "roi" && roiAnalytics}
    </div>
  );
}
