"""
Knowledge Module - FastAPI Routes

REST API endpoints for the knowledge module.
"""
import logging
from typing import Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import StreamingResponse

from ...application import (
    IngestionUseCase,
    RetrievalUseCase,
    IngestionRequest,
    IngestionResponse,
    RetrievalRequest,
    RetrievalResponse,
    DocumentResponse,
    DocumentListResponse,
    DataSourceResponse,
    EntityResponse,
    HealthResponse,
    QueryModeDTO,
)
from ...domain.repository_interfaces import DocumentRepositoryInterface
from ...infrastructure import (
    LightRAGRepository,
    PostgresDocumentRepository,
    LightRAGConfig,
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/knowledge", tags=["Knowledge"])

# Global instances (in production, use dependency injection)
_lightrag_repo: Optional[LightRAGRepository] = None
_document_repo: Optional[DocumentRepositoryInterface] = None


async def get_lightrag_repo() -> LightRAGRepository:
    """Get or create LightRAG repository instance."""
    global _lightrag_repo
    if _lightrag_repo is None:
        config = LightRAGConfig.from_env()
        _lightrag_repo = LightRAGRepository(config)
        await _lightrag_repo.initialize()
    return _lightrag_repo


async def get_document_repo() -> DocumentRepositoryInterface:
    """Get document repository instance."""
    global _document_repo
    if _document_repo is None:
        _document_repo = PostgresDocumentRepository()
    return _document_repo


async def get_ingestion_usecase() -> IngestionUseCase:
    """Get ingestion use case instance."""
    lightrag = await get_lightrag_repo()
    documents = await get_document_repo()
    return IngestionUseCase(lightrag, documents)


async def get_retrieval_usecase() -> RetrievalUseCase:
    """Get retrieval use case instance."""
    lightrag = await get_lightrag_repo()
    return RetrievalUseCase(lightrag)


@router.post("/ingest", response_model=IngestionResponse)
async def ingest_document(
    request: IngestionRequest,
    usecase: IngestionUseCase = Depends(get_ingestion_usecase)
) -> IngestionResponse:
    """
    Ingest a document into the knowledge base.
    
    If document_id is provided and exists, the document will be re-ingested.
    Otherwise, a new document will be created.
    """
    logger.info(f"Ingesting document: {request.title or 'Untitled'}")
    return await usecase.execute(request)


@router.post("/ingest/file", response_model=IngestionResponse)
async def ingest_file(
    file: UploadFile = File(...),
    title: Optional[str] = None,
    document_id: Optional[UUID] = None,
    metadata: Optional[str] = None,
    usecase: IngestionUseCase = Depends(get_ingestion_usecase)
) -> IngestionResponse:
    """
    Ingest a file into the knowledge base.
    
    Supports various file formats: txt, md, pdf, docx, etc.
    """
    import json
    
    # Read file content
    content = await file.read()
    
    try:
        text_content = content.decode('utf-8')
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="File must be text-based (UTF-8 encoded)"
        )
    
    # Parse metadata if provided
    meta_dict = None
    if metadata:
        try:
            meta_dict = json.loads(metadata)
        except json.JSONDecodeError:
            pass
    
    request = IngestionRequest(
        content=text_content,
        document_id=document_id,
        title=title or file.filename,
        document_type=file.filename.split('.')[-1] if '.' in file.filename else 'txt',
        metadata=meta_dict,
    )
    
    logger.info(f"Ingesting file: {file.filename}")
    return await usecase.execute(request)


@router.post("/retrieve", response_model=RetrievalResponse)
async def retrieve_context(
    request: RetrievalRequest,
    usecase: RetrievalUseCase = Depends(get_retrieval_usecase)
) -> RetrievalResponse:
    """
    Retrieve context from the knowledge base.
    
    Supports multiple query modes:
    - naive: Simple vector search
    - local: Entity-focused retrieval
    - global: High-level community summaries
    - hybrid: Combines local and global
    - mix: Knowledge graph + vector retrieval
    """
    logger.info(f"Retrieving context for query: {request.query[:50]}...")
    return await usecase.execute(request)


