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
Ablation Study Configurations for ASTRA

Defines all ablation configurations to systematically test
the contribution of each component to ASTRA's performance.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set
from enum import Enum


class AblationType(Enum):
    """Types of ablations to perform"""
    CORE_ARCHITECTURE = "core_architecture"
    MEMORY_SYSTEM = "memory_system"
    DOMAIN_MODULES = "domain_modules"
    PHYSICS_ENGINE = "physics_engine"
    CAUSAL_DISCOVERY = "causal_discovery"
    META_LEARNING = "meta_learning"
    CAPABILITIES = "capabilities"


@dataclass
class AblationConfig:
    """Configuration for a single ablation study"""
    name: str
    description: str
    ablation_type: AblationType

    # Components to disable
    disabled_components: Set[str] = field(default_factory=set)

    # Component-specific settings
    settings: Dict[str, Any] = field(default_factory=dict)

    # Expected impact (hypothesis)
    expected_impact: str = ""
    expected_degradation: float = 0.0  # Expected performance drop (%)


def get_core_architecture_ablations() -> List[AblationConfig]:
    """Ablations for core V4.0 architecture components"""
    return [
        AblationConfig(
            name="no_mce",
            description="Remove Meta-Context Engine (multi-dimensional context layering)",
            ablation_type=AblationType.CORE_ARCHITECTURE,
            disabled_components={"mce", "meta_context_engine"},
            expected_impact="Reduced ability to layer context across temporal, perceptual, and conceptual dimensions",
            expected_degradation=15.0
        ),
        AblationConfig(
            name="no_asc",
            description="Remove Autocatalytic Self-Compiler (self-improvement through code synthesis)",
            ablation_type=AblationType.CORE_ARCHITECTURE,
            disabled_components={"asc", "autocatalytic_self_compiler"},
            expected_impact="No adaptive self-improvement or code synthesis capabilities",
            expected_degradation=10.0
        ),
        AblationConfig(
            name="no_crn",
            description="Remove Cognitive-Relativity Navigator (dynamic abstraction scaling)",
            ablation_type=AblationType.CORE_ARCHITECTURE,
            disabled_components={"crn", "cognitive_relativity_navigator"},
            expected_impact="Fixed abstraction level, no dynamic scaling based on task complexity",
            expected_degradation=12.0
        ),
        AblationConfig(
            name="no_mmol",
            description="Remove Multi-Mind Orchestration Layer (7 specialized minds)",
            ablation_type=AblationType.CORE_ARCHITECTURE,
            disabled_components={"mmol", "multi_mind_orchestration"},
            expected_impact="Single reasoning mode instead of 7 specialized minds",
            expected_degradation=20.0
        ),
    ]


def get_memory_system_ablations() -> List[AblationConfig]:
    """Ablations for memory system components"""
    return [
        AblationConfig(
            name="no_working_memory",
            description="Remove Working Memory (7±2 capacity constraint)",
            ablation_type=AblationType.MEMORY_SYSTEM,
            disabled_components={"working_memory"},
            expected_impact="Impaired multi-step reasoning and information synthesis",
            expected_degradation=18.0
        ),
        AblationConfig(
            name="no_episodic_memory",
            description="Remove Episodic Memory (session-specific experiences)",
            ablation_type=AblationType.MEMORY_SYSTEM,
            disabled_components={"episodic_memory"},
            expected_impact="No ability to recall session-specific context",
            expected_degradation=8.0
        ),
        AblationConfig(
            name="no_mork_ontology",
            description="Remove MORK Ontology (concept hierarchies)",
            ablation_type=AblationType.MEMORY_SYSTEM,
            disabled_components={"mork_ontology"},
            expected_impact="Reduced conceptual understanding and relationship mapping",
            expected_degradation=15.0
        ),
        AblationConfig(
            name="no_vector_store",
            description="Remove Vector Store (semantic retrieval)",
            ablation_type=AblationType.MEMORY_SYSTEM,
            disabled_components={"vector_store"},
            expected_impact="Impaired semantic similarity and analogical reasoning",
            expected_degradation=12.0
        ),
        AblationConfig(
            name="minimal_memory",
            description="Minimal memory (only basic caching)",
            ablation_type=AblationType.MEMORY_SYSTEM,
            disabled_components={"working_memory", "episodic_memory", "mork_ontology", "vector_store"},
            expected_impact="Only basic caching, no sophisticated memory operations",
            expected_degradation=35.0
        ),
    ]


