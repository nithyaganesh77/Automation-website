"use client";

import { useState } from "react";
import Link from "next/link";
import { PublicNav } from "@/components/layout/PublicNav";
import { PublicFooter } from "@/components/layout/PublicFooter";
import { CheckCircle2, ArrowRight, Sparkles, HelpCircle } from "lucide-react";

export default function PricingPage() {
  const [annual, setAnnual] = useState(false);

  const plans = [
    {
      name: "Starter Plan",
      tier: "STARTER",
      monthlyPrice: 2499,
      annualPrice: 24990,
      monthlyDocs: 50,
      seats: 3,
      desc: "Essential automated invoice extraction and audit for small Indian businesses & startups.",
      highlighted: false,
      features: [
        "Up to 50 invoices & bills per month",
        "Up to 3 team members (Admin & Reviewer)",
        "Deterministic Indian GST validation (CGST/SGST/IGST)",
        "Duplicate invoice detection (SHA-256 hash)",
        "Standard multi-sheet Excel ledger exports",
        "Dual AI provider failover (Gemini + Groq)",
        "Standard email support (24-hour SLA)",
      ],
    },
    {
      name: "Professional Plan",
      tier: "PROFESSIONAL",
      monthlyPrice: 9999,
      annualPrice: 99990,
      monthlyDocs: 500,
      seats: 15,
      desc: "Comprehensive document intelligence and vendor risk automation for growing businesses and CA firms.",
      highlighted: true,
      badge: "Most Popular for SMEs",
      features: [
        "Up to 500 documents per month",
        "Up to 15 team members across all 6 enterprise roles",
        "Advanced multi-agent spend anomaly & spike detection",
        "Vendor historical spend baseline & risk scoring",
        "Custom approval routing rules & thresholds",
        "Priority LLM inference queue",
        "Audit log export & complete compliance history",
        "Priority Slack & WhatsApp pilot engineer support",
      ],
    },
    {
      name: "Enterprise Plan",
      tier: "ENTERPRISE",
      monthlyPrice: 29999,
      annualPrice: 299990,
      monthlyDocs: 5000,
      seats: 100,
      desc: "High-throughput autonomous processing, multi-department segregation, and custom on-premise SLA.",
      highlighted: false,
      features: [
        "5,000+ monthly documents (custom scaling)",
        "Unlimited departments & up to 100 team members",
        "Complete multi-tenant data segregation",
        "Dedicated customer-hosted / on-premise Docker option",
        "Custom ERP and accounting API integrations (Tally / Zoho)",
        "Bring-Your-Own-Key (BYOK) for zero cloud markup",
        "Dedicated Enterprise SLA & 24/7 emergency support",
        "Custom legal Data Processing Addendum (DPA)",
      ],
    },
  ];

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 dark:bg-navy-950 text-slate-900 dark:text-white">
      <PublicNav />

      {/* Header */}
      <section className="pt-12 pb-14 border-b border-slate-200 dark:border-navy-800 bg-white dark:bg-navy-900 text-center">
        <div className="max-w-4xl mx-auto px-4 space-y-4">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300">
            <Sparkles className="h-3.5 w-3.5" />
            <span>14-Day Free Pilot Trial Included</span>
          </div>
          <h1 className="text-4xl font-extrabold tracking-tight">Transparent Indian Pricing in INR</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 max-w-xl mx-auto">
            Choose the plan that fits your monthly invoice volume. Zero hidden fees. Cancel or upgrade anytime.
          </p>

          {/* Monthly / Annual Toggle */}
          <div className="pt-4 flex items-center justify-center gap-3">
            <span className={`text-xs font-semibold ${!annual ? "text-slate-900 dark:text-white" : "text-slate-400"}`}>
              Monthly Billing
            </span>
            <button
              onClick={() => setAnnual(!annual)}
              className="w-12 h-6 rounded-full bg-blue-600 p-1 flex items-center transition-colors"
            >
              <div
                className={`w-4 h-4 rounded-full bg-white transition-transform ${annual ? "translate-x-6" : ""}`}
              />
            </button>
            <span className={`text-xs font-semibold ${annual ? "text-slate-900 dark:text-white" : "text-slate-400"}`}>
              Annual Billing <span className="text-emerald-500 font-bold">(Save 2 Months)</span>
            </span>
          </div>
        </div>
      </section>

      {/* Pricing Cards */}
      <section className="py-16 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {plans.map((p) => {
            const price = annual ? Math.round(p.annualPrice / 12) : p.monthlyPrice;
            return (
              <div
                key={p.tier}
                className={`relative rounded-2xl bg-white dark:bg-navy-900 p-8 border flex flex-col justify-between transition-all ${
                  p.highlighted
                    ? "border-blue-500 dark:border-blue-500 shadow-xl shadow-blue-500/10 ring-2 ring-blue-500/20"
                    : "border-slate-200 dark:border-navy-800 hover:border-slate-300"
                }`}
              >
                {p.highlighted && (
                  <span className="absolute -top-3.5 left-1/2 -translate-x-1/2 px-3.5 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-blue-600 text-white shadow-md">
                    {p.badge}
                  </span>
                )}

                <div>
                  <h3 className="text-xl font-bold text-slate-900 dark:text-white">{p.name}</h3>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 min-h-[36px]">{p.desc}</p>

                  <div className="mt-5 flex items-baseline gap-1">
                    <span className="text-4xl font-extrabold text-slate-900 dark:text-white">
                      ₹{price.toLocaleString("en-IN")}
                    </span>
                    <span className="text-xs font-medium text-slate-400">/month</span>
                  </div>
                  <p className="text-[11px] text-slate-400 mt-0.5">
                    {annual
                      ? `Billed annually (₹${p.annualPrice.toLocaleString("en-IN")}/yr)`
                      : `Billed monthly + 18% GST`}
                  </p>

                  <div className="my-6 p-3.5 rounded-xl bg-slate-50 dark:bg-navy-800/60 text-xs font-medium space-y-1.5">
                    <div className="flex justify-between">
                      <span className="text-slate-500">Document Quota:</span>
                      <span className="font-bold text-blue-600 dark:text-blue-400">{p.monthlyDocs} docs/mo</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Included Seats:</span>
                      <span className="font-bold text-slate-900 dark:text-white">{p.seats} users</span>
                    </div>
                  </div>

                  <div className="space-y-2.5 mb-8">
                    {p.features.map((f, i) => (
                      <div key={i} className="flex items-start gap-2.5 text-xs text-slate-600 dark:text-slate-300">
                        <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0 mt-0.5" />
                        <span>{f}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <Link
                  href="/register"
                  className={`w-full py-3 px-4 rounded-xl text-xs font-semibold flex items-center justify-center gap-2 transition-all ${
                    p.highlighted
                      ? "bg-blue-600 hover:bg-blue-700 text-white shadow-md shadow-blue-500/20"
                      : "bg-slate-900 hover:bg-slate-800 text-white dark:bg-slate-100 dark:text-slate-900 dark:hover:bg-white"
                  }`}
                >
                  Start 14-Day Free Trial
                  <ArrowRight className="h-4 w-4" />
                </Link>
              </div>
            );
          })}
        </div>
      </section>

      {/* Pricing FAQs */}
      <section className="py-16 border-t border-slate-200 dark:border-navy-800 bg-white dark:bg-navy-900">
        <div className="max-w-4xl mx-auto px-4 space-y-8">
          <div className="text-center space-y-2">
            <h2 className="text-2xl font-bold">Frequently Asked Questions</h2>
            <p className="text-xs text-slate-500">Everything you need to know about DocuMind AI commercial licensing.</p>
          </div>

          <div className="space-y-4 text-xs">
            {[
              {
                q: "What happens when my organization reaches its monthly document limit?",
                a: "DocuMind AI never silently bills surprise overages. When your quota is reached, subsequent uploads are safely held and return HTTP 402 with an option to instantly upgrade to the next tier or wait for your monthly reset.",
              },
              {
                q: "Do I need a credit card to start the 14-day free trial?",
                a: "No credit card or upfront payment is required. You can register your organization, configure your business profile and GSTIN, and process pilot invoices immediately.",
              },
              {
                q: "Can we install DocuMind AI on our own Windows server or Linux Docker host?",
                a: "Yes. Our Enterprise plan includes full customer-hosted Docker Compose deployment with Bring-Your-Own-Key (BYOK) for Gemini and Groq, ensuring documents never leave your corporate intranet.",
              },
              {
                q: "Are my documents used to train AI models?",
                a: "Never. Under our enterprise terms, customer financial documents are strictly processed ephemerally for extraction and are never stored or used to train third-party foundation models.",
              },
            ].map((faq, idx) => (
              <div key={idx} className="p-5 rounded-xl bg-slate-50 dark:bg-navy-800/50 border border-slate-200 dark:border-navy-700/60 space-y-2">
                <h4 className="font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <HelpCircle className="h-4 w-4 text-blue-500 shrink-0" />
                  {faq.q}
                </h4>
                <p className="text-slate-600 dark:text-slate-300 leading-relaxed pl-6">{faq.a}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <PublicFooter />
    </div>
  );
}

