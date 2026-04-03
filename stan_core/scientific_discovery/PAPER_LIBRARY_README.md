# Astronomical Paper Library for STAN_IX_ASTRO

A specialized knowledge base system for astronomical research papers with Retrieval-Augmented Generation (RAG) capabilities.

## Overview

This system allows you to:
- Build a personal library of PDF papers (including paywalled content you have access to)
- Search semantically across your papers
- Get precise, citation-backed answers from your literature
- Integrate with Claude/GPT for intelligent question-answering
- Incrementally build your library over time

## Why Use This Instead of Web Search or LLM Training Data?

| Approach | Advantages | Disadvantages | Best For |
|----------|------------|---------------|----------|
| **Paper Library (RAG)** | • Access to paywalled papers<br>• Always up-to-date<br>• Precise citations<br>• Specialized to your research<br>• Works offline | • Requires setup<br>• Storage needed<br>• Limited to your papers | • Deep research<br>• Writing papers<br>• Building institutional knowledge |
| **LLM Training Data** | • Zero setup<br>• Broad knowledge<br>• Fast | • Training cutoff<br>• No paywall access<br>• Can't cite precisely<br>• May hallucinate | • General questions<br>• Quick overview<br>• Brainstorming |
| **Web Search** | • Latest papers<br>• Broad coverage<br>• No storage | • No paywall access<br>• Rate limits<br>• Inconsistent | • New topics<br>• Finding recent papers<br>• Initial literature review |

**Recommendation**: Use all three in combination for maximum effectiveness.

## Installation

```bash
cd /Users/gjw255/astrodata/SWARM/STAN_IX_ASTRO/stan_core/scientific_discovery

# Install dependencies
pip install pdfplumber PyPDF2 numpy tiktoken

# Optional: For better embeddings
pip install sentence-transformers
```

## Quick Start

### 1. Initialize Your Library

```bash
python setup_paper_library.py --init
```

This creates the library structure at:
```
STAN_IX_ASTRO/data/paper_library/
├── papers/          # PDF files
├── index/           # Catalog and search index
├── chunks/          # Text chunks for search
└── embeddings/      # Vector embeddings
```

### 2. Add Papers

```bash
# Add all PDFs from a directory
python setup_paper_library.py --add-dir ~/papers/astronomy

# Add a single PDF
python setup_paper_library.py --add-pdf ~/Downloads/paper.pdf
```

### 3. Search Your Library

```bash
python setup_paper_library.py --query "star formation"
```

### 4. View Statistics

```bash
python setup_paper_library.py --stats
```

## Python API

### Basic Usage

```python
from stan_core.scientific_discovery.paper_library import PaperLibrary
from stan_core.scientific_discovery.paper_rag_query import PaperRAGSystem

# Create library
library = PaperLibrary()

# Add papers
paper = library.add_pdf('/path/to/paper.pdf')

# Search
results = library.search('Herschel W3')
for result in results:
    print(f"{result['score']:.2f}: {result['paper'].title}")
```

### RAG Queries with LLM

```python
# Create RAG system
rag = PaperRAGSystem()

# Query (returns prompt for LLM)
result = rag.query(
    "What is the current understanding of IMF variation?",
    top_k=10
)

# Result includes:
# - result.answer: Formatted prompt for LLM
# - result.context: Retrieved passages
# - result.sources: Citation information

# Use with Claude
import anthropic

client = anthropic.Anthropic(api_key="your-key")
message = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=2000,
    messages=[{"role": "user", "content": result.answer}]
)

print(message.content[0].text)
```

### Batch Processing

```python
# Add papers incrementally
rag = PaperRAGSystem()

# Process in batches of 10
added = rag.batch_add_papers(
    '/path/to/papers',
    num_at_time=10
)

print(f"Added {added} papers")
```

## Architecture

```
Query Flow:
───────────

User Query → [RAG System]
                     ↓
        ┌──────────────┴──────────────┐
        │                              │
    [Keyword Search]          [Vector Search]
        │                              │
        └──────────────┬──────────────┘
                       ↓
              [Merge & Rank]
                       ↓
              [Format Context]
                       ↓
              [Send to LLM]
                       ↓
              [Answer + Citations]
```

