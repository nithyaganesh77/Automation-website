"use client";

import { useState } from "react";
import Link from "next/link";
import { PublicNav } from "@/components/layout/PublicNav";
import { PublicFooter } from "@/components/layout/PublicFooter";
import {
  Sparkles,
  CheckCircle2,
  Building2,
  Mail,
  Phone,
  FileText,
  Server,
  ArrowRight,
  ShieldCheck,
  Zap,
  Layers,
  BarChart3,
  FileSpreadsheet,
} from "lucide-react";

export default function DemoPage() {
  const [submitted, setSubmitted] = useState(false);
  const [activeDemoStep, setActiveDemoStep] = useState(1);
  const [formData, setFormData] = useState({
    company_name: "",
    contact_name: "",
    email: "",
    phone: "",
    monthly_invoices: "100-500",
    accounting_system: "Tally Prime",
    deployment_preference: "cloud",
    consent_agreed: false,
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.consent_agreed) return;
    setSubmitted(true);
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 dark:bg-navy-950 text-slate-900 dark:text-white">
      <PublicNav />

      {/* Header */}
      <section className="pt-12 pb-14 border-b border-slate-200 dark:border-navy-800 bg-white dark:bg-navy-900 text-center">
        <div className="max-w-4xl mx-auto px-4 space-y-4">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300">
            <Sparkles className="h-3.5 w-3.5" />
            <span>Controlled Customer Pilot Program</span>
          </div>
          <h1 className="text-4xl font-extrabold tracking-tight">Experience DocuMind AI in Action</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 max-w-xl mx-auto">
            Explore our interactive synthetic walkthrough below or request a dedicated controlled pilot onboarding session for your finance team.
          </p>
        </div>
      </section>

      {/* Interactive Sandbox Walkthrough */}
      <section className="py-12 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 border-b border-slate-200 dark:border-navy-800">
        <div className="bg-white dark:bg-navy-900 rounded-3xl border border-slate-200 dark:border-navy-800 p-6 md:p-10 shadow-sm space-y-8">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-100 dark:border-navy-800">
            <div>
              <span className="text-xs font-bold text-blue-600 uppercase tracking-wider">Live Synthetic Sandbox</span>
              <h2 className="text-2xl font-bold mt-1">7-Step Document Lifecycle Walkthrough</h2>
            </div>
            <div className="flex flex-wrap gap-2">
              {[1, 2, 3, 4, 5, 6, 7].map((s) => (
                <button
                  key={s}
                  onClick={() => setActiveDemoStep(s)}
                  className={`h-8 w-8 rounded-lg text-xs font-bold transition-all ${
                    activeDemoStep === s
                      ? "bg-blue-600 text-white shadow-md shadow-blue-500/20"
                      : "bg-slate-100 dark:bg-navy-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200"
                  }`}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>

          {/* Sandbox Visual Display */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-center min-h-[280px]">
            {activeDemoStep === 1 && (
              <>
                <div className="space-y-4">
                  <span className="px-2.5 py-1 rounded-md text-[10px] font-bold bg-blue-100 text-blue-800 uppercase">
                    Step 1: Intake & Parse
                  </span>
                  <h3 className="text-xl font-bold">Document Ingestion & Local OCR</h3>
                  <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
                    Customer uploads single or batch PDFs, TIFFs, or mobile phone images. Native PDF text is extracted instantly via PyMuPDF; degraded scans route to local PaddleOCR engine.
                  </p>
                  <div className="text-xs font-mono text-slate-400">File: p2_invoice_01_clean_intra.pdf (12,410 bytes)</div>
                </div>
                <div className="p-5 rounded-2xl bg-slate-900 text-emerald-400 font-mono text-xs space-y-1">
                  <p className="text-slate-400">// Ingestion Log</p>
                  <p>&gt; Ingesting p2_invoice_01_clean_intra.pdf</p>
                  <p>&gt; SHA-256: 4b92c8... verified</p>
                  <p>&gt; OCR Engine: Native PDF (2 pages)</p>
                  <p>&gt; Status: Ingestion Complete (120ms)</p>
                </div>
              </>
            )}

            {activeDemoStep === 2 && (
              <>
                <div className="space-y-4">
                  <span className="px-2.5 py-1 rounded-md text-[10px] font-bold bg-indigo-100 text-indigo-800 uppercase">
                    Step 2: AI Multi-Agent Extraction
                  </span>
                  <h3 className="text-xl font-bold">Structured Information Extraction</h3>
                  <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
                    Extraction agent uses Google Gemini 2.5 Flash (with Groq LPU circuit breaker failover) to parse supplier name, GSTIN, PAN, line items, and taxes without fabricating values.
                  </p>
                </div>
                <div className="p-5 rounded-2xl bg-slate-900 text-slate-200 font-mono text-xs space-y-1">
                  <p className="text-slate-400">// Extracted Fields (JSON)</p>
                  <p className="text-blue-400">&quot;invoice_number&quot;: &quot;INV-2026-B001&quot;,</p>
                  <p className="text-blue-400">&quot;supplier_name&quot;: &quot;Apex Industrial Supplies Pvt Ltd&quot;,</p>
                  <p className="text-blue-400">&quot;supplier_gstin&quot;: &quot;27AAACG9876Q1Z5&quot;,</p>
                  <p className="text-blue-400">&quot;taxable_amount&quot;: 10000.00,</p>
                  <p className="text-blue-400">&quot;grand_total&quot;: 11800.00</p>
                </div>
              </>
            )}

            {activeDemoStep === 3 && (
              <>
                <div className="space-y-4">
                  <span className="px-2.5 py-1 rounded-md text-[10px] font-bold bg-emerald-100 text-emerald-800 uppercase">
                    Step 3: Deterministic GST Validation
                  </span>
                  <h3 className="text-xl font-bold">CGST + SGST vs IGST Verification</h3>
                  <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
                    Deterministic Python validation tests whether supplier state (27) matches buyer state (27), confirming Intra-State 9% CGST (₹900) + 9% SGST (₹900) matches grand total ₹11,800.00.
                  </p>
                </div>
                <div className="p-5 rounded-2xl bg-emerald-950 text-emerald-200 font-mono text-xs space-y-1 border border-emerald-800">
                  <p className="font-bold text-emerald-400">MATH VALIDATION PASSED [0.0ms]</p>
                  <p>&bull; Tax Rule: INTRA_STATE_9_9</p>
                  <p>&bull; Expected Tax: ₹1,800.00 | Stated Tax: ₹1,800.00</p>
                  <p>&bull; Math Discrepancy: ₹0.00 (within ₹2.00 tolerance)</p>
                </div>
              </>
            )}

            {activeDemoStep === 4 && (
              <>
                <div className="space-y-4">
                  <span className="px-2.5 py-1 rounded-md text-[10px] font-bold bg-amber-100 text-amber-800 uppercase">
                    Step 4: Duplicate & Anomaly Check
                  </span>
                  <h3 className="text-xl font-bold">Fraud & Duplicate Protection</h3>
                  <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
                    Evaluates SHA-256 byte hash against historical documents. If a duplicate invoice number or spend spike is found, the document is flagged for manual review.
                  </p>
                </div>
                <div className="p-5 rounded-2xl bg-slate-900 text-slate-200 font-mono text-xs space-y-1">
                  <p className="text-slate-400">// Security Scans</p>
                  <p>&bull; Duplicate Check: <span className="text-emerald-400">UNIQUE (No match found)</span></p>
                  <p>&bull; Historical Median: ₹9,500.00</p>
                  <p>&bull; Spend Spike Ratio: 1.05x (<span className="text-emerald-400">Normal Range &lt; 3x</span>)</p>
                  <p>&bull; Confidence Score: <span className="text-emerald-400 font-bold">99.2%</span></p>
                </div>
              </>
            )}

            {activeDemoStep === 5 && (
              <>
                <div className="space-y-4">
                  <span className="px-2.5 py-1 rounded-md text-[10px] font-bold bg-blue-100 text-blue-800 uppercase">
                    Step 5: Confidence & Routing
                  </span>
                  <h3 className="text-xl font-bold">Autonomous Auto-Approval</h3>
                  <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
                    With confidence (99.2%) exceeding the auto-approve threshold (98.0%) and zero math discrepancies, the document is automatically approved and saved into PostgreSQL.
                  </p>
                </div>
                <div className="p-5 rounded-2xl bg-blue-950 text-blue-200 font-mono text-xs space-y-1 border border-blue-800">
                  <p className="font-bold text-blue-400">ROUTER VERDICT: AUTO_APPROVED</p>
                  <p>&bull; Human Review Required: FALSE</p>
                  <p>&bull; Destination: PostgreSQL Table &apos;invoices&apos;</p>
                  <p>&bull; Audit Event Logged: INVOICE_AUTO_APPROVED</p>
                </div>
              </>
            )}

            {activeDemoStep === 6 && (
              <>
                <div className="space-y-4">
                  <span className="px-2.5 py-1 rounded-md text-[10px] font-bold bg-purple-100 text-purple-800 uppercase">
                    Step 6: Human Approval Center
                  </span>
                  <h3 className="text-xl font-bold">Human-in-the-Loop Review</h3>
                  <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
                    For ambiguous invoices or math mismatches, accountants receive side-by-side visual PDF inspection with highlighted discrepancy callouts and one-click field editing.
                  </p>
                </div>
                <div className="p-5 rounded-2xl bg-slate-900 text-slate-200 font-mono text-xs space-y-2">
                  <p className="text-slate-400">// Human Approval Center UI Preview</p>
                  <div className="flex gap-2 text-[11px]">
                    <span className="px-2 py-1 rounded bg-emerald-600 text-white font-bold">Approve (Enter)</span>
                    <span className="px-2 py-1 rounded bg-red-600 text-white font-bold">Reject (Esc)</span>
                    <span className="px-2 py-1 rounded bg-slate-700 text-white font-bold">Edit Fields</span>
                  </div>
                  <p className="text-[11px] text-slate-400 pt-1">Reviewer: ca_audit@zenithcorp.in</p>
                </div>
              </>
            )}

            {activeDemoStep === 7 && (
              <>
                <div className="space-y-4">
                  <span className="px-2.5 py-1 rounded-md text-[10px] font-bold bg-emerald-100 text-emerald-800 uppercase">
                    Step 7: Ledger Export
                  </span>
                  <h3 className="text-xl font-bold">Multi-Sheet Excel Accounting Export</h3>
                  <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
                    Generates standardized openpyxl Excel workbooks with separate tabs for Summary Ledgers, Line Item Detail, and GST Tax Breakdowns ready for Tally Prime or Zoho Books.
                  </p>
                </div>
                <div className="p-5 rounded-2xl bg-emerald-950 text-emerald-200 font-mono text-xs space-y-1 border border-emerald-800">
                  <p className="font-bold text-emerald-400">EXCEL EXPORT GENERATED</p>
                  <p>&bull; File: documind_export_20261103.xlsx</p>
                  <p>&bull; Sheets: [Summary, Invoices, Line Items, Tax Audit]</p>
                  <p>&bull; Reconciled Invoices: 5 | Total Value: ₹15,56,400.00</p>
                </div>
              </>
            )}
          </div>
        </div>
      </section>

      {/* Pilot Demo Request Form */}
      <section className="py-16 max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white dark:bg-navy-900 rounded-3xl border border-slate-200 dark:border-navy-800 p-8 md:p-12 shadow-sm space-y-6">
          <div className="text-center space-y-2">
            <h2 className="text-2xl font-bold">Request a Controlled Customer Pilot</h2>
            <p className="text-xs text-slate-500">
              We are onboarding three pilot businesses in India for hands-on production testing.
            </p>
          </div>

          {submitted ? (
            <div className="p-6 rounded-2xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 text-center space-y-3">
              <CheckCircle2 className="h-10 w-10 text-emerald-600 mx-auto" />
              <h3 className="text-base font-bold text-emerald-900 dark:text-emerald-200">
                Pilot Request Received!
              </h3>
              <p className="text-xs text-emerald-800 dark:text-emerald-300 max-w-md mx-auto leading-relaxed">
                Thank you for applying for the DocuMind AI pilot program. Our senior engineering team will contact{" "}
                <strong>{formData.email}</strong> within 24 business hours to arrange your guided onboarding session.
              </p>
              <div className="pt-2">
                <Link
                  href="/"
                  className="text-xs font-bold text-emerald-700 dark:text-emerald-400 hover:underline"
                >
                  Return to Home Page &rarr;
                </Link>
              </div>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Company Name
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Acme Logistics Pvt Ltd"
                    value={formData.company_name}
                    onChange={(e) => setFormData({ ...formData, company_name: e.target.value })}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-navy-700 bg-slate-50 dark:bg-navy-800 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Contact Person Name
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Ramesh Kumar (Finance Head)"
                    value={formData.contact_name}
                    onChange={(e) => setFormData({ ...formData, contact_name: e.target.value })}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-navy-700 bg-slate-50 dark:bg-navy-800 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Work Email
                  </label>
                  <input
                    type="email"
                    required
                    placeholder="ramesh@company.com"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-navy-700 bg-slate-50 dark:bg-navy-800 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Phone (+91)
                  </label>
                  <input
                    type="tel"
                    required
                    placeholder="+91-9876543210"
                    value={formData.phone}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-navy-700 bg-slate-50 dark:bg-navy-800 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Monthly Invoice Volume
                  </label>
                  <select
                    value={formData.monthly_invoices}
                    onChange={(e) => setFormData({ ...formData, monthly_invoices: e.target.value })}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-navy-700 bg-slate-50 dark:bg-navy-800 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="under-100">&lt; 100 invoices/month</option>
                    <option value="100-500">100 - 500 invoices/month</option>
                    <option value="500-2000">500 - 2,000 invoices/month</option>
                    <option value="2000-plus">2,000+ invoices/month</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Preferred Deployment
                  </label>
                  <select
                    value={formData.deployment_preference}
                    onChange={(e) => setFormData({ ...formData, deployment_preference: e.target.value })}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-navy-700 bg-slate-50 dark:bg-navy-800 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="cloud">Managed Indian Cloud (Zero Setup)</option>
                    <option value="onpremise">Customer-Hosted On-Premise Docker</option>
                  </select>
                </div>
              </div>

              {/* Consent Checkbox */}
              <div className="pt-2">
                <label className="flex items-start gap-2.5 text-xs text-slate-600 dark:text-slate-300 cursor-pointer">
                  <input
                    type="checkbox"
                    required
                    checked={formData.consent_agreed}
                    onChange={(e) => setFormData({ ...formData, consent_agreed: e.target.checked })}
                    className="mt-0.5 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span>
                    I confirm consent to participate in the controlled DocuMind AI pilot program and agree to the{" "}
                    <Link href="/terms" className="text-blue-600 underline">
                      Pilot Terms & Conditions
                    </Link>{" "}
                    and{" "}
                    <Link href="/privacy" className="text-blue-600 underline">
                      Privacy Policy
                    </Link>
                    .
                  </span>
                </label>
              </div>

              <button
                type="submit"
                className="w-full py-3 px-6 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs flex items-center justify-center gap-2 shadow-md shadow-blue-500/20"
              >
                Submit Pilot Application
                <ArrowRight className="h-4 w-4" />
              </button>
            </form>
          )}
        </div>
      </section>

      <PublicFooter />
    </div>
  );
}

