"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  FileText,
  FileCheck2,
  Clock,
  AlertTriangle,
  CopyCheck,
  TrendingUp,
  Cpu,
  ArrowRight,
  RefreshCw,
  IndianRupee,
  ShieldCheck,
  CheckCircle,
} from "lucide-react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import { api } from "@/lib/api-client";
import { formatCurrency, formatDate } from "@/lib/utils";
import { DashboardMetrics, AgentStatusSummary } from "@/types";

const STATUS_COLORS: Record<string, string> = {
  Approved: "#10b981",
  "Needs Review": "#f59e0b",
  Processing: "#3b82f6",
  Completed: "#6366f1",
  Failed: "#ef4444",
  Uploaded: "#64748b",
};

export default function DashboardPage() {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [agents, setAgents] = useState<AgentStatusSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDashboardData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [dashData, agentData] = await Promise.all([
        api.get<DashboardMetrics>("/reports/dashboard"),
        api.get<AgentStatusSummary[]>("/agents"),
      ]);
      setMetrics(dashData);
      setAgents(agentData);
    } catch (err: any) {
      setError(err.message || "Failed to load dashboard data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-96 text-slate-400 gap-3">
        <RefreshCw className="h-8 w-8 animate-spin text-blue-600" />
        <p className="text-sm font-medium">Loading live enterprise telemetry...</p>
      </div>
    );
  }

  if (error || !metrics) {
    return (
      <div className="p-6 bg-rose-50 border border-rose-200 rounded-xl text-rose-700">
        <p className="font-semibold text-sm">Failed to connect to backend telemetry</p>
        <p className="text-xs mt-1">{error}</p>
        <button
          onClick={fetchDashboardData}
          className="mt-3 px-3 py-1.5 rounded-lg bg-rose-600 text-white text-xs font-semibold hover:bg-rose-700"
        >
          Retry Connection
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Top Banner & Quick Action */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200/80 pb-5">
        <div>
          <h1 className="text-2xl font-bold text-navy-900 tracking-tight">Executive Intelligence Dashboard</h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Real-time financial ingestion metrics, deterministic validation, and agent telemetry.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={fetchDashboardData}
            className="flex items-center gap-2 px-3.5 py-2 rounded-lg border border-slate-200 bg-white text-xs font-medium text-slate-600 hover:bg-slate-50 transition-colors shadow-sm"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            Refresh
          </button>
          <Link
            href="/upload"
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-sm shadow-blue-600/30 transition-all"
          >
            Upload Invoices
            <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Value */}
        <div className="p-5 bg-white rounded-xl border border-slate-200/80 shadow-sm flex items-start justify-between">
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Total Invoice Volume</p>
            <p className="text-2xl font-bold text-navy-900 mt-2">
              {formatCurrency(metrics.total_invoice_value, metrics.currency)}
            </p>
            <span className="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-600 mt-1">
              <TrendingUp className="h-3 w-3" />
              Verified Invoices
            </span>
          </div>
          <div className="p-2.5 rounded-xl bg-blue-50 text-blue-600 border border-blue-100">
            <IndianRupee className="h-5 w-5" />
          </div>
        </div>

        {/* Processed Documents */}
        <div className="p-5 bg-white rounded-xl border border-slate-200/80 shadow-sm flex items-start justify-between">
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Documents Ingested</p>
            <p className="text-2xl font-bold text-navy-900 mt-2">{metrics.total_documents}</p>
            <span className="text-[11px] text-slate-400 mt-1 block">
              {metrics.processed_documents} successfully processed
            </span>
          </div>
          <div className="p-2.5 rounded-xl bg-slate-100 text-slate-700 border border-slate-200">
            <FileText className="h-5 w-5" />
          </div>
        </div>

        {/* Pending Approvals */}
        <div className="p-5 bg-white rounded-xl border border-slate-200/80 shadow-sm flex items-start justify-between">
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Pending Human Review</p>
            <p className="text-2xl font-bold text-amber-600 mt-2">{metrics.pending_approvals}</p>
            <Link
              href="/approvals"
              className="text-[11px] text-blue-600 font-semibold hover:underline mt-1 inline-flex items-center gap-1"
            >
              Open Approval Queue <ArrowRight className="h-3 w-3" />
            </Link>
          </div>
          <div className="p-2.5 rounded-xl bg-amber-50 text-amber-600 border border-amber-200">
            <Clock className="h-5 w-5" />
          </div>
        </div>

        {/* Duplicate & Anomaly Warnings */}
        <div className="p-5 bg-white rounded-xl border border-slate-200/80 shadow-sm flex items-start justify-between">
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Duplicate Warnings</p>
            <p className="text-2xl font-bold text-rose-600 mt-2">{metrics.duplicate_warnings}</p>
            <span className="text-[11px] text-slate-400 mt-1 block">
              {metrics.failed_documents} failed validations
            </span>
          </div>
          <div className="p-2.5 rounded-xl bg-rose-50 text-rose-600 border border-rose-200">
            <CopyCheck className="h-5 w-5" />
          </div>
        </div>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Expense Trend Chart */}
        <div className="lg:col-span-2 p-6 bg-white rounded-xl border border-slate-200/80 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-sm font-bold text-navy-900">Monthly Spending & Tax Trajectory</h2>
              <p className="text-xs text-slate-400">Aggregated historical invoice volume by calendar month</p>
            </div>
            <div className="flex items-center gap-3 text-xs">
              <span className="flex items-center gap-1.5 text-slate-600">
                <span className="h-2.5 w-2.5 rounded-sm bg-blue-600" />
                Gross Total
              </span>
              <span className="flex items-center gap-1.5 text-slate-600">
                <span className="h-2.5 w-2.5 rounded-sm bg-cyan-500" />
                Tax Liability
              </span>
            </div>
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={metrics.monthly_expense_trend} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <XAxis dataKey="month" tick={{ fontSize: 11, fill: "#64748b" }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 11, fill: "#64748b" }} axisLine={false} tickLine={false} />
                <Tooltip
                  formatter={(val: any) => formatCurrency(val)}
                  contentStyle={{ backgroundColor: "#102A43", borderColor: "#334E68", borderRadius: "8px", color: "#fff", fontSize: "12px" }}
                />
                <Bar dataKey="total" fill="#2563eb" radius={[4, 4, 0, 0]} name="Total Amount" />
                <Bar dataKey="tax" fill="#06b6d4" radius={[4, 4, 0, 0]} name="GST Tax" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Processing Status Breakdown */}
        <div className="p-6 bg-white rounded-xl border border-slate-200/80 shadow-sm flex flex-col">
          <h2 className="text-sm font-bold text-navy-900 mb-1">Ingestion Status Breakdown</h2>
          <p className="text-xs text-slate-400 mb-4">Real-time status of multi-agent pipeline</p>
          <div className="h-48 w-full flex-1">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={metrics.processing_status_distribution}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={75}
                  paddingAngle={4}
                  dataKey="value"
                >
                  {metrics.processing_status_distribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={STATUS_COLORS[entry.name] || "#94a3b8"} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ backgroundColor: "#102A43", borderColor: "#334E68", borderRadius: "8px", color: "#fff", fontSize: "12px" }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-100 text-xs">
            {metrics.processing_status_distribution.map((item) => (
              <div key={item.name} className="flex items-center gap-1.5">
                <span
                  className="h-2 w-2 rounded-full shrink-0"
                  style={{ backgroundColor: STATUS_COLORS[item.name] || "#94a3b8" }}
                />
                <span className="text-slate-500 truncate">{item.name}:</span>
                <span className="font-semibold text-slate-800 ml-auto">{item.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Live AI Agents Status Strip */}
      <div className="p-6 bg-navy-950 text-white rounded-xl border border-navy-800 shadow-lg">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-blue-600/20 text-blue-400 border border-blue-500/30">
              <Cpu className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-sm font-bold tracking-tight">Active Multi-Agent Orchestration Nodes</h2>
              <p className="text-xs text-slate-400">9 Specialized LangGraph agents executing autonomous pipeline</p>
            </div>
          </div>
          <Link
            href="/agents"
            className="text-xs font-semibold text-blue-400 hover:text-blue-300 flex items-center gap-1"
          >
            Inspect Execution Traces <ArrowRight className="h-3 w-3" />
          </Link>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-9 gap-2.5">
          {agents.map((agent) => (
            <div
              key={agent.agent_id}
              className="p-3 rounded-lg bg-navy-900 border border-navy-800 flex flex-col justify-between"
            >
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-[10px] text-slate-400 font-medium truncate">{agent.agent_id.toUpperCase()}</span>
                <span className={`h-1.5 w-1.5 rounded-full ${agent.status === "ACTIVE" ? "bg-emerald-400 animate-pulse" : "bg-slate-500"}`} />
              </div>
              <p className="text-xs font-bold text-white leading-tight truncate" title={agent.name}>
                {agent.name.replace(" Agent", "")}
              </p>
              <div className="mt-2 pt-1.5 border-t border-navy-800 flex items-center justify-between text-[10px] text-slate-400">
                <span>{agent.total_executions} runs</span>
                <span className="text-slate-300 font-mono">{agent.avg_latency_ms}ms</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Recent Audit Activity */}
      <div className="p-6 bg-white rounded-xl border border-slate-200/80 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-sm font-bold text-navy-900">Immutable Audit Trail</h2>
            <p className="text-xs text-slate-400">Chronological governance history of all system and reviewer actions</p>
          </div>
          <Link href="/settings" className="text-xs font-semibold text-blue-600 hover:underline">
            View Full Audit Log
          </Link>
        </div>

        <div className="divide-y divide-slate-100">
          {metrics.recent_activity.map((act) => (
            <div key={act.id} className="py-3 flex items-center justify-between text-xs">
              <div className="flex items-center gap-3">
                <div className="h-7 w-7 rounded-full bg-slate-100 text-slate-600 flex items-center justify-center font-bold text-[10px]">
                  {act.entity.charAt(0)}
                </div>
                <div>
                  <p className="font-semibold text-slate-800">{act.action}</p>
                  <p className="text-slate-400 text-[11px]">
                    Target: <span className="font-mono text-slate-600">{act.entity}</span>
                  </p>
                </div>
              </div>
              <span className="text-slate-400 font-mono text-[11px]">{act.timestamp}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

