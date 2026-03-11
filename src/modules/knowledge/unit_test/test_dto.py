"""
Unit Tests for Application DTOs

Tests for request and response models in the application layer.
"""
import pytest
from uuid import uuid4, UUID
from datetime import datetime

from ..application.dto import (
    QueryModeDTO,
    IngestionRequest,
    IngestionResponse,
    RetrievalRequest,
    RetrievalResponse,
    DocumentResponse,
    DocumentListResponse,
    DataSourceResponse,
    EntityResponse,
    HealthResponse,
)


class TestQueryModeDTO:
    """Tests for the QueryModeDTO enum."""
    
    def test_query_mode_dto_values(self):
        """Test that QueryModeDTO has expected values."""
        assert QueryModeDTO.NAIVE == "naive"
        assert QueryModeDTO.LOCAL == "local"
        assert QueryModeDTO.GLOBAL == "global"
        assert QueryModeDTO.HYBRID == "hybrid"
        assert QueryModeDTO.MIX == "mix"
        assert QueryModeDTO.BYPASS == "bypass"


class TestIngestionRequest:
    """Tests for the IngestionRequest DTO."""
    
    def test_ingestion_request_creation_minimal(self):
        """Test creating an IngestionRequest with minimal data."""
        request = IngestionRequest()
        
        assert request.content is None
        assert request.file_path is None
        assert request.document_id is None
        assert request.data_source_id is None
        assert request.document_type == "txt"
        assert request.title is None
        assert request.metadata is None
    
    def test_ingestion_request_with_content(self):
        """Test creating an IngestionRequest with content."""
        request = IngestionRequest(
            content="Test document content",
            title="Test Document",
            document_type="md",
        )
        
        assert request.content == "Test document content"
        assert request.title == "Test Document"
        assert request.document_type == "md"
    
    def test_ingestion_request_with_file_path(self):
        """Test creating an IngestionRequest with file path."""
        request = IngestionRequest(
            file_path="/path/to/document.pdf",
            document_type="pdf",
        )
        
        assert request.file_path == "/path/to/document.pdf"
        assert request.document_type == "pdf"
    
    def test_ingestion_request_with_document_id(self):
        """Test creating an IngestionRequest for re-ingestion."""
        doc_id = uuid4()
        request = IngestionRequest(document_id=doc_id)
        
        assert request.document_id == doc_id
    
    def test_ingestion_request_with_metadata(self):
        """Test creating an IngestionRequest with metadata."""
        metadata = {"author": "John Doe", "version": "1.0"}
        request = IngestionRequest(
            content="Test content",
            metadata=metadata,
        )
        
        assert request.metadata == metadata
        assert request.metadata["author"] == "John Doe"


class TestIngestionResponse:
    """Tests for the IngestionResponse DTO."""
    
    def test_ingestion_response_creation(self):
        """Test creating an IngestionResponse."""
        doc_id = uuid4()
        response = IngestionResponse(
            success=True,
            document_id=doc_id,
            message="Document ingested successfully",
        )
        
        assert response.success is True
        assert response.document_id == doc_id
        assert response.message == "Document ingested successfully"
        assert response.chunks_created == 0
        assert response.entities_extracted == 0
        assert response.relationships_created == 0
    
    def test_ingestion_response_with_counts(self):
        """Test creating an IngestionResponse with counts."""
        doc_id = uuid4()
        response = IngestionResponse(
            success=True,
            document_id=doc_id,
            message="Success",
            chunks_created=10,
            entities_extracted=5,
            relationships_created=8,
        )
        
        assert response.chunks_created == 10
        assert response.entities_extracted == 5
        assert response.relationships_created == 8
    
    def test_ingestion_response_failure(self):
        """Test creating a failure IngestionResponse."""
        doc_id = uuid4()
        response = IngestionResponse(
            success=False,
            document_id=doc_id,
            message="Ingestion failed: Invalid file format",
        )
        
        assert response.success is False
        assert "Invalid file format" in response.message


class TestRetrievalRequest:
    """Tests for the RetrievalRequest DTO."""
    
    def test_retrieval_request_creation_minimal(self):
        """Test creating a RetrievalRequest with minimal data."""
        request = RetrievalRequest(query="What is the project status?")
        
        assert request.query == "What is the project status?"
        assert request.mode == QueryModeDTO.HYBRID
        assert request.top_k == 60
        assert request.include_references is False
        assert request.only_context is False
        assert request.conversation_history is None
    
    def test_retrieval_request_with_all_options(self):
        """Test creating a RetrievalRequest with all options."""
        history = [
            {"role": "user", "content": "Previous question"},
            {"role": "assistant", "content": "Previous answer"},
        ]
        request = RetrievalRequest(
            query="Follow-up question",
            mode=QueryModeDTO.LOCAL,
            top_k=20,
            include_references=True,
            only_context=True,
            conversation_history=history,
        )
        
        assert request.query == "Follow-up question"
        assert request.mode == QueryModeDTO.LOCAL
        assert request.top_k == 20
        assert request.include_references is True
        assert request.only_context is True
        assert request.conversation_history == history
    
    def test_retrieval_request_mode_validation(self):
        """Test that all query modes are valid."""
        for mode in QueryModeDTO:
            request = RetrievalRequest(query="test", mode=mode)
            assert request.mode == mode
    
    def test_retrieval_request_top_k_validation(self):
        """Test top_k validation bounds."""
        # Valid values
        request = RetrievalRequest(query="test", top_k=1)
        assert request.top_k == 1
        
        request = RetrievalRequest(query="test", top_k=100)
        assert request.top_k == 100


class TestRetrievalResponse:
    """Tests for the RetrievalResponse DTO."""
    
    def test_retrieval_response_creation(self):
        """Test creating a RetrievalResponse."""
        response = RetrievalResponse(
            content="This is the retrieved content.",
            mode=QueryModeDTO.HYBRID,
        )
        
        assert response.content == "This is the retrieved content."
        assert response.mode == QueryModeDTO.HYBRID
        assert response.references == []
        assert response.entities == []
        assert response.context_used is None
    
    def test_retrieval_response_with_references(self):
        """Test creating a RetrievalResponse with references."""
        references = [
            {"document_id": str(uuid4()), "chunk_index": 5},
            {"document_id": str(uuid4()), "chunk_index": 12},
        ]
        response = RetrievalResponse(
            content="Response content",
            mode=QueryModeDTO.LOCAL,
            references=references,
        )
        
        assert len(response.references) == 2
        assert response.references[0]["chunk_index"] == 5
    
    def test_retrieval_response_with_entities(self):
        """Test creating a RetrievalResponse with entities."""
        entities = [
            {"name": "Project Alpha", "type": "project"},
            {"name": "John Doe", "type": "person"},
        ]
        response = RetrievalResponse(
            content="Response",
            mode=QueryModeDTO.MIX,
            entities=entities,
        )
        
        assert len(response.entities) == 2
        assert response.entities[0]["name"] == "Project Alpha"
    
    def test_retrieval_response_with_context(self):
        """Test creating a RetrievalResponse with context used."""
        response = RetrievalResponse(
            content="Generated response",
            mode=QueryModeDTO.HYBRID,
            context_used="Retrieved context text...",
        )
        
        assert response.context_used == "Retrieved context text..."


