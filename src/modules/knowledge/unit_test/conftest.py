"""
Shared Fixtures for Knowledge Module Unit Tests

Provides common fixtures and test utilities.
"""
import os
import pytest
from datetime import datetime, timedelta
from uuid import uuid4, UUID

# NIL_UUID for Python < 3.11 compatibility
NIL_UUID = UUID('00000000-0000-0000-0000-000000000000')
from unittest.mock import AsyncMock, MagicMock, patch

# Set test environment variables before importing modules
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("POSTGRES_PORT", "5432")
os.environ.setdefault("POSTGRES_USER", "test_user")
os.environ.setdefault("POSTGRES_PASSWORD", "test_password")
os.environ.setdefault("POSTGRES_DB", "test_db")
os.environ.setdefault("FIREWORKS_API_KEY", "test_api_key")
os.environ.setdefault("OPENAI_API_KEY", "test_openai_key")
os.environ.setdefault("LIGHTRAG_WORKING_DIR", "./test_rag_storage")


@pytest.fixture
def sample_uuid():
    """Generate a sample UUID for testing."""
    return uuid4()


@pytest.fixture
def sample_uuid_str():
    """Generate a sample UUID string for testing."""
    return str(uuid4())


@pytest.fixture
def sample_datetime():
    """Get a sample datetime for testing."""
    return datetime.utcnow()


@pytest.fixture
def sample_datetime_str():
    """Get a sample datetime string for testing."""
    return datetime.utcnow().isoformat()


@pytest.fixture
def mock_async_session():
    """Create a mock async database session."""
    session = AsyncMock()
    return session


@pytest.fixture
def mock_connection_pool():
    """Create a mock asyncpg connection pool."""
    pool = AsyncMock()
    
    async def mock_acquire():
        conn = AsyncMock()
        conn.fetchrow = AsyncMock()
        conn.fetch = AsyncMock()
        conn.execute = AsyncMock()
        conn.executemany = AsyncMock()
        return conn
    
    pool.acquire.return_value.__aenter__ = mock_acquire
    pool.acquire.return_value.__aexit__ = AsyncMock()
    
    return pool


@pytest.fixture
def sample_document_data():
    """Sample document data for testing."""
    return {
        "id": uuid4(),
        "data_source_id": uuid4(),
        "document_type": "pdf",
        "title": "Test Document",
        "content_hash": "sha256:abc123def456",
        "file_path": "/test/path/document.pdf",
        "file_size": 1024,
        "status": "pending",
        "metadata": {"author": "Test Author"},
        "error_message": None,
        "created_at": datetime.utcnow(),
        "created_by": NIL_UUID,
        "updated_at": datetime.utcnow(),
        "updated_by": NIL_UUID,
    }


@pytest.fixture
def sample_chunk_data():
    """Sample chunk data for testing."""
    return {
        "id": uuid4(),
        "document_id": uuid4(),
        "locator": {
            "page": 1,
            "header_path": "Introduction",
            "start_char": 0,
            "end_char": 500,
        },
        "content": "This is a sample chunk of text for testing purposes.",
        "length": 50,
        "chunk_index": 0,
        "valid_til": None,
        "embedding_status": "pending",
        "created_at": datetime.utcnow(),
        "created_by": NIL_UUID,
        "updated_at": datetime.utcnow(),
        "updated_by": NIL_UUID,
    }


@pytest.fixture
def sample_data_source_data():
    """Sample data source data for testing."""
    return {
        "id": uuid4(),
        "name": "google_drive",
        "description": "Test Google Drive source",
        "config": {"folder_id": "test_folder_123"},
        "is_active": True,
        "created_at": datetime.utcnow(),
        "created_by": NIL_UUID,
        "updated_at": datetime.utcnow(),
        "updated_by": NIL_UUID,
    }


@pytest.fixture
def sample_graph_entity_data():
    """Sample graph entity data for testing."""
    return {
        "id": uuid4(),
        "name": "Test Entity",
        "description": "A test entity for unit testing",
        "metadata": {"source": "test"},
        "reference": "chunk://test-chunk-id",
        "entity_type": "concept",
        "confidence": 0.95,
        "created_at": datetime.utcnow(),
        "created_by": NIL_UUID,
        "updated_at": datetime.utcnow(),
        "updated_by": NIL_UUID,
    }


@pytest.fixture
def sample_relationship_data():
    """Sample relationship data for testing."""
    return {
        "id": uuid4(),
        "name": "related_to",
        "source_entity_id": uuid4(),
        "target_entity_id": uuid4(),
        "description": "Test relationship",
        "metadata": {},
        "reference": None,
        "weight": 1.0,
        "confidence": 0.85,
        "created_at": datetime.utcnow(),
        "created_by": NIL_UUID,
        "updated_at": datetime.utcnow(),
        "updated_by": NIL_UUID,
    }


@pytest.fixture
def sample_vector_data():
    """Sample vector data for testing."""
    return {
        "id": uuid4(),
        "chunk_id": uuid4(),
        "embedding_model": "text-embedding-3-small",
        "dimension": 1536,
        "vector_data": [0.1] * 1536,  # Mock vector
        "created_at": datetime.utcnow(),
        "created_by": NIL_UUID,
        "updated_at": datetime.utcnow(),
        "updated_by": NIL_UUID,
    }


@pytest.fixture
def sample_content():
    """Sample document content for chunking tests."""
    return """
# Introduction

This is the introduction section of the document. It provides an overview
of the content that follows.

## Background

The background section contains historical context and relevant information
about the topic at hand.

## Objectives

The main objectives of this document are:
1. Explain the concept
2. Provide examples
3. Demonstrate usage

# Chapter 1: Getting Started

[PAGE 1]

This is the first page of the main content. It contains important information
about getting started with the system.

[PAGE 2]

The second page continues with more details about configuration and setup.

# Chapter 2: Advanced Topics

## Section 2.1: Configuration

Configuration is an important aspect of the system. Here we discuss
the various configuration options available.

## Section 2.2: Integration

Integration with other systems requires careful planning and execution.
"""


@pytest.fixture
def sample_markdown_content():
    """Sample markdown content for header-based chunking tests."""
    return """# Main Title

This is the introduction.

## Section 1

Content for section 1.

### Subsection 1.1

More detailed content.

## Section 2

Content for section 2.

# Another Main Section

Some final content.
"""


@pytest.fixture
def sample_page_content():
    """Sample content with page markers."""
    return """First page content here.

[PAGE 1]

Content of page 1.

[PAGE 2]

Content of page 2.

[PAGE 3]

Content of page 3.
"""


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )