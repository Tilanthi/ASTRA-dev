#!/usr/bin/env python3
"""
Setup Script for Astronomical Paper Library
===========================================

Quick setup to initialize your paper library and add first papers.

Usage:
    python setup_paper_library.py --help

Author: STAN_IX_ASTRO
Date: January 10, 2026
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scientific_discovery.paper_library import PaperLibrary
from scientific_discovery.paper_rag_query import PaperRAGSystem

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def create_example_config():
    """Create example configuration file."""
    config = {
        "library_path": "/path/to/your/paper_library",
        "chunk_size": 1000,
        "chunk_overlap": 200,
        "embedding_model": "local",
        "paper_directories": [
            "/path/to/your/papers",
            "~/Downloads/papers",
        ],
        "auto_import": {
            "enabled": True,
            "check_interval_hours": 24,
        },
    }

    config_path = Path.home() / '.stan_ix_astro' / 'paper_library_config.json'
    config_path.parent.mkdir(exist_ok=True)

    import json
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)

    logger.info(f"Created example config at: {config_path}")
    logger.info("Edit this file with your paths and preferences.")

    return config_path


def main():
    parser = argparse.ArgumentParser(
        description='Setup astronomical paper library'
    )

    parser.add_argument(
        '--init',
        action='store_true',
        help='Initialize new paper library'
    )

    parser.add_argument(
        '--add-dir',
        type=str,
        metavar='DIRECTORY',
        help='Add all PDFs from directory'
    )

    parser.add_argument(
        '--add-pdf',
        type=str,
        metavar='FILE',
        help='Add single PDF file'
    )

    parser.add_argument(
        '--library-path',
        type=str,
        default=None,
        help='Path to paper library (default: STAN_IX_ASTRO/data/paper_library)'
    )

    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show library statistics'
    )

    parser.add_argument(
        '--query',
        type=str,
        metavar='QUERY',
        help='Search the library'
    )

    parser.add_argument(
        '--list',
        action='store_true',
        help='List all papers in library'
    )

    parser.add_argument(
        '--create-config',
        action='store_true',
        help='Create example configuration file'
    )

    args = parser.parse_args()

    # Create library
    library = PaperLibrary(library_path=args.library_path)

    # Handle commands
    if args.create_config:
        create_example_config()
        return

    if args.add_dir:
