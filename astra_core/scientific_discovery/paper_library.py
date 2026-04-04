#!/usr/bin/env python3
"""
Astronomical Paper Library - RAG System for Research Papers
==========================================================

A specialized knowledge base for astronomical research papers that:
1. Stores and indexes PDF papers
2. Builds incrementally over time
3. Enables semantic search and retrieval
4. Integrates with LLM for question-answering

Advantages over web search or LLM training data:
- Up-to-date with latest research (no training cutoff)
- Access to paywalled papers (if you have access)
- Specialized to your research interests
- Persistent knowledge that grows with you
- Precise citation tracking

Author: STAN_IX_ASTRO
Date: January 10, 2026
"""

import os
import json
import hashlib
import logging
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import re

# PDF processing
try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False

try:
    import PyPDF2
    HAS_PYPDF2 = True
except ImportError:
    HAS_PYPDF2 = False

# Vector embeddings
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

# Text chunking
try:
    import tiktoken
    HAS_TIKTOKEN = True
except ImportError:
    HAS_TIKTOKEN = False

logger = logging.getLogger(__name__)


# =============================================================================
# Data Structures
# =============================================================================

@dataclass
class PaperChunk:
    """A chunk of text from a paper for vector storage."""
    chunk_id: str
    paper_id: str
    text: str
    chunk_index: int
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Embedding (computed later)
    embedding: Optional[np.ndarray] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        d = {
            'chunk_id': self.chunk_id,
            'paper_id': self.paper_id,
            'text': self.text,
            'chunk_index': self.chunk_index,
            'metadata': self.metadata,
        }
        # Don't store embedding in JSON (too large)
        return d


@dataclass
class Paper:
    """Complete paper record."""
    paper_id: str
    title: str
    authors: List[str] = field(default_factory=list)
    year: int = 0
    journal: str = ""
    volume: str = ""
    pages: str = ""
    doi: str = ""
    arxiv_id: str = ""
    arxiv_url: str = ""
    pdf_url: str = ""

    # Content
    abstract: str = ""
    full_text: str = ""
    chunks: List[PaperChunk] = field(default_factory=list)

    # Extracted information
    citations: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    topics: List[str] = field(default_factory=list)

    # File metadata
    file_path: Optional[Path] = None
    file_size_bytes: int = 0
    added_date: str = field(default_factory=lambda: datetime.now().isoformat())
    last_accessed: str = field(default_factory=lambda: datetime.now().isoformat())

    # Processing status
    processed: bool = False
    embedding_computed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            'paper_id': self.paper_id,
            'title': self.title,
            'authors': self.authors,
            'year': self.year,
            'journal': self.journal,
            'volume': self.volume,
            'pages': self.pages,
            'doi': self.doi,
            'arxiv_id': self.arxiv_id,
            'arxiv_url': self.arxiv_url,
            'pdf_url': self.pdf_url,
            'abstract': self.abstract,
            'num_chunks': len(self.chunks),
            'citations': self.citations,
            'keywords': self.keywords,
            'topics': self.topics,
            'file_path': str(self.file_path) if self.file_path else None,
            'file_size_bytes': self.file_size_bytes,
            'added_date': self.added_date,
            'last_accessed': self.last_accessed,
            'processed': self.processed,
            'embedding_computed': self.embedding_computed,
        }


# =============================================================================
# Paper Library Manager
# =============================================================================

class PaperLibrary:
    """
    Manager for astronomical paper library.

    Features:
    - Add papers incrementally
    - Automatic PDF processing
    - Text chunking for semantic search
    - Vector embeddings for similarity
    - Persistent storage
    - Query and retrieval
    """

    def __init__(self,
                 library_path: str = None,
                 chunk_size: int = 1000,
                 chunk_overlap: int = 200):
        """
        Initialize paper library.

        Args:
            library_path: Path to library directory
            chunk_size: Target chunk size in tokens
            chunk_overlap: Overlap between chunks
        """
        if library_path is None:
            library_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                'data', 'paper_library'
            )

        self.library_path = Path(library_path)
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # Create directories
        self.papers_dir = self.library_path / 'papers'
        self.index_dir = self.library_path / 'index'
        self.chunks_dir = self.library_path / 'chunks'
        self.embeddings_dir = self.library_path / 'embeddings'

        for dir_path in [self.papers_dir, self.index_dir,
                        self.chunks_dir, self.embeddings_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        # In-memory storage
        self.papers: Dict[str, Paper] = {}
        self.chunks: Dict[str, PaperChunk] = {}

        # Index files
        self.catalog_path = self.index_dir / 'catalog.json'
        self.embeddings_index_path = self.index_dir / 'embeddings.npy'

        # Load existing catalog
        self._load_catalog()

        logger.info(f"PaperLibrary initialized at {self.library_path}")
        logger.info(f"  Total papers: {len(self.papers)}")
        logger.info(f"  Total chunks: {len(self.chunks)}")
