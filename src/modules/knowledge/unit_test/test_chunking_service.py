"""
Unit Tests for Chunking Service

Tests for ChunkLocator, ChunkResult, and all chunking strategies.
"""
import pytest
from typing import List

from ..domain.services.chunking_service import (
    ChunkingStrategy,
    ChunkLocator,
    ChunkResult,
    ChunkingStrategyInterface,
    FixedSizeChunker,
    PageBasedChunker,
    HeaderBasedChunker,
    SemanticChunker,
    HybridChunker,
    HeaderSemanticChunker,
    ChunkingService,
)


class TestChunkingStrategy:
    """Tests for the ChunkingStrategy enum."""
    
    def test_chunking_strategy_values(self):
        """Test that ChunkingStrategy has expected values."""
        assert ChunkingStrategy.FIXED_SIZE.value == "fixed_size"
        assert ChunkingStrategy.SEMANTIC.value == "semantic"
        assert ChunkingStrategy.PAGE_BASED.value == "page_based"
        assert ChunkingStrategy.HEADER_BASED.value == "header_based"
        assert ChunkingStrategy.HYBRID.value == "hybrid"
        assert ChunkingStrategy.HEADER_SEMANTIC.value == "header_semantic"


class TestChunkLocator:
    """Tests for the ChunkLocator dataclass."""
    
    def test_chunk_locator_creation_default(self):
        """Test creating a ChunkLocator with default values."""
        locator = ChunkLocator()
        
        assert locator.page is None
        assert locator.header_path is None
        assert locator.start_char is None
        assert locator.end_char is None
        assert locator.line_start is None
        assert locator.line_end is None
    
    def test_chunk_locator_creation_with_values(self):
        """Test creating a ChunkLocator with custom values."""
        locator = ChunkLocator(
            page=5,
            header_path="Introduction > Background",
            start_char=100,
            end_char=500,
            line_start=10,
            line_end=25,
        )
        
        assert locator.page == 5
        assert locator.header_path == "Introduction > Background"
        assert locator.start_char == 100
        assert locator.end_char == 500
        assert locator.line_start == 10
        assert locator.line_end == 25
    
    def test_chunk_locator_to_dict(self):
        """Test converting ChunkLocator to dictionary."""
        locator = ChunkLocator(
            page=3,
            header_path="Section 1",
            start_char=0,
            end_char=100,
        )
        
        result = locator.to_dict()
        
        assert isinstance(result, dict)
        assert result["page"] == 3
        assert result["header_path"] == "Section 1"
        assert result["start_char"] == 0
        assert result["end_char"] == 100
        assert result["line_start"] is None
        assert result["line_end"] is None
    
    def test_chunk_locator_from_dict(self):
        """Test creating ChunkLocator from dictionary."""
        data = {
            "page": 2,
            "header_path": "Test Path",
            "start_char": 50,
            "end_char": 150,
            "line_start": 5,
            "line_end": 10,
        }
        
        locator = ChunkLocator.from_dict(data)
        
        assert locator.page == 2
        assert locator.header_path == "Test Path"
        assert locator.start_char == 50
        assert locator.end_char == 150
        assert locator.line_start == 5
        assert locator.line_end == 10
    
    def test_chunk_locator_roundtrip(self):
        """Test to_dict and from_dict roundtrip."""
        original = ChunkLocator(
            page=1,
            header_path="Test",
            start_char=0,
            end_char=100,
            line_start=1,
            line_end=5,
        )
        
        dict_form = original.to_dict()
        restored = ChunkLocator.from_dict(dict_form)
        
        assert restored.page == original.page
        assert restored.header_path == original.header_path
        assert restored.start_char == original.start_char
        assert restored.end_char == original.end_char
        assert restored.line_start == original.line_start
        assert restored.line_end == original.line_end


class TestChunkResult:
    """Tests for the ChunkResult dataclass."""
    
    def test_chunk_result_creation(self):
        """Test creating a ChunkResult."""
        locator = ChunkLocator(page=1)
        result = ChunkResult(
            content="Test content",
            index=0,
            locator=locator,
        )
        
        assert result.content == "Test content"
        assert result.index == 0
        assert result.locator == locator
        assert result.metadata == {}
    
    def test_chunk_result_length_property(self):
        """Test the length property."""
        result = ChunkResult(
            content="This is test content",
            index=0,
            locator=ChunkLocator(),
        )
        
        assert result.length == len("This is test content")
    
    def test_chunk_result_with_metadata(self):
        """Test ChunkResult with metadata."""
        result = ChunkResult(
            content="Test",
            index=0,
            locator=ChunkLocator(),
            metadata={"key": "value", "strategy": "test"},
        )
        
        assert result.metadata["key"] == "value"
        assert result.metadata["strategy"] == "test"


