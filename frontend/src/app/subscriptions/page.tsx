"use client";

import { useEffect, useState } from "react";
import { AppLayout } from "@/components/layout/AppLayout";
import { api } from "@/lib/api-client";
import {
  CreditCard,
  CheckCircle2,
  AlertCircle,
  Zap,
  TrendingUp,
  ShieldCheck,
  Building,
  Users,
  FileCheck,
  ArrowRight,
} from "lucide-react";

interface PlanDetails {
  tier: string;
  name: string;
  description: string;
  monthly_price_inr: number;
  annual_price_inr: number;
  monthly_document_limit: number;
  max_users_limit: number;
  features: string[];
  highlighted: boolean;
}

interface SubscriptionStatus {
  plan_tier: string;
  status: string;
  is_trial: boolean;
  trial_days_remaining: number | null;
  documents_used: number;
  monthly_document_limit: number;
  users_count: number;
  max_users_limit: number;
  can_upload: boolean;
  usage_percentage: number;
  billing_cycle: string;
  price_amount: number;
  currency: string;
  current_period_start: string;
  current_period_end: string | null;
}

export default function SubscriptionsPage() {
  const [plans, setPlans] = useState<PlanDetails[]>([]);
  const [currentSub, setCurrentSub] = useState<SubscriptionStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [upgradingTier, setUpgradingTier] = useState<string | null>(null);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  useEffect(() => {
    fetchSubscriptionData();
  }, []);

  const fetchSubscriptionData = async () => {
    try {
      setLoading(true);
      const [plansData, currentData] = await Promise.all([
        api.get<PlanDetails[]>("/subscriptions/plans"),
        api.get<SubscriptionStatus>("/subscriptions/current"),
      ]);
      setPlans(plansData);
      setCurrentSub(currentData);
    } catch (err: any) {
      console.error("Failed to load subscription details:", err);
      setMessage({ type: "error", text: err.message || "Failed to load subscription details." });
    } finally {
      setLoading(false);
    }
  };

  const handleUpgrade = async (tier: string) => {
    try {
      setUpgradingTier(tier);
      setMessage(null);
      const updated = await api.post<SubscriptionStatus>("/subscriptions/upgrade", {
        target_plan: tier,
        billing_cycle: "MONTHLY",
      });
      setCurrentSub(updated);
      setMessage({
        type: "success",
        text: `Successfully upgraded organization to ${tier} Plan (${updated.monthly_document_limit} docs/mo)!`,
      });
    } catch (err: any) {
      setMessage({ type: "error", text: err.message || "Failed to upgrade subscription." });
    } finally {
      setUpgradingTier(null);
    }
  };

  return (
    <AppLayout>
      <div className="space-y-8 max-w-7xl mx-auto pb-12">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white flex items-center gap-2.5">
              <CreditCard className="h-7 w-7 text-blue-600" />
              Subscription & Usage Management
            </h1>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
              Commercial multi-tenant billing tiers, document processing quotas, and team licensing.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-800">
              <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
              Razorpay Ready (No Paid Keys Required)
            </span>
          </div>
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

        {/* Current Plan & Quota Card */}
        {currentSub && (
          <div className="bg-white dark:bg-navy-900 rounded-2xl border border-slate-200 dark:border-navy-800 p-6 md:p-8 shadow-sm">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-center">
              {/* Plan info */}
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Active Plan</span>
                  {currentSub.is_trial && (
                    <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300 border border-amber-300">
                      TRIAL ({currentSub.trial_days_remaining ?? 14} days left)
                    </span>
                  )}
                </div>
                <h3 className="text-3xl font-extrabold text-slate-900 dark:text-white mt-1">
                  {currentSub.plan_tier} Plan
                </h3>
                <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
                  Billed {currentSub.billing_cycle.toLowerCase()} in {currentSub.currency}.
                </p>
              </div>

              {/* Monthly Document Usage Bar */}
              <div className="space-y-2">
                <div className="flex justify-between items-center text-sm font-medium">
                  <span className="text-slate-600 dark:text-slate-300 flex items-center gap-1.5">
                    <FileCheck className="h-4 w-4 text-blue-500" />
                    Monthly Documents
                  </span>
                  <span className="text-slate-900 dark:text-white font-bold">
                    {currentSub.documents_used} / {currentSub.monthly_document_limit} ({currentSub.usage_percentage}%)
                  </span>
                </div>
                <div className="w-full h-3 bg-slate-100 dark:bg-navy-800 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${
                      currentSub.usage_percentage >= 90
                        ? "bg-red-500"
                        : currentSub.usage_percentage >= 70
                        ? "bg-amber-500"
                        : "bg-blue-600"
                    }`}
                    style={{ width: `${Math.min(currentSub.usage_percentage, 100)}%` }}
                  />
                </div>
                <p className="text-xs text-slate-400">
                  {currentSub.monthly_document_limit - currentSub.documents_used} uploads remaining this billing period.
                </p>
              </div>

              {/* Team Members Limit */}
              <div className="space-y-2">
                <div className="flex justify-between items-center text-sm font-medium">
                  <span className="text-slate-600 dark:text-slate-300 flex items-center gap-1.5">
                    <Users className="h-4 w-4 text-emerald-500" />
                    Active Team Members
                  </span>
                  <span className="text-slate-900 dark:text-white font-bold">
                    {currentSub.users_count} / {currentSub.max_users_limit} seats
                  </span>
                </div>
                <div className="w-full h-3 bg-slate-100 dark:bg-navy-800 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-emerald-500 rounded-full transition-all duration-500"
                    style={{
                      width: `${Math.min((currentSub.users_count / currentSub.max_users_limit) * 100, 100)}%`,
                    }}
                  />
                </div>
                <p className="text-xs text-slate-400">
                  6 supported enterprise roles with multi-tenant data isolation.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Pricing Tier Comparison Cards */}
        <div>
          <h2 className="text-xl font-bold text-slate-900 dark:text-white mb-2">Available Commercial Tiers</h2>
          <p className="text-sm text-slate-500 dark:text-slate-400 mb-6">
            Transparent INR pricing designed for Indian businesses, SMEs, and automated enterprise accounts payable.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {plans.map((p) => {
              const isCurrent = currentSub?.plan_tier === p.tier;
              const isUpgrading = upgradingTier === p.tier;

              return (
                <div
                  key={p.tier}
                  className={`relative flex flex-col rounded-2xl bg-white dark:bg-navy-900 border transition-all duration-200 p-6 md:p-8 ${
                    p.highlighted
                      ? "border-blue-500 dark:border-blue-500 shadow-lg shadow-blue-500/10 ring-2 ring-blue-500/20"
                      : "border-slate-200 dark:border-navy-800 hover:border-slate-300 dark:hover:border-navy-700"
                  }`}
                >
                  {p.highlighted && (
                    <span className="absolute -top-3.5 left-1/2 -translate-x-1/2 px-3 py-1 rounded-full text-xs font-bold tracking-wide uppercase bg-blue-600 text-white shadow-md">
                      Most Popular for SMEs
                    </span>
                  )}

                  <div className="mb-6">
                    <h3 className="text-xl font-bold text-slate-900 dark:text-white">{p.name}</h3>
                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 min-h-[36px]">{p.description}</p>
                    <div className="mt-4 flex items-baseline gap-1">
                      <span className="text-3xl font-extrabold text-slate-900 dark:text-white">
                        ₹{p.monthly_price_inr.toLocaleString("en-IN")}
                      </span>
                      <span className="text-sm font-medium text-slate-400">/month</span>
                    </div>
                    <p className="text-xs text-slate-400 mt-0.5">
                      Or ₹{p.annual_price_inr.toLocaleString("en-IN")}/year (save 2 months)
                    </p>
                  </div>

                  {/* Highlights */}
                  <div className="p-3 rounded-xl bg-slate-50 dark:bg-navy-800/50 mb-6 space-y-1.5 text-xs text-slate-600 dark:text-slate-300">
                    <div className="flex items-center justify-between font-semibold">
                      <span>Monthly Limit:</span>
                      <span className="text-blue-600 dark:text-blue-400">{p.monthly_document_limit} docs/mo</span>
                    </div>
                    <div className="flex items-center justify-between font-semibold">
                      <span>Max Team Seats:</span>
                      <span className="text-blue-600 dark:text-blue-400">{p.max_users_limit} users</span>
                    </div>
                  </div>

                  {/* Feature Checklist */}
                  <div className="flex-1 space-y-2.5 mb-8">
                    {p.features.map((f, idx) => (
                      <div key={idx} className="flex items-start gap-2.5 text-xs text-slate-600 dark:text-slate-300">
                        <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0 mt-0.5" />
                        <span>{f}</span>
                      </div>
                    ))}
                  </div>

                  {/* Action Button */}
                  <button
                    disabled={isCurrent || isUpgrading}
                    onClick={() => handleUpgrade(p.tier)}
                    className={`w-full py-2.5 px-4 rounded-xl text-sm font-semibold transition-all duration-150 flex items-center justify-center gap-2 ${
                      isCurrent
                        ? "bg-slate-100 dark:bg-navy-800 text-slate-400 dark:text-slate-500 cursor-default"
                        : p.highlighted
                        ? "bg-blue-600 hover:bg-blue-700 text-white shadow-md shadow-blue-500/20"
                        : "bg-slate-900 hover:bg-slate-800 text-white dark:bg-slate-100 dark:hover:bg-white dark:text-slate-900"
                    }`}
                  >
                    {isCurrent ? (
                      "Current Active Plan"
                    ) : isUpgrading ? (
                      "Processing..."
                    ) : (
                      <>
                        Switch to {p.tier}
                        <ArrowRight className="h-4 w-4" />
                      </>
                    )}
                  </button>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </AppLayout>
  );
}
