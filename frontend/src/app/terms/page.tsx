import { PublicNav } from "@/components/layout/PublicNav";
import { PublicFooter } from "@/components/layout/PublicFooter";

export default function TermsPage() {
  return (
    <div className="min-h-screen flex flex-col bg-slate-50 dark:bg-navy-950 text-slate-900 dark:text-white">
      <PublicNav />

      <section className="pt-12 pb-14 border-b border-slate-200 dark:border-navy-800 bg-white dark:bg-navy-900 text-center">
        <div className="max-w-4xl mx-auto px-4 space-y-4">
          <span className="text-xs font-bold uppercase tracking-wider text-blue-600 dark:text-blue-400">
            Commercial Agreement
          </span>
          <h1 className="text-4xl font-extrabold tracking-tight">Commercial Terms of Service</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 max-w-xl mx-auto">
            Effective Date: November 3, 2026 &bull; DocuMind AI Commercial SaaS & Pilot Program
          </p>
        </div>
      </section>

      <section className="py-16 max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 space-y-10 text-xs leading-relaxed text-slate-700 dark:text-slate-300">
        <div className="space-y-4">
          <h2 className="text-xl font-bold text-slate-900 dark:text-white">1. Agreement to Terms</h2>
          <p>
            By registering an account, initiating a pilot evaluation, or uploading business documents to DocuMind AI, your enterprise agrees to be legally bound by these Commercial Terms of Service. If you are entering into this agreement on behalf of a company, you represent that you possess the authority to bind such legal entity.
          </p>
        </div>

        <div className="space-y-4">
          <h2 className="text-xl font-bold text-slate-900 dark:text-white">2. Controlled Customer Pilot Program Provisions</h2>
          <p>
            Participating pilot organizations agree to the following terms during the evaluation phase:
          </p>
          <ul className="list-disc pl-5 space-y-1.5 text-slate-600 dark:text-slate-300">
            <li><strong>Evaluation License:</strong> DocuMind AI grants a non-exclusive, non-transferable right to ingest and evaluate business documents across the 14-day pilot window.</li>
            <li><strong>Customer Data Ownership:</strong> The customer retains complete and unencumbered ownership of all uploaded invoice files, vendor master records, and generated Excel accounting reports.</li>
            <li><strong>Consent for Processing:</strong> By uploading documents, the pilot customer grants DocuMind AI permission to perform OCR, layout parsing, tax math validation, and anomaly checks solely to provide the contracted intelligence service.</li>
            <li><strong>Accuracy Baseline Understanding:</strong> While DocuMind AI achieves high laboratory accuracy on standard benchmarks, real-world customer pilot accuracy depends on layout quality and document resolution. Customer agrees to utilize the Human-in-the-Loop review center for all ambiguous financial entries.</li>
          </ul>
        </div>

        <div className="space-y-4">
          <h2 className="text-xl font-bold text-slate-900 dark:text-white">3. Commercial Subscriptions & Quota Gating</h2>
          <p>
            Commercial plans (STARTER, PROFESSIONAL, ENTERPRISE) are billed in Indian Rupees (INR) + applicable Goods & Services Tax (18% GST).
          </p>
          <ul className="list-disc pl-5 space-y-1.5 text-slate-600 dark:text-slate-300">
            <li><strong>Usage Quotas:</strong> Each tier provides a designated monthly document quota (e.g. 50, 500, or 5,000 documents). Upon quota exhaustion, processing is safely held (HTTP 402) until plan upgrade or monthly billing rollover.</li>
            <li><strong>Payment Gateway:</strong> Commercial transactions are processed via authorized payment aggregators (e.g. Razorpay). Real payment integrations remain in sandbox verification mode until authorized by customer contract.</li>
          </ul>
        </div>

        <div className="space-y-4">
          <h2 className="text-xl font-bold text-slate-900 dark:text-white">4. Professional Accounting Disclaimer</h2>
          <p>
            DocuMind AI provides automated data extraction, GST mathematical verification, and fraud anomaly detection as decision-support software. It does not replace certified tax practitioners, chartered accountants, or statutory auditors. The ultimate legal responsibility for tax filings submitted to the Goods and Services Tax Network (GSTN) remains with the taxpayer enterprise.
          </p>
        </div>

        <div className="space-y-4">
          <h2 className="text-xl font-bold text-slate-900 dark:text-white">5. Governing Law & Dispute Resolution</h2>
          <p>
            These Terms shall be governed by and construed in accordance with the substantive laws of India. Any legal action or dispute arising hereunder shall be subject to the exclusive jurisdiction of the competent courts in Bengaluru, Karnataka, India.
          </p>
        </div>
      </section>

      <PublicFooter />
    </div>
  );
}

