# DocuMind AI

**Turn invoices and business documents into validated records your finance team can review, approve, and export.**

DocuMind AI brings document intake, invoice extraction, GST validation, and human approval into one workspace. Built for businesses, accountants, and GST practitioners, it gives reviewers the source evidence and calculation checks they need to resolve exceptions before posting records.

[Open DocuMind AI](https://documind.kizuna2026.workers.dev) · [Create an organization](https://documind.kizuna2026.workers.dev/register) · [Explore the API](https://automation-website-pyp9.onrender.com/docs)

## From upload to approval

1. **Upload a batch.** Drop in invoices, purchase orders, receipts, delivery challans, or contracts. The platform reads multi-page PDFs, images, Word documents, and Excel workbooks.
2. **Inspect extracted fields.** Review structured data alongside the OCR text, field-level evidence, and confidence scores.
3. **Resolve exceptions.** Check flagged totals, GST breakdowns, suspected duplicates, and unusual vendor spend. Add reviewer notes and approve records through the review queue.
4. **Export approved records.** Generate Excel or CSV exports, update vendor ledgers, and review monthly spend and supplier activity.

## What the nine agents do

| Stage | Responsibility |
| --- | --- |
| 1. Intake | Checks size and file signatures and computes a SHA-256 digest. |
| 2. OCR | Extracts text across pages and supported file types. |
| 3. Classification | Identifies the document category. |
| 4. Extraction | Produces schema-validated fields with evidence and confidence. |
| 5. Validation | Recalculates line items and checks CGST, SGST, IGST, and reverse-charge fields using decimal arithmetic and a configured INR 2.00 rounding tolerance. |
| 6. Duplicate detection | Checks the file digest, supplier GSTIN and invoice number, and similar dates and amounts. |
| 7. Anomaly detection | Flags nonstandard tax slabs and vendor spend above three times the vendor's median. |
| 8. Decision and approval | Evaluates the checks and routes exceptions for human review. |
| 9. Reporting and finalization | Saves approved records, updates vendor ledgers, and prepares exports. |

The processing pipeline uses Gemini as its primary AI provider and Groq as a fallback. Transient failures and rate limits trigger bounded retries and provider failover. When provider access is unavailable, a deterministic parser can fall back to layout and pattern matching. Set `DISABLE_EXTERNAL_AI` to keep documents out of external AI APIs.

## Finance workspace

| View | What you can do |
| --- | --- |
| Dashboard | Track spending, recent audit events, and agent processing status. |
| Invoices and bills | Filter documents by vendor, date, status, or confidence. |
| Approvals | Compare extracted fields with OCR text, inspect calculations, and record decisions. |
| Vendors and suppliers | Look up GSTIN, operating state, and spending history. |
| GST and tax reports | Review monthly expenses and supplier rankings, then export a filtered subset. |

## Security and privacy controls

- **Uploads.** A 10 MB file limit, binary signature checks, and UUID filenames restrict what enters storage. Files are stored in tenant-scoped directories with path containment checks.
- **Accounts and sessions.** Login, registration, and upload endpoints have rate limits. Access tokens expire after 30 minutes, and refresh tokens rotate.
- **Downloads.** Exports support authenticated downloads or signed, single-use links that expire after 60 seconds.
- **Browser protections.** The frontend uses DOMPurify for dynamic content and applies CSP, HSTS, and anti-framing headers.
- **Data rights.** The product includes consent flows, tenant data isolation, and APIs for data export and deletion.

## Run locally

On Windows, run the repository's setup and start scripts from PowerShell.

```powershell
powershell -ExecutionPolicy Bypass -File .\setup.ps1
powershell -ExecutionPolicy Bypass -File .\start.ps1
```

To start the containerized stack, run:

```bash
docker compose up --build -d
```

| Service | Local port |
| --- | --- |
| Web UI | 3000 |
| FastAPI and Swagger UI | 8000 |
| Grafana | 3001 |
| Prometheus | 9090 |
| MinIO console and S3 API | 9001 and 9000 |
| Qdrant | 6333 |
| PostgreSQL | 5432 |
| Redis | 6379 |

Create an organization to access a tenant workspace. For production deployments, replace development credentials and review any automatic administrator seeding before exposing the application.

### Run the tests

```powershell
& "backend\.venv\Scripts\python.exe" -m pytest backend/tests/ -v
& "backend\.venv\Scripts\python.exe" -m pytest backend/tests/test_security_hardening.py -v
```

The security suite covers login throttling, upload signature rejection, safe file paths, authentication on protected endpoints, and single-use export links.

## Architecture and deployment

| Layer | Technology |
| --- | --- |
| Web | Next.js 14 App Router, TypeScript, Tailwind CSS, Lucide, Recharts |
| API | FastAPI, Python 3.11, Pydantic v2, SQLAlchemy, Alembic, SlowAPI |
| Document processing | PyMuPDF, python-docx, openpyxl, Pillow, PureMagic, Filetype |
| Orchestration | LangGraph with Gemini, Groq, and a deterministic fallback |
| Storage and background jobs | PostgreSQL 16 or SQLite, Redis, MinIO, Qdrant, Celery |
| Hosting | Cloudflare Workers for the frontend and Render for the API |

The backend lives in `backend/app/`, with agents in `backend/app/agents/`, versioned endpoints in `backend/app/api/v1/`, and tests in `backend/tests/`. The web application lives in `frontend/src/`. Deployment configuration is in `worker.js`, `wrangler.jsonc`, and `docker-compose.yml`.

[Web app](https://documind.kizuna2026.workers.dev) · [API backend](https://automation-website-pyp9.onrender.com) · [Swagger UI](https://automation-website-pyp9.onrender.com/docs)

## Further reading

- [System architecture](docs/architecture/ARCHITECTURE.md)
- [Customer installation and deployment guide](docs/CUSTOMER_INSTALLATION_GUIDE.md)
- [Customer pilot onboarding guide](docs/PHASE_5I_CUSTOMER_PILOT_GUIDE.md)
- [Production readiness audit](docs/PRODUCTION_READINESS.md)
- [Security review](docs/FINAL_SECURITY_REVIEW.md)
- [AI performance benchmark](docs/AI_PERFORMANCE_BENCHMARK.md)
