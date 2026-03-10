"""
Chunking Service

Provides configurable document chunking strategies with locator metadata.
"""
import re
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum

logger = logging.getLogger(__name__)


class ChunkingStrategy(Enum):
    """Available chunking strategies."""
    FIXED_SIZE = "fixed_size"
    SEMANTIC = "semantic"
    PAGE_BASED = "page_based"
    HEADER_BASED = "header_based"
    HYBRID = "hybrid"
    HEADER_SEMANTIC = "header_semantic"


@dataclass
class ChunkLocator:
    """
    Locator information for a chunk.
    
    Helps identify exactly where in a document a chunk came from.
    """
    page: Optional[int] = None
    header_path: Optional[str] = None  # e.g., "Chapter 2 > Section 1 > Subsection A"
    start_char: Optional[int] = None
    end_char: Optional[int] = None
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "page": self.page,
            "header_path": self.header_path,
            "start_char": self.start_char,
            "end_char": self.end_char,
            "line_start": self.line_start,
            "line_end": self.line_end,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChunkLocator":
        """Create from dictionary."""
        return cls(
            page=data.get("page"),
            header_path=data.get("header_path"),
            start_char=data.get("start_char"),
            end_char=data.get("end_char"),
            line_start=data.get("line_start"),
            line_end=data.get("line_end"),
        )


@dataclass
class ChunkResult:
    """
    Result of chunking a document.
    """
    content: str
    index: int
    locator: ChunkLocator
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def length(self) -> int:
        """Return the length of the chunk content."""
        return len(self.content)


class ChunkingStrategyInterface(ABC):
    """Abstract base class for chunking strategies."""
    
    @abstractmethod
    def chunk(self, content: str, **kwargs) -> List[ChunkResult]:
        """
        Chunk the content into smaller pieces.
        
        Args:
            content: The document content to chunk
            **kwargs: Additional strategy-specific parameters
            
        Returns:
            List of ChunkResult objects
        """
        pass


class FixedSizeChunker(ChunkingStrategyInterface):
    """
    Chunks content into fixed-size pieces with optional overlap.
    
    Good for: Simple, predictable chunk sizes
    """
    
    def __init__(
        self,
        chunk_size: int = 1000,
        overlap: int = 200,
        respect_sentence_boundary: bool = True,
    ):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.respect_sentence_boundary = respect_sentence_boundary
    
    def chunk(self, content: str, **kwargs) -> List[ChunkResult]:
        """Chunk content into fixed-size pieces."""
        chunks = []
        start = 0
        index = 0
        
        while start < len(content):
            end = start + self.chunk_size
            
            # Adjust to respect sentence boundary
            if self.respect_sentence_boundary and end < len(content):
                # Look for sentence end within a window
                window = content[end - 100:end + 100]
                sentence_end = re.search(r'[.!?]\s+', window)
                if sentence_end:
                    end = end - 100 + sentence_end.end()
            
            chunk_content = content[start:min(end, len(content))].strip()
            
            if chunk_content:
                chunks.append(ChunkResult(
                    content=chunk_content,
                    index=index,
                    locator=ChunkLocator(
                        start_char=start,
                        end_char=end,
                    ),
                    metadata={"strategy": "fixed_size"},
                ))
                index += 1
            
            start = end - self.overlap if end < len(content) else len(content)
        
        return chunks


