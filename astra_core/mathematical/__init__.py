"""
STAN_IX_ASTRO Mathematical Reasoning Module

This module contains enhanced mathematical reasoning capabilities for STAN,
including the Aletheia-style 3-agent architecture for IMO-ProofBench problems.

Components:
- AletheiaSTANSystem: Enhanced 3-agent architecture (Generator-Verifier-Reviser)
- AletheiaProofSystem: Basic 3-agent architecture
"""

# aletheia_stan_architecture.py has a baselined syntax error
# (tests/known_broken_syntax.txt); quarantined so the package stays importable.
try:
    from .aletheia_stan_architecture import (
        AletheiaSTANSystem,
        ProofStrategy,
        VerdictType,
        ProofAttempt,
        ValidationResult,
        GeneratorOutput
    )
except (ImportError, SyntaxError):
    AletheiaSTANSystem = None
    ProofStrategy = None
    VerdictType = None
    ProofAttempt = None
    ValidationResult = None
    GeneratorOutput = None

__all__ = [
    'AletheiaSTANSystem',
    'ProofStrategy',
    'VerdictType',
    'ProofAttempt',
    'ValidationResult',
    'GeneratorOutput'
]
