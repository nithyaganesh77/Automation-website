# DocuMind AI — Phase 5H Customer Installation & Deployment Guide

**Product**: DocuMind AI Enterprise Document Intelligence & Invoice Automation Platform  
**Version**: 1.0.0 Commercial Release  
**Audience**: IT Administrators, DevOps Engineers, Enterprise System Integrators  
**Date**: November 3, 2026

---

## 1. System Requirements & Architecture Overview

DocuMind AI can be deployed either as a **containerized multi-service Docker stack** or as a **native host deployment** on Windows Server and Linux (Ubuntu / Debian / RHEL).

```
                      +-----------------------------+
                      |   Reverse Proxy (Nginx)     |
                      |   Port 80/443 (TLS/SSL)     |
                      +--------------+--------------+
                                     |
               +---------------------+---------------------+
               |                                           |
               v                                           v
    +--------------------+                       +--------------------+
    | Next.js Frontend   |                       |  FastAPI Backend   |
    | (Port 3000)        |                       |  (Port 8000)       |
    +--------------------+                       +---------+----------+
                                                           |
          +------------------------------------------------+--------------------+
          |                       |                        |                    |
          v                       v                        v                    v
+------------------+    +-------------------+    +-------------------+  +---------------+
| PostgreSQL 16    |    | Redis 7 Cache     |    | Qdrant Vector DB  |  | MinIO Storage |
| (Port 5432)      |    | (Port 6379)       |    | (Port 6333)       |  | (Port 9000)   |
+------------------+    +-------------------+    +-------------------+  +---------------+
```

### 1.1 Minimum & Recommended Hardware

| Resource | Minimum (Small Office / Pilot) | Recommended (Enterprise Production) |
|---|---|---|
| **CPU** | 4 Cores (x86_64 or ARM64) | 8 Cores (3.0 GHz+) |
| **Memory** | 8 GB RAM | 16–32 GB RAM |
| **Disk** | 25 GB SSD | 100+ GB NVMe SSD |
| **Network** | 10 Mbps Internet (for Gemini/Groq APIs) | 100 Mbps Redundant Uplink |
| **Air-Gap Support**| Fully functional in `DISABLE_EXTERNAL_AI=True` | Fully functional in `DISABLE_EXTERNAL_AI=True` |

---

## 2. Environment Configuration (`.env`)

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Configure essential environment variables:

```ini
# --- Application Environment ---
ENVIRONMENT=production
DEBUG=false
APP_NAME="DocuMind AI"
API_V1_STR=/api/v1
SECRET_KEY=generate-a-strong-64-character-hex-string-using-openssl
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# --- Database Selection ---
# Production PostgreSQL (Standard):
DATABASE_URL=postgresql://documind_user:StrongPassword123@localhost:5432/documind_db
# Offline / Single-Host SQLite (Alternative):
# DATABASE_URL=sqlite:///./documind.db

# --- AI Providers (Zero Cost Tier / BYOK) ---
AI_PRIMARY_PROVIDER=gemini
AI_FALLBACK_PROVIDER=groq
GEMINI_API_KEY=your-gemini-api-key-here
GEMINI_MODEL=gemini-2.5-flash
GROQ_API_KEY=your-groq-api-key-here
GROQ_MODEL=openai/gpt-oss-120b

# --- Privacy & Air-Gap Mode ---
DISABLE_EXTERNAL_AI=false

# --- Storage Configuration ---
STORAGE_TYPE=local
UPLOAD_DIR=storage/uploads
MAX_FILE_SIZE_BYTES=10485760

# --- Vector Database & Cache (Optional / Docker) ---
QDRANT_HOST=localhost
QDRANT_PORT=6333
REDIS_HOST=localhost
REDIS_PORT=6379
```

---

## 3. Installation Method A: Docker Compose (Recommended)

### Step 1: Install Docker & Docker Compose
Ensure Docker Engine 24.0+ and Docker Compose v2 are running:
```bash
docker --version
docker compose version
```

### Step 2: Launch All Services
```bash
docker compose up -d
```
Docker will launch:
- `postgres` (PostgreSQL 16 Alpine on port 5432)
- `redis` (Redis 7 Alpine on port 6379)
- `qdrant` (Qdrant Vector Database on port 6333)
- `minio` (MinIO Object Storage on ports 9000 & 9001)
- `backend` (FastAPI application on port 8000)
- `frontend` (Next.js web application on port 3000)

### Step 3: Run Database Migrations
```bash
docker compose exec backend alembic upgrade head
```

