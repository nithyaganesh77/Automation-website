"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AppLayout } from "@/components/layout/AppLayout";
import { api } from "@/lib/api-client";
import {
  Sparkles,
  Building2,
  Users,
  Cpu,
  FileCheck2,
  CheckCircle2,
  AlertCircle,
  ArrowRight,
  ArrowLeft,
  Mail,
  Shield,
  UploadCloud,
} from "lucide-react";

interface OnboardingStatus {
  organization_id: string;
  organization_name: string;
  onboarding_completed: boolean;
  current_step: string;
  profile_completed: boolean;
  team_members_count: number;
  pending_invites_count: number;
  ai_configured: boolean;
  first_invoice_uploaded: boolean;
  has_active_subscription: boolean;
}

interface Invitation {
  id: string;
  email: string;
  role: string;
  status: string;
  expires_at: string;
}

const ROLES = [
  "Administrator",
  "Accountant",
  "Reviewer",
  "Read-only User",
];

export default function OnboardingPage() {
  const router = useRouter();
  const [status, setStatus] = useState<OnboardingStatus | null>(null);
  const [currentStep, setCurrentStep] = useState<number>(1);
  const [loading, setLoading] = useState<boolean>(true);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  // Step 1: Profile form
  const [profile, setProfile] = useState({
    legal_name: "",
    gstin: "",
    pan: "",
    address: "",
    city: "",
    state: "",
    pincode: "",
    phone: "",
    currency: "INR",
  });

  // Step 2: Team invites
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState("Reviewer");
  const [invitations, setInvitations] = useState<Invitation[]>([]);

  // Step 3: AI Config
  const [aiConfig, setAiConfig] = useState({
    primary_provider: "gemini",
    fallback_provider: "groq",
    confidence_threshold: 0.85,
    auto_approve_threshold: 0.98,
    tax_tolerance: 2.0,
    currency_symbol: "₹",
  });

  useEffect(() => {
    fetchStatus();
  }, []);

  const fetchStatus = async () => {
    try {
      setLoading(true);
      const data = await api.get<OnboardingStatus>("/onboarding/status");
      setStatus(data);
      if (data.onboarding_completed) {
        setCurrentStep(4);
      } else if (data.ai_configured) {
        setCurrentStep(4);
      } else if (data.team_members_count > 1 || data.pending_invites_count > 0) {
        setCurrentStep(3);
      } else if (data.profile_completed) {
        setCurrentStep(2);
      }

      const invs = await api.get<Invitation[]>("/onboarding/invitations").catch(() => []);
      setInvitations(invs);
    } catch (err: any) {
      console.error("Failed to load onboarding status:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleProfileSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setMessage(null);
      const res = await api.post<OnboardingStatus>("/onboarding/profile", profile);
      setStatus(res);
      setMessage({ type: "success", text: "Business profile saved successfully!" });
      setCurrentStep(2);
    } catch (err: any) {
      setMessage({ type: "error", text: err.message || "Failed to update profile." });
    }
  };

  const handleSendInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inviteEmail) return;
    try {
      setMessage(null);
      const newInv = await api.post<Invitation>("/onboarding/invite", {
        email: inviteEmail,
        role: inviteRole,
      });
      setInvitations((prev) => [...prev, newInv]);
      setInviteEmail("");
      setMessage({ type: "success", text: `Invitation sent to ${newInv.email} (${newInv.role}).` });
    } catch (err: any) {
      setMessage({ type: "error", text: err.message || "Failed to send invitation." });
    }
  };

  const handleAiConfigSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setMessage(null);
      const res = await api.post<OnboardingStatus>("/onboarding/ai-config", aiConfig);
      setStatus(res);
      setMessage({ type: "success", text: "AI engine parameters configured successfully!" });
      setCurrentStep(4);
    } catch (err: any) {
      setMessage({ type: "error", text: err.message || "Failed to configure AI engine." });
    }
  };

  const handleFinalize = async () => {
    try {
      setMessage(null);
      await api.post("/onboarding/complete");
      router.push("/dashboard");
    } catch (err: any) {
      setMessage({ type: "error", text: err.message || "Failed to finalize onboarding." });
    }
  };

  return (
    <AppLayout>
      <div className="space-y-8 max-w-4xl mx-auto pb-16">
        {/* Banner */}
        <div className="text-center space-y-2">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-semibold bg-blue-100 text-blue-800 dark:bg-blue-950/60 dark:text-blue-300 border border-blue-200 dark:border-blue-800">
            <Sparkles className="h-3.5 w-3.5" />
            DocuMind AI Commercial Onboarding Wizard
          </div>
          <h1 className="text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
            Set Up Your Organization
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 max-w-md mx-auto">
            Configure business details, invite team members with granular roles, and tune multi-agent AI validation.
          </p>
        </div>

        {/* Stepper Header */}
        <div className="grid grid-cols-4 gap-2 bg-white dark:bg-navy-900 p-3 rounded-2xl border border-slate-200 dark:border-navy-800 shadow-sm">
          {[
            { step: 1, label: "Profile", icon: Building2 },
            { step: 2, label: "Team", icon: Users },
            { step: 3, label: "AI Config", icon: Cpu },
            { step: 4, label: "Ready", icon: FileCheck2 },
          ].map((item) => {
            const isDone = currentStep > item.step;
            const isCurrent = currentStep === item.step;
            return (
              <div
                key={item.step}
                onClick={() => isDone && setCurrentStep(item.step)}
                className={`flex items-center gap-2.5 p-3 rounded-xl transition-all ${
                  isCurrent
                    ? "bg-blue-50 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400 font-semibold"
                    : isDone
                    ? "text-emerald-600 dark:text-emerald-400 cursor-pointer hover:bg-slate-50 dark:hover:bg-navy-800"
                    : "text-slate-400 dark:text-slate-500"
                }`}
              >
                <div
                  className={`h-8 w-8 rounded-lg flex items-center justify-center shrink-0 ${
                    isCurrent
                      ? "bg-blue-600 text-white shadow-sm"
                      : isDone
                      ? "bg-emerald-600 text-white"
                      : "bg-slate-100 dark:bg-navy-800 text-slate-400"
                  }`}
                >
                  {isDone ? <CheckCircle2 className="h-4 w-4" /> : <item.icon className="h-4 w-4" />}
                </div>
                <div className="hidden sm:block">
                  <span className="text-xs uppercase tracking-wider block opacity-70">Step {item.step}</span>
                  <span className="text-sm font-medium">{item.label}</span>
                </div>
              </div>
            );
          })}
        </div>

        {/* Message Banner */}
        {message && (
          <div
            className={`p-4 rounded-xl flex items-center gap-3 text-sm font-medium ${
              message.type === "success"
                ? "bg-emerald-50 text-emerald-900 border border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-200 dark:border-emerald-800"
                : "bg-red-50 text-red-900 border border-red-200 dark:bg-red-950/40 dark:text-red-200 dark:border-red-800"
            }`}
          >
            {message.type === "success" ? (
              <CheckCircle2 className="h-5 w-5 text-emerald-600 shrink-0" />
            ) : (
              <AlertCircle className="h-5 w-5 text-red-600 shrink-0" />
            )}
            <span>{message.text}</span>
          </div>
        )}

        {/* Step 1: Business Profile */}
        {currentStep === 1 && (
          <div className="bg-white dark:bg-navy-900 rounded-2xl border border-slate-200 dark:border-navy-800 p-6 md:p-8 shadow-sm">
            <h2 className="text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2 mb-2">
              <Building2 className="h-5 w-5 text-blue-600" />
              1. Legal Business Details & GST Compliance
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400 mb-6">
              Enter your registered business identity to calibrate Indian GST tax reconciliation and vendor matching.
            </p>

            <form onSubmit={handleProfileSubmit} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Legal Business Name
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Acme Logistics Private Limited"
                    value={profile.legal_name}
                    onChange={(e) => setProfile({ ...profile, legal_name: e.target.value })}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-navy-700 bg-slate-50 dark:bg-navy-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Indian GSTIN (15 characters)
                  </label>
                  <input
                    type="text"
                    maxLength={15}
                    placeholder="e.g. 27AAACG9876Q1Z5"
                    value={profile.gstin}
                    onChange={(e) => setProfile({ ...profile, gstin: e.target.value.toUpperCase() })}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-navy-700 bg-slate-50 dark:bg-navy-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Permanent Account Number (PAN)
                  </label>
                  <input
                    type="text"
                    maxLength={10}
                    placeholder="e.g. AAACG9876Q"
                    value={profile.pan}
                    onChange={(e) => setProfile({ ...profile, pan: e.target.value.toUpperCase() })}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-navy-700 bg-slate-50 dark:bg-navy-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Contact Phone Number
                  </label>
                  <input
                    type="text"
                    placeholder="+91-9876543210"
                    value={profile.phone}
                    onChange={(e) => setProfile({ ...profile, phone: e.target.value })}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-navy-700 bg-slate-50 dark:bg-navy-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Registered Office Address
                </label>
                <textarea
                  rows={2}
                  placeholder="Street address, business park, or commercial building"
                  value={profile.address}
                  onChange={(e) => setProfile({ ...profile, address: e.target.value })}
                  className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-navy-700 bg-slate-50 dark:bg-navy-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">City</label>
                  <input
                    type="text"
                    placeholder="Mumbai"
                    value={profile.city}
                    onChange={(e) => setProfile({ ...profile, city: e.target.value })}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-navy-700 bg-slate-50 dark:bg-navy-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">State</label>
                  <input
                    type="text"
                    placeholder="Maharashtra"
                    value={profile.state}
                    onChange={(e) => setProfile({ ...profile, state: e.target.value })}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-navy-700 bg-slate-50 dark:bg-navy-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Pincode</label>
                  <input
                    type="text"
                    placeholder="400001"
                    value={profile.pincode}
                    onChange={(e) => setProfile({ ...profile, pincode: e.target.value })}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-navy-700 bg-slate-50 dark:bg-navy-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono"
                  />
                </div>
              </div>

              <div className="pt-4 flex justify-end">
                <button
                  type="submit"
                  className="py-2.5 px-6 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-sm flex items-center gap-2 shadow-md shadow-blue-500/20"
                >
                  Save & Continue
                  <ArrowRight className="h-4 w-4" />
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Step 2: Team Members */}
        {currentStep === 2 && (
          <div className="bg-white dark:bg-navy-900 rounded-2xl border border-slate-200 dark:border-navy-800 p-6 md:p-8 shadow-sm space-y-6">
            <div>
              <h2 className="text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2 mb-1">
                <Users className="h-5 w-5 text-blue-600" />
                2. Invite Team & Assign Enterprise Roles
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Grant role-based access for accountants, reviewers, and compliance auditors.
              </p>
            </div>

            <form onSubmit={handleSendInvite} className="flex flex-col sm:flex-row gap-3">
              <div className="relative flex-1">
                <Mail className="absolute left-3.5 top-3 h-4 w-4 text-slate-400" />
                <input
                  type="email"
                  required
                  placeholder="colleague@yourcompany.com"
                  value={inviteEmail}
                  onChange={(e) => setInviteEmail(e.target.value)}
                  className="w-full pl-10 pr-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-navy-700 bg-slate-50 dark:bg-navy-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <select
                value={inviteRole}
                onChange={(e) => setInviteRole(e.target.value)}
                className="px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-navy-700 bg-slate-50 dark:bg-navy-800 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {ROLES.map((r) => (
                  <option key={r} value={r}>
                    {r}
                  </option>
                ))}
              </select>

              <button
                type="submit"
                className="py-2.5 px-5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-sm whitespace-nowrap shadow-md shadow-blue-500/20"
              >
                Send Invitation
              </button>
            </form>

            {/* Invitations Table */}
            {invitations.length > 0 && (
              <div className="border border-slate-200 dark:border-navy-800 rounded-xl overflow-hidden">
                <table className="w-full text-xs text-left">
                  <thead className="bg-slate-50 dark:bg-navy-800/60 text-slate-500 font-semibold uppercase tracking-wider">
                    <tr>
                      <th className="py-2.5 px-4">Email Address</th>
                      <th className="py-2.5 px-4">Role Assigned</th>
                      <th className="py-2.5 px-4">Status</th>
                      <th className="py-2.5 px-4">Expires</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200 dark:divide-navy-800">
                    {invitations.map((inv) => (
                      <tr key={inv.id} className="text-slate-700 dark:text-slate-300">
                        <td className="py-2.5 px-4 font-medium">{inv.email}</td>
                        <td className="py-2.5 px-4">
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300">
                            {inv.role}
                          </span>
                        </td>
                        <td className="py-2.5 px-4">
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300">
                            {inv.status}
                          </span>
                        </td>
                        <td className="py-2.5 px-4 text-slate-400">7 days</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            <div className="pt-4 flex justify-between">
              <button
                type="button"
                onClick={() => setCurrentStep(1)}
                className="py-2.5 px-4 rounded-xl border border-slate-200 dark:border-navy-700 text-sm font-semibold flex items-center gap-2 hover:bg-slate-50 dark:hover:bg-navy-800"
              >
                <ArrowLeft className="h-4 w-4" />
                Back
              </button>
              <button
                type="button"
                onClick={() => setCurrentStep(3)}
                className="py-2.5 px-6 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-sm flex items-center gap-2 shadow-md shadow-blue-500/20"
              >
                Continue to AI Config
                <ArrowRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        )}

        {/* Step 3: AI Engine Config */}
        {currentStep === 3 && (
          <div className="bg-white dark:bg-navy-900 rounded-2xl border border-slate-200 dark:border-navy-800 p-6 md:p-8 shadow-sm space-y-6">
            <div>
              <h2 className="text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2 mb-1">
                <Cpu className="h-5 w-5 text-blue-600" />
                3. Multi-Agent AI Engine & Provider Failover
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Select your primary and secondary AI engines and set autonomous approval thresholds.
              </p>
            </div>

            <form onSubmit={handleAiConfigSubmit} className="space-y-5">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Primary AI Inference Provider
                  </label>
                  <select
                    value={aiConfig.primary_provider}
                    onChange={(e) => setAiConfig({ ...aiConfig, primary_provider: e.target.value })}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-navy-700 bg-slate-50 dark:bg-navy-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="gemini">Google Gemini API (Primary Recommended)</option>
                    <option value="groq">Groq Cloud LPU (Ultra-Low Latency)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Secondary Failover Provider
                  </label>
                  <select
                    value={aiConfig.fallback_provider}
                    onChange={(e) => setAiConfig({ ...aiConfig, fallback_provider: e.target.value })}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-navy-700 bg-slate-50 dark:bg-navy-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="groq">Groq API (Instant Circuit Breaker Failover)</option>
                    <option value="gemini">Google Gemini API</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Autonomous Approval Threshold ({Math.round(aiConfig.auto_approve_threshold * 100)}%)
                  </label>
                  <input
                    type="range"
                    min="0.80"
                    max="1.00"
                    step="0.01"
                    value={aiConfig.auto_approve_threshold}
                    onChange={(e) => setAiConfig({ ...aiConfig, auto_approve_threshold: parseFloat(e.target.value) })}
                    className="w-full accent-blue-600"
                  />
                  <p className="text-[11px] text-slate-400 mt-1">
                    Invoices with field confidence &ge; {Math.round(aiConfig.auto_approve_threshold * 100)}% and zero math discrepancies are auto-approved.
                  </p>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Rounding Tax Tolerance Amount (₹{aiConfig.tax_tolerance.toFixed(2)})
                  </label>
                  <input
                    type="number"
                    step="0.5"
                    min="0"
                    max="10"
                    value={aiConfig.tax_tolerance}
                    onChange={(e) => setAiConfig({ ...aiConfig, tax_tolerance: parseFloat(e.target.value) })}
                    className="w-full px-3.5 py-2 rounded-xl border border-slate-200 dark:border-navy-700 bg-slate-50 dark:bg-navy-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <p className="text-[11px] text-slate-400 mt-1">
                    Allowable fraction rounding differences across subtotal + CGST/SGST reconciliations.
                  </p>
                </div>
              </div>

              <div className="pt-4 flex justify-between">
                <button
                  type="button"
                  onClick={() => setCurrentStep(2)}
                  className="py-2.5 px-4 rounded-xl border border-slate-200 dark:border-navy-700 text-sm font-semibold flex items-center gap-2 hover:bg-slate-50 dark:hover:bg-navy-800"
                >
                  <ArrowLeft className="h-4 w-4" />
                  Back
                </button>
                <button
                  type="submit"
                  className="py-2.5 px-6 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-sm flex items-center gap-2 shadow-md shadow-blue-500/20"
                >
                  Save & Complete Setup
                  <ArrowRight className="h-4 w-4" />
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Step 4: Finalize & First Invoice */}
        {currentStep === 4 && (
          <div className="bg-white dark:bg-navy-900 rounded-2xl border border-slate-200 dark:border-navy-800 p-8 shadow-sm text-center space-y-6">
            <div className="h-16 w-16 bg-emerald-100 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400 rounded-2xl flex items-center justify-center mx-auto">
              <CheckCircle2 className="h-8 w-8" />
            </div>

            <div>
              <h2 className="text-2xl font-extrabold text-slate-900 dark:text-white">Organization Ready!</h2>
              <p className="text-sm text-slate-500 dark:text-slate-400 max-w-md mx-auto mt-1">
                Your business profile, multi-agent pipeline, and enterprise roles are active. You are on the STARTER 14-day free trial.
              </p>
            </div>

            <div className="flex flex-col sm:flex-row gap-4 justify-center pt-2">
              <button
                onClick={() => router.push("/upload")}
                className="py-3 px-6 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-sm flex items-center justify-center gap-2 shadow-md shadow-blue-500/20"
              >
                <UploadCloud className="h-4 w-4" />
                Upload First Invoice
              </button>

              <button
                onClick={handleFinalize}
                className="py-3 px-6 rounded-xl border border-slate-200 dark:border-navy-700 text-slate-700 dark:text-slate-200 font-semibold text-sm hover:bg-slate-50 dark:hover:bg-navy-800 flex items-center justify-center gap-2"
              >
                Go to Dashboard
                <ArrowRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        )}
      </div>
    </AppLayout>
  );
}