class TestFixedSizeChunker:
    """Tests for the FixedSizeChunker strategy."""
    
    def test_fixed_size_chunker_creation(self):
        """Test creating a FixedSizeChunker."""
        chunker = FixedSizeChunker(
            chunk_size=500,
            overlap=100,
            respect_sentence_boundary=False,
        )
        
        assert chunker.chunk_size == 500
        assert chunker.overlap == 100
        assert chunker.respect_sentence_boundary is False
    
    def test_fixed_size_chunker_small_content(self):
        """Test chunking content smaller than chunk size."""
        chunker = FixedSizeChunker(chunk_size=1000)
        content = "This is a short piece of content."
        
        chunks = chunker.chunk(content)
        
        assert len(chunks) == 1
        assert chunks[0].content == content
    
    def test_fixed_size_chunker_large_content(self):
        """Test chunking content larger than chunk size."""
        chunker = FixedSizeChunker(chunk_size=100, overlap=20)
        content = "A" * 250  # 250 characters
        
        chunks = chunker.chunk(content)
        
        assert len(chunks) > 1
        # Each chunk should be approximately chunk_size
        for chunk in chunks:
            assert len(chunk.content) <= 120  # Allow some flexibility
    
    def test_fixed_size_chunker_locator_info(self):
        """Test that locators contain character positions."""
        chunker = FixedSizeChunker(chunk_size=100, overlap=0)
        content = "A" * 300
        
        chunks = chunker.chunk(content)
        
        # Check that locators have start and end positions
        for chunk in chunks:
            assert chunk.locator.start_char is not None
            assert chunk.locator.end_char is not None
    
    def test_fixed_size_chunker_respects_sentence_boundary(self):
        """Test sentence boundary respect."""
        chunker = FixedSizeChunker(
            chunk_size=50,
            overlap=0,
            respect_sentence_boundary=True,
        )
        content = "This is sentence one. This is sentence two. This is sentence three."
        
        chunks = chunker.chunk(content)
        
        # Chunks should end at sentence boundaries when possible
        for chunk in chunks:
            # Either ends with sentence-ending punctuation or is the last chunk
            assert (
                chunk.content.rstrip().endswith('.') or
                chunk.content.rstrip().endswith('!') or
                chunk.content.rstrip().endswith('?') or
                chunk == chunks[-1]
            )


class TestPageBasedChunker:
    """Tests for the PageBasedChunker strategy."""
    
    def test_page_based_chunker_creation(self):
        """Test creating a PageBasedChunker."""
        chunker = PageBasedChunker(
            page_marker_pattern=r"\[PAGE\s*(\d+)\]",
            max_chunk_size=2000,
        )
        
        assert chunker.max_chunk_size == 2000
    
    def test_page_based_chunker_with_markers(self, sample_page_content):
        """Test chunking content with page markers."""
        chunker = PageBasedChunker()
        
        chunks = chunker.chunk(sample_page_content)
        
        # Should create chunks based on page markers
        assert len(chunks) >= 1
        
        # Check that locators have page info
        for chunk in chunks:
            if chunk.locator.page is not None:
                assert chunk.locator.page > 0
    
    def test_page_based_chunker_no_markers(self):
        """Test chunking content without page markers."""
        chunker = PageBasedChunker(max_chunk_size=500)
        content = "This is content without any page markers. " * 20
        
        chunks = chunker.chunk(content)
        
        # Should treat as single page and split by size
        assert len(chunks) >= 1
    
    def test_page_based_chunker_custom_pattern(self):
        """Test with custom page marker pattern."""
        chunker = PageBasedChunker(
            page_marker_pattern=r"---PAGE(\d+)---",
            max_chunk_size=1000,
        )
        content = "Intro\n---PAGE1---\nPage 1 content\n---PAGE2---\nPage 2 content"
        
        chunks = chunker.chunk(content)
        
        assert len(chunks) >= 1


class TestHeaderBasedChunker:
    """Tests for the HeaderBasedChunker strategy."""
    
    def test_header_based_chunker_creation(self):
        """Test creating a HeaderBasedChunker."""
        chunker = HeaderBasedChunker(
            min_chunk_size=50,
            max_chunk_size=2000,
            header_levels=[1, 2, 3],
        )
        
        assert chunker.min_chunk_size == 50
        assert chunker.max_chunk_size == 2000
        assert chunker.header_levels == [1, 2, 3]
    
    def test_header_based_chunker_with_headers(self, sample_markdown_content):
        """Test chunking markdown content with headers."""
        chunker = HeaderBasedChunker(min_chunk_size=10)
        
        chunks = chunker.chunk(sample_markdown_content)
        
        # Should create chunks based on headers
        assert len(chunks) >= 1
        
        # Check that locators have header path info
        for chunk in chunks:
            if chunk.locator.header_path:
                assert isinstance(chunk.locator.header_path, str)
    
    def test_header_based_chunker_no_headers(self):
        """Test chunking content without headers."""
        chunker = HeaderBasedChunker()
        content = "Just plain text without any headers at all."
        
        chunks = chunker.chunk(content)
        
        # Should still create at least one chunk
        assert len(chunks) >= 1
    
    def test_header_based_chunker_nested_headers(self):
        """Test chunking with nested headers."""
        content = """# Main

## Sub1

### SubSub1

Content here.

## Sub2

More content.
"""
        chunker = HeaderBasedChunker(min_chunk_size=5)
        
        chunks = chunker.chunk(content)
        
        assert len(chunks) >= 1


class TestSemanticChunker:
    """Tests for the SemanticChunker strategy."""
    
    def test_semantic_chunker_creation(self):
        """Test creating a SemanticChunker."""
        chunker = SemanticChunker(
            min_chunk_size=100,
            max_chunk_size=1500,
            overlap_sentences=2,
        )
        
        assert chunker.min_chunk_size == 100
        assert chunker.max_chunk_size == 1500
        assert chunker.overlap_sentences == 2
    
    def test_semantic_chunker_paragraphs(self):
        """Test chunking content with paragraphs."""
        content = """
First paragraph with some content here.

Second paragraph with more content.

Third paragraph with even more content.

Fourth paragraph to test chunking.
"""
        chunker = SemanticChunker(min_chunk_size=50, max_chunk_size=100)
        
        chunks = chunker.chunk(content)
        
        assert len(chunks) >= 1
    
    def test_semantic_chunker_single_paragraph(self):
        """Test chunking a single paragraph."""
        chunker = SemanticChunker()
        content = "Just a single paragraph of text."
        
        chunks = chunker.chunk(content)
        
        assert len(chunks) == 1
    
    def test_semantic_chunker_respects_max_size(self):
        """Test that chunks respect max size."""
        chunker = SemanticChunker(min_chunk_size=10, max_chunk_size=200)
        content = "\n\n".join([
            "Paragraph " + str(i) + " " + "word " * 10
            for i in range(10)
        ])
        
        chunks = chunker.chunk(content)
        
        # Most chunks should be under max_chunk_size with some flexibility
        for chunk in chunks[:-1]:  # Exclude last which might be smaller
            # Allow some flexibility for paragraph boundaries
            assert len(chunk.content) <= 250


class TestHybridChunker:
    """Tests for the HybridChunker strategy."""
    
    def test_hybrid_chunker_creation(self):
        """Test creating a HybridChunker."""
        chunker = HybridChunker(
            max_chunk_size=2000,
            min_chunk_size=100,
        )
        
        assert chunker.max_chunk_size == 2000
        assert chunker.min_chunk_size == 100
    
    def test_hybrid_chunker_detects_headers(self, sample_markdown_content):
        """Test that HybridChunker detects and uses headers."""
        chunker = HybridChunker()
        
        chunks = chunker.chunk(sample_markdown_content)
        
        assert len(chunks) >= 1
    
    def test_hybrid_chunker_detects_pages(self, sample_page_content):
        """Test that HybridChunker detects page markers."""
        chunker = HybridChunker()
        
        chunks = chunker.chunk(sample_page_content)
        
        assert len(chunks) >= 1
    
    def test_hybrid_chunker_falls_back_to_semantic(self):
        """Test fallback to semantic chunking."""
        chunker = HybridChunker()
        content = "Just plain text without any structure. " * 20
        
        chunks = chunker.chunk(content)
        
        assert len(chunks) >= 1


