"use client";

import { useEffect, useState } from "react";
import {
  BarChart3,
  Download,
  FileSpreadsheet,
  FileText,
  IndianRupee,
  TrendingUp,
  Building2,
  Calendar,
  CheckCircle,
  RefreshCw,
} from "lucide-react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
} from "recharts";
import { api } from "@/lib/api-client";
import { formatCurrency } from "@/lib/utils";
import { ExportRecord } from "@/types";

export default function ReportsPage() {
  const [expenseData, setExpenseData] = useState<any[]>([]);
  const [supplierData, setSupplierData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);
  const [exportSuccess, setExportSuccess] = useState<string | null>(null);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [expenses, suppliers] = await Promise.all([
        api.get<any[]>("/reports/expenses"),
        api.get<any[]>("/reports/suppliers"),
      ]);
      setExpenseData(expenses);
      setSupplierData(suppliers);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleTriggerExport = async (format: "EXCEL" | "CSV", exportType: "INVOICES" | "SUPPLIERS") => {
    setExporting(true);
    setExportSuccess(null);
    try {
      const res = await api.post<any>("/reports/exports", {
        export_type: exportType,
        format,
      });
      setExportSuccess(`Successfully generated ${format} export (${res.record_count} records).`);
      // Trigger download
      window.open(`/api/v1/reports/exports/${res.id}/download`, "_blank");
    } catch (err: any) {
      alert(err.message || "Export failed");
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200/80 pb-5">
        <div>
          <h1 className="text-2xl font-bold text-navy-900 tracking-tight">Financial Reports & Exports</h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Accounting-ready ledgers, tax liability schedules, and vendor expenditure analytics.
          </p>
        </div>

        {/* Quick Export Actions */}
        <div className="flex items-center gap-2.5">
          <button
            disabled={exporting}
            onClick={() => handleTriggerExport("EXCEL", "INVOICES")}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-sm transition-all disabled:opacity-50"
          >
            <FileSpreadsheet className="h-4 w-4" />
            Export Excel (.xlsx)
          </button>
          <button
            disabled={exporting}
            onClick={() => handleTriggerExport("CSV", "INVOICES")}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-sm transition-all disabled:opacity-50"
          >
            <Download className="h-4 w-4" />
            Export CSV
          </button>
        </div>
      </div>

      {exportSuccess && (
        <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-center justify-between">
          <span>{exportSuccess}</span>
          <button onClick={() => setExportSuccess(null)} className="text-emerald-600 hover:underline">
            Dismiss
          </button>
        </div>
      )}

      {/* Monthly Expense & Tax Chart */}
      <div className="p-6 bg-white rounded-xl border border-slate-200/80 shadow-sm space-y-4">
        <div>
          <h2 className="text-sm font-bold text-navy-900">Monthly Expense Trajectory & GST Accumulation</h2>
          <p className="text-xs text-slate-400">Total verified spend vs. Input Tax Credit (ITC) claimable</p>
        </div>

        <div className="h-72 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={expenseData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <XAxis dataKey="month" tick={{ fontSize: 11, fill: "#64748b" }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 11, fill: "#64748b" }} axisLine={false} tickLine={false} />
              <Tooltip
                formatter={(val: any) => formatCurrency(val)}
                contentStyle={{ backgroundColor: "#102A43", borderColor: "#334E68", borderRadius: "8px", color: "#fff", fontSize: "12px" }}
              />
              <Bar dataKey="total_amount" fill="#1d4ed8" radius={[4, 4, 0, 0]} name="Total Amount" />
              <Bar dataKey="tax_amount" fill="#0891b2" radius={[4, 4, 0, 0]} name="GST Tax" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Supplier Spend Concentration */}
      <div className="bg-white rounded-xl border border-slate-200/80 shadow-sm p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-sm font-bold text-navy-900">Vendor Expenditure Concentration</h2>
            <p className="text-xs text-slate-400">Top vendors ranked by cumulative procurement spend</p>
          </div>
          <button
            onClick={() => handleTriggerExport("EXCEL", "SUPPLIERS")}
            className="text-xs text-blue-600 font-semibold hover:underline flex items-center gap-1"
          >
            Export Supplier Spend Ledger
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold text-[11px]">
                <th className="py-2.5 px-3">Supplier Name</th>
                <th className="py-2.5 px-3">Invoices Count</th>
                <th className="py-2.5 px-3">Share of Total Procurement</th>
                <th className="py-2.5 px-3 text-right">Cumulative Spend</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {supplierData.map((s) => (
                <tr key={s.supplier_id} className="hover:bg-slate-50">
                  <td className="py-3 px-3 font-semibold text-slate-900">{s.supplier_name}</td>
                  <td className="py-3 px-3 font-medium text-slate-700">{s.invoice_count}</td>
                  <td className="py-3 px-3">
                    <div className="flex items-center gap-2">
                      <div className="w-24 bg-slate-100 rounded-full h-1.5 overflow-hidden">
                        <div
                          className="bg-blue-600 h-1.5 rounded-full"
                          style={{ width: `${s.percentage_of_total}%` }}
                        />
                      </div>
                      <span className="font-mono text-slate-500">{s.percentage_of_total}%</span>
                    </div>
                  </td>
                  <td className="py-3 px-3 text-right font-bold text-navy-900 font-mono">
                    {formatCurrency(s.total_spend)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

