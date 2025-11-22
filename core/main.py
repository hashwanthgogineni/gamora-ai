"""Gamora AI Backend - Main Application"""

from contextlib import asynccontextmanager
from typing import Dict, Any
from pathlib import Path
import logging
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import uvicorn

from core.orchestrator import MasterOrchestrator
from core.auth import AuthManager
from core.rate_limiter import RateLimiter
from core.websocket_manager import WebSocketManager
from services.database import DatabaseManager
from services.cache import CacheManager
from services.storage import StorageService
from api.routes import (
    auth_router,
    projects_router,
    generation_router
)
from config.settings import Settings
from utils.logger import setup_logger
from prometheus_client import REGISTRY

logger = setup_logger(__name__)
components: Dict[str, Any] = {}


def get_or_create_metric(metric_class, name, description, *args, **kwargs):
    for collector in list(REGISTRY._collector_to_names.keys()):
        if hasattr(collector, '_name') and collector._name == name:
            return collector
    try:
        return metric_class(name, description, *args, **kwargs)
    except ValueError:
        for collector in list(REGISTRY._collector_to_names.keys()):
            if hasattr(collector, '_name') and collector._name == name:
                return collector
        logger.warning(f"Could not register metric {name}, using no-op wrapper")
        class NoOpMetric:
            def labels(self, *args, **kwargs):
                return self
            def inc(self, *args, **kwargs):
                pass
            def observe(self, *args, **kwargs):
                pass
        return NoOpMetric()

REQUEST_COUNT = get_or_create_metric(Counter, 'gamoraai_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
REQUEST_LATENCY = get_or_create_metric(Histogram, 'gamoraai_request_latency_seconds', 'Request latency', ['endpoint'])
GENERATION_COUNT = get_or_create_metric(Counter, 'gamoraai_generations_total', 'Total generations', ['status'])
GENERATION_TIME = get_or_create_metric(Histogram, 'gamoraai_generation_time_seconds', 'Generation time')


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting Gamora AI Backend...")
    
    settings = Settings()
    
    logger.info("📊 Connecting to Supabase...")
    db_manager = DatabaseManager(settings.supabase_url, settings.supabase_key)
    await db_manager.connect()
    await db_manager.create_tables()
    
    logger.info("🔄 Initializing cache...")
    cache_manager = CacheManager()
    await cache_manager.connect()
    
    logger.info("💾 Connecting to Supabase Storage...")
    storage_service = StorageService(
        supabase_url=settings.supabase_url,
        supabase_key=settings.supabase_key,
        bucket=settings.storage_bucket
    )
    await storage_service.connect()
    
    logger.info("🔐 Setting up authentication...")
    auth_manager = AuthManager(settings.supabase_url, settings.supabase_anon_key)
    await auth_manager.initialize()
    
    logger.info("⏱️  Setting up rate limiter...")
    rate_limiter = RateLimiter(cache_manager)
    
    logger.info("🔌 Setting up WebSocket manager...")
    ws_manager = WebSocketManager()
    
    logger.info("🌐 Initializing Web Game Service...")
    from services.web_game_service import WebGameService
    web_game_service = WebGameService(
        projects_dir=settings.projects_dir.replace("projects", "web_projects"),
        templates_dir="./web_templates"
    )
    await web_game_service.start()
    
    logger.info("🤖 Initializing AI Orchestrator...")
    orchestrator = MasterOrchestrator(
        deepseek_api_key=settings.deepseek_api_key,
        cache_manager=cache_manager,
        storage_service=storage_service,
        ws_manager=ws_manager,
        web_game_service=web_game_service,
        enable_ai_assets=settings.enable_ai_assets if hasattr(settings, 'enable_ai_assets') else True
    )
    await orchestrator.initialize()
    
    logger.info("🧹 Initializing project cleanup service...")
    from services.project_cleanup import ProjectCleanupService
    cleanup_service = ProjectCleanupService(
        projects_dir=Path(settings.projects_dir),
        db_manager=db_manager
    )
    
    try:
        cleanup_stats = await cleanup_service.cleanup_on_startup()
        if cleanup_stats['deleted'] > 0:
            logger.info(f"🧹 Cleaned up {cleanup_stats['deleted']} old projects, freed {cleanup_stats['space_freed_mb']:.2f} MB")
    except Exception as e:
        logger.warning(f"⚠️  Cleanup service error: {e}")
    
    components['settings'] = settings
    components['db'] = db_manager
    components['cache'] = cache_manager
    components['storage'] = storage_service
    components['auth'] = auth_manager
    components['rate_limiter'] = rate_limiter
    components['ws_manager'] = ws_manager
    components['orchestrator'] = orchestrator
    components['cleanup'] = cleanup_service
    
    logger.info("✅ Gamora AI Backend started successfully!")
    logger.info(f"📍 Server running on {settings.host}:{settings.port}")
    logger.info(f"📚 API Docs: http://{settings.host}:{settings.port}/docs")
    
    yield
    
    logger.info("🛑 Shutting down Gamora AI Backend...")
    await orchestrator.shutdown()
    await storage_service.disconnect()
    await cache_manager.disconnect()
    await db_manager.disconnect()
    logger.info("✅ Shutdown complete")


app = FastAPI(
    title="Gamora AI Backend",
    description="AI-Powered Game Generation Platform",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.middleware("http")
async def metrics_middleware(request, call_next):
    start_time = datetime.utcnow()
    response = await call_next(request)
    latency = (datetime.utcnow() - start_time).total_seconds()
    
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    REQUEST_LATENCY.labels(endpoint=request.url.path).observe(latency)
    
    return response


app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(projects_router, prefix="/api/v1/projects", tags=["Projects"])
app.include_router(generation_router, prefix="/api/v1/generate", tags=["Generation"])


@app.get("/")
async def root():
    return {
        "name": "Gamora AI Backend",
        "version": "2.0.0",
        "status": "operational",
        "ai_models": ["DeepSeek"],
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
async def health_check():
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {}
    }
    
    services = {
        "database": components.get('db'),
        "cache": components.get('cache'),
        "storage": components.get('storage')
    }
    
    for name, service in services.items():
        try:
            if service and hasattr(service, 'is_healthy'):
                is_healthy = await service.is_healthy()
                health_status["services"][name] = "healthy" if is_healthy else "unhealthy"
            else:
                health_status["services"][name] = "not_initialized"
        except Exception as e:
            health_status["services"][name] = f"error: {str(e)}"
            health_status["status"] = "degraded"
    
    return health_status


@app.get("/metrics")
async def metrics():
    from starlette.responses import Response
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/stats")
async def get_stats():
    stats = {
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0",
        "ai_models": {
            "primary": "DeepSeek"
        }
    }
    
    if 'cache' in components:
        stats["cache"] = await components['cache'].get_stats()
    if 'db' in components:
        stats["database"] = await components['db'].get_stats()
    if 'ws_manager' in components:
        stats["active_websockets"] = len(components['ws_manager'].active_connections)
    
    return stats


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "request_id": request.headers.get("X-Request-ID", "unknown")
        }
    )


def get_components():
    return components


if __name__ == "__main__":
    settings = Settings()
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        workers=settings.workers if not settings.debug else 1,
        log_level="info"
    )