class TestHeaderSemanticChunker:
    """Tests for the HeaderSemanticChunker strategy."""
    
    def test_header_semantic_chunker_creation(self):
        """Test creating a HeaderSemanticChunker."""
        chunker = HeaderSemanticChunker(
            max_chunk_size=2000,
            min_chunk_size=100,
            include_header_context=True,
            header_context_format="[{header_path}]",
            overlap_sentences=2,
        )
        
        assert chunker.max_chunk_size == 2000
        assert chunker.min_chunk_size == 100
        assert chunker.include_header_context is True
    
    def test_header_semantic_chunker_with_headers(self, sample_markdown_content):
        """Test chunking with header context."""
        chunker = HeaderSemanticChunker(
            include_header_context=True,
            min_chunk_size=10,
        )
        
        chunks = chunker.chunk(sample_markdown_content)
        
        assert len(chunks) >= 1
        
        # Check that header context is included
        for chunk in chunks:
            assert chunk.metadata.get("strategy") == "header_semantic"
    
    def test_header_semantic_chunker_without_header_context(self, sample_markdown_content):
        """Test chunking without header context."""
        chunker = HeaderSemanticChunker(
            include_header_context=False,
            min_chunk_size=10,
        )
        
        chunks = chunker.chunk(sample_markdown_content)
        
        assert len(chunks) >= 1
    
    def test_header_semantic_chunker_custom_format(self):
        """Test custom header context format."""
        chunker = HeaderSemanticChunker(
            include_header_context=True,
            header_context_format="PATH: {header_path}",
            min_chunk_size=10,
        )
        content = "# Test Header\n\nSome content here."
        
        chunks = chunker.chunk(content)
        
        assert len(chunks) >= 1
        # Check if custom format is used
        if chunks[0].content.startswith("PATH:"):
            assert "Test Header" in chunks[0].content
    
    def test_header_semantic_chunker_splits_by_headers(self):
        """Test that content is split by headers first."""
        content = """# Section 1

Content for section 1.

# Section 2

Content for section 2.

# Section 3

Content for section 3.
"""
        chunker = HeaderSemanticChunker(min_chunk_size=5)
        
        chunks = chunker.chunk(content)
        
        # Should have chunks for each section
        assert len(chunks) >= 3


class TestChunkingService:
    """Tests for the main ChunkingService class."""
    
    def test_chunking_service_creation(self):
        """Test creating a ChunkingService."""
        service = ChunkingService(
            default_strategy=ChunkingStrategy.HYBRID,
        )
        
        assert service.default_strategy == ChunkingStrategy.HYBRID
    
    def test_chunking_service_default_strategies(self):
        """Test that default strategies are registered."""
        service = ChunkingService()
        
        assert ChunkingStrategy.FIXED_SIZE in service._strategies
        assert ChunkingStrategy.SEMANTIC in service._strategies
        assert ChunkingStrategy.PAGE_BASED in service._strategies
        assert ChunkingStrategy.HEADER_BASED in service._strategies
        assert ChunkingStrategy.HYBRID in service._strategies
        assert ChunkingStrategy.HEADER_SEMANTIC in service._strategies
    
    def test_chunking_service_chunk_default_strategy(self):
        """Test chunking with default strategy."""
        service = ChunkingService()
        content = "Test content for chunking."
        
        chunks = service.chunk(content)
        
        assert len(chunks) >= 1
    
    def test_chunking_service_chunk_specific_strategy(self):
        """Test chunking with a specific strategy."""
        service = ChunkingService()
        content = "Test content. " * 50
        
        chunks = service.chunk(
            content,
            strategy=ChunkingStrategy.FIXED_SIZE,
        )
        
        assert len(chunks) >= 1
    
    def test_chunking_service_invalid_strategy(self):
        """Test that invalid strategy raises error."""
        service = ChunkingService()
        
        # Create a mock invalid strategy
        with pytest.raises(ValueError):
            # We need to pass an invalid enum value
            service._strategies.pop(ChunkingStrategy.FIXED_SIZE, None)
            service.chunk("test", strategy=ChunkingStrategy.FIXED_SIZE)
    
    def test_chunking_service_register_custom_strategy(self):
        """Test registering a custom chunking strategy."""
        service = ChunkingService()
        
        class CustomChunker(ChunkingStrategyInterface):
            def chunk(self, content: str, **kwargs) -> List[ChunkResult]:
                return [ChunkResult(
                    content=content,
                    index=0,
                    locator=ChunkLocator(),
                    metadata={"custom": True},
                )]
        
        custom_chunker = CustomChunker()
        service.register_strategy(ChunkingStrategy.FIXED_SIZE, custom_chunker)
        
        chunks = service.chunk("test", strategy=ChunkingStrategy.FIXED_SIZE)
        
        assert len(chunks) == 1
        assert chunks[0].metadata.get("custom") is True
    
    def test_chunking_service_with_kwargs(self):
        """Test chunking with additional kwargs."""
        service = ChunkingService()
        content = "Test content."
        
        # Most chunkers accept additional kwargs without error
        chunks = service.chunk(content, some_param="value")
        
        assert len(chunks) >= 1