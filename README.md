# DocuMind AI — Autonomous Document Intelligence & Invoice Automation Platform

[![Live App](https://img.shields.io/badge/Live_App-Cloudflare_Workers-F38020.svg?logo=cloudflare&logoColor=white)](https://documind.kizuna2026.workers.dev)
[![API Backend](https://img.shields.io/badge/Backend-FastAPI_on_Render-009688.svg?logo=fastapi&logoColor=white)](https://automation-website-pyp9.onrender.com)
[![Next.js](https://img.shields.io/badge/Next.js-14.2+-000000.svg?logo=next.js&logoColor=white)](https://nextjs.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-9--Agent_Multi--Agent-FF6B6B.svg)](https://langchain-ai.github.io/langgraph/)
[![Security](https://img.shields.io/badge/OWASP_Top_10-Hardened-28a745.svg?logo=shield&logoColor=white)](#3-owasp-top-10-enterprise-security-hardening)
[![License](https://img.shields.io/badge/License-Proprietary-blue.svg)](#)

DocuMind AI is a production-grade enterprise SaaS platform designed for autonomous business document ingestion, multi-page OCR parsing, classification, structured schema extraction, deterministic financial validation, cryptographic duplicate detection, and human-in-the-loop approval workflows tailored for businesses, tax professionals, and enterprise finance teams.

---

## 🌐 Live Production Deployments

| Component | Production URL | Status | Description |
|---|---|:---:|---|
| **Web Application** | [https://documind.kizuna2026.workers.dev](https://documind.kizuna2026.workers.dev) | 🟢 **Live** | Global edge Next.js frontend with SPA catch-all routing & HSTS |
| **API Backend** | [https://automation-website-pyp9.onrender.com](https://automation-website-pyp9.onrender.com) | 🟢 **Live** | FastAPI backend with persistent SQLite/PostgreSQL & auto-seeder |
| **Interactive API Docs** | [https://automation-website-pyp9.onrender.com/docs](https://automation-website-pyp9.onrender.com/docs) | 🟢 **Live** | OpenAPI / Swagger interactive documentation |
| **New Organization Onboarding** | [https://documind.kizuna2026.workers.dev/register](https://documind.kizuna2026.workers.dev/register) | 🟢 **Live** | Customer self-serve tenant onboarding with password visibility toggle |

---

## 1. Architectural Highlights

### Multi-Agent Pipeline (LangGraph 9-Agent Engine)
DocuMind AI orchestrates a synchronized 9-agent directed acyclic graph (DAG) workflow:
1. **Document Intake Agent**: File format validation, binary magic-byte inspection, SHA-256 cryptographic digest computation, exact duplicate detection.
2. **OCR Agent**: Multi-page text extraction with native PDF parsing (PyMuPDF / `fitz`), Word (`python-docx`), Excel (`openpyxl`), and image OCR parsing.
3. **Classification Agent**: Categorization into Tax Invoices, Purchase Orders, Receipts, Delivery Challans, and Contracts.
4. **Extraction Agent**: Strict Pydantic JSON schema extraction with field-level evidence and confidence tracking.
5. **Validation Agent**: Deterministic Python mathematical engine validating line items, tax breakdowns, and Indian GST rules (CGST, SGST, IGST, reverse charges).
6. **Duplicate Detection Agent**: Multi-tier deduplication (exact hash -> supplier GSTIN + invoice number -> fuzzy date/amount).
7. **Anomaly Detection Agent**: Statistical vendor spend deviation (>3x median) and non-standard tax slab identification.
8. **Decision & Approval Agent**: Evaluates pipeline results and orchestrates human-in-the-loop review.
9. **Reporting and Finalization Agent**: Persists approved records, updates vendor ledgers, and generates Excel/CSV exports.

### Free-First Zero-Budget AI Architecture
- **Primary AI Provider**: Google Gemini API (`gemini-2.5-flash`) via the official `google-genai` SDK.
- **Secondary AI Provider**: Groq API (`qwen/qwen3.8-27b` / `llama-3.3-70b-versatile`) via the `groq` SDK.
- **Failover Middleware**: Automatically catches rate limits (HTTP 429) or transient provider outages (HTTP 503) and transfers tasks with bounded exponential backoff.
- **Local Fallback Mode**: Zero-API deterministic regex/layout parsing fallback for offline or zero-quota environments.
- **Document Privacy Safeguard**: 100% local processing toggle preventing external AI data egress (`DISABLE_EXTERNAL_AI`).
- **Exact Decimal Arithmetic**: Uses Python `decimal.Decimal` with ₹2.00 rounding tolerance to eliminate floating-point calculation errors.

---

## 2. Business & Tax Professional User Experience

The platform is purpose-built for business owners, accountants, and GST tax practitioners with non-technical, intuitive domain terminology:

- **Dashboard**: Financial KPIs, monthly spending trajectories, recent audit logs, and live agent status.
- **Upload Invoices & Bills**: Drag-and-drop batch intake with customer consent validation and quota enforcement.
- **Invoices & Bills Repository**: Multi-column filtering by vendor, date range, status, and confidence score.
- **Tax & Bill Approvals**: Dedicated review queue with side-by-side OCR text viewer, mathematical audit breakdowns, and reviewer notes.
- **Vendors & Suppliers**: Comprehensive vendor directory with GSTIN tracking, state of operation, and lifetime spend history.
- **GST & Tax Reports**: Monthly expense breakdowns, top supplier spend rankings, and filtered exports.
- **Clean Authentication**: Fully customer-ready login and registration screens with interactive **Password Visibility Toggles** (`Eye` / `EyeOff`) and zero debug/synthetic buttons.
- **Workspace Navigation**: Collapsible, responsive sidebar with close button (`✕`) for full-screen document auditing on laptops, tablets, and mobile devices.

---

## 3. OWASP Top 10 Enterprise Security Hardening

The repository has been comprehensively hardened across all layers according to OWASP Top 10 standards:

### Backend API Hardening (FastAPI)
- **Brute-Force & Rate Limiting (`slowapi`)**:
  - `/api/v1/auth/login`: Maximum 5 attempts per IP per 15 minutes. Includes progressive 1-second delay mitigation on failed attempts.
  - `/api/v1/auth/register`: Maximum 3 accounts per IP per hour.
  - `/api/v1/documents/upload`: Maximum 30 uploads per user per minute.
- **SQL Injection Defense**: 100% of database queries use SQLAlchemy ORM parameterized models. Zero raw SQL string interpolation.
- **Binary Magic-Byte Inspection**: Uploads are validated against binary headers (`%PDF-`, `\x89PNG`, `\xff\xd8\xff`). Disguised executables (Windows PE `MZ`, Linux ELF `\x7fELF`, shell scripts `#!`) disguised as `.pdf` are rejected with HTTP 400.
- **Strict 10MB File Limit**: Pre-parsing size enforcement prevents resource exhaustion.
- **Anti-LFI & UUID Storage**: Uploads are never stored using user-supplied filenames. Stored physically as `{uuid4()}.{ext}` inside tenant-isolated directories with strict path containment checks.
- **JWT Session Hardening**: Access token expiration set to 30 minutes. Implemented **Refresh Token Rotation (RTR)** with a `RevokedToken` table to prevent token replay attacks. Enforces 64+ character secret keys on startup.
- **Signed Single-Use File Exports**: Export downloads (`/api/v1/reports/exports/{id}/download`) require either valid Bearer authentication or short-lived (60-second) cryptographically signed download tokens burned upon first use.

### Edge & Frontend Hardening (Cloudflare Workers & Next.js)
- **Cross-Site Scripting (XSS) Sanitization**: Integrated `DOMPurify` for dynamic AI extractions, OCR text, and notes.
- **HTTP Security Headers**:
  - `Content-Security-Policy`: Restricts scripts, objects, connections, and frame ancestors.
  - `Strict-Transport-Security: max-age=63072000; includeSubDomains; preload` (HSTS).
  - `X-Frame-Options: DENY` (Clickjacking defense).
  - `X-Content-Type-Options: nosniff`.
  - `Referrer-Policy: strict-origin-when-cross-origin`.
  - `Permissions-Policy: camera=(), microphone=(), geolocation=()`.
- **Cloudflare SPA Route Rewrites**: The edge router rewrites non-static asset routes to `/server/app/index.html` with HTTP 200 OK, completely eliminating 404s on hard page refreshes or deep links.

---

## 4. Technology Stack

- **Backend**: FastAPI, Python 3.11, Pydantic v2, SQLAlchemy 2.0, Alembic, SlowAPI.
- **Frontend**: Next.js 14 (App Router), TypeScript, Tailwind CSS, Lucide Icons, Recharts, DOMPurify.
- **Edge Deployment**: Cloudflare Workers (Assets binding + Node.js compatibility).
- **Multi-Agent Orchestration**: LangGraph, Google Gemini API, Groq Cloud API.
- **Document Processing**: PyMuPDF (`fitz`), `python-docx`, `openpyxl`, `Pillow`, PureMagic, Filetype.
- **Database & Storage**: PostgreSQL 16 & SQLite 3 (Fallback), Redis, MinIO S3, Qdrant Vector DB.
- **Compliance & Privacy**: Digital Personal Data Protection (DPDP) Act 2023 consent flows, GDPR export/forget-me APIs, tenant data isolation.

---

## 5. Local Development Quickstart

For local Windows 10/11 development:

```powershell
# 1. Automated environment setup (Python virtualenv, Node dependencies, initial database)
powershell -ExecutionPolicy Bypass -File .\setup.ps1

# 2. Launch both FastAPI backend and Next.js frontend
powershell -ExecutionPolicy Bypass -File .\start.ps1
```

### Running Automated Test Suites

```powershell
# Run the complete test suite (Unit tests + Security hardening tests)
& "backend\.venv\Scripts\python.exe" -m pytest backend/tests/ -v

# Run the dedicated OWASP security hardening test suite
& "backend\.venv\Scripts\python.exe" -m pytest backend/tests/test_security_hardening.py -v
```

All 5 security hardening tests and 11 regression tests execute with a **100% pass rate**:
- `test_rate_limiting_login_threshold`: Verified HTTP 429 after 5 failed attempts.
- `test_disguised_executable_rejected`: Verified magic-byte rejection of disguised executables.
- `test_path_traversal_sanitized_to_safe_uuid`: Verified sanitization of traversal paths to safe UUID storage.
- `test_unauthenticated_protected_endpoints_return_401`: Verified strict Bearer token requirement.
- `test_export_signed_download_token_single_use`: Verified single-use download token consumption and revocation.

---

## 6. Docker Compose Deployment (9 Services)

To run the complete containerized stack locally:

```bash
docker compose up --build -d
```

| Service | Port | Description |
|---|---|---|
| **Next.js Web UI** | `http://localhost:3000` | Full-stack SaaS application |
| **FastAPI Backend** | `http://localhost:8000` | REST API & Swagger UI (`/docs`) |
| **Grafana Dashboards** | `http://localhost:3001` | Live metrics & agent telemetry (`admin`/`admin`) |
| **Prometheus Server** | `http://localhost:9090` | System metrics scraper |
| **MinIO Console** | `http://localhost:9001` | S3 Object storage browser (`minioadmin`/`minioadmin`) |
| **MinIO S3 API** | `http://localhost:9000` | S3-compatible document storage endpoint |
| **Qdrant Vector DB** | `http://localhost:6333` | Vector search REST API |
| **PostgreSQL** | `localhost:5432` | Relational database (`documind`/`documind_secure_password`) |
| **Redis** | `localhost:6379` | Celery message broker & cache |

---

## 7. Account Credentials & Customer Access

- **Initial Administrator Account**:
  - **Email**: `admin@documind.ai`
  - **Password**: `Password123!`
  - *(Auto-seeded automatically on backend startup)*
- **Self-Serve Customer Onboarding**:
  - Businesses and tax accountants can register a new organization directly at [/register](https://documind.kizuna2026.workers.dev/register) with isolated tenant provisioning.

---

## 8. Project Structure

```
documind-ai/
├── backend/
│   ├── app/
│   │   ├── api/v1/         # FastAPI endpoints (auth, docs, invoices, approvals, reports)
│   │   ├── agents/         # LangGraph 9-Agent workflow & state definitions
│   │   ├── core/           # Security, SlowAPI rate limiting, config, Celery
│   │   ├── database/       # SQLAlchemy engine & session management
│   │   ├── models/         # 28 normalized SQLAlchemy models (including RevokedToken)
│   │   ├── schemas/        # Strict Pydantic request/response schemas
│   │   ├── services/       # OCR, LLM failover, storage, duplicate & anomaly engines
│   │   └── main.py         # FastAPI application entrypoint with security headers & limiter
│   ├── tests/              # Pytest automated test suite (including test_security_hardening.py)
│   └── requirements.txt    # Backend Python dependencies
├── frontend/
│   ├── src/
│   │   ├── app/            # Next.js 14 App Router (All 24 enterprise pages)
│   │   ├── components/     # UI components, layout shell, responsive sidebar
│   │   ├── lib/            # Typed API client, DOMPurify sanitization, utility functions
│   │   └── types/          # Shared TypeScript type definitions
│   ├── next.config.mjs     # Standalone output, rewrites, and security response headers
│   └── package.json        # Frontend dependencies
├── worker.js               # Cloudflare Workers edge router with CSP, HSTS & SPA rewrites
├── wrangler.jsonc          # Cloudflare Workers deployment configuration
├── docker-compose.yml      # Multi-container orchestration (9 services)
├── setup.ps1               # Automated Windows environment setup
├── start.ps1               # Development start script
├── stop.ps1                # Development stop script
├── test.ps1                # Automated test execution script
└── README.md               # Master project documentation
```

---

## 9. Comprehensive Documentation & Operational Guides

- [Production Readiness Audit Report](file:///docs/PRODUCTION_READINESS.md)
- [Customer Installation & Deployment Guide](file:///docs/CUSTOMER_INSTALLATION_GUIDE.md)
- [Customer Pilot Onboarding Guide](file:///docs/PHASE_5I_CUSTOMER_PILOT_GUIDE.md)
- [Final Security Review](file:///docs/FINAL_SECURITY_REVIEW.md)
- [System Architecture](file:///docs/architecture/ARCHITECTURE.md)
- [AI Benchmark & Evaluation Report](file:///docs/AI_PERFORMANCE_BENCHMARK.md)
