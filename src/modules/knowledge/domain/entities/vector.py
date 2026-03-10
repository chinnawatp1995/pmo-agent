"""
Vector Entity

Represents a vector embedding for a chunk.
"""
from typing import Optional
from uuid import UUID

from pydantic import Field

from .base import BaseModel


class Vector(BaseModel):
    """
    Vector entity representing an embedding for a chunk.
    
    Attributes:
        chunk_id: Reference to the chunk this vector represents
        embedding_model: Name of the embedding model used
        dimension: Dimension of the vector
        vector_data: The actual vector data (stored separately, not in DB)
    """
    
    chunk_id: UUID = Field(
        ...,
        description="Reference to the chunk"
    )
    embedding_model: str = Field(
        default="text-embedding-3-small",
        description="Name of the embedding model"
    )
    dimension: int = Field(
        default=1536,
        description="Dimension of the vector"
    )
    vector_data: Optional[list[float]] = Field(
        default=None,
        description="The actual vector embedding (not persisted in DB)"
    )
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "chunk_id": "123e4567-e89b-12d3-a456-426614174001",
                "embedding_model": "text-embedding-3-small",
                "dimension": 1536,
                "created_at": "2024-01-15T10:30:00",
            }
        }