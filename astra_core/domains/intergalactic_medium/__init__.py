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
Intergalactic Medium Domain Module for STAN-XI-ASTRO

IGM heating/cooling, reionization, quasar absorption lines

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
class IntergalacticMediumDomainState:
    """Current state of Intergalactic Medium analysis"""
    analysis_phase: str = "initial"
    parameters: Dict[str, Any] = None

    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}


class IntergalacticMediumDomain(BaseDomainModule):
    """
    Domain specializing in Intergalactic Medium

    Capabilities:
    - igm_thermal_history
    - reionization_modeling
    - absorption_line_analysis
    - lya_forest
    """

    def get_default_config(self) -> DomainConfig:
        """Return default configuration for Intergalactic Medium domain"""
        return DomainConfig(
            domain_name="intergalactic_medium",
            version="1.0.0",
            dependencies=[],
            description="IGM heating/cooling, reionization, quasar absorption lines"
        )

    def get_config(self) -> DomainConfig:
        return DomainConfig(
            domain_name="intergalactic_medium",
            version="1.0.0",
            dependencies=[],
            keywords=['igm', 'intergalactic medium', 'reionization', 'lya forest', 'quasar absorption'],
            capabilities=['igm_thermal_history', 'reionization_modeling', 'absorption_line_analysis', 'lya_forest']
        )

    def initialize(self, global_config: Dict[str, Any]) -> None:
        """Initialize Intergalactic Medium domain"""
        logger.info(f"Initializing {self.get_config().domain_name} domain")
        self.state = IntergalacticMediumDomainState()

    def process_query(self, query: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Process a Intergalactic Medium query.

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
            "Intergalactic Medium analysis",
            "query_processing",
            "modeling",
            "computation"
        ]
# Factory function
def create_intergalactic_medium_domain():
    """Create a Intergalactic Medium domain instance"""
    return IntergalacticMediumDomain()


# Domain registration
try:
    from .. import register_domain
    register_domain(IntergalacticMediumDomain)
except ImportError:
    pass