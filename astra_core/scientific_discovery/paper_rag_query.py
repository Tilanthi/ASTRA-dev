#!/usr/bin/env python3

# Copyright 2024-2026 Glenn J. White (The Open University / RAL Space)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Astronomical Paper Library - RAG Query System
==============================================

Retrieval-Augmented Generation system for querying your paper library.
Integrates with Claude/other LLMs for intelligent question-answering.

Author: STAN_IX_ASTRO
Date: January 10, 2026
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from pathlib import Path

# Import paper library (relative import)
try:
    from .paper_library import PaperLibrary, Paper, PaperChunk
except ImportError:
    from paper_library import PaperLibrary, Paper, PaperChunk

logger = logging.getLogger(__name__)


# =============================================================================
# Data Structures
# =============================================================================

@dataclass
class RetrievedContext:
    """Context retrieved from paper library."""
    chunks: List[PaperChunk]
    papers: Dict[str, Paper]
    query: str
    retrieval_method: str

    def format_for_llm(self, max_chars: int = 8000) -> str:
        """
        Format retrieved context for LLM consumption.

        Creates a structured prompt with paper citations.
        """
        context_parts = []

        context_parts.append("RELEVANT PASSAGES FROM PAPER LIBRARY:\n")
        context_parts.append("=" * 80 + "\n\n")

        # Group chunks by paper
        paper_chunks = {}
        for chunk in self.chunks:
            if chunk.paper_id not in paper_chunks:
                paper_chunks[chunk.paper_id] = []
            paper_chunks[chunk.paper_id].append(chunk)

        # Add each paper's chunks
        current_chars = 100  # Reserve for header/footer
        for paper_id, chunks in paper_chunks.items():
            if current_chars >= max_chars:
                break

            paper = self.papers.get(paper_id)
            if not paper:
                continue

            # Paper header with citation
            citation = f"{paper.authors[0] if paper.authors else 'Unknown'} et al. ({paper.year})"
            if paper.journal:
                citation += f", {paper.journal}"
            if paper.doi:
                citation += f", DOI: {paper.doi}"

            context_parts.append(f"PAPER: {paper.title}\n")
            context_parts.append(f"CITATION: {citation}\n")
            context_parts.append("-" * 80 + "\n")

            current_chars += len(citation) + 50

            # Add chunks from this paper
            for chunk in chunks:
                chunk_text = chunk.text.strip()
                if len(chunk_text) > 500:
                    chunk_text = chunk_text[:500] + "..."

                context_parts.append(f"[{chunk.metadata.get('section', 'Text')}]\n")
                context_parts.append(f"{chunk_text}\n\n")

                current_chars += len(chunk_text) + 50
                if current_chars >= max_chars:
                    break

            context_parts.append("\n")

        return "".join(context_parts[:max_chars])


@dataclass
class QueryResult:
    """Result from RAG query."""
    answer: str
    context: RetrievedContext
    sources: List[Dict[str, Any]]
    confidence: float
    query: str


# =============================================================================
# RAG Query System
# =============================================================================