class PageBasedChunker(ChunkingStrategyInterface):
    """
    Chunks content by page markers.
    
    Good for: PDFs, documents with clear page breaks
    Expects: Content with page markers like [PAGE 1], --- Page 1 ---, etc.
    """
    
    # Common page marker patterns
    PAGE_PATTERNS = [
        r'\[PAGE\s*(\d+)\]',
        r'---\s*Page\s*(\d+)\s*---',
        r'\f',  # Form feed character
        r'Page\s*(\d+)',
    ]
    
    def __init__(
        self,
        page_marker_pattern: Optional[str] = None,
        max_chunk_size: int = 2000,
    ):
        self.page_marker_pattern = page_marker_pattern
        self.max_chunk_size = max_chunk_size
    
    def chunk(self, content: str, **kwargs) -> List[ChunkResult]:
        """Chunk content by pages."""
        chunks = []
        
        # Use custom pattern or default patterns
        if self.page_marker_pattern:
            patterns = [self.page_marker_pattern]
        else:
            patterns = self.PAGE_PATTERNS
        
        # Try to find page breaks
        page_breaks = []
        for pattern in patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                page_num = match.group(1) if match.lastindex else len(page_breaks) + 1
                page_breaks.append((match.start(), int(page_num)))
        
        # Sort by position
        page_breaks.sort(key=lambda x: x[0])
        
        if not page_breaks:
            # No page markers found, treat as single page
            logger.warning("No page markers found, treating as single page")
            return self._chunk_large_content(content, 1)
        
        # Create chunks for each page
        for i, (pos, page_num) in enumerate(page_breaks):
            start = pos
            end = page_breaks[i + 1][0] if i + 1 < len(page_breaks) else len(content)
            page_content = content[start:end].strip()
            
            if page_content:
                # If page is too large, split it
                if len(page_content) > self.max_chunk_size:
                    page_chunks = self._split_large_chunk(page_content, page_num, start)
                    chunks.extend(page_chunks)
                else:
                    chunks.append(ChunkResult(
                        content=page_content,
                        index=len(chunks),
                        locator=ChunkLocator(
                            page=page_num,
                            start_char=start,
                            end_char=end,
                        ),
                        metadata={"strategy": "page_based"},
                    ))
        
        return chunks
    
    def _chunk_large_content(self, content: str, page: int) -> List[ChunkResult]:
        """Chunk large content without page markers."""
        chunks = []
        start = 0
        index = 0
        
        while start < len(content):
            end = start + self.max_chunk_size
            chunk_content = content[start:end].strip()
            
            if chunk_content:
                chunks.append(ChunkResult(
                    content=chunk_content,
                    index=index,
                    locator=ChunkLocator(
                        page=page,
                        start_char=start,
                        end_char=end,
                    ),
                    metadata={"strategy": "page_based"},
                ))
                index += 1
            
            start = end
        
        return chunks
    
    def _split_large_chunk(self, content: str, page: int, base_start: int) -> List[ChunkResult]:
        """Split a large page into smaller chunks."""
        chunks = []
        start = 0
        index_offset = 0
        
        while start < len(content):
            end = start + self.max_chunk_size
            chunk_content = content[start:end].strip()
            
            if chunk_content:
                chunks.append(ChunkResult(
                    content=chunk_content,
                    index=len(chunks),
                    locator=ChunkLocator(
                        page=page,
                        start_char=base_start + start,
                        end_char=base_start + end,
                    ),
                    metadata={"strategy": "page_based", "sub_chunk": True},
                ))
            
            start = end
        
        return chunks


