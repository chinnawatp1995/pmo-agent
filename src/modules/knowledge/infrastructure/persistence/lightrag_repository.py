"""
LightRAG Repository Implementation

Implementation of the LightRAG service interface using the LightRAG library
with PostgreSQL for KV/Vector/DocStatus storage.
"""
import asyncio
import inspect
from typing import Optional, List, Any, AsyncGenerator
from uuid import UUID, uuid4
import hashlib
import logging

from ...domain.service_interfaces import (
    LightRAGServiceInterface,
    QueryMode,
    IngestionResult,
    RetrievalResult,
)
from ..config.lightrag_config import LightRAGConfig

logger = logging.getLogger(__name__)


class LightRAGRepository(LightRAGServiceInterface):
    """
    Implementation of LightRAG service using the lightrag-hku library.
    
    This repository handles:
    - Document ingestion with entity/relationship extraction
    - Context retrieval with multiple query modes
    - Knowledge graph management
    """
    
    def __init__(self, config: Optional[LightRAGConfig] = None):
        """
        Initialize the LightRAG repository.
        
        Args:
            config: Optional configuration. If not provided, loads from environment.
        """
        self.config = config or LightRAGConfig.from_env()
        self._rag = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the LightRAG service and storage backends."""
        if self._initialized:
            return
        
        # Set up environment variables for LightRAG
        self.config.setup_env()
        
        try:
            from lightrag import LightRAG
            from lightrag.llm.openai import openai_embed
            from lightrag.kg.shared_storage import initialize_pipeline_status
            
            # Create custom LLM function based on provider
            llm_func = self._create_llm_function()
            
            # Initialize LightRAG with PostgreSQL storage
            self._rag = LightRAG(
                working_dir=self.config.working_dir,
                embedding_func=openai_embed,
                llm_model_func=llm_func,
                kv_storage=self.config.kv_storage,
                vector_storage=self.config.vector_storage,
                graph_storage=self.config.graph_storage,
                doc_status_storage=self.config.doc_status_storage,
                workspace=self.config.workspace,
            )
            
            # Initialize storages
            await self._rag.initialize_storages()
            await initialize_pipeline_status()
            
            self._initialized = True
            logger.info("LightRAG initialized successfully")
            
        except ImportError as e:
            logger.error(f"Failed to import LightRAG: {e}")
            raise RuntimeError(
                "LightRAG not installed. Install with: pip install lightrag-hku"
            )
        except Exception as e:
            logger.error(f"Failed to initialize LightRAG: {e}")
            raise
    
    def _create_llm_function(self):
        """Create LLM function based on configuration."""
        try:
            from openai import AsyncOpenAI
            
            if self.config.llm.provider == "fireworks":
                client = AsyncOpenAI(
                    api_key=self.config.llm.api_key,
                    base_url=self.config.llm.base_url,
                )
            else:
                client = AsyncOpenAI(
                    api_key=self.config.llm.api_key,
                    base_url=self.config.llm.base_url,
                )
            
            async def llm_func(
                prompt: str,
                system_prompt: Optional[str] = None,
                **kwargs
            ) -> str:
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})
                
                response = await client.chat.completions.create(
                    model=self.config.llm.model,
                    messages=messages,
                    max_tokens=self.config.llm.max_tokens,
                    temperature=self.config.llm.temperature,
                )
                return response.choices[0].message.content
            
            return llm_func
            
        except ImportError:
            raise RuntimeError(
                "OpenAI SDK not installed. Install with: pip install openai"
            )
    
    async def shutdown(self) -> None:
        """Shutdown and cleanup LightRAG resources."""
        if self._rag and self._initialized:
            try:
                await self._rag.finalize_storages()
                logger.info("LightRAG shutdown complete")
            except Exception as e:
                logger.error(f"Error during LightRAG shutdown: {e}")
            finally:
                self._initialized = False
                self._rag = None
    
    def _ensure_initialized(self) -> None:
        """Ensure the service is initialized before operations."""
        if not self._initialized or self._rag is None:
            raise RuntimeError(
                "LightRAG service not initialized. Call initialize() first."
            )
    
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
        self._ensure_initialized()
        
        doc_id = document_id or uuid4()
        
        try:
            # Prepare content with metadata
            if metadata:
                content_with_meta = f"[Metadata: {metadata}]\n\n{content}"
            else:
                content_with_meta = content
            
            # Insert into LightRAG
            await self._rag.ainsert(content_with_meta)
            
            return IngestionResult(
                success=True,
                document_id=doc_id,
                chunks_created=0,  # LightRAG manages this internally
                entities_extracted=0,
                relationships_created=0,
            )
            
        except Exception as e:
            logger.error(f"Failed to ingest text: {e}")
            return IngestionResult(
                success=False,
                document_id=doc_id,
                error_message=str(e),
            )
    
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
        self._ensure_initialized()
        
        doc_id = document_id or uuid4()
        
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Add file metadata
            file_metadata = {
                "file_path": file_path,
                **(metadata or {}),
            }
            
            return await self.ingest_text(content, doc_id, file_metadata)
            
        except FileNotFoundError:
            return IngestionResult(
                success=False,
                document_id=doc_id,
                error_message=f"File not found: {file_path}",
            )
        except Exception as e:
            logger.error(f"Failed to ingest file: {e}")
            return IngestionResult(
                success=False,
                document_id=doc_id,
                error_message=str(e),
            )
    
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
        self._ensure_initialized()
        
        try:
            from lightrag import QueryParam
            
            # Build query parameters
            param = QueryParam(
                mode=mode.value,
                top_k=top_k,
                only_need_context=only_context,
                include_references=include_references,
            )
            
            if conversation_history:
                param.conversation_history = conversation_history
            
            # Execute query
            result = await self._rag.aquery(query, param=param)
            
            return RetrievalResult(
                content=result if isinstance(result, str) else str(result),
                mode=mode,
                references=[],  # Extract from result if available
                context_used=None,
            )
            
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return RetrievalResult(
                content=f"Error: {str(e)}",
                mode=mode,
            )
    
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
        self._ensure_initialized()
        
        try:
            from lightrag import QueryParam
            
            param = QueryParam(
                mode=mode.value,
                top_k=top_k,
                stream=True,
            )
            
            if conversation_history:
                param.conversation_history = conversation_history
            
            result = await self._rag.aquery(query, param=param)
            
            if inspect.isasyncgen(result):
                async for chunk in result:
                    yield chunk
            else:
                yield str(result)
                
        except Exception as e:
            logger.error(f"Streaming query failed: {e}")
            yield f"Error: {str(e)}"
    
    async def delete_document(self, document_id: UUID) -> bool:
        """
        Delete a document and its associated data.
        
        Note: LightRAG doesn't have built-in document deletion.
        This is a placeholder for future implementation.
        
        Args:
            document_id: The document ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        self._ensure_initialized()
        
        # LightRAG doesn't support direct document deletion yet
        # This would require custom implementation
        logger.warning(
            "Document deletion not fully supported in LightRAG. "
            f"Document ID: {document_id}"
        )
        return False
    
    async def get_entity(self, entity_name: str) -> Optional[dict]:
        """
        Get details about a specific entity.
        
        Args:
            entity_name: Name of the entity
            
        Returns:
            Entity details or None if not found
        """
        self._ensure_initialized()
        
        try:
            # Query for entity information
            result = await self._rag.aquery(
                f"What is {entity_name}?",
                param=QueryParam(mode="local", only_need_context=True)
            )
            
            return {
                "name": entity_name,
                "context": result,
            }
        except Exception as e:
            logger.error(f"Failed to get entity: {e}")
            return None
    
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
        self._ensure_initialized()
        
        try:
            # LightRAG has graph export functionality
            # This is a simplified implementation
            return {
                "format": format,
                "include_vectors": include_vectors,
                "message": "Graph export not yet implemented",
            }
        except Exception as e:
            logger.error(f"Failed to export graph: {e}")
            return None