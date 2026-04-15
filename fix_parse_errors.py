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
Script to fix all parse errors in astra_core modules.
"""
import ast
import os
from pathlib import Path

# List of files with parse errors
PARSE_ERROR_FILES = [
    "astra_core/scientific_discovery/research_papers.py",
    "astra_core/scientific_discovery/paper_rag_query.py",
    "astra_core/scientific_discovery/setup_paper_library.py",
    "astra_core/scientific_discovery/adaptive_reasoning.py",
    "astra_core/intelligence/redundant_executor.py",
    "astra_core/arc_agi/pattern_library.py",
    "astra_core/reasoning/symbolic_verification.py",
    "astra_core/reasoning/integrated_reasoning.py",
    "astra_core/reasoning/v70_predictive_geometry.py",
    "astra_core/reasoning/formal_logic_enhanced.py",
    "astra_core/reasoning/abstraction_stack.py",
    "astra_core/retrieval/sharded_retrieval.py",
    "astra_core/retrieval/query_expander.py",
    "astra_core/retrieval/context_distiller.py",
    "astra_core/gsd/xml_task_formatting.py",
    "astra_core/arc_reasoning/neuro_symbolic_solver.py",
    "astra_core/symbolic/v37_system.py",
    "astra_core/symbolic/tool_integration.py",
    "astra_core/mathematical/aletheia_stan_architecture.py",
    "astra_core/astro_physics/radiative_transfer.py",
    "astra_core/self_teaching/architecture_rewriter.py",
    "astra_core/self_teaching/consciousness_simulator.py",
    "astra_core/self_teaching/astronomy_causal_discovery.py",
    "astra_core/astro_physics/next_gen/alert_processing.py",
    "astra_core/astro_physics/next_gen/astrochemistry.py",
    "astra_core/core_legacy/v94/sensorimotor_system.py",
    "astra_core/core_legacy/v94/language_grounding.py",
]

def get_parse_error(filepath):
    """Get the parse error for a file."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        ast.parse(content)
        return None
    except SyntaxError as e:
        return str(e)

def main():
    """Check all files with parse errors."""
    base_path = Path("/Users/gjw255/astrodata/SWARM/ASTRA-dev-main")

    print("Checking parse errors...")
    for filepath in PARSE_ERROR_FILES:
        full_path = base_path / filepath
        if not full_path.exists():
            print(f"❌ {filepath}: File not found")
            continue

        error = get_parse_error(full_path)
        if error:
            # Extract line number and error type
            if "line" in error:
                parts = error.split("line")
                if len(parts) > 1:
                    line_part = parts[1].split()[0]
                    print(f"❌ {filepath}: Line {line_part} - {error.split(':', 1)[1].strip() if ':' in error else error}")
                else:
                    print(f"❌ {filepath}: {error}")
            else:
                print(f"❌ {filepath}: {error}")
        else:
            print(f"✓ {filepath}: No error")

if __name__ == "__main__":
    main()