class HeaderBasedChunker(ChunkingStrategyInterface):
    """
    Chunks content by markdown-style headers.
    
    Good for: Markdown documents, technical documentation
    Supports: #, ##, ###, etc.
    """
    
    HEADER_PATTERN = r'^(#{1,6})\s+(.+)$'
    
    def __init__(
        self,
        min_chunk_size: int = 100,
        max_chunk_size: int = 3000,
        header_levels: Optional[List[int]] = None,
    ):
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        self.header_levels = header_levels or [1, 2, 3]  # H1, H2, H3
    
    def chunk(self, content: str, **kwargs) -> List[ChunkResult]:
        """Chunk content by headers."""
        chunks = []
        lines = content.split('\n')
        
        current_header_path = []
        current_content = []
        current_start = 0
        index = 0
        
        for i, line in enumerate(lines):
            header_match = re.match(self.HEADER_PATTERN, line)
            
            if header_match:
                # Save previous section if it has content
                if current_content:
                    chunk_text = '\n'.join(current_content).strip()
                    if len(chunk_text) >= self.min_chunk_size:
                        chunks.append(self._create_chunk(
                            chunk_text, index, current_header_path, 
                            current_start, i
                        ))
                        index += 1
                    elif chunks:
                        # Append to previous chunk if too small
                        chunks[-1].content += '\n\n' + chunk_text
                
                # Update header path
                level = len(header_match.group(1))
                title = header_match.group(2).strip()
                
                if level <= len(current_header_path):
                    current_header_path = current_header_path[:level - 1]
                current_header_path.append(title)
                
                current_content = [line]
                current_start = i
            else:
                current_content.append(line)
        
        # Handle remaining content
        if current_content:
            chunk_text = '\n'.join(current_content).strip()
            if chunk_text:
                if len(chunk_text) >= self.min_chunk_size or not chunks:
                    chunks.append(self._create_chunk(
                        chunk_text, index, current_header_path,
                        current_start, len(lines)
                    ))
                else:
                    chunks[-1].content += '\n\n' + chunk_text
        
        # Split chunks that are too large
        final_chunks = []
        for chunk in chunks:
            if len(chunk.content) > self.max_chunk_size:
                final_chunks.extend(self._split_by_size(chunk))
            else:
                final_chunks.append(chunk)
        
        # Re-index
        for i, chunk in enumerate(final_chunks):
            chunk.index = i
        
        return final_chunks
    
    def _create_chunk(
        self,
        content: str,
        index: int,
        header_path: List[str],
        start_line: int,
        end_line: int,
    ) -> ChunkResult:
        """Create a chunk result."""
        return ChunkResult(
            content=content,
            index=index,
            locator=ChunkLocator(
                header_path=' > '.join(header_path) if header_path else None,
                line_start=start_line,
                line_end=end_line,
            ),
            metadata={"strategy": "header_based"},
        )
    
    def _split_by_size(self, chunk: ChunkResult) -> List[ChunkResult]:
        """Split a large chunk into smaller pieces."""
        chunks = []
        lines = chunk.content.split('\n')
        current_lines = []
        current_size = 0
        index = 0
        
        for line in lines:
            if current_size + len(line) > self.max_chunk_size and current_lines:
                chunks.append(ChunkResult(
                    content='\n'.join(current_lines),
                    index=index,
                    locator=ChunkLocator(
                        header_path=chunk.locator.header_path,
                        line_start=chunk.locator.line_start + index,
                    ),
                    metadata={"strategy": "header_based", "split": True},
                ))
                index += 1
                current_lines = []
                current_size = 0
            
            current_lines.append(line)
            current_size += len(line) + 1
        
        if current_lines:
            chunks.append(ChunkResult(
                content='\n'.join(current_lines),
                index=index,
                locator=ChunkLocator(
                    header_path=chunk.locator.header_path,
                    line_start=chunk.locator.line_start + index,
                ),
                metadata={"strategy": "header_based", "split": True},
            ))
        
        return chunks


class SemanticChunker(ChunkingStrategyInterface):
    """
    Chunks content based on semantic boundaries (paragraphs, sections).
    
    Good for: Natural text flow, preserving context
    """
    
    def __init__(
        self,
        min_chunk_size: int = 300,
        max_chunk_size: int = 2000,
        overlap_sentences: int = 2,
    ):
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        self.overlap_sentences = overlap_sentences
    
    def chunk(self, content: str, **kwargs) -> List[ChunkResult]:
        """Chunk content by semantic boundaries."""
        # Split into paragraphs
        paragraphs = re.split(r'\n\s*\n', content)
        chunks = []
        current_paragraphs = []
        current_size = 0
        index = 0
        start_char = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            para_size = len(para)
            
            if current_size + para_size > self.max_chunk_size and current_paragraphs:
                # Save current chunk
                chunk_content = '\n\n'.join(current_paragraphs)
                chunks.append(ChunkResult(
                    content=chunk_content,
                    index=index,
                    locator=ChunkLocator(
                        start_char=start_char,
                        end_char=start_char + len(chunk_content),
                    ),
                    metadata={"strategy": "semantic"},
                ))
                index += 1
                start_char += len(chunk_content)
                
                # Keep some overlap
                if self.overlap_sentences > 0:
                    last_para = current_paragraphs[-1]
                    sentences = re.split(r'[.!?]+\s+', last_para)
                    overlap = '. '.join(sentences[-self.overlap_sentences:])
                    current_paragraphs = [overlap, para]
                    current_size = len(overlap) + para_size
                else:
                    current_paragraphs = [para]
                    current_size = para_size
            else:
                current_paragraphs.append(para)
                current_size += para_size + 2  # +2 for paragraph break
        
        # Handle remaining content
        if current_paragraphs:
            chunk_content = '\n\n'.join(current_paragraphs)
            chunks.append(ChunkResult(
                content=chunk_content,
                index=index,
                locator=ChunkLocator(
                    start_char=start_char,
                    end_char=start_char + len(chunk_content),
                ),
                metadata={"strategy": "semantic"},
            ))
        
        return chunks


class HybridChunker(ChunkingStrategyInterface):
    """
    Combines multiple chunking strategies for optimal results.
    
    Priority: Headers > Pages > Semantic > Fixed Size
    """
    
    def __init__(
        self,
        max_chunk_size: int = 2000,
        min_chunk_size: int = 100,
    ):
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
        
        self.header_chunker = HeaderBasedChunker(
            min_chunk_size=min_chunk_size,
            max_chunk_size=max_chunk_size,
        )
        self.page_chunker = PageBasedChunker(max_chunk_size=max_chunk_size)
        self.semantic_chunker = SemanticChunker(
            min_chunk_size=min_chunk_size,
            max_chunk_size=max_chunk_size,
        )
        self.fixed_chunker = FixedSizeChunker(
            chunk_size=max_chunk_size,
            overlap=200,
        )
    
    def chunk(self, content: str, **kwargs) -> List[ChunkResult]:
        """Chunk using the best strategy for the content."""
        # Detect content type and choose strategy
        has_headers = bool(re.search(r'^#{1,6}\s+', content, re.MULTILINE))
        has_pages = bool(re.search(r'\[PAGE\s*\d+\]|---\s*Page\s*\d+|Page\s*\d+', content, re.IGNORECASE))
        
        if has_headers:
            logger.info("Using header-based chunking")
            return self.header_chunker.chunk(content, **kwargs)
        elif has_pages:
            logger.info("Using page-based chunking")
            return self.page_chunker.chunk(content, **kwargs)
        else:
            logger.info("Using semantic chunking")
            chunks = self.semantic_chunker.chunk(content, **kwargs)
            
            # Fall back to fixed size if semantic didn't work well
            if len(chunks) == 1 and len(chunks[0].content) > self.max_chunk_size * 2:
                logger.info("Falling back to fixed-size chunking")
                return self.fixed_chunker.chunk(content, **kwargs)
            
            return chunks


