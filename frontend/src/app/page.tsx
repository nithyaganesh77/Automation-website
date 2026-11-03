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
  Lock,
  Layers,
  Sparkles,
  Server,
  Cloud,
  FileSpreadsheet,
  AlertTriangle,
} from "lucide-react";

export default function HomePage() {
  return (
    <div className="min-h-screen flex flex-col bg-slate-50 dark:bg-navy-950 text-slate-900 dark:text-white">
      <PublicNav />

      {/* Hero Section */}
      <section className="relative overflow-hidden pt-12 pb-20 md:pt-20 md:pb-32 border-b border-slate-200 dark:border-navy-800 bg-gradient-to-b from-blue-50/50 via-white to-slate-50 dark:from-navy-900/60 dark:via-navy-950 dark:to-navy-950">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center space-y-6">
          {/* Pilot Badge */}
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-semibold bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300 border border-blue-200 dark:border-blue-800 shadow-sm">
            <Sparkles className="h-4 w-4 text-blue-600" />
            <span>Now Accepting Commercial Pilot Customers in India</span>
          </div>

          <h1 className="text-4xl sm:text-5xl md:text-6xl font-extrabold tracking-tight max-w-4xl mx-auto leading-tight">
            Autonomous Invoice Intelligence &{" "}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-indigo-600">
              Indian GST Automation
            </span>
          </h1>

          <p className="text-base sm:text-lg text-slate-600 dark:text-slate-300 max-w-2xl mx-auto leading-relaxed">
            Eliminate hours of manual accounts payable data entry. Nine collaborative LangGraph AI agents extract, validate, check tax math, detect duplicate vendor bills, and export reconciled accounting ledgers.
          </p>

          {/* Action CTAs */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
            <Link
              href="/register"
              className="w-full sm:w-auto px-8 py-3.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-sm flex items-center justify-center gap-2 shadow-lg shadow-blue-500/25 transition-all"
            >
              Start 14-Day Free Pilot Trial
              <ArrowRight className="h-4 w-4" />
            </Link>
            <Link
              href="/demo"
              className="w-full sm:w-auto px-7 py-3.5 rounded-xl border border-slate-300 dark:border-navy-700 bg-white dark:bg-navy-900 text-slate-700 dark:text-slate-200 font-semibold text-sm hover:bg-slate-50 dark:hover:bg-navy-800 flex items-center justify-center gap-2 transition-all shadow-sm"
            >
              Explore Interactive Demo
            </Link>
          </div>

          {/* Value Props Strip */}
          <div className="pt-8 flex flex-wrap items-center justify-center gap-6 text-xs font-medium text-slate-500 dark:text-slate-400">
            <span className="flex items-center gap-1.5">
              <CheckCircle2 className="h-4 w-4 text-emerald-500" />
              Zero Upfront Software Cost
            </span>
            <span className="flex items-center gap-1.5">
              <CheckCircle2 className="h-4 w-4 text-emerald-500" />
              Bring-Your-Own-Key (BYOK)
            </span>
            <span className="flex items-center gap-1.5">
              <CheckCircle2 className="h-4 w-4 text-emerald-500" />
              Deterministic CGST/SGST/IGST Verification
            </span>
            <span className="flex items-center gap-1.5">
              <CheckCircle2 className="h-4 w-4 text-emerald-500" />
              On-Premises or Cloud Docker
            </span>
          </div>
        </div>
      </section>

      {/* 9-Agent Workflow Visual */}
      <section className="py-16 md:py-24 border-b border-slate-200 dark:border-navy-800 bg-white dark:bg-navy-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
          <div className="text-center space-y-3 max-w-3xl mx-auto">
            <span className="text-xs font-bold uppercase tracking-wider text-blue-600 dark:text-blue-400">
              Autonomous Intelligence
            </span>
            <h2 className="text-3xl font-bold tracking-tight">The 9-Agent Multi-Agent Workflow</h2>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Unlike fragile single-prompt wrappers, DocuMind AI orchestrates a stateful LangGraph pipeline where specialized agents review each invoice sequentially.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[
              {
                num: "01",
                name: "Intake & Parser Agent",
                desc: "PyMuPDF digital extraction with local PaddleOCR fallback for scanned or mobile photograph receipts.",
                icon: FileCheck2,
              },
              {
                num: "02",
                name: "Classifier Agent",
                desc: "High-speed heuristic layout matcher (<1ms) routing invoices, POs, bills, and challans accurately.",
                icon: Layers,
              },
              {
                num: "03",
                name: "Extraction Agent",
                desc: "Dual-provider extraction powered by Gemini 2.5 Flash with Groq LPU circuit breaker failover.",
                icon: Cpu,
              },
              {
                num: "04",
                name: "Indian GST Math Validator",
                desc: "Deterministic rule engine testing line items, taxable values, 9% CGST + 9% SGST vs 18% IGST.",
                icon: Zap,
              },
              {
                num: "05",
                name: "Duplicate Detection Agent",
                desc: "SHA-256 byte hashing and supplier invoice number matching preventing duplicate payments.",
                icon: AlertTriangle,
              },
              {
                num: "06",
                name: "Anomaly & Spend Agent",
                desc: "Statistical baseline scoring flagging unusual price jumps (>3x vendor median) and round numbers.",
                icon: BarChart3,
              },
              {
                num: "07",
                name: "Confidence Scorer Agent",
                desc: "Bayesian certainty weighting dynamically determining whether document qualifies for auto-approval.",
                icon: ShieldCheck,
              },
              {
                num: "08",
                name: "Human-in-the-Loop Router",
                desc: "Zero silent approvals. Financial edge cases routed to authorized accountants with side-by-side PDF preview.",
                icon: Lock,
              },
              {
                num: "09",
                name: "ERP Persistence & Export",
                desc: "Stores verified records in PostgreSQL and exports multi-sheet Excel ledgers ready for Tally/Zoho.",
                icon: FileSpreadsheet,
              },
            ].map((agent) => (
              <div
                key={agent.num}
                className="p-6 rounded-2xl bg-slate-50 dark:bg-navy-800/60 border border-slate-200 dark:border-navy-700/80 hover:border-blue-400 transition-all space-y-3"
              >
                <div className="flex items-center justify-between">
                  <div className="h-10 w-10 rounded-xl bg-blue-100 dark:bg-blue-950 flex items-center justify-center text-blue-600 dark:text-blue-400">
                    <agent.icon className="h-5 w-5" />
                  </div>
                  <span className="font-mono text-xs font-bold text-slate-400">{agent.num}</span>
                </div>
                <h3 className="font-bold text-base text-slate-900 dark:text-white">{agent.name}</h3>
                <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">{agent.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Deployment Flexibility */}
      <section className="py-16 md:py-24 border-b border-slate-200 dark:border-navy-800 bg-slate-50 dark:bg-navy-950">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
          <div className="text-center space-y-3 max-w-2xl mx-auto">
            <span className="text-xs font-bold uppercase tracking-wider text-blue-600 dark:text-blue-400">
              Customer Installation Options
            </span>
            <h2 className="text-3xl font-bold tracking-tight">Deploy Where Your Finance Team Works</h2>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Keep your sensitive business invoices on your own local server or utilize our secure managed cloud.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-4xl mx-auto">
            <div className="p-8 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-800 shadow-sm space-y-4">
              <div className="h-12 w-12 rounded-xl bg-indigo-100 dark:bg-indigo-950 flex items-center justify-center text-indigo-600 dark:text-indigo-400">
                <Server className="h-6 w-6" />
              </div>
              <h3 className="text-xl font-bold text-slate-900 dark:text-white">Customer-Hosted / On-Premises</h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
                Run DocuMind AI on your own Windows server, Linux machine, or internal Docker cluster. Financial documents never leave your company network.
              </p>
              <ul className="space-y-2 text-xs text-slate-600 dark:text-slate-300">
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                  Docker Compose one-click stack (Postgres + Redis + MinIO)
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                  Bring-Your-Own-Key for Google Gemini and Groq
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                  Full local database backup & disaster recovery
                </li>
              </ul>
              <div className="pt-2">
                <Link
                  href="/features"
                  className="text-xs font-bold text-blue-600 hover:underline flex items-center gap-1"
                >
                  View Installation Specifications &rarr;
                </Link>
              </div>
            </div>

            <div className="p-8 rounded-2xl bg-white dark:bg-navy-900 border border-slate-200 dark:border-navy-800 shadow-sm space-y-4">
              <div className="h-12 w-12 rounded-xl bg-blue-100 dark:bg-blue-950 flex items-center justify-center text-blue-600 dark:text-blue-400">
                <Cloud className="h-6 w-6" />
              </div>
              <h3 className="text-xl font-bold text-slate-900 dark:text-white">Managed Indian Cloud SaaS</h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
                Zero infrastructure overhead. Sign up, configure your business profile and GSTIN, invite your team, and start automating accounts payable in 5 minutes.
              </p>
              <ul className="space-y-2 text-xs text-slate-600 dark:text-slate-300">
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                  Indian data center hosting compliant with DPDP Act 2023
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                  14-day free trial on STARTER & PROFESSIONAL plans
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                  Role-based tenant isolation & 24/7 cluster monitoring
                </li>
              </ul>
              <div className="pt-2">
                <Link
                  href="/pricing"
                  className="text-xs font-bold text-blue-600 hover:underline flex items-center gap-1"
                >
                  Compare Commercial Plans &rarr;
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16 md:py-20 bg-blue-600 text-white">
        <div className="max-w-4xl mx-auto px-4 text-center space-y-6">
          <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight">
            Ready to Automate Your Business Invoices?
          </h2>
          <p className="text-sm sm:text-base text-blue-100 max-w-xl mx-auto">
            Join our Indian business pilot program. Zero setup fees, complete data privacy, and direct engineer support.
          </p>
          <div className="flex flex-col sm:flex-row justify-center gap-4 pt-2">
            <Link
              href="/register"
              className="px-8 py-3.5 rounded-xl bg-white text-blue-600 font-bold text-sm hover:bg-blue-50 shadow-lg shadow-blue-700/50 transition-all"
            >
              Start 14-Day Free Trial
            </Link>
            <Link
              href="/demo"
              className="px-8 py-3.5 rounded-xl border border-blue-400 text-white font-semibold text-sm hover:bg-blue-700/60 transition-all"
            >
              Request Controlled Pilot
            </Link>
          </div>
        </div>
      </section>

      <PublicFooter />
    </div>
  );
}