class TestDocumentResponse:
    """Tests for the DocumentResponse DTO."""
    
    def test_document_response_creation(self):
        """Test creating a DocumentResponse."""
        doc_id = uuid4()
        source_id = uuid4()
        now = datetime.utcnow()
        
        response = DocumentResponse(
            id=doc_id,
            data_source_id=source_id,
            document_type="pdf",
            title="Test Document",
            status="completed",
            file_path="/test/path.pdf",
            file_size=1024,
            created_at=now,
            updated_at=now,
        )
        
        assert response.id == doc_id
        assert response.data_source_id == source_id
        assert response.document_type == "pdf"
        assert response.title == "Test Document"
        assert response.status == "completed"
        assert response.file_size == 1024
    
    def test_document_response_with_metadata(self):
        """Test creating a DocumentResponse with metadata."""
        metadata = {"author": "Test Author"}
        response = DocumentResponse(
            id=uuid4(),
            data_source_id=uuid4(),
            document_type="txt",
            title="Test",
            status="completed",
            file_path=None,
            file_size=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            metadata=metadata,
        )
        
        assert response.metadata == metadata


class TestDocumentListResponse:
    """Tests for the DocumentListResponse DTO."""
    
    def test_document_list_response_creation(self):
        """Test creating a DocumentListResponse."""
        documents = [
            DocumentResponse(
                id=uuid4(),
                data_source_id=uuid4(),
                document_type="pdf",
                title="Doc 1",
                status="completed",
                file_path=None,
                file_size=None,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            ),
            DocumentResponse(
                id=uuid4(),
                data_source_id=uuid4(),
                document_type="md",
                title="Doc 2",
                status="pending",
                file_path=None,
                file_size=None,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            ),
        ]
        
        response = DocumentListResponse(
            documents=documents,
            total=2,
            limit=100,
            offset=0,
        )
        
        assert len(response.documents) == 2
        assert response.total == 2
        assert response.limit == 100
        assert response.offset == 0
    
    def test_document_list_response_empty(self):
        """Test creating an empty DocumentListResponse."""
        response = DocumentListResponse(
            documents=[],
            total=0,
            limit=100,
            offset=0,
        )
        
        assert len(response.documents) == 0
        assert response.total == 0


class TestDataSourceResponse:
    """Tests for the DataSourceResponse DTO."""
    
    def test_data_source_response_creation(self):
        """Test creating a DataSourceResponse."""
        source_id = uuid4()
        now = datetime.utcnow()
        
        response = DataSourceResponse(
            id=source_id,
            name="google_drive",
            description="Company Google Drive",
            is_active=True,
            created_at=now,
        )
        
        assert response.id == source_id
        assert response.name == "google_drive"
        assert response.description == "Company Google Drive"
        assert response.is_active is True


class TestEntityResponse:
    """Tests for the EntityResponse DTO."""
    
    def test_entity_response_creation(self):
        """Test creating an EntityResponse."""
        response = EntityResponse(
            name="Project Alpha",
            description="A machine learning project",
            entity_type="project",
            metadata={"status": "active"},
            confidence=0.95,
        )
        
        assert response.name == "Project Alpha"
        assert response.description == "A machine learning project"
        assert response.entity_type == "project"
        assert response.metadata == {"status": "active"}
        assert response.confidence == 0.95
    
    def test_entity_response_minimal(self):
        """Test creating an EntityResponse with minimal data."""
        response = EntityResponse(
            name="Test Entity",
            description=None,
            entity_type=None,
            confidence=None,
            metadata={},
        )
        
        assert response.name == "Test Entity"
        assert response.description is None
        assert response.entity_type is None
        assert response.confidence is None


class TestHealthResponse:
    """Tests for the HealthResponse DTO."""
    
    def test_health_response_creation(self):
        """Test creating a HealthResponse."""
        now = datetime.utcnow()
        
        response = HealthResponse(
            status="healthy",
            lightrag_initialized=True,
            database_connected=True,
            timestamp=now,
        )
        
        assert response.status == "healthy"
        assert response.lightrag_initialized is True
        assert response.database_connected is True
        assert response.timestamp == now
    
    def test_health_response_unhealthy(self):
        """Test creating an unhealthy HealthResponse."""
        response = HealthResponse(
            status="unhealthy",
            lightrag_initialized=False,
            database_connected=False,
            timestamp=datetime.utcnow(),
        )
        
        assert response.status == "unhealthy"
        assert response.lightrag_initialized is False
        assert response.database_connected is False