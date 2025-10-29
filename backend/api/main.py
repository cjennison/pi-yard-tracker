"""
Pi Yard Tracker REST API

FastAPI application for querying photos and detections.
"""

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import logging

from backend.database import get_db
from .routes import photos_router, detections_router, stats_router
from .schemas import HealthResponse
from .live_stream import handle_websocket

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Pi Yard Tracker API",
    description="REST API for wildlife detection system",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware (allow all origins for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# Startup/Shutdown Events
# ============================================================

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    try:
        db = get_db()
        logger.info("✅ API started successfully")
        logger.info(f"📊 Database: {db.db_path}")
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("👋 API shutting down")


# ============================================================
# Routes
# ============================================================

@app.get("/", tags=["health"])
def root():
    """API root - redirect to docs"""
    return {
        "message": "Pi Yard Tracker API",
        "version": "3.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse, tags=["health"])
def health_check():
    """
    Health check endpoint
    
    Returns API status and database connectivity.
    """
    try:
        db = get_db()
        stats = db.get_stats()
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return HealthResponse(
        status="healthy",
        database=db_status,
        version="3.0.0"
    )


# Register route modules
app.include_router(photos_router)
app.include_router(detections_router)
app.include_router(stats_router)


# ============================================================
# WebSocket Endpoints
# ============================================================

@app.websocket("/live")
async def websocket_live_feed(websocket: WebSocket):
    """
    WebSocket endpoint for live camera feed with detection overlay
    
    Streams real-time camera frames with YOLO detection results.
    Clients can send configuration updates like confidence threshold.
    """
    await handle_websocket(websocket)


# ============================================================
# Run with: uvicorn backend.api.main:app --reload
# ============================================================
