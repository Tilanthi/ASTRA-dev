"""
ASTRA Scientific Discovery Module
===================================

Comprehensive scientific discovery system for autonomous research in astronomy
and astrophysics. Integrates literature mining, data analysis, theoretical
modeling, and autonomous experiment design.

Modules:
--------
- literature_validator: Real literature validation and novelty assessment
- eureka_detector: Genuine scientific insight detection (NEW v3.0)
- eureka_validator: Eureka-enhanced literature validation (NEW v3.0)
- query_optimizer: Intelligent literature search query optimization
- validation_pipeline: Multi-stage discovery validation
- research_papers: PDF processing, citation networks, literature mining
- astro_databases: Access to Vizier, SIMBAD, ADS, and other catalogs
- data_repositories: Access to ALMA, NASA, ESO, CADC, arXiv datasets
- advanced_analysis: ML photometry, galaxy classification, phot-z
- theoretical_physics: MHD solvers, plasma physics, radiation-hydro
- discovery_orchestrator: Central autonomous discovery coordinator

Version: 3.0.0-Eureka
Date: 2026-07-03
"""

# =============================================================================
# Literature Validation (v2.0)
# =============================================================================
from .literature_validator import (
    LiteratureValidator,
    NoveltyReport,
    ConfidenceLevel,
    SimilarPaper,
    CitationReport,
    FormulaReport,
    create_literature_validator,
)

# =============================================================================
# Eureka Detector (NEW v3.0 - 2026-07-03)
# =============================================================================
try:
    from .eureka_detector import (
        EurekaDetector,
        EurekaAssessment,
        ScientificClaim,
        ClaimType,
        create_eureka_detector,
    )
except ImportError as e:
    import logging
    logging.warning(f"Could not import eureka_detector: {e}")

# =============================================================================
# Eureka Validator (NEW v3.0 - 2026-07-03)
# =============================================================================
try:
    from .eureka_validator import (
        EurekaEnhancedValidator,
        EurekaValidationReport,
        create_eureka_enhanced_validator,
    )
except ImportError as e:
    import logging
    logging.warning(f"Could not import eureka_validator: {e}")

# =============================================================================
# Query Optimizer (NEW v2.0 - 2026-07-01)
# =============================================================================
try:
    from .query_optimizer import (
        LiteratureQueryOptimizer,
        OptimizedQuery,
        ScientificTermExtractor,
        QueryBuilder,
        optimize_discovery_query,
    )
except ImportError as e:
    import logging
    logging.warning(f"Could not import query_optimizer: {e}")

# =============================================================================
# Validation Pipeline (NEW v2.0)
# =============================================================================
from .validation_pipeline import (
    ValidationPipeline,
    PipelineReport,
    ValidationResult,
    ValidationStage,
    ValidationStatus,
    create_validation_pipeline,
)

# =============================================================================
# Research Paper Processing
# =============================================================================
try:
    from .research_papers import (
        PDFProcessor,
        Paper,
        CitationGraph,
    )
except ImportError as e:
    import logging
    logging.warning(f"Could not import research_papers: {e}")

# =============================================================================
# Discovery Orchestrator (Main Entry Point)
# =============================================================================
try:
    from .discovery_orchestrator import (
        ScientificDiscoveryOrchestrator,
        DiscoveryTask,
        DiscoveryResult,
        Hypothesis,
        ExperimentProposal,
        LiteratureReview,
    )
except ImportError as e:
    import logging
    logging.warning(f"Could not import discovery_orchestrator: {e}")

__all__ = [
    # Literature Validation (v2.0)
    'LiteratureValidator',
    'NoveltyReport',
    'ConfidenceLevel',
    'SimilarPaper',
    'CitationReport',
    'FormulaReport',
    'create_literature_validator',

    # Eureka Detector (v3.0 - 2026-07-03)
    'EurekaDetector',
    'EurekaAssessment',
    'ScientificClaim',
    'ClaimType',
    'create_eureka_detector',

    # Eureka Validator (v3.0 - 2026-07-03)
    'EurekaEnhancedValidator',
    'EurekaValidationReport',
    'create_eureka_enhanced_validator',

    # Query Optimizer (v2.0 - 2026-07-01)
    'LiteratureQueryOptimizer',
    'OptimizedQuery',
    'ScientificTermExtractor',
    'QueryBuilder',
    'optimize_discovery_query',

    # Validation Pipeline (v2.0)
    'ValidationPipeline',
    'PipelineReport',
    'ValidationResult',
    'ValidationStage',
    'ValidationStatus',
    'create_validation_pipeline',
]

__version__ = '3.0.0-Eureka'



def autocorrelation_detect(data: np.ndarray, max_lag: int = None) -> Dict[str, Any]:
    """Detect patterns using autocorrelation analysis."""
    import numpy as np
    if max_lag is None:
        max_lag = len(data) // 4
    autocorr = np.correlate(data, data, mode='full')
    autocorr = autocorr[len(autocorr)//2:]
    autocorr = autocorr / autocorr[0]
    return {'autocorrelation': autocorr[:max_lag], 'peaks': []}



def utility_function_27(*args, **kwargs):
    """Utility function 27."""
    return None



def autocorrelation_detect(data: np.ndarray, max_lag: int = None) -> Dict[str, Any]:
    """Detect patterns using autocorrelation analysis."""
    import numpy as np
    if max_lag is None:
        max_lag = len(data) // 4
    autocorr = np.correlate(data, data, mode='full')
    autocorr = autocorr[len(autocorr)//2:]
    autocorr = autocorr / autocorr[0]
    return {'autocorrelation': autocorr[:max_lag], 'peaks': []}



def utility_function_7(*args, **kwargs):
    """Utility function 7."""
    return None


# ---------------------------------------------------------------------------
# Lazy access to the AlphaEvolve-style evolved_analysis subpackage (PEP 562).
# Accessing `astra_core.scientific_discovery.evolved_analysis` imports it on
# demand, so the heavy evolved_analysis load (and its leapcore-by-path wiring)
# is NOT paid when scientific_discovery itself is imported — only when something
# actually asks for it. Available to ASTRA without growing import-time cost.
# ---------------------------------------------------------------------------
def __getattr__(name):
    if name == "evolved_analysis":
        # Resolve by full dotted path via importlib — NOT `from . import evolved_analysis`,
        # which would re-trigger this __getattr__ and recurse.
        import importlib
        _ea = importlib.import_module(
            "astra_core.scientific_discovery.evolved_analysis")
        globals()["evolved_analysis"] = _ea   # cache; __getattr__ won't fire again
        return _ea
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


