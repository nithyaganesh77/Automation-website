# DocuMind AI — REST API Reference

Interactive Swagger documentation is available at `/docs` when running the backend service.

## Base URL
`/api/v1`

---

## 1. Authentication
- `POST /api/v1/auth/register`: Create organization tenant and admin account.
- `POST /api/v1/auth/login`: Authenticate and obtain JWT access & refresh tokens.
- `POST /api/v1/auth/refresh`: Refresh expired JWT access token.
- `POST /api/v1/auth/forgot-password`: Request password reset instructions.
- `GET /api/v1/auth/me`: Get current authenticated user profile and organization.

---

## 2. Documents
- `POST /api/v1/documents/upload`: Upload document and execute LangGraph multi-agent pipeline.
- `POST /api/v1/documents/bulk-upload`: Batch upload multiple files simultaneously.
- `GET /api/v1/documents`: List documents with search, pagination, status and type filters.
- `GET /api/v1/documents/{id}`: Detailed document dossier including pages, extracted fields, line items, validations, duplicates, anomalies, and agent execution traces.
- `DELETE /api/v1/documents/{id}`: Soft/hard delete document and records.
- `POST /api/v1/documents/{id}/reprocess`: Trigger re-execution of AI agents.
- `GET /api/v1/documents/{id}/download`: Download raw uploaded document file.

---

## 3. Invoices
- `GET /api/v1/invoices`: List parsed invoices with vendor and date filters.
- `GET /api/v1/invoices/{id}`: Detailed invoice entity with line items and tax reconciliation.
- `PATCH /api/v1/invoices/{id}`: Correct extracted invoice values, line items, and trigger automatic deterministic revalidation.
- `GET /api/v1/invoices/{id}/validation`: Retrieve validation findings for invoice.

---

## 4. Approvals
- `GET /api/v1/approvals`: List documents awaiting human review.
- `POST /api/v1/approvals/{id}/approve`: Approve invoice for accounting export with audit comment.
- `POST /api/v1/approvals/{id}/reject`: Reject invoice with mandatory reviewer reason.

---

## 5. Suppliers
- `GET /api/v1/suppliers`: Directory of suppliers with cumulative spend and invoice counts.
- `POST /api/v1/suppliers`: Register verified supplier profile and GSTIN.
- `PATCH /api/v1/suppliers/{id}`: Update supplier contact and tax details.

---

## 6. AI Agent Telemetry
- `GET /api/v1/agents`: Health status, run counts, failure rates, and avg latencies for all 9 agents.
- `GET /api/v1/agents/executions`: Execution traces with latency ms, tokens used, and cost USD.
- `GET /api/v1/agents/executions/{id}`: Full input/output JSON payload inspection.

---

## 7. Reports & Exports
- `GET /api/v1/reports/dashboard`: Executive KPI counts, expense trajectories, and distribution graphs.
- `GET /api/v1/reports/expenses`: Monthly expense totals and GST accumulation.
- `GET /api/v1/reports/suppliers`: Vendor spend concentration ranking.
- `POST /api/v1/exports`: Generate accounting report in Excel (`.xlsx`) or CSV format.
- `GET /api/v1/exports/{id}/download`: Download generated report.

---

## 8. Settings & Governance
- `GET /api/v1/settings`: Fetch AI provider and financial tolerance thresholds.
- `PATCH /api/v1/settings`: Update Gemini/OpenAI API keys, rounding tolerances, confidence thresholds.
- `GET /api/v1/settings/audit-logs`: Immutable log of all system and user operations.
- `GET /api/v1/notifications`: In-app reviewer alerts and task notifications.
