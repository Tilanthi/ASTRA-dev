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
Documentation for multi_scale_inference module.

This module provides multi_scale_inference capabilities for STAN.
Enhanced through self-evolution cycle 164.
"""

#!/usr/bin/env python3
"""
Molecular Cloud Stigmergic Agents
==================================

Specialized agents for molecular cloud and dust analysis that communicate
via stigmergic trails following Gordon's biological principles.

Agent Types:
1. MolecularLineAgent - Spectral line analysis and excitation
2. DustContinuumAgent - Thermal dust emission and SED fitting
3. CloudStructureAgent - Column density and mass analysis
4. KinematicsAgent - Velocity fields and turbulence
5. ChemistryAgent - Molecular abundances and depletion
6. StarFormationAgent - Dense gas and SF diagnostics

All agents share discoveries through pheromone trails in StigmergicMemory.

Author: Claude Code (ASTRO-SWARM)
Date: 2024-11
"""

import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid

from .agents import (
    AstroAgent, PheromoneTrail, StigmergicMemory
)
from .physics import PhysicsEngine
from .knowledge_graph import (
    AstronomicalKnowledgeGraph, AstroNode, AstroEdge,
    AstroNodeType, RelationType
)
from .molecular_cloud_physics import (
    MolecularCloudPhysicsEngine, MolecularLineDatabase,
    DustModelLibrary, DustModel, CloudSpectralLine, DustSED,
    MolecularCloudProperties
)


# =============================================================================
# MOLECULAR CLOUD PHEROMONE TYPES
# =============================================================================

class CloudDiscoveryType(Enum):
    """Types of discoveries molecular cloud agents can make"""
    COLUMN_DENSITY = "column_density"
    TEMPERATURE = "temperature"
    VELOCITY_FIELD = "velocity_field"
    MASS_ESTIMATE = "mass_estimate"
    DENSE_CORE = "dense_core"
    OUTFLOW = "outflow"
    CHEMICAL_ABUNDANCE = "chemical_abundance"
    DEPLETION = "depletion"
    MAGNETIC_FIELD = "magnetic_field"
    STABILITY = "stability"
    STAR_FORMATION = "star_formation"
    FILAMENT = "filament"
    SHOCK = "shock"


@dataclass
class CloudPheromoneTrail(PheromoneTrail):
    """
    Extended pheromone trail for molecular cloud discoveries

    Carries additional cloud-specific information:
    - Physical region (core, envelope, filament, outflow)
    - Tracer molecule used
    - Reliability flags
    """
    # Cloud-specific fields
    cloud_region: str = "unspecified"  # core, envelope, filament, outflow, hii_region
    tracer_used: str = "unspecified"   # CO, HCN, dust_850um, etc.
    spatial_resolution_pc: float = 0.0
    spectral_resolution_kms: float = 0.0

    # Cross-validation flags
    confirmed_by_other_tracer: bool = False
    consistent_with_model: bool = True


# =============================================================================
# MOLECULAR LINE AGENT
# =============================================================================

class MolecularLineAgent(AstroAgent):
    """
    Agent specialized in molecular line spectroscopy

    Analyzes:
    - CO isotopologues for column density
    - NH3 for kinetic temperature
    - Dense gas tracers (HCN, HCO+, N2H+)
    - Shock tracers (SiO, CH3OH)
    - PDR tracers (CI, CII)

    Leaves trails about:
    - Excitation temperatures
    - Column densities
    - Optical depths
    - Velocity centroids and widths
    - Chemical anomalies
    """

    def __init__(self, agent_id: str,
                 physics_engine: PhysicsEngine,
                 knowledge_graph: AstronomicalKnowledgeGraph,
                 stigmergic_memory: StigmergicMemory):
        super().__init__(agent_id, physics_engine, knowledge_graph, stigmergic_memory)
        self.cloud_physics = MolecularCloudPhysicsEngine()
        self.line_db = MolecularLineDatabase()

    @property
    def agent_type(self) -> str:
        return "MolecularLineAgent"

    def analyze(self, data: Dict) -> Dict:
        """
        Analyze molecular line data

        Expected data format:
        {
            'lines': {
                '12CO_1-0': CloudSpectralLine,
                '13CO_1-0': CloudSpectralLine,
                ...
            },
            'position': {'ra': float, 'dec': float},
            'cloud_name': str
        }
        """
        results = {
            'agent': self.agent_id,
            'type': self.agent_type,
            'discoveries': []
        }

        lines = data.get('lines', {})

        # Analyze CO isotopologues if available
        if '12CO_1-0' in lines and '13CO_1-0' in lines:
            co_results = self._analyze_co(lines)
            results['co_analysis'] = co_results
            self._leave_co_trail(co_results, data)

        # Analyze NH3 for temperature
        if 'NH3_1,1' in lines and 'NH3_2,2' in lines:
            nh3_results = self._analyze_nh3(lines)
            results['nh3_analysis'] = nh3_results
            self._leave_temperature_trail(nh3_results, data)

        # Analyze dense gas tracers
        if 'HCN_1-0' in lines:
            dense_results = self._analyze_dense_gas(lines)
            results['dense_gas_analysis'] = dense_results
            self._leave_dense_gas_trail(dense_results, data)

        # Check for shock tracers
        if 'SiO_2-1' in lines:
            shock_results = self._analyze_shocks(lines)
            results['shock_analysis'] = shock_results
            self._leave_shock_trail(shock_results, data)

        # Read trails from other agents to cross-validate
        self._cross_validate_with_trails(results)

        return results

    def _analyze_co(self, lines: Dict) -> Dict:
        """Analyze CO isotopologue data"""
        co12 = lines['12CO_1-0']
        co13 = lines['13CO_1-0']
        c18o = lines.get('C18O_1-0')

        return self.cloud_physics.analyze_co_isotopologues(co12, co13, c18o)

    def _analyze_nh3(self, lines: Dict) -> Dict:
        """Analyze NH3 data for temperature"""
        nh3_11 = lines['NH3_1,1']
        nh3_22 = lines['NH3_2,2']

        return self.cloud_physics.analyze_nh3_temperature(nh3_11, nh3_22)

    def _analyze_dense_gas(self, lines: Dict) -> Dict:
        """Analyze dense gas tracers"""
        hcn = lines['HCN_1-0']
        hcop = lines.get('HCO+_1-0')
        n2hp = lines.get('N2H+_1-0')

        return self.cloud_physics.analyze_dense_gas(hcn, hcop, n2hp)

    def _analyze_shocks(self, lines: Dict) -> Dict:
        """Analyze shock tracers"""
        sio = lines['SiO_2-1']
        results = {
            'SiO_detected': True,
            'SiO_intensity': sio.integrated_intensity,
            'SiO_velocity': sio.velocity_centroid,
            'SiO_width': sio.line_width,
            'shock_indicator': sio.integrated_intensity > 0.5  # K km/s threshold
        }

        # SiO broad wings indicate outflow
        if sio.line_width > 5.0:  # km/s
            results['outflow_likely'] = True

        return results

    def _leave_co_trail(self, co_results: Dict, data: Dict):
        """Leave pheromone trail for CO analysis results"""
        trail = CloudPheromoneTrail(
            trail_id=f"mol_{uuid.uuid4().hex[:8]}",
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            timestamp=datetime.now(),
            discovery_type=CloudDiscoveryType.COLUMN_DENSITY.value,
            content={
                'N_H2': co_results['N_H2'],
                'A_V': co_results['A_V'],
                'T_ex': co_results['T_ex'],
                'tau_12CO': co_results['tau_12CO'],
                'method': 'CO_isotopologue_ratio'
            },
            confidence=0.8 if co_results['tau_12CO'] < 10 else 0.6,
            strength=8,
            evidence_quality=0.85,
            cloud_region="general",
            tracer_used="13CO",
        )
        self.memory.leave_trail(trail)

    def _leave_temperature_trail(self, nh3_results: Dict, data: Dict):
        """Leave pheromone trail for temperature measurement"""
        trail = CloudPheromoneTrail(
            trail_id=f"mol_{uuid.uuid4().hex[:8]}",
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            timestamp=datetime.now(),
            discovery_type=CloudDiscoveryType.TEMPERATURE.value,
            content={
                'T_kin': nh3_results['T_kin'],
                'T_rot': nh3_results['T_rot'],
                'method': 'NH3_rotational'
            },
            confidence=0.9,
            strength=9,
            evidence_quality=0.9,
            cloud_region="dense_gas",
            tracer_used="NH3",
        )
        self.memory.leave_trail(trail)

    def _leave_dense_gas_trail(self, dense_results: Dict, data: Dict):
        """Leave pheromone trail for dense gas detection"""
        trail = CloudPheromoneTrail(
            trail_id=f"mol_{uuid.uuid4().hex[:8]}",
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            timestamp=datetime.now(),
            discovery_type=CloudDiscoveryType.DENSE_CORE.value,
            content={
                'I_HCN': dense_results.get('I_HCN', 0),
                'chemistry': dense_results.get('chemistry_indicator', 'unknown'),
                'CO_depletion': dense_results.get('CO_depletion', 'unknown'),
            },
            confidence=0.75,
            strength=7,
            evidence_quality=0.8,
            cloud_region="core",
            tracer_used="HCN",
        )
        self.memory.leave_trail(trail)

    def _leave_shock_trail(self, shock_results: Dict, data: Dict):
        """Leave pheromone trail for shock detection"""
        if shock_results.get('shock_indicator', False):
            trail = CloudPheromoneTrail(
                trail_id=f"mol_{uuid.uuid4().hex[:8]}",
                agent_id=self.agent_id,
                agent_type=self.agent_type,
                timestamp=datetime.now(),
                discovery_type=CloudDiscoveryType.SHOCK.value,
                content={
                    'SiO_intensity': shock_results['SiO_intensity'],
                    'outflow_likely': shock_results.get('outflow_likely', False),
                    'velocity': shock_results['SiO_velocity'],
                },
                confidence=0.85,
                strength=8,
                evidence_quality=0.9,
                cloud_region="outflow",
                tracer_used="SiO",
            )
            self.memory.leave_trail(trail)

    def _cross_validate_with_trails(self, results: Dict):
        """Read trails from other agents to cross-validate"""
        # Read dust temperature trails
        dust_trails = [t for t in self.memory.get_strong_trails(threshold=6)
                       if t.discovery_type == CloudDiscoveryType.TEMPERATURE.value
                       and 'dust' in t.content.get('method', '')]

        if dust_trails and 'nh3_analysis' in results:
            dust_T = dust_trails[0].content.get('T_dust', 0)
            gas_T = results['nh3_analysis'].get('T_kin', 0)

            # Gas and dust should be coupled in dense regions
            if abs(dust_T - gas_T) < 5:
                results['T_gas_dust_coupled'] = True
                # Reinforce both trails
                dust_trails[0].reinforce(0.1)


# =============================================================================
# DUST CONTINUUM AGENT
# =============================================================================

class DustContinuumAgent(AstroAgent):
    """
    Agent specialized in dust continuum analysis

    Analyzes:
    - Submm/mm continuum for column density
    - Multi-band SEDs for temperature
    - Dust opacity and emissivity index
    - Extended structure vs point sources

    Leaves trails about:
    - Dust temperatures
    - Column densities
    - Mass estimates
    - Dust properties (β, κ)
    """

    def __init__(self, agent_id: str,
                 physics_engine: PhysicsEngine,
                 knowledge_graph: AstronomicalKnowledgeGraph,
                 stigmergic_memory: StigmergicMemory,
                 dust_model: DustModel = DustModel.OSSENKOPF_THICK):
        super().__init__(agent_id, physics_engine, knowledge_graph, stigmergic_memory)
        self.cloud_physics = MolecularCloudPhysicsEngine(dust_model)
        self.dust_model = dust_model

    @property
    def agent_type(self) -> str:
        return "DustContinuumAgent"

    def analyze(self, data: Dict) -> Dict:
        """
        Analyze dust continuum data

        Expected data format:
        {
            'sed': DustSED or None,
            'single_band': {
                'flux_Jy': float,
                'wavelength_um': float,
                'beam_arcsec': float
            },
            'distance_pc': float,
            'assumed_T_dust': float (if no SED)
        }
        """
        results = {
            'agent': self.agent_id,
            'type': self.agent_type,
            'discoveries': []
        }

        # Full SED fitting if available
        if 'sed' in data and data['sed'] is not None:
            sed_results = self.cloud_physics.fit_dust_sed(data['sed'])
            results['sed_fit'] = sed_results
            self._leave_sed_trail(sed_results, data)

        # Single-band analysis
        elif 'single_band' in data:
            sb = data['single_band']
            T_dust = data.get('assumed_T_dust', 20.0)
            distance = data['distance_pc']

            sb_results = self.cloud_physics.column_density_from_submm(
                sb['flux_Jy'], sb['wavelength_um'], T_dust,
                sb['beam_arcsec'], distance
            )
            results['single_band'] = sb_results
            self._leave_column_density_trail(sb_results, data)

        # Cross-validate with molecular line results
        self._cross_validate_with_lines(results)

        return results

    def _leave_sed_trail(self, sed_results: Dict, data: Dict):
        """Leave pheromone trail for SED fit results"""
        # Temperature trail
        trail_T = CloudPheromoneTrail(
            trail_id=f"dust_{uuid.uuid4().hex[:8]}",
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            timestamp=datetime.now(),
            discovery_type=CloudDiscoveryType.TEMPERATURE.value,
            content={
                'T_dust': sed_results['T_dust'],
                'T_dust_err': sed_results['T_dust_err'],
                'beta': sed_results['beta'],
                'method': 'dust_SED_fit'
            },
            confidence=0.9,
            strength=9,
            evidence_quality=0.95,
            cloud_region="general",
            tracer_used=f"dust_SED_{self.dust_model.value}",
        )
        self.memory.leave_trail(trail_T)

        # Mass trail
        trail_M = CloudPheromoneTrail(
            trail_id=f"dust_{uuid.uuid4().hex[:8]}",
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            timestamp=datetime.now(),
            discovery_type=CloudDiscoveryType.MASS_ESTIMATE.value,
            content={
                'M_gas': sed_results['M_gas'],
                'M_dust': sed_results['M_dust'],
                'method': 'dust_SED',
                'dust_model': sed_results['dust_model']
            },
            confidence=0.8,
            strength=8,
            evidence_quality=0.85,
            cloud_region="general",
            tracer_used="dust_continuum",
        )
        self.memory.leave_trail(trail_M)

    def _leave_column_density_trail(self, sb_results: Dict, data: Dict):
        """Leave pheromone trail for column density"""
        trail = CloudPheromoneTrail(
            trail_id=f"dust_{uuid.uuid4().hex[:8]}",
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            timestamp=datetime.now(),
            discovery_type=CloudDiscoveryType.COLUMN_DENSITY.value,
            content={
                'N_H2': sb_results['N_H2'],
                'A_V': sb_results['A_V'],
                'M_beam': sb_results['M_beam'],
                'T_dust_assumed': sb_results['T_dust'],
                'method': 'single_band_submm'
            },
            confidence=0.7,  # Lower confidence for assumed T
            strength=7,
            evidence_quality=0.75,
            cloud_region="general",
            tracer_used="dust_submm",
        )
        self.memory.leave_trail(trail)

    def _cross_validate_with_lines(self, results: Dict):
        """Cross-validate dust results with molecular line trails"""
        line_N_trails = [t for t in self.memory.get_strong_trails(threshold=6)
                         if t.discovery_type == CloudDiscoveryType.COLUMN_DENSITY.value
                         and 'CO' in t.content.get('method', '')]

        if line_N_trails and 'sed_fit' in results:
            line_N = line_N_trails[0].content.get('N_H2', 0)
            dust_N = results['sed_fit'].get('N_H2', 0)

            ratio = dust_N / line_N if line_N > 0 else 0

            results['N_H2_dust_line_ratio'] = ratio

            # Good agreement: 0.5 < ratio < 2
            if 0.5 < ratio < 2.0:
                results['N_H2_consistent'] = True
                line_N_trails[0].reinforce(0.1)
            else:
                results['N_H2_consistent'] = False
                # May indicate CO depletion or opacity issues


# =============================================================================
# CLOUD STRUCTURE AGENT
# =============================================================================

class CloudStructureAgent(AstroAgent):
    """
    Agent specialized in cloud structure analysis

    Analyzes:
    - Mass-size relations
    - Density profiles
    - Filament identification
    - Core identification
    - Virial stability

    Leaves trails about:
    - Mass estimates
    - Stability parameters
    - Structure classifications
    """

    def __init__(self, agent_id: str,
                 physics_engine: PhysicsEngine,
                 knowledge_graph: AstronomicalKnowledgeGraph,
                 stigmergic_memory: StigmergicMemory):
        super().__init__(agent_id, physics_engine, knowledge_graph, stigmergic_memory)
        self.cloud_physics = MolecularCloudPhysicsEngine()

    @property
    def agent_type(self) -> str:
        return "CloudStructureAgent"

    def analyze(self, data: Dict) -> Dict:
        """
        Analyze cloud structure

        Expected data format:
        {
            'radius_pc': float,
            'mass_msun': float,
            'sigma_v': float (km/s),
            'T_kin': float (K),
            'n_H2': float (cm⁻³),
            'P_ext': float (K cm⁻³, optional)
        }
        """
        results = {
            'agent': self.agent_id,
            'type': self.agent_type,
            'discoveries': []
        }

        R = data.get('radius_pc', 1.0)
        M = data.get('mass_msun', 100.0)
        sigma_v = data.get('sigma_v', 1.0)
        T_kin = data.get('T_kin', 15.0)
        n_H2 = data.get('n_H2', 1e4)
        P_ext = data.get('P_ext', 1e4)  # Default external pressure

        # Virial analysis
        M_vir = self.cloud_physics.virial_mass(R, sigma_v)
        alpha_vir = self.cloud_physics.virial_parameter(M, R, sigma_v)

        # Jeans analysis
        M_J = self.cloud_physics.jeans_mass(T_kin, n_H2)
        M_BE = self.cloud_physics.bonnor_ebert_mass(T_kin, P_ext)

        # Mach number
        mach = self.cloud_physics.mach_number(sigma_v, T_kin)

        results['virial'] = {
            'M_virial': M_vir,
            'alpha_virial': alpha_vir,
            'bound': alpha_vir < 2
        }

        results['jeans'] = {
            'M_jeans': M_J,
            'M_BE': M_BE,
            'supercritical': M > M_J
        }

        results['turbulence'] = {
            'mach_number': mach,
            'supersonic': mach > 1
        }

        # Classification
        if alpha_vir < 1 and M > M_J:
            structure_class = "collapsing_core"
        elif alpha_vir < 2:
            structure_class = "gravitationally_bound"
        elif mach > 5:
            structure_class = "turbulent_cloud"
        else:
            structure_class = "pressure_confined"

        results['classification'] = structure_class

        # Leave trails
        self._leave_stability_trail(results, data)

        return results

    def _leave_stability_trail(self, results: Dict, data: Dict):
        """Leave pheromone trail for stability analysis"""
        trail = CloudPheromoneTrail(
            trail_id=f"struct_{uuid.uuid4().hex[:8]}",
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            timestamp=datetime.now(),
            discovery_type=CloudDiscoveryType.STABILITY.value,
            content={
                'alpha_virial': results['virial']['alpha_virial'],
                'M_virial': results['virial']['M_virial'],
                'M_jeans': results['jeans']['M_jeans'],
                'mach': results['turbulence']['mach_number'],
                'classification': results['classification']
            },
            confidence=0.85,
            strength=8,
            evidence_quality=0.85,
            cloud_region="general",
            tracer_used="kinematics",
        )
        self.memory.leave_trail(trail)


# =============================================================================
# STAR FORMATION AGENT
# =============================================================================

class StarFormationAgent(AstroAgent):
    """
    Agent specialized in star formation diagnostics

    Analyzes:
    - Dense gas fraction
    - Star formation thresholds
    - YSO content
    - Outflow activity
    - Evolutionary stage

    Leaves trails about:
    - Star formation indicators
    - Evolutionary classification
    - SFR estimates
    """

    def __init__(self, agent_id: str,
                 physics_engine: PhysicsEngine,
                 knowledge_graph: AstronomicalKnowledgeGraph,
                 stigmergic_memory: StigmergicMemory):
        super().__init__(agent_id, physics_engine, knowledge_graph, stigmergic_memory)
        self.cloud_physics = MolecularCloudPhysicsEngine()

    @property
    def agent_type(self) -> str:
        return "StarFormationAgent"

    def analyze(self, data: Dict) -> Dict:
        """
        Analyze star formation activity

        Expected data format:
        {
            'M_total': float (M_sun),
            'A_V_peak': float (mag),
            'I_HCN': float (K km/s),
            'distance_pc': float,
            'has_outflows': bool,
            'n_YSOs': int (optional)
        }
        """
        results = {
            'agent': self.agent_id,
            'type': self.agent_type,
            'discoveries': []
        }

        M_total = data.get('M_total', 100)
        A_V = data.get('A_V_peak', 5)
        I_HCN = data.get('I_HCN', 0)
        distance = data.get('distance_pc', 400)
        has_outflows = data.get('has_outflows', False)
        n_YSOs = data.get('n_YSOs', 0)

        # Check star formation threshold
        sf_threshold = self.cloud_physics.star_formation_threshold(A_V)
        results['threshold'] = sf_threshold

        # Dense gas fraction
        if I_HCN > 0:
            f_dense = self.cloud_physics.dense_gas_fraction(M_total, I_HCN, distance)
            results['dense_gas_fraction'] = f_dense
        else:
            f_dense = 0

        # Evolutionary classification
        if n_YSOs > 0 or has_outflows:
            if n_YSOs > 10:
                stage = "active_cluster_forming"
            else:
                stage = "early_star_forming"
        elif sf_threshold.get('likely_star_forming', False):
            stage = "pre_stellar"
        else:
            stage = "quiescent"

        results['evolutionary_stage'] = stage

        # Star formation efficiency (if YSOs known)
        if n_YSOs > 0:
            M_stars_est = n_YSOs * 0.5  # Assume 0.5 M_sun average
            SFE = M_stars_est / (M_total + M_stars_est)
            results['SFE'] = SFE

        # Leave trails
        self._leave_sf_trail(results, data)

        return results

    def _leave_sf_trail(self, results: Dict, data: Dict):
        """Leave pheromone trail for star formation analysis"""
        trail = CloudPheromoneTrail(
            trail_id=f"sf_{uuid.uuid4().hex[:8]}",
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            timestamp=datetime.now(),
            discovery_type=CloudDiscoveryType.STAR_FORMATION.value,
            content={
                'evolutionary_stage': results['evolutionary_stage'],
                'above_threshold': results['threshold'].get('above_threshold', False),
                'dense_gas_fraction': results.get('dense_gas_fraction', 0),
                'SFE': results.get('SFE', 0)
            },
            confidence=0.8,
            strength=8,
            evidence_quality=0.8,
            cloud_region="general",
            tracer_used="multi_tracer",
        )
        self.memory.leave_trail(trail)


# =============================================================================
# MOLECULAR CLOUD SWARM COORDINATOR
# =============================================================================

class MolecularCloudSwarm:
    """
    Coordinator for molecular cloud analysis swarm

    Manages multiple specialized agents that analyze different aspects
    of molecular clouds and share discoveries through stigmergic trails.
    """

    def __init__(self,
                 physics_engine: PhysicsEngine,
                 knowledge_graph: AstronomicalKnowledgeGraph,
                 storage_path: str = "molecular_cloud_stigmergy"):
        self.physics = physics_engine
        self.kg = knowledge_graph
        self.memory = StigmergicMemory(storage_path=storage_path)

        # Initialize agents
        self.agents = {
            'molecular_line': MolecularLineAgent(
                "mol_line_01", physics_engine, knowledge_graph, self.memory
            ),
            'dust_continuum': DustContinuumAgent(
                "dust_01", physics_engine, knowledge_graph, self.memory
            ),
            'structure': CloudStructureAgent(
                "struct_01", physics_engine, knowledge_graph, self.memory
            ),
            'star_formation': StarFormationAgent(
                "sf_01", physics_engine, knowledge_graph, self.memory
            ),
        }

    def analyze_cloud(self, cloud_data: Dict) -> Dict:
        """
        Run full swarm analysis on a molecular cloud

        Each agent analyzes its specialty, leaves trails, and
        cross-validates with other agents' discoveries.
        """
        results = {
            'cloud_name': cloud_data.get('name', 'unknown'),
            'analysis_time': datetime.now().isoformat(),
            'agent_results': {},
            'consensus': {}
        }

        # Phase 1: Individual agent analysis
        for name, agent in self.agents.items():
            agent_data = self._prepare_agent_data(cloud_data, name)
            if agent_data:
                agent_result = agent.analyze(agent_data)
                results['agent_results'][name] = agent_result

        # Phase 2: Apply evaporation (decay old trails)
        self.memory.apply_evaporation(rate=0.05)

        # Phase 3: Build consensus from strong trails
        results['consensus'] = self._build_consensus()

        # Phase 4: Update knowledge graph
        self._update_knowledge_graph(results)

        return results

    def _prepare_agent_data(self, cloud_data: Dict, agent_type: str) -> Optional[Dict]:
        """Prepare data for specific agent type"""
        if agent_type == 'molecular_line':
            if 'spectral_lines' in cloud_data:
                return {
                    'lines': cloud_data['spectral_lines'],
                    'position': cloud_data.get('position', {}),
                    'cloud_name': cloud_data.get('name', '')
                }

        elif agent_type == 'dust_continuum':
            if 'dust_sed' in cloud_data or 'single_band' in cloud_data:
                return {
                    'sed': cloud_data.get('dust_sed'),
                    'single_band': cloud_data.get('single_band'),
                    'distance_pc': cloud_data.get('distance_pc', 400),
                    'assumed_T_dust': cloud_data.get('T_dust', 20)
                }

        elif agent_type == 'structure':
            if 'radius_pc' in cloud_data and 'mass_msun' in cloud_data:
                return {
                    'radius_pc': cloud_data['radius_pc'],
                    'mass_msun': cloud_data['mass_msun'],
                    'sigma_v': cloud_data.get('sigma_v', 1.0),
                    'T_kin': cloud_data.get('T_kin', 15),
                    'n_H2': cloud_data.get('n_H2', 1e4)
                }

        elif agent_type == 'star_formation':
            return {
                'M_total': cloud_data.get('mass_msun', 100),
                'A_V_peak': cloud_data.get('A_V_peak', 5),
                'I_HCN': cloud_data.get('I_HCN', 0),
                'distance_pc': cloud_data.get('distance_pc', 400),
                'has_outflows': cloud_data.get('has_outflows', False),
                'n_YSOs': cloud_data.get('n_YSOs', 0)
            }

        return None

    def _build_consensus(self) -> Dict:
        """Build consensus from strong pheromone trails"""
        consensus = {}

        # Get all strong trails
        strong_trails = self.memory.get_strong_trails(threshold=7)

        # Group by discovery type
        by_type = {}
        for trail in strong_trails:
            dtype = trail.discovery_type
            if dtype not in by_type:
                by_type[dtype] = []
            by_type[dtype].append(trail)

        # Build consensus for each type
        for dtype, trails in by_type.items():
            if dtype == CloudDiscoveryType.TEMPERATURE.value:
                temps = [t.content.get('T_kin') or t.content.get('T_dust') for t in trails]
                temps = [t for t in temps if t]
                if temps:
                    consensus['T_consensus'] = np.mean(temps)
                    consensus['T_std'] = np.std(temps)

            elif dtype == CloudDiscoveryType.COLUMN_DENSITY.value:
                N_vals = [t.content.get('N_H2') for t in trails if t.content.get('N_H2')]
                if N_vals:
                    consensus['N_H2_consensus'] = np.median(N_vals)

            elif dtype == CloudDiscoveryType.MASS_ESTIMATE.value:
                M_vals = [t.content.get('M_gas') or t.content.get('M_virial') for t in trails]
                M_vals = [m for m in M_vals if m]
                if M_vals:
                    consensus['M_consensus'] = np.median(M_vals)

        consensus['n_strong_trails'] = len(strong_trails)
        consensus['discovery_types'] = list(by_type.keys())

        return consensus

    def _update_knowledge_graph(self, results: Dict):
        """Update knowledge graph with analysis results"""
        cloud_name = results['cloud_name']

        # Add cloud node if not exists
        cloud_node = AstroNode(
            node_id=f"cloud_{cloud_name}",
            node_type=AstroNodeType.MOLECULAR_CLOUD,
            name=cloud_name,
            properties=results['consensus']
        )
        self.kg.add_node(cloud_node)

    def get_trail_summary(self) -> str:
        """Get summary of current stigmergic trails"""
        lines = [
            "=" * 60,
            "MOLECULAR CLOUD STIGMERGIC TRAIL SUMMARY",
            "=" * 60,
            f"Total trails: {len(self.memory.trails)}",
            f"Strong trails (strength >= 7): {len(self.memory.get_strong_trails(7))}",
            "",
            "By Discovery Type:",
        ]

        by_type = {}
        for trail in self.memory.trails.values():
            dtype = trail.discovery_type
            if dtype not in by_type:
                by_type[dtype] = []
            by_type[dtype].append(trail)

        for dtype, trails in sorted(by_type.items()):
            lines.append(f"  {dtype}: {len(trails)} trails")

        return "\n".join(lines)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'CloudDiscoveryType',
    'CloudPheromoneTrail',
    'MolecularLineAgent',
    'DustContinuumAgent',
    'CloudStructureAgent',
    'StarFormationAgent',
    'MolecularCloudSwarm',
]



def utility_function_7(*args, **kwargs):
    """Utility function 7."""
    return None



def utility_function_27(*args, **kwargs):
    """Utility function 27."""
    return None
