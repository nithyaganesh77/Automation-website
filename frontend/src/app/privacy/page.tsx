import { PublicNav } from "@/components/layout/PublicNav";
import { PublicFooter } from "@/components/layout/PublicFooter";
import { ShieldCheck, Lock, CheckCircle2 } from "lucide-react";

export default function PrivacyPage() {
  return (
    <div className="min-h-screen flex flex-col bg-slate-50 dark:bg-navy-950 text-slate-900 dark:text-white">
      <PublicNav />

      <section className="pt-12 pb-14 border-b border-slate-200 dark:border-navy-800 bg-white dark:bg-navy-900 text-center">
        <div className="max-w-4xl mx-auto px-4 space-y-4">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">
            <Lock className="h-3.5 w-3.5" />
            <span>Zero Model Training Pledge</span>
          </div>
          <h1 className="text-4xl font-extrabold tracking-tight">Privacy Policy & Data Protection</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 max-w-xl mx-auto">
            Last Updated: November 3, 2026 &bull; Compliant with Indian DPDP Act 2023
          </p>
        </div>
      </section>

      <section className="py-16 max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 space-y-10 text-xs leading-relaxed text-slate-700 dark:text-slate-300">
        <div className="p-6 rounded-2xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 space-y-2">
          <h3 className="text-sm font-bold text-emerald-900 dark:text-emerald-200 flex items-center gap-2">
            <ShieldCheck className="h-5 w-5 text-emerald-600" />
            Our Core Financial Privacy Commitment
          </h3>
          <p className="text-emerald-800 dark:text-emerald-300">
            DocuMind AI never sells, shares, or utilizes customer invoice data, financial statements, or tax identifiers to train or fine-tune public foundation AI models. Your business data remains strictly isolated within your organization boundary.
          </p>
        </div>

        <div className="space-y-4">
          <h2 className="text-xl font-bold text-slate-900 dark:text-white">1. Information We Collect</h2>
          <p>
            When utilizing DocuMind AI, we collect only the information necessary to provide automated document intelligence:
          </p>
          <ul className="list-disc pl-5 space-y-1.5 text-slate-600 dark:text-slate-300">
            <li><strong>Account & Registration Details:</strong> Full name, professional email address, organization name, and role.</li>
            <li><strong>Business Identity:</strong> Legal company name, registered address, Indian GSTIN, PAN, and contact phone.</li>
            <li><strong>Ingested Document Data:</strong> Supplier invoices, receipts, and challans uploaded by authorized members of your organization.</li>
            <li><strong>System Audit Logs:</strong> Cryptographic SHA-256 document hashes, timestamps, and reviewer approval actions for compliance.</li>
          </ul>
        </div>

        <div className="space-y-4">
          <h2 className="text-xl font-bold text-slate-900 dark:text-white">2. AI Processing Architecture & BYOK</h2>
          <p>
            Document text is processed via stateful LangGraph workflows utilizing Google Gemini and Groq Cloud LPU APIs.
          </p>
          <ul className="list-disc pl-5 space-y-1.5 text-slate-600 dark:text-slate-300">
            <li><strong>Ephemeral Inference:</strong> Text payloads are submitted to LLM APIs under enterprise zero-data-retention agreements where API inputs and outputs are not retained for model training.</li>
            <li><strong>Bring-Your-Own-Key (BYOK):</strong> Organizations may supply their own Gemini or Groq API credentials, establishing direct legal privity between their enterprise and the AI provider.</li>
            <li><strong>Local Deterministic Fallback:</strong> If an organization enables privacy mode, document classification and validation execute entirely on local CPU engines with zero external network transmission.</li>
          </ul>
        </div>

        <div className="space-y-4">
          <h2 className="text-xl font-bold text-slate-900 dark:text-white">3. Multi-Tenant Data Isolation</h2>
          <p>
            DocuMind AI enforces complete tenant boundary segregation at the relational database layer. Every table carries an indexed <code>organization_id</code> foreign key. Queries are scoped strictly to the authenticated tenant. Users from one organization cannot access, query, or enumerate documents from another organization.
          </p>
        </div>

        <div className="space-y-4">
          <h2 className="text-xl font-bold text-slate-900 dark:text-white">4. Compliance with Indian DPDP Act 2023</h2>
          <p>
            In accordance with the Digital Personal Data Protection Act 2023:
          </p>
          <ul className="list-disc pl-5 space-y-1.5 text-slate-600 dark:text-slate-300">
            <li><strong>Consent Architecture:</strong> Customers provide affirmative consent prior to processing financial documents during the pilot and production phases.</li>
            <li><strong>Right to Erasure:</strong> Organizations have the unilateral right to delete any uploaded document, invoice ledger, or user account permanently from our databases and storage volumes.</li>
            <li><strong>Data Localization:</strong> Our managed cloud instances operate exclusively within secure data center zones inside the Republic of India.</li>
          </ul>
        </div>

        <div className="space-y-4">
          <h2 className="text-xl font-bold text-slate-900 dark:text-white">5. Contact Our Data Protection Officer</h2>
          <p>
            For questions regarding our privacy architecture, SOC2 compliance roadmaps, or to exercise data rights, contact our Data Protection Officer at: <a href="mailto:privacy@documind.ai" className="text-blue-600 underline">privacy@documind.ai</a>.
          </p>
        </div>
      </section>

      <PublicFooter />
    </div>
  );
}

