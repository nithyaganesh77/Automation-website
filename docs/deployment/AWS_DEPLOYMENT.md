# DocuMind AI — AWS Production Deployment Guide

This guide details the reference architecture and configuration steps for deploying DocuMind AI into Amazon Web Services (AWS) using containerized infrastructure, managed databases, and cloud object storage.

---

## 1. Reference Architecture

```
                       [ Route 53 (DNS) ]
                               │
                               ▼
               [ CloudFront CDN / S3 (Frontend) ]
                               │
                               ▼
                  [ Application Load Balancer ]
                               │
          ┌────────────────────┴────────────────────┐
          ▼                                         ▼
   [ ECS Task: API Backend ]              [ ECS Task: Celery Worker ]
   (FastAPI / Python 3.11)                (Asynchronous Document Pipeline)
          │                                         │
          ├────────────────────┬────────────────────┤
          ▼                    ▼                    ▼
   [ Amazon RDS Postgres ]   [ Amazon ElastiCache ]   [ Amazon S3 ]
   (Multi-AZ Database)       (Redis Broker & Cache)   (Encrypted Document Bucket)
```

---

## 2. Infrastructure Components

### A. Container Hosting: Amazon ECS (Fargate)
- **Cluster**: Deploy backend FastAPI tasks and Celery worker tasks on AWS Fargate serverless containers.
- **Service Configuration**:
  - `documind-api`: 2 vCPU, 4GB RAM per container task, auto-scaling on CPU > 70% or request count.
  - `documind-worker`: 2 vCPU, 4GB RAM per container task, auto-scaling based on SQS/Redis queue backlog.
- **Task Definition IAM Role**: Provide least-privilege IAM policy granting access to S3 document bucket and AWS Secrets Manager.

### B. Database: Amazon RDS for PostgreSQL
- **Engine**: PostgreSQL 16.
- **Instance Type**: `db.m6g.large` with Multi-AZ redundancy enabled.
- **Storage**: General Purpose SSD (gp3) with storage auto-scaling.
- **Encryption**: AWS KMS encryption at rest.

### C. In-Memory Broker: Amazon ElastiCache for Redis
- **Engine**: Redis 7.
- **Node Type**: `cache.m6g.large` with clustered replication enabled.

### D. File Storage: Amazon S3
- **Bucket**: `documind-documents-prod`
- **Security**: Default AES-256 / KMS encryption, Block Public Access enabled, Versioning enabled, and lifecycle policies moving older archives to S3 Glacier after 365 days.
- **Access**: Signed URLs for authorized frontend document downloads.

### E. Secrets Management: AWS Secrets Manager
- Store database credentials, JWT secret keys, and LLM API keys (`GEMINI_API_KEY`, `OPENAI_API_KEY`).
- Injected automatically as environment variables into ECS container tasks.

### F. Observability & Monitoring: Amazon CloudWatch & Managed Prometheus
- ECS container logs shipped to CloudWatch Logs group `/aws/ecs/documind`.
- Amazon Managed Service for Prometheus (AMP) scraping `/metrics` endpoint.
- Alarms configured for task CPU spikes, database connection exhaustion, and 5xx error rates.

---

## 3. Step-by-Step Deployment Runbook

### Step 1: Build & Push Docker Images to Amazon ECR
```bash
# Authenticate Docker to AWS ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <aws_account_id>.dkr.ecr.us-east-1.amazonaws.com

# Build and tag backend image
docker build -f infrastructure/docker/Dockerfile.backend -t documind-backend:latest .
docker tag documind-backend:latest <aws_account_id>.dkr.ecr.us-east-1.amazonaws.com/documind-backend:v1.0.0
docker push <aws_account_id>.dkr.ecr.us-east-1.amazonaws.com/documind-backend:v1.0.0

# Build and tag frontend image
docker build -f infrastructure/docker/Dockerfile.frontend -t documind-frontend:latest .
docker tag documind-frontend:latest <aws_account_id>.dkr.ecr.us-east-1.amazonaws.com/documind-frontend:v1.0.0
docker push <aws_account_id>.dkr.ecr.us-east-1.amazonaws.com/documind-frontend:v1.0.0
```

### Step 2: Provision RDS and Run Migrations
```bash
# Execute initial schema migration
export DATABASE_URL="postgresql://user:password@<rds-endpoint>:5432/documind_db"
python scripts/seed_db.py
```

### Step 3: Deploy ECS Service & Verify Health
```bash
# Check service health
curl -f https://api.documind.yourcompany.com/health
```