def get_domain_module_ablations() -> List[AblationConfig]:
    """Ablations for domain modules"""
    return [
        AblationConfig(
            name="core_domains_only",
            description="Only core domains (reasoning, memory, physics, causal)",
            ablation_type=AblationType.DOMAIN_MODULES,
            settings={"max_domains": "core_only"},
            expected_impact="No astrophysics-specific domain knowledge",
            expected_degradation=40.0
        ),
        AblationConfig(
            name="no_ism_domains",
            description="Remove all ISM-related domains",
            ablation_type=AblationType.DOMAIN_MODULES,
            settings={"excluded_domains": ["ism", "ism_structure", "ism_chemistry", "ism_dynamics"]},
            expected_impact="No specialized ISM knowledge",
            expected_degradation=25.0
        ),
        AblationConfig(
            name="no_star_formation_domains",
            description="Remove star formation domains",
            ablation_type=AblationType.DOMAIN_MODULES,
            settings={"excluded_domains": ["star_formation", "stellar_evolution", "protostars"]},
            expected_impact="No specialized star formation knowledge",
            expected_degradation=20.0
        ),
        AblationConfig(
            name="no_exoplanet_domains",
            description="Remove exoplanet domains",
            ablation_type=AblationType.DOMAIN_MODULES,
            settings={"excluded_domains": ["exoplanets", "transit_photometry", "radial_velocity"]},
            expected_impact="No specialized exoplanet knowledge",
            expected_degradation=15.0
        ),
        AblationConfig(
            name="no_high_energy_domains",
            description="Remove high-energy astrophysics domains",
            ablation_type=AblationType.DOMAIN_MODULES,
            settings={"excluded_domains": ["high_energy", "pulsars", "black_holes", "xray_binaries"]},
            expected_impact="No specialized high-energy astrophysics knowledge",
            expected_degradation=18.0
        ),
    ]


def get_physics_engine_ablations() -> List[AblationConfig]:
    """Ablations for physics engine"""
    return [
        AblationConfig(
            name="basic_physics_only",
            description="Only basic physics stage (no curriculum learning)",
            ablation_type=AblationType.PHYSICS_ENGINE,
            settings={"physics_stages": ["basic"]},
            expected_impact="No advanced physics reasoning capabilities",
            expected_degradation=30.0
        ),
        AblationConfig(
            name="no_analogical_reasoning",
            description="Remove physics analogical reasoning",
            ablation_type=AblationType.PHYSICS_ENGINE,
            disabled_components={"physics_analogical_reasoner"},
            expected_impact="No physics-based analogical reasoning",
            expected_degradation=10.0
        ),
        AblationConfig(
            name="no_constraint_validation",
            description="Remove physics constraint validation",
            ablation_type=AblationType.PHYSICS_ENGINE,
            disabled_components={"physics_constraint_validator"},
            expected_impact="No validation of physical plausibility",
            expected_degradation=15.0
        ),
        AblationConfig(
            name="no_unified_physics",
            description="Remove unified physics engine (use basic models only)",
            ablation_type=AblationType.PHYSICS_ENGINE,
            disabled_components={"unified_physics_engine"},
            expected_impact="No integrated physics modeling",
            expected_degradation=25.0
        ),
    ]


