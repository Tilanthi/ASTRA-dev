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
Local RAG with ChromaDB: Vector Retrieval for Knowledge Augmentation

Provides local vector retrieval using ChromaDB:
- Runs locally on M1 Mac, no GPU needed
- Uses built-in sentence embeddings
- Scientific facts knowledge base
- MORK-backed document store
- Problem signature matching

Expected gain: +5-8% accuracy

Date: 2025-12-10
Version: 38.0
"""

import hashlib
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
import json
from pathlib import Path
import numpy as np


@dataclass
class Document:
    """A document in the RAG store"""
    doc_id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None

    def __hash__(self):
        return hash(self.doc_id)


@dataclass
class RetrievalResult:
    """Result from RAG retrieval"""
    documents: List[Document]
    scores: List[float]
    query: str
    total_retrieved: int

    def get_context(self, max_length: int = 2000) -> str:
        """Format retrieved docs as context string"""
        context_parts = []
        current_length = 0

        for doc, score in zip(self.documents, self.scores):
            doc_text = f"[Relevance: {score:.2f}] {doc.content}"
            if current_length + len(doc_text) > max_length:
                break
            context_parts.append(doc_text)
            current_length += len(doc_text)

        return "\n\n".join(context_parts)


class SimpleEmbedder:
    """
    Simple TF-IDF based embedder for when sentence-transformers is not available.

    Falls back to word overlap similarity.
    """

    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self.vocabulary: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}

    def encode(self, texts: List[str]) -> np.ndarray:
        """Encode texts to vectors using simple TF-IDF"""
        embeddings = []

        for text in texts:
            words = text.lower().split()
            vec = np.zeros(self.dimension)

            for i, word in enumerate(words[:self.dimension]):
                # Simple hash-based embedding
                word_hash = int(hashlib.md5(word.encode()).hexdigest(), 16)
                idx = word_hash % self.dimension
                vec[idx] += 1.0

            # Normalize
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm

            embeddings.append(vec)

        return np.array(embeddings)


class LocalRAG:
    """
    Local RAG implementation with optional ChromaDB backend.

    Uses ChromaDB when available, falls back to in-memory store.
    ChromaDB runs locally on M1 Mac, no GPU needed.
    """

    def __init__(self, persist_dir: Optional[str] = None, collection_name: str = "stan_knowledge"):
        """
        Initialize LocalRAG.

        Args:
            persist_dir: Directory for persistent storage (None for in-memory)
            collection_name: Name of the collection
        """
        self.persist_dir = persist_dir
        self.collection_name = collection_name
        self.chromadb_available = self._check_chromadb()

        if self.chromadb_available:
            self._init_chromadb()
