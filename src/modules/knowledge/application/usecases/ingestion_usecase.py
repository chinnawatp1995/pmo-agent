"""
Ingestion Use Case

Business logic for document ingestion into the knowledge base.
"""
import hashlib
import logging
from typing import Optional
from uuid import UUID, uuid4, NIL_UUID

from ...domain.entities import Document, DocumentStatus, DocumentType, DataSourceType
from ...domain.repository_interfaces import DocumentRepositoryInterface, DataSourceRepositoryInterface
from ...domain.service_interfaces import LightRAGServiceInterface, IngestionResult
from ..dto import IngestionRequest, IngestionResponse

logger = logging.getLogger(__name__)


class IngestionUseCase:
    """
    Use case for ingesting documents into the knowledge base.
    
    Handles:
    - Content validation
    - Duplicate detection via content hash
    - Re-ingestion of existing documents
    - Document metadata tracking
    """
    
    def __init__(
        self,
        lightrag_service: LightRAGServiceInterface,
        document_repository: DocumentRepositoryInterface,
        data_source_repository: Optional[DataSourceRepositoryInterface] = None,
    ):
        """
        Initialize the use case.
        
        Args:
            lightrag_service: Service for RAG operations
            document_repository: Repository for document metadata
            data_source_repository: Optional repository for data sources
        """
        self.lightrag_service = lightrag_service
        self.document_repository = document_repository
        self.data_source_repository = data_source_repository
    
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
            
            # Ingest into LightRAG
            if request.file_path:
                result = await self.lightrag_service.ingest_file(
                    file_path=request.file_path,
                    document_id=document_id,
                    metadata=request.metadata,
                )
            else:
                result = await self.lightrag_service.ingest_text(
                    content=content,
                    document_id=document_id,
                    metadata=request.metadata,
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
            logger.error(f"Ingestion failed: {e}")
            return IngestionResponse(
                success=False,
                document_id=document_id or uuid4(),
                message=f"Ingestion error: {str(e)}",
            )
    
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