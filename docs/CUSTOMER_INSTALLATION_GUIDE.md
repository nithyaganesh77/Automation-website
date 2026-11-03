# DOCUMIND AI — CUSTOMER-HOSTED INSTALLATION & DEPLOYMENT GUIDE

**Version:** 1.0.0 (Commercial Production Release)  
**Target Environments:** Windows 10/11 / Server 2022, Linux (Ubuntu 22.04 LTS / Debian 12 / RHEL 9), Docker Compose  
**Data Privacy Assurance:** Complete on-premise document storage and database retention under your control.

---

## 1. ARCHITECTURE OVERVIEW

DocuMind AI is architected to operate entirely within your organization's private network infrastructure:
- **Relational Data:** PostgreSQL 16 (or local SQLite for zero-dependency standalone installs).
- **Document Storage:** Local encrypted filesystem or S3-compatible MinIO object storage.
- **AI Inference:** Google Gemini API (`gemini-3.8-flash`) and Groq API (`qwen/qwen3.8-27b`) via Bring-Your-Own-Key (BYOK), or 100% offline deterministic processing mode.
- **Backend Services:** FastAPI asynchronous API server.
- **Frontend Portal:** Next.js 14 web application.

---

## 2. PREREQUISITES & SYSTEM REQUIREMENTS

### Minimum Hardware Requirements
| Resource | Minimum (Small Office) | Recommended (Enterprise Production) |
| :--- | :--- | :--- |
| **CPU** | 4 Cores (x86_64 or ARM64) | 8+ Cores |
| **RAM** | 8 GB | 16 GB - 32 GB |
| **Disk Space** | 20 GB SSD | 100+ GB NVMe SSD |
| **Network** | Outbound HTTPS (Ports 443) to Gemini/Groq APIs | Inbound Port 80/443 (Reverse Proxy) |

### Software Prerequisites
- **Python:** 3.11.x (tested on 3.11.9)
- **Node.js:** v20.x LTS or higher
- **Git:** 2.40+
- **Docker & Docker Compose** (for containerized deployments)

---

## 3. DEPLOYMENT OPTION A: DOCKER COMPOSE (RECOMMENDED)

The fastest and most isolated way to deploy DocuMind AI on Linux or Windows with Docker Desktop.

### Step 1: Clone the Repository
```bash
git clone https://github.com/nithyaganesh77/Automation-website.git documind-ai
cd documind-ai
```

### Step 2: Configure Environment Variables
Copy the production template:
```bash
cp .env.example .env
```
Edit `.env` with your secure production values:
```env
# Database Configuration (PostgreSQL container)
DATABASE_URL=postgresql+psycopg2://postgres:StrongProdPassword2026!@postgres:5432/documind_db

# Security & Authentication (Generate using: openssl rand -hex 32)
SECRET_KEY=generate_your_own_64_character_hex_secret_key_here
ENVIRONMENT=production
DEBUG=false

# Bring-Your-Own-Key AI Providers
GEMINI_API_KEY=your_google_gemini_api_key_here
GROQ_API_KEY=your_groq_api_key_here
AI_PRIMARY_PROVIDER=gemini
AI_FALLBACK_PROVIDER=groq
GEMINI_MODEL=gemini-3.8-flash
GROQ_MODEL=qwen/qwen3.8-27b

# Storage & Cache
STORAGE_TYPE=local
UPLOAD_DIR=/app/storage/uploads
REDIS_URL=redis://redis:6379/0
```

### Step 3: Launch Containers
```bash
docker compose up -d --build
```

### Step 4: Verify Deployment Health
Check running containers:
```bash
docker compose ps
```
Verify the API health check:
```bash
curl http://localhost:8000/health
```
Expected response:
```json
{
  "status": "healthy",
  "service": "DocuMind AI",
  "version": "1.0.0",
  "environment": "production",
  "database": {"status": "healthy", "dialect": "postgresql", "is_production": true}
}
```

Access the web portal at `http://localhost:3000`.

---

## 4. DEPLOYMENT OPTION B: WINDOWS BARE-METAL SERVER

For Windows Server 2019/2022 or Windows 11 workstation installations without Docker.

### Step 1: Run Automated Setup
Open an elevated PowerShell prompt:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\setup.ps1
```
This script automatically:
1. Detects Python 3.11 and Node.js.
2. Creates Python virtual environment in `backend\.venv`.
3. Installs backend dependencies.
4. Installs frontend npm packages in `frontend\`.
5. Builds the production Next.js application.

### Step 2: Configure Environment
Copy `.env.example` to `.env` and enter your AI API keys.
For standalone Windows setups, the system uses the high-performance local SQLite engine with PRAGMA foreign keys (`DATABASE_URL=sqlite:///./documind.db`).

