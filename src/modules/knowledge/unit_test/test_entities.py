"""
Unit Tests for Domain Entities

Tests for base, data_source, document, chunk, vector, graph_entity, and relationship entities.
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4, UUID

# NIL_UUID for Python < 3.11 compatibility
NIL_UUID = UUID('00000000-0000-0000-0000-000000000000')

from ..domain.entities.base import BaseModel
from ..domain.entities.data_source import DataSource, DataSourceType
from ..domain.entities.document import Document, DocumentType, DocumentStatus
from ..domain.entities.chunk import Chunk, ChunkLocator
from ..domain.entities.vector import Vector
from ..domain.entities.graph_entity import GraphEntity
from ..domain.entities.relationship import Relationship


class TestBaseModel:
    """Tests for the BaseModel entity."""
    
    def test_base_model_creation(self):
        """Test creating a BaseModel instance."""
        model = BaseModel()
        
        assert model.id is not None
        assert isinstance(model.id, UUID)
        assert model.created_at is not None
        assert isinstance(model.created_at, datetime)
        assert model.updated_at is not None
        assert model.created_by == NIL_UUID
        assert model.updated_by == NIL_UUID
        assert model.deleted_at is None
        assert model.deleted_by is None
    
    def test_base_model_with_custom_values(self):
        """Test creating a BaseModel with custom values."""
        custom_id = uuid4()
        custom_user = uuid4()
        now = datetime.utcnow()
        
        model = BaseModel(
            id=custom_id,
            created_at=now,
            created_by=custom_user,
            updated_at=now,
            updated_by=custom_user,
        )
        
        assert model.id == custom_id
        assert model.created_at == now
        assert model.created_by == custom_user
        assert model.updated_at == now
        assert model.updated_by == custom_user
    
    def test_is_deleted_false_initially(self):
        """Test that is_deleted returns False initially."""
        model = BaseModel()
        assert model.is_deleted() is False
    
    def test_is_deleted_true_after_mark_deleted(self):
        """Test that is_deleted returns True after mark_deleted."""
        model = BaseModel()
        model.mark_deleted()
        
        assert model.is_deleted() is True
        assert model.deleted_at is not None
        assert isinstance(model.deleted_at, datetime)
    
    def test_mark_deleted_with_user(self):
        """Test mark_deleted with a specific user."""
        model = BaseModel()
        user_id = uuid4()
        model.mark_deleted(deleted_by=user_id)
        
        assert model.is_deleted() is True
        assert model.deleted_by == user_id
    
    def test_mark_updated(self):
        """Test mark_updated updates timestamp."""
        model = BaseModel()
        original_updated_at = model.updated_at
        
        # Small delay to ensure time difference
        import time
        time.sleep(0.01)
        
        user_id = uuid4()
        model.mark_updated(updated_by=user_id)
        
        assert model.updated_at > original_updated_at
        assert model.updated_by == user_id
    
    def test_from_attributes_config(self):
        """Test that from_attributes config is enabled."""
        assert BaseModel.Config.from_attributes is True


class TestDataSourceType:
    """Tests for the DataSourceType enum."""
    
    def test_data_source_type_values(self):
        """Test that DataSourceType has expected values."""
        assert DataSourceType.GOOGLE_DRIVE == "google_drive"
        assert DataSourceType.ONE_DRIVE == "one_drive"
        assert DataSourceType.MS_SHARE_POINT == "ms_share_point"
        assert DataSourceType.LOCAL_FILESYSTEM == "local_filesystem"
        assert DataSourceType.WEB == "web"
        assert DataSourceType.API == "api"
    
    def test_default_method(self):
        """Test the default class method."""
        default = DataSourceType.default()
        assert default == DataSourceType.GOOGLE_DRIVE


class TestDataSource:
    """Tests for the DataSource entity."""
    
    def test_data_source_creation(self):
        """Test creating a DataSource instance."""
        source = DataSource()
        
        assert source.id is not None
        assert source.name == DataSourceType.GOOGLE_DRIVE  # Default
        assert source.description is None
        assert source.config is None
        assert source.is_active is True
    
    def test_data_source_with_values(self, sample_data_source_data):
        """Test creating a DataSource with custom values."""
        source = DataSource(
            name=DataSourceType.GOOGLE_DRIVE,
            description="Test Description",
            config={"key": "value"},
            is_active=False,
        )
        
        assert source.name == DataSourceType.GOOGLE_DRIVE
        assert source.description == "Test Description"
        assert source.config == {"key": "value"}
        assert source.is_active is False
    
    def test_data_source_inherits_base_model(self):
        """Test that DataSource inherits from BaseModel."""
        source = DataSource()
        assert hasattr(source, 'id')
        assert hasattr(source, 'created_at')
        assert hasattr(source, 'mark_deleted')
        assert hasattr(source, 'mark_updated')


class TestDocumentType:
    """Tests for the DocumentType enum."""
    
    def test_document_type_values(self):
        """Test that DocumentType has expected values."""
        assert DocumentType.PDF == "pdf"
        assert DocumentType.MD == "md"
        assert DocumentType.MARKDOWN == "markdown"
        assert DocumentType.TXT == "txt"
        assert DocumentType.JSON == "json"
        assert DocumentType.CSV == "csv"
    
    def test_from_extension_pdf(self):
        """Test from_extension for PDF."""
        assert DocumentType.from_extension(".pdf") == DocumentType.PDF
    
    def test_from_extension_md(self):
        """Test from_extension for Markdown."""
        assert DocumentType.from_extension(".md") == DocumentType.MD
        assert DocumentType.from_extension(".markdown") == DocumentType.MARKDOWN
    
    def test_from_extension_txt(self):
        """Test from_extension for text files."""
        assert DocumentType.from_extension(".txt") == DocumentType.TXT
    
    def test_from_extension_unknown(self):
        """Test from_extension returns TXT for unknown extensions."""
        assert DocumentType.from_extension(".unknown") == DocumentType.TXT
    
    def test_from_extension_case_insensitive(self):
        """Test from_extension is case insensitive."""
        assert DocumentType.from_extension(".PDF") == DocumentType.PDF
        assert DocumentType.from_extension(".Md") == DocumentType.MD


class TestDocumentStatus:
    """Tests for the DocumentStatus enum."""
    
    def test_document_status_values(self):
        """Test that DocumentStatus has expected values."""
        assert DocumentStatus.PENDING == "pending"
        assert DocumentStatus.PROCESSING == "processing"
        assert DocumentStatus.COMPLETED == "completed"
        assert DocumentStatus.FAILED == "failed"
        assert DocumentStatus.REINGESTING == "reingesting"


class TestDocument:
    """Tests for the Document entity."""
    
    def test_document_creation(self):
        """Test creating a Document instance."""
        data_source_id = uuid4()
        doc = Document(data_source_id=data_source_id)
        
        assert doc.id is not None
        assert doc.data_source_id == data_source_id
        assert doc.document_type == DocumentType.TXT
        assert doc.status == DocumentStatus.PENDING
        assert doc.title is None
        assert doc.content_hash is None
        assert doc.file_path is None
        assert doc.file_size is None
        assert doc.metadata is None
        assert doc.error_message is None
    
    def test_document_with_values(self, sample_document_data):
        """Test creating a Document with custom values."""
        doc = Document(
            data_source_id=sample_document_data["data_source_id"],
            document_type=DocumentType.PDF,
            title="Test Title",
            content_hash="abc123",
            file_path="/test/path",
            file_size=1024,
            metadata={"key": "value"},
        )
        
        assert doc.document_type == DocumentType.PDF
        assert doc.title == "Test Title"
        assert doc.content_hash == "abc123"
        assert doc.file_path == "/test/path"
        assert doc.file_size == 1024
        assert doc.metadata == {"key": "value"}
    
    def test_mark_processing(self):
        """Test mark_processing method."""
        doc = Document(data_source_id=uuid4())
        original_updated_at = doc.updated_at
        
        import time
        time.sleep(0.01)
        
        doc.mark_processing()
        
        assert doc.status == DocumentStatus.PROCESSING
        assert doc.updated_at > original_updated_at
    
    def test_mark_completed(self):
        """Test mark_completed method."""
        doc = Document(data_source_id=uuid4())
        doc.status = DocumentStatus.PROCESSING
        
        doc.mark_completed()
        
        assert doc.status == DocumentStatus.COMPLETED
    
    def test_mark_failed(self):
        """Test mark_failed method."""
        doc = Document(data_source_id=uuid4())
        doc.status = DocumentStatus.PROCESSING
        
        doc.mark_failed("Test error message")
        
        assert doc.status == DocumentStatus.FAILED
        assert doc.error_message == "Test error message"
    
    def test_mark_reingesting(self):
        """Test mark_reingesting method."""
        doc = Document(data_source_id=uuid4())
        doc.status = DocumentStatus.COMPLETED
        
        doc.mark_reingesting()
        
        assert doc.status == DocumentStatus.REINGESTING


class TestChunk:
    """Tests for the Chunk entity."""
    
    def test_chunk_creation(self):
        """Test creating a Chunk instance."""
        document_id = uuid4()
        content = "Test content"
        
        chunk = Chunk(document_id=document_id, content=content)
        
        assert chunk.id is not None
        assert chunk.document_id == document_id
        assert chunk.content == content
        assert chunk.length == len(content)
        assert chunk.locator == {}
        assert chunk.chunk_index == 0
        assert chunk.valid_til is None
        assert chunk.embedding_status == "pending"
    
    def test_chunk_length_auto_calculated(self):
        """Test that chunk length is auto-calculated."""
        content = "This is test content with specific length"
        chunk = Chunk(document_id=uuid4(), content=content)
        
        assert chunk.length == len(content)
    
    def test_chunk_with_locator(self):
        """Test creating a Chunk with locator info."""
        locator = {
            "page": 5,
            "header_path": "Introduction > Background",
            "start_char": 100,
            "end_char": 500,
        }
        
        chunk = Chunk(
            document_id=uuid4(),
            content="Test content",
            locator=locator,
        )
        
        assert chunk.locator == locator
        assert chunk.locator["page"] == 5
    
    def test_is_valid_no_expiry(self):
        """Test is_valid returns True when no expiry."""
        chunk = Chunk(document_id=uuid4(), content="Test")
        
        assert chunk.is_valid() is True
    
    def test_is_valid_future_expiry(self):
        """Test is_valid returns True for future expiry."""
        future = datetime.utcnow() + timedelta(days=1)
        chunk = Chunk(
            document_id=uuid4(),
            content="Test",
            valid_til=future,
        )
        
        assert chunk.is_valid() is True
    
    def test_is_valid_past_expiry(self):
        """Test is_valid returns False for past expiry."""
        past = datetime.utcnow() - timedelta(days=1)
        chunk = Chunk(
            document_id=uuid4(),
            content="Test",
            valid_til=past,
        )
        
        assert chunk.is_valid() is False
    
    def test_mark_embedding_completed(self):
        """Test mark_embedding_completed method."""
        chunk = Chunk(document_id=uuid4(), content="Test")
        
        chunk.mark_embedding_completed()
        
        assert chunk.embedding_status == "completed"
    
    def test_mark_embedding_failed(self):
        """Test mark_embedding_failed method."""
        chunk = Chunk(document_id=uuid4(), content="Test")
        
        chunk.mark_embedding_failed()
        
        assert chunk.embedding_status == "failed"


class TestVector:
    """Tests for the Vector entity."""
    
    def test_vector_creation(self):
        """Test creating a Vector instance."""
        chunk_id = uuid4()
        
        vector = Vector(chunk_id=chunk_id)
        
        assert vector.id is not None
        assert vector.chunk_id == chunk_id
        assert vector.embedding_model == "text-embedding-3-small"
        assert vector.dimension == 1536
        assert vector.vector_data is None
    
    def test_vector_with_data(self):
        """Test creating a Vector with data."""
        chunk_id = uuid4()
        vector_data = [0.1] * 1536
        
        vector = Vector(
            chunk_id=chunk_id,
            embedding_model="custom-model",
            dimension=768,
            vector_data=vector_data,
        )
        
        assert vector.embedding_model == "custom-model"
        assert vector.dimension == 768
        assert vector.vector_data == vector_data


class TestGraphEntity:
    """Tests for the GraphEntity entity."""
    
    def test_graph_entity_creation(self):
        """Test creating a GraphEntity instance."""
        entity = GraphEntity(name="Test Entity")
        
        assert entity.id is not None
        assert entity.name == "Test Entity"
        assert entity.description is None
        assert entity.metadata == {}
        assert entity.reference is None
        assert entity.entity_type is None
        assert entity.confidence is None
    
    def test_graph_entity_with_values(self, sample_graph_entity_data):
        """Test creating a GraphEntity with custom values."""
        entity = GraphEntity(
            name=sample_graph_entity_data["name"],
            description=sample_graph_entity_data["description"],
            metadata=sample_graph_entity_data["metadata"],
            reference=sample_graph_entity_data["reference"],
            entity_type=sample_graph_entity_data["entity_type"],
            confidence=sample_graph_entity_data["confidence"],
        )
        
        assert entity.name == sample_graph_entity_data["name"]
        assert entity.description == sample_graph_entity_data["description"]
        assert entity.metadata == sample_graph_entity_data["metadata"]
        assert entity.entity_type == sample_graph_entity_data["entity_type"]
        assert entity.confidence == sample_graph_entity_data["confidence"]
    
    def test_confidence_validation_valid(self):
        """Test confidence score validation with valid values."""
        entity = GraphEntity(name="Test", confidence=0.5)
        assert entity.confidence == 0.5
        
        entity = GraphEntity(name="Test", confidence=0.0)
        assert entity.confidence == 0.0
        
        entity = GraphEntity(name="Test", confidence=1.0)
        assert entity.confidence == 1.0


class TestRelationship:
    """Tests for the Relationship entity."""
    
    def test_relationship_creation(self):
        """Test creating a Relationship instance."""
        rel = Relationship(name="related_to")
        
        assert rel.id is not None
        assert rel.name == "related_to"
        assert rel.source_entity_id is None
        assert rel.target_entity_id is None
        assert rel.description is None
        assert rel.metadata == {}
        assert rel.reference is None
        assert rel.weight == 1.0
        assert rel.confidence is None
    
    def test_relationship_with_values(self, sample_relationship_data):
        """Test creating a Relationship with custom values."""
        rel = Relationship(
            name=sample_relationship_data["name"],
            source_entity_id=sample_relationship_data["source_entity_id"],
            target_entity_id=sample_relationship_data["target_entity_id"],
            description=sample_relationship_data["description"],
            metadata=sample_relationship_data["metadata"],
            weight=sample_relationship_data["weight"],
            confidence=sample_relationship_data["confidence"],
        )
        
        assert rel.name == sample_relationship_data["name"]
        assert rel.source_entity_id == sample_relationship_data["source_entity_id"]
        assert rel.target_entity_id == sample_relationship_data["target_entity_id"]
        assert rel.weight == sample_relationship_data["weight"]
        assert rel.confidence == sample_relationship_data["confidence"]
    
    def test_weight_default(self):
        """Test that weight defaults to 1.0."""
        rel = Relationship(name="test")
        assert rel.weight == 1.0