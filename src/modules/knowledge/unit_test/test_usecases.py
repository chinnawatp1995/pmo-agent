"""
Unit Tests for Application Use Cases

Tests for IngestionUseCase and RetrievalUseCase.
"""
import pytest
from uuid import uuid4

# NIL_UUID for Python < 3.11 compatibility
NIL_UUID = uuid4().__class__('00000000-0000-0000-0000-000000000000')
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from ..application.usecases.ingestion_usecase import IngestionUseCase
from ..application.usecases.retrieval_usecase import RetrievalUseCase
from ..application.dto import (
    IngestionRequest,
    IngestionResponse,
    RetrievalRequest,
    RetrievalResponse,
    QueryModeDTO,
)
from ..domain.entities import Document, DocumentStatus, DocumentType, DataSource
from ..domain.service_interfaces import IngestionResult, RetrievalResult, QueryMode
from ..domain.services.chunking_service import ChunkingStrategy


class TestIngestionUseCase:
    """Tests for the IngestionUseCase."""
    
    @pytest.fixture
    def mock_lightrag_service(self):
        """Create a mock LightRAG service."""
        service = AsyncMock()
        service.ingest_text = AsyncMock(return_value=IngestionResult(
            success=True,
            document_id=uuid4(),
            chunks_created=5,
            entities_extracted=3,
            relationships_created=2,
        ))
        service.ingest_file = AsyncMock(return_value=IngestionResult(
            success=True,
            document_id=uuid4(),
            chunks_created=5,
        ))
        return service
    
    @pytest.fixture
    def mock_document_repository(self):
        """Create a mock document repository."""
        repo = AsyncMock()
        repo.create = AsyncMock()
        repo.update = AsyncMock()
        repo.get_by_id = AsyncMock(return_value=None)
        repo.get_by_content_hash = AsyncMock(return_value=None)
        return repo
    
    @pytest.fixture
    def mock_chunk_repository(self):
        """Create a mock chunk repository."""
        repo = AsyncMock()
        repo.create_batch = AsyncMock()
        repo.delete_by_document = AsyncMock(return_value=5)
        return repo
    
    @pytest.fixture
    def mock_data_source_repository(self):
        """Create a mock data source repository."""
        repo = AsyncMock()
        repo.list = AsyncMock(return_value=[])
        repo.create = AsyncMock()
        return repo
    
    @pytest.mark.asyncio
    async def test_ingestion_usecase_creation(
        self,
        mock_lightrag_service,
        mock_document_repository,
    ):
        """Test creating an IngestionUseCase."""
        usecase = IngestionUseCase(
            lightrag_service=mock_lightrag_service,
            document_repository=mock_document_repository,
        )
        
        assert usecase.lightrag_service == mock_lightrag_service
        assert usecase.document_repository == mock_document_repository
    
    @pytest.mark.asyncio
    async def test_ingestion_with_content(
        self,
        mock_lightrag_service,
        mock_document_repository,
        mock_chunk_repository,
    ):
        """Test ingesting content."""
        # Setup mocks
        doc = Document(
            id=uuid4(),
            data_source_id=uuid4(),
            document_type=DocumentType.TXT,
            status=DocumentStatus.PENDING,
        )
        mock_document_repository.create.return_value = doc
        mock_document_repository.update.return_value = doc
        
        usecase = IngestionUseCase(
            lightrag_service=mock_lightrag_service,
            document_repository=mock_document_repository,
            chunk_repository=mock_chunk_repository,
            use_custom_chunking=True,
        )
        
        request = IngestionRequest(
            content="This is test content for ingestion.",
            title="Test Document",
        )
        
        response = await usecase.execute(request)
        
        assert response.success is True
        assert response.document_id is not None
        assert response.message is not None
    
    @pytest.mark.asyncio
    async def test_ingestion_without_content_or_file(
        self,
        mock_lightrag_service,
        mock_document_repository,
    ):
        """Test ingestion fails without content or file path."""
        usecase = IngestionUseCase(
            lightrag_service=mock_lightrag_service,
            document_repository=mock_document_repository,
        )
        
        request = IngestionRequest()
        
        response = await usecase.execute(request)
        
        assert response.success is False
        assert "must be provided" in response.message
    
    @pytest.mark.asyncio
    async def test_ingestion_detects_duplicate(
        self,
        mock_lightrag_service,
        mock_document_repository,
    ):
        """Test that duplicate content is detected."""
        existing_doc = Document(
            id=uuid4(),
            data_source_id=uuid4(),
            content_hash="abc123",
            status=DocumentStatus.COMPLETED,
        )
        mock_document_repository.get_by_content_hash.return_value = existing_doc
        
        usecase = IngestionUseCase(
            lightrag_service=mock_lightrag_service,
            document_repository=mock_document_repository,
        )
        
        request = IngestionRequest(content="Duplicate content")
        
        response = await usecase.execute(request)
        
        assert response.success is True
        assert "duplicate" in response.message.lower() or "already exists" in response.message.lower()
    
    @pytest.mark.asyncio
    async def test_ingestion_reingestion(
        self,
        mock_lightrag_service,
        mock_document_repository,
        mock_chunk_repository,
    ):
        """Test re-ingesting an existing document."""
        doc_id = uuid4()
        existing_doc = Document(
            id=doc_id,
            data_source_id=uuid4(),
            content_hash="old_hash",
            status=DocumentStatus.COMPLETED,
        )
        mock_document_repository.get_by_id.return_value = existing_doc
        mock_document_repository.update.return_value = existing_doc
        
        usecase = IngestionUseCase(
            lightrag_service=mock_lightrag_service,
            document_repository=mock_document_repository,
            chunk_repository=mock_chunk_repository,
            use_custom_chunking=True,
        )
        
        request = IngestionRequest(
            content="Updated content",
            document_id=doc_id,
        )
        
        response = await usecase.execute(request)
        
        # Verify delete_by_document was called for re-ingestion
        mock_chunk_repository.delete_by_document.assert_called_once_with(doc_id)
    
    @pytest.mark.asyncio
    async def test_ingestion_reingestion_document_not_found(
        self,
        mock_lightrag_service,
        mock_document_repository,
    ):
        """Test re-ingestion fails when document not found."""
        doc_id = uuid4()
        mock_document_repository.get_by_id.return_value = None
        
        usecase = IngestionUseCase(
            lightrag_service=mock_lightrag_service,
            document_repository=mock_document_repository,
        )
        
        request = IngestionRequest(
            content="Content",
            document_id=doc_id,
        )
        
        response = await usecase.execute(request)
        
        assert response.success is False
        assert "not found" in response.message.lower()
    
    @pytest.mark.asyncio
    async def test_ingestion_with_metadata(
        self,
        mock_lightrag_service,
        mock_document_repository,
        mock_chunk_repository,
    ):
        """Test ingestion with custom metadata."""
        doc = Document(
            id=uuid4(),
            data_source_id=uuid4(),
            status=DocumentStatus.PENDING,
        )
        mock_document_repository.create.return_value = doc
        mock_document_repository.update.return_value = doc
        
        usecase = IngestionUseCase(
            lightrag_service=mock_lightrag_service,
            document_repository=mock_document_repository,
            chunk_repository=mock_chunk_repository,
            use_custom_chunking=True,
        )
        
        request = IngestionRequest(
            content="Test content",
            metadata={"author": "Test Author", "version": "1.0"},
        )
        
        response = await usecase.execute(request)
        
        assert response.success is True
    
    @pytest.mark.asyncio
    async def test_ingestion_direct_mode(
        self,
        mock_lightrag_service,
        mock_document_repository,
    ):
        """Test ingestion without custom chunking."""
        doc = Document(
            id=uuid4(),
            data_source_id=uuid4(),
            status=DocumentStatus.PENDING,
        )
        mock_document_repository.create.return_value = doc
        mock_document_repository.update.return_value = doc
        
        usecase = IngestionUseCase(
            lightrag_service=mock_lightrag_service,
            document_repository=mock_document_repository,
            chunk_repository=None,
            use_custom_chunking=False,
        )
        
        request = IngestionRequest(content="Test content")
        
        response = await usecase.execute(request)
        
        assert response.success is True
        # LightRAG ingest_text should be called directly
        mock_lightrag_service.ingest_text.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_ingestion_handles_exception(
        self,
        mock_lightrag_service,
        mock_document_repository,
    ):
        """Test that exceptions are handled gracefully."""
        mock_document_repository.create.side_effect = Exception("Database error")
        
        usecase = IngestionUseCase(
            lightrag_service=mock_lightrag_service,
            document_repository=mock_document_repository,
        )
        
        request = IngestionRequest(content="Test content")
        
        response = await usecase.execute(request)
        
        assert response.success is False
        assert "error" in response.message.lower()


