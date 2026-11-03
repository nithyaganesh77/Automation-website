import Link from "next/link";
import { ShieldCheck, Mail, MapPin, Phone, ExternalLink } from "lucide-react";

export function PublicFooter() {
  return (
    <footer className="bg-slate-900 text-slate-400 text-xs border-t border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Brand & Mission */}
          <div className="space-y-3 md:col-span-1">
            <div className="flex items-center gap-2">
              <div className="h-7 w-7 rounded-lg bg-blue-600 flex items-center justify-center text-white">
                <ShieldCheck className="h-4 w-4" />
              </div>
              <span className="font-bold text-white text-base">DocuMind AI</span>
            </div>
            <p className="text-slate-400 text-xs leading-relaxed">
              Enterprise Multi-Agent Business Document Intelligence and Indian GST Invoice Automation Platform.
            </p>
            <div className="pt-2">
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[10px] font-semibold bg-emerald-950 text-emerald-300 border border-emerald-800">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
                DPDP Act 2023 Compliant (India)
              </span>
            </div>
          </div>

          {/* Product & Solutions */}
          <div className="space-y-2">
            <h4 className="font-semibold text-white uppercase tracking-wider text-[11px]">Solutions</h4>
            <ul className="space-y-1.5">
              <li>
                <Link href="/features" className="hover:text-white transition-colors">
                  9 Multi-Agent Workflows
                </Link>
              </li>
              <li>
                <Link href="/features" className="hover:text-white transition-colors">
                  Indian GST Reconciliation
                </Link>
              </li>
              <li>
                <Link href="/pricing" className="hover:text-white transition-colors">
                  Commercial Pricing (INR)
                </Link>
              </li>
              <li>
                <Link href="/demo" className="hover:text-white transition-colors">
                  Interactive Pilot Sandbox
                </Link>
              </li>
              <li>
                <Link href="/security" className="hover:text-white transition-colors">
                  Bring-Your-Own-Key (BYOK)
                </Link>
              </li>
            </ul>
          </div>

          {/* Legal & Compliance */}
          <div className="space-y-2">
            <h4 className="font-semibold text-white uppercase tracking-wider text-[11px]">Trust & Legal</h4>
            <ul className="space-y-1.5">
              <li>
                <Link href="/privacy" className="hover:text-white transition-colors">
                  Privacy Policy (Zero Model Training)
                </Link>
              </li>
              <li>
                <Link href="/terms" className="hover:text-white transition-colors">
                  Commercial Terms of Service
                </Link>
              </li>
              <li>
                <Link href="/security" className="hover:text-white transition-colors">
                  Data Processing Addendum (DPA)
                </Link>
              </li>
              <li>
                <Link href="/terms" className="hover:text-white transition-colors">
                  Customer Pilot Terms
                </Link>
              </li>
              <li>
                <Link href="/security" className="hover:text-white transition-colors">
                  Tenant Isolation Architecture
                </Link>
              </li>
            </ul>
          </div>

          {/* Contact & Support */}
          <div className="space-y-2">
            <h4 className="font-semibold text-white uppercase tracking-wider text-[11px]">Pilot Contact</h4>
            <ul className="space-y-2">
              <li className="flex items-start gap-2">
                <MapPin className="h-4 w-4 text-blue-400 shrink-0 mt-0.5" />
                <span>Indiranagar, Bengaluru / Powai, Mumbai, India</span>
              </li>
              <li className="flex items-center gap-2">
                <Mail className="h-4 w-4 text-blue-400 shrink-0" />
                <a href="mailto:pilot@documind.ai" className="hover:text-white">
                  pilot@documind.ai
                </a>
              </li>
              <li className="flex items-center gap-2">
                <Phone className="h-4 w-4 text-blue-400 shrink-0" />
                <span>+91 (080) 4567-8900</span>
              </li>
            </ul>
          </div>
        </div>

        <div className="mt-8 pt-6 border-t border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-4 text-[11px] text-slate-500">
          <p>&copy; {new Date().getFullYear()} DocuMind AI Technologies. All rights reserved.</p>
          <div className="flex items-center gap-4">
            <span>Free-First SaaS Architecture</span>
            <span>&bull;</span>
            <span>Google Gemini + Groq LPU</span>
            <span>&bull;</span>
            <span>PostgreSQL Production Ready</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
