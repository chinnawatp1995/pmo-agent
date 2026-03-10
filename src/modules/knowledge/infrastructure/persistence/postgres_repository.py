"""
PostgreSQL Repository Implementation

Implementation of repository interfaces using PostgreSQL with asyncpg.
Handles CRUD operations for documents, chunks, and related entities.
"""
import logging
from typing import Optional, List
from uuid import UUID
from datetime import datetime

import asyncpg

from ...domain.repository_interfaces import (
    DocumentRepositoryInterface,
    ChunkRepositoryInterface,
    DataSourceRepositoryInterface,
)
from ...domain.entities import Document, Chunk, DataSource
from ..config.lightrag_config import PostgreSQLConfig

logger = logging.getLogger(__name__)


class PostgresDocumentRepository(DocumentRepositoryInterface):
    """
    PostgreSQL implementation of document repository.
    
    Handles persistence of document metadata and status tracking.
    """
    
    def __init__(self, config: Optional[PostgreSQLConfig] = None):
        """
        Initialize the repository.
        
        Args:
            config: PostgreSQL configuration
        """
        self.config = config or PostgreSQLConfig.from_env()
        self._pool: Optional[asyncpg.Pool] = None
    
    async def _get_pool(self) -> asyncpg.Pool:
        """Get or create the connection pool."""
        if self._pool is None:
            self._pool = await asyncpg.create_pool(
                host=self.config.host,
                port=self.config.port,
                user=self.config.user,
                password=self.config.password,
                database=self.config.database,
                min_size=2,
                max_size=10,
            )
        return self._pool
    
    async def close(self) -> None:
        """Close the connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None
    
    async def create(self, document: Document) -> Document:
        """Create a new document record."""
        pool = await self._get_pool()
        
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO knowledge_documents 
                (id, data_source_id, document_type, title, content_hash, 
                 file_path, file_size, status, metadata, error_message,
                 created_at, created_by, updated_at, updated_by)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                RETURNING *
                """,
                document.id,
                document.data_source_id,
                document.document_type.value,
                document.title,
                document.content_hash,
                document.file_path,
                document.file_size,
                document.status.value,
                document.metadata,
                document.error_message,
                document.created_at,
                document.created_by,
                document.updated_at,
                document.updated_by,
            )
            
            return self._row_to_document(row)
    
    async def get_by_id(self, document_id: UUID) -> Optional[Document]:
        """Get a document by its ID."""
        pool = await self._get_pool()
        
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM knowledge_documents 
                WHERE id = $1 AND deleted_at IS NULL
                """,
                document_id,
            )
            
            return self._row_to_document(row) if row else None
    
    async def get_by_content_hash(self, content_hash: str) -> Optional[Document]:
        """Get a document by its content hash."""
        pool = await self._get_pool()
        
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM knowledge_documents 
                WHERE content_hash = $1 AND deleted_at IS NULL
                """,
                content_hash,
            )
            
            return self._row_to_document(row) if row else None
    
    async def list(
        self,
        data_source_id: Optional[UUID] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Document]:
        """List documents with optional filtering."""
        pool = await self._get_pool()
        
        conditions = ["deleted_at IS NULL"]
        params = []
        param_idx = 1
        
        if data_source_id:
            conditions.append(f"data_source_id = ${param_idx}")
            params.append(data_source_id)
            param_idx += 1
        
        if status:
            conditions.append(f"status = ${param_idx}")
            params.append(status)
            param_idx += 1
        
        params.extend([limit, offset])
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                f"""
                SELECT * FROM knowledge_documents 
                WHERE {' AND '.join(conditions)}
                ORDER BY created_at DESC
                LIMIT ${param_idx} OFFSET ${param_idx + 1}
                """,
                *params,
            )
            
            return [self._row_to_document(row) for row in rows]
    
    async def update(self, document: Document) -> Document:
        """Update an existing document."""
        pool = await self._get_pool()
        
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                UPDATE knowledge_documents 
                SET data_source_id = $2, document_type = $3, title = $4,
                    content_hash = $5, file_path = $6, file_size = $7,
                    status = $8, metadata = $9, error_message = $10,
                    updated_at = $11, updated_by = $12
                WHERE id = $1
                RETURNING *
                """,
                document.id,
                document.data_source_id,
                document.document_type.value,
                document.title,
                document.content_hash,
                document.file_path,
                document.file_size,
                document.status.value,
                document.metadata,
                document.error_message,
                document.updated_at,
                document.updated_by,
            )
            
            return self._row_to_document(row)
    
    async def delete(self, document_id: UUID) -> bool:
        """Soft delete a document."""
        pool = await self._get_pool()
        
        async with pool.acquire() as conn:
            result = await conn.execute(
                """
                UPDATE knowledge_documents 
                SET deleted_at = $2, deleted_by = $3
                WHERE id = $1 AND deleted_at IS NULL
                """,
                document_id,
                datetime.utcnow(),
                UUID(int=0),  # NIL UUID
            )
            
            return "UPDATE 1" in result
    
    async def exists(self, document_id: UUID) -> bool:
        """Check if a document exists."""
        pool = await self._get_pool()
        
        async with pool.acquire() as conn:
            exists = await conn.fetchval(
                """
                SELECT EXISTS(
                    SELECT 1 FROM knowledge_documents 
                    WHERE id = $1 AND deleted_at IS NULL
                )
                """,
                document_id,
            )
            
            return exists
    
    def _row_to_document(self, row) -> Document:
        """Convert a database row to a Document entity."""
        from ...domain.entities import DocumentType, DocumentStatus
        
        return Document(
            id=row["id"],
            data_source_id=row["data_source_id"],
            document_type=DocumentType(row["document_type"]),
            title=row["title"],
            content_hash=row["content_hash"],
            file_path=row["file_path"],
            file_size=row["file_size"],
            status=DocumentStatus(row["status"]),
            metadata=row["metadata"],
            error_message=row["error_message"],
            created_at=row["created_at"],
            created_by=row["created_by"],
            updated_at=row["updated_at"],
            updated_by=row["updated_by"],
            deleted_at=row["deleted_at"],
            deleted_by=row["deleted_by"],
        )


class PostgresChunkRepository(ChunkRepositoryInterface):
    """
    PostgreSQL implementation of chunk repository.
    
    Handles persistence of document chunks.
    """
    
    def __init__(self, config: Optional[PostgreSQLConfig] = None):
        self.config = config or PostgreSQLConfig.from_env()
        self._pool: Optional[asyncpg.Pool] = None
    
    async def _get_pool(self) -> asyncpg.Pool:
        """Get or create the connection pool."""
        if self._pool is None:
            self._pool = await asyncpg.create_pool(
                host=self.config.host,
                port=self.config.port,
                user=self.config.user,
                password=self.config.password,
                database=self.config.database,
                min_size=2,
                max_size=10,
            )
        return self._pool
    
    async def close(self) -> None:
        """Close the connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None
    
    async def create(self, chunk: Chunk) -> Chunk:
        """Create a new chunk record."""
        pool = await self._get_pool()
        
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO knowledge_chunks 
                (id, document_id, locator, content, length, chunk_index,
                 valid_til, embedding_status, created_at, created_by,
                 updated_at, updated_by)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                RETURNING *
                """,
                chunk.id,
                chunk.document_id,
                chunk.locator,
                chunk.content,
                chunk.length,
                chunk.chunk_index,
                chunk.valid_til,
                chunk.embedding_status,
                chunk.created_at,
                chunk.created_by,
                chunk.updated_at,
                chunk.updated_by,
            )
            
            return self._row_to_chunk(row)
    
    async def get_by_id(self, chunk_id: UUID) -> Optional[Chunk]:
        """Get a chunk by its ID."""
        pool = await self._get_pool()
        
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM knowledge_chunks 
                WHERE id = $1 AND deleted_at IS NULL
                """,
                chunk_id,
            )
            
            return self._row_to_chunk(row) if row else None
    
    async def list_by_document(
        self,
        document_id: UUID,
        limit: int = 100,
        offset: int = 0
    ) -> List[Chunk]:
        """List chunks for a specific document."""
        pool = await self._get_pool()
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM knowledge_chunks 
                WHERE document_id = $1 AND deleted_at IS NULL
                ORDER BY chunk_index
                LIMIT $2 OFFSET $3
                """,
                document_id,
                limit,
                offset,
            )
            
            return [self._row_to_chunk(row) for row in rows]
    
    async def delete_by_document(self, document_id: UUID) -> int:
        """Delete all chunks for a document."""
        pool = await self._get_pool()
        
        async with pool.acquire() as conn:
            result = await conn.execute(
                """
                UPDATE knowledge_chunks 
                SET deleted_at = $2
                WHERE document_id = $1 AND deleted_at IS NULL
                """,
                document_id,
                datetime.utcnow(),
            )
            
            # Extract count from result
            return int(result.split()[-1]) if "UPDATE" in result else 0
    
    def _row_to_chunk(self, row) -> Chunk:
        """Convert a database row to a Chunk entity."""
        return Chunk(
            id=row["id"],
            document_id=row["document_id"],
            locator=row["locator"] or {},
            content=row["content"],
            length=row["length"],
            chunk_index=row["chunk_index"],
            valid_til=row["valid_til"],
            embedding_status=row["embedding_status"],
            created_at=row["created_at"],
            created_by=row["created_by"],
            updated_at=row["updated_at"],
            updated_by=row["updated_by"],
            deleted_at=row["deleted_at"],
            deleted_by=row["deleted_by"],
        )


class PostgresDataSourceRepository(DataSourceRepositoryInterface):
    """
    PostgreSQL implementation of data source repository.
    """
    
    def __init__(self, config: Optional[PostgreSQLConfig] = None):
        self.config = config or PostgreSQLConfig.from_env()
        self._pool: Optional[asyncpg.Pool] = None
    
    async def _get_pool(self) -> asyncpg.Pool:
        """Get or create the connection pool."""
        if self._pool is None:
            self._pool = await asyncpg.create_pool(
                host=self.config.host,
                port=self.config.port,
                user=self.config.user,
                password=self.config.password,
                database=self.config.database,
                min_size=2,
                max_size=10,
            )
        return self._pool
    
    async def close(self) -> None:
        """Close the connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None
    
    async def create(self, data_source: DataSource) -> DataSource:
        """Create a new data source."""
        pool = await self._get_pool()
        
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO knowledge_data_sources 
                (id, name, description, config, is_active,
                 created_at, created_by, updated_at, updated_by)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                RETURNING *
                """,
                data_source.id,
                data_source.name.value,
                data_source.description,
                data_source.config,
                data_source.is_active,
                data_source.created_at,
                data_source.created_by,
                data_source.updated_at,
                data_source.updated_by,
            )
            
            return self._row_to_data_source(row)
    
    async def get_by_id(self, data_source_id: UUID) -> Optional[DataSource]:
        """Get a data source by ID."""
        pool = await self._get_pool()
        
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM knowledge_data_sources 
                WHERE id = $1 AND deleted_at IS NULL
                """,
                data_source_id,
            )
            
            return self._row_to_data_source(row) if row else None
    
    async def list(self, active_only: bool = True) -> List[DataSource]:
        """List all data sources."""
        pool = await self._get_pool()
        
        condition = "deleted_at IS NULL"
        if active_only:
            condition += " AND is_active = TRUE"
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                f"""
                SELECT * FROM knowledge_data_sources 
                WHERE {condition}
                ORDER BY created_at DESC
                """
            )
            
            return [self._row_to_data_source(row) for row in rows]
    
    async def update(self, data_source: DataSource) -> DataSource:
        """Update a data source."""
        pool = await self._get_pool()
        
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                UPDATE knowledge_data_sources 
                SET name = $2, description = $3, config = $4, 
                    is_active = $5, updated_at = $6, updated_by = $7
                WHERE id = $1
                RETURNING *
                """,
                data_source.id,
                data_source.name.value,
                data_source.description,
                data_source.config,
                data_source.is_active,
                data_source.updated_at,
                data_source.updated_by,
            )
            
            return self._row_to_data_source(row)
    
    def _row_to_data_source(self, row) -> DataSource:
        """Convert a database row to a DataSource entity."""
        from ...domain.entities import DataSourceType
        
        return DataSource(
            id=row["id"],
            name=DataSourceType(row["name"]),
            description=row["description"],
            config=row["config"],
            is_active=row["is_active"],
            created_at=row["created_at"],
            created_by=row["created_by"],
            updated_at=row["updated_at"],
            updated_by=row["updated_by"],
            deleted_at=row["deleted_at"],
            deleted_by=row["deleted_by"],
        )