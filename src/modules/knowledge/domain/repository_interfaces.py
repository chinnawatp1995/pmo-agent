"""
Repository Interfaces (Ports)

Abstract interfaces that define the contracts for data persistence.
These are implemented by the infrastructure layer following Dependency Inversion.
"""
from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID

from .entities import Document, Chunk, Vector, GraphEntity, Relationship, DataSource


class DocumentRepositoryInterface(ABC):
    """Abstract interface for document persistence."""
    
    @abstractmethod
    async def create(self, document: Document) -> Document:
        """Create a new document record."""
        pass
    
    @abstractmethod
    async def get_by_id(self, document_id: UUID) -> Optional[Document]:
        """Get a document by its ID."""
        pass
    
    @abstractmethod
    async def get_by_content_hash(self, content_hash: str) -> Optional[Document]:
        """Get a document by its content hash."""
        pass
    
    @abstractmethod
    async def list(
        self,
        data_source_id: Optional[UUID] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Document]:
        """List documents with optional filtering."""
        pass
    
    @abstractmethod
    async def update(self, document: Document) -> Document:
        """Update an existing document."""
        pass
    
    @abstractmethod
    async def delete(self, document_id: UUID) -> bool:
        """Soft delete a document."""
        pass
    
    @abstractmethod
    async def exists(self, document_id: UUID) -> bool:
        """Check if a document exists."""
        pass


class ChunkRepositoryInterface(ABC):
    """Abstract interface for chunk persistence."""
    
    @abstractmethod
    async def create(self, chunk: Chunk) -> Chunk:
        """Create a new chunk record."""
        pass
    
    @abstractmethod
    async def get_by_id(self, chunk_id: UUID) -> Optional[Chunk]:
        """Get a chunk by its ID."""
        pass
    
    @abstractmethod
    async def list_by_document(
        self,
        document_id: UUID,
        limit: int = 100,
        offset: int = 0
    ) -> List[Chunk]:
        """List chunks for a specific document."""
        pass
    
    @abstractmethod
    async def delete_by_document(self, document_id: UUID) -> int:
        """Delete all chunks for a document."""
        pass


class VectorRepositoryInterface(ABC):
    """Abstract interface for vector persistence."""
    
    @abstractmethod
    async def create(self, vector: Vector) -> Vector:
        """Create a new vector record."""
        pass
    
    @abstractmethod
    async def get_by_chunk_id(self, chunk_id: UUID) -> Optional[Vector]:
        """Get a vector by its chunk ID."""
        pass
    
    @abstractmethod
    async def similarity_search(
        self,
        query_vector: List[float],
        top_k: int = 10,
        threshold: float = 0.0
    ) -> List[tuple[Vector, float]]:
        """Find similar vectors."""
        pass
    
    @abstractmethod
    async def delete_by_chunk(self, chunk_id: UUID) -> bool:
        """Delete a vector by chunk ID."""
        pass


class GraphRepositoryInterface(ABC):
    """Abstract interface for knowledge graph persistence."""
    
    @abstractmethod
    async def create_entity(self, entity: GraphEntity) -> GraphEntity:
        """Create a graph entity."""
        pass
    
    @abstractmethod
    async def get_entity_by_name(self, name: str) -> Optional[GraphEntity]:
        """Get an entity by name."""
        pass
    
    @abstractmethod
    async def create_relationship(self, relationship: Relationship) -> Relationship:
        """Create a relationship between entities."""
        pass
    
    @abstractmethod
    async def get_entity_relationships(
        self,
        entity_id: UUID,
        relationship_type: Optional[str] = None
    ) -> List[Relationship]:
        """Get relationships for an entity."""
        pass
    
    @abstractmethod
    async def search_entities(
        self,
        query: str,
        limit: int = 10
    ) -> List[GraphEntity]:
        """Search entities by name or description."""
        pass


class DataSourceRepositoryInterface(ABC):
    """Abstract interface for data source persistence."""
    
    @abstractmethod
    async def create(self, data_source: DataSource) -> DataSource:
        """Create a new data source."""
        pass
    
    @abstractmethod
    async def get_by_id(self, data_source_id: UUID) -> Optional[DataSource]:
        """Get a data source by ID."""
        pass
    
    @abstractmethod
    async def list(self, active_only: bool = True) -> List[DataSource]:
        """List all data sources."""
        pass
    
    @abstractmethod
    async def update(self, data_source: DataSource) -> DataSource:
        """Update a data source."""
        pass