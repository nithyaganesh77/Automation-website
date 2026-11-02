# DocuMind AI — System Architecture & Multi-Agent Orchestration

## 1. Executive Summary

DocuMind AI is an enterprise document intelligence and invoice automation SaaS platform. It combines a stateful **LangGraph** multi-agent pipeline with deterministic Python calculation engines to ingest, parse, classify, validate, cross-reference, and audit commercial business documents.

### Architectural Philosophy
1. **Zero Silent Approvals**: In financial systems, unverified AI outputs must never be written as approved ledger transactions.
2. **Deterministic Financial Math**: Decimal arithmetic (`decimal.Decimal`) enforces tax consistency, line item reconciliations, and GST component checks.
3. **Tenant Data Isolation**: Database queries enforce organization partition keys at the ORM layer, preventing cross-tenant data leakage.
4. **Resilient AI Layer**: Dynamic provider abstraction supporting Google Gemini 2.0 and OpenAI with deterministic rule-based offline fallbacks.

---

## 2. Multi-Agent Orchestration (LangGraph)

The core processing engine is built on LangGraph using a shared `DocuMindState` TypedDict.

```
       [ Upload Ingestion ]
                │
                ▼
   ┌────────────────────────┐
   │ Agent 1: Intake Agent  │ ──► MIME check, SHA-256 hash, exact hash duplicate
   └────────────────────────┘
                │
                ▼
   ┌────────────────────────┐
   │ Agent 2: OCR Agent     │ ──► Native PyMuPDF text & scanned layout extraction
   └────────────────────────┘
                │
                ▼
   ┌────────────────────────┐
   │ Agent 3: Classify Agent│ ──► Tax Invoice, PO, Receipt, Challan, Contract
   └────────────────────────┘
                │
                ▼
   ┌────────────────────────┐
   │ Agent 4: Extract Agent │ ──► Strict Pydantic JSON schema, line items, evidence
   └────────────────────────┘
                │
                ▼
   ┌────────────────────────┐
   │ Agent 5: Validate Agent│ ──► Deterministic GSTIN regex, line item math, tolerance
   └────────────────────────┘
                │
                ▼
   ┌────────────────────────┐
   │ Agent 6: Deduplication │ ──► Hash match, vendor invoice # match, fuzzy matching
   └────────────────────────┘
                │
                ▼
   ┌────────────────────────┐
   │ Agent 7: Anomaly Agent │ ──► Statistical supplier variance, non-standard tax rates
   └────────────────────────┘
                │
                ▼
   ┌────────────────────────┐
   │ Agent 8: Decision Node │ ──► Human-in-the-loop routing (APPROVED vs REVIEW)
   └────────────────────────┘
                │
                ▼
   ┌────────────────────────┐
   │ Agent 9: Finalization  │ ──► PostgreSQL storage, supplier ledger, accounting export
   └────────────────────────┘
```

### Agent Responsibilities
- **Agent 1 (Intake)**: Verifies file size, extension, computes SHA-256 cryptographic digest, and immediately queries for exact file collisions.
- **Agent 2 (OCR)**: Extracts native PDF text layers first using PyMuPDF (fitz); extracts structured page layouts with coordinates.
- **Agent 3 (Classification)**: Classifies document type with confidence scoring.
- **Agent 4 (Extraction)**: Extracts supplier, customer, dates, GSTINs, currency, line items, and taxes with field-level evidence citations.
- **Agent 5 (Validation)**: Validates mandatory fields, checks GSTIN checksums/formats, reconciles line item arithmetic, and compares subtotal + taxes against grand total within a configurable tolerance (e.g. ₹2.00).
- **Agent 6 (Duplicate Detection)**: Employs hierarchical matching (SHA-256 -> Supplier + Invoice Number -> Fuzzy date and amount similarity).
- **Agent 7 (Anomaly Detection)**: Flags invoices > 3x historical vendor spend, tax slabs deviating from standard GST (0%, 5%, 12%, 18%, 28%), or large round figures without tax itemization.
- **Agent 8 (Decision & Approval)**: Evaluates complete validation and anomaly state. Routes uncertain documents to human review.
- **Agent 9 (Reporting & Finalization)**: Persists approved invoices, updates vendor lifetime spend, and prepares Excel/CSV export ledgers.

---

## 3. Database Schema

DocuMind AI utilizes 24 normalized tables with UUID primary keys and organization-level foreign key isolation:
- `organizations`, `users`, `roles`, `permissions`, `organization_members`
- `documents`, `document_pages`, `extracted_fields`
- `invoices`, `invoice_line_items`, `suppliers`, `customers`, `purchase_orders`
- `validation_results`, `duplicate_matches`, `anomaly_findings`
- `agent_executions`, `workflow_checkpoints`
- `approval_requests`, `approval_history`
- `exports`, `audit_logs`, `notifications`, `organization_settings`

---

## 4. Security & Compliance
- **Authentication**: JWT with short-lived access tokens and refresh tokens.
- **Password Hashing**: Bcrypt with auto-salted rounds.
- **RBAC**: Multi-tenant roles (`Admin`, `Reviewer`, `Operator`, `Viewer`).
- **Prompt Injection Defense**: Document text is isolated and treated as untrusted data inputs.
