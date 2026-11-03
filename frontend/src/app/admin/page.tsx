"use client";

import { useEffect, useState } from "react";
import { AppLayout } from "@/components/layout/AppLayout";
import { api } from "@/lib/api-client";
import {
  ShieldAlert,
  Building2,
  Users,
  FileText,
  DollarSign,
  HardDrive,
  Cpu,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
} from "lucide-react";

interface OrganizationOverview {
  id: string;
  name: string;
  slug: string;
  legal_name: string | null;
  gstin: string | null;
  created_at: string;
  members_count: number;
  documents_count: number;
  invoices_total_amount: number;
  subscription_plan: string;
  subscription_status: string;
  onboarding_completed: boolean;
}

interface SuperAdminMetrics {
  total_organizations: number;
  total_users: number;
  total_documents: number;
  total_invoices_value_inr: number;
  total_processed_volume_bytes: number;
  failed_processing_jobs_count: number;
  ai_metrics: Record<string, any>;
  storage_consumption: Record<string, any>;
  subscriptions_breakdown: Record<string, number>;
  system_health: {
    status: string;
    database: Record<string, any>;
    ai_engine: Record<string, any>;
    storage: Record<string, any>;
    active_daemons: Record<string, any>;
  };
  recent_organizations: OrganizationOverview[];
}

