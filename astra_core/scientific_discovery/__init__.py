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
STAN Scientific Discovery Module
================================

Comprehensive scientific discovery system for autonomous research in astronomy
and astrophysics. Integrates literature mining, data analysis, theoretical
modeling, and autonomous experiment design.

Modules:
--------
- research_papers: PDF processing, citation networks, literature mining
- astro_databases: Access to Vizier, SIMBAD, ADS, and other catalogs
- data_repositories: Access to ALMA, NASA, ESO, CADC, arXiv datasets
- advanced_analysis: ML photometry, galaxy classification, phot-z
- theoretical_physics: MHD solvers, plasma physics, radiation-hydro
- discovery_orchestrator: Central autonomous discovery coordinator

Version: 1.0.0-Discovery
Date: 2025-12-27
"""

# =============================================================================
# Research Paper Processing
# =============================================================================
from .research_papers import (
    PDFProcessor,
    CitationNetwork,
    LiteratureMiner,
    PaperAnalyzer,
    Paper,
    CitationGraph,
    extract_paper_metadata,
    build_citation_network,
)

# =============================================================================
# Astronomical Database Access
# =============================================================================
from .astro_databases import (
    AstroDatabaseConnector,
    VizierClient,
    SIMBADClient,
    ADSClient,
    CatalogQuery,
    SourceInfo,
    query_catalog,
    cross_match_catalogs,
)

# =============================================================================
# Data Repository Access
# =============================================================================
from .data_repositories import (
    DataRepositoryManager,
    ALMAArchive,
    NASAArchive,
    ESOArchive,
    CADCArchive,
    ArxivClient,
    DatasetDownloader,
    download_observation,
    query_archive,
)

# =============================================================================
# Advanced Data Analysis
# =============================================================================
from .advanced_analysis import (
    AdvancedAnalyzer,
    GalaxyClassifier,
    PhotometricRedshiftEstimator,
    SEDFitter,
    SourceExtractor,
    LineIdentifier,
    classify_galaxy,
    estimate_photoz,
    fit_sed,
    identify_lines,
)

# =============================================================================
# Theoretical Physics
# =============================================================================
from .theoretical_physics import (
    TheoreticalPhysicsEngine,
    MHDSolver,
    PlasmaPhysicsModule,
    RadiationHydrodynamics,
    GRMHDModule,
    CosmicRayTransport,
    MagneticReconnection,
    solve_mhd,
    run_radiation_hydro,
)

# =============================================================================
# Discovery Orchestrator (Main Entry Point)
# =============================================================================
from .discovery_orchestrator import (
    ScientificDiscoveryOrchestrator,
    DiscoveryTask,
    DiscoveryResult,
    Hypothesis,
    ExperimentProposal,
    LiteratureReview,
    create_discovery_system,
    autonomous_discovery,
    review_literature,
    propose_experiment,
)

__all__ = [
    # Research Papers
    'PDFProcessor',
    'CitationNetwork',
    'LiteratureMiner',
    'PaperAnalyzer',
    'Paper',
    'CitationGraph',
    'extract_paper_metadata',
    'build_citation_network',

    # Astro Databases
    'AstroDatabaseConnector',
    'VizierClient',
    'SIMBADClient',
    'ADSClient',
    'CatalogQuery',
    'SourceInfo',
    'query_catalog',
    'cross_match_catalogs',

    # Data Repositories
    'DataRepositoryManager',
    'ALMAArchive',
    'NASAArchive',
    'ESOArchive',
    'CADCArchive',
    'ArxivClient',
    'DatasetDownloader',
    'download_observation',
    'query_archive',

    # Advanced Analysis
    'AdvancedAnalyzer',
    'GalaxyClassifier',
    'PhotometricRedshiftEstimator',
    'SEDFitter',
    'SourceExtractor',
    'LineIdentifier',
    'classify_galaxy',
    'estimate_photoz',
    'fit_sed',
    'identify_lines',

    # Theoretical Physics
    'TheoreticalPhysicsEngine',
    'MHDSolver',
    'PlasmaPhysicsModule',
    'RadiationHydrodynamics',
    'GRMHDModule',
    'CosmicRayTransport',
    'MagneticReconnection',
    'solve_mhd',
    'run_radiation_hydro',

    # Discovery Orchestrator
    'ScientificDiscoveryOrchestrator',
    'DiscoveryTask',
    'DiscoveryResult',
    'Hypothesis',
    'ExperimentProposal',
    'LiteratureReview',
    'create_discovery_system',
    'autonomous_discovery',
    'review_literature',
    'propose_experiment',
]

__version__ = '1.0.0-Discovery'



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