class HeaderSemanticChunker(ChunkingStrategyInterface):
    """
    Two-pass chunking strategy:
    1. Split content by markdown headers
    2. Prepend ancestor header path to each section for context
    3. Apply semantic chunking to each header section
    
    This preserves document hierarchy context while enabling fine-grained
    semantic chunking within each section.
    
    Example output:
        "[Installation > Requirements > Python Version] To run this project..."
    
    Good for: Technical documentation, knowledge bases, hierarchical content
    """
    
    HEADER_PATTERN = r'^(#{1,6})\s+(.+)$'
    
    def __init__(
        self,
        max_chunk_size: int = 2000,
        min_chunk_size: int = 100,
        include_header_context: bool = True,
        header_context_format: str = "[{header_path}]",
        overlap_sentences: int = 2,
    ):
        """
        Initialize the HeaderSemanticChunker.
        
        Args:
            max_chunk_size: Maximum size of each chunk
            min_chunk_size: Minimum size for a chunk (smaller sections merged)
            include_header_context: Whether to prepend header path to chunks
            header_context_format: Format string for header context. Use {header_path}
            overlap_sentences: Number of sentences to overlap between semantic chunks
        """
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
        self.include_header_context = include_header_context
        self.header_context_format = header_context_format
        self.overlap_sentences = overlap_sentences
    
    def chunk(self, content: str, **kwargs) -> List[ChunkResult]:
        """
        Chunk content using header-first then semantic approach.
        
        Args:
            content: The document content to chunk
            
        Returns:
            List of ChunkResult objects with header context prepended
        """
        # Pass 1: Split by headers and build sections with ancestor paths
        sections = self._split_by_headers(content)
        
        # Pass 2: Apply semantic chunking to each section
        final_chunks = []
        global_index = 0
        
        for section in sections:
            section_content = section['content']
            header_path = section['header_path']
            start_line = section['start_line']
            
            # Prepend header context if enabled
            if self.include_header_context and header_path:
                header_context = self.header_context_format.format(header_path=header_path)
                section_content = f"{header_context}\n\n{section_content}"
            
            # Apply semantic chunking to this section
            semantic_chunks = self._semantic_chunk_section(
                section_content,
                header_path,
                start_line,
                global_index,
            )
            
            final_chunks.extend(semantic_chunks)
            global_index = len(final_chunks)
        
        # Re-index all chunks
        for i, chunk in enumerate(final_chunks):
            chunk.index = i
        
        logger.info(f"HeaderSemanticChunker: Created {len(final_chunks)} chunks from {len(sections)} sections")
        return final_chunks
    
    def _split_by_headers(self, content: str) -> List[Dict[str, Any]]:
        """
        Split content by headers, tracking ancestor paths.
        
        Returns list of sections with:
            - content: The section text (including header line)
            - header_path: The ancestor path string (e.g., "Chapter 1 > Section 1.1")
            - header_level: The header level (1-6)
            - start_line: Starting line number
        """
        lines = content.split('\n')
        sections = []
        
        # Track current header path at each level
        header_stack: List[str] = []
        
        current_content = []
        current_start_line = 0
        current_header_path = ""
        current_header_level = 0
        
        for i, line in enumerate(lines):
            header_match = re.match(self.HEADER_PATTERN, line)
            
            if header_match:
                # Save previous section if it has content
                if current_content:
                    section_text = '\n'.join(current_content).strip()
                    if section_text:
                        sections.append({
                            'content': section_text,
                            'header_path': current_header_path,
                            'header_level': current_header_level,
                            'start_line': current_start_line,
                        })
                
                # Update header stack
                level = len(header_match.group(1))
                title = header_match.group(2).strip()
                
                # Pop headers at same or deeper level
                while len(header_stack) >= level:
                    header_stack.pop()
                
                # Push current header
                header_stack.append(title)
                
                # Build ancestor path
                current_header_path = ' > '.join(header_stack)
                current_header_level = level
                current_content = [line]
                current_start_line = i
            else:
                current_content.append(line)
        
        # Handle remaining content
        if current_content:
            section_text = '\n'.join(current_content).strip()
            if section_text:
                sections.append({
                    'content': section_text,
                    'header_path': current_header_path,
                    'header_level': current_header_level,
                    'start_line': current_start_line,
                })
        
        return sections
    
    def _semantic_chunk_section(
        self,
        content: str,
        header_path: str,
        start_line: int,
        start_index: int,
    ) -> List[ChunkResult]:
        """
        Apply semantic chunking to a single header section.
        
        Splits by paragraphs while respecting min/max chunk sizes.
        """
        # Split into paragraphs
        paragraphs = re.split(r'\n\s*\n', content)
        chunks = []
        
        current_paragraphs = []
        current_size = 0
        index = start_index
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            para_size = len(para)
            
            # If adding this paragraph exceeds max size, save current chunk
            if current_size + para_size + 2 > self.max_chunk_size and current_paragraphs:
                chunk_content = '\n\n'.join(current_paragraphs)
                
                if len(chunk_content) >= self.min_chunk_size:
                    chunks.append(self._create_chunk(
                        chunk_content,
                        index,
                        header_path,
                        start_line,
                    ))
                    index += 1
                
                # Handle overlap for context continuity
                if self.overlap_sentences > 0 and current_paragraphs:
                    last_para = current_paragraphs[-1]
                    sentences = re.split(r'(?<=[.!?])\s+', last_para)
                    if len(sentences) > self.overlap_sentences:
                        overlap = ' '.join(sentences[-self.overlap_sentences:])
                        current_paragraphs = [overlap, para]
                        current_size = len(overlap) + para_size + 2
                    else:
                        current_paragraphs = [para]
                        current_size = para_size
                else:
                    current_paragraphs = [para]
                    current_size = para_size
            else:
                current_paragraphs.append(para)
                current_size += para_size + 2
        
        # Handle remaining content
        if current_paragraphs:
            chunk_content = '\n\n'.join(current_paragraphs)
            if chunk_content.strip():
                chunks.append(self._create_chunk(
                    chunk_content,
                    index,
                    header_path,
                    start_line,
                ))
        
        return chunks
    
    def _create_chunk(
        self,
        content: str,
        index: int,
        header_path: str,
        base_line: int,
    ) -> ChunkResult:
        """Create a ChunkResult with proper metadata."""
        return ChunkResult(
            content=content,
            index=index,
            locator=ChunkLocator(
                header_path=header_path if header_path else None,
                line_start=base_line,
            ),
            metadata={
                "strategy": "header_semantic",
                "header_context_included": self.include_header_context,
            },
        )


