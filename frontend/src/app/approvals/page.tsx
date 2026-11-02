"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  CheckCircle2,
  XCircle,
  Clock,
  AlertTriangle,
  FileText,
  Eye,
  Check,
  X,
  MessageSquare,
  ShieldCheck,
  RefreshCw,
} from "lucide-react";
import { api } from "@/lib/api-client";
import { formatCurrency, formatDate } from "@/lib/utils";
import { ApprovalRequest } from "@/types";

export default function ApprovalsPage() {
  const [requests, setRequests] = useState<ApprovalRequest[]>([]);
  const [statusFilter, setStatusFilter] = useState("PENDING");
  const [loading, setLoading] = useState(true);

  // Review Modal State
  const [selectedReq, setSelectedReq] = useState<ApprovalRequest | null>(null);
  const [actionType, setActionType] = useState<"APPROVE" | "REJECT" | null>(null);
  const [comment, setComment] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const fetchApprovals = async () => {
    setLoading(true);
    try {
      const data = await api.get<ApprovalRequest[]>(`/approvals?status=${statusFilter}`);
      setRequests(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchApprovals();
  }, [statusFilter]);

  const handleActionSubmit = async () => {
    if (!selectedReq || !actionType) return;
    setSubmitting(true);
    try {
      const endpoint = actionType === "APPROVE" ? "approve" : "reject";
      await api.post(`/approvals/${selectedReq.id}/${endpoint}`, {
        action: actionType,
        comments: comment,
      });
      setSelectedReq(null);
      setActionType(null);
      setComment("");
      await fetchApprovals();
    } catch (err: any) {
      alert(err.message || "Failed to process approval action");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-navy-900 tracking-tight">Human Approval Center</h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Review invoices flagged for verification before accounting export. Zero silent approvals.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {["PENDING", "APPROVED", "REJECTED", "ALL"].map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                statusFilter === st
                  ? "bg-blue-600 text-white shadow-sm"
                  : "bg-white border border-slate-200 text-slate-600 hover:bg-slate-50"
              }`}
            >
              {st === "ALL" ? "All Requests" : st.replace("_", " ")}
            </button>
          ))}
          <button
            onClick={fetchApprovals}
            className="p-2 rounded-lg border border-slate-200 bg-white text-slate-600 hover:bg-slate-50"
            title="Refresh"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Approval Requests Table */}
      <div className="bg-white rounded-xl border border-slate-200/80 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-slate-50/80 border-b border-slate-200 text-slate-500 font-semibold uppercase tracking-wider text-[11px]">
                <th className="py-3 px-4">Priority</th>
                <th className="py-3 px-4">Document / File</th>
                <th className="py-3 px-4">Vendor</th>
                <th className="py-3 px-4">Invoice #</th>
                <th className="py-3 px-4">Amount</th>
                <th className="py-3 px-4">Submitted</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-right">Review Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-slate-400">
                    <RefreshCw className="h-6 w-6 animate-spin mx-auto text-blue-600 mb-2" />
                    Loading approval queue...
                  </td>
                </tr>
              ) : requests.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-slate-400">
                    No documents currently awaiting approval.
                  </td>
                </tr>
              ) : (
                requests.map((req) => (
                  <tr key={req.id} className="hover:bg-slate-50/70 transition-colors">
                    {/* Priority */}
                    <td className="py-3.5 px-4">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          req.priority === "URGENT"
                            ? "bg-rose-100 text-rose-800"
                            : req.priority === "HIGH"
                            ? "bg-amber-100 text-amber-800"
                            : "bg-blue-100 text-blue-800"
                        }`}
                      >
                        {req.priority}
                      </span>
                    </td>

                    {/* Document */}
                    <td className="py-3.5 px-4 font-semibold text-slate-800">
                      <div className="flex items-center gap-2">
                        <FileText className="h-4 w-4 text-blue-600 shrink-0" />
                        <Link
                          href={`/documents/${req.document_id}`}
                          className="hover:underline hover:text-blue-600 line-clamp-1"
                        >
                          {req.document?.file_name || `Doc ${req.document_id.substring(0, 8)}`}
                        </Link>
                      </div>
                    </td>

                    {/* Vendor */}
                    <td className="py-3.5 px-4 font-medium text-slate-700">
                      {req.document?.supplier_name || "—"}
                    </td>

                    {/* Invoice Number */}
                    <td className="py-3.5 px-4 font-mono text-slate-700">
                      {req.document?.invoice_number || "—"}
                    </td>

                    {/* Amount */}
                    <td className="py-3.5 px-4 font-bold text-slate-900">
                      {req.document?.grand_total ? formatCurrency(req.document.grand_total) : "—"}
                    </td>

                    {/* Submitted At */}
                    <td className="py-3.5 px-4 font-mono text-[11px] text-slate-500">
                      {formatDate(req.created_at)}
                    </td>

                    {/* Status */}
                    <td className="py-3.5 px-4">
                      <span
                        className={`px-2.5 py-1 rounded-full text-[10px] font-bold ${
                          req.status === "APPROVED"
                            ? "bg-emerald-100 text-emerald-800"
                            : req.status === "REJECTED"
                            ? "bg-rose-100 text-rose-800"
                            : "bg-amber-100 text-amber-800"
                        }`}
                      >
                        {req.status}
                      </span>
                    </td>

                    {/* Actions */}
                    <td className="py-3.5 px-4 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        <Link
                          href={`/documents/${req.document_id}`}
                          className="p-1.5 rounded text-slate-400 hover:text-blue-600 hover:bg-blue-50"
                          title="Inspect Document"
                        >
                          <Eye className="h-4 w-4" />
                        </Link>
                        {req.status === "PENDING" && (
                          <>
                            <button
                              onClick={() => {
                                setSelectedReq(req);
                                setActionType("APPROVE");
                                setComment("Approved following financial inspection.");
                              }}
                              className="px-2.5 py-1 rounded-md bg-emerald-600 hover:bg-emerald-500 text-white font-semibold flex items-center gap-1 shadow-sm"
                            >
                              <Check className="h-3.5 w-3.5" />
                              Approve
                            </button>
                            <button
                              onClick={() => {
                                setSelectedReq(req);
                                setActionType("REJECT");
                                setComment("");
                              }}
                              className="px-2.5 py-1 rounded-md bg-rose-600 hover:bg-rose-500 text-white font-semibold flex items-center gap-1 shadow-sm"
                            >
                              <X className="h-3.5 w-3.5" />
                              Reject
                            </button>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Review Confirmation Modal */}
      {selectedReq && actionType && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 text-left shadow-2xl border border-slate-200">
            <h2 className="text-base font-bold text-navy-900">
              {actionType === "APPROVE" ? "Confirm Invoice Approval" : "Reject Invoice"}
            </h2>
            <p className="text-xs text-slate-500 mt-1">
              Document: <span className="font-semibold text-slate-800">{selectedReq.document?.file_name}</span>
            </p>

            <div className="mt-4">
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                Reviewer Comments (Logged to Audit History)
              </label>
              <textarea
                required={actionType === "REJECT"}
                placeholder={actionType === "REJECT" ? "State exact reason for rejection..." : "Add reviewer notes..."}
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                rows={3}
                className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2.5 text-xs text-slate-800 focus:outline-none focus:border-blue-500"
              />
            </div>

            <div className="mt-6 flex justify-end gap-2">
              <button
                type="button"
                onClick={() => { setSelectedReq(null); setActionType(null); }}
                className="px-4 py-2 rounded-lg text-xs font-semibold text-slate-600 hover:bg-slate-100"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={submitting || (actionType === "REJECT" && !comment.trim())}
                onClick={handleActionSubmit}
                className={`px-4 py-2 rounded-lg text-xs font-semibold text-white shadow-sm disabled:opacity-50 ${
                  actionType === "APPROVE" ? "bg-emerald-600 hover:bg-emerald-500" : "bg-rose-600 hover:bg-rose-500"
                }`}
              >
                {submitting ? "Submitting..." : `Confirm ${actionType === "APPROVE" ? "Approval" : "Rejection"}`}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