## Incremental Building Strategy

### Recommended Approach

1. **Start with Core Papers** (50-100 papers)
   - Your research area's foundational papers
   - Key methodological papers
   - Papers you cite frequently

2. **Expand Gradually** (5-10 papers/month)
   - Recent papers in your field
   - Papers from key collaborators
   - Papers recommended by colleagues

3. **Curate Systematically**
   - Review quarterly
   - Remove duplicates
   - Update with new versions

### Example: W3 Star Formation

```python
# W3-specific library
library = PaperLibrary(library_path='./w3_papers')

# Core Herschel papers
library.add_pdf('herschel_w3_1.pdf')
library.add_pdf('herschel_w3_2.pdf')
library.add_pdf('rivera_ingraham_2021.pdf')

# Methodological papers
library.add_pdf('getsources_paper.pdf')
library.add_pdf('clump_finding_methods.pdf')

# Your own papers
library.add_pdf('my_w3_analysis.pdf')
```

## Advanced Features

### Citation Network Analysis

```python
from stan_core.scientific_discovery.research_papers import CitationGraph

# Build citation network from your papers
citation_graph = CitationGraph()

for paper in library.papers.values():
    citation_graph.add_paper(paper)

# Find influential papers
influential = citation_graph.get_most_influential()
```

### Integration with STAN_IX_ASTRO Discovery

```python
from stan_core.scientific_discovery import autonomous_discovery

# Use your paper library in autonomous discovery
result = autonomous_discovery(
    research_question="What determines the IMF in high-mass star formation?",
    paper_library=library,  # Your curated papers
    enable_literature=True,
    enable_data=True
)
```

## File Structure

```
stan_core/scientific_discovery/
├── paper_library.py              # Core library system
├── paper_rag_query.py           # RAG query system
├── paper_library_comparison.py  # Comparison document
├── setup_paper_library.py       # CLI setup tool
├── research_papers.py           # PDF processing & citation networks
└── PAPER_LIBRARY_README.md      # This file
```

## Configuration

Create a config file at `~/.stan_ix_astro/paper_library_config.json`:

```json
{
  "library_path": "/path/to/paper_library",
  "chunk_size": 1000,
  "chunk_overlap": 200,
  "embedding_model": "local",
  "paper_directories": [
    "~/papers/astronomy",
    "~/Downloads/papers"
  ]
}
```

## Performance Tips

1. **Storage**: ~5 MB per paper (PDF + embeddings)
2. **Search Speed**: < 1 second for 1000 papers
3. **Memory**: ~500 MB for 1000-paper library

## Troubleshooting

### PDF Extraction Fails

Some PDFs (especially scanned ones) may fail text extraction. Solutions:
- Try converting PDF to text first
- Use OCR tools (tesseract)
- Download the arXiv source version

### Memory Issues with Large Libraries

For libraries > 1000 papers:
- Use FAISS or Milvus for vector storage
- Implement chunked loading
- Use database instead of JSON catalog

## Integration with Existing Workflows

### With Zotero/Mendeley

```python
# Export from Zotero as PDFs
# Then batch add:
library.add_from_directory('~/Zotero/storage')
```

### With ADS/arXiv

```python
# Download from arXiv
import arxiv

paper = next(arxiv.Client().results(arxiv.Search(query='astro-ph.GA')))
# Download and add to library
```

## Future Enhancements

- [ ] Integration with ADS API
- [ ] Automatic arXiv downloads
- [ ] PDF OCR for scanned papers
- [ ] Collaborative filtering (recommend similar papers)
- [ ] Figure/table extraction
- [ ] Automated summarization

## Questions?

For issues or questions, check:
1. The comparison document: `paper_library_comparison.py`
2. STAN_IX_ASTRO documentation: `/Users/gjw255/astrodata/SWARM/STAN_IX_ASTRO/CLAUDE.md`

## License

Part of STAN_IX_ASTRO - Autonomous Scientific Discovery System

---

**Version**: 1.0.0
**Date**: January 10, 2026
**Author**: STAN_IX_ASTRO System
