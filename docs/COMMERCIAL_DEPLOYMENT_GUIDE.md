# DOCUMIND AI — COMMERCIAL SAAS DEPLOYMENT & PRODUCTION HARDENING GUIDE

**Audience:** Platform Architects, Site Reliability Engineers, DevOps Teams, Commercial SaaS Operators  
**Release Target:** DocuMind AI v1.0.0 Commercial SaaS  
**Compliance Standard:** Indian Digital Personal Data Protection (DPDP) Act 2023, ISO/IEC 27001, SOC 2 Type II baseline  

---

## 1. PRODUCTION TOPOLOGY & INFRASTRUCTURE

DocuMind AI is architected as a decoupled, multi-tenant cloud application with zero shared storage state across tenants:

```mermaid
flowchart TD
    Client["HTTPS Web Clients\n& Accounting Integrations"] --> ReverseProxy["Nginx / Traefik SSL Proxy\n(TLS 1.3, HSTS, Rate Limiting)"]
    ReverseProxy --> NextJS["Next.js 14 Frontend Cluster\n(Port 3000)"]
    ReverseProxy --> FastAPI["FastAPI Application Cluster\n(Port 8000 / Uvicorn Gunicorn)"]
    FastAPI --> PgBouncer["PgBouncer Connection Pooler"]
    PgBouncer --> PostgreSQL["PostgreSQL 16 High-Availability\n(Multi-AZ Primary + Read Replica)"]
    FastAPI --> Redis["Redis 7 Cluster\n(Rate Limiting & Celery Task Queue)"]
    FastAPI --> Celery["Celery Distributed Workers\n(PaddleOCR & Document Ingestion)"]
    FastAPI --> Storage["S3 / MinIO Object Storage\n(Encrypted at rest AES-256)"]
    FastAPI --> Qdrant["Qdrant Vector DB\n(Document Semantics & Deduplication)"]
    FastAPI --> Gemini["Google Gemini 3.8 Flash\n(Primary Structured Extraction)"]
    FastAPI --> Groq["Groq Qwen 3.8 27B\n(Sub-second Fallback LLM)"]
```

---

## 2. PRODUCTION HARDENING SPECIFICATIONS

### A. Database Connection Pooling & Tuning
In `backend/app/database/session.py`, production parameters must be configured in environment variables:
```env
DATABASE_URL=postgresql+psycopg2://documind_app:ComplexPassword2026!@pgbouncer.internal:6432/documind_prod
```
- **Connection Pool Size:** 20 connections per Uvicorn worker process.
- **Max Overflow:** 10 connections.
- **Pool Timeout:** 30 seconds.
- **Pool Recycle:** 1,800 seconds (prevents stale TCP connections).
- **Transaction Isolation:** `READ COMMITTED`.
- **Pre-Ping:** `True` (automatically purges dropped or closed connections).

### B. High-Availability Celery Distributed Background Processing
In production, documents are queued through Redis to avoid blocking user HTTP workers:
```bash
celery -A app.core.celery_app worker --loglevel=INFO --concurrency=4 -Q document_intake,ocr_processing,accounting_export
```

### C. Nginx Reverse Proxy with SSL Hardening
```nginx
server {
    listen 443 ssl http2;
    server_name app.documind.ai;

    ssl_certificate /etc/letsencrypt/live/app.documind.ai/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/app.documind.ai/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-eval' 'unsafe-inline'; img-src 'self' data: https:; style-src 'self' 'unsafe-inline';" always;

    # Frontend UI Route
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Backend API Route
    location /api/v1/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        client_max_body_size 25M;
    }
}
```

---

## 3. COMMERCIAL SUBSCRIPTION & BILLING INTEGRATION

DocuMind AI provides three tiered plans enforced at the API layer:

| Plan Tier | Monthly Price | Monthly Documents | Max Users | Anomaly Detection | SLA |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Starter** | ₹2,499 / mo | 50 docs | 3 users | Standard duplicate checks | Best effort |
| **Professional** | ₹9,999 / mo | 500 docs | 15 users | Statistical vendor baseline | 99.5% uptime |
| **Enterprise** | ₹29,999 / mo | 5,000+ docs | 100 users | Advanced compliance audit | 99.9% uptime |

### Quota Enforcement Architecture
- In `backend/app/services/subscription_service.py`, `check_upload_quota()` gates all uploads.
- When an organization exceeds its quota or a trial expires, the API strictly returns `HTTP 402 Payment Required`.
- **Prepared for Razorpay:** Table `subscriptions` includes `razorpay_customer_id` and `razorpay_subscription_id`. When commercial activation begins, a webhook listener in `backend/app/api/v1/subscriptions.py` updates the status from `TRIAL` to `ACTIVE` upon payment confirmation.

---

## 4. MULTI-TENANT ISOLATION GUARANTEES

1. **Foreign Key Scoping:** All financial tables (`documents`, `invoices`, `suppliers`, `exports`, `audit_logs`) carry `organization_id` foreign keys indexed with `ondelete="CASCADE"`.
2. **Context-Enforced Queries:** The `get_current_user_context` dependency validates JWT claims against the `organization_members` table on every authenticated call.
3. **Cross-Tenant Guard:** All database read/write queries explicitly scope to `auth_ctx.organization_id`.
4. **Storage Segregation:** Document paths on disk are partitioned as `storage/uploads/{organization_id}/{uuid}.pdf`.

---

## 5. MONITORING, ALERTING & SLA

- **Prometheus Metrics:** Available at `GET /metrics`. Tracks HTTP request rates, latency distributions, and Celery queue lengths.
- **Grafana OSS Dashboard:** Pre-configured dashboard template in `monitoring/grafana/dashboards/documind_saas.json`.
- **Health & Readiness Probes:**
  - Liveness: `GET /health` (returns database health and provider availability).
  - Readiness: `GET /ready` (tests database query execution).

