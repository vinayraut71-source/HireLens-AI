"""
FastAPI application entrypoint.
PRD Section 8: API Endpoints under /api/v1 prefix.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.auth.router import router as auth_router
from app.users.router import router as users_router
from app.resumes.router import router as resumes_router
from app.jobs.router import router as jobs_router
from app.applications.router import router as applications_router
from app.analytics.router import router as analytics_router
from app.roadmap.router import router as roadmap_router
from app.recommendations.router import router as recommendations_router, discovery_router
from app.ai.router import router as ai_router
from app.infrastructure.router import router as infra_router
from app.job_sources.router import router as job_sources_router

app = FastAPI(
    title=settings.APP_NAME,
    description="HireLens AI API - Production Scaffolding",
    version=settings.APP_VERSION,
    openapi_url="/api/v1/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Register v1 Routers ---
app.include_router(auth_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(resumes_router, prefix="/api/v1")
app.include_router(jobs_router, prefix="/api/v1")
app.include_router(applications_router, prefix="/api/v1")
app.include_router(analytics_router, prefix="/api/v1")
app.include_router(roadmap_router, prefix="/api/v1")
app.include_router(recommendations_router, prefix="/api/v1")
app.include_router(discovery_router, prefix="/api/v1")
app.include_router(ai_router, prefix="/api/v1")
app.include_router(infra_router, prefix="/api/v1")
app.include_router(job_sources_router, prefix="/api/v1")


@app.get("/health", tags=["System Health"])
async def health_check():
    """System status check endpoint."""
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "version": settings.APP_VERSION,
    }
