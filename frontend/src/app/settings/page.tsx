"use client";

import { useEffect, useState } from "react";
import {
  Settings,
  Cpu,
  Key,
  Sliders,
  Shield,
  Building,
  User,
  Save,
  CheckCircle2,
  AlertCircle,
  FileText,
} from "lucide-react";
import { api } from "@/lib/api-client";
import { formatDate } from "@/lib/utils";

export default function SettingsPage() {
  const [provider, setProvider] = useState("gemini");
  const [geminiKey, setGeminiKey] = useState("");
  const [openaiKey, setOpenaiKey] = useState("");
  const [confidenceThreshold, setConfidenceThreshold] = useState(0.85);
  const [taxTolerance, setTaxTolerance] = useState(2.0);
  const [autoApproveThreshold, setAutoApproveThreshold] = useState(0.98);
  const [currency, setCurrency] = useState("INR");
  const [apiKeyConfigured, setApiKeyConfigured] = useState(false);

  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [saved, setSaved] = useState(false);
  const [loading, setLoading] = useState(true);

  const fetchSettings = async () => {
    setLoading(true);
    try {
      const [settingsData, logsData] = await Promise.all([
        api.get<any>("/settings"),
        api.get<any[]>("/settings/audit-logs"),
      ]);
      setProvider(settingsData.ai_provider || "gemini");
      setApiKeyConfigured(settingsData.api_key_configured);
      setConfidenceThreshold(settingsData.confidence_threshold || 0.85);
      setTaxTolerance(settingsData.tax_tolerance || 2.0);
      setAutoApproveThreshold(settingsData.auto_approve_threshold || 0.98);
      setCurrency(settingsData.currency || "INR");
      setAuditLogs(logsData);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSettings();
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaved(false);
    try {
      await api.patch("/settings", {
        ai_provider: provider,
        gemini_api_key: geminiKey || undefined,
        openai_api_key: openaiKey || undefined,
        confidence_threshold: confidenceThreshold,
        tax_tolerance: taxTolerance,
        auto_approve_threshold: autoApproveThreshold,
        currency,
      });
      setSaved(true);
      setGeminiKey("");
      setOpenaiKey("");
      await fetchSettings();
      setTimeout(() => setSaved(false), 4000);
    } catch (err: any) {
      alert(err.message || "Failed to save settings");
    }
  };

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-navy-900 tracking-tight">Organization & Engine Settings</h1>
        <p className="text-sm text-slate-500 mt-0.5">
          Configure AI provider endpoints, deterministic financial tolerance thresholds, and review immutable audit governance.
        </p>
      </div>

      {saved && (
        <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-center gap-2">
          <CheckCircle2 className="h-4 w-4 text-emerald-600" />
          <span>System configuration and AI provider preferences updated successfully.</span>
        </div>
      )}

      {/* Main Settings Form */}
      <form onSubmit={handleSave} className="space-y-6">
        {/* AI Model & Provider Card */}
        <div className="bg-white rounded-xl border border-slate-200/80 shadow-sm p-6 space-y-4">
          <div className="flex items-center gap-2.5 pb-3 border-b border-slate-100">
            <Cpu className="h-5 w-5 text-blue-600" />
            <div>
              <h2 className="text-sm font-bold text-navy-900">AI LLM Provider Configuration</h2>
              <p className="text-xs text-slate-400">Select model provider for document classification & structured schema extraction</p>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">Primary Provider</label>
              <select
                value={provider}
                onChange={(e) => setProvider(e.target.value)}
                className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs text-slate-800 focus:outline-none focus:border-blue-500"
              >
                <option value="gemini">Google Gemini (Gemini 2.0 Flash / Pro)</option>
                <option value="openai">OpenAI (GPT-4o / GPT-4o-mini)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                API Key Status
              </label>
              <div className="flex items-center gap-2 h-9 px-3 rounded-lg bg-slate-50 border border-slate-200 text-xs">
                {apiKeyConfigured ? (
                  <span className="text-emerald-600 font-semibold flex items-center gap-1.5">
                    <span className="h-2 w-2 rounded-full bg-emerald-500" />
                    Key Configured & Active
                  </span>
                ) : (
                  <span className="text-slate-400 font-medium">
                    Offline / Deterministic Synthetic Engine Active
                  </span>
                )}
              </div>
            </div>
          </div>

          {provider === "gemini" ? (
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                Update Gemini API Key
              </label>
              <input
                type="password"
                placeholder="AIzaSy... (leave blank to keep current)"
                value={geminiKey}
                onChange={(e) => setGeminiKey(e.target.value)}
                className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs font-mono"
              />
            </div>
          ) : (
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                Update OpenAI API Key
              </label>
              <input
                type="password"
                placeholder="sk-proj-... (leave blank to keep current)"
                value={openaiKey}
                onChange={(e) => setOpenaiKey(e.target.value)}
                className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs font-mono"
              />
            </div>
          )}
        </div>

        {/* Business Rules & Validation Tolerances */}
        <div className="bg-white rounded-xl border border-slate-200/80 shadow-sm p-6 space-y-4">
          <div className="flex items-center gap-2.5 pb-3 border-b border-slate-100">
            <Sliders className="h-5 w-5 text-blue-600" />
            <div>
              <h2 className="text-sm font-bold text-navy-900">Deterministic Financial Rules & Tolerances</h2>
              <p className="text-xs text-slate-400">Control strictness of mathematical checks, rounding tolerances, and approval thresholds</p>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                Tax Rounding Tolerance
              </label>
              <div className="relative">
                <input
                  type="number"
                  step="0.10"
                  min="0.00"
                  max="10.00"
                  value={taxTolerance}
                  onChange={(e) => setTaxTolerance(Number(e.target.value))}
                  className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs font-mono"
                />
              </div>
              <span className="text-[10px] text-slate-400 mt-1 block">Maximum allowable rounding diff (₹)</span>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                Extraction Confidence Threshold
              </label>
              <input
                type="number"
                step="0.01"
                min="0.50"
                max="1.00"
                value={confidenceThreshold}
                onChange={(e) => setConfidenceThreshold(Number(e.target.value))}
                className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs font-mono"
              />
              <span className="text-[10px] text-slate-400 mt-1 block">Flags values under {(confidenceThreshold * 100).toFixed(0)}%</span>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                Auto-Approval Threshold
              </label>
              <input
                type="number"
                step="0.01"
                min="0.90"
                max="1.00"
                value={autoApproveThreshold}
                onChange={(e) => setAutoApproveThreshold(Number(e.target.value))}
                className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs font-mono"
              />
              <span className="text-[10px] text-slate-400 mt-1 block">Zero silent approvals enabled</span>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                Base Accounting Currency
              </label>
              <select
                value={currency}
                onChange={(e) => setCurrency(e.target.value)}
                className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs text-slate-800"
              >
                <option value="INR">INR — Indian Rupee (₹)</option>
                <option value="USD">USD — US Dollar ($)</option>
                <option value="EUR">EUR — Euro (€)</option>
                <option value="GBP">GBP — British Pound (£)</option>
              </select>
            </div>
          </div>

          <div className="pt-2 flex justify-end">
            <button
              type="submit"
              className="flex items-center gap-1.5 px-5 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-sm shadow-blue-600/30 transition-all"
            >
              <Save className="h-4 w-4" />
              Save Configuration
            </button>
          </div>
        </div>
      </form>

      {/* Immutable Audit Log Table */}
      <div className="bg-white rounded-xl border border-slate-200/80 shadow-sm p-6 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-100">
          <div>
            <h2 className="text-sm font-bold text-navy-900 flex items-center gap-2">
              <Shield className="h-4 w-4 text-blue-600" />
              Organization Security & Audit History
            </h2>
            <p className="text-xs text-slate-400">Immutable trace of user registrations, logins, document uploads, and human approvals</p>
          </div>
          <span className="text-xs text-slate-500">{auditLogs.length} audit entries</span>
        </div>

        <div className="divide-y divide-slate-100 max-h-80 overflow-y-auto">
          {auditLogs.map((log) => (
            <div key={log.id} className="py-3 flex items-center justify-between text-xs">
              <div>
                <span className="font-bold text-slate-800">{log.action}</span>
                <span className="text-slate-500 ml-2">Target: {log.entity_type}</span>
              </div>
              <span className="text-slate-400 font-mono text-[11px]">{formatDate(log.timestamp)}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
