# DocuMind AI — PostgreSQL Production & Disaster Recovery Manual

## 1. Executive Overview

This document details the enterprise production deployment, backup strategies, tenant isolation guarantees, and disaster recovery procedures for **DocuMind AI** running on PostgreSQL 16.

DocuMind AI is architected with a multi-tenant database model where every table containing tenant data enforces an indexed `organization_id` column. Production deployments run with PostgreSQL configured with connection pooling (`QueuePool`), transactional isolation (`READ COMMITTED`), and automated WAL / snapshot backups.

---

## 2. Production Connection Pooling & Architecture

DocuMind AI utilizes SQLAlchemy 2.0 with the `psycopg2` driver configured as follows:

| Parameter | Value | Rationale |
| :--- | :--- | :--- |
| **Engine Dialect** | `postgresql+psycopg2://` | High-performance C-extension driver with native binary support |
| **Pool Class** | `sqlalchemy.pool.QueuePool` | Thread-safe connection queue preventing database socket starvation |
| **Pool Size** | `20` | Baseline persistent connection pool for concurrent FastAPI workers |
| **Max Overflow** | `10` | Elastic burst capacity during heavy batch document ingestion |
| **Pool Timeout** | `30 seconds` | Prevents indefinite thread hanging during spike traffic |
| **Pool Recycle** | `1,800 seconds` (30m) | Proactively closes stale connections before firewall timeouts |
| **Pool Pre-Ping** | `True` | Executes `SELECT 1` ping before hand-off, eliminating stale socket errors |
| **Isolation Level** | `READ COMMITTED` | Ensures transactional consistency without phantom dirties |

---

## 3. Database Deployment & Service Initialization

### 3.1 Docker Compose Deployment (Recommended)
```bash
# Start PostgreSQL service with health check
docker-compose up -d postgres

# Check container status
docker-compose ps postgres

# View PostgreSQL runtime logs
docker-compose logs -f postgres
```

### 3.2 Linux Native Service (Ubuntu / Debian / RHEL)
```bash
# Ubuntu / Debian
sudo systemctl enable postgresql
sudo systemctl start postgresql
sudo systemctl status postgresql

# Create DocuMind user and database
sudo -u postgres psql -c "CREATE USER postgres WITH PASSWORD 'postgres';"
sudo -u postgres psql -c "CREATE DATABASE documind_db OWNER postgres;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE documind_db TO postgres;"
```

---

## 4. Multi-Tenant Data Isolation Guarantees

DocuMind AI enforces tenant isolation through application-layer scoping and foreign key constraints:

1. **Foreign Key Constraints**: All child entities (`documents`, `invoices`, `suppliers`, `subscriptions`, `audit_logs`) reference `organizations(id)` with `ON DELETE CASCADE`.
2. **Query Scoping**: All API dependencies (`get_current_active_user`) inject the authenticated user's `organization_id`. All repository queries append `.filter(Model.organization_id == current_user.organization_id)`.
3. **Cross-Tenant Verification**: Automated test suites in `scripts/test_postgres_production_cycle.py` verify that SQL statements compiled by SQLAlchemy strictly contain `organization_id = '<current_org_id>'`.

---

## 5. Automated Backup Procedures

DocuMind AI supports two automated backup methods: custom binary archive format (`-F c`) and compressed SQL streams (`gzip`).

### 5.1 Native Backup (`pg_dump`)
```bash
# Set credentials
export PGPASSWORD="your_secure_password"

# Generate compressed custom binary backup
pg_dump -h localhost \
        -p 5432 \
        -U postgres \
        -d documind_db \
        -F c \
        -b \
        -v \
        -f "/opt/documind/storage/backups/documind_$(date +%Y%m%d_%H%M%S).dump"
```

### 5.2 Docker Container Backup
```bash
# Execute within Docker container
docker exec -t documind-postgres pg_dump -U postgres documind_db | \
  gzip > /opt/documind/storage/backups/documind_$(date +%Y%m%d_%H%M%S).sql.gz
```

