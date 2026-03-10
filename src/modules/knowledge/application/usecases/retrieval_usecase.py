"""
Retrieval Use Case

Business logic for retrieving context from the knowledge base.
Enriches results with locator metadata for citation support.
"""
import logging
from typing import Optional, List, AsyncGenerator, Dict, Any
from uuid import UUID

from ...domain.repository_interfaces import ChunkRepositoryInterface
from ...domain.service_interfaces import LightRAGServiceInterface, QueryMode
from ...domain.services.chunking_service import ChunkLocator
from ..dto import RetrievalRequest, RetrievalResponse, QueryModeDTO

logger = logging.getLogger(__name__)


class RetrievalUseCase:
    """
    Use case for retrieving information from the knowledge base.
    
    Handles:
    - Query processing with different modes
    - Context retrieval
    - Streaming responses
    - Entity extraction
    - Locator enrichment for citations
    """
    
    def __init__(
        self,
        lightrag_service: LightRAGServiceInterface,
        chunk_repository: Optional[ChunkRepositoryInterface] = None,
        enrich_with_locators: bool = True,
    ):
        """
        Initialize the use case.
        
        Args:
            lightrag_service: Service for RAG operations
            chunk_repository: Repository for chunk metadata with locators
            enrich_with_locators: Whether to enrich results with locators
        """
        self.lightrag_service = lightrag_service
        self.chunk_repository = chunk_repository
        self.enrich_with_locators = enrich_with_locators and chunk_repository is not None
    
    async def execute(
        self,
        request: RetrievalRequest,
        user_id: Optional[UUID] = None
    ) -> RetrievalResponse:
        """
        Execute the retrieval use case.
        
        Args:
            request: Retrieval request with query
            user_id: Optional user ID for tracking
            
        Returns:
            RetrievalResponse with retrieved content and enriched locators
        """
        try:
            # Convert DTO mode to domain mode
            query_mode = self._convert_mode(request.mode)
            
            # Execute query
            result = await self.lightrag_service.query(
                query=request.query,
                mode=query_mode,
                top_k=request.top_k,
                include_references=request.include_references,
                only_context=request.only_context,
                conversation_history=request.conversation_history,
            )
            
            # Enrich references with locators if available
            enriched_references = result.references
            if self.enrich_with_locators and result.references:
                enriched_references = await self._enrich_references_with_locators(
                    result.references
                )
            
            return RetrievalResponse(
                content=result.content,
                mode=request.mode,
                references=enriched_references,
                entities=result.entities,
                context_used=result.context_used,
            )
            
        except Exception as e:
            logger.error(f"Retrieval failed: {e}")
            return RetrievalResponse(
                content=f"Error: {str(e)}",
                mode=request.mode,
            )
    
    async def execute_stream(
        self,
        request: RetrievalRequest,
        user_id: Optional[UUID] = None
    ) -> AsyncGenerator[str, None]:
        """
        Execute the retrieval with streaming response.
        
        Args:
            request: Retrieval request with query
            user_id: Optional user ID for tracking
            
        Yields:
            Chunks of the response
        """
        try:
            query_mode = self._convert_mode(request.mode)
            
            async for chunk in self.lightrag_service.query_stream(
                query=request.query,
                mode=query_mode,
                top_k=request.top_k,
                conversation_history=request.conversation_history,
            ):
                yield chunk
                
        except Exception as e:
            logger.error(f"Streaming retrieval failed: {e}")
            yield f"Error: {str(e)}"
    
    async def get_entity(self, entity_name: str) -> Optional[dict]:
        """
        Get details about a specific entity.
        
        Args:
            entity_name: Name of the entity
            
        Returns:
            Entity details or None
        """
        try:
            return await self.lightrag_service.get_entity(entity_name)
        except Exception as e:
            logger.error(f"Failed to get entity: {e}")
            return None
    
    async def get_chunks_by_document(
        self,
        document_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Get all chunks for a document with locators.
        
        Useful for viewing how a document was chunked.
        
        Args:
            document_id: Document UUID
            limit: Maximum number of chunks to return
            offset: Offset for pagination
            
        Returns:
            List of chunks with content and locators
        """
        if not self.chunk_repository:
            return []
        
        try:
            chunks = await self.chunk_repository.list_by_document(
                document_id=document_id,
                limit=limit,
                offset=offset,
            )
            
            return [
                {
                    "id": str(chunk.id),
                    "document_id": str(chunk.document_id),
                    "content": chunk.content,
                    "length": chunk.length,
                    "locator": chunk.locator,
                }
                for chunk in chunks
            ]
        except Exception as e:
            logger.error(f"Failed to get chunks: {e}")
            return []
    
    async def search_chunks(
        self,
        query: str,
        document_id: Optional[UUID] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Search chunks by content.
        
        Args:
            query: Search query
            document_id: Optional document to search within
            limit: Maximum results
            
        Returns:
            List of matching chunks with locators
        """
        if not self.chunk_repository:
            return []
        
        try:
            chunks = await self.chunk_repository.search_by_content(
                query=query,
                document_id=document_id,
                limit=limit,
            )
            
            return [
                {
                    "id": str(chunk.id),
                    "document_id": str(chunk.document_id),
                    "content": chunk.content,
                    "length": chunk.length,
                    "locator": chunk.locator,
                }
                for chunk in chunks
            ]
        except Exception as e:
            logger.error(f"Failed to search chunks: {e}")
            return []
    
    async def export_graph(
        self,
        format: str = "json",
        include_vectors: bool = False
    ) -> dict:
        """
        Export the knowledge graph.
        
        Args:
            format: Export format
            include_vectors: Whether to include vectors
            
        Returns:
            Exported graph data
        """
        try:
            result = await self.lightrag_service.export_graph(
                format=format,
                include_vectors=include_vectors,
            )
            return result or {"error": "Export failed"}
        except Exception as e:
            logger.error(f"Failed to export graph: {e}")
            return {"error": str(e)}
    
    async def _enrich_references_with_locators(
        self,
        references: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Enrich references with locator information from our database.
        
        Args:
            references: List of reference dicts from LightRAG
            
        Returns:
            Enriched references with locator info
        """
        if not references or not self.chunk_repository:
            return references
        
        # Extract chunk IDs from references
        chunk_ids = []
        for ref in references:
            # Try to get chunk_id from metadata
            chunk_id = ref.get("chunk_id")
            if chunk_id:
                try:
                    chunk_ids.append(UUID(chunk_id))
                except (ValueError, TypeError):
                    pass
        
        if not chunk_ids:
            return references
        
        try:
            # Get locators for all chunk IDs
            locators = await self.chunk_repository.get_locators_by_ids(chunk_ids)
            
            # Enrich references with locators
            enriched = []
            for ref in references:
                enriched_ref = dict(ref)
                chunk_id = ref.get("chunk_id")
                
                if chunk_id:
                    try:
                        chunk_uuid = UUID(chunk_id)
                        if chunk_uuid in locators:
                            locator = locators[chunk_uuid]
                            enriched_ref["locator"] = locator.to_dict()
                    except (ValueError, TypeError):
                        pass
                
                enriched.append(enriched_ref)
            
            return enriched
            
        except Exception as e:
            logger.warning(f"Failed to enrich references with locators: {e}")
            return references
    
    def _convert_mode(self, mode: QueryModeDTO) -> QueryMode:
        """Convert DTO mode to domain mode."""
        mode_mapping = {
            QueryModeDTO.NAIVE: QueryMode.NAIVE,
            QueryModeDTO.LOCAL: QueryMode.LOCAL,
            QueryModeDTO.GLOBAL: QueryMode.GLOBAL,
            QueryModeDTO.HYBRID: QueryMode.HYBRID,
            QueryModeDTO.MIX: QueryMode.MIX,
            QueryModeDTO.BYPASS: QueryMode.BYPASS,
        }
        return mode_mapping.get(mode, QueryMode.HYBRID)