class ChunkingService:
    """
    Main service for document chunking.
    
    Provides a unified interface for different chunking strategies.
    """
    
    _strategies: Dict[ChunkingStrategy, ChunkingStrategyInterface] = {}
    
    def __init__(
        self,
        default_strategy: ChunkingStrategy = ChunkingStrategy.HYBRID,
        **default_kwargs,
    ):
        self.default_strategy = default_strategy
        self.default_kwargs = default_kwargs
        
        # Initialize strategies
        self._strategies = {
            ChunkingStrategy.FIXED_SIZE: FixedSizeChunker(),
            ChunkingStrategy.SEMANTIC: SemanticChunker(),
            ChunkingStrategy.PAGE_BASED: PageBasedChunker(),
            ChunkingStrategy.HEADER_BASED: HeaderBasedChunker(),
            ChunkingStrategy.HYBRID: HybridChunker(),
            ChunkingStrategy.HEADER_SEMANTIC: HeaderSemanticChunker(),
        }
    
    def chunk(
        self,
        content: str,
        strategy: Optional[ChunkingStrategy] = None,
        **kwargs,
    ) -> List[ChunkResult]:
        """
        Chunk content using the specified strategy.
        
        Args:
            content: The document content to chunk
            strategy: Chunking strategy to use (defaults to hybrid)
            **kwargs: Additional parameters for the chunker
            
        Returns:
            List of ChunkResult objects with content and locators
        """
        strategy = strategy or self.default_strategy
        chunker = self._strategies.get(strategy)
        
        if not chunker:
            raise ValueError(f"Unknown chunking strategy: {strategy}")
        
        # Merge default kwargs with provided kwargs
        merged_kwargs = {**self.default_kwargs, **kwargs}
        
        return chunker.chunk(content, **merged_kwargs)
    
    def register_strategy(
        self,
        strategy: ChunkingStrategy,
        chunker: ChunkingStrategyInterface,
    ) -> None:
        """Register a custom chunking strategy."""
        self._strategies[strategy] = chunker