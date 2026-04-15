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
Kilonovae Domain Module for STAN-XI-ASTRO

Compact object mergers, r-process nucleosynthesis, electromagnetic counterparts

Date: 2026-03-20
Version: 1.0.0
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

# Import domain base
from .. import BaseDomainModule, DomainConfig


@dataclass
class KilonovaeDomainState:
    """Current state of Kilonovae analysis"""
    analysis_phase: str = "initial"
    parameters: Dict[str, Any] = None

    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}


class KilonovaeDomain(BaseDomainModule):
    """
    Domain specializing in Kilonovae

    Capabilities:
    - kilonova_modeling
    - rprocess_nucleosynthesis
    - em_counterparts
    - light_curve_models
    """

    def get_default_config(self) -> DomainConfig:
        """Return default configuration for Kilonovae domain"""
        return DomainConfig(
            domain_name="kilonovae",
            version="1.0.0",
            dependencies=[],
            description="Compact object mergers, r-process nucleosynthesis, electromagnetic counterparts"
        )

    def get_config(self) -> DomainConfig:
        return DomainConfig(
            domain_name="kilonovae",
            version="1.0.0",
            dependencies=[],
            keywords=['kilonova', 'r-process', 'neutron star merger', 'electromagnetic counterpart', 'heavy_elements'],
            capabilities=['kilonova_modeling', 'rprocess_nucleosynthesis', 'em_counterparts', 'light_curve_models']
        )

    def initialize(self, global_config: Dict[str, Any]) -> None:
        """Initialize Kilonovae domain"""
        logger.info(f"Initializing {self.get_config().domain_name} domain")
        self.state = KilonovaeDomainState()

    def process_query(self, query: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Process a Kilonovae query.

        Args:
            query: The input query
            context: Optional context information

        Returns:
            DomainQueryResult with answer and metadata
        """
        from .. import DomainQueryResult

        # Simple implementation for now
        result = DomainQueryResult(
            domain_name=self.get_config().domain_name,
            answer=f"{self.get_config().description}: Analysis of '{query}'",
            confidence=0.7,
            reasoning_trace=[],
            capabilities_used=[],
            metadata={}
        )

        return result


    def get_capabilities(self) -> List[str]:
        """Return list of domain capabilities"""
        config = self.get_config()
        return config.capabilities if config.capabilities else [
            "Kilonovae analysis",
            "query_processing",
            "modeling",
            "computation"
        ]
# Factory function
def create_kilonovae_domain():
    """Create a Kilonovae domain instance"""
    return KilonovaeDomain()


# Domain registration
try:
    from .. import register_domain
    register_domain(KilonovaeDomain)
except ImportError:
    pass