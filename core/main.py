"""
Gamora AI Backend - Main Application
Ultimate game generation platform with ChatGPT-4 + DeepSeek R1
"""

import os
import asyncio
from contextlib import asynccontextmanager
from typing import Dict, Any
import logging
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import uvicorn

# Import core modules
from core.orchestrator import MasterOrchestrator
from core.auth import AuthManager
from core.rate_limiter import RateLimiter
from core.websocket_manager import WebSocketManager
from services.database import DatabaseManager
from services.cache import CacheManager
from services.godot_service import GodotService
from services.storage import StorageService
from api.routes import (
    auth_router,
    projects_router,
    generation_router
)
from config.settings import Settings
from utils.logger import setup_logger

# Initialize logger
logger = setup_logger(__name__)

# Prometheus metrics (register only once to avoid duplicates)
# Check registry first to avoid duplicate registration errors
from prometheus_client import REGISTRY

def get_or_create_metric(metric_class, name, description, *args, **kwargs):
    """Get existing metric from registry or create new one"""
    # Check if metric already exists in registry
    for collector in list(REGISTRY._collector_to_names.keys()):
        if hasattr(collector, '_name') and collector._name == name:
            return collector
    # If not found, create new metric
    try:
        return metric_class(name, description, *args, **kwargs)
    except ValueError:
        # If registration fails, try to find it again (might have been registered by another thread)
        for collector in list(REGISTRY._collector_to_names.keys()):
            if hasattr(collector, '_name') and collector._name == name:
                return collector
        # If still not found, create a no-op metric wrapper to prevent crashes
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

# Global components
components: Dict[str, Any] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("🚀 Starting Gamora AI Backend...")
    
    # Load settings
    settings = Settings()
    
    # Initialize database (Supabase)
    logger.info("📊 Connecting to Supabase...")
    db_manager = DatabaseManager(settings.supabase_url, settings.supabase_key)
    await db_manager.connect()
    await db_manager.create_tables()  # Note: Run SQL schema manually in Supabase
    
    # Initialize cache (in-memory)
    logger.info("🔄 Initializing cache...")
    cache_manager = CacheManager()
    await cache_manager.connect()
    
    # Initialize storage (Supabase)
    logger.info("💾 Connecting to Supabase Storage...")
    storage_service = StorageService(
        supabase_url=settings.supabase_url,
        supabase_key=settings.supabase_key,
        bucket=settings.storage_bucket
    )
    await storage_service.connect()
    
    # Initialize Godot service (optional - backend can run without it)
    logger.info("🎮 Starting Godot Service...")
    godot_service = None
    try:
        godot_service = GodotService(
            godot_path=settings.godot_path,
            projects_dir=settings.projects_dir
        )
        await godot_service.start()
        logger.info("✅ Godot Service started successfully")
    except Exception as e:
        logger.warning(f"⚠️  Godot Service not available: {e}")
        logger.warning("   Backend will run without game builds. AI generation will still work.")
        logger.warning("   Install Godot and set GODOT_PATH to enable game builds.")
    
    # Initialize authentication (Supabase)
    logger.info("🔐 Setting up authentication...")
    auth_manager = AuthManager(settings.supabase_url, settings.supabase_anon_key)
    await auth_manager.initialize()
    
    # Initialize rate limiter
    logger.info("⏱️  Setting up rate limiter...")
    rate_limiter = RateLimiter(cache_manager)
    
    # Initialize WebSocket manager
    logger.info("🔌 Setting up WebSocket manager...")
    ws_manager = WebSocketManager()
    
    # Initialize master orchestrator
    logger.info("🤖 Initializing AI Orchestrator (DeepSeek R1 Primary + OpenAI for Assets)...")
    orchestrator = MasterOrchestrator(
        openai_api_key=settings.openai_api_key,
        deepseek_api_key=settings.deepseek_api_key,
        cache_manager=cache_manager,
        godot_service=godot_service,
        storage_service=storage_service,
        ws_manager=ws_manager
    )
    await orchestrator.initialize()
    
    # Store components globally
    components['settings'] = settings
    components['db'] = db_manager
    components['cache'] = cache_manager
    components['storage'] = storage_service
    components['godot'] = godot_service
    components['auth'] = auth_manager
    components['rate_limiter'] = rate_limiter
    components['ws_manager'] = ws_manager
    components['orchestrator'] = orchestrator
    
    logger.info("✅ Gamora AI Backend started successfully!")
    logger.info(f"📍 Server running on {settings.host}:{settings.port}")
    logger.info(f"📚 API Docs: http://{settings.host}:{settings.port}/docs")
    
    yield
    
    # Cleanup on shutdown
    logger.info("🛑 Shutting down Gamora AI Backend...")
    await orchestrator.shutdown()
    await godot_service.stop()
    await storage_service.disconnect()
    await cache_manager.disconnect()
    await db_manager.disconnect()
    logger.info("✅ Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Gamora AI Backend",
    description="Ultimate AI-Powered Game Generation Platform | DeepSeek R1 (Primary) + OpenAI (Assets)",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.middleware("http")
async def metrics_middleware(request, call_next):
    """Track request metrics"""
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


# Include routers
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(projects_router, prefix="/api/v1/projects", tags=["Projects"])
app.include_router(generation_router, prefix="/api/v1/generate", tags=["Generation"])


# Root endpoints
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Gamora AI Backend",
        "version": "2.0.0",
        "status": "operational",
        "ai_models": ["DeepSeek-R1 (Primary)", "DALL-E-3 (Assets)"],
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
async def health_check():
    """Comprehensive health check"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {}
    }
    
    # Check all services
    services = {
        "database": components.get('db'),
        "cache": components.get('cache'),
        "godot": components.get('godot'),
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
    """Prometheus metrics endpoint"""
    from starlette.responses import Response
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/stats")
async def get_stats():
    """Get system statistics"""
    stats = {
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0",
        "ai_models": {
            "primary": "DeepSeek-R1",
            "image_generation": "DALL-E-3"
        }
    }
    
    # Get component stats if available
    if 'cache' in components:
        stats["cache"] = await components['cache'].get_stats()
    if 'db' in components:
        stats["database"] = await components['db'].get_stats()
    if 'ws_manager' in components:
        stats["active_websockets"] = len(components['ws_manager'].active_connections)
    
    return stats


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handle all unhandled exceptions"""
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
    """Dependency to get global components"""
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
