"""
Service Interfaces (Ports)

Abstract interfaces for external services and complex operations.
These define contracts for LightRAG integration and other services.
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Any, AsyncGenerator
from uuid import UUID
from enum import Enum

from .entities import Document


class QueryMode(str, Enum):
    """Enumeration of LightRAG query modes."""
    
    NAIVE = "naive"          # Simple vector search
    LOCAL = "local"          # Entity-focused retrieval
    GLOBAL = "global"        # High-level community summaries
    HYBRID = "hybrid"        # Combines local and global
    MIX = "mix"              # Knowledge graph + vector retrieval
    BYPASS = "bypass"        # Direct LLM without RAG


class IngestionResult:
    """Result of a document ingestion operation."""
    
    def __init__(
        self,
        success: bool,
        document_id: UUID,
        chunks_created: int = 0,
        entities_extracted: int = 0,
        relationships_created: int = 0,
        error_message: Optional[str] = None
    ):
        self.success = success
        self.document_id = document_id
        self.chunks_created = chunks_created
        self.entities_extracted = entities_extracted
        self.relationships_created = relationships_created
        self.error_message = error_message


class RetrievalResult:
    """Result of a retrieval operation."""
    
    def __init__(
        self,
        content: str,
        mode: QueryMode,
        references: Optional[List[dict]] = None,
        entities: Optional[List[dict]] = None,
        context_used: Optional[str] = None
    ):
        self.content = content
        self.mode = mode
        self.references = references or []
        self.entities = entities or []
        self.context_used = context_used


class LightRAGServiceInterface(ABC):
    """
    Abstract interface for LightRAG operations.
    
    This interface defines the contract for RAG operations
    including document ingestion and context retrieval.
    """
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the LightRAG service and storage backends."""
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown and cleanup LightRAG resources."""
        pass
    
    @abstractmethod
    async def ingest_text(
        self,
        content: str,
        document_id: Optional[UUID] = None,
        metadata: Optional[dict] = None
    ) -> IngestionResult:
        """
        Ingest text content into the knowledge base.
        
        Args:
            content: The text content to ingest
            document_id: Optional document ID (for re-ingestion)
            metadata: Optional metadata to attach
            
        Returns:
            IngestionResult with details of the operation
        """
        pass
    
    @abstractmethod
    async def ingest_file(
        self,
        file_path: str,
        document_id: Optional[UUID] = None,
        metadata: Optional[dict] = None
    ) -> IngestionResult:
        """
        Ingest a file into the knowledge base.
        
        Args:
            file_path: Path to the file to ingest
            document_id: Optional document ID (for re-ingestion)
            metadata: Optional metadata to attach
            
        Returns:
            IngestionResult with details of the operation
        """
        pass
    
    @abstractmethod
    async def query(
        self,
        query: str,
        mode: QueryMode = QueryMode.HYBRID,
        top_k: int = 60,
        include_references: bool = False,
        only_context: bool = False,
        conversation_history: Optional[List[dict]] = None
    ) -> RetrievalResult:
        """
        Query the knowledge base.
        
        Args:
            query: The natural language query
            mode: Query mode (naive, local, global, hybrid, mix)
            top_k: Number of top results to retrieve
            include_references: Include source references in response
            only_context: Return only context without LLM generation
            conversation_history: Prior conversation for context
            
        Returns:
            RetrievalResult with the response and metadata
        """
        pass
    
    @abstractmethod
    async def query_stream(
        self,
        query: str,
        mode: QueryMode = QueryMode.HYBRID,
        top_k: int = 60,
        conversation_history: Optional[List[dict]] = None
    ) -> AsyncGenerator[str, None]:
        """
        Query with streaming response.
        
        Args:
            query: The natural language query
            mode: Query mode
            top_k: Number of top results
            conversation_history: Prior conversation
            
        Yields:
            Chunks of the response as they're generated
        """
        pass
    
    @abstractmethod
    async def delete_document(self, document_id: UUID) -> bool:
        """
        Delete a document and its associated data.
        
        Args:
            document_id: The document ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_entity(self, entity_name: str) -> Optional[dict]:
        """
        Get details about a specific entity.
        
        Args:
            entity_name: Name of the entity
            
        Returns:
            Entity details or None if not found
        """
        pass
    
    @abstractmethod
    async def export_graph(
        self,
        format: str = "json",
        include_vectors: bool = False
    ) -> Any:
        """
        Export the knowledge graph.
        
        Args:
            format: Export format (json, csv, etc.)
            include_vectors: Whether to include vector data
            
        Returns:
            Exported graph data
        """
        pass


class EmbeddingServiceInterface(ABC):
    """Abstract interface for embedding generation."""
    
    @abstractmethod
    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        pass
    
    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        pass
    
    @abstractmethod
    def get_dimension(self) -> int:
        """Get the dimension of embeddings."""
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        """Get the name of the embedding model."""
        pass