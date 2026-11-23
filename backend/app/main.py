import time
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

from app.core.config import settings
from app.core.logging import logger
from app.database.session import engine, Base, check_db_health
import app.models  # Ensure all models are registered

# API Routers
from app.api.v1.auth import router as auth_router
from app.api.v1.documents import router as documents_router
from app.api.v1.invoices import router as invoices_router
from app.api.v1.approvals import router as approvals_router
from app.api.v1.suppliers import router as suppliers_router
from app.api.v1.agents import router as agents_router
from app.api.v1.reports import router as reports_router
from app.api.v1.settings import router as settings_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.onboarding import router as onboarding_router
from app.api.v1.subscriptions import router as subscriptions_router
from app.api.v1.super_admin import router as super_admin_router
from app.api.v1.compliance import router as compliance_router
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.core.rate_limit import limiter

# Initialize FastAPI Application
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Enterprise Multi-Agent Business Document Intelligence and Invoice Automation SaaS",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Register Slowapi Rate Limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus Metrics
REQUEST_COUNT = Counter("documind_http_requests_total", "Total HTTP requests", ["method", "endpoint", "status"])
REQUEST_LATENCY = Histogram("documind_http_request_duration_seconds", "HTTP request latency in seconds", ["endpoint"])


@app.middleware("http")
async def prometheus_metrics_and_logging_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    endpoint = request.url.path
    status_code = response.status_code

    REQUEST_COUNT.labels(method=request.method, endpoint=endpoint, status=status_code).inc()
    REQUEST_LATENCY.labels(endpoint=endpoint).observe(duration)
    
    # Security Response Headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    return response


@app.on_event("startup")
def on_startup():
    logger.info("Initializing DocuMind AI database tables...")
    Base.metadata.create_all(bind=engine)
    
    # Auto-seed default Admin and Reviewer if missing (ensures survival across container restarts)
    try:
        from app.database.session import SessionLocal
        from app.models.all_models import User, Organization, OrganizationMember, OrganizationSetting
        from app.core.security import hash_password

        db = SessionLocal()
        try:
            admin = db.query(User).filter(User.email == "admin@documind.ai").first()
            if not admin:
                org = db.query(Organization).filter(Organization.slug == "documind-hq").first()
                if not org:
                    org = Organization(
                        name="DocuMind HQ",
                        slug="documind-hq",
                        legal_name="DocuMind Technologies Private Limited",
                        gstin="29AAAAA0000A1Z5",
                        onboarding_completed=True,
                        onboarding_step="COMPLETE"
                    )
                    db.add(org)
                    db.flush()
                    org_setting = OrganizationSetting(
                        organization_id=org.id,
                        ai_provider="gemini",
                        currency="INR"
                    )
                    db.add(org_setting)

                admin = User(
                    email="admin@documind.ai",
                    hashed_password=hash_password("Password123!"),
                    full_name="Alex Mercer (Chief Admin)",
                    is_active=True,
                    is_superuser=True
                )
                db.add(admin)
                db.flush()

                member = OrganizationMember(
                    organization_id=org.id,
                    user_id=admin.id,
                    role="Admin"
                )
                db.add(member)

            reviewer = db.query(User).filter(User.email == "reviewer@documind.ai").first()
            if not reviewer:
                org = db.query(Organization).filter(Organization.slug == "documind-hq").first()
                if org:
                    reviewer = User(
                        email="reviewer@documind.ai",
                        hashed_password=hash_password("Password123!"),
                        full_name="Sarah Jenkins (Financial Reviewer)",
                        is_active=True,
                        is_superuser=False
                    )
                    db.add(reviewer)
                    db.flush()
                    member = OrganizationMember(
                        organization_id=org.id,
                        user_id=reviewer.id,
                        role="Reviewer"
                    )
                    db.add(member)

            db.commit()
            logger.info("Admin and Reviewer default accounts verified.")
        except Exception as seed_err:
            db.rollback()
            logger.error(f"Error seeding accounts on startup: {seed_err}")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Startup seeding error: {e}")

    logger.info("DocuMind AI application startup complete.")


# Health Check Endpoints
@app.get("/", tags=["Health"])
def root():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "docs_url": "/docs",
        "health_url": "/health"
    }


@app.get("/health", tags=["Health"])
def health_check():
    db_health = check_db_health()
    return {
        "status": "healthy" if db_health.get("status") == "healthy" else "degraded",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "database": db_health
    }


@app.get("/ready", tags=["Health"])
def readiness_check():
    try:
        # Check DB connectivity
        with engine.connect() as conn:
            conn.execute(Base.metadata.tables["organizations"].select().limit(1))
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not_ready", "error": str(e)}
        )


@app.get("/metrics", tags=["Monitoring"])
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


# Register API V1 Routers
app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(documents_router, prefix=settings.API_V1_PREFIX)
app.include_router(invoices_router, prefix=settings.API_V1_PREFIX)
app.include_router(approvals_router, prefix=settings.API_V1_PREFIX)
app.include_router(suppliers_router, prefix=settings.API_V1_PREFIX)
app.include_router(agents_router, prefix=settings.API_V1_PREFIX)
app.include_router(reports_router, prefix=settings.API_V1_PREFIX)
app.include_router(settings_router, prefix=settings.API_V1_PREFIX)
app.include_router(notifications_router, prefix=settings.API_V1_PREFIX)
app.include_router(onboarding_router, prefix=settings.API_V1_PREFIX)
app.include_router(subscriptions_router, prefix=settings.API_V1_PREFIX)
app.include_router(super_admin_router, prefix=settings.API_V1_PREFIX)
app.include_router(compliance_router, prefix=settings.API_V1_PREFIX)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