### Step 3: Run Database Migrations
```powershell
cd backend
$env:PYTHONPATH="."
.\.venv\Scripts\alembic.exe upgrade head
cd ..
```

### Step 4: Start DocuMind AI Services
Run the production startup script:
```powershell
.\start.ps1
```
- Backend will listen on `http://127.0.0.1:8000`
- Frontend will listen on `http://localhost:3000`

---

## 5. DEPLOYMENT OPTION C: LINUX (UBUNTU / DEBIAN / RHEL)

### Step 1: Install System Packages
```bash
sudo apt update && sudo apt install -y python3.11 python3.11-venv python3-pip nodejs npm git postgresql postgresql-contrib redis-server
```

### Step 2: Configure PostgreSQL Database
```bash
sudo -u postgres psql -c "CREATE DATABASE documind_db;"
sudo -u postgres psql -c "CREATE USER documind WITH ENCRYPTED PASSWORD 'SecurePassword123!';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE documind_db TO documind;"
```

### Step 3: Setup Backend Virtual Environment
```bash
git clone https://github.com/nithyaganesh77/Automation-website.git /opt/documind
cd /opt/documind
python3.11 -m venv backend/.venv
source backend/.venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt
```

### Step 4: Configure Frontend
```bash
cd /opt/documind/frontend
npm install
npm run build
```

### Step 5: Setup Systemd Services
Create `/etc/systemd/system/documind-backend.service`:
```ini
[Unit]
Description=DocuMind AI Backend Daemon
After=network.target postgresql.service redis.service

[Service]
User=www-data
WorkingDirectory=/opt/documind/backend
Environment="PYTHONPATH=/opt/documind/backend"
EnvironmentFile=/opt/documind/.env
ExecStart=/opt/documind/backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

Create `/etc/systemd/system/documind-frontend.service`:
```ini
[Unit]
Description=DocuMind AI Frontend Portal
After=network.target

[Service]
User=www-data
WorkingDirectory=/opt/documind/frontend
ExecStart=/usr/bin/npm start -- -p 3000
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start services:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now documind-backend documind-frontend
```

---

## 6. BACKUP & DISASTER RECOVERY

### Automated Database Backup
Run the verified database backup script:
```bash
python scripts/db_audit_and_backup.py
```
This performs an atomic, online backup to `storage/backups/documind_backup_<timestamp>.db` and outputs SHA-256 verification hashes.

For PostgreSQL deployments:
```bash
pg_dump -U documind -h localhost documind_db > storage/backups/documind_pg_$(date +%Y%m%d_%H%M%S).sql
```

### Backup Schedule Recommendation
Set up a daily cron job:
```bash
0 2 * * * /opt/documind/backend/.venv/bin/python /opt/documind/scripts/db_audit_and_backup.py >> /var/log/documind_backup.log 2>&1
```

---

## 7. UPGRADE PROCEDURE

When a new version of DocuMind AI is released:
```bash
cd /opt/documind
# 1. Back up database first
python scripts/db_audit_and_backup.py

# 2. Pull updates
git pull origin main

# 3. Update dependencies
backend/.venv/bin/pip install -r backend/requirements.txt
cd frontend && npm install && npm run build && cd ..

# 4. Apply database schema migrations
cd backend && ./.venv/bin/alembic upgrade head && cd ..

# 5. Restart services
sudo systemctl restart documind-backend documind-frontend
```

---

## 8. TROUBLESHOOTING

| Symptom | Probable Cause | Corrective Action |
| :--- | :--- | :--- |
| **HTTP 502 Bad Gateway** | Backend daemon not started or crashed | Run `Get-Service` or `systemctl status documind-backend`. Inspect `uvicorn` logs. |
| **HTTP 402 Payment Required** | Monthly document limit reached | Check plan quota via `/api/v1/subscriptions/current` or upgrade subscription tier. |
| **OCR Text Extraction Empty** | Corrupt PDF or non-standard font encoding | Ensure `pymupdf` and `paddleocr` are installed. File is routed to OCR fallback automatically. |
| **AI Rate Limit (HTTP 429)** | Exceeded free-tier Gemini/Groq limits | System automatically fails over between Gemini and Groq. Check telemetry at `/api/v1/agents/dashboard-metrics`. |
| **Database Connection Refused** | PostgreSQL service stopped | Verify PostgreSQL service is active on port 5432. Standalone setups automatically fall back to SQLite. |

