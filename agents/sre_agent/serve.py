"""
SRE Agent Server - FastAPI server for the SRE agent with health checks and monitoring.
"""

import os
import time
import uuid
from datetime import datetime

import uvicorn
from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from google.adk.cli.fast_api import get_fast_api_app

try:
    from .utils import get_logger
    from .settings import get_db_url, redact_db_url
except ImportError:
    from utils import get_logger
    from settings import get_db_url, redact_db_url

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Add request/response logging + request id for troubleshooting."""

    async def dispatch(self, request, call_next):
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        start_time = time.time()

        logger.info(f"[{request_id}] Request: {request.method} {request.url}")

        try:
            response = await call_next(request)
            duration_ms = (time.time() - start_time) * 1000
            logger.info(f"[{request_id}] Response: {response.status_code} in {duration_ms:.1f}ms")
            response.headers["x-request-id"] = request_id
            return response
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                f"[{request_id}] Request failed after {duration_ms:.1f}ms: {e}", exc_info=True
            )
            raise


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    session_uri = get_db_url()
    port = os.getenv("PORT", "8000")
    env = os.getenv("NODE_ENV", "development")
    version = os.getenv("APP_VERSION", "1.0.0")

    logger.info(
        f"SRE Agent API Service initializing - Port: {port}, Env: {env}, Version: {version}"
    )
    logger.debug(f"Session URI (redacted): {redact_db_url(session_uri)}")

    # Create FastAPI app using ADK (API-only, no web UI)
    app: FastAPI = get_fast_api_app(
        agents_dir=".",
        allow_origins=["*"],
        web=False,
        session_service_uri=session_uri,
    )

    app.add_middleware(RequestLoggingMiddleware)

    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "service": "sre-agent-api",
            "timestamp": datetime.utcnow().isoformat(),
            "version": version,
            "mode": "api-only",
            "port": port,
            "environment": env,
        }

    @app.get("/health/readiness")
    async def readiness_check():
        return {"status": "ready", "service": "sre-agent-api"}

    @app.get("/health/liveness")
    async def liveness_check():
        return {"status": "alive", "service": "sre-agent-api"}

    @app.on_event("startup")
    async def startup_event():
        route_count = len([r for r in app.routes if hasattr(r, "methods") and hasattr(r, "path")])
        logger.info(f"SRE Agent API Service ready - {route_count} routes available on port {port}")

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port, reload=False)
