"""
Relationship Entity

Represents a relationship between entities in the knowledge graph.
"""
from typing import Optional
from uuid import UUID

from pydantic import Field

from .base import BaseModel


class Relationship(BaseModel):
    """
    Relationship entity representing an edge in the knowledge graph.
    
    These relationships connect entities and represent how they
    are related to each other.
    
    Attributes:
        name: The type/name of the relationship (e.g., "works_for", "contains")
        source_entity_id: ID of the source entity
        target_entity_id: ID of the target entity
        description: Description of the relationship
        metadata: Additional metadata about the relationship
        reference: Optional reference to source chunk or document
        weight: Weight/strength of the relationship
        confidence: Confidence score of relationship extraction
    """
    
    name: str = Field(
        ...,
        description="Type/name of the relationship"
    )
    source_entity_id: Optional[UUID] = Field(
        default=None,
        description="ID of the source entity"
    )
    target_entity_id: Optional[UUID] = Field(
        default=None,
        description="ID of the target entity"
    )
    description: Optional[str] = Field(
        default=None,
        description="Description of the relationship"
    )
    metadata: dict = Field(
        default_factory=dict,
        description="Additional metadata about the relationship"
    )
    reference: Optional[str] = Field(
        default=None,
        description="Reference to source chunk/document"
    )
    weight: Optional[float] = Field(
        default=1.0,
        ge=0.0,
        description="Weight/strength of the relationship"
    )
    confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Confidence score of extraction (0-1)"
    )
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "works_on",
                "source_entity_id": "123e4567-e89b-12d3-a456-426614174001",
                "target_entity_id": "123e4567-e89b-12d3-a456-426614174002",
                "description": "John Smith works on Project Alpha",
                "metadata": {
                    "since": "2024-01-01",
                    "role": "lead developer"
                },
                "reference": "chunk://123e4567-e89b-12d3-a456-426614174003",
                "weight": 1.0,
                "confidence": 0.89,
                "created_at": "2024-01-15T10:30:00",
            }
        }