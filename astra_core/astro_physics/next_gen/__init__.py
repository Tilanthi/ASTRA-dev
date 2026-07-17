"""
Next-Generation Astrophysics Capabilities

This module extends STAN with advanced capabilities for next-generation
telescope data analysis and theoretical modeling.

Modules:
- archive_query: VO/TAP interfaces to major astronomical archives
- transient_science: Light curve fitting, classification, transient physics
- astrochemistry: Extended chemical networks, COMs, isotopologue analysis
- disk_physics: Protoplanetary disk structure, planet-disk interaction
- galactic_dynamics: Orbit fitting, stellar streams, chemical evolution
- ml_survey: Machine learning for large survey analysis
- atmospheric_retrieval: Exoplanet atmosphere modeling
- cosmological_context: Galaxy-halo connection, environment effects
- alert_processing: Real-time transient alert stream handling
- radio_astronomy: Radio data processing (ALMA, VLA, LOFAR, MWA)

Date: 2025-12-15
Version: 1.1
"""

# Best-effort submodule loading: each next_gen module is imported individually
# and its public names are exposed (or set to None if the submodule or a name
# is unavailable). Several next_gen modules are still incomplete (missing
# classes); this guard keeps the package importable so the complete modules
# (astrochemistry, alert_processing, archive_query, ...) remain usable.
import importlib as _importlib

_NEXT_GEN_NAMES = {
    'archive_query': ['VOQueryEngine', 'TAP_Client', 'AstroqueryInterface',
                      'CrossMatchEngine', 'ArchiveDataManager',
                      'ALMAArchive', 'NRAOArchive', 'LOFARArchive', 'MWAArchive',
                      'ESOArchive', 'RadioArchiveManager'],
    'transient_science': ['TransientClassifier', 'LightCurveFitter', 'SupernovaModels',
                          'GRBAfterglowModel', 'KilonovaModel', 'TransientAlertBroker'],
    'astrochemistry': ['ChemicalNetwork', 'UMISTNetwork', 'KIDANetwork',
                       'GrainSurfaceChemistry', 'IsotopologueAnalyzer',
                       'COMFormationModel', 'DeuteriumFractionation'],
    'disk_physics': ['ProtoplanetaryDisk', 'DiskEvolutionModel', 'GapOpeningCriteria',
                     'DustGrainEvolution', 'DiskDispersalModel', 'PlanetDiskInteraction'],
    'galactic_dynamics': ['GalacticPotential', 'OrbitIntegrator', 'StellarStreamFinder',
                          'ChemicalEvolutionModel', 'ActionAngleCalculator', 'ClusterDissolutionModel'],
    'ml_survey': ['AnomalyDetector', 'PhotometricRedshiftEstimator', 'SourceClassifier',
                  'SpectralAutoencoder', 'ActiveLearningSelector'],
    'atmospheric_retrieval': ['AtmosphericRetrieval', 'TransmissionSpectrum', 'EmissionSpectrum',
                              'CloudModel', 'ChemicalEquilibrium'],
    'cosmological_context': ['HaloMassFunction', 'GalaxyHaloConnection', 'EnvironmentalMetrics',
                             'CGMModel', 'ReionizationModel'],
    'alert_processing': ['AlertStreamProcessor', 'ZTFAlertHandler', 'RubinAlertHandler',
                         'AlertFilterPipeline', 'FollowUpPrioritizer'],
    'radio_astronomy': ['RadioFacility', 'ObservingBand', 'RadioObservation', 'Visibility',
                        'RadioSource', 'FacilitySpecs', 'RadioContinuumAnalysis', 'RadioSpectralLine',
                        'RadioInterferometry', 'LowFrequencyRadio', 'RadioPolarization',
                        'RadioSourcePhysics', 'RadioArchiveInterface',
                        'jy_to_kelvin', 'kelvin_to_jy', 'freq_to_wavelength', 'wavelength_to_freq'],
}

for _modname, _names in _NEXT_GEN_NAMES.items():
    try:
        _mod = _importlib.import_module('.' + _modname, __name__)
    except Exception:
        _mod = None
    for _n in _names:
        globals()[_n] = getattr(_mod, _n, None) if _mod is not None else None

del _importlib, _modname, _names, _mod

__all__ = [
    # Archive Query
    'VOQueryEngine', 'TAP_Client', 'AstroqueryInterface',
    'CrossMatchEngine', 'ArchiveDataManager',
    'ALMAArchive', 'NRAOArchive', 'LOFARArchive', 'MWAArchive',
    'ESOArchive', 'RadioArchiveManager',

    # Transient Science
    'TransientClassifier', 'LightCurveFitter', 'SupernovaModels',
    'GRBAfterglowModel', 'KilonovaModel', 'TransientAlertBroker',

    # Astrochemistry
    'ChemicalNetwork', 'UMISTNetwork', 'KIDANetwork',
    'GrainSurfaceChemistry', 'IsotopologueAnalyzer',
    'COMFormationModel', 'DeuteriumFractionation',

    # Disk Physics
    'ProtoplanetaryDisk', 'DiskEvolutionModel', 'GapOpeningCriteria',
    'DustGrainEvolution', 'DiskDispersalModel', 'PlanetDiskInteraction',

    # Galactic Dynamics
    'GalacticPotential', 'OrbitIntegrator', 'StellarStreamFinder',
    'ChemicalEvolutionModel', 'ActionAngleCalculator', 'ClusterDissolutionModel',

    # ML Survey
    'AnomalyDetector', 'PhotometricRedshiftEstimator', 'SourceClassifier',
    'SpectralAutoencoder', 'ActiveLearningSelector',

    # Atmospheric Retrieval
    'AtmosphericRetrieval', 'TransmissionSpectrum', 'EmissionSpectrum',
    'CloudModel', 'ChemicalEquilibrium',

    # Cosmological Context
    'HaloMassFunction', 'GalaxyHaloConnection', 'EnvironmentalMetrics',
    'CGMModel', 'ReionizationModel',

    # Alert Processing
    'AlertStreamProcessor', 'ZTFAlertHandler', 'RubinAlertHandler',
    'AlertFilterPipeline', 'FollowUpPrioritizer',

    # Radio Astronomy
    'RadioFacility', 'ObservingBand', 'RadioObservation', 'Visibility', 'RadioSource',
    'FacilitySpecs', 'RadioContinuumAnalysis', 'RadioSpectralLine',
    'RadioInterferometry', 'LowFrequencyRadio', 'RadioPolarization',
    'RadioSourcePhysics', 'RadioArchiveInterface',
    'jy_to_kelvin', 'kelvin_to_jy', 'freq_to_wavelength', 'wavelength_to_freq',
]

__version__ = '1.1'


