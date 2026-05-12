"""
Main FastAPI application for NexusAI.
Entry point that sets up the app with all routes, middleware, and configuration.
"""

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging
import time
from datetime import datetime

from sqlalchemy import text
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from backend.app.core import settings
from backend.app.core.database import init_db, close_db, engine
from backend.app.core.rate_limit import limiter
from backend.app.services.redis_client import close_redis, init_redis

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

if settings.sentry_dsn:
    import sentry_sdk

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.environment,
        traces_sample_rate=0.05,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Async context manager for app startup and shutdown.
    Handles initialization and cleanup of resources.
    """
    # Startup
    logger.info("⚙️  NexusAI Backend Startup")
    try:
        await init_db()
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}")
        raise

    await init_redis()

    yield

    # Shutdown
    logger.info("⚙️  NexusAI Backend Shutdown")
    try:
        await close_redis()
        await close_db()
        logger.info("✅ Database connection closed")
    except Exception as e:
        logger.error(f"❌ Error during shutdown: {e}")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Enterprise AI-powered code editor and assistant",
    lifespan=lifespan,
    debug=settings.debug,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# ======================== MIDDLEWARE ========================

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_credentials,
    allow_methods=settings.cors_methods,
    allow_headers=settings.cors_headers,
)

# Trusted Host Middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.example.com"]
)


@app.middleware("http")
async def add_request_logging(request: Request, call_next):
    """Log all incoming requests and their processing time."""
    start_time = time.time()
    request.state.start_time = start_time

    try:
        response = await call_next(request)
        process_time = time.time() - start_time

        response.headers["X-Process-Time"] = str(process_time)

        logger.info(
            f"{request.method} {request.url.path} - "
            f"Status: {response.status_code} - "
            f"Time: {process_time:.3f}s"
        )

        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            f"{request.method} {request.url.path} - "
            f"Error: {str(e)} - "
            f"Time: {process_time:.3f}s"
        )
        raise


@app.middleware("http")
async def add_request_context(request: Request, call_next):
    """Add useful context to requests."""
    request.state.ip_address = request.client.host if request.client else "unknown"
    request.state.user_agent = request.headers.get("user-agent", "unknown")
    response = await call_next(request)
    return response


# ======================== EXCEPTION HANDLERS ========================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.utcnow().isoformat(),
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.debug else "An unexpected error occurred",
            "timestamp": datetime.utcnow().isoformat(),
        }
    )


# ======================== ROOT ENDPOINTS ========================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.app_version,
        "environment": settings.environment,
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/health/live")
async def health_live():
    """Liveness probe: process is up (use for load balancers / orchestrators)."""
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/health/ready")
async def health_ready():
    """Readiness probe: verify database connectivity before receiving traffic."""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {
            "status": "ready",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.warning("Readiness check failed: %s", e)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "not_ready",
                "database": "disconnected",
                "detail": str(e) if settings.debug else "Database unavailable",
                "timestamp": datetime.utcnow().isoformat(),
            },
        )


@app.get("/docs-json")
async def get_openapi():
    """Get OpenAPI schema."""
    return app.openapi()


# ======================== INCLUDE ROUTERS ========================

# Import all API v2 routers
from backend.app.api.v2 import (
    api_keys,
    audit_logs,
    auth,
    chat,
    code_execution,
    files,
    git,
    organizations,
    projects,
    session,
    usage_metrics,
    webhooks,
    websocket,
)

# Include routers
app.include_router(auth.router)
app.include_router(organizations.router)
app.include_router(webhooks.router)
app.include_router(api_keys.router)
app.include_router(audit_logs.router)
app.include_router(usage_metrics.router)
app.include_router(projects.router)
app.include_router(files.router)
app.include_router(git.router)
app.include_router(code_execution.router)
app.include_router(session.router)
app.include_router(chat.router)
app.include_router(websocket.router)

logger.info("✅ API v2 routers registered successfully")


@app.get("/")
async def api_developer_index():
    """
    API discovery for developers: links to docs, health, and the versioned API surface.
    """
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "documentation": {
            "swagger_ui": "/docs",
            "redoc": "/redoc",
            "openapi_json": "/openapi.json",
        },
        "health": {
            "summary": "/health",
            "liveness": "/health/live",
            "readiness": "/health/ready",
        },
        "api": {
            "version": "v2",
            "base_path": "/api/v2",
            "capabilities": [
                "authentication",
                "organizations",
                "webhooks",
                "api_keys",
                "audit_logs",
                "usage_metrics",
                "projects",
                "files",
                "git",
                "code_execution",
                "session",
                "chat",
                "websocket",
            ],
        },
    }


# ======================== STATIC FILES ========================

# Mount static files (frontend build)
try:
    app.mount("/static", StaticFiles(directory="frontend/dist"), name="static")
    logger.info("✅ Static files mounted from frontend/dist")
except Exception as e:
    logger.warning(f"⚠️  Could not mount static files: {e}")


# ======================== STARTUP INFO ========================

@app.on_event("startup")
async def startup_event():
    """Log startup information."""
    logger.info(f"""

    🚀 ╔════════════════════════════════════════════════════════╗
       ║                   NEXUSAI BACKEND                     ║
       ║                   Version {settings.app_version:20s}║
       ╚════════════════════════════════════════════════════════╝

    📊 Configuration:
       • Environment: {settings.environment}
       • Debug mode: {settings.debug}
       • Database: {settings.database_url.split('://')[0]}
       • CORS origins: {len(settings.cors_origins)} configured

    🔌 Services:
       • FastAPI running
       • Database: Initializing...
       • Authentication: JWT + API keys (Bearer / X-API-Key)

    📝 Documentation:
       • OpenAPI: http://localhost:8000/docs
       • ReDoc: http://localhost:8000/redoc

    """)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info",
    )