export default function SuperAdminPage() {
  const [metrics, setMetrics] = useState<SuperAdminMetrics | null>(null);
  const [organizations, setOrganizations] = useState<OrganizationOverview[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchAdminData();
  }, []);

  const fetchAdminData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [m, orgs] = await Promise.all([
        api.get<SuperAdminMetrics>("/admin/metrics"),
        api.get<OrganizationOverview[]>("/admin/organizations"),
      ]);
      setMetrics(m);
      setOrganizations(orgs);
    } catch (err: any) {
      console.error("Super Admin access error:", err);
      setError(
        err.status === 403
          ? "Access Denied: You must be a global Super Administrator to access platform operations."
          : err.message || "Failed to load super admin telemetry."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <AppLayout>
      <div className="space-y-8 max-w-7xl mx-auto pb-12">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white flex items-center gap-2.5">
              <ShieldAlert className="h-7 w-7 text-indigo-600" />
              Platform Super Admin Control Center
            </h1>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
              Cross-tenant telemetry, global subscription oversight, and multi-agent health monitoring.
            </p>
          </div>

          <button
            onClick={fetchAdminData}
            disabled={loading}
            className="self-start md:self-auto py-2 px-4 rounded-xl border border-slate-200 dark:border-navy-700 bg-white dark:bg-navy-800 text-xs font-semibold flex items-center gap-2 hover:bg-slate-50 dark:hover:bg-navy-700 shadow-sm"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
            Refresh Telemetry
          </button>
        </div>

        {/* Error State */}
        {error && (
          <div className="p-6 rounded-2xl bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-800 flex items-start gap-3 text-red-900 dark:text-red-200">
            <AlertTriangle className="h-5 w-5 text-red-600 shrink-0 mt-0.5" />
            <div>
              <h3 className="text-sm font-bold">Privilege Boundary Enforced</h3>
              <p className="text-xs mt-1 text-red-700 dark:text-red-300">{error}</p>
            </div>
          </div>
        )}

        {/* Super Admin Metrics Grid */}
        {metrics && (
          <>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-white dark:bg-navy-900 p-5 rounded-2xl border border-slate-200 dark:border-navy-800 shadow-sm">
                <div className="flex items-center justify-between text-slate-400 mb-2">
                  <span className="text-xs font-semibold uppercase">Total Tenants</span>
                  <Building2 className="h-4 w-4 text-blue-500" />
                </div>
                <div className="text-2xl font-extrabold text-slate-900 dark:text-white">
                  {metrics.total_organizations}
                </div>
                <p className="text-[11px] text-slate-400 mt-1">Active registered business orgs</p>
              </div>

              <div className="bg-white dark:bg-navy-900 p-5 rounded-2xl border border-slate-200 dark:border-navy-800 shadow-sm">
                <div className="flex items-center justify-between text-slate-400 mb-2">
                  <span className="text-xs font-semibold uppercase">Registered Users</span>
                  <Users className="h-4 w-4 text-emerald-500" />
                </div>
                <div className="text-2xl font-extrabold text-slate-900 dark:text-white">
                  {metrics.total_users}
                </div>
                <p className="text-[11px] text-slate-400 mt-1">Across 6 enterprise roles</p>
              </div>

              <div className="bg-white dark:bg-navy-900 p-5 rounded-2xl border border-slate-200 dark:border-navy-800 shadow-sm">
                <div className="flex items-center justify-between text-slate-400 mb-2">
                  <span className="text-xs font-semibold uppercase">Docs Processed</span>
                  <FileText className="h-4 w-4 text-indigo-500" />
                </div>
                <div className="text-2xl font-extrabold text-slate-900 dark:text-white">
                  {metrics.total_documents}
                </div>
                <p className="text-[11px] text-slate-400 mt-1">
                  {metrics.failed_processing_jobs_count} flagged/failed
                </p>
              </div>

              <div className="bg-white dark:bg-navy-900 p-5 rounded-2xl border border-slate-200 dark:border-navy-800 shadow-sm">
                <div className="flex items-center justify-between text-slate-400 mb-2">
                  <span className="text-xs font-semibold uppercase">Total Invoiced Volume</span>
                  <DollarSign className="h-4 w-4 text-amber-500" />
                </div>
                <div className="text-2xl font-extrabold text-slate-900 dark:text-white">
                  ₹{metrics.total_invoices_value_inr.toLocaleString("en-IN", { maximumFractionDigits: 0 })}
                </div>
                <p className="text-[11px] text-slate-400 mt-1">Reconciled Indian GST spend</p>
              </div>
            </div>

            {/* System Health & Subscriptions Summary */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* System Health */}
              <div className="bg-white dark:bg-navy-900 p-6 rounded-2xl border border-slate-200 dark:border-navy-800 shadow-sm space-y-4">
                <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <Cpu className="h-4 w-4 text-emerald-500" />
                  Cluster Health & Infrastructure
                </h3>

                <div className="space-y-2.5 text-xs">
                  <div className="flex justify-between items-center py-1.5 border-b border-slate-100 dark:border-navy-800">
                    <span className="text-slate-500">Database Engine</span>
                    <span className="font-semibold text-emerald-600 dark:text-emerald-400 flex items-center gap-1">
                      <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                      {metrics.system_health.database?.engine || "PostgreSQL / SQLite"} ({metrics.system_health.database?.status})
                    </span>
                  </div>

                  <div className="flex justify-between items-center py-1.5 border-b border-slate-100 dark:border-navy-800">
                    <span className="text-slate-500">AI Primary Provider</span>
                    <span className="font-semibold text-slate-900 dark:text-white">
                      {metrics.ai_metrics?.primary_provider} ({metrics.ai_metrics?.gemini_status})
                    </span>
                  </div>

                  <div className="flex justify-between items-center py-1.5 border-b border-slate-100 dark:border-navy-800">
                    <span className="text-slate-500">Secondary Fallback</span>
                    <span className="font-semibold text-slate-900 dark:text-white">
                      {metrics.ai_metrics?.fallback_provider} ({metrics.ai_metrics?.groq_status})
                    </span>
                  </div>

                  <div className="flex justify-between items-center py-1.5">
                    <span className="text-slate-500">Storage Consumption</span>
                    <span className="font-semibold text-slate-900 dark:text-white flex items-center gap-1">
                      <HardDrive className="h-3.5 w-3.5 text-slate-400" />
                      {(metrics.total_processed_volume_bytes / 1024).toFixed(1)} KB
                    </span>
                  </div>
                </div>
              </div>

              {/* Subscriptions Breakdown */}
              <div className="bg-white dark:bg-navy-900 p-6 rounded-2xl border border-slate-200 dark:border-navy-800 shadow-sm space-y-4">
                <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-blue-500" />
                  Subscription Distribution
                </h3>

                <div className="space-y-3">
                  {["STARTER", "PROFESSIONAL", "ENTERPRISE"].map((tier) => {
                    const count = metrics.subscriptions_breakdown?.[tier] || 0;
                    const pct = metrics.total_organizations ? Math.round((count / metrics.total_organizations) * 100) : 0;
                    return (
                      <div key={tier} className="space-y-1">
                        <div className="flex justify-between text-xs font-medium">
                          <span className="text-slate-600 dark:text-slate-300">{tier} Plan</span>
                          <span className="font-bold text-slate-900 dark:text-white">
                            {count} orgs ({pct}%)
                          </span>
                        </div>
                        <div className="h-2 rounded-full bg-slate-100 dark:bg-navy-800 overflow-hidden">
                          <div
                            className={`h-full rounded-full ${
                              tier === "ENTERPRISE"
                                ? "bg-indigo-600"
                                : tier === "PROFESSIONAL"
                                ? "bg-blue-600"
                                : "bg-slate-400"
                            }`}
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Security & Multi-Tenant Guarantee */}
              <div className="bg-white dark:bg-navy-900 p-6 rounded-2xl border border-slate-200 dark:border-navy-800 shadow-sm space-y-3">
                <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <ShieldAlert className="h-4 w-4 text-amber-500" />
                  Multi-Tenant Security Scoping
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
                  Every query is strictly constrained by <code className="text-blue-500 font-mono">organization_id</code>.
                  Zero cross-tenant data leakage. Automated circuit breakers safeguard against LLM rate-limit disruptions.
                </p>
                <div className="pt-2">
                  <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[11px] font-semibold bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
                    <CheckCircle2 className="h-3.5 w-3.5" />
                    Security Baseline Compliant
                  </span>
                </div>
              </div>
            </div>

            {/* Organizations Directory Table */}
            <div className="bg-white dark:bg-navy-900 rounded-2xl border border-slate-200 dark:border-navy-800 shadow-sm overflow-hidden">
              <div className="p-5 border-b border-slate-200 dark:border-navy-800 flex justify-between items-center">
                <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <Building2 className="h-5 w-5 text-blue-600" />
                  All Registered Organizations ({organizations.length})
                </h3>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left">
                  <thead className="bg-slate-50 dark:bg-navy-800/60 text-slate-500 font-semibold uppercase tracking-wider">
                    <tr>
                      <th className="py-3 px-4">Organization Name</th>
                      <th className="py-3 px-4">Slug</th>
                      <th className="py-3 px-4">Subscription Plan</th>
                      <th className="py-3 px-4 text-center">Team Members</th>
                      <th className="py-3 px-4 text-center">Documents</th>
                      <th className="py-3 px-4 text-right">Invoiced Total</th>
                      <th className="py-3 px-4 text-center">Onboarding</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200 dark:divide-navy-800">
                    {organizations.map((org) => (
                      <tr key={org.id} className="text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-navy-800/40">
                        <td className="py-3 px-4">
                          <span className="font-bold text-slate-900 dark:text-white">{org.name}</span>
                          {org.legal_name && (
                            <span className="block text-[11px] text-slate-400">{org.legal_name}</span>
                          )}
                        </td>
                        <td className="py-3 px-4 font-mono text-[11px] text-slate-400">{org.slug}</td>
                        <td className="py-3 px-4">
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300 border border-blue-200 dark:border-blue-800">
                            {org.subscription_plan}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-center font-semibold">{org.members_count}</td>
                        <td className="py-3 px-4 text-center font-semibold">{org.documents_count}</td>
                        <td className="py-3 px-4 text-right font-medium">
                          ₹{org.invoices_total_amount.toLocaleString("en-IN", { maximumFractionDigits: 0 })}
                        </td>
                        <td className="py-3 px-4 text-center">
                          {org.onboarding_completed ? (
                            <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-600 dark:text-emerald-400">
                              <CheckCircle2 className="h-3.5 w-3.5" /> Done
                            </span>
                          ) : (
                            <span className="text-[11px] text-amber-500 font-medium">In Progress</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}
      </div>
    </AppLayout>
  );
}
