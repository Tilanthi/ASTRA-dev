"""
Research Papers - PDF Processing and Literature Mining
======================================================

Comprehensive literature analysis for autonomous scientific discovery.
Processes PDFs, builds citation networks, extracts key findings, and
identifies hypotheses from scientific papers.

Key Components:
- PDFProcessor: Extract text and metadata from PDFs
- CitationNetwork: Build and analyze citation graphs
- LiteratureMiner: Extract key findings and hypotheses
- PaperAnalyzer: Paper classification and topic modeling

Dependencies:
- pdfplumber (preferred) or PyPDF2 for PDF processing
- networkx for citation network analysis
- spacy for NLP (optional - enhanced features)
- beautifulsoup4 for HTML/XML parsing

Version: 1.0.0
Date: 2025-12-27
"""

import re
import json
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple, Set
from pathlib import Path
from collections import defaultdict, Counter
import hashlib

# Standard library
from datetime import datetime

# Try importing PDF libraries
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

# Try importing NLP
try:
    import spacy
    HAS_SPACY = True
except ImportError:
    HAS_SPACY = False

# Try importing network analysis
try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False
    nx = None

logger = logging.getLogger(__name__)


# =============================================================================
# Data Structures
# =============================================================================

@dataclass
class Paper:
    """Scientific paper metadata and content"""
    paper_id: str
    title: str
    authors: List[str] = field(default_factory=list)
    journal: str = ""
    year: int = 0
    doi: str = ""
    arxiv_id: str = ""

    # Content
    abstract: str = ""
    full_text: str = ""
    sections: Dict[str, str] = field(default_factory=dict)

    # Extracted information
    citations: List[str] = field(default_factory=list)  # DOIs or titles of cited papers
    key_findings: List[str] = field(default_factory=list)
    hypotheses: List[str] = field(default_factory=list)
    methods: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)

    # Metadata
    file_path: Optional[Path] = None
    processed_at: float = field(default_factory=lambda: datetime.now().timestamp())

    def __post_init__(self):
        if not self.paper_id:
            # Generate ID from title hash
            self.paper_id = hashlib.md5(self.title.encode()).hexdigest()[:8]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'paper_id': self.paper_id,
            'title': self.title,
            'authors': self.authors,
            'journal': self.journal,
            'year': self.year,
            'doi': self.doi,
            'arxiv_id': self.arxiv_id,
            'abstract': self.abstract,
            'num_citations': len(self.citations),
            'num_findings': len(self.key_findings),
            'num_hypotheses': len(self.hypotheses),
            'keywords': self.keywords,
        }


@dataclass
class CitationGraph:
    """Citation network graph"""
    graph: Any = None  # networkx Graph
    papers: Dict[str, Paper] = field(default_factory=dict)

    # Network statistics
    num_nodes: int = 0
    num_edges: int = 0
    avg_citations: float = 0.0
    influential_papers: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert statistics to dictionary"""
        return {
            'num_papers': self.num_nodes,
            'num_citations': self.num_edges,
            'avg_citations': self.avg_citations,
            'influential_papers': self.influential_papers[:10],
        }


# =============================================================================
# PDF Processor
# =============================================================================

class PDFProcessor:
    """
    Extract text and metadata from PDF files.

    Supports multiple PDF libraries with automatic fallback.
    """

    def __init__(self):
        self.has_pdf_support = HAS_PDFPLUMBER or HAS_PYPDF2

        if not self.has_pdf_support:
            logger.warning("No PDF library available. Install pdfplumber or PyPDF2.")

        logger.info(f"PDFProcessor initialized (pdfplumber={HAS_PDFPLUMBER}, PyPDF2={HAS_PYPDF2})")

    def extract_text(self, pdf_path: Path) -> str:
        """
        Extract full text from PDF.

        Args:
            pdf_path: Path to PDF file

        Returns:
