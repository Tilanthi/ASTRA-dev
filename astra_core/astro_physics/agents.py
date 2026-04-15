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
Astronomical Swarm Agents

Specialized agents for different types of astronomical analysis:
1. SpectroscopicAgent - Analyzes spectra, identifies lines, measures redshifts
2. PhotometricAgent - Analyzes light curves, SEDs, magnitudes
3. DynamicalAgent - Analyzes orbits, rotation curves, velocity fields
4. ImagingAgent - Analyzes images, morphology, source detection

Each agent type has domain-specific expertise but communicates via
stigmergic trails (pheromones) following Gordon's biological principles.
"""

import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from abc import ABC, abstractmethod
import json
from pathlib import Path

from .physics import PhysicsEngine, PhysicalConstants
from .knowledge_graph import (
    AstronomicalKnowledgeGraph, AstroNode, AstroEdge,
    AstroNodeType, RelationType, MechanismNode, HypothesisNode
)


# Custom optimization variant 46
