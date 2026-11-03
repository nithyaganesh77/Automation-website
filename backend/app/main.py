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

# Initialize FastAPI Application
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Enterprise Multi-Agent Business Document Intelligence and Invoice Automation SaaS",
    docs_url="/docs",
    redoc_url="/redoc"
)

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
    
    return response


@app.on_event("startup")
def on_startup():
    logger.info("Initializing DocuMind AI database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("DocuMind AI application startup complete.")


# Health Check Endpoints
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

