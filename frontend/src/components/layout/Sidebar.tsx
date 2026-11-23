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
} from "lucide-react";
import { cn } from "@/lib/utils";

const navigation = [
  { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { name: "Upload Invoices", href: "/upload", icon: UploadCloud },
  { name: "Invoices & Bills", href: "/documents", icon: FileText },
  { name: "Tax & Bill Approvals", href: "/approvals", icon: CheckCircle2 },
  { name: "Vendors & Suppliers", href: "/suppliers", icon: Building2 },
  { name: "GST & Tax Audit", href: "/agents", icon: FileCheck2 },
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
    <aside className="w-64 bg-navy-950 text-slate-300 flex flex-col border-r border-navy-800 shrink-0 select-none z-30 transition-all duration-200">
      {/* Brand Header with Close Button */}
      <div className="h-16 flex items-center justify-between px-5 border-b border-navy-800/80 bg-navy-900/50">
        <div className="flex items-center gap-2.5">
          <div className="h-9 w-9 rounded-lg bg-blue-600 flex items-center justify-center text-white shadow-md shadow-blue-500/20">
            <ShieldCheck className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-bold text-white text-base tracking-tight">DocuMind</span>
              <span className="text-blue-400 font-semibold text-[10px] px-1 py-0.2 rounded bg-blue-500/10 border border-blue-500/20">AI</span>
            </div>
            <p className="text-[10px] text-slate-400 font-medium">GST & Invoice Intelligence</p>
          </div>
        </div>

        {/* Close Button */}
        {onClose && (
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-white hover:bg-navy-800 rounded-lg transition-colors"
            title="Close Sidebar"
            aria-label="Close Sidebar"
          >
            <X className="h-5 w-5" />
          </button>
        )}
      </div>

      {/* Nav Menu */}
      <div className="flex-1 py-6 px-3 space-y-1 overflow-y-auto">
        <div className="px-3 pb-2 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
          Workspace
        </div>
        {navigation.map((item) => {
          const isActive = pathname === item.href || (item.href !== "/dashboard" && pathname.startsWith(item.href));
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-all duration-150",
                isActive
                  ? "bg-blue-600 text-white shadow-sm shadow-blue-600/30 font-semibold"
                  : "text-slate-300 hover:bg-navy-800/70 hover:text-white"
              )}
            >
              <item.icon className={cn("h-4 w-4 shrink-0", isActive ? "text-white" : "text-slate-400")} />
              <span>{item.name}</span>
            </Link>
          );
        })}
      </div>

      {/* GST & Tax Compliance Status Card with Close Button */}
      {showStatusCard && (
        <div className="relative p-3.5 border border-navy-800 m-3 bg-navy-900/60 rounded-xl transition-all shadow-sm">
          <button
            onClick={handleDismiss}
            className="absolute top-2.5 right-2.5 p-1 text-slate-400 hover:text-white hover:bg-navy-800 rounded-md transition-colors"
            title="Close this card"
            aria-label="Close this card"
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
    </aside>
  );
}

