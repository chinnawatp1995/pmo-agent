"""
Document Entity

Represents a document that has been ingested into the knowledge base.
"""
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import Field

from .base import BaseModel


class DocumentType(str, Enum):
    """Enumeration of supported document types."""
    
    PDF = "pdf"
    MD = "md"
    MARKDOWN = "markdown"
    XLSX = "xlsx"
    XLS = "xls"
    DOC = "doc"
    DOCX = "docx"
    TXT = "txt"
    HTML = "html"
    JSON = "json"
    CSV = "csv"
    PPT = "ppt"
    PPTX = "pptx"
    RTF = "rtf"
    XML = "xml"
    
    @classmethod
    def from_extension(cls, extension: str) -> "DocumentType":
        """Get document type from file extension."""
        extension_map = {
            ".pdf": cls.PDF,
            ".md": cls.MD,
            ".markdown": cls.MARKDOWN,
            ".xlsx": cls.XLSX,
            ".xls": cls.XLS,
            ".doc": cls.DOC,
            ".docx": cls.DOCX,
            ".txt": cls.TXT,
            ".html": cls.HTML,
            ".htm": cls.HTML,
            ".json": cls.JSON,
            ".csv": cls.CSV,
            ".ppt": cls.PPT,
            ".pptx": cls.PPTX,
            ".rtf": cls.RTF,
            ".xml": cls.XML,
        }
        return extension_map.get(extension.lower(), cls.TXT)


class DocumentStatus(str, Enum):
    """Enumeration of document processing statuses."""
    
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REINGESTING = "reingesting"


class Document(BaseModel):
    """
    Document entity representing an ingested document.
    
    Attributes:
        data_source_id: Reference to the data source this document came from
        document_type: The type/format of the document
        title: Human-readable title of the document
        content_hash: Hash of the document content for deduplication
        file_path: Original file path or URL
        file_size: Size of the document in bytes
        status: Current processing status
        metadata: Additional metadata about the document
        error_message: Error message if processing failed
    """
    
    data_source_id: UUID = Field(
        ...,
        description="Reference to the data source"
    )
    document_type: DocumentType = Field(
        default=DocumentType.TXT,
        description="Type of document"
    )
    title: Optional[str] = Field(
        default=None,
        description="Human-readable title"
    )
    content_hash: Optional[str] = Field(
        default=None,
        description="Hash of document content for deduplication"
    )
    file_path: Optional[str] = Field(
        default=None,
        description="Original file path or URL"
    )
    file_size: Optional[int] = Field(
        default=None,
        description="Size in bytes"
    )
    status: DocumentStatus = Field(
        default=DocumentStatus.PENDING,
        description="Processing status"
    )
    metadata: Optional[dict] = Field(
        default=None,
        description="Additional metadata"
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if processing failed"
    )
    
    def mark_processing(self) -> None:
        """Mark document as currently being processed."""
        self.status = DocumentStatus.PROCESSING
        self.mark_updated()
    
    def mark_completed(self) -> None:
        """Mark document processing as completed."""
        self.status = DocumentStatus.COMPLETED
        self.mark_updated()
    
    def mark_failed(self, error_message: str) -> None:
        """Mark document processing as failed."""
        self.status = DocumentStatus.FAILED
        self.error_message = error_message
        self.mark_updated()
    
    def mark_reingesting(self) -> None:
        """Mark document as being re-ingested."""
        self.status = DocumentStatus.REINGESTING
        self.mark_updated()
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "data_source_id": "123e4567-e89b-12d3-a456-426614174001",
                "document_type": "pdf",
                "title": "Project Requirements Document",
                "content_hash": "sha256:abc123...",
                "file_path": "/documents/requirements.pdf",
                "file_size": 1024000,
                "status": "completed",
                "metadata": {
                    "author": "John Doe",
                    "created_date": "2024-01-01"
                },
                "created_at": "2024-01-15T10:30:00",
                "created_by": "00000000-0000-0000-0000-000000000000",
            }
        }