def get_causal_discovery_ablations() -> List[AblationConfig]:
    """Ablations for causal discovery components"""
    return [
        AblationConfig(
            name="no_v50_causal",
            description="Remove V50 causal discovery engine",
            ablation_type=AblationType.CAUSAL_DISCOVERY,
            disabled_components={"v50_causal_discovery"},
            expected_impact="No advanced causal discovery capabilities",
            expected_degradation=12.0
        ),
        AblationConfig(
            name="no_v70_causal",
            description="Remove V70 causal discovery engine",
            ablation_type=AblationType.CAUSAL_DISCOVERY,
            disabled_components={"v70_causal_discovery"},
            expected_impact="No hierarchical Bayesian causal discovery",
            expected_degradation=8.0
        ),
        AblationConfig(
            name="no_astro_causal",
            description="Remove astrophysical causal models",
            ablation_type=AblationType.CAUSAL_DISCOVERY,
            disabled_components={"astro_causal_models"},
            expected_impact="No domain-specific causal reasoning",
            expected_degradation=15.0
        ),
        AblationConfig(
            name="no_causal_discovery",
            description="Remove all causal discovery capabilities",
            ablation_type=AblationType.CAUSAL_DISCOVERY,
            disabled_components={"v50_causal_discovery", "v70_causal_discovery", "astro_causal_models"},
            expected_impact="No causal reasoning, only correlation-based",
            expected_degradation=20.0
        ),
    ]


def get_meta_learning_ablations() -> List[AblationConfig]:
    """Ablations for meta-learning components"""
    return [
        AblationConfig(
            name="no_maml",
            description="Remove MAML optimizer (fast adaptation)",
            ablation_type=AblationType.META_LEARNING,
            disabled_components={"maml_optimizer"},
            expected_impact="No few-shot learning adaptation",
            expected_degradation=10.0
        ),
        AblationConfig(
            name="no_cross_domain_meta",
            description="Remove cross-domain meta-learner",
            ablation_type=AblationType.META_LEARNING,
            disabled_components={"cross_domain_meta_learner"},
            expected_impact="No transfer learning between domains",
            expected_degradation=12.0
        ),
        AblationConfig(
            name="no_meta_learning",
            description="Remove all meta-learning capabilities",
            ablation_type=AblationType.META_LEARNING,
            disabled_components={"maml_optimizer", "cross_domain_meta_learner"},
            expected_impact="No learning-to-learn capabilities",
            expected_degradation=18.0
        ),
    ]


def get_capability_ablations() -> List[AblationConfig]:
    """Ablations for specialist capabilities"""
    return [
        AblationConfig(
            name="no_specialist_capabilities",
            description="Remove all 66+ specialist capabilities (V36-V94)",
            ablation_type=AblationType.CAPABILITIES,
            disabled_components={"specialist_capabilities"},
            expected_impact="No specialist reasoning capabilities",
            expected_degradation=45.0
        ),
        AblationConfig(
            name="basic_capabilities_only",
            description="Only basic capabilities (V1-V20)",
            ablation_type=AblationType.CAPABILITIES,
            settings={"max_capability_version": 20},
            expected_impact="Limited to basic reasoning capabilities",
            expected_degradation=35.0
        ),
    ]


def get_all_ablations() -> List[AblationConfig]:
    """Get all ablation configurations"""
    all_ablations = []
    all_ablations.extend(get_core_architecture_ablations())
    all_ablations.extend(get_memory_system_ablations())
    all_ablations.extend(get_domain_module_ablations())
    all_ablations.extend(get_physics_engine_ablations())
    all_ablations.extend(get_causal_discovery_ablations())
    all_ablations.extend(get_meta_learning_ablations())
    all_ablations.extend(get_capability_ablations())
    return all_ablations


def get_ablation_by_name(name: str) -> Optional[AblationConfig]:
    """Get ablation configuration by name"""
    for ablation in get_all_ablations():
        if ablation.name == name:
            return ablation
    return None


def get_critical_ablations() -> List[AblationConfig]:
    """Get most critical ablations to test (high expected impact)"""
    critical = [
        get_ablation_by_name("no_mmol"),
        get_ablation_by_name("minimal_memory"),
        get_ablation_by_name("core_domains_only"),
        get_ablation_by_name("basic_physics_only"),
        get_ablation_by_name("no_causal_discovery"),
        get_ablation_by_name("no_specialist_capabilities"),
    ]
    return [a for a in critical if a is not None]
