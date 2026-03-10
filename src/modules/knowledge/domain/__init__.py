"""
Knowledge Module - Domain Layer

This layer contains pure business logic with no external dependencies.
"""
from .entities import (
    BaseModel,
    DataSource,
    DataSourceType,
    Document,
    DocumentType,
    DocumentStatus,
    Chunk,
    Vector,
    GraphEntity,
    Relationship,
)
from .repository_interfaces import (
    DocumentRepositoryInterface,
    ChunkRepositoryInterface,
    VectorRepositoryInterface,
    GraphRepositoryInterface,
    DataSourceRepositoryInterface,
)
from .service_interfaces import (
    QueryMode,
    IngestionResult,
    RetrievalResult,
    LightRAGServiceInterface,
    EmbeddingServiceInterface,
)

__all__ = [
    # Entities
    "BaseModel",
    "DataSource",
    "DataSourceType",
    "Document",
    "DocumentType",
    "DocumentStatus",
    "Chunk",
    "Vector",
    "GraphEntity",
    "Relationship",
    # Repository Interfaces
    "DocumentRepositoryInterface",
    "ChunkRepositoryInterface",
    "VectorRepositoryInterface",
    "GraphRepositoryInterface",
    "DataSourceRepositoryInterface",
    # Service Interfaces
    "QueryMode",
    "IngestionResult",
    "RetrievalResult",
    "LightRAGServiceInterface",
    "EmbeddingServiceInterface",
]