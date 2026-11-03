"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  UploadCloud,
  FileText,
  CheckCircle2,
  Building2,
  Cpu,
  BarChart3,
  Settings,
  ShieldCheck,
  CreditCard,
  Sparkles,
  ShieldAlert,
} from "lucide-react";
import { cn } from "@/lib/utils";

const navigation = [
  { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { name: "Upload Documents", href: "/upload", icon: UploadCloud },
  { name: "Documents", href: "/documents", icon: FileText },
  { name: "Approval Center", href: "/approvals", icon: CheckCircle2 },
  { name: "Suppliers", href: "/suppliers", icon: Building2 },
  { name: "AI Agent Monitor", href: "/agents", icon: Cpu },
  { name: "Reports & Analytics", href: "/reports", icon: BarChart3 },
  { name: "Subscription & Plans", href: "/subscriptions", icon: CreditCard },
  { name: "Onboarding Wizard", href: "/onboarding", icon: Sparkles },
  { name: "Platform Admin", href: "/admin", icon: ShieldAlert },
  { name: "Settings", href: "/settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 bg-navy-950 text-slate-300 flex flex-col border-r border-navy-800 shrink-0 select-none">
      {/* Brand Header */}
      <div className="h-16 flex items-center px-6 gap-3 border-b border-navy-800/80 bg-navy-900/50">
        <div className="h-9 w-9 rounded-lg bg-blue-600 flex items-center justify-center text-white shadow-md shadow-blue-500/20">
          <ShieldCheck className="h-5 w-5" />
        </div>
        <div>
          <span className="font-bold text-white text-lg tracking-tight">DocuMind</span>
          <span className="text-blue-400 font-semibold text-xs ml-1.5 px-1.5 py-0.5 rounded bg-blue-500/10 border border-blue-500/20">AI</span>
          <p className="text-[10px] text-slate-400 font-medium">Enterprise Intelligence</p>
        </div>
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

      {/* System Status Card */}
      <div className="p-4 border-t border-navy-800/80 m-3 bg-navy-900/40 rounded-xl">
        <div className="flex items-center justify-between text-xs mb-2">
          <span className="text-slate-400 font-medium">LangGraph Engine</span>
          <span className="flex items-center gap-1.5 text-emerald-400 font-semibold">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
            9 Agents Live
          </span>
        </div>
        <p className="text-[11px] text-slate-400 leading-relaxed">
          Deterministic math validation & human-in-the-loop active.
        </p>
      </div>
    </aside>
  );
}

