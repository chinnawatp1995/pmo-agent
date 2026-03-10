"""
Chunk Entity

Represents a text chunk extracted from a document for RAG processing.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import Field

from .base import BaseModel


class ChunkLocator:
    """
    Value Object for locating a chunk within its source document.
    
    Attributes:
        page: Page number (for PDFs, etc.)
        header_path: Path of headers (for markdown/HTML)
        start_char: Starting character position
        end_char: Ending character position
        section: Section identifier
    """
    page: Optional[int] = None
    header_path: Optional[str] = None
    start_char: Optional[int] = None
    end_char: Optional[int] = None
    section: Optional[str] = None


class Chunk(BaseModel):
    """
    Chunk entity representing a text segment from a document.
    
    Attributes:
        document_id: Reference to the source document
        locator: Location information within the document
        content: The actual text content of the chunk
        length: Character length of the content
        chunk_index: Index of this chunk within the document
        valid_til: Optional expiration timestamp
        embedding_status: Status of embedding generation
    """
    
    document_id: UUID = Field(
        ...,
        description="Reference to the source document"
    )
    locator: dict = Field(
        default_factory=dict,
        description="Location info: {page, header_path, start_char, end_char, section}"
    )
    content: str = Field(
        ...,
        description="The text content of the chunk"
    )
    length: int = Field(
        default=0,
        description="Character length of the content"
    )
    chunk_index: int = Field(
        default=0,
        description="Index of this chunk in the document"
    )
    valid_til: Optional[datetime] = Field(
        default=None,
        description="Expiration timestamp for time-sensitive content"
    )
    embedding_status: str = Field(
        default="pending",
        description="Status of embedding: pending, completed, failed"
    )
    
    def __init__(self, **data):
        super().__init__(**data)
        if self.length == 0 and self.content:
            self.length = len(self.content)
    
    def is_valid(self) -> bool:
        """Check if the chunk is still valid (not expired)."""
        if self.valid_til is None:
            return True
        return datetime.utcnow() < self.valid_til
    
    def mark_embedding_completed(self) -> None:
        """Mark embedding as completed."""
        self.embedding_status = "completed"
        self.mark_updated()
    
    def mark_embedding_failed(self) -> None:
        """Mark embedding as failed."""
        self.embedding_status = "failed"
        self.mark_updated()
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "document_id": "123e4567-e89b-12d3-a456-426614174001",
                "locator": {
                    "page": 5,
                    "header_path": "Introduction > Background",
                    "start_char": 1200,
                    "end_char": 1500
                },
                "content": "This is a sample chunk of text extracted from the document...",
                "length": 300,
                "chunk_index": 12,
                "valid_til": None,
                "embedding_status": "completed",
                "created_at": "2024-01-15T10:30:00",
            }
        }