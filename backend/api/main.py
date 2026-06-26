import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from resolvr.memory.structured_store import init_db
from api.routers import chat, ingest, sessions, documents
from api.middleware.rate_limit import SimpleRateLimiter

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize the SQLite database and create schemas
    logger.info("Starting up Resolvr API Service...")
    try:
        init_db()
        logger.info("Database schemas loaded successfully.")
    except Exception as e:
        logger.error(f"Error during startup database initialization: {e}")
        
    yield
    # Shutdown
    logger.info("Shutting down Resolvr API Service...")

app = FastAPI(
    title="Resolvr API Service",
    description="Backend API service for Project Resolvr, the Stateful Financial Auditor",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS (allow React frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify Vercel URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add Rate Limiter Middleware to protect Gemini API key quota
app.add_middleware(SimpleRateLimiter, max_requests=10, window_seconds=60)

# Register Routers
app.include_router(ingest.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(sessions.router, prefix="/api")
app.include_router(documents.router, prefix="/api")

@app.get("/")
def read_root():
    return {"status": "online", "service": "Resolvr Financial Auditor Engine"}
