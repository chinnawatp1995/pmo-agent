"""
Graph Entity

Represents an entity in the knowledge graph extracted from documents.
"""
from typing import Optional
from uuid import UUID

from pydantic import Field

from .base import BaseModel


class GraphEntity(BaseModel):
    """
    Graph entity representing a node in the knowledge graph.
    
    These entities are extracted from documents during ingestion
    and represent concepts, people, organizations, etc.
    
    Attributes:
        name: The name/label of the entity
        description: Description of the entity
        metadata: Additional metadata (type, source, etc.)
        reference: Optional reference to source chunk or document
        entity_type: Type classification (person, org, concept, etc.)
        confidence: Confidence score of entity extraction
    """
    
    name: str = Field(
        ...,
        description="Name/label of the entity"
    )
    description: Optional[str] = Field(
        default=None,
        description="Description of the entity"
    )
    metadata: dict = Field(
        default_factory=dict,
        description="Additional metadata about the entity"
    )
    reference: Optional[str] = Field(
        default=None,
        description="Reference to source chunk/document"
    )
    entity_type: Optional[str] = Field(
        default=None,
        description="Type classification (person, org, concept, etc.)"
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
                "name": "Project Alpha",
                "description": "A machine learning research project focused on NLP",
                "metadata": {
                    "source_document": "requirements.pdf",
                    "mentions": 15
                },
                "reference": "chunk://123e4567-e89b-12d3-a456-426614174001",
                "entity_type": "project",
                "confidence": 0.95,
                "created_at": "2024-01-15T10:30:00",
            }
        }