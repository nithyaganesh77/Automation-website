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
  Activity,
  Zap,
  Lock,
  Eye,
  EyeOff,
  Check,
  X,
  RefreshCw,
  IndianRupee,
} from "lucide-react";
import { api } from "@/lib/api-client";
import { formatDate } from "@/lib/utils";

export default function SettingsPage() {
  // Settings Form State
  const [primaryProvider, setPrimaryProvider] = useState("gemini");
  const [fallbackProvider, setFallbackProvider] = useState("groq");
  const [geminiModel, setGeminiModel] = useState("gemini-2.0-flash");
  const [groqModel, setGroqModel] = useState("llama-3.3-70b-versatile");
  const [geminiKey, setGeminiKey] = useState("");
  const [groqKey, setGroqKey] = useState("");
  const [disableExternalAi, setDisableExternalAi] = useState(false);
  const [dailyRequestLimit, setDailyRequestLimit] = useState(1500);
  const [monthlyTokenBudget, setMonthlyTokenBudget] = useState(1000000);
  const [safeQuotaMode, setSafeQuotaMode] = useState(true);
  const [confidenceThreshold, setConfidenceThreshold] = useState(0.85);
  const [taxTolerance, setTaxTolerance] = useState(2.0);
  const [currency, setCurrency] = useState("INR");

  // Configured Statuses
  const [geminiConfigured, setGeminiConfigured] = useState(false);
  const [groqConfigured, setGroqConfigured] = useState(false);

  // Telemetry State
  const [telemetry, setTelemetry] = useState<any>(null);
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [saved, setSaved] = useState(false);
  const [loading, setLoading] = useState(true);

  // Connection Test States
  const [testingGemini, setTestingGemini] = useState(false);
  const [testingGroq, setTestingGroq] = useState(false);
  const [geminiTestResult, setGeminiTestResult] = useState<{ success: boolean; msg: string } | null>(null);
  const [groqTestResult, setGroqTestResult] = useState<{ success: boolean; msg: string } | null>(null);

  const fetchSettings = async () => {
    setLoading(true);
    try {
      const [settingsData, logsData, telemetryData] = await Promise.all([
        api.get<any>("/settings"),
        api.get<any[]>("/settings/audit-logs"),
        api.get<any>("/settings/telemetry"),
      ]);

      setPrimaryProvider(settingsData.primary_provider || "gemini");
      setFallbackProvider(settingsData.fallback_provider || "groq");
      setGeminiModel(settingsData.gemini_model || "gemini-2.0-flash");
      setGroqModel(settingsData.groq_model || "llama-3.3-70b-versatile");
      setGeminiConfigured(settingsData.gemini_configured);
      setGroqConfigured(settingsData.groq_configured);
      setDisableExternalAi(settingsData.disable_external_ai);
      setDailyRequestLimit(settingsData.daily_request_limit || 1500);
      setMonthlyTokenBudget(settingsData.monthly_token_budget || 1000000);
      setSafeQuotaMode(settingsData.safe_quota_mode);
      setConfidenceThreshold(settingsData.confidence_threshold || 0.85);
      setTaxTolerance(settingsData.tax_tolerance || 2.0);
      setCurrency(settingsData.currency || "INR");

      setAuditLogs(logsData);
      setTelemetry(telemetryData);
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
        primary_provider: primaryProvider,
        fallback_provider: fallbackProvider,
        gemini_model: geminiModel,
        groq_model: groqModel,
        gemini_api_key: geminiKey || undefined,
        groq_api_key: groqKey || undefined,
        disable_external_ai: disableExternalAi,
        daily_request_limit: dailyRequestLimit,
        monthly_token_budget: monthlyTokenBudget,
        safe_quota_mode: safeQuotaMode,
        confidence_threshold: confidenceThreshold,
        tax_tolerance: taxTolerance,
        currency,
      });
      setSaved(true);
      setGeminiKey("");
      setGroqKey("");
      await fetchSettings();
      setTimeout(() => setSaved(false), 4000);
    } catch (err: any) {
      alert(err.message || "Failed to save settings");
    }
  };

  const handleTestConnection = async (provider: "gemini" | "groq") => {
    if (provider === "gemini") {
      setTestingGemini(true);
      setGeminiTestResult(null);
      try {
        const res = await api.post<any>("/settings/test-connection", {
          provider: "gemini",
          api_key: geminiKey || undefined,
        });
        setGeminiTestResult({ success: res.success, msg: res.message });
      } catch (err: any) {
        setGeminiTestResult({ success: false, msg: err.message || "Connection failed" });
      } finally {
        setTestingGemini(false);
      }
    } else {
      setTestingGroq(true);
      setGroqTestResult(null);
      try {
        const res = await api.post<any>("/settings/test-connection", {
          provider: "groq",
          api_key: groqKey || undefined,
        });
        setGroqTestResult({ success: res.success, msg: res.message });
      } catch (err: any) {
        setGroqTestResult({ success: false, msg: err.message || "Connection failed" });
      } finally {
        setTestingGroq(false);
      }
    }
  };

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200/80 pb-5">
        <div>
          <h1 className="text-2xl font-bold text-navy-900 tracking-tight">AI Telemetry & System Configuration</h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Free-first architecture with Google Gemini (Primary), Groq (Failover), and deterministic local safeguards.
          </p>
        </div>
        <button
          onClick={fetchSettings}
          className="flex items-center gap-2 px-3.5 py-2 rounded-lg border border-slate-200 bg-white text-xs font-semibold text-slate-700 hover:bg-slate-50 shadow-sm"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          Refresh Stats
        </button>
      </div>

      {saved && (
        <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-center gap-2">
          <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
          <span>System configuration and AI provider preferences updated successfully.</span>
        </div>
      )}

      {/* AI Telemetry & Usage Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Gemini Telemetry */}
        <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-slate-500 uppercase">Primary: Gemini</span>
            <span
              className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                telemetry?.gemini_status === "ONLINE"
                  ? "bg-emerald-100 text-emerald-800"
                  : telemetry?.gemini_status === "RATE_LIMITED"
                  ? "bg-amber-100 text-amber-800"
                  : "bg-slate-100 text-slate-600"
              }`}
            >
              {telemetry?.gemini_status || "IDLE"}
            </span>
          </div>
          <p className="text-xl font-bold text-navy-900">{telemetry?.gemini_requests || 0} reqs</p>
          <span className="text-[11px] text-slate-400 mt-1 block">
            {Number(telemetry?.gemini_tokens || 0).toLocaleString()} tokens consumed
          </span>
        </div>

        {/* Groq Telemetry */}
        <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-slate-500 uppercase">Fallback: Groq</span>
            <span
              className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                telemetry?.groq_status === "ONLINE"
                  ? "bg-emerald-100 text-emerald-800"
                  : "bg-slate-100 text-slate-600"
              }`}
            >
              {telemetry?.groq_status || "IDLE"}
            </span>
          </div>
          <p className="text-xl font-bold text-navy-900">{telemetry?.groq_requests || 0} reqs</p>
          <span className="text-[11px] text-slate-400 mt-1 block">
            {Number(telemetry?.groq_tokens || 0).toLocaleString()} tokens consumed
          </span>
        </div>

        {/* Failover Events */}
        <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-slate-500 uppercase">Auto Failovers</span>
            <Zap className="h-4 w-4 text-amber-500" />
          </div>
          <p className="text-xl font-bold text-amber-600">{telemetry?.fallback_events || 0}</p>
          <span className="text-[11px] text-slate-400 mt-1 block">
            Active Provider: <strong className="text-slate-700 capitalize">{telemetry?.last_active_provider || "gemini"}</strong>
          </span>
        </div>

        {/* Estimated API Cost */}
        <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-slate-500 uppercase">Estimated Spend</span>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800">
              FREE TIER
            </span>
          </div>
          <p className="text-xl font-bold text-emerald-700">$0.00 USD</p>
          <span className="text-[11px] text-slate-400 mt-1 block">Zero development budget active</span>
        </div>
      </div>

      {/* Main Settings Form */}
      <form onSubmit={handleSave} className="space-y-6">
        {/* Document Privacy Alert & Local Processing Toggle */}
        <div className="p-5 rounded-xl bg-white border border-slate-200/80 shadow-sm space-y-4">
          <div className="flex items-start justify-between gap-4">
            <div className="flex items-start gap-3">
              <div className="p-2.5 rounded-lg bg-blue-50 text-blue-600 mt-0.5">
                <Shield className="h-5 w-5" />
              </div>
              <div>
                <h2 className="text-sm font-bold text-navy-900">Document Privacy & Confidentiality Safeguard</h2>
                <p className="text-xs text-slate-500 mt-1 leading-relaxed">
                  External free-tier providers (Google Gemini & Groq) operate under public cloud data processing policies.
                  You can enforce strict zero-cloud privacy by enabling Local-Only Processing.
                </p>
              </div>
            </div>

            <label className="relative inline-flex items-center cursor-pointer shrink-0">
              <input
                type="checkbox"
                checked={disableExternalAi}
                onChange={(e) => setDisableExternalAi(e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
            </label>
          </div>

          {disableExternalAi && (
            <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg text-xs text-amber-800 font-medium">
              🔒 Local Processing Mode Active: No documents or text snippets will be transmitted to external AI endpoints. Documents will be parsed 100% locally using PyMuPDF and deterministic rules.
            </div>
          )}
        </div>

        {/* Free-First AI Providers (Gemini + Groq) */}
        <div className="bg-white rounded-xl border border-slate-200/80 shadow-sm p-6 space-y-5">
          <div className="flex items-center gap-2.5 pb-3 border-b border-slate-100">
            <Cpu className="h-5 w-5 text-blue-600" />
            <div>
              <h2 className="text-sm font-bold text-navy-900">Free AI Provider Orchestration</h2>
              <p className="text-xs text-slate-400">Configure primary Gemini and secondary Groq fallback credentials</p>
            </div>
          </div>

          {/* Primary Provider: Gemini */}
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="font-bold text-xs text-slate-800">Primary Provider: Google Gemini</span>
                <span className="text-[10px] px-2 py-0.5 rounded bg-blue-100 text-blue-800 font-semibold">
                  {geminiConfigured ? "Key Active" : "No Key Set (Using Local)"}
                </span>
              </div>
              <button
                type="button"
                disabled={testingGemini || (!geminiKey && !geminiConfigured)}
                onClick={() => handleTestConnection("gemini")}
                className="px-3 py-1.5 rounded-lg border border-slate-300 bg-white text-[11px] font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-40"
              >
                {testingGemini ? "Testing..." : "Test Gemini Connection"}
              </button>
            </div>

            {geminiTestResult && (
              <div
                className={`p-2.5 rounded text-xs flex items-center gap-2 ${
                  geminiTestResult.success
                    ? "bg-emerald-50 text-emerald-800 border border-emerald-200"
                    : "bg-rose-50 text-rose-800 border border-rose-200"
                }`}
              >
                {geminiTestResult.success ? <Check className="h-4 w-4" /> : <X className="h-4 w-4" />}
                <span>{geminiTestResult.msg}</span>
              </div>
            )}

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
              <div>
                <label className="font-semibold text-slate-700 block mb-1">Model Name</label>
                <input
                  type="text"
                  value={geminiModel}
                  onChange={(e) => setGeminiModel(e.target.value)}
                  className="w-full bg-white border border-slate-200 rounded-lg px-3 py-2 text-xs font-mono"
                />
              </div>
              <div>
                <label className="font-semibold text-slate-700 block mb-1">Gemini API Key</label>
                <input
                  type="password"
                  placeholder={geminiConfigured ? "•••••••••••••••• (Configured)" : "Paste AIzaSy... key"}
                  value={geminiKey}
                  onChange={(e) => setGeminiKey(e.target.value)}
                  className="w-full bg-white border border-slate-200 rounded-lg px-3 py-2 text-xs font-mono"
                />
              </div>
            </div>
          </div>

          {/* Fallback Provider: Groq */}
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="font-bold text-xs text-slate-800">Fallback Provider: Groq (Llama 3.3 / Mixtral)</span>
                <span className="text-[10px] px-2 py-0.5 rounded bg-blue-100 text-blue-800 font-semibold">
                  {groqConfigured ? "Key Active" : "No Key Set"}
                </span>
              </div>
              <button
                type="button"
                disabled={testingGroq || (!groqKey && !groqConfigured)}
                onClick={() => handleTestConnection("groq")}
                className="px-3 py-1.5 rounded-lg border border-slate-300 bg-white text-[11px] font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-40"
              >
                {testingGroq ? "Testing..." : "Test Groq Connection"}
              </button>
            </div>

            {groqTestResult && (
              <div
                className={`p-2.5 rounded text-xs flex items-center gap-2 ${
                  groqTestResult.success
                    ? "bg-emerald-50 text-emerald-800 border border-emerald-200"
                    : "bg-rose-50 text-rose-800 border border-rose-200"
                }`}
              >
                {groqTestResult.success ? <Check className="h-4 w-4" /> : <X className="h-4 w-4" />}
                <span>{groqTestResult.msg}</span>
              </div>
            )}

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
              <div>
                <label className="font-semibold text-slate-700 block mb-1">Model Name</label>
                <input
                  type="text"
                  value={groqModel}
                  onChange={(e) => setGroqModel(e.target.value)}
                  className="w-full bg-white border border-slate-200 rounded-lg px-3 py-2 text-xs font-mono"
                />
              </div>
              <div>
                <label className="font-semibold text-slate-700 block mb-1">Groq API Key</label>
                <input
                  type="password"
                  placeholder={groqConfigured ? "•••••••••••••••• (Configured)" : "Paste gsk_... key"}
                  value={groqKey}
                  onChange={(e) => setGroqKey(e.target.value)}
                  className="w-full bg-white border border-slate-200 rounded-lg px-3 py-2 text-xs font-mono"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Quota & Cost Control */}
        <div className="bg-white rounded-xl border border-slate-200/80 shadow-sm p-6 space-y-4">
          <div className="flex items-center gap-2.5 pb-3 border-b border-slate-100">
            <Sliders className="h-5 w-5 text-blue-600" />
            <div>
              <h2 className="text-sm font-bold text-navy-900">Free Tier Budget & Quota Controls</h2>
              <p className="text-xs text-slate-400">Protects against rate-limit lockouts by throttling or falling back</p>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
            <div>
              <label className="font-semibold text-slate-700 block mb-1">Daily Request Limit</label>
              <input
                type="number"
                min="100"
                max="10000"
                value={dailyRequestLimit}
                onChange={(e) => setDailyRequestLimit(Number(e.target.value))}
                className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs font-mono"
              />
              <span className="text-[10px] text-slate-400 mt-1 block">Default: 1,500 calls/day</span>
            </div>

            <div>
              <label className="font-semibold text-slate-700 block mb-1">Monthly Token Budget</label>
              <input
                type="number"
                min="100000"
                max="50000000"
                value={monthlyTokenBudget}
                onChange={(e) => setMonthlyTokenBudget(Number(e.target.value))}
                className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs font-mono"
              />
              <span className="text-[10px] text-slate-400 mt-1 block">Default: 1,000,000 tokens</span>
            </div>

            <div>
              <label className="font-semibold text-slate-700 block mb-1">Safe Quota Mode</label>
              <select
                value={safeQuotaMode ? "true" : "false"}
                onChange={(e) => setSafeQuotaMode(e.target.value === "true")}
                className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs"
              >
                <option value="true">Active (Fallback to Local Engine)</option>
                <option value="false">Off (Retry Until Provider Refuses)</option>
              </select>
              <span className="text-[10px] text-slate-400 mt-1 block">Mitigates unexpected costs by enforcing local fallback</span>
            </div>
          </div>
        </div>

        {/* Business & Accounting Rules */}
        <div className="bg-white rounded-xl border border-slate-200/80 shadow-sm p-6 space-y-4">
          <div className="flex items-center gap-2.5 pb-3 border-b border-slate-100">
            <Sliders className="h-5 w-5 text-blue-600" />
            <div>
              <h2 className="text-sm font-bold text-navy-900">Deterministic Financial Rules & Tolerances</h2>
              <p className="text-xs text-slate-400">Strict decimal verification tolerances for Indian GST & commercial invoices</p>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
            <div>
              <label className="font-semibold text-slate-700 block mb-1">Tax Rounding Tolerance (₹)</label>
              <input
                type="number"
                step="0.10"
                min="0.00"
                max="10.00"
                value={taxTolerance}
                onChange={(e) => setTaxTolerance(Number(e.target.value))}
                className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs font-mono"
              />
              <span className="text-[10px] text-slate-400 mt-1 block">Allowable rounding discrepancy</span>
            </div>

            <div>
              <label className="font-semibold text-slate-700 block mb-1">Extraction Confidence Gate</label>
              <input
                type="number"
                step="0.01"
                min="0.50"
                max="1.00"
                value={confidenceThreshold}
                onChange={(e) => setConfidenceThreshold(Number(e.target.value))}
                className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs font-mono"
              />
              <span className="text-[10px] text-slate-400 mt-1 block">Flag below {(confidenceThreshold * 100).toFixed(0)}%</span>
            </div>

            <div>
              <label className="font-semibold text-slate-700 block mb-1">Base Currency</label>
              <select
                value={currency}
                onChange={(e) => setCurrency(e.target.value)}
                className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs"
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
              className="flex items-center gap-1.5 px-5 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-sm transition-all"
            >
              <Save className="h-4 w-4" />
              Save Configuration
            </button>
          </div>
        </div>
      </form>

      {/* Audit History */}
      <div className="bg-white rounded-xl border border-slate-200/80 shadow-sm p-6 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-100">
          <div>
            <h2 className="text-sm font-bold text-navy-900 flex items-center gap-2">
              <Shield className="h-4 w-4 text-blue-600" />
              Immutable Governance Audit History
            </h2>
            <p className="text-xs text-slate-400">Chronological trail of configuration updates and operator actions</p>
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
