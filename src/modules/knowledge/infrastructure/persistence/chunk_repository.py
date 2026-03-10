"""
Chunk Repository Implementation

PostgreSQL-based implementation of ChunkRepositoryInterface.
"""
import logging
from typing import Optional, List, Dict, Any
from uuid import UUID
import json

from ...domain.entities import Chunk
from ...domain.repository_interfaces import ChunkRepositoryInterface
from ...domain.services.chunking_service import ChunkLocator

logger = logging.getLogger(__name__)


class PostgresChunkRepository(ChunkRepositoryInterface):
    """
    PostgreSQL implementation of ChunkRepositoryInterface.
    
    Stores chunk metadata with locators for citation support.
    """
    
    def __init__(self, connection_pool):
        """
        Initialize the repository.
        
        Args:
            connection_pool: AsyncPG connection pool
        """
        self.pool = connection_pool
    
    async def create(self, chunk: Chunk) -> Chunk:
        """Create a new chunk record."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO knowledge_chunks (
                    id, document_id, content, locator, length,
                    created_at, updated_at, created_by, updated_by
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                RETURNING *
                """,
                chunk.id,
                chunk.document_id,
                chunk.content,
                json.dumps(chunk.locator) if chunk.locator else None,
                chunk.length,
                chunk.created_at,
                chunk.updated_at,
                chunk.created_by,
                chunk.updated_by,
            )
            return self._row_to_chunk(row)
    
    async def create_batch(self, chunks: List[Chunk]) -> List[Chunk]:
        """Create multiple chunk records in a batch."""
        if not chunks:
            return []
        
        async with self.pool.acquire() as conn:
            # Prepare values for batch insert
            values = [
                (
                    chunk.id,
                    chunk.document_id,
                    chunk.content,
                    json.dumps(chunk.locator) if chunk.locator else None,
                    chunk.length,
                    chunk.created_at,
                    chunk.updated_at,
                    chunk.created_by,
                    chunk.updated_by,
                )
                for chunk in chunks
            ]
            
            # Batch insert
            rows = await conn.executemany(
                """
                INSERT INTO knowledge_chunks (
                    id, document_id, content, locator, length,
                    created_at, updated_at, created_by, updated_by
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """,
                values,
            )
            
            return chunks  # Return the input chunks since we have the data
    
    async def get_by_id(self, chunk_id: UUID) -> Optional[Chunk]:
        """Get a chunk by its ID."""
        async with self.pool.acquire() as conn:
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
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM knowledge_chunks
                WHERE document_id = $1 AND deleted_at IS NULL
                ORDER BY created_at
                LIMIT $2 OFFSET $3
                """,
                document_id,
                limit,
                offset,
            )
            return [self._row_to_chunk(row) for row in rows]
    
    async def delete_by_document(self, document_id: UUID) -> int:
        """Delete all chunks for a document (soft delete)."""
        async with self.pool.acquire() as conn:
            result = await conn.execute(
                """
                UPDATE knowledge_chunks
                SET deleted_at = NOW()
                WHERE document_id = $1 AND deleted_at IS NULL
                """,
                document_id,
            )
            # Return count of updated rows
            return int(result.split()[-1]) if result else 0
    
    async def get_locators_by_ids(self, chunk_ids: List[UUID]) -> Dict[UUID, ChunkLocator]:
        """Get locators for multiple chunks."""
        if not chunk_ids:
            return {}
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, locator FROM knowledge_chunks
                WHERE id = ANY($1) AND deleted_at IS NULL
                """,
                chunk_ids,
            )
            
            result = {}
            for row in rows:
                chunk_id = row['id']
                locator_data = row['locator']
                if locator_data:
                    if isinstance(locator_data, str):
                        locator_data = json.loads(locator_data)
                    result[chunk_id] = ChunkLocator.from_dict(locator_data)
            
            return result
    
    async def search_by_content(
        self,
        query: str,
        document_id: Optional[UUID] = None,
        limit: int = 10,
    ) -> List[Chunk]:
        """Search chunks by content using full-text search."""
        async with self.pool.acquire() as conn:
            if document_id:
                rows = await conn.fetch(
                    """
                    SELECT * FROM knowledge_chunks
                    WHERE document_id = $1
                      AND deleted_at IS NULL
                      AND to_tsvector('english', content) @@ plainto_tsquery('english', $2)
                    ORDER BY ts_rank(to_tsvector('english', content), plainto_tsquery('english', $2)) DESC
                    LIMIT $3
                    """,
                    document_id,
                    query,
                    limit,
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT * FROM knowledge_chunks
                    WHERE deleted_at IS NULL
                      AND to_tsvector('english', content) @@ plainto_tsquery('english', $1)
                    ORDER BY ts_rank(to_tsvector('english', content), plainto_tsquery('english', $1)) DESC
                    LIMIT $2
                    """,
                    query,
                    limit,
                )
            
            return [self._row_to_chunk(row) for row in rows]
    
    def _row_to_chunk(self, row: Any) -> Chunk:
        """Convert a database row to a Chunk entity."""
        locator_data = row.get('locator')
        if locator_data and isinstance(locator_data, str):
            locator_data = json.loads(locator_data)
        
        return Chunk(
            id=row['id'],
            document_id=row['document_id'],
            content=row['content'],
            locator=locator_data,
            length=row['length'],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            created_by=row.get('created_by'),
            updated_by=row.get('updated_by'),
            deleted_at=row.get('deleted_at'),
            deleted_by=row.get('deleted_by'),
        )