class TestRetrievalUseCase:
    """Tests for the RetrievalUseCase."""
    
    @pytest.fixture
    def mock_lightrag_service(self):
        """Create a mock LightRAG service."""
        service = AsyncMock()
        service.query = AsyncMock(return_value=RetrievalResult(
            content="This is the retrieved response.",
            mode=QueryMode.HYBRID,
            references=[{"document_id": str(uuid4()), "chunk_index": 0}],
            entities=[{"name": "Test Entity", "type": "concept"}],
            context_used="Retrieved context...",
        ))
        service.query_stream = AsyncMock()
        service.get_entity = AsyncMock(return_value={
            "name": "Test Entity",
            "description": "A test entity",
        })
        service.export_graph = AsyncMock(return_value={"nodes": [], "edges": []})
        return service
    
    @pytest.fixture
    def mock_chunk_repository(self):
        """Create a mock chunk repository."""
        repo = AsyncMock()
        repo.get_locators_by_ids = AsyncMock(return_value={})
        repo.list_by_document = AsyncMock(return_value=[])
        repo.search_by_content = AsyncMock(return_value=[])
        return repo
    
    @pytest.mark.asyncio
    async def test_retrieval_usecase_creation(
        self,
        mock_lightrag_service,
    ):
        """Test creating a RetrievalUseCase."""
        usecase = RetrievalUseCase(
            lightrag_service=mock_lightrag_service,
        )
        
        assert usecase.lightrag_service == mock_lightrag_service
    
    @pytest.mark.asyncio
    async def test_retrieval_execute(
        self,
        mock_lightrag_service,
    ):
        """Test executing a retrieval request."""
        usecase = RetrievalUseCase(
            lightrag_service=mock_lightrag_service,
        )
        
        request = RetrievalRequest(
            query="What is the project status?",
            mode=QueryModeDTO.HYBRID,
        )
        
        response = await usecase.execute(request)
        
        assert response.content is not None
        assert response.mode == QueryModeDTO.HYBRID
    
    @pytest.mark.asyncio
    async def test_retrieval_with_different_modes(
        self,
        mock_lightrag_service,
    ):
        """Test retrieval with different query modes."""
        usecase = RetrievalUseCase(
            lightrag_service=mock_lightrag_service,
        )
        
        modes = [
            QueryModeDTO.NAIVE,
            QueryModeDTO.LOCAL,
            QueryModeDTO.GLOBAL,
            QueryModeDTO.HYBRID,
            QueryModeDTO.MIX,
        ]
        
        for mode in modes:
            request = RetrievalRequest(query="Test query", mode=mode)
            response = await usecase.execute(request)
            assert response.mode == mode
    
    @pytest.mark.asyncio
    async def test_retrieval_with_references(
        self,
        mock_lightrag_service,
        mock_chunk_repository,
    ):
        """Test retrieval with references."""
        usecase = RetrievalUseCase(
            lightrag_service=mock_lightrag_service,
            chunk_repository=mock_chunk_repository,
            enrich_with_locators=True,
        )
        
        request = RetrievalRequest(
            query="Test query",
            include_references=True,
        )
        
        response = await usecase.execute(request)
        
        assert response.references is not None
    
    @pytest.mark.asyncio
    async def test_retrieval_with_context_only(
        self,
        mock_lightrag_service,
    ):
        """Test retrieval with only_context option."""
        usecase = RetrievalUseCase(
            lightrag_service=mock_lightrag_service,
        )
        
        request = RetrievalRequest(
            query="Test query",
            only_context=True,
        )
        
        response = await usecase.execute(request)
        
        mock_lightrag_service.query.assert_called_once()
        call_kwargs = mock_lightrag_service.query.call_args[1]
        assert call_kwargs["only_context"] is True
    
    @pytest.mark.asyncio
    async def test_retrieval_with_conversation_history(
        self,
        mock_lightrag_service,
    ):
        """Test retrieval with conversation history."""
        usecase = RetrievalUseCase(
            lightrag_service=mock_lightrag_service,
        )
        
        history = [
            {"role": "user", "content": "Previous question"},
            {"role": "assistant", "content": "Previous answer"},
        ]
        
        request = RetrievalRequest(
            query="Follow-up question",
            conversation_history=history,
        )
        
        response = await usecase.execute(request)
        
        mock_lightrag_service.query.assert_called_once()
        call_kwargs = mock_lightrag_service.query.call_args[1]
        assert call_kwargs["conversation_history"] == history
    
    @pytest.mark.asyncio
    async def test_retrieval_get_entity(
        self,
        mock_lightrag_service,
    ):
        """Test getting entity details."""
        usecase = RetrievalUseCase(
            lightrag_service=mock_lightrag_service,
        )
        
        entity = await usecase.get_entity("Test Entity")
        
        assert entity is not None
        assert entity["name"] == "Test Entity"
    
    @pytest.mark.asyncio
    async def test_retrieval_get_entity_not_found(
        self,
        mock_lightrag_service,
    ):
        """Test getting entity that doesn't exist."""
        mock_lightrag_service.get_entity.return_value = None
        
        usecase = RetrievalUseCase(
            lightrag_service=mock_lightrag_service,
        )
        
        entity = await usecase.get_entity("Non-existent Entity")
        
        assert entity is None
    
    @pytest.mark.asyncio
    async def test_retrieval_get_chunks_by_document(
        self,
        mock_lightrag_service,
        mock_chunk_repository,
    ):
        """Test getting chunks by document ID."""
        from ..domain.entities import Chunk
        
        chunk = Chunk(
            id=uuid4(),
            document_id=uuid4(),
            content="Test chunk content",
            locator={"page": 1},
        )
        mock_chunk_repository.list_by_document.return_value = [chunk]
        
        usecase = RetrievalUseCase(
            lightrag_service=mock_lightrag_service,
            chunk_repository=mock_chunk_repository,
        )
        
        chunks = await usecase.get_chunks_by_document(uuid4())
        
        assert isinstance(chunks, list)
    
    @pytest.mark.asyncio
    async def test_retrieval_search_chunks(
        self,
        mock_lightrag_service,
        mock_chunk_repository,
    ):
        """Test searching chunks."""
        from ..domain.entities import Chunk
        
        chunk = Chunk(
            id=uuid4(),
            document_id=uuid4(),
            content="Relevant content",
        )
        mock_chunk_repository.search_by_content.return_value = [chunk]
        
        usecase = RetrievalUseCase(
            lightrag_service=mock_lightrag_service,
            chunk_repository=mock_chunk_repository,
        )
        
        results = await usecase.search_chunks("relevant query")
        
        assert isinstance(results, list)
    
    @pytest.mark.asyncio
    async def test_retrieval_export_graph(
        self,
        mock_lightrag_service,
    ):
        """Test exporting the knowledge graph."""
        usecase = RetrievalUseCase(
            lightrag_service=mock_lightrag_service,
        )
        
        result = await usecase.export_graph(format="json")
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_retrieval_handles_exception(
        self,
        mock_lightrag_service,
    ):
        """Test that exceptions are handled gracefully."""
        mock_lightrag_service.query.side_effect = Exception("Query failed")
        
        usecase = RetrievalUseCase(
            lightrag_service=mock_lightrag_service,
        )
        
        request = RetrievalRequest(query="Test query")
        
        response = await usecase.execute(request)
        
        assert "Error" in response.content


