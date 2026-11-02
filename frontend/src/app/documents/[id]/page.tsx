"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  FileText,
  ArrowLeft,
  CheckCircle2,
  AlertTriangle,
  CopyCheck,
  Cpu,
  Layers,
  Edit3,
  Save,
  Download,
  RotateCcw,
  Check,
  X,
  FileCheck2,
  Calendar,
  Building2,
  ExternalLink,
  ShieldCheck,
  RefreshCw,
} from "lucide-react";
import { api } from "@/lib/api-client";
import { formatCurrency, formatDate } from "@/lib/utils";
import { DocumentDetail, Invoice, ValidationResult, DuplicateMatch, AnomalyFinding } from "@/types";

export default function DocumentDetailPage() {
  const params = useParams();
  const router = useRouter();
  const documentId = params.id as string;

  const [doc, setDoc] = useState<DocumentDetail | null>(null);
  const [activeTab, setActiveTab] = useState<"fields" | "lines" | "tax" | "validation" | "duplicates" | "agents">("fields");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [selectedPage, setSelectedPage] = useState(1);
  const [editMode, setEditMode] = useState(false);

  // Editable Form State
  const [invoiceNumber, setInvoiceNumber] = useState("");
  const [invoiceDate, setInvoiceDate] = useState("");
  const [supplierName, setSupplierName] = useState("");
  const [supplierGstin, setSupplierGstin] = useState("");
  const [subtotal, setSubtotal] = useState<number>(0);
  const [totalTax, setTotalTax] = useState<number>(0);
  const [grandTotal, setGrandTotal] = useState<number>(0);

  const fetchDocument = async () => {
    setLoading(true);
    try {
      const data = await api.get<DocumentDetail>(`/documents/${documentId}`);
      setDoc(data);

      if (data.invoice) {
        setInvoiceNumber(data.invoice.invoice_number || "");
        setInvoiceDate(data.invoice.invoice_date || "");
        setSupplierName(data.invoice.supplier_name_raw || "");
        setSupplierGstin(data.invoice.supplier_gstin_raw || "");
        setSubtotal(data.invoice.subtotal || 0);
        setTotalTax(data.invoice.total_tax || 0);
        setGrandTotal(data.invoice.grand_total || 0);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocument();
  }, [documentId]);

  const handleSaveInvoiceEdits = async () => {
    if (!doc?.invoice) return;
    setSaving(true);
    try {
      await api.patch(`/invoices/${doc.invoice.id}`, {
        invoice_number: invoiceNumber,
        invoice_date: invoiceDate,
        supplier_name_raw: supplierName,
        supplier_gstin_raw: supplierGstin,
        subtotal,
        total_tax: totalTax,
        grand_total: grandTotal,
      });
      setEditMode(false);
      await fetchDocument();
    } catch (err: any) {
      alert(err.message || "Failed to save edits");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-96 text-slate-400 gap-3">
        <RefreshCw className="h-8 w-8 animate-spin text-blue-600" />
        <p className="text-sm font-medium">Loading document intelligence dossier...</p>
      </div>
    );
  }

  if (!doc) {
    return (
      <div className="p-8 text-center text-slate-500">
        <p className="font-semibold">Document not found</p>
        <Link href="/documents" className="text-blue-600 text-xs mt-2 inline-block hover:underline">
          Return to Documents Repository
        </Link>
      </div>
    );
  }

  const invoice = doc.invoice;
  const validation = doc.validations?.[0];
  const currentPageText = doc.pages?.find((p) => p.page_number === selectedPage)?.extracted_text || "No text extracted for this page.";

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Top Bar with Navigation & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200/80 pb-4">
        <div className="flex items-center gap-3">
          <button
            onClick={() => router.back()}
            className="p-2 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-600 shadow-sm"
          >
            <ArrowLeft className="h-4 w-4" />
          </button>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold text-navy-900 tracking-tight">{doc.file_name}</h1>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-blue-100 text-blue-800">
                {doc.document_type}
              </span>
              <span
                className={`px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                  doc.status === "APPROVED"
                    ? "bg-emerald-100 text-emerald-800"
                    : doc.status === "NEEDS_REVIEW"
                    ? "bg-amber-100 text-amber-800"
                    : "bg-slate-100 text-slate-700"
                }`}
              >
                {doc.status}
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5 font-mono">
              Document ID: {doc.id} • SHA-256: {doc.file_hash_sha256?.substring(0, 16)}...
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <a
            href={`/api/v1/documents/${doc.id}/download`}
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 bg-white text-xs font-medium text-slate-700 hover:bg-slate-50 shadow-sm"
          >
            <Download className="h-3.5 w-3.5" />
            Download Original
          </a>
          {doc.status === "NEEDS_REVIEW" && (
            <Link
              href="/approvals"
              className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-emerald-600 text-white text-xs font-semibold hover:bg-emerald-500 shadow-sm"
            >
              <Check className="h-3.5 w-3.5" />
              Approve / Reject in Queue
            </Link>
          )}
        </div>
      </div>

      {/* Main Two-Column View */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Original Document / OCR Viewer (5 Columns) */}
        <div className="lg:col-span-5 bg-white rounded-xl border border-slate-200/80 shadow-sm p-4 flex flex-col h-[750px]">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100 text-xs">
            <span className="font-bold text-slate-800 flex items-center gap-1.5">
              <FileText className="h-4 w-4 text-blue-600" />
              Document Text & Layout
            </span>
            {/* Page Selector */}
            {doc.pages && doc.pages.length > 1 && (
              <div className="flex items-center gap-1">
                {doc.pages.map((p) => (
                  <button
                    key={p.page_number}
                    onClick={() => setSelectedPage(p.page_number)}
                    className={`px-2 py-0.5 rounded text-[11px] font-semibold ${
                      selectedPage === p.page_number
                        ? "bg-blue-600 text-white"
                        : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                    }`}
                  >
                    P{p.page_number}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* OCR Content Box */}
          <div className="flex-1 overflow-y-auto mt-3 p-4 rounded-lg bg-slate-900 text-slate-200 font-mono text-xs leading-relaxed whitespace-pre-wrap select-text">
            {currentPageText}
          </div>

          <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-400">
            <span>OCR Engine: {doc.pages?.[0]?.ocr_engine || "PyMuPDF"}</span>
            <span>Total Pages: {doc.pages?.length || 1}</span>
          </div>
        </div>

        {/* Right Column: Tabbed Data & Intelligence Suite (7 Columns) */}
        <div className="lg:col-span-7 bg-white rounded-xl border border-slate-200/80 shadow-sm flex flex-col h-[750px] overflow-hidden">
          {/* Navigation Tabs Header */}
          <div className="flex border-b border-slate-200 bg-slate-50/70 px-4 pt-2 overflow-x-auto text-xs shrink-0">
            <button
              onClick={() => setActiveTab("fields")}
              className={`px-4 py-2.5 font-semibold border-b-2 transition-colors whitespace-nowrap ${
                activeTab === "fields"
                  ? "border-blue-600 text-blue-600 bg-white rounded-t-lg"
                  : "border-transparent text-slate-500 hover:text-slate-800"
              }`}
            >
              Extracted Fields
            </button>
            <button
              onClick={() => setActiveTab("lines")}
              className={`px-4 py-2.5 font-semibold border-b-2 transition-colors whitespace-nowrap ${
                activeTab === "lines"
                  ? "border-blue-600 text-blue-600 bg-white rounded-t-lg"
                  : "border-transparent text-slate-500 hover:text-slate-800"
              }`}
            >
              Line Items ({invoice?.line_items?.length || 0})
            </button>
            <button
              onClick={() => setActiveTab("tax")}
              className={`px-4 py-2.5 font-semibold border-b-2 transition-colors whitespace-nowrap ${
                activeTab === "tax"
                  ? "border-blue-600 text-blue-600 bg-white rounded-t-lg"
                  : "border-transparent text-slate-500 hover:text-slate-800"
              }`}
            >
              Tax Reconciliation
            </button>
            <button
              onClick={() => setActiveTab("validation")}
              className={`px-4 py-2.5 font-semibold border-b-2 transition-colors whitespace-nowrap flex items-center gap-1.5 ${
                activeTab === "validation"
                  ? "border-blue-600 text-blue-600 bg-white rounded-t-lg"
                  : "border-transparent text-slate-500 hover:text-slate-800"
              }`}
            >
              Validations
              {validation?.errors?.length ? (
                <span className="h-4 w-4 rounded-full bg-rose-500 text-white text-[9px] flex items-center justify-center font-bold">
                  {validation.errors.length}
                </span>
              ) : null}
            </button>
            <button
              onClick={() => setActiveTab("duplicates")}
              className={`px-4 py-2.5 font-semibold border-b-2 transition-colors whitespace-nowrap flex items-center gap-1.5 ${
                activeTab === "duplicates"
                  ? "border-blue-600 text-blue-600 bg-white rounded-t-lg"
                  : "border-transparent text-slate-500 hover:text-slate-800"
              }`}
            >
              Duplicates & Anomalies
              {(doc.duplicates?.length || 0) + (doc.anomalies?.length || 0) > 0 && (
                <span className="h-4 w-4 rounded-full bg-amber-500 text-white text-[9px] flex items-center justify-center font-bold">
                  {(doc.duplicates?.length || 0) + (doc.anomalies?.length || 0)}
                </span>
              )}
            </button>
            <button
              onClick={() => setActiveTab("agents")}
              className={`px-4 py-2.5 font-semibold border-b-2 transition-colors whitespace-nowrap ${
                activeTab === "agents"
                  ? "border-blue-600 text-blue-600 bg-white rounded-t-lg"
                  : "border-transparent text-slate-500 hover:text-slate-800"
              }`}
            >
              Agent Execution Traces
            </button>
          </div>

          {/* Tab Body */}
          <div className="p-6 flex-1 overflow-y-auto">
            {/* TAB 1: Extracted Fields */}
            {activeTab === "fields" && (
              <div className="space-y-6">
                <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                  <div>
                    <h2 className="text-sm font-bold text-navy-900">Extracted Commercial Entities</h2>
                    <p className="text-xs text-slate-400">Structured data extracted with confidence scores</p>
                  </div>
                  {invoice && !editMode ? (
                    <button
                      onClick={() => setEditMode(true)}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 text-slate-700 hover:bg-slate-50 text-xs font-semibold"
                    >
                      <Edit3 className="h-3.5 w-3.5 text-blue-600" />
                      Correct Values
                    </button>
                  ) : editMode ? (
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => setEditMode(false)}
                        className="px-3 py-1.5 rounded-lg text-slate-500 hover:bg-slate-100 text-xs font-semibold"
                      >
                        Cancel
                      </button>
                      <button
                        onClick={handleSaveInvoiceEdits}
                        disabled={saving}
                        className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold"
                      >
                        <Save className="h-3.5 w-3.5" />
                        {saving ? "Revalidating..." : "Save & Revalidate"}
                      </button>
                    </div>
                  ) : null}
                </div>

                {editMode ? (
                  /* Editable Mode Form */
                  <div className="space-y-4 text-xs">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="font-semibold text-slate-700 block mb-1">Invoice Number</label>
                        <input
                          type="text"
                          value={invoiceNumber}
                          onChange={(e) => setInvoiceNumber(e.target.value)}
                          className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs"
                        />
                      </div>
                      <div>
                        <label className="font-semibold text-slate-700 block mb-1">Invoice Date (YYYY-MM-DD)</label>
                        <input
                          type="date"
                          value={invoiceDate}
                          onChange={(e) => setInvoiceDate(e.target.value)}
                          className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs"
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="font-semibold text-slate-700 block mb-1">Supplier / Vendor Name</label>
                        <input
                          type="text"
                          value={supplierName}
                          onChange={(e) => setSupplierName(e.target.value)}
                          className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs"
                        />
                      </div>
                      <div>
                        <label className="font-semibold text-slate-700 block mb-1">Supplier GSTIN</label>
                        <input
                          type="text"
                          value={supplierGstin}
                          onChange={(e) => setSupplierGstin(e.target.value)}
                          className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs font-mono"
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-3 gap-3">
                      <div>
                        <label className="font-semibold text-slate-700 block mb-1">Subtotal (₹)</label>
                        <input
                          type="number"
                          step="0.01"
                          value={subtotal}
                          onChange={(e) => setSubtotal(Number(e.target.value))}
                          className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs"
                        />
                      </div>
                      <div>
                        <label className="font-semibold text-slate-700 block mb-1">Total Tax (₹)</label>
                        <input
                          type="number"
                          step="0.01"
                          value={totalTax}
                          onChange={(e) => setTotalTax(Number(e.target.value))}
                          className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs"
                        />
                      </div>
                      <div>
                        <label className="font-semibold text-slate-700 block mb-1">Grand Total (₹)</label>
                        <input
                          type="number"
                          step="0.01"
                          value={grandTotal}
                          onChange={(e) => setGrandTotal(Number(e.target.value))}
                          className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs font-bold"
                        />
                      </div>
                    </div>
                  </div>
                ) : (
                  /* Read Only Display Grid */
                  <div className="grid grid-cols-2 gap-4 text-xs">
                    <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200/80">
                      <span className="text-slate-400 font-medium">Invoice Number</span>
                      <p className="text-sm font-bold text-navy-900 mt-1 font-mono">
                        {invoice?.invoice_number || "—"}
                      </p>
                    </div>

                    <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200/80">
                      <span className="text-slate-400 font-medium">Invoice Date</span>
                      <p className="text-sm font-bold text-navy-900 mt-1">
                        {formatDate(invoice?.invoice_date)}
                      </p>
                    </div>

                    <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200/80">
                      <span className="text-slate-400 font-medium">Supplier Name</span>
                      <p className="text-sm font-bold text-navy-900 mt-1">
                        {invoice?.supplier_name_raw || "—"}
                      </p>
                    </div>

                    <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200/80">
                      <span className="text-slate-400 font-medium">Supplier GSTIN</span>
                      <p className="text-sm font-bold text-navy-900 mt-1 font-mono">
                        {invoice?.supplier_gstin_raw || "—"}
                      </p>
                    </div>

                    <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200/80">
                      <span className="text-slate-400 font-medium">Customer (Billed To)</span>
                      <p className="text-sm font-bold text-navy-900 mt-1">
                        {invoice?.customer_name_raw || "—"}
                      </p>
                    </div>

                    <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200/80">
                      <span className="text-slate-400 font-medium">Grand Total</span>
                      <p className="text-sm font-bold text-emerald-700 mt-1">
                        {invoice?.grand_total ? formatCurrency(invoice.grand_total, invoice.currency) : "—"}
                      </p>
                    </div>
                  </div>
                )}

                {/* Extracted Fields Table */}
                <div className="pt-4 border-t border-slate-100">
                  <h3 className="text-xs font-bold text-navy-900 mb-2 uppercase tracking-wider text-slate-500">
                    Field-Level Confidence & Evidence
                  </h3>
                  <div className="space-y-1.5">
                    {doc.extracted_fields?.map((f) => (
                      <div
                        key={f.id}
                        className="flex items-center justify-between p-2 rounded bg-slate-50 text-xs border border-slate-100"
                      >
                        <span className="font-semibold text-slate-700">{f.field_name}</span>
                        <div className="flex items-center gap-3">
                          <span className="text-slate-900 font-mono">{f.field_value || "null"}</span>
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                              f.confidence >= 0.9
                                ? "bg-emerald-100 text-emerald-800"
                                : "bg-amber-100 text-amber-800"
                            }`}
                          >
                            {(f.confidence * 100).toFixed(0)}%
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* TAB 2: Line Items */}
            {activeTab === "lines" && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h2 className="text-sm font-bold text-navy-900">Extracted Line Items</h2>
                  <span className="text-xs text-slate-500">
                    {invoice?.line_items?.length || 0} items identified
                  </span>
                </div>

                <div className="overflow-x-auto border border-slate-200 rounded-lg">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold text-[11px]">
                      <tr>
                        <th className="p-2.5">#</th>
                        <th className="p-2.5">Description</th>
                        <th className="p-2.5">HSN/SAC</th>
                        <th className="p-2.5 text-right">Qty</th>
                        <th className="p-2.5 text-right">Unit Price</th>
                        <th className="p-2.5 text-right">Tax Rate</th>
                        <th className="p-2.5 text-right">Line Total</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {invoice?.line_items?.map((item) => (
                        <tr key={item.id || item.line_number} className="hover:bg-slate-50">
                          <td className="p-2.5 font-mono text-slate-500">{item.line_number}</td>
                          <td className="p-2.5 font-medium text-slate-800">{item.description}</td>
                          <td className="p-2.5 font-mono text-slate-600">{item.hsn_sac || "—"}</td>
                          <td className="p-2.5 text-right font-mono">{Number(item.quantity).toFixed(1)}</td>
                          <td className="p-2.5 text-right font-mono">{formatCurrency(item.unit_price)}</td>
                          <td className="p-2.5 text-right font-mono">{Number(item.tax_rate).toFixed(0)}%</td>
                          <td className="p-2.5 text-right font-bold text-slate-900 font-mono">
                            {formatCurrency(item.line_total)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* TAB 3: Tax Reconciliation */}
            {activeTab === "tax" && (
              <div className="space-y-4">
                <div>
                  <h2 className="text-sm font-bold text-navy-900">Tax Breakdown & Arithmetic Audit</h2>
                  <p className="text-xs text-slate-400">Strict decimal verification of CGST, SGST, IGST totals</p>
                </div>

                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3 text-xs">
                  <div className="flex justify-between py-1">
                    <span className="text-slate-600">Taxable Subtotal</span>
                    <span className="font-mono font-semibold text-slate-800">
                      {formatCurrency(invoice?.taxable_amount)}
                    </span>
                  </div>
                  <div className="flex justify-between py-1">
                    <span className="text-slate-600">Central GST (CGST)</span>
                    <span className="font-mono text-slate-800">{formatCurrency(invoice?.cgst)}</span>
                  </div>
                  <div className="flex justify-between py-1">
                    <span className="text-slate-600">State GST (SGST)</span>
                    <span className="font-mono text-slate-800">{formatCurrency(invoice?.sgst)}</span>
                  </div>
                  <div className="flex justify-between py-1">
                    <span className="text-slate-600">Integrated GST (IGST)</span>
                    <span className="font-mono text-slate-800">{formatCurrency(invoice?.igst)}</span>
                  </div>
                  <div className="flex justify-between py-1.5 border-t border-slate-200">
                    <span className="font-semibold text-slate-700">Total Tax Calculated</span>
                    <span className="font-mono font-bold text-slate-900">{formatCurrency(invoice?.total_tax)}</span>
                  </div>
                  <div className="flex justify-between py-2 border-t border-slate-200 text-sm">
                    <span className="font-bold text-navy-900">Reconciled Grand Total</span>
                    <span className="font-mono font-bold text-emerald-700">
                      {formatCurrency(invoice?.grand_total)}
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* TAB 4: Validations */}
            {activeTab === "validation" && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-sm font-bold text-navy-900">Deterministic Validation Engine</h2>
                    <p className="text-xs text-slate-400">Mathematical rules & GST compliance verification</p>
                  </div>
                  <span
                    className={`px-2.5 py-1 rounded-full text-xs font-bold ${
                      validation?.status === "PASSED"
                        ? "bg-emerald-100 text-emerald-800"
                        : validation?.status === "WARNING"
                        ? "bg-amber-100 text-amber-800"
                        : "bg-rose-100 text-rose-800"
                    }`}
                  >
                    {validation?.status || "UNKNOWN"}
                  </span>
                </div>

                {/* Errors */}
                {validation?.errors && validation.errors.length > 0 && (
                  <div className="space-y-2">
                    <p className="text-xs font-bold text-rose-700 uppercase">Validation Errors ({validation.errors.length})</p>
                    {validation.errors.map((err, i) => (
                      <div key={i} className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-xs text-rose-800">
                        <span className="font-bold">{err.field}:</span> {err.message}
                      </div>
                    ))}
                  </div>
                )}

                {/* Warnings */}
                {validation?.warnings && validation.warnings.length > 0 && (
                  <div className="space-y-2">
                    <p className="text-xs font-bold text-amber-700 uppercase">Validation Warnings ({validation.warnings.length})</p>
                    {validation.warnings.map((w, i) => (
                      <div key={i} className="p-3 rounded-lg bg-amber-50 border border-amber-200 text-xs text-amber-800">
                        <span className="font-bold">{w.field}:</span> {w.message}
                      </div>
                    ))}
                  </div>
                )}

                {/* Explanations */}
                <div className="pt-2 border-t border-slate-100">
                  <p className="text-xs font-bold text-slate-700 uppercase mb-2">Field Reconciliation Explanations</p>
                  <div className="space-y-1.5 text-xs text-slate-600">
                    {validation?.field_explanations &&
                      Object.entries(validation.field_explanations).map(([k, v]) => (
                        <div key={k} className="p-2 rounded bg-slate-50 border border-slate-100">
                          <span className="font-semibold text-slate-800">{k}:</span> {String(v)}
                        </div>
                      ))}
                  </div>
                </div>
              </div>
            )}

            {/* TAB 5: Duplicates & Anomalies */}
            {activeTab === "duplicates" && (
              <div className="space-y-6">
                <div>
                  <h2 className="text-sm font-bold text-navy-900">Duplicate Matching & Anomaly Detection</h2>
                  <p className="text-xs text-slate-400">Cryptographic hashes and statistical anomaly findings</p>
                </div>

                {/* Duplicates */}
                <div>
                  <h3 className="text-xs font-bold text-slate-700 uppercase mb-2">Duplicate Matches Detected</h3>
                  {doc.duplicates && doc.duplicates.length > 0 ? (
                    <div className="space-y-2">
                      {doc.duplicates.map((m) => (
                        <div key={m.id} className="p-3 rounded-lg bg-amber-50 border border-amber-200 text-xs">
                          <div className="flex items-center justify-between font-bold text-amber-900">
                            <span>Match Type: {m.match_type}</span>
                            <span>Score: {(m.match_score * 100).toFixed(0)}%</span>
                          </div>
                          <p className="text-amber-800 mt-1">{m.match_details?.reason || "Duplicate detected"}</p>
                          <Link
                            href={`/documents/${m.matched_document_id}`}
                            className="text-[11px] text-blue-600 hover:underline mt-1 inline-flex items-center gap-1 font-semibold"
                          >
                            View Conflicting Document <ExternalLink className="h-3 w-3" />
                          </Link>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-emerald-600 bg-emerald-50 p-3 rounded-lg border border-emerald-200">
                      ✓ No duplicate invoices or cryptographic hash collisions detected.
                    </p>
                  )}
                </div>

                {/* Anomalies */}
                <div>
                  <h3 className="text-xs font-bold text-slate-700 uppercase mb-2">Statistical Anomalies</h3>
                  {doc.anomalies && doc.anomalies.length > 0 ? (
                    <div className="space-y-2">
                      {doc.anomalies.map((a) => (
                        <div key={a.id} className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-xs">
                          <div className="flex items-center justify-between font-bold text-rose-900">
                            <span>{a.anomaly_type}</span>
                            <span className="px-2 py-0.5 rounded bg-rose-200 text-rose-900 text-[10px]">
                              {a.severity}
                            </span>
                          </div>
                          <p className="text-rose-800 mt-1">{a.description}</p>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-emerald-600 bg-emerald-50 p-3 rounded-lg border border-emerald-200">
                      ✓ No statistical deviations or tax slab anomalies detected.
                    </p>
                  )}
                </div>
              </div>
            )}

            {/* TAB 6: Agents Timeline */}
            {activeTab === "agents" && (
              <div className="space-y-4">
                <div>
                  <h2 className="text-sm font-bold text-navy-900">Multi-Agent Execution Timeline</h2>
                  <p className="text-xs text-slate-400">Step-by-step trace of LangGraph node execution</p>
                </div>

                <div className="space-y-3">
                  {doc.agent_executions?.map((exec) => (
                    <div key={exec.id} className="p-3.5 rounded-lg bg-slate-50 border border-slate-200 text-xs">
                      <div className="flex items-center justify-between font-bold text-navy-900">
                        <span className="flex items-center gap-2">
                          <Cpu className="h-4 w-4 text-blue-600" />
                          {exec.agent_name}
                        </span>
                        <span className="px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 text-[10px]">
                          {exec.status}
                        </span>
                      </div>
                      <div className="grid grid-cols-3 gap-2 mt-2 pt-2 border-t border-slate-200/80 text-[11px] text-slate-500 font-mono">
                        <span>Latency: {exec.latency_ms} ms</span>
                        <span>Tokens: {exec.tokens_used}</span>
                        <span>Cost: ${Number(exec.cost_usd).toFixed(6)}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

