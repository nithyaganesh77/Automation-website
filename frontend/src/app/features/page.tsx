import Link from "next/link";
import { PublicNav } from "@/components/layout/PublicNav";
import { PublicFooter } from "@/components/layout/PublicFooter";
import {
  ShieldCheck,
  Zap,
  Cpu,
  BarChart3,
  FileCheck2,
  CheckCircle2,
  ArrowRight,
  Layers,
  FileSpreadsheet,
  AlertTriangle,
  FileSearch,
  Hash,
  Database,
  Lock,
} from "lucide-react";

export default function FeaturesPage() {
  return (
    <div className="min-h-screen flex flex-col bg-slate-50 dark:bg-navy-950 text-slate-900 dark:text-white">
      <PublicNav />

      {/* Hero */}
      <section className="pt-12 pb-16 border-b border-slate-200 dark:border-navy-800 bg-white dark:bg-navy-900 text-center">
        <div className="max-w-4xl mx-auto px-4 space-y-4">
          <span className="text-xs font-bold uppercase tracking-wider text-blue-600 dark:text-blue-400">
            Engine Architecture
          </span>
          <h1 className="text-4xl font-extrabold tracking-tight">Enterprise Features Built for Indian Accounting</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 max-w-2xl mx-auto">
            From complex multi-line tax invoices to duplicate detection and side-by-side human approval, discover how DocuMind AI automates your accounts payable.
          </p>
        </div>
      </section>

      {/* Feature Sections */}
      <section className="py-16 space-y-20 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Feature 1: Indian GST Math Engine */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-12 items-center">
          <div className="space-y-4">
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">
              <Zap className="h-3.5 w-3.5" />
              <span>Zero Silent Approvals</span>
            </div>
            <h2 className="text-2xl font-bold tracking-tight">Deterministic Indian GST Validation</h2>
            <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
              LLMs are notorious for mathematical hallucination. DocuMind AI enforces a strict deterministic validation barrier written in Python:
            </p>
            <ul className="space-y-2.5 text-xs text-slate-600 dark:text-slate-300">
              <li className="flex items-start gap-2">
                <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0 mt-0.5" />
                <span>
                  <strong>Intra vs Inter-State Reconciliation:</strong> Automatically verifies whether CGST (9%) + SGST (9%) or IGST (18%) applies based on supplier and customer state codes.
                </span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0 mt-0.5" />
                <span>
                  <strong>Line Item Subtotal Verification:</strong> Verifies that quantity &times; unit price &minus; discounts reconciles with stated taxable amount within your configured rounding tolerance (e.g. ₹2.00).
                </span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0 mt-0.5" />
                <span>
                  <strong>15-Character GSTIN Checksum:</strong> Validates format compliance and cross-references state codes against the Indian tax registry.
                </span>
              </li>
            </ul>
          </div>

          <div className="p-6 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-800 shadow-sm space-y-4 font-mono text-xs">
            <div className="flex items-center justify-between text-slate-400 pb-2 border-b border-slate-100 dark:border-navy-800">
              <span>GST Validation Trace</span>
              <span className="text-emerald-500 font-bold">100% RECONCILED</span>
            </div>
            <div className="space-y-1 text-slate-700 dark:text-slate-300">
              <p>Supplier GSTIN: <span className="text-blue-500">27AAACG9876Q1Z5</span> (Maharashtra - State 27)</p>
              <p>Customer GSTIN: <span className="text-blue-500">27BBBCY1234F1Z8</span> (Maharashtra - State 27)</p>
              <p>Transaction Type: <span className="text-emerald-500 font-bold">INTRA-STATE</span></p>
              <div className="my-2 p-3 rounded-lg bg-slate-50 dark:bg-navy-800 space-y-1">
                <p>Taxable Amount: ₹10,000.00</p>
                <p>CGST (9.0%):     ₹   900.00  [PASS]</p>
                <p>SGST (9.0%):     ₹   900.00  [PASS]</p>
                <p>IGST (0.0%):     ₹     0.00  [PASS]</p>
                <p className="font-bold pt-1 border-t border-slate-200 dark:border-navy-700">
                  Grand Total:     ₹11,800.00  [ZERO DISCREPANCY]
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Feature 2: Dual Provider Failover */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-12 items-center">
          <div className="order-2 md:order-1 p-6 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-800 shadow-sm space-y-4">
            <div className="flex items-center justify-between text-xs text-slate-400 pb-2 border-b border-slate-100 dark:border-navy-800">
              <span>Circuit Breaker Telemetry</span>
              <span className="text-emerald-500 font-bold">AUTO-ROUTED</span>
            </div>
            <div className="space-y-3 text-xs">
              <div className="p-3 rounded-xl bg-blue-50 dark:bg-blue-950/40 border border-blue-200 dark:border-blue-800">
                <span className="font-bold text-blue-600 block mb-1">Primary Engine: Google Gemini 2.5 Flash</span>
                <p className="text-slate-600 dark:text-slate-300">
                  Processes complex multimodal layouts with 1M tokens/min capacity on free tier.
                </p>
              </div>
              <div className="p-3 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800">
                <span className="font-bold text-emerald-600 block mb-1">Secondary Fallback: Groq Cloud LPU</span>
                <p className="text-slate-600 dark:text-slate-300">
                  High-speed inference (~3s per document). Automatically triggered when Google API rate limits hit.
                </p>
              </div>
            </div>
          </div>

          <div className="order-1 md:order-2 space-y-4">
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300">
              <Cpu className="h-3.5 w-3.5" />
              <span>Free-First Cloud Resilience</span>
            </div>
            <h2 className="text-2xl font-bold tracking-tight">Dual-Provider Automatic Failover</h2>
            <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
              Never let an API outage stall your accounting closing. If Google Gemini experiences high demand (HTTP 503) or rate limits, DocuMind AI's internal circuit breaker instantly redirects inference to Groq LPU for 180 seconds with zero dropped invoices.
            </p>
          </div>
        </div>

        {/* Feature 3: Duplicate & Spend Anomaly Detection */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-12 items-center">
          <div className="space-y-4">
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300">
              <AlertTriangle className="h-3.5 w-3.5" />
              <span>Fraud & Risk Protection</span>
            </div>
            <h2 className="text-2xl font-bold tracking-tight">Duplicate Detection & Spend Anomaly Alerts</h2>
            <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
              Prevent double payments and vendor billing errors before invoices hit your bank account:
            </p>
            <ul className="space-y-2.5 text-xs text-slate-600 dark:text-slate-300">
              <li className="flex items-start gap-2">
                <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0 mt-0.5" />
                <span>
                  <strong>SHA-256 Byte Hash Matching:</strong> Identifies re-uploaded identical PDF files instantly before running costly OCR.
                </span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0 mt-0.5" />
                <span>
                  <strong>Supplier Invoice Key Deduplication:</strong> Flags duplicate invoice numbers for the same supplier GSTIN across different billing dates.
                </span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0 mt-0.5" />
                <span>
                  <strong>Statistical Baseline Spikes:</strong> Calculates historical median spend per vendor and warns reviewers when an invoice is 3x higher than average.
                </span>
              </li>
            </ul>
          </div>

          <div className="p-6 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-800 shadow-sm space-y-3">
            <div className="flex items-center gap-2 text-xs font-bold text-amber-600">
              <AlertTriangle className="h-4 w-4" />
              <span>Anomaly Detected: Historical Spend Spike</span>
            </div>
            <p className="text-xs text-slate-600 dark:text-slate-300">
              Vendor <strong>Apex Industrial Supplies</strong>: Current bill ₹4,80,000.00 is <strong>3.4x higher</strong> than the 6-month historical median (₹1,40,000.00). Routed to Senior Accountant for verification.
            </p>
            <div className="pt-2 flex gap-2">
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300">
                REQUIRES REVIEW
              </span>
              <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-100 dark:bg-navy-800 text-slate-500">
                Rule ID: SPEND_SPIKE_3X
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-12 bg-slate-100 dark:bg-navy-900 border-t border-slate-200 dark:border-navy-800 text-center">
        <div className="max-w-2xl mx-auto px-4 space-y-4">
          <h3 className="text-2xl font-bold">See It in Action on Your Invoices</h3>
          <p className="text-xs text-slate-500">
            Sign up for our 14-day free trial or request a controlled pilot demonstration.
          </p>
          <div className="flex justify-center gap-3">
            <Link
              href="/register"
              className="py-2.5 px-6 rounded-xl bg-blue-600 text-white font-semibold text-xs shadow-md shadow-blue-500/20"
            >
              Start Free Trial
            </Link>
            <Link
              href="/demo"
              className="py-2.5 px-6 rounded-xl border border-slate-300 dark:border-navy-700 bg-white dark:bg-navy-800 text-xs font-semibold"
            >
              Request Demo
            </Link>
          </div>
        </div>
      </section>

      <PublicFooter />
    </div>
  );
}

