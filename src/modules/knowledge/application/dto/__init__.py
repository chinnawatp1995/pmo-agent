"""
Knowledge Module - Data Transfer Objects (DTOs)

Request and Response models for the application layer.
"""
from typing import Optional, List, Any
from uuid import UUID
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class QueryModeDTO(str, Enum):
    """Query mode options."""
    NAIVE = "naive"
    LOCAL = "local"
    GLOBAL = "global"
    HYBRID = "hybrid"
    MIX = "mix"
    BYPASS = "bypass"


class IngestionRequest(BaseModel):
    """Request model for document ingestion."""
    
    content: Optional[str] = Field(
        default=None,
        description="Text content to ingest (if not using file)"
    )
    file_path: Optional[str] = Field(
        default=None,
        description="Path to file to ingest"
    )
    document_id: Optional[UUID] = Field(
        default=None,
        description="Existing document ID for re-ingestion"
    )
    data_source_id: Optional[UUID] = Field(
        default=None,
        description="ID of the data source"
    )
    document_type: Optional[str] = Field(
        default="txt",
        description="Type of document (pdf, md, txt, etc.)"
    )
    title: Optional[str] = Field(
        default=None,
        description="Title of the document"
    )
    metadata: Optional[dict] = Field(
        default=None,
        description="Additional metadata"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "content": "This is sample document content...",
                "document_type": "txt",
                "title": "Sample Document",
                "metadata": {"author": "John Doe"}
            }
        }


class IngestionResponse(BaseModel):
    """Response model for document ingestion."""
    
    success: bool = Field(description="Whether ingestion was successful")
    document_id: UUID = Field(description="ID of the ingested document")
    message: str = Field(description="Status message")
    chunks_created: int = Field(default=0, description="Number of chunks created")
    entities_extracted: int = Field(default=0, description="Number of entities extracted")
    relationships_created: int = Field(default=0, description="Number of relationships created")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "document_id": "123e4567-e89b-12d3-a456-426614174000",
                "message": "Document ingested successfully",
                "chunks_created": 15,
                "entities_extracted": 8,
                "relationships_created": 12
            }
        }


class RetrievalRequest(BaseModel):
    """Request model for knowledge retrieval."""
    
    query: str = Field(description="Natural language query")
    mode: QueryModeDTO = Field(
        default=QueryModeDTO.HYBRID,
        description="Query mode (naive, local, global, hybrid, mix)"
    )
    top_k: int = Field(
        default=60,
        ge=1,
        le=100,
        description="Number of top results to retrieve"
    )
    include_references: bool = Field(
        default=False,
        description="Include source references in response"
    )
    only_context: bool = Field(
        default=False,
        description="Return only context without LLM generation"
    )
    conversation_history: Optional[List[dict]] = Field(
        default=None,
        description="Prior conversation for context"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "What is the project timeline?",
                "mode": "hybrid",
                "top_k": 60,
                "include_references": True
            }
        }


class RetrievalResponse(BaseModel):
    """Response model for knowledge retrieval."""
    
    content: str = Field(description="Retrieved/generated content")
    mode: QueryModeDTO = Field(description="Query mode used")
    references: List[dict] = Field(
        default_factory=list,
        description="Source references"
    )
    entities: List[dict] = Field(
        default_factory=list,
        description="Related entities"
    )
    context_used: Optional[str] = Field(
        default=None,
        description="Context used for generation"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "content": "Based on the documents, the project timeline is...",
                "mode": "hybrid",
                "references": [
                    {"document_id": "123e4567-e89b-12d3-a456-426614174000", "chunk_index": 5}
                ],
                "entities": [
                    {"name": "Project Alpha", "type": "project"}
                ]
            }
        }


class DocumentResponse(BaseModel):
    """Response model for document details."""
    
    id: UUID
    data_source_id: UUID
    document_type: str
    title: Optional[str]
    status: str
    file_path: Optional[str]
    file_size: Optional[int]
    created_at: datetime
    updated_at: datetime
    metadata: Optional[dict] = None
    
    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """Response model for document listing."""
    
    documents: List[DocumentResponse]
    total: int
    limit: int
    offset: int


class DataSourceResponse(BaseModel):
    """Response model for data source."""
    
    id: UUID
    name: str
    description: Optional[str]
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class EntityResponse(BaseModel):
    """Response model for graph entity."""
    
    name: str
    description: Optional[str]
    entity_type: Optional[str]
    metadata: dict
    confidence: Optional[float]
    
    class Config:
        from_attributes = True


class HealthResponse(BaseModel):
    """Response model for health check."""
    
    status: str
    lightrag_initialized: bool
    database_connected: bool
    timestamp: datetime