---

## 4. Installation Method B: Native Host Deployment

### Linux (Ubuntu 22.04 LTS)

#### 1. System Packages
```bash
sudo apt update && sudo apt install -y python3-pip python3-venv nodejs npm postgresql postgresql-contrib
```

#### 2. PostgreSQL Setup
```bash
sudo -u postgres psql -c "CREATE USER documind_user WITH PASSWORD 'StrongPassword123';"
sudo -u postgres psql -c "CREATE DATABASE documind_db OWNER documind_user;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE documind_db TO documind_user;"
```

#### 3. Backend Setup
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
alembic upgrade head
```

#### 4. Frontend Setup
```bash
cd ../frontend
npm install
npm run build
```

#### 5. Process Management (systemd)
Create `/etc/systemd/system/documind-backend.service`:
```ini
[Unit]
Description=DocuMind AI Backend API
After=network.target postgresql.service

[Service]
User=ubuntu
WorkingDirectory=/opt/documind/backend
ExecStart=/opt/documind/backend/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

Create `/etc/systemd/system/documind-frontend.service`:
```ini
[Unit]
Description=DocuMind AI Next.js Frontend
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/opt/documind/frontend
ExecStart=/usr/bin/npm start
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now documind-backend documind-frontend
```

---

### Windows Host (PowerShell)

#### 1. Automated Setup
Execute the automated PowerShell setup script:
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1
```

#### 2. Start Application
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start.ps1
```

#### 3. Inspect Service Status
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\status.ps1
```

---

## 5. Automated Installation Verification

After installation, run the automated verification suite to validate all 9 operational layers:

```bash
python scripts/verify_customer_installation.py
```

### Verification Checklist:
- [x] Python 3.10+ runtime and OS environment
- [x] Docker Compose configuration and service definitions
- [x] Clean database schema initialization (all 27 tables present)
- [x] AI Provider API connectivity and failover check (Gemini & Groq)
- [x] Multi-tenant organization creation and Admin registration
- [x] Synthetic invoice upload, OCR parsing, and deterministic GST calculation
- [x] Excel accounting ledger export generation
- [x] Atomic database backup and restore verification
- [x] Commercial webhook HMAC signature verification

---

## 6. Disaster Recovery & Scheduled Backups

DocuMind AI includes an automated Disaster Recovery Manager (`scripts/disaster_recovery_manager.py`).

### 6.1 Creating an Immediate Backup
```bash
python scripts/disaster_recovery_manager.py backup
```
Backups are saved to `storage/backups/` with:
- Compressed atomic snapshot (`.db` or `.sql.gz`)
- Cryptographic SHA-256 integrity manifest (`.json`)
- Retention policy enforcement (automatic pruning of snapshots older than 30 days)

### 6.2 Restoring from Backup
```bash
python scripts/disaster_recovery_manager.py restore storage/backups/documind_backup_YYYYMMDD_HHMMSS.db
```

### 6.3 Scheduling Daily Backups
On Linux (crontab):
```bash
0 2 * * * /opt/documind/backend/.venv/bin/python /opt/documind/scripts/disaster_recovery_manager.py backup >> /var/log/documind_backup.log 2>&1
```

On Windows (Task Scheduler):
```powershell
$action = New-ScheduledTaskAction -Execute "D:\git\automation\backend\.venv\Scripts\python.exe" -Argument "D:\git\automation\scripts\disaster_recovery_manager.py backup"
$trigger = New-ScheduledTaskTrigger -Daily -At 2:00AM
Register-ScheduledTask -Action $action -Trigger $trigger -TaskName "DocuMind_Daily_Backup" -Description "Daily atomic backup for DocuMind AI"
```

---

## 7. Troubleshooting & Support

| Symptom | Cause | Solution |
|---|---|---|
| **Port 5432 Connection Refused** | PostgreSQL service stopped or blocked | Start PostgreSQL service or run Docker Compose (`docker compose up -d postgres`). Alternatively set `DATABASE_URL=sqlite:///./documind.db`. |
| **HTTP 400: Customer Consent Missing** | Missing consent checkbox on upload | Pass `customer_consent=true` in multipart form payload or tick the consent checkbox in the UI. |
| **HTTP 402: Usage Quota Exceeded** | Subscription monthly document limit hit | Upgrade subscription tier via `/api/v1/subscriptions/upgrade` or from Billing settings. |
| **401 Unauthorized on API calls** | Missing or expired JWT bearer token | Authenticate via `/api/v1/auth/login` to obtain a fresh access token. |

