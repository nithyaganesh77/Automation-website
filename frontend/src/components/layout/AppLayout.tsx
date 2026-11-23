"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { Sidebar } from "@/components/layout/Sidebar";
import { Navbar } from "@/components/layout/Navbar";

const PUBLIC_ROUTES = [
  "/",
  "/pricing",
  "/features",
  "/contact",
  "/privacy",
  "/terms",
  "/demo",
  "/login",
  "/register"
];

export function AppLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [mounted, setMounted] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const isPublicPage = PUBLIC_ROUTES.some(
    (route) => pathname === route || (route !== "/" && pathname.startsWith(route))
  );

  useEffect(() => {
    setMounted(true);
    const token = typeof window !== "undefined" ? localStorage.getItem("documind_token") : null;
    if (!token && !isPublicPage) {
      router.push("/login");
    }

    // Restore sidebar preference
    const saved = typeof window !== "undefined" ? localStorage.getItem("documind_sidebar_open") : null;
    if (saved !== null) {
      setSidebarOpen(saved === "true");
    }
  }, [pathname, isPublicPage, router]);

  const handleToggleSidebar = () => {
    setSidebarOpen((prev) => {
      const next = !prev;
      localStorage.setItem("documind_sidebar_open", String(next));
      return next;
    });
  };

  const handleCloseSidebar = () => {
    setSidebarOpen(false);
    localStorage.setItem("documind_sidebar_open", "false");
  };

  // Public marketing & auth pages render directly without app workspace shell
  if (isPublicPage) {
    return <main className="min-h-screen">{children}</main>;
  }

  if (!mounted) {
    return (
      <div className="min-h-screen bg-slate-900 flex flex-col items-center justify-center text-white space-y-4">
        <div className="w-10 h-10 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
        <p className="text-sm font-medium text-slate-400">Loading DocuMind AI...</p>
      </div>
    );
  }

  // Authenticated workspace shell
  return (
    <div className="flex h-screen overflow-hidden bg-slate-50">
      <Sidebar isOpen={sidebarOpen} onClose={handleCloseSidebar} />
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <Navbar sidebarOpen={sidebarOpen} onToggleSidebar={handleToggleSidebar} />
        <main className="flex-1 overflow-y-auto p-8">{children}</main>
      </div>
    </div>
  );
}

