"""FastAPI main application.

Task: T-563 - Extend main.py to initialize DaprEventPublisher
Phase: Phase V - Event-Driven Architecture
"""

import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.database import create_db_and_tables
from app.routers import auth, tasks, chat, recurring, reminders
from app.events.publisher import close_event_publisher

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI(
    title="Todo API",
    description="Phase-II Full-Stack Todo Application API",
    version="1.0.0"
)

# CORS configuration for local development
# Allows frontend (localhost:3000) to communicate with backend
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,  # CRITICAL: Required for cookies/authentication
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "Accept",
        "Accept-Language",
        "Content-Language",
        "Cookie",
        "Set-Cookie",
        "Access-Control-Allow-Credentials",
        "Access-Control-Allow-Origin",
    ],
    expose_headers=[
        "Set-Cookie",
        "Access-Control-Allow-Credentials",
    ],
    max_age=600,  # Cache preflight requests for 10 minutes
)


@app.middleware("http")
async def add_security_headers(request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response


@app.on_event("startup")
async def on_startup():
    """Initialize server on startup."""
    # Create database tables
    create_db_and_tables()

    # Initialize MCP tools cache to avoid asyncio.run() in request handlers
    try:
        from app.mcp.server import initialize_tools
        await initialize_tools()
    except ImportError:
        # MCP module not available, skip initialization
        logger.warning("MCP module not available, skipping initialization")

    # T-563: Log event publisher status
    from app.events.publisher import get_event_publisher
    publisher = get_event_publisher()
    logger.info(f"Event publisher initialized: enabled={publisher.enabled}")


@app.on_event("shutdown")
async def on_shutdown():
    """Cleanup on server shutdown.

    Task: T-563 - Extend main.py for event publisher lifecycle
    """
    # Close event publisher HTTP client
    logger.info("Shutting down event publisher...")
    await close_event_publisher()
    logger.info("Event publisher closed")


# Mount routers
app.include_router(auth.router, prefix="/api")
app.include_router(tasks.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
# Phase V routers
app.include_router(recurring.router, prefix="/api")
app.include_router(reminders.router, prefix="/api")


@app.get("/")
def root():
    """Root endpoint."""
    return {"message": "Todo API - See /docs for API documentation"}


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok"}
