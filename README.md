# DocuMind AI — Autonomous Document Intelligence & Invoice Automation Platform

[![CI Pipeline](https://github.com/documind-ai/documind/actions/workflows/ci.yml/badge.svg)](https://github.com/documind-ai/documind/actions/workflows/ci.yml)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14.2+-000000.svg?logo=next.js&logoColor=white)](https://nextjs.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-Multi--Agent-FF6B6B.svg)](https://langchain-ai.github.io/langgraph/)
[![License](https://img.shields.io/badge/License-Proprietary-blue.svg)](#)

DocuMind AI is a production-grade enterprise SaaS platform for autonomous document ingestion, multi-page OCR parsing, classification, structured schema extraction, deterministic financial validation, cryptographic duplicate detection, and human-in-the-loop approval workflows.

---

## 1. Architectural Highlights

- **9 Specialized LangGraph AI Agents**:
  1. **Document Intake Agent**: File type validation, SHA-256 cryptographic digest computation, exact duplicate detection.
  2. **OCR Agent**: Multi-page text extraction with native PDF fallback (PyMuPDF), Word (`python-docx`), Excel (`openpyxl`), and image OCR parsing.
  3. **Classification Agent**: Categorization into Tax Invoices, Purchase Orders, Receipts, Delivery Challans, and Contracts.
  4. **Extraction Agent**: Strict Pydantic JSON schema extraction with field-level evidence and confidence tracking.
  5. **Validation Agent**: Deterministic Python mathematical engine validating line items, tax breakdowns, and Indian GST rules.
  6. **Duplicate Detection Agent**: Multi-tier deduplication (exact hash -> supplier + invoice number -> fuzzy date/amount).
  7. **Anomaly Detection Agent**: Statistical vendor spend deviation and tax slab anomaly detection.
  8. **Decision & Approval Agent**: Evaluates pipeline results and orchestrates human-in-the-loop review.
  9. **Reporting and Finalization Agent**: Persists approved records, updates vendor ledgers, and generates Excel/CSV exports.
- **Free-First Zero-Budget AI Architecture**:
  - **Primary**: Google Gemini API (`gemini-2.0-flash`) via the official `google-genai` SDK.
  - **Fallback**: Groq API (`llama-3.3-70b-versatile` / `llama-3.1-8b-instant`) via the `groq` SDK.
  - **Failover Protection**: Automatic failover upon rate limits (HTTP 429) or transient provider outages with bounded exponential backoff.
  - **Local Fallback**: Zero-API deterministic regex/layout parsing fallback for offline or zero-quota environments.
- **100% Free & Open-Source Local Infrastructure**:
  - **MinIO**: High-performance local S3-compatible object storage with signed URLs.
  - **Qdrant**: Local vector database for semantic chunk retrieval and embedding indexing.
  - **PostgreSQL & Redis**: Production-grade relational persistence and asynchronous Celery task queue.
  - **Prometheus & Grafana**: Local metric scraping and real-time observability dashboards.
- **Zero Silent Approvals**: Unverified financial records or documents with mathematical discrepancies are never silently approved.
- **Exact Decimal Arithmetic**: Uses Python `decimal.Decimal` with ₹2.00 rounding tolerance to eliminate floating-point calculation errors.
- **Cost & Privacy Controls**: Admin-controlled daily request limits, monthly token budgets, and an instant toggle for 100% local processing mode (disabling all third-party AI egress).

---

## 2. Technology Stack

- **Backend**: FastAPI, Python 3.11, Pydantic v2, SQLAlchemy 2.0, Alembic.
- **Frontend**: Next.js 14 (App Router), TypeScript, Tailwind CSS, Lucide Icons, Recharts (24 Application Routes).
- **AI & Agent Orchestration**: LangGraph, Google Gemini API (Primary), Groq API (Fallback), Local Regex/Heuristic Engine.
- **Document Processing**: PyMuPDF (`fitz`), `python-docx`, `openpyxl`, `Pillow`, PaddleOCR.
- **Database & Storage**: PostgreSQL 16 (QueuePool) & SQLite 3 (Dialect-routed fallback), Redis, MinIO S3, Qdrant.
- **Data Protection & Compliance**: DPDP Act 2023 consent lifecycle, GDPR export/forget-me, Tenant air-gap (`DISABLE_EXTERNAL_AI`).
- **DevOps & Monitoring**: Docker Compose (9 services with health checks), Prometheus, Grafana, Disaster Recovery Manager.

---

## 3. Windows PowerShell Quickstart

For local Windows 10/11 development, use the dedicated automation scripts:

| Script | Purpose |
|---|---|
| `.\setup.ps1` | Verifies Python, Node.js, npm, Docker; provisions virtual environment; installs dependencies; seeds initial database. |
| `.\start.ps1` | Launches local FastAPI and Next.js development servers (or `-Docker` for complete container stack). |
| `.\stop.ps1` | Gracefully terminates Docker containers and background development processes. |
| `.\test.ps1` | Runs the full Pytest automated test suite with verbose reporting. |
| `.\reset-dev.ps1` | Resets development database, regenerates synthetic invoices, and reseeds initial demo state. |

### Running the Test Suite
```powershell
powershell -ExecutionPolicy Bypass -File .\test.ps1
```

### Starting the Application
```powershell
powershell -ExecutionPolicy Bypass -File .\start.ps1
```

---

## 4. Docker Compose Deployment (9 Services)

To launch the complete enterprise containerized stack:

```bash
docker compose up --build -d
```

### Exposed Endpoints & Ports

| Service | Port | Description |
|---|---|---|
| **Next.js Web UI** | `http://localhost:3000` | Enterprise 10-page SaaS dashboard |
| **Grafana Dashboards** | `http://localhost:3001` | Live metrics & agent telemetry (`admin`/`admin`) |
| **FastAPI Backend** | `http://localhost:8000` | REST API & Swagger UI (`/docs`) |
| **Prometheus Server** | `http://localhost:9090` | System metrics & scrape targets |
| **MinIO Console** | `http://localhost:9001` | S3 Object storage browser (`minioadmin`/`minioadmin`) |
| **MinIO S3 API** | `http://localhost:9000` | S3-compatible document storage endpoint |
| **Qdrant Vector DB** | `http://localhost:6333` | Vector search REST API |
| **PostgreSQL** | `localhost:5432` | Relational database (`documind`/`documind_secure_password`) |
| **Redis** | `localhost:6379` | Celery message broker & cache |

---

## 5. Default Test Credentials

The database comes pre-seeded with synthetic enterprise records:

| Role | Email | Password |
|---|---|---|
| **Chief Administrator** | `admin@documind.ai` | `Password123!` |
| **Financial Reviewer** | `reviewer@documind.ai` | `Password123!` |

*(One-click demo buttons are available on the login page for instant authentication).*

---

## 6. Project Structure

```
documind-ai/
├── backend/
│   ├── app/
│   │   ├── api/v1/         # FastAPI endpoints (auth, docs, invoices, approvals, etc.)
│   │   ├── agents/         # LangGraph 9-Agent workflow & state definitions
│   │   ├── core/           # Config, security, logging, Celery
│   │   ├── database/       # SQLAlchemy engine & session management
│   │   ├── models/         # 27 normalized SQLAlchemy database models
│   │   ├── schemas/        # Strict Pydantic request/response schemas
│   │   ├── services/       # OCR, LLM failover, validation, duplicate & anomaly engines
│   │   └── main.py         # FastAPI application entrypoint
│   ├── tests/              # Pytest automated test suite (39/39 passing)
│   └── requirements.txt    # Backend Python dependencies
├── frontend/
│   ├── src/
│   │   ├── app/            # Next.js 14 App Router (All 24 full enterprise pages)
│   │   ├── components/     # UI components, layout shell, navigation
│   │   ├── lib/            # Typed API client, utility functions
│   │   └── types/          # Shared TypeScript type definitions
│   ├── package.json        # Frontend dependencies
│   └── tailwind.config.ts  # Dark navy & white design system configuration
├── infrastructure/
│   ├── docker/             # Dockerfile.backend & Dockerfile.frontend
│   └── monitoring/         # Prometheus scrape configuration & Grafana provisioning
├── evaluation/
│   ├── datasets/           # 50 Indian GST benchmark invoices + Phase 2 edge cases
│   ├── prompts/            # Promptfoo LLM prompt evaluation suite
│   └── AI_EVALUATION.md    # AI accuracy & retrieval benchmarks documentation
├── docs/                   # Architecture, Security, Database, and Release guides
├── scripts/                # Disaster recovery, installation verify, and synthetic scripts
├── docker-compose.yml      # Multi-container orchestration (9 services)
├── setup.ps1               # Automated Windows environment setup
├── start.ps1               # Development start script
├── stop.ps1                # Development stop script
├── test.ps1                # Automated test execution script
├── reset-dev.ps1           # Environment reset and reseeding script
└── README.md               # Master project documentation
```

---

## 7. Comprehensive Documentation & Release Package

- [Customer Installation & Deployment Guide](file:///docs/CUSTOMER_INSTALLATION_GUIDE.md)
- [Customer Pilot Onboarding Guide](file:///docs/PHASE_5I_CUSTOMER_PILOT_GUIDE.md)
- [Final Security Review](file:///docs/FINAL_SECURITY_REVIEW.md)
- [Final Database & Migration Review](file:///docs/FINAL_DATABASE_REVIEW.md)
- [Final Release Checklist](file:///docs/FINAL_RELEASE_CHECKLIST.md)
- [System Architecture](file:///docs/architecture/ARCHITECTURE.md)
- [AI Benchmark & Evaluation Report](file:///docs/AI_PERFORMANCE_BENCHMARK.md)