class PaperRAGSystem:
    """
    Retrieval-Augmented Generation system for paper library.

    Combines:
    1. Vector similarity search
    2. Keyword search
    3. LLM-based answer generation
    4. Proper citation tracking
    """

    def __init__(self,
                 library_path: str = None,
                 embedding_model: str = "local"):
        """
        Initialize RAG system.

        Args:
            library_path: Path to paper library
            embedding_model: "local", "openai", or "cohere"
        """
        self.library = PaperLibrary(library_path=library_path)
        self.embedding_model = embedding_model

        logger.info(f"PaperRAGSystem initialized")
        logger.info(f"  Papers in library: {len(self.library.papers)}")
        logger.info(f"  Chunks in library: {len(self.library.chunks)}")

    def retrieve(self,
                query: str,
                top_k: int = 10,
                method: str = "hybrid") -> RetrievedContext:
        """
        Retrieve relevant context for query.

        Args:
            query: User's question
            top_k: Number of chunks to retrieve
            method: "keyword", "vector", or "hybrid"

        Returns:
            RetrievedContext with relevant chunks
        """
        logger.info(f"Retrieving context for query: {query[:50]}...")

        if method == "keyword":
            chunks = self._keyword_search(query, top_k)
        elif method == "vector":
            chunks = self._vector_search(query, top_k)
        else:  # hybrid
            chunks_keyword = self._keyword_search(query, top_k // 2)
            chunks_vector = self._vector_search(query, top_k // 2)

            # Combine and deduplicate
            chunks = self._merge_results(chunks_keyword, chunks_vector, top_k)

        # Get papers for these chunks
        paper_ids = set(c.paper_id for c in chunks)
        papers = {pid: self.library.get_paper(pid) for pid in paper_ids}

        context = RetrievedContext(
            chunks=chunks,
            papers={k: v for k, v in papers.items() if v is not None},
            query=query,
            retrieval_method=method
        )

        logger.info(f"Retrieved {len(chunks)} chunks from {len(papers)} papers")

        return context

    def _keyword_search(self, query: str, top_k: int) -> List[PaperChunk]:
        """Keyword-based search through chunks."""
        query_lower = query.lower()
        query_words = set(query_lower.split())

        scored_chunks = []

        for chunk_id, chunk in self.library.chunks.items():
            text = chunk.text.lower()

            score = 0.0

            # Exact phrase match
            if query_lower in text:
                score += 2.0

            # Word matches
            word_matches = sum(1 for w in query_words if w in text)
            if word_matches > 0:
                score += word_matches * 0.1

            # Title/abstract bonus
            paper = self.library.get_paper(chunk.paper_id)
            if paper:
                if query_lower in paper.title.lower():
                    score += 1.0
                if query_lower in paper.abstract.lower():
                    score += 0.5

            if score > 0:
                scored_chunks.append((chunk, score))

        # Sort by score
        scored_chunks.sort(key=lambda x: x[1], reverse=True)

        return [c[0] for c in scored_chunks[:top_k]]

    def _vector_search(self, query: str, top_k: int) -> List[PaperChunk]:
        """
        Vector similarity search.

        NOTE: This is a simplified version. For production use:
        - Use proper embedding model (OpenAI, sentence-transformers)
        - Use FAISS or Milvus for efficient search
        - Implement proper chunk embeddings
        """
        # For now, fallback to keyword search
        # In production, this would:
        # 1. Embed the query
        # 2. Search vector database
        # 3. Return top-k chunks
        return self._keyword_search(query, top_k)

    def _merge_results(self,
                      chunks1: List[PaperChunk],
                      chunks2: List[PaperChunk],
                      top_k: int) -> List[PaperChunk]:
        """Merge and deduplicate results from multiple search methods."""
        seen = set()
        merged = []

        for chunk in chunks1 + chunks2:
            if chunk.chunk_id not in seen:
                merged.append(chunk)
                seen.add(chunk.chunk_id)

        return merged[:top_k]

    def query(self,
             query: str,
             top_k: int = 10,
             llm_callback: Optional[callable] = None) -> QueryResult:
        """
        Query the paper library and generate answer.

        Args:
            query: User's question
            top_k: Number of context chunks to retrieve
            llm_callback: Optional function to call with prompt

        Returns:
            QueryResult with answer and sources
        """
        logger.info(f"Processing query: {query}")

        # Retrieve relevant context
        context = self.retrieve(query, top_k=top_k, method="hybrid")

        # Format context for LLM
        context_text = context.format_for_llm()

        # Build prompt
        prompt = self._build_prompt(query, context_text)

        # Get answer (either via callback or return prompt for manual LLM call)
        if llm_callback:
            answer = llm_callback(prompt)
        else:
            # Return prompt for manual LLM invocation
            answer = None

        # Extract sources
        sources = []
        for paper_id, paper in context.papers.items():
            sources.append({
                'paper_id': paper_id,
                'title': paper.title,
                'authors': paper.authors,
                'year': paper.year,
                'journal': paper.journal,
                'doi': paper.doi,
                'arxiv_id': paper.arxiv_id,
            })

        result = QueryResult(
            answer=answer if answer else prompt,
            context=context,
            sources=sources,
            confidence=len(context.chunks) / top_k,  # Simple confidence metric
            query=query
        )

        logger.info(f"Query complete: {len(sources)} sources, confidence={result.confidence:.2f}")

        return result

    def _build_prompt(self, query: str, context: str) -> str:
        """Build prompt for LLM."""
        prompt = f"""You are an expert astronomy research assistant with access to a specialized library of scientific papers.

USER QUESTION: {query}

{context}

INSTRUCTIONS:
1. Answer the question using ONLY the information provided in the relevant passages above.
2. If the passages don't contain enough information to answer the question completely, state this clearly.
3. Cite specific papers using the format: (Author et al., Year)
4. If multiple papers present different views, describe each view.
5. Do not make up information or use outside knowledge.
6. Be precise and specific in your answer.

ANSWER:"""

        return prompt

    def batch_add_papers(self,
                        directory: str,
                        num_at_time: int = 10) -> int:
        """
        Add papers in batches for incremental building.

        Args:
            directory: Directory containing PDFs
            num_at_time: Number of papers to process per batch

        Returns:
            Number of papers added
        """
        directory = Path(directory)
        pdf_files = list(directory.rglob('*.pdf'))

        logger.info(f"Found {len(pdf_files)} PDFs")
        logger.info(f"Processing in batches of {num_at_time}")

        added_count = 0
        for i, pdf_file in enumerate(pdf_files):
            # Check if already in library
            existing_papers = [p for p in self.library.papers.values()
                             if p.filepath == str(pdf_file)]

            if existing_papers:
                continue

            # Process PDF
            try:
                paper = self.process_pdf(pdf_file)
                if paper:
                    self.library.add_paper(paper)
                    added_count += 1

                    if added_count % num_at_time == 0:
                        logger.info(f"Added {added_count} papers so far...")
            except Exception as e:
                logger.error(f"Error processing {pdf_file}: {e}")

        return added_count
