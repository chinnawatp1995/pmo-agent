"""
Ingestion Use Case

Business logic for document ingestion into the knowledge base.
Supports custom chunking with locator metadata.
"""
import hashlib
import logging
from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4

# NIL_UUID for Python < 3.11 compatibility
NIL_UUID = UUID('00000000-0000-0000-0000-000000000000')

from ...domain.entities import Document, DocumentStatus, DocumentType, DataSourceType, Chunk
from ...domain.repository_interfaces import (
    DocumentRepositoryInterface,
    DataSourceRepositoryInterface,
    ChunkRepositoryInterface,
)
from ...domain.service_interfaces import LightRAGServiceInterface, IngestionResult
from ...domain.services.chunking_service import (
    ChunkingService,
    ChunkingStrategy,
    ChunkResult,
)
from ..dto import IngestionRequest, IngestionResponse

logger = logging.getLogger(__name__)


class IngestionUseCase:
    """
    Use case for ingesting documents into the knowledge base.
    
    Handles:
    - Content validation
    - Custom chunking with locator metadata
    - Duplicate detection via content hash
    - Re-ingestion of existing documents
    - Document metadata tracking
    """
    
    def __init__(
        self,
        lightrag_service: LightRAGServiceInterface,
        document_repository: DocumentRepositoryInterface,
        chunk_repository: Optional[ChunkRepositoryInterface] = None,
        data_source_repository: Optional[DataSourceRepositoryInterface] = None,
        chunking_service: Optional[ChunkingService] = None,
        chunking_strategy: ChunkingStrategy = ChunkingStrategy.HYBRID,
        use_custom_chunking: bool = True,
    ):
        """
        Initialize the use case.
        
        Args:
            lightrag_service: Service for RAG operations
            document_repository: Repository for document metadata
            chunk_repository: Repository for chunk metadata with locators
            data_source_repository: Optional repository for data sources
            chunking_service: Custom chunking service (created if not provided)
            chunking_strategy: Strategy to use for chunking
            use_custom_chunking: Whether to use custom chunking (default: True)
        """
        self.lightrag_service = lightrag_service
        self.document_repository = document_repository
        self.chunk_repository = chunk_repository
        self.data_source_repository = data_source_repository
        self.use_custom_chunking = use_custom_chunking and chunk_repository is not None
        
        # Initialize chunking service
        self.chunking_service = chunking_service or ChunkingService(
            default_strategy=chunking_strategy
        )
        self.chunking_strategy = chunking_strategy
    
    async def execute(
        self,
        request: IngestionRequest,
        user_id: Optional[UUID] = None
    ) -> IngestionResponse:
        """
        Execute the ingestion use case.
        
        Args:
            request: Ingestion request with content or file path
            user_id: Optional user ID for audit trail
            
        Returns:
            IngestionResponse with result details
        """
        user_id = user_id or NIL_UUID
        
        # Validate request
        if not request.content and not request.file_path:
            return IngestionResponse(
                success=False,
                document_id=uuid4(),
                message="Either content or file_path must be provided",
            )
        
        try:
            # Get or create data source
            data_source_id = await self._get_or_create_data_source(request)
            
            # Determine if this is a re-ingestion
            document_id = request.document_id
            is_reingestion = document_id is not None
            
            # Get content for processing
            content = await self._get_content(request)
            
            # Calculate content hash for deduplication
            content_hash = self._calculate_hash(content)
            
            # Check for existing document (if not re-ingestion)
            if not is_reingestion:
                existing_doc = await self.document_repository.get_by_content_hash(content_hash)
                if existing_doc:
                    logger.info(f"Document already exists with ID: {existing_doc.id}")
                    return IngestionResponse(
                        success=True,
                        document_id=existing_doc.id,
                        message="Document already exists (duplicate content)",
                        chunks_created=0,
                        entities_extracted=0,
                        relationships_created=0,
                    )
            
            # Create or update document record
            if is_reingestion:
                document = await self.document_repository.get_by_id(document_id)
                if document:
                    document.mark_reingesting()
                    document = await self.document_repository.update(document)
                    # Delete old chunks for re-ingestion
                    if self.chunk_repository:
                        await self.chunk_repository.delete_by_document(document_id)
                else:
                    return IngestionResponse(
                        success=False,
                        document_id=document_id,
                        message=f"Document not found for re-ingestion: {document_id}",
                    )
            else:
                document = Document(
                    id=uuid4(),
                    data_source_id=data_source_id,
                    document_type=self._get_document_type(request),
                    title=request.title,
                    content_hash=content_hash,
                    file_path=request.file_path,
                    file_size=len(content) if content else None,
                    status=DocumentStatus.PENDING,
                    metadata=request.metadata,
                    created_by=user_id,
                    updated_by=user_id,
                )
                document = await self.document_repository.create(document)
                document_id = document.id
            
            # Mark as processing
            document.mark_processing()
            await self.document_repository.update(document)
            
            # Process with custom chunking or direct LightRAG ingestion
            if self.use_custom_chunking:
                result = await self._ingest_with_custom_chunking(
                    content=content,
                    document=document,
                    request=request,
                    user_id=user_id,
                )
            else:
                # Direct LightRAG ingestion (no custom chunking)
                result = await self._ingest_direct(
                    content=content,
                    document=document,
                    request=request,
                )
            
            # Update document status based on result
            if result.success:
                document.mark_completed()
                await self.document_repository.update(document)
                
                return IngestionResponse(
                    success=True,
                    document_id=document_id,
                    message="Document ingested successfully",
                    chunks_created=result.chunks_created,
                    entities_extracted=result.entities_extracted,
                    relationships_created=result.relationships_created,
                )
            else:
                document.mark_failed(result.error_message or "Unknown error")
                await self.document_repository.update(document)
                
                return IngestionResponse(
                    success=False,
                    document_id=document_id,
                    message=f"Ingestion failed: {result.error_message}",
                )
                
        except Exception as e:
            logger.error(f"Ingestion failed: {e}", exc_info=True)
            return IngestionResponse(
                success=False,
                document_id=document_id or uuid4(),
                message=f"Ingestion error: {str(e)}",
            )
    
    async def _ingest_with_custom_chunking(
        self,
        content: str,
        document: Document,
        request: IngestionRequest,
        user_id: UUID,
    ) -> IngestionResult:
        """
        Ingest document with custom chunking.
        
        This approach:
        1. Chunks content using ChunkingService
        2. Stores chunks with locators in our database
        3. Passes chunks to LightRAG for embedding and graph extraction
        """
        # Determine chunking strategy from request or use default
        strategy = self._get_chunking_strategy(request)
        
        # Chunk the content
        chunk_results: List[ChunkResult] = self.chunking_service.chunk(
            content=content,
            strategy=strategy,
        )
        
        logger.info(f"Document {document.id} split into {len(chunk_results)} chunks using {strategy.value} strategy")
        
        # Create Chunk entities
        now = datetime.utcnow()
        chunks: List[Chunk] = []
        
        for chunk_result in chunk_results:
            chunk = Chunk(
                id=uuid4(),
                document_id=document.id,
                content=chunk_result.content,
                locator=chunk_result.locator.to_dict(),
                length=chunk_result.length,
                created_at=now,
                updated_at=now,
                created_by=user_id,
                updated_by=user_id,
            )
            chunks.append(chunk)
        
        # Store chunks in our database
        if self.chunk_repository and chunks:
            await self.chunk_repository.create_batch(chunks)
            logger.info(f"Stored {len(chunks)} chunks with locators")
        
        # Ingest each chunk into LightRAG
        total_entities = 0
        total_relationships = 0
        
        for i, chunk in enumerate(chunks):
            # Pass chunk to LightRAG with metadata linking back to our chunk
            chunk_metadata = {
                **(request.metadata or {}),
                "chunk_id": str(chunk.id),
                "document_id": str(document.id),
                "chunk_index": i,
                "locator": chunk.locator,
            }
            
            result = await self.lightrag_service.ingest_text(
                content=chunk.content,
                document_id=document.id,
                metadata=chunk_metadata,
            )
            
            if result.success:
                total_entities += result.entities_extracted or 0
                total_relationships += result.relationships_created or 0
            else:
                logger.warning(f"Failed to ingest chunk {i}: {result.error_message}")
        
        return IngestionResult(
            success=True,
            chunks_created=len(chunks),
            entities_extracted=total_entities,
            relationships_created=total_relationships,
        )
    
    async def _ingest_direct(
        self,
        content: str,
        document: Document,
        request: IngestionRequest,
    ) -> IngestionResult:
        """
        Direct LightRAG ingestion without custom chunking.
        
        LightRAG handles chunking internally.
        """
        if request.file_path:
            return await self.lightrag_service.ingest_file(
                file_path=request.file_path,
                document_id=document.id,
                metadata=request.metadata,
            )
        else:
            return await self.lightrag_service.ingest_text(
                content=content,
                document_id=document.id,
                metadata=request.metadata,
            )
    
    def _get_chunking_strategy(self, request: IngestionRequest) -> ChunkingStrategy:
        """Get chunking strategy from request or use default."""
        # Check if strategy is specified in request metadata
        if request.metadata and "chunking_strategy" in request.metadata:
            strategy_name = request.metadata["chunking_strategy"]
            try:
                return ChunkingStrategy(strategy_name.lower())
            except ValueError:
                logger.warning(f"Unknown chunking strategy: {strategy_name}, using default")
        
        return self.chunking_strategy
    
    async def _get_or_create_data_source(self, request: IngestionRequest) -> UUID:
        """Get existing data source ID or create a default one."""
        if request.data_source_id:
            return request.data_source_id
        
        # Create a default data source if repository is available
        if self.data_source_repository:
            # Check for existing default data source
            sources = await self.data_source_repository.list(active_only=True)
            if sources:
                return sources[0].id
            
            # Create default data source
            from ...domain.entities import DataSource
            default_source = DataSource(
                id=uuid4(),
                name=DataSourceType.LOCAL_FILESYSTEM,
                description="Default data source",
                is_active=True,
            )
            created = await self.data_source_repository.create(default_source)
            return created.id
        
        # Return NIL UUID if no data source management
        return NIL_UUID
    
    async def _get_content(self, request: IngestionRequest) -> str:
        """Get content from request."""
        if request.content:
            return request.content
        
        if request.file_path:
            with open(request.file_path, 'r', encoding='utf-8') as f:
                return f.read()
        
        return ""
    
    def _calculate_hash(self, content: str) -> str:
        """Calculate SHA-256 hash of content."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def _get_document_type(self, request: IngestionRequest) -> DocumentType:
        """Determine document type from request."""
        if request.document_type:
            try:
                return DocumentType(request.document_type.lower())
            except ValueError:
                pass
        
        if request.file_path:
            ext = request.file_path.rsplit('.', 1)[-1] if '.' in request.file_path else ''
            return DocumentType.from_extension(f".{ext}")
        
        return DocumentType.TXT