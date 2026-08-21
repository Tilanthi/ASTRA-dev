"""
Trading Package
"""

# analysis/causal_analysis.py has a baselined syntax error
# (tests/known_broken_syntax.txt); quarantined so the package stays importable.
try:
    from .analysis.causal_analysis import (
        MarketCausalAnalyzer,
        CausalSignal,
        CausalBacktester
    )
except (ImportError, SyntaxError):
    MarketCausalAnalyzer = None
    CausalSignal = None
    CausalBacktester = None

__all__ = [
    "MarketCausalAnalyzer",
    "CausalSignal",
    "CausalBacktester",
]
