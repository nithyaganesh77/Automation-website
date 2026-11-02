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
  2. **OCR Agent**: Multi-page text extraction with native PDF fallback (PyMuPDF) and scanned layout parsing.
  3. **Classification Agent**: Categorization into Tax Invoices, Purchase Orders, Receipts, Delivery Challans, and Contracts.
  4. **Extraction Agent**: Strict Pydantic JSON schema extraction with field-level evidence and confidence tracking.
  5. **Validation Agent**: Deterministic Python mathematical engine validating line items, tax breakdowns, and Indian GST rules.
  6. **Duplicate Detection Agent**: Multi-tier deduplication (exact hash -> supplier + invoice number -> fuzzy date/amount).
  7. **Anomaly Detection Agent**: Statistical vendor spend deviation and tax slab anomaly detection.
  8. **Decision & Approval Agent**: Evaluates pipeline results and orchestrates human-in-the-loop review.
  9. **Reporting and Finalization Agent**: Persists approved records, updates vendor ledgers, and generates Excel/CSV exports.
- **Zero Silent Approvals**: Unverified financial records are never silently approved or exported without validation and review.
- **Exact Decimal Arithmetic**: Uses `decimal.Decimal` for all currency calculations to prevent floating-point rounding errors.
- **Multi-Tenant Isolation**: Complete database-level isolation by organization ID.

---

## 2. Technology Stack

- **Frontend**: Next.js 14, TypeScript, Tailwind CSS, Lucide Icons, Recharts.
- **Backend**: FastAPI, Python 3.11, Pydantic v2, SQLAlchemy 2.0, Alembic.
- **AI & Agent Orchestration**: LangGraph, Google Gemini 2.0 API, OpenAI API (with deterministic offline fallback engine).
- **Document Processing**: PyMuPDF (`pymupdf`), `python-docx`, `openpyxl`, `Pillow`.
- **Database & Storage**: PostgreSQL, SQLite (local development), Redis, Celery.
- **DevOps & Monitoring**: Docker, Docker Compose, Prometheus metrics instrumentation, GitHub Actions CI.

---

## 3. Quickstart Guide

### Option A: Running with Docker Compose (Recommended)

1. Clone repository and start the complete local container stack:
```bash
docker compose up --build
```

2. Open the applications:
- **Frontend Dashboard**: [http://localhost:3000](http://localhost:3000)
- **FastAPI Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Prometheus Metrics**: [http://localhost:9090](http://localhost:9090)

---

### Option B: Running Locally

#### 1. Backend Setup (Python 3.11)
```bash
# From workspace root
uv venv --python 3.11 backend/.venv
# Or: python -m venv backend/.venv

# Activate virtual environment
# Windows:
backend\.venv\Scripts\activate
# Linux/Mac:
source backend/.venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Generate synthetic test documents
python scripts/generate_synthetic_invoices.py

# Seed database with sample organization and test documents
python scripts/seed_db.py

# Start FastAPI development server
uvicorn app.main:app --reload --port 8000
```

#### 2. Frontend Setup (Node.js 20+)
```bash
cd frontend
npm install
npm run dev
```

Navigate to [http://localhost:3000](http://localhost:3000) to access the platform.

---

## 4. Default Test Credentials

The database comes pre-seeded with synthetic enterprise records:

| Role | Email | Password |
|---|---|---|
| **Chief Administrator** | `admin@documind.ai` | `Password123!` |
| **Financial Reviewer** | `reviewer@documind.ai` | `Password123!` |

*(One-click demo buttons are available on the login page for instant authentication).*

---

## 5. Automated Test Suite

Run the complete backend test suite:
```bash
pytest backend/tests -v
```

Tests cover:
- User registration, authentication, JWT tokens, and RBAC permissions.
- Mathematical consistency, tax tolerance, and GSTIN checksum validation.
- Multi-tenant data isolation across organizations.
- LangGraph agent execution and dashboard metric generation.

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
│   │   ├── models/         # 24 normalized SQLAlchemy database models
│   │   ├── schemas/        # Strict Pydantic request/response schemas
│   │   ├── services/       # OCR, LLM abstraction, validation, duplicate & anomaly engines
│   │   └── main.py         # FastAPI application entrypoint
│   ├── tests/              # Pytest automated test suite
│   └── requirements.txt    # Backend Python dependencies
├── frontend/
│   ├── src/
│   │   ├── app/            # Next.js 14 App Router (All 10 full enterprise pages)
│   │   ├── components/     # UI components, layout shell, navigation
│   │   ├── lib/            # Typed API client, utility functions
│   │   └── types/          # Shared TypeScript type definitions
│   ├── package.json        # Frontend dependencies
│   └── tailwind.config.ts  # Dark navy & white design system configuration
├── infrastructure/
│   ├── docker/             # Dockerfile.backend & Dockerfile.frontend
│   └── monitoring/         # Prometheus scrape configuration
├── evaluation/
│   └── datasets/           # Synthetic test invoices (PDFs)
├── docs/                   # Architecture, API, Security, and AWS Deployment guides
├── scripts/                # Synthetic PDF generator & database seed scripts
├── docker-compose.yml      # Multi-container orchestration
└── README.md               # Master project documentation
```

---

## 7. License & Compliance
This software is built for enterprise commercial deployment with strict financial governance and data isolation.
