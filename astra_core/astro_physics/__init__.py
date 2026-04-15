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
ASTRO-SWARM: Astronomical Inference via Stigmergic Swarm Intelligence

A reconfiguration of the V36-Swarm-MORK-Graph system for astronomical
and astrophysical problem solving.

Key capabilities beyond conventional LLMs:
1. Physics-constrained causal inference
2. Multi-agent parallel hypothesis exploration
3. Persistent knowledge accumulation across sessions
4. Cross-domain analogical reasoning
5. Mechanism discovery from observational data

Extended capabilities (v2.0):
6. Radiative transfer and non-LTE excitation
7. FITS/spectral cube data handling
8. Bayesian inference and MCMC sampling
9. Multi-wavelength SED fitting
10. Astrochemical network modeling
11. Interferometric imaging (UV, CLEAN, self-cal)
12. Advanced gravitational lensing
13. MHD turbulence analysis
14. Spectroscopic database access (CDMS, JPL, LAMDA, Splatalogue)
15. Multi-scale simulation coupling

V43 additions:
16. Core ISM physics (gravitational collapse, shocks, HII regions, SNRs)
17. Data analysis infrastructure (line fitting, source extraction, kinematics)

V44 additions:
18. Radio astronomy surveys and source detection
19. Star formation and stellar evolution (IMF, supernovae, feedback)
20. SPH gas dynamics and molecular cloud formation
21. Infrared and submillimeter astronomy
22. Time series and power spectrum analysis
23. Data cube and spectrum visualization

