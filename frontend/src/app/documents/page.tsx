"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  FileText,
  Search,
  Filter,
  Download,
  RotateCcw,
  Trash2,
  ExternalLink,
  RefreshCw,
  Eye,
  CheckCircle2,
  Clock,
  AlertTriangle,
  FileQuestion,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { api } from "@/lib/api-client";
import { formatCurrency, formatDate } from "@/lib/utils";
import { DocumentSummary, DocumentListResponse } from "@/types";

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(15);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);

  // Filters
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState("");

  const fetchDocuments = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.append("page", page.toString());
      params.append("page_size", pageSize.toString());
      if (search) params.append("search", search);
      if (statusFilter) params.append("status", statusFilter);
      if (typeFilter) params.append("document_type", typeFilter);

      const res = await api.get<DocumentListResponse>(`/documents?${params.toString()}`);
      setDocuments(res.items);
      setTotal(res.total);
      setTotalPages(res.total_pages);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, [page, statusFilter, typeFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchDocuments();
  };

  const handleReprocess = async (docId: string) => {
    try {
      await api.post(`/documents/${docId}/reprocess`);
      fetchDocuments();
    } catch (err) {
      alert("Failed to reprocess document");
    }
  };

  const handleDelete = async (docId: string) => {
    if (!confirm("Are you sure you want to delete this document and its associated records?")) return;
    try {
      await api.delete(`/documents/${docId}`);
      fetchDocuments();
    } catch (err) {
      alert("Failed to delete document");
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "APPROVED":
        return <span className="px-2.5 py-1 rounded-full text-[11px] font-semibold bg-emerald-100 text-emerald-800">Approved</span>;
      case "NEEDS_REVIEW":
        return <span className="px-2.5 py-1 rounded-full text-[11px] font-semibold bg-amber-100 text-amber-800">Needs Review</span>;
      case "PROCESSING":
        return <span className="px-2.5 py-1 rounded-full text-[11px] font-semibold bg-blue-100 text-blue-800 animate-pulse">Processing</span>;
      case "REJECTED":
        return <span className="px-2.5 py-1 rounded-full text-[11px] font-semibold bg-rose-100 text-rose-800">Rejected</span>;
      case "FAILED":
        return <span className="px-2.5 py-1 rounded-full text-[11px] font-semibold bg-rose-100 text-rose-800">Failed</span>;
      default:
        return <span className="px-2.5 py-1 rounded-full text-[11px] font-semibold bg-slate-100 text-slate-700">{status}</span>;
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-navy-900 tracking-tight">Document Repository</h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Enterprise database of ingested documents, extracted fields, and verification histories.
          </p>
        </div>
        <Link
          href="/upload"
          className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-sm transition-all text-center"
        >
          Upload New Document
        </Link>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-sm flex flex-col md:flex-row gap-3 items-center justify-between">
        <form onSubmit={handleSearchSubmit} className="relative w-full md:w-80">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search filename or ID..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-slate-50 border border-slate-200 rounded-lg pl-9 pr-4 py-2 text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:border-blue-500"
          />
        </form>

        <div className="flex items-center gap-2.5 w-full md:w-auto">
          {/* Status Filter */}
          <select
            value={statusFilter}
            onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
            className="bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs text-slate-700 focus:outline-none focus:border-blue-500"
          >
            <option value="">All Statuses</option>
            <option value="APPROVED">Approved</option>
            <option value="NEEDS_REVIEW">Needs Review</option>
            <option value="PROCESSING">Processing</option>
            <option value="FAILED">Failed</option>
            <option value="REJECTED">Rejected</option>
          </select>

          {/* Type Filter */}
          <select
            value={typeFilter}
            onChange={(e) => { setTypeFilter(e.target.value); setPage(1); }}
            className="bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs text-slate-700 focus:outline-none focus:border-blue-500"
          >
            <option value="">All Document Types</option>
            <option value="Purchase Invoice">Purchase Invoice</option>
            <option value="Sales Invoice">Sales Invoice</option>
            <option value="Purchase Order">Purchase Order</option>
            <option value="Receipt">Receipt</option>
            <option value="Expense Bill">Expense Bill</option>
            <option value="Delivery Challan">Delivery Challan</option>
            <option value="Contract">Contract</option>
            <option value="Other">Other</option>
          </select>

          <button
            onClick={fetchDocuments}
            className="p-2 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50"
            title="Refresh"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Documents Data Table */}
      <div className="bg-white rounded-xl border border-slate-200/80 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-slate-50/80 border-b border-slate-200 text-slate-500 font-semibold uppercase tracking-wider text-[11px]">
                <th className="py-3 px-4">Document</th>
                <th className="py-3 px-4">Type</th>
                <th className="py-3 px-4">Vendor / Supplier</th>
                <th className="py-3 px-4">Invoice #</th>
                <th className="py-3 px-4">Total Amount</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Confidence</th>
                <th className="py-3 px-4">Uploaded</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan={9} className="py-12 text-center text-slate-400">
                    <RefreshCw className="h-6 w-6 animate-spin mx-auto text-blue-600 mb-2" />
                    Loading documents...
                  </td>
                </tr>
              ) : documents.length === 0 ? (
                <tr>
                  <td colSpan={9} className="py-12 text-center text-slate-400">
                    No documents found matching the specified filters.
                  </td>
                </tr>
              ) : (
                documents.map((doc) => (
                  <tr key={doc.id} className="hover:bg-slate-50/70 transition-colors">
                    {/* Document Name */}
                    <td className="py-3.5 px-4">
                      <div className="flex items-center gap-2.5">
                        <FileText className="h-4 w-4 text-blue-600 shrink-0" />
                        <div>
                          <Link
                            href={`/documents/${doc.id}`}
                            className="font-semibold text-slate-800 hover:text-blue-600 hover:underline line-clamp-1"
                          >
                            {doc.file_name}
                          </Link>
                          <span className="text-[10px] text-slate-400 font-mono">
                            {doc.id.substring(0, 8)}...
                          </span>
                        </div>
                      </div>
                    </td>

                    {/* Document Type */}
                    <td className="py-3.5 px-4 font-medium text-slate-700">
                      {doc.document_type}
                    </td>

                    {/* Supplier */}
                    <td className="py-3.5 px-4 font-medium text-slate-800">
                      {doc.supplier_name || "—"}
                    </td>

                    {/* Invoice # */}
                    <td className="py-3.5 px-4 font-mono text-slate-700">
                      {doc.invoice_number || "—"}
                    </td>

                    {/* Grand Total */}
                    <td className="py-3.5 px-4 font-semibold text-slate-900">
                      {doc.grand_total !== undefined && doc.grand_total !== null
                        ? formatCurrency(doc.grand_total)
                        : "—"}
                    </td>

                    {/* Status */}
                    <td className="py-3.5 px-4">{getStatusBadge(doc.status)}</td>

                    {/* Confidence Pill */}
                    <td className="py-3.5 px-4">
                      <div className="flex items-center gap-1.5">
                        <div className="w-12 bg-slate-100 rounded-full h-1.5 overflow-hidden">
                          <div
                            className={`h-1.5 rounded-full ${
                              doc.confidence >= 0.9
                                ? "bg-emerald-500"
                                : doc.confidence >= 0.75
                                ? "bg-amber-500"
                                : "bg-rose-500"
                            }`}
                            style={{ width: `${Math.round(doc.confidence * 100)}%` }}
                          />
                        </div>
                        <span className="font-mono text-[11px] text-slate-500">
                          {Math.round(doc.confidence * 100)}%
                        </span>
                      </div>
                    </td>

                    {/* Upload Date */}
                    <td className="py-3.5 px-4 text-slate-500 font-mono text-[11px]">
                      {formatDate(doc.created_at)}
                    </td>

                    {/* Actions */}
                    <td className="py-3.5 px-4 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        <Link
                          href={`/documents/${doc.id}`}
                          className="p-1.5 rounded-md text-slate-400 hover:text-blue-600 hover:bg-blue-50"
                          title="View Details"
                        >
                          <Eye className="h-4 w-4" />
                        </Link>
                        <a
                          href={`/api/v1/documents/${doc.id}/download`}
                          target="_blank"
                          rel="noreferrer"
                          className="p-1.5 rounded-md text-slate-400 hover:text-slate-800 hover:bg-slate-100"
                          title="Download Original"
                        >
                          <Download className="h-4 w-4" />
                        </a>
                        <button
                          onClick={() => handleReprocess(doc.id)}
                          className="p-1.5 rounded-md text-slate-400 hover:text-amber-600 hover:bg-amber-50"
                          title="Reprocess with AI Agents"
                        >
                          <RotateCcw className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleDelete(doc.id)}
                          className="p-1.5 rounded-md text-slate-400 hover:text-rose-600 hover:bg-rose-50"
                          title="Delete"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar */}
        <div className="px-6 py-3.5 border-t border-slate-200/80 bg-slate-50/50 flex items-center justify-between text-xs text-slate-500">
          <div>
            Showing <span className="font-semibold text-slate-700">{documents.length}</span> of{" "}
            <span className="font-semibold text-slate-700">{total}</span> documents
          </div>
          <div className="flex items-center gap-2">
            <button
              disabled={page <= 1}
              onClick={() => setPage((p) => Math.max(p - 1, 1))}
              className="p-1.5 rounded-md border border-slate-200 text-slate-600 hover:bg-white disabled:opacity-40"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
            <span className="font-medium text-slate-700">
              Page {page} of {Math.max(totalPages, 1)}
            </span>
            <button
              disabled={page >= totalPages}
              onClick={() => setPage((p) => p + 1)}
              className="p-1.5 rounded-md border border-slate-200 text-slate-600 hover:bg-white disabled:opacity-40"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