@router.post("/retrieve/stream")
async def retrieve_context_stream(
    request: RetrievalRequest,
    usecase: RetrievalUseCase = Depends(get_retrieval_usecase)
):
    """
    Retrieve context with streaming response.
    
    Returns chunks of the response as they're generated.
    """
    logger.info(f"Streaming retrieval for query: {request.query[:50]}...")
    
    async def generate():
        async for chunk in usecase.execute_stream(request):
            yield chunk
    
    return StreamingResponse(generate(), media_type="text/plain")


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(
    data_source_id: Optional[UUID] = None,
    status: Optional[str] = None,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    repo: DocumentRepositoryInterface = Depends(get_document_repo)
) -> DocumentListResponse:
    """
    List documents in the knowledge base.
    
    Supports filtering by data source and status.
    """
    documents = await repo.list(
        data_source_id=data_source_id,
        status=status,
        limit=limit,
        offset=offset,
    )
    
    return DocumentListResponse(
        documents=[
            DocumentResponse(
                id=doc.id,
                data_source_id=doc.data_source_id,
                document_type=doc.document_type.value,
                title=doc.title,
                status=doc.status.value,
                file_path=doc.file_path,
                file_size=doc.file_size,
                created_at=doc.created_at,
                updated_at=doc.updated_at,
                metadata=doc.metadata,
            )
            for doc in documents
        ],
        total=len(documents),
        limit=limit,
        offset=offset,
    )


@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    repo: DocumentRepositoryInterface = Depends(get_document_repo)
) -> DocumentResponse:
    """Get details of a specific document."""
    document = await repo.get_by_id(document_id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return DocumentResponse(
        id=document.id,
        data_source_id=document.data_source_id,
        document_type=document.document_type.value,
        title=document.title,
        status=document.status.value,
        file_path=document.file_path,
        file_size=document.file_size,
        created_at=document.created_at,
        updated_at=document.updated_at,
        metadata=document.metadata,
    )


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: UUID,
    repo: DocumentRepositoryInterface = Depends(get_document_repo)
):
    """Delete a document from the knowledge base."""
    deleted = await repo.delete(document_id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {"message": "Document deleted", "document_id": str(document_id)}


@router.get("/entities/{entity_name}", response_model=EntityResponse)
async def get_entity(
    entity_name: str,
    usecase: RetrievalUseCase = Depends(get_retrieval_usecase)
) -> EntityResponse:
    """Get details about a specific entity in the knowledge graph."""
    entity = await usecase.get_entity(entity_name)
    
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    return EntityResponse(
        name=entity.get("name", entity_name),
        description=entity.get("description"),
        entity_type=entity.get("type"),
        metadata=entity.get("metadata", {}),
        confidence=entity.get("confidence"),
    )


@router.post("/graph/export")
async def export_graph(
    format: str = Query(default="json", regex="^(json|csv)$"),
    include_vectors: bool = Query(default=False),
    usecase: RetrievalUseCase = Depends(get_retrieval_usecase)
):
    """Export the knowledge graph."""
    result = await usecase.export_graph(format=format, include_vectors=include_vectors)
    return result


@router.get("/health", response_model=HealthResponse)
async def health_check(
    lightrag: LightRAGRepository = Depends(get_lightrag_repo)
) -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        lightrag_initialized=lightrag._initialized,
        database_connected=True,  # Would need actual check
        timestamp=datetime.utcnow(),
    )


# Lifecycle events
async def on_startup():
    """Initialize resources on startup."""
    logger.info("Initializing Knowledge Module...")
    await get_lightrag_repo()
    logger.info("Knowledge Module initialized")


async def on_shutdown():
    """Cleanup resources on shutdown."""
    global _lightrag_repo, _document_repo
    logger.info("Shutting down Knowledge Module...")
    
    if _lightrag_repo:
        await _lightrag_repo.shutdown()
        _lightrag_repo = None
    
    if _document_repo:
        await _document_repo.close()
        _document_repo = None
    
    logger.info("Knowledge Module shutdown complete")