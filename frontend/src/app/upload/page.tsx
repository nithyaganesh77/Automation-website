"use client";

import { useState, useRef } from "react";
import { useRouter } from "next/navigation";
import {
  UploadCloud,
  FileText,
  CheckCircle2,
  AlertCircle,
  X,
  ArrowRight,
  ShieldCheck,
  FileCheck,
  RefreshCw,
} from "lucide-react";
import { api } from "@/lib/api-client";
import { DocumentDetail } from "@/types";

const ALLOWED_EXTS = ["pdf", "png", "jpg", "jpeg", "docx", "xlsx"];

export default function UploadPage() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [processedDocs, setProcessedDocs] = useState<DocumentDetail[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [consentAgreed, setConsentAgreed] = useState(false);

  const handleFiles = (files: FileList | null) => {
    if (!files) return;
    setError(null);
    const newFiles: File[] = [];

    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      const ext = file.name.split(".").pop()?.toLowerCase() || "";
      if (!ALLOWED_EXTS.includes(ext)) {
        setError(`File '${file.name}' has an unsupported extension. Allowed: PDF, PNG, JPG, DOCX, XLSX.`);
        return;
      }
      if (file.size > 25 * 1024 * 1024) {
        setError(`File '${file.name}' exceeds the 25MB maximum limit.`);
        return;
      }
      newFiles.push(file);
    }
    setSelectedFiles((prev) => [...prev, ...newFiles]);
  };

  const removeFile = (index: number) => {
    setSelectedFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleUploadSubmit = async () => {
    if (selectedFiles.length === 0) return;
    if (!consentAgreed) {
      setError("Document upload requires explicit customer consent.");
      return;
    }
    setUploading(true);
    setError(null);
    setUploadProgress(20);

    const uploadedResults: DocumentDetail[] = [];

    try {
      for (let i = 0; i < selectedFiles.length; i++) {
        const file = selectedFiles[i];
        const formData = new FormData();
        formData.append("file", file);
        formData.append("customer_consent", "true");

        setUploadProgress(Math.round(((i + 0.5) / selectedFiles.length) * 100));
        const res = await api.post<DocumentDetail>("/documents/upload", formData);
        uploadedResults.push(res);
        setUploadProgress(Math.round(((i + 1) / selectedFiles.length) * 100));
      }

      setProcessedDocs(uploadedResults);
      setSelectedFiles([]);
    } catch (err: any) {
      setError(err.message || "Failed to process documents through AI pipeline");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-navy-900 tracking-tight">Document Ingestion & Multi-Agent Intake</h1>
        <p className="text-sm text-slate-500 mt-1">
          Upload commercial invoices, POs, delivery challans, or receipts for OCR extraction and financial validation.
        </p>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center gap-3">
          <AlertCircle className="h-4 w-4 shrink-0 text-rose-500" />
          <span>{error}</span>
        </div>
      )}

      {/* Drag & Drop Zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
        onDragLeave={() => setDragActive(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragActive(false);
          handleFiles(e.dataTransfer.files);
        }}
        onClick={() => fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-2xl p-10 text-center cursor-pointer transition-all ${
          dragActive
            ? "border-blue-500 bg-blue-50/50 scale-[0.99]"
            : "border-slate-300 bg-white hover:border-slate-400 hover:bg-slate-50/50"
        }`}
      >
        <input
          type="file"
          ref={fileInputRef}
          multiple
          accept=".pdf,.png,.jpg,.jpeg,.docx,.xlsx"
          className="hidden"
          onChange={(e) => handleFiles(e.target.files)}
        />
        <div className="h-16 w-16 mx-auto rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center mb-4 border border-blue-100">
          <UploadCloud className="h-8 w-8" />
        </div>
        <p className="text-base font-semibold text-navy-900">
          Click to upload or drag & drop business documents
        </p>
        <p className="text-xs text-slate-400 mt-1">
          Supported Formats: PDF, PNG, JPG, JPEG, Word (.docx), Excel (.xlsx) • Up to 25MB each
        </p>
      </div>

      {/* Selected Files Staging List */}
      {selectedFiles.length > 0 && (
        <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold text-navy-900">
              Files Staged for Processing ({selectedFiles.length})
            </h2>
            <button
              onClick={() => setSelectedFiles([])}
              className="text-xs text-rose-600 hover:underline font-semibold"
            >
              Clear All
            </button>
          </div>

          <div className="space-y-2 max-h-60 overflow-y-auto">
            {selectedFiles.map((file, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between p-3 rounded-lg bg-slate-50 border border-slate-200 text-xs"
              >
                <div className="flex items-center gap-3">
                  <FileText className="h-4 w-4 text-blue-600 shrink-0" />
                  <div>
                    <p className="font-semibold text-slate-800">{file.name}</p>
                    <p className="text-[11px] text-slate-400">{(file.size / 1024).toFixed(1)} KB</p>
                  </div>
                </div>
                <button
                  onClick={(e) => { e.stopPropagation(); removeFile(idx); }}
                  className="text-slate-400 hover:text-rose-600 p-1"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>

          {/* Progress Bar when uploading */}
          {uploading && (
            <div className="space-y-2 pt-2">
              <div className="flex justify-between text-xs font-semibold text-slate-600">
                <span>Executing LangGraph Multi-Agent Pipeline...</span>
                <span>{uploadProgress}%</span>
              </div>
              <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
            </div>
          )}

          {/* Pilot Customer Consent Checkbox */}
          <div className="pt-2 border-t border-slate-100 dark:border-navy-800">
            <label className="flex items-start gap-2.5 text-xs text-slate-600 dark:text-slate-300 cursor-pointer">
              <input
                type="checkbox"
                checked={consentAgreed}
                onChange={(e) => setConsentAgreed(e.target.checked)}
                className="mt-0.5 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
              />
              <span>
                I confirm that our organization has authorized the ingestion of these business documents under the DocuMind AI pilot evaluation terms and explicitly consent to automated OCR extraction, deterministic GST reconciliation, multi-agent AI processing (including external LLM inference via Google Gemini and Groq APIs where active), and anomaly analysis under the Digital Personal Data Protection (DPDP) Act 2023.
              </span>
            </label>
          </div>

          <div className="flex justify-end pt-2">
            <button
              disabled={uploading || !consentAgreed}
              onClick={handleUploadSubmit}
              className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs shadow-md shadow-blue-600/30 transition-all disabled:opacity-50"
            >
              {uploading ? (
                <>
                  <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                  Processing Documents...
                </>
              ) : (
                <>
                  Launch Multi-Agent Intake ({selectedFiles.length})
                  <ArrowRight className="h-3.5 w-3.5" />
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {/* Processed Results Notification */}
      {processedDocs.length > 0 && (
        <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-6 space-y-4">
          <div className="flex items-center gap-2 text-emerald-800 font-bold text-sm">
            <CheckCircle2 className="h-5 w-5 text-emerald-600" />
            <span>Multi-Agent Ingestion Complete ({processedDocs.length} Documents)</span>
          </div>

          <div className="divide-y divide-emerald-100">
            {processedDocs.map((doc) => (
              <div key={doc.id} className="py-3 flex items-center justify-between text-xs">
                <div>
                  <p className="font-semibold text-slate-900">{doc.file_name}</p>
                  <div className="flex items-center gap-2 mt-0.5 text-slate-500">
                    <span className="font-medium text-slate-700">{doc.document_type}</span>
                    <span>•</span>
                    <span>Confidence: {(doc.confidence * 100).toFixed(0)}%</span>
                    <span>•</span>
                    <span className="px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-semibold">
                      {doc.status}
                    </span>
                  </div>
                </div>
                <button
                  onClick={() => router.push(`/documents/${doc.id}`)}
                  className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-semibold flex items-center gap-1 shadow-sm"
                >
                  View Extracted Details
                  <ArrowRight className="h-3 w-3" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Feature Capabilities Card */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-4">
        <div className="p-4 rounded-xl bg-white border border-slate-200/80 shadow-sm">
          <div className="h-8 w-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center mb-2.5">
            <ShieldCheck className="h-4 w-4" />
          </div>
          <h2 className="text-xs font-bold text-navy-900">Deterministic Checks</h2>
          <p className="text-[11px] text-slate-500 mt-1 leading-relaxed">
            Mathematical reconciliations for GST, line items, and totals run via strict decimal formulas.
          </p>
        </div>

        <div className="p-4 rounded-xl bg-white border border-slate-200/80 shadow-sm">
          <div className="h-8 w-8 rounded-lg bg-cyan-50 text-cyan-600 flex items-center justify-center mb-2.5">
            <FileCheck className="h-4 w-4" />
          </div>
          <h2 className="text-xs font-bold text-navy-900">Cryptographic Deduplication</h2>
          <p className="text-[11px] text-slate-500 mt-1 leading-relaxed">
            Exact SHA-256 hashes and fuzzy date/amount similarity checks prevent accidental double pay.
          </p>
        </div>

        <div className="p-4 rounded-xl bg-white border border-slate-200/80 shadow-sm">
          <div className="h-8 w-8 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center mb-2.5">
            <CheckCircle2 className="h-4 w-4" />
          </div>
          <h2 className="text-xs font-bold text-navy-900">Zero Silent Approvals</h2>
          <p className="text-[11px] text-slate-500 mt-1 leading-relaxed">
            Discrepancies automatically halt automated export and route to human reviewer verification.
          </p>
        </div>
      </div>
    </div>
  );
}

