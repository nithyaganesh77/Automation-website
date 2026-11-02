import "./globals.css";
import type { Metadata } from "next";
import { AppLayout } from "@/components/layout/AppLayout";

export const metadata: Metadata = {
  title: "DocuMind AI — Enterprise Document Intelligence & Invoice Automation",
  description: "Autonomous multi-agent document extraction, validation, anomaly detection, and human approval platform.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="antialiased text-slate-800 bg-slate-50">
        <AppLayout>{children}</AppLayout>
      </body>
    </html>
  );
}
