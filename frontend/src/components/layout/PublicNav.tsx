"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ShieldCheck, ArrowRight, Menu, X } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";

const navLinks = [
  { name: "Product Overview", href: "/" },
  { name: "Features", href: "/features" },
  { name: "Commercial Pricing", href: "/pricing" },
  { name: "Security & DPDP", href: "/security" },
  { name: "Contact & Pilot", href: "/contact" },
];

export function PublicNav() {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <nav className="sticky top-0 z-50 bg-white/90 dark:bg-navy-950/90 backdrop-blur-md border-b border-slate-200 dark:border-navy-800 transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2.5">
            <div className="h-9 w-9 rounded-xl bg-blue-600 flex items-center justify-center text-white shadow-md shadow-blue-500/20">
              <ShieldCheck className="h-5 w-5" />
            </div>
            <div>
              <span className="font-extrabold text-slate-900 dark:text-white text-lg tracking-tight">DocuMind</span>
              <span className="text-blue-600 dark:text-blue-400 font-bold text-xs ml-1.5 px-1.5 py-0.5 rounded bg-blue-50 dark:bg-blue-950 border border-blue-200 dark:border-blue-800">
                AI
              </span>
            </div>
          </Link>

          {/* Desktop Nav Links */}
          <div className="hidden md:flex items-center gap-1 lg:gap-2">
            {navLinks.map((link) => {
              const active = pathname === link.href;
              return (
                <Link
                  key={link.name}
                  href={link.href}
                  className={cn(
                    "px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors",
                    active
                      ? "text-blue-600 dark:text-blue-400 bg-blue-50/80 dark:bg-blue-950/50"
                      : "text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white hover:bg-slate-50 dark:hover:bg-navy-900"
                  )}
                >
                  {link.name}
                </Link>
              );
            })}
          </div>

          {/* Action Buttons */}
          <div className="hidden md:flex items-center gap-3">
            <Link
              href="/login"
              className="px-3.5 py-1.5 text-xs font-semibold text-slate-700 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white transition-colors"
            >
              Sign In
            </Link>
            <Link
              href="/demo"
              className="px-3.5 py-1.5 rounded-xl border border-blue-200 dark:border-blue-800 text-xs font-semibold text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-950/50 transition-colors"
            >
              Request Pilot Demo
            </Link>
            <Link
              href="/register"
              className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold flex items-center gap-1.5 shadow-md shadow-blue-500/20 transition-all"
            >
              14-Day Free Trial
              <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>

          {/* Mobile hamburger */}
          <div className="md:hidden flex items-center">
            <button
              onClick={() => setMobileOpen(!mobileOpen)}
              className="p-2 rounded-lg text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-navy-800"
              aria-label="Toggle menu"
            >
              {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileOpen && (
        <div className="md:hidden px-4 pt-2 pb-4 space-y-2 border-t border-slate-200 dark:border-navy-800 bg-white dark:bg-navy-950">
          {navLinks.map((link) => (
            <Link
              key={link.name}
              href={link.href}
              onClick={() => setMobileOpen(false)}
              className="block px-3 py-2 rounded-lg text-sm font-medium text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-navy-800"
            >
              {link.name}
            </Link>
          ))}
          <div className="pt-2 border-t border-slate-200 dark:border-navy-800 flex flex-col gap-2">
            <Link
              href="/login"
              onClick={() => setMobileOpen(false)}
              className="w-full text-center py-2 text-sm font-semibold text-slate-700 dark:text-slate-200"
            >
              Sign In
            </Link>
            <Link
              href="/demo"
              onClick={() => setMobileOpen(false)}
              className="w-full text-center py-2 rounded-xl border border-blue-200 dark:border-blue-800 text-sm font-semibold text-blue-600 dark:text-blue-400"
            >
              Request Pilot Demo
            </Link>
            <Link
              href="/register"
              onClick={() => setMobileOpen(false)}
              className="w-full text-center py-2 rounded-xl bg-blue-600 text-white text-sm font-semibold shadow-sm"
            >
              Start 14-Day Free Trial
            </Link>
          </div>
        </div>
      )}
    </nav>
  );
}