Date: 2025-12-23
Version: 3.1.0 (V44)
"""

# Core components (using relative imports)
from .core import AstroSwarmSystem
from .physics import PhysicsEngine, AstrophysicalConstraints
from .knowledge_graph import AstronomicalKnowledgeGraph
from .inference import BayesianSwarmInference
from .agents import AstroAgent, SpectroscopicAgent, PhotometricAgent, DynamicalAgent

# Extended capability modules
from .radiative_transfer import (
    StatisticalEquilibriumSolver, LineProfileSynthesizer,
    DustContinuumRT, PDRInterface
)
from .data_interface import (
    FITSHandler, SpectralCubeHandler, VOTableHandler,
    RegionHandler, CASAInterface
)
from .uncertainty_quantification import (
    PriorSet, GaussianLikelihood, MetropolisHastings,
    EnsembleSampler, NestedSampler, FisherMatrix
)
from .sed_fitting import (
    FilterLibrary, ModifiedBlackbody, StellarPopulation,
    AGNTemplate, CompositeSED, SEDFitter
)
from .chemical_networks import (
    ReactionNetwork, ChemistrySolver, PDRChemistry,
    GrainChemistry, HotCoreChemistry
)
from .interferometry import (
    ArrayConfiguration, UVSimulator, Imager,
    CLEANDeconvolver, SelfCalibrator, VisibilityModeler
)
from .advanced_lensing import (
    Cosmology, SIEProfile, NFWProfile, CompositeLensModel,
    TimeDelayCosmography, SubstructureDetector
)
from .turbulence_analysis import (
    StructureFunctionAnalysis, PowerSpectrumAnalysis,
    VelocityAnalysis, SpectralPCA, DavisChandrasekharFermi,
    HistogramRelativeOrientations, TurbulenceStatistics
)
from .spectroscopic_databases import (
    CDMSDatabase, JPLDatabase, LAMDADatabase,
    SplatalogueInterface, HITRANDatabase, UnifiedSpectroscopyQuery,
    SpectralLine, MoleculeData, CollisionPartner
)
from .multiscale_coupling import (
    MultiScaleSimulation, ZoomRegion, ScaleCoupler,
    TurbulentPressureModel, StarFormationModel,
    StellarFeedbackModel, AGNFeedbackModel,
    CoolingFunction, HierarchicalRefinement
)

# V43: Core ISM Physics
from .gravitational_collapse import (
    JeansAnalysis, VirialAnalysis, FreefallCollapse,
    FragmentationCriterion, AccretionRates,
    get_jeans_analyzer, get_virial_analyzer
)
from .shock_physics import (
    RankineHugoniot, JShock, CShock, ShockChemistry,
    OutflowShockAnalysis, get_shock_chemistry
)
from .hii_region_physics import (
    StromgrenSphere, NebularDiagnosticsCalculator,
    RecombinationLines, FreeFreeEmission,
    stromgren_radius, get_diagnostics_calculator
)
from .supernova_remnant_physics import (
    SedovTaylorBlastwave, SNREvolution, SynchrotronEmission,
    XRayThermalEmission, get_snr_evolution
)

# V43: Data Analysis Infrastructure
from .spectral_line_analysis import (
    GaussianLineFitter, VoigtProfileFitter, HyperfineStructureFitter,
    LineIdentifier, OpticalDepthCorrector, ColumnDensityCalculator,
    fit_gaussian_line, identify_line
)
from .source_extraction import (
    SourceDetector, AperturePhotometry, PSFPhotometry,
    DendrogramExtractor, FilamentFinder, CoreCatalogBuilder,
    detect_sources, extract_dendrogram, find_filaments
)
from .kinematic_analysis import (
    MomentMapGenerator, PVDiagramExtractor, RotationCurveAnalyzer,
    InfallSignatureDetector, OutflowAnalyzer, TurbulentFieldDecomposer,
    make_moment_maps, extract_pv_diagram, detect_infall
)

# V44: Extended Astrophysics Capabilities
from .radio_surveys import (
    RadioSource, SurveyCatalog, RadioSourceType, SurveyType,
    RadioSurveyAnalyzer, VariabilityAnalyzer,
    create_analyzer, get_cross_match_tolerance, load_survey_catalog, estimate_luminosity
)
from .star_formation import (
    StellarPhase, RemnantType, SFTRindicator,
    StellarPopulation, Star,
    InitialMassFunction, StarFormationLaw, StarFormationRateTracer,
    StellarEvolution, SupernovaFeedback,
    create_stellar_population, sample_masses_from_imf, calculate_sfr_from_luminosity
)
from .sph_gas_dynamics import (
    SPHParticle, SPHKernel, KernelType, Filament,
    SPHSimulation, FilamentFinder, MolecularCloudFormation,
    TurbulentDriver, GravitySolver,
    create_sph_simulation, find_filaments_in_data, get_h2_fraction
)
from .infrared_submm import (
    IRBand, PAHFeature,
    IRPhotometry, PAHSpectrum, DustProperties,
    ModifiedBlackbody, IRColorAnalysis, SubmillimeterAnalysis, LineCooling,
    fit_dust_sed, calculate_gas_mass, get_ir_color
)
from .time_series_analysis import (
    SignalType, TimeSeries, PeriodogramResult,
    PowerSpectrumAnalyzer, VariabilityDetector, WaveletAnalyzer,
    CrossCorrelationAnalyzer, BurstDetector,
    analyze_power_spectrum, detect_periodicity, compute_structure_function, cross_correlate_series
)
from .data_visualization import (
    VisualizationType, DataCube, Spectrum,
    CubeVisualizer, SpectrumVisualizer, MultiPanelFigure,
    create_moment_map_cube, plot_spectrum
)

# V45: Deep Learning Integration (Phase 1)
from .deep_learning import (
    DLConfig,
    GalaxyMorphologyCNN,
    ISMStructureCNN,
    SpectralAutoencoder,
    LightCurveAutoencoder,
    TimeSeriesTransformer,
    RadiativeTransferPINN,
    StellarStructurePINN,
    CrossModalMatcher,
    train_autoencoder,
    SpectralDataset,
    ImageDataset
)
from .deep_learning.filament_detector import (
    FilamentDetector,
    VelocityCoherentFilamentDetector,
    FilamentProperties,
    FilamentDetectionHead,
    FilamentEncoder,
    train_filament_detector
)
from .deep_learning.molecular_cloud_segmenter import (
    MolecularCloudSegmenter,
    VelocityCubeSegmenter,
    CloudProperties,
    CloudPropertyHead,
    MaskRCNNBackbone,
    train_cloud_segmenter
)
from .deep_learning.shock_detector import (
    InterstellarShockDetector,
    SpectralLineShockDetector,
    TemporalShockDetector,
    ShockProperties,
    ShockTypeClassifier,
    ShockParameterRegressor,
    train_shock_detector
)

# V45: Real-Time Processing (Phase 2)
from .streaming.streaming_alert_processor import (
    StreamingAlertProcessor,
    AlertClassifier,
    AlertPrioritizer,
    AlertMetadata,
    ProcessedAlert,
    AlertSource,
    TransientType,
    create_alert_processor
)
from .streaming.real_time_anomaly_detection import (
    RealTimeAnomalyDetector,
    LightCurveAnomalyDetector,
    SpectralAnomalyDetector,
    AnomalyReport,
    IsolationForestOnline,
    OnlineStandardScaler,
    create_anomaly_detector
)

# V45: Multi-Messenger Joint Inference (Phase 3)
from .multi_messenger.gw_em_correlation import (
    GWEMCorrelator,
    TemporalCorrelation,
    SpatialCorrelation,
    DistanceConsistency,
    KilonovaModel,
    MultiEpochCorrelation,
    GWTrigger,
    EMCounterpart,
    JointGWEMDetection,
    create_gw_em_correlator
)
from .multi_messenger.joint_lightcurve_modeling import (
    JointLightCurveFitter,
    GWStrainModel,
    KilonovaLightCurveModel,
    GRBAfterglowModel,
    NeutrinoFluenceModel,
    JointLikelihood,
    MultiMessengerData,
    PhysicalParameters,
    create_joint_fitter
)

# V45: Causal Discovery for Astronomy (Phase 4)
from ..causal.discovery.astro_causal_discovery import (
    AstroFCI,
    TemporalCausalDiscovery,
    AstronomicalConditionalIndependence,
    CausalGraph,
    create_astro_fci,
    create_temporal_discovery
)

__version__ = "4.0.0"  # V45 - Deep Learning & Multi-Messenger Integration
__all__ = [
    # Core components
    'AstroSwarmSystem',
    'PhysicsEngine',
    'AstrophysicalConstraints',
    'AstronomicalKnowledgeGraph',
    'BayesianSwarmInference',
    'AstroAgent',
    'SpectroscopicAgent',
    'PhotometricAgent',
    'DynamicalAgent',
    # Radiative transfer
    'StatisticalEquilibriumSolver',
    'LineProfileSynthesizer',
    'DustContinuumRT',
    'PDRInterface',
    # Data interface
    'FITSHandler',
    'SpectralCubeHandler',
    'VOTableHandler',
    'RegionHandler',
    'CASAInterface',
    # Uncertainty quantification
    'PriorSet',
    'GaussianLikelihood',
    'MetropolisHastings',
    'EnsembleSampler',
    'NestedSampler',
    'FisherMatrix',
    # SED fitting
    'FilterLibrary',
    'ModifiedBlackbody',
    'StellarPopulation',
    'AGNTemplate',
    'CompositeSED',
    'SEDFitter',
    # Chemical networks
    'ReactionNetwork',
    'ChemistrySolver',
    'PDRChemistry',
    'GrainChemistry',
    'HotCoreChemistry',
    # Interferometry
    'ArrayConfiguration',
    'UVSimulator',
    'Imager',
    'CLEANDeconvolver',
    'SelfCalibrator',
    'VisibilityModeler',
    # Advanced lensing
    'Cosmology',
    'SIEProfile',
    'NFWProfile',
    'CompositeLensModel',
    'TimeDelayCosmography',
    'SubstructureDetector',
    # Turbulence analysis
    'StructureFunctionAnalysis',
    'PowerSpectrumAnalysis',
    'VelocityAnalysis',
    'SpectralPCA',
    'DavisChandrasekharFermi',
    'HistogramRelativeOrientations',
    'TurbulenceStatistics',
    # Spectroscopic databases
    'CDMSDatabase',
    'JPLDatabase',
    'LAMDADatabase',
    'SplatalogueInterface',
    'HITRANDatabase',
    'UnifiedSpectroscopyQuery',
    'SpectralLine',
    'MoleculeData',
    'CollisionPartner',
    # Multi-scale coupling
    'MultiScaleSimulation',
    'ZoomRegion',
    'ScaleCoupler',
    'TurbulentPressureModel',
    'StarFormationModel',
    'StellarFeedbackModel',
    'AGNFeedbackModel',
    'CoolingFunction',
    'HierarchicalRefinement',
    # V43: Core ISM Physics
    'JeansAnalysis',
    'VirialAnalysis',
    'FreefallCollapse',
    'FragmentationCriterion',
    'AccretionRateCalculator',
    'get_jeans_analysis',
    'get_virial_analysis',
    'RankineHugoniot',
    'JShock',
    'CShock',
    'ShockChemistry',
    'OutflowShock',
    'get_shock_chemistry',
    'StromgrenSphere',
    'NebularDiagnosticsCalculator',
    'RecombinationLines',
    'FreeFreeEmission',
    'calculate_stromgren_radius',
    'get_nebular_diagnostics',
    'SedovTaylorBlastwave',
    'SNREvolution',
    'SynchrotronEmission',
    'XRayThermalEmission',
    'get_snr_evolution',
    # V43: Data Analysis Infrastructure
    'GaussianLineFitter',
    'VoigtProfileFitter',
    'HyperfineStructureFitter',
    'LineIdentifier',
    'OpticalDepthCorrector',
    'ColumnDensityCalculator',
    'fit_gaussian',
    'fit_hyperfine',
    'identify_lines',
    'SourceDetector',
    'AperturePhotometry',
    'PSFPhotometry',
    'DendrogramExtractor',
    'FilamentFinder',
    'CoreCatalogBuilder',
    'detect_sources',
    'extract_dendrogram',
    'find_filaments',
    'MomentMapGenerator',
    'PVDiagramExtractor',
    'RotationCurveAnalyzer',
    'InfallSignatureDetector',
    'OutflowAnalyzer',
    'TurbulentFieldDecomposer',
    'make_moment_maps',
    'extract_pv_diagram',
    'detect_infall',
    # V44: Extended Astrophysics Capabilities
    # Radio surveys
    'RadioSource',
    'SurveyCatalog',
    'RadioSourceType',
    'SurveyType',
    'RadioSurveyAnalyzer',
    'VariabilityAnalyzer',
    'create_analyzer',
    'get_cross_match_tolerance',
    'load_survey_catalog',
    'estimate_luminosity',
    # Star formation
    'StellarPhase',
    'RemnantType',
    'SFTRindicator',
    'StellarPopulation',
    'Star',
    'InitialMassFunction',
    'StarFormationLaw',
    'StarFormationRateTracer',
    'StellarEvolution',
    'SupernovaFeedback',
    'create_stellar_population',
    'sample_masses_from_imf',
    'calculate_sfr_from_luminosity',
    # SPH gas dynamics
    'SPHParticle',
    'SPHKernel',
    'KernelType',
    'Filament',
    'SPHSimulation',
    'FilamentFinder',
    'MolecularCloudFormation',
    'TurbulentDriver',
    'GravitySolver',
    'create_sph_simulation',
    'find_filaments_in_data',
    'get_h2_fraction',
    # Infrared/submillimeter
    'IRBand',
    'PAHFeature',
    'IRPhotometry',
    'PAHSpectrum',
    'DustProperties',
    'ModifiedBlackbody',
    'IRColorAnalysis',
    'SubmillimeterAnalysis',
    'LineCooling',
    'fit_dust_sed',
    'calculate_gas_mass',
    'get_ir_color',
    # Time series analysis
    'SignalType',
    'TimeSeries',
    'PeriodogramResult',
    'PowerSpectrumAnalyzer',
    'VariabilityDetector',
    'WaveletAnalyzer',
    'CrossCorrelationAnalyzer',
    'BurstDetector',
    'analyze_power_spectrum',
    'detect_periodicity',
    'compute_structure_function',
    'cross_correlate_series',
    # Data visualization
    'VisualizationType',
    'DataCube',
    'Spectrum',
    'CubeVisualizer',
    'SpectrumVisualizer',
    'MultiPanelFigure',
    'create_moment_map_cube',
    'plot_spectrum',
    # V45: Deep Learning Integration (Phase 1)
    'DLConfig',
    'GalaxyMorphologyCNN',
    'ISMStructureCNN',
    'SpectralAutoencoder',
    'LightCurveAutoencoder',
    'TimeSeriesTransformer',
    'RadiativeTransferPINN',
    'StellarStructurePINN',
    'CrossModalMatcher',
    'train_autoencoder',
    'SpectralDataset',
    'ImageDataset',
    'FilamentDetector',
    'VelocityCoherentFilamentDetector',
    'FilamentProperties',
    'FilamentDetectionHead',
    'FilamentEncoder',
    'train_filament_detector',
    'MolecularCloudSegmenter',
    'VelocityCubeSegmenter',
    'CloudProperties',
    'CloudPropertyHead',
    'MaskRCNNBackbone',
    'train_cloud_segmenter',
    'InterstellarShockDetector',
    'SpectralLineShockDetector',
    'TemporalShockDetector',
    'ShockProperties',
    'ShockTypeClassifier',
    'ShockParameterRegressor',
    'train_shock_detector',
    # V45: Real-Time Processing (Phase 2)
    'StreamingAlertProcessor',
    'AlertClassifier',
    'AlertPrioritizer',
    'AlertMetadata',
    'ProcessedAlert',
    'AlertSource',
    'TransientType',
    'create_alert_processor',
    'RealTimeAnomalyDetector',
    'LightCurveAnomalyDetector',
    'SpectralAnomalyDetector',
    'AnomalyReport',
    'IsolationForestOnline',
    'OnlineStandardScaler',
    'create_anomaly_detector',
    # V45: Multi-Messenger Joint Inference (Phase 3)
    'GWEMCorrelator',
    'TemporalCorrelation',
    'SpatialCorrelation',
    'DistanceConsistency',
    'KilonovaModel',
    'MultiEpochCorrelation',
    'GWTrigger',
    'EMCounterpart',
    'JointGWEMDetection',
    'create_gw_em_correlator',
    'JointLightCurveFitter',
    'GWStrainModel',
    'KilonovaLightCurveModel',
    'GRBAfterglowModel',
    'NeutrinoFluenceModel',
    'JointLikelihood',
    'MultiMessengerData',
    'PhysicalParameters',
    'create_joint_fitter',
    # V45: Causal Discovery for Astronomy (Phase 4)
    'AstroFCI',
    'TemporalCausalDiscovery',
    'AstronomicalConditionalIndependence',
    'CausalGraph',
    'create_astro_fci',
    'create_temporal_discovery',
]



def utility_function_7(*args, **kwargs):
    """Utility function 7."""
    return None



def utility_function_27(*args, **kwargs):
    """Utility function 27."""
    return None


