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
Astrochemical Surveys Domain Module for STAN-XI-ASTRO

Specializes in astrochemical surveys and chemistry:
- Interstellar molecular inventories
- Chemical complexity in space
- Deuterium fractionation
- Isotopic ratios
- Prebiotic chemistry
- Molecular clocks
- Metal-poor chemistry
- Extragalactic astrochemistry
- Snow lines and ice chemistry
- ALMA and IRAM chemical surveys

Date: 2026-03-20
Version: 1.0.0
"""

import numpy as np
from typing import Dict, List, Any, Optional
import logging

try:
    from .. import BaseDomainModule, DomainConfig, DomainQueryResult, register_domain
except ImportError:
    class BaseDomainModule:
        def __init__(self, config=None):
            self.config = config
            self._initialized = False

    class DomainConfig:
        def __init__(self, **kwargs):
            self.domain_name = kwargs.get('domain_name', '')
            self.version = kwargs.get('version', '1.0.0')
            self.dependencies = kwargs.get('dependencies', [])
            self.keywords = kwargs.get('keywords', [])
            self.task_types = kwargs.get('task_types', [])
            self.enabled = kwargs.get('enabled', True)
            self.description = kwargs.get('description', '')
            self.capabilities = kwargs.get('capabilities', [])

    class DomainQueryResult:
        def __init__(self, **kwargs):
            self.domain_name = kwargs.get('domain_name', '')
            self.answer = kwargs.get('answer', '')
            self.confidence = kwargs.get('confidence', 0.0)
            self.reasoning_trace = kwargs.get('reasoning_trace', [])
            self.capabilities_used = kwargs.get('capabilities_used', [])
            self.metadata = kwargs.get('metadata', {})

    def register_domain(cls):
        return cls

logger = logging.getLogger(__name__)


@register_domain
class AstrochemicalSurveysDomain(BaseDomainModule):
    """Domain specializing in astrochemical surveys"""

    def __init__(self, config: Optional[DomainConfig] = None):
        self.config = config or self.get_default_config()
        self._initialized = False

    def get_default_config(self) -> DomainConfig:
        return DomainConfig(
            domain_name="astrochemical_surveys",
            version="1.0.0",
            dependencies=["astro_physics", "ism", "star_formation"],
            keywords=[
                "astrochemistry", "molecular inventory", "molecule", "complex organic",
                "prebiotic", "amino acid", "sugar", "rna", "dna", "aldehyde",
                "alcohol", "nitrile", "polyyne", "carbon chain", "fullerene", "pa",
                "deuterium", "fractionation", "d/h ratio", "isotopologue", "13c",
                "18o", "15n", "ice mantel", "snow line", "co ice", "h2o ice",
                "alma", "irm", "noema", "chemical survey", "spectral line survey"
            ],
            task_types=["MOLECULAR_INVENTORY", "ISOTOPOLOGUE_ANALYSIS", "ICE_CHEMISTRY"],
            description="Astrochemical surveys and interstellar chemistry",
            capabilities=[
                "line_identification",
                "column_density",
                "abundance_ratio",
                "fractionation_modeling",
                "ice_spectroscopy",
                "chemical_modeling"
            ]
        )

    def initialize(self, global_config: Dict[str, Any]) -> None:
        super().initialize(global_config)
        logger.info("Astrochemical Surveys domain initialized")

    def process_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        query_lower = query.lower()

        if any(kw in query_lower for kw in ['molecule', 'inventory', 'line survey']):
            return self._process_inventory_query(query, context)
        elif any(kw in query_lower for kw in ['deuterium', 'fractionation', 'd/h']):
            return self._process_fractionation_query(query, context)
        elif any(kw in query_lower for kw in ['ice', 'mantel', 'snow line']):
            return self._process_ice_query(query, context)
        elif any(kw in query_lower for kw in ['prebiotic', 'organic', 'amino']):
            return self._process_prebiotic_query(query, context)
        elif any(kw in query_lower for kw in ['alma', 'irm', 'survey']):
            return self._process_survey_query(query, context)
        else:
            return self._process_general_astrochem_query(query, context)

    def get_capabilities(self) -> List[str]:
        return self.config.capabilities

    def _process_inventory_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        reasoning_trace = ["Processing molecular inventory query"]

        answer = (
            "ISM contains >250 molecules detected via rotational spectroscopy. "
            "Abundant species: H₂ (dominant), CO (tracer), H₂O, OH, NH₃, HCN. "
            "Organic molecules: CH₃OH, C₂H₅OH, CH₃CHO, HCOOCH₃, (CH₃)₂O. "
            "Complex organics: glycolaldehyde, ethylene glycol, CH₃NCO. "
            "Carbon chains: C₂H, C₃H, C₄H, C₆H, HC₃N, HC₅N, HC₇N, HC₉N, HC₁₁N. "
            "Fullerenes: C₆₀ (buckminsterfullerene), C₇₀. "
            "Detection methods: mm/submm (ALMA, IRAM), IR (JWST ice features), "
            "radio lines (OH maser, H₂O maser). Column densities from "
            "rotational diagrams: N/Q ∝ ∫ T_B dv / A_μ S_μ."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.90,
            reasoning_trace=reasoning_trace,
            capabilities_used=["line_identification", "column_density"],
            metadata={"query_type": "INVENTORY"}
        )

    def _process_fractionation_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        reasoning_trace = ["Processing fractionation query"]

        answer = (
            "Deuterium fractionation: D/H ratio enhanced in cold gas due to "
            "zero-point energy differences. Key reactions: H₃⁺ + HD → H₂D⁺ + H₂ + ΔE. "
            "Fractionation f = [XD]/[XH] ~ 10⁻³ (ISM), enhanced to 0.1 in cold cores. "
            "Observations: DCO⁺/HCO⁺, N₂D⁺/N₂H⁺, DCN/HCN, D₂CO/H₂CO. "
            "Multiply deuterated species: ND₃, CD₃OH, D₂CO. "
            "Other isotopes: ¹³C/¹²C ~ 1/60, ¹⁸O/¹⁶O ~ 1/500, ¹⁵N/¹⁴N ~ 1/300. "
            "Uses: tracing cold gas (<20 K), ionization fraction, "
            "chemical age, initial conditions (pre-stellar enrichment)."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.89,
            reasoning_trace=reasoning_trace,
            capabilities_used=["abundance_ratio", "fractionation_modeling"],
            metadata={"query_type": "FRACTIONATION"}
        )

    def _process_ice_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        reasoning_trace = ["Processing ice chemistry query"]

        answer = (
            "Ice mantles form on dust grains in cold, dense regions. "
            "Components: H₂O (dominant), CO, CO₂, CH₃OH, NH₃, CH₄, H₂CO. "
            "Snow lines: H₂O (~150 K), CO₂ (~80 K), CO (~20 K). "
            "Ice spectroscopy: IR bands (3 μm H₂O, 4.67 μm CO, 6.85 μm CH₃OH). "
            "Processing: UV photolysis, cosmic ray irradiation, thermal processing. "
            "Complex organics form in ices: HNCO, CH₃CN, CH₃CHO. "
            "Observations: JWST NIRSpec, Spitzer c2d, VLT. Ice abundances "
            "relative to H₂O: CO ~ 10-30%, CH₃OH ~ 5-30%, CO₂ ~ 10-40%."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.88,
            reasoning_trace=reasoning_trace,
            capabilities_used=["ice_spectroscopy", "chemical_modeling"],
            metadata={"query_type": "ICE"}
        )

    def _process_prebiotic_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        reasoning_trace = ["Processing prebiotic chemistry query"]

        answer = (
            "Prebiotic molecules detected in ISM: amino acids (glycine), "
            "sugars (glycolaldehyde), nucleobase precursors (pyrimidine). "
            "Interstellar synthesis pathways: grain-surface hydrogenation "
            "(CO → HCO → H₂CO → CH₃OH), radical recombination in ices, "
            "gas-phase ion-molecule reactions. "
            "Complexity limit: detection of molecules up to ~12 atoms. "
            "Hot cores/corinos: thermal desorption releases ice products. "
            "ALMA detections: glycolaldehyde (MM1), ethylene glycol (IRAS 16293). "
            "Prebiotic reservoirs: comets, meteorites, protoplanetary disks."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.87,
            reasoning_trace=reasoning_trace,
            capabilities_used=["line_identification", "chemical_modeling"],
            metadata={"query_type": "PREBIOTIC"}
        )

    def _process_survey_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        reasoning_trace = ["Processing survey query"]

        answer = (
            "Major astrochemical surveys: (1) ALMA: EMoCA (2 mm band), PILS "
            "(Class 0 protostar, IRAS 16293), ASAI (hot cores/corinos). "
            "(2) IRAM 30m: TIMASSS (spectral scan 80-300 GHz). "
            "(3) Yebes 40m: QUIJOTE (dark clouds). "
            "(4) GBT: CMZ (Galactic Center). "
            "Survey goals: complete molecular inventories, abundance patterns, "
            "chemical evolution, spatial variations. Data products: line catalogs, "
            "column densities, abundance maps, chemical models. Challenges: "
            "line confusion, spectral resolution, calibration."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.86,
            reasoning_trace=reasoning_trace,
            capabilities_used=["line_identification", "column_density"],
            metadata={"query_type": "SURVEY"}
        )

    def _process_general_astrochem_query(self, query: str, context: Dict[str, Any]) -> DomainQueryResult:
        reasoning_trace = ["Processing general astrochemistry query"]

        answer = (
            "Astrochemistry studies molecular universe from clouds to planets. "
            "Key processes: gas-phase ion-molecule reactions, grain-surface "
            "hydrogenation, UV photodissociation, cosmic ray ionization, "
            "freeze-out/desorption. Chemical models: rate equations, "
            "Monte Carlo (stochastic), macroscopic Monte Carlo. "
            "Observational tracers: rotational spectra (mm/submm), "
            "vibrational bands (IR), ro-vibrational (near-IR). "
            "Laboratory astrophysics: spectroscopy, ice analogs, "
            "reaction rate measurements. Facilities: ALMA, NOEMA, "
            "IRAM 30m, GBT, VLA, JCMT, Sofia (past), JWST (ice)."
        )

        return DomainQueryResult(
            domain_name=self.config.domain_name,
            answer=answer,
            confidence=0.85,
            reasoning_trace=reasoning_trace,
            capabilities_used=["chemical_modeling", "line_identification"],
            metadata={"query_type": "GENERAL"}
        )


def create_astrochemical_surveys_domain() -> AstrochemicalSurveysDomain:
    return AstrochemicalSurveysDomain()
