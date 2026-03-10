"""
Knowledge Module - Domain Entities

Note: LightRAG handles chunking, vectorization, and entity/relationship extraction
internally. We only track Document and DataSource for:
- Document metadata and status tracking
- Data source provenance
- Audit trail

LightRAG's internal storage handles:
- KV_STORAGE: Chunks, metadata, LLM cache
- VECTOR_STORAGE: Entity/relation/chunk vectors
- GRAPH_STORAGE: Entity-relation graphs
- DOC_STATUS_STORAGE: Indexing status
"""
from .base import BaseModel
from .data_source import DataSource, DataSourceType
from .document import Document, DocumentType

# Optional - kept for potential custom analytics outside LightRAG
from .chunk import Chunk
from .vector import Vector
from .graph_entity import GraphEntity
from .relationship import Relationship

__all__ = [
    # Primary entities (for tracking)
    "BaseModel",
    "DataSource",
    "DataSourceType",
    "Document",
    "DocumentType",
    # Optional entities (LightRAG manages these internally)
    "Chunk",
    "Vector",
    "GraphEntity",
    "Relationship",
]