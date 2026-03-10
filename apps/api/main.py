"""
PMO Agent API - Main FastAPI Application

Entry point for the PMO Agent API server.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.modules.knowledge import router as knowledge_router
from src.modules.knowledge.interfaces.api.routes import on_startup, on_shutdown

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown events."""
    # Startup
    logger.info("Starting PMO Agent API...")
    await on_startup()
    logger.info("PMO Agent API started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down PMO Agent API...")
    await on_shutdown()
    logger.info("PMO Agent API shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="PMO Agent API",
    description="""
    PMO Multi-Agent System API with Knowledge Management capabilities.
    
    ## Features
    
    * **Knowledge Module**: RAG-based document ingestion and retrieval
    * **Query Modes**: naive, local, global, hybrid, mix
    * **Document Management**: Upload, list, and manage documents
    * **Knowledge Graph**: Entity and relationship extraction
    
    ## Technologies
    
    * LightRAG for RAG operations
    * PostgreSQL with pgvector for vector storage
    * FalkorDB for knowledge graph storage
    """,
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health():
    """Basic health check endpoint."""
    return {"status": "healthy", "service": "pmo-agent-api"}


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "service": "PMO Agent API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health"
    }


# Include module routers
app.include_router(knowledge_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "apps.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )