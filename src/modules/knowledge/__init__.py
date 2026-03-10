"""
Knowledge Module

This module provides RAG (Retrieval-Augmented Generation) capabilities using LightRAG
with PostgreSQL for vector storage and FalkorDB for graph storage.

Key Features:
- Document ingestion with entity/relationship extraction
- Multiple query modes (naive, local, global, hybrid, mix)
- Knowledge graph management
- Document metadata tracking

Usage:
    from src.modules.knowledge import router, on_startup, on_shutdown
    
    # In your FastAPI app:
    app.include_router(router)
    app.add_event_handler("startup", on_startup)
    app.add_event_handler("shutdown", on_shutdown)
"""
from .interfaces import router, on_startup, on_shutdown

__all__ = ["router", "on_startup", "on_shutdown"]