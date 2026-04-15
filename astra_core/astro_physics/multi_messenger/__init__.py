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
