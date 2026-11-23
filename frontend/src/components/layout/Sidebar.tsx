"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  UploadCloud,
  FileText,
  CheckCircle2,
  Building2,
  ShieldCheck,
  BarChart3,
  Settings,
  CreditCard,
  Sparkles,
  ShieldAlert,
  X,
  FileCheck2,
  ChevronLeft,
  Plus,
} from "lucide-react";
import { cn } from "@/lib/utils";

const navigation = [
  { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { name: "Invoices & Bills", href: "/documents", icon: FileText },
  { name: "Tax & Bill Approvals", href: "/approvals", icon: CheckCircle2, badge: "Review", badgeColor: "amber" },
  { name: "Vendors & Suppliers", href: "/suppliers", icon: Building2 },
  { name: "GST & Tax Audit", href: "/agents", icon: FileCheck2, badge: "Active", badgeColor: "emerald" },
  { name: "GST & Tax Reports", href: "/reports", icon: BarChart3 },
  { name: "Subscription & Billing", href: "/subscriptions", icon: CreditCard },
  { name: "Quick Setup Guide", href: "/onboarding", icon: Sparkles },
  { name: "Company Admin", href: "/admin", icon: ShieldAlert },
  { name: "Settings", href: "/settings", icon: Settings },
];

interface SidebarProps {
  isOpen?: boolean;
  onClose?: () => void;
}

export function Sidebar({ isOpen = true, onClose }: SidebarProps) {
  const pathname = usePathname();
  const [showStatusCard, setShowStatusCard] = useState(true);

  useEffect(() => {
    const isDismissed = localStorage.getItem("documind_hide_status_card") === "true";
    if (isDismissed) {
      setShowStatusCard(false);
    }
  }, []);

  const handleDismiss = () => {
    setShowStatusCard(false);
    localStorage.setItem("documind_hide_status_card", "true");
  };

  if (!isOpen) {
    return null;
  }

  return (
    <aside className="w-64 bg-navy-950 text-slate-300 flex flex-col border-r border-navy-800 shrink-0 select-none z-30 transition-all duration-300 ease-out shadow-xl shadow-black/20">
      {/* Brand Header with Close Button */}
      <div className="h-16 flex items-center justify-between px-5 border-b border-navy-800/80 bg-navy-900/60 backdrop-blur-md">
        <Link href="/dashboard" className="flex items-center gap-2.5 group">
          <div className="h-9 w-9 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center text-white shadow-md shadow-blue-500/25 group-hover:scale-105 transition-transform duration-200">
            <ShieldCheck className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-bold text-white text-base tracking-tight group-hover:text-blue-300 transition-colors">DocuMind</span>
              <span className="text-blue-400 font-bold text-[10px] px-1.5 py-0.5 rounded-md bg-blue-500/15 border border-blue-500/25">AI</span>
            </div>
            <p className="text-[10px] text-slate-400 font-medium">GST & Invoice Intelligence</p>
          </div>
        </Link>

        {/* Close Button */}
        {onClose && (
          <button
            onClick={onClose}
            className="flex items-center justify-center h-8 w-8 text-slate-400 hover:text-white hover:bg-white/10 active:scale-95 rounded-lg border border-transparent hover:border-slate-700/60 transition-all duration-200 shadow-sm"
            title="Close / Collapse Sidebar"
            aria-label="Close Sidebar"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>

      {/* Primary Action Button: Upload Invoice */}
      <div className="px-4 pt-4 pb-1">
        <Link
          href="/upload"
          className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl bg-gradient-to-r from-blue-600 via-indigo-600 to-blue-700 hover:from-blue-500 hover:via-indigo-500 hover:to-blue-600 text-white text-xs font-semibold shadow-md shadow-blue-500/25 hover:shadow-lg hover:shadow-blue-500/35 hover:-translate-y-0.5 active:translate-y-0 active:scale-[0.98] transition-all duration-200 group relative overflow-hidden"
        >
          <div className="absolute inset-0 bg-white/20 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700" />
          <Plus className="h-4 w-4 transition-transform group-hover:rotate-90 duration-200" />
          <span>Upload Invoices</span>
        </Link>
      </div>

      {/* Nav Menu */}
      <div className="flex-1 py-3 px-3 space-y-1 overflow-y-auto">
        <div className="px-3 pb-1.5 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
          Workspace
        </div>
        {navigation.map((item) => {
          const isActive = pathname === item.href || (item.href !== "/dashboard" && pathname.startsWith(item.href));
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-medium transition-all duration-150 group",
                isActive
                  ? "bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-md shadow-blue-600/30 font-semibold"
                  : "text-slate-300 hover:bg-navy-800/80 hover:text-white hover:translate-x-1"
              )}
            >
              <div className="flex items-center gap-3">
                <item.icon className={cn("h-4 w-4 shrink-0 transition-transform duration-150 group-hover:scale-110", isActive ? "text-white" : "text-slate-400 group-hover:text-blue-400")} />
                <span>{item.name}</span>
              </div>
              {item.badge && (
                <span
                  className={cn(
                    "text-[10px] font-bold px-1.5 py-0.5 rounded-md border transition-colors",
                    item.badgeColor === "amber" && "bg-amber-500/15 text-amber-300 border-amber-500/30",
                    item.badgeColor === "emerald" && "bg-emerald-500/15 text-emerald-300 border-emerald-500/30 flex items-center gap-1"
                  )}
                >
                  {item.badgeColor === "emerald" && <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />}
                  {item.badge}
                </span>
              )}
            </Link>
          );
        })}
      </div>

      {/* GST & Tax Compliance Status Card with Close Button */}
      {showStatusCard && (
        <div className="relative p-3.5 border border-navy-800 m-3 bg-gradient-to-br from-navy-900/90 to-navy-950/90 rounded-xl transition-all shadow-md hover:border-navy-700/80">
          <button
            onClick={handleDismiss}
            className="absolute top-2.5 right-2.5 p-1 text-slate-400 hover:text-white hover:bg-white/10 rounded-md transition-colors"
            title="Dismiss notification"
            aria-label="Dismiss notification"
          >
            <X className="h-3.5 w-3.5" />
          </button>
          <div className="flex items-center gap-1.5 text-xs mb-1.5 pr-6">
            <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse shrink-0" />
            <span className="font-semibold text-emerald-400">GST & Tax Guard Active</span>
          </div>
          <p className="text-[11px] text-slate-300 leading-relaxed pr-2">
            Automated tax calculation, GSTIN verification & duplicate bill checks active.
          </p>
        </div>
      )}

      {/* Bottom Collapse Button */}
      {onClose && (
        <div className="px-3 py-2 border-t border-navy-800/80 bg-navy-950/50">
          <button
            onClick={onClose}
            className="w-full flex items-center justify-center gap-2 py-2 px-3 rounded-lg text-xs font-medium text-slate-400 hover:text-white hover:bg-navy-800/60 active:scale-95 transition-all duration-150"
            title="Collapse Sidebar"
          >
            <ChevronLeft className="h-3.5 w-3.5" />
            <span>Collapse Sidebar</span>
          </button>
        </div>
      )}
    </aside>
  );
}

