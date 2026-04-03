"""
Multi-Messenger Astronomy Integration

Joint analysis and correlation of gravitational wave, electromagnetic,
and neutrino observations for multi-messenger astrophysics.

Author: STAN Evolution Team
Date: 2025-03-18
Version: 1.0.0
"""

from .gw_em_correlation import (
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

from .joint_lightcurve_modeling import (
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

__all__ = [
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
]