class TestQueryModeConversion:
    """Tests for query mode conversion between DTO and domain."""
    
    def test_query_mode_dto_to_domain_mapping(self):
        """Test that all DTO modes have corresponding domain modes."""
        mapping = {
            QueryModeDTO.NAIVE: QueryMode.NAIVE,
            QueryModeDTO.LOCAL: QueryMode.LOCAL,
            QueryModeDTO.GLOBAL: QueryMode.GLOBAL,
            QueryModeDTO.HYBRID: QueryMode.HYBRID,
            QueryModeDTO.MIX: QueryMode.MIX,
            QueryModeDTO.BYPASS: QueryMode.BYPASS,
        }
        
        for dto_mode, domain_mode in mapping.items():
            assert dto_mode.value == domain_mode.value


class TestIngestionResult:
    """Tests for the IngestionResult class."""
    
    def test_ingestion_result_creation_success(self):
        """Test creating a successful IngestionResult."""
        doc_id = uuid4()
        result = IngestionResult(
            success=True,
            document_id=doc_id,
            chunks_created=10,
            entities_extracted=5,
            relationships_created=3,
        )
        
        assert result.success is True
        assert result.document_id == doc_id
        assert result.chunks_created == 10
        assert result.entities_extracted == 5
        assert result.relationships_created == 3
        assert result.error_message is None
    
    def test_ingestion_result_creation_failure(self):
        """Test creating a failed IngestionResult."""
        doc_id = uuid4()
        result = IngestionResult(
            success=False,
            document_id=doc_id,
            error_message="Processing failed",
        )
        
        assert result.success is False
        assert result.error_message == "Processing failed"


class TestRetrievalResult:
    """Tests for the RetrievalResult class."""
    
    def test_retrieval_result_creation(self):
        """Test creating a RetrievalResult."""
        result = RetrievalResult(
            content="Retrieved content",
            mode=QueryMode.HYBRID,
            references=[{"doc_id": "123"}],
            entities=[{"name": "Entity"}],
            context_used="Context text",
        )
        
        assert result.content == "Retrieved content"
        assert result.mode == QueryMode.HYBRID
        assert len(result.references) == 1
        assert len(result.entities) == 1
        assert result.context_used == "Context text"
    
    def test_retrieval_result_defaults(self):
        """Test RetrievalResult default values."""
        result = RetrievalResult(
            content="Content",
            mode=QueryMode.NAIVE,
        )
        
        assert result.references == []
        assert result.entities == []
        assert result.context_used is None