### 5.3 Daily Automated Cron Job
Add to `/etc/cron.d/documind_backup`:
```cron
# Daily backup at 02:00 AM UTC with 30-day retention
0 2 * * * root /usr/local/bin/documind_daily_backup.sh >> /var/log/documind_backup.log 2>&1
```

Script `/usr/local/bin/documind_daily_backup.sh`:
```bash
#!/bin/bash
set -euo pipefail

BACKUP_DIR="/opt/documind/storage/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/documind_${TIMESTAMP}.dump"

mkdir -p "${BACKUP_DIR}"

docker exec -t documind-postgres pg_dump -U postgres -d documind_db -F c -b -f "/tmp/backup.dump"
docker cp documind-postgres:/tmp/backup.dump "${BACKUP_FILE}"
docker exec -t documind-postgres rm /tmp/backup.dump

# Delete backups older than 30 days
find "${BACKUP_DIR}" -type f -name "documind_*.dump" -mtime +30 -delete

echo "[$(date)] Backup completed successfully: ${BACKUP_FILE}"
```

---

## 6. Complete Disaster Recovery & Restoration Procedure

In the event of database corruption, accidental deletion, or server failure, follow this exact recovery playbook:

### Step 1: Stop Application Ingestion
Prevent new incoming document processing during restoration:
```bash
docker-compose stop backend celery-worker
```

### Step 2: Validate Backup Archive Integrity
```bash
# Check archive file size and header
ls -lh /opt/documind/storage/backups/documind_20261103_090000.dump
pg_restore --list /opt/documind/storage/backups/documind_20261103_090000.dump | head -n 25
```

### Step 3: Terminate Active Database Connections
```sql
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = 'documind_db'
  AND pid <> pg_backend_pid();
```

### Step 4: Drop and Recreate Clean Database
```bash
# Using psql
sudo -u postgres psql -c "DROP DATABASE IF EXISTS documind_db;"
sudo -u postgres psql -c "CREATE DATABASE documind_db OWNER postgres;"
```

### Step 5: Execute pg_restore
```bash
# Restore custom binary archive
pg_restore -h localhost \
           -p 5432 \
           -U postgres \
           -d documind_db \
           -v \
           --clean \
           --if-exists \
           /opt/documind/storage/backups/documind_20261103_090000.dump
```

If restoring from a compressed SQL stream (`.sql.gz`):
```bash
gunzip -c /opt/documind/storage/backups/documind_20261103_090000.sql.gz | \
  docker exec -i documind-postgres psql -U postgres -d documind_db
```

### Step 6: Verify Database Integrity Post-Restore
```bash
# Execute validation query
docker exec -it documind-postgres psql -U postgres -d documind_db -c "
  SELECT 
    (SELECT COUNT(*) FROM organizations) AS organizations_count,
    (SELECT COUNT(*) FROM users) AS users_count,
    (SELECT COUNT(*) FROM documents) AS documents_count,
    (SELECT COUNT(*) FROM invoices) AS invoices_count;
"
```

### Step 7: Restart Application Services
```bash
docker-compose up -d backend frontend celery-worker
docker-compose logs -f backend
```

---

## 7. Migration Verification Playbook (Alembic)

When upgrading DocuMind AI versions:
```bash
# Run latest migrations
docker exec -it documind-backend alembic upgrade head

# Inspect current revision
docker exec -it documind-backend alembic current

# Inspect migration history
docker exec -it documind-backend alembic history
```

---

## 8. Summary Checklist for Pilot Businesses

| Verification Item | Pilot Target | Status |
| :--- | :--- | :--- |
| Database Engine | PostgreSQL 16 Alpine | Validated in Docker Compose |
| Connection Pool | 20 persistent, 10 overflow | Validated via QueuePool audit |
| Tenant Isolation | Row-level org scoping | Validated via AST inspection |
| Automated Backups | Daily cron + 30-day rotation | Script template verified |
| Restore Protocol | Tested `< 5 min` RTO | Playbook documented |
| Data Integrity Check | Relational integrity & FKs | Zero orphan records enforced |

