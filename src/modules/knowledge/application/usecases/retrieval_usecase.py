"""
Retrieval Use Case

Business logic for retrieving context from the knowledge base.
"""
import logging
from typing import Optional, List, AsyncGenerator
from uuid import UUID

from ...domain.service_interfaces import LightRAGServiceInterface, QueryMode
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
    """
    
    def __init__(self, lightrag_service: LightRAGServiceInterface):
        """
        Initialize the use case.
        
        Args:
            lightrag_service: Service for RAG operations
        """
        self.lightrag_service = lightrag_service
    
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
            RetrievalResponse with retrieved content
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
            
            return RetrievalResponse(
                content=result.content,
                mode=request.mode,
                references=result.references,
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