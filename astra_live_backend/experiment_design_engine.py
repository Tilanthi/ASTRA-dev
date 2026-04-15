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
ASTRA Live — Automated Experiment Design & Proposal Engine
Generates observation proposals to test theoretical predictions.

CRITICAL DISTINCTION: ASTRA proposes, humans execute.
ASTRA cannot point telescopes or collect observations, but it can:
1. Identify what observations are needed to test theories
2. Find gaps in existing data
3. Prioritize observations by scientific impact
4. Generate detailed proposals that astronomers can submit
5. Track proposal status (proposed → accepted → executed → results returned)

This makes ASTRA a "theory proposal engine" that guides real observational programs.
"""
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import json
from datetime import datetime


class ProposalStatus(Enum):
    """Status of observation proposal."""
    DRAFT = "draft"
    PROPOSED = "proposed"
    UNDER_REVIEW = "under_review"
    ACCEPTED = "accepted"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    RESULTS_RETURNED = "results_returned"


@dataclass
class ObservationRequirement:
    """What observations are needed to test a theory."""
    theory_name: str
    parameter_range: Tuple[float, float]  # (min, max)
    parameter_name: str
    object_types: List[str]  # e.g., ["dwarf_galaxies", "low_mass_galaxies"]
    observables: List[str]  # e.g., ["velocity_curve", "surface_brightness"]
    precision_required: float  # e.g., 0.1 for 10% precision
    sample_size_needed: int  # Statistical power calculation
    urgency: str  # "high", "medium", "low"


@dataclass
class DataGap:
    """A gap between existing data and what's needed to test theories."""
    gap_type: str
    theory_names: List[str]  # Which theories need this data?
    missing_range: str  # What parameter/scale/objects?
    existing_coverage: float  # Percentage [0-1]
    priority_impact: float  # How important? [0-1]
    feasibility: float  # How hard to observe? [0-1]
    estimated_cost: str  # e.g., "10 HST orbits", "5 nights Keck"


@dataclass
class ObservationProposal:
    """A complete observation proposal that astronomers can submit."""
    proposal_id: str
    title: str
    abstract: str  # 200-word summary
    theory_being_tested: str  # Which theory does this test?
    scientific_justification: str  # Why is this important?
    target_objects: Dict[str, Any]  # What to observe?
    observational_requirements: Dict[str, Any]
    facility_recommendations: List[str]  # Which telescopes?
    time_requirements: Dict[str, Any]  # Exposure time, timeline
    expected_results: Dict[str, Any]  # What will we learn?
    alternative_approaches: List[str]  # If main proposal rejected
    proposal_status: ProposalStatus
    date_created: str
    date_modified: str


class ExperimentDesignEngine:
    """
    Generates observation proposals to test theoretical predictions.

    Core workflow:
    1. Identify observation requirements from theories
    2. Find gaps in existing data
    3. Prioritize by scientific impact
    4. Generate detailed proposals
    5. Track proposal status
    """

    def __init__(self):
        # Data registry - what data do we have access to?
        self.data_inventory = self._initialize_data_inventory()

        # Theory requirements tracker
        self.theory_requirements = []

        # Data gaps tracker
        self.data_gaps: List[DataGap] = []

        # Proposals
        self.proposals: Dict[str, ObservationProposal] = {}

        # Statistics
        self.proposals_generated = 0
        self.proposals_accepted = 0
        self.proposals_completed = 0

    def _initialize_data_inventory(self) -> Dict[str, Dict]:
        """Initialize inventory of existing astronomical data."""
        return {
            "exoplanets": {
                "objects": {"mass": "0.01-100 M_jup", "radius": "0.1-20 R_earth", "period": "0.1-100 days"},
                "observables": ["mass", "radius", "period", "transit_depth", "radial_velocity"],
                "parameter_ranges": {
                    "mass": (0.01, 100),  # Jupiter masses
                    "period": (0.1, 100),  # days
                    "eccentricity": (0.0, 1.0)
                },
                "coverage": {"low_mass_pclose": 0.9, "hot_jupiters": 0.8, "long_period": 0.6},
                "sources": ["Kepler", "TESS", "radial_velocity"]
            },

            "galaxies": {
                "objects": {"dwarf": "1e8-1e11 M_sun", "spiral": "1e10-1e12 M_sun",
                              "elliptical": "1e11-1e12 M_sun"},
                "observables": ["velocity_curve", "surface_brightness", "metallicity",
                              "star_formation_rate", "morphology", "color"],
                "parameter_ranges": {
                    "acceleration": (1e-12, 1e-8),  # m/s²
                    "mass": (1e8, 1e12),  # Solar masses
                    "radius": (1, 100)  # kpc
                },
                "coverage": {"high_mass": 0.7, "low_mass": 0.3, "dwarf": 0.2},
                "sources": ["SDSS", "Gaia", "Halpha surveys", "rotation_curves"]
            },

            "cosmology": {
                "objects": {"supernovae": "Type Ia", "galaxy_clusters": "0.01-10 redshift"},
                "observables": ["redshift", "luminosity_distance", "peculiar_velocity"],
                "parameter_ranges": {
                    "redshift": (0.01, 10.0),
                    "H0": (50, 100),  # km/s/Mpc
                    "Ω_m": (0.0, 1.0)
                },
                "coverage": {"low_z_sn": 0.9, "high_z_sn": 0.7, "clusters": 0.5},
                "sources": ["Pantheon+", "DES", "HSC"]
            },

            "stellar": {
                "objects": {"main_sequence": "0.1-100 M_sun", "giants": ">10 M_sun"},
                "observables": ["luminosity", "temperature", "metallicity",
                              "mass", "radius", "age"],
                "parameter_ranges": {
                    "mass": (0.1, 100),
                    "temperature": (3000, 10000),  # K
                    "age": (1e6, 1e10)  # years
                },
                "coverage": {"solar_type": 0.9, "massive_stars": 0.4, "low_mass": 0.8},
                "sources": ["Gaia", "Kepler", "spectroscopic surveys"]
            }
        }

    def identify_observation_requirements(self, theories: List[Dict]) -> List[ObservationRequirement]:
        """
        Analyze theories and identify what observations are needed.

        Takes theoretical predictions and determines what data is needed to test them.
        """
        requirements = []

        for theory in theories:
            theory_name = theory.get('name', 'Unknown Theory')

            # Check if theory makes specific parameter range predictions
            if 'parameter_range' in theory:
                param_range = theory['parameter_range']
                requirements.append(ObservationRequirement(
                    theory_name=theory_name,
                    parameter_range=param_range['range'],
                    parameter_name=param_range['parameter'],
                    object_types=param_range.get('objects', []),
                    observables=param_range.get('observables', []),
                    precision_required=param_range.get('precision', 0.1),
                    sample_size_needed=self._calculate_sample_size(param_range.get('effect_size', 0.5)),
                    urgency=param_range.get('urgency', 'medium')
                ))

        return requirements

    def find_data_gaps(self, requirements: List[ObservationRequirement]) -> List[DataGap]:
        """
        Identify gaps between existing data and what's needed to test theories.

        For each requirement, check if we have adequate data coverage.
        """
        gaps = []

        for req in requirements:
            # Check if we have data for the required parameter range
            coverage = self._assess_data_coverage(req)

            if coverage < 0.8:  # Gap exists if < 80% coverage
                # Calculate impact and feasibility
                impact = self._calculate_scientific_impact(req)
                feasibility = self._assess_observation_feasibility(req)

                gaps.append(DataGap(
                    gap_type=f"{req.parameter_name}: {req.parameter_range[0]}-{req.parameter_range[1]}",
                    theory_names=[req.theory_name],
                    missing_range=f"{req.parameter_range[0]:.2e}-{req.parameter_range[1]:.2e}",
                    existing_coverage=coverage,
                    priority_impact=impact,
                    feasibility=feasibility,
                    estimated_cost=self._estimate_observation_cost(req)
                ))

        return gaps

    def _assess_data_coverage(self, req: ObservationRequirement) -> float:
        """Assess if we have adequate data for this requirement."""
        # Look for matching data in inventory
        for domain, inventory in self.data_inventory.items():
            if req.parameter_name in inventory.get('parameter_ranges', {}):
                # Check if our range overlaps with needed range
                our_ranges = inventory['parameter_ranges'].get(req.parameter_name, [])

                if isinstance(our_ranges, dict):
                    # Check if any range covers the requirement
                    # For simplicity, assume 50% coverage if domain matches
                    return 0.5
                elif isinstance(our_ranges, tuple) and len(our_ranges) == 2:
                    our_min, our_max = our_ranges
                    need_min, need_max = req.parameter_range

                    # Calculate overlap
                    overlap = min(our_max, need_max) - max(our_min, need_min)
                    total_range = need_max - need_min

                    if total_range > 0:
                        return overlap / total_range

        # No coverage found
        return 0.0

    def _calculate_sample_size(self, effect_size: float) -> int:
        """Calculate required sample size for statistical power."""
        # Simplified power calculation
        alpha = 0.05  # Significance level
        beta = 0.8    # Power (1 - Type II error rate)

        # Cohen's h approximation
        n = 16 / (effect_size**2)

        # Minimum sample size
        return max(20, int(n * 2))  # At least 20, doubled for safety

    def _calculate_scientific_impact(self, req: ObservationRequirement) -> float:
        """Calculate scientific impact of filling this gap."""
        impact = 0.5  # Base impact

        # Higher impact if multiple theories need this
        # (This would be tracked globally)
        impact += 0.2 if req.urgency == "high" else 0.0

        # Higher impact for novel parameter ranges
        if "acceleration" in req.parameter_name.lower():
            impact += 0.2  # Acceleration studies are hot topic

        # Higher impact for extreme regimes
        if req.parameter_range[0] < req.parameter_range[1] * 0.01:
            impact += 0.1  # Very low range

        return min(1.0, impact)

    def _assess_observation_feasibility(self, req: ObservationRequirement) -> float:
        """Assess how feasible this observation is [0-1]."""
        feasibility = 0.7  # Base feasibility

        # Adjust for object types
        for obj_type in req.object_types:
            if "dwarf" in obj_type.lower():
                feasibility -= 0.2  # Faint objects are hard
            if "low_mass" in obj_type.lower():
                feasibility -= 0.1
            if "high_z" in obj_type.lower():
                feasibility -= 0.3  # High redshift is hard

        # Adjust for required precision
        if req.precision_required < 0.05:  # Need 5% precision
            feasibility -= 0.2  # High precision is hard

        return max(0.1, feasibility)

    def _estimate_observation_cost(self, req: ObservationRequirement) -> str:
        """Estimate the cost of this observation."""
        # Very rough estimation
        cost_components = []

        if "dwarf" in " ".join(req.object_types).lower():
            if req.precision_required < 0.1:
                cost_components.append("10 hours Keck time")
            else:
                cost_components.append("20 hours Keck time")

        if "galaxy" in " ".join(req.object_types).lower():
            if req.sample_size_needed > 100:
                cost_components.append("Survey time: 50 hours")

        if cost_components:
            return " + ".join(cost_components)
        else:
            return "Standard observation"

    def prioritize_observations(self, gaps: List[DataGap]) -> List[Dict]:
        """
        Prioritize which observations to do first.

        Sorts by scientific impact and feasibility.
        """
        prioritized = []

        for gap in gaps:
            # Score = impact × feasibility
            score = gap.priority_impact * gap.feasibility

            prioritized.append({
                'gap_type': gap.gap_type,
                'theories_affected': gap.theory_names,
                'priority_score': score,
                'impact': gap.priority_impact,
                'feasibility': gap.feasibility,
                'estimated_cost': gap.estimated_cost,
                'existing_coverage': gap.existing_coverage
            })

        # Sort by priority score (descending)
        prioritized.sort(key=lambda x: x['priority_score'], reverse=True)

        return prioritized

    def generate_proposal(self, gap: DataGap, proposal_id: str = None) -> ObservationProposal:
        """
        Generate a detailed observation proposal that astronomers can submit.

        This is the output that goes to real telescopes/proposal systems.
        """
        if proposal_id is None:
            proposal_id = f"PROP-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        # Parse gap type to understand what's needed
        gap_info = self._parse_gap_type(gap.gap_type)

        # Generate title
        title = self._generate_proposal_title(gap, gap_info)

        # Generate abstract
        abstract = self._generate_abstract(gap, gap_info)

        # Determine facility recommendations
        facilities = self._recommend_facilities(gap, gap_info)

        # Generate time requirements
        time_reqs = self._generate_time_requirements(gap, gap_info)

        # Expected results
        expected = self._generate_expected_results(gap, gap_info)

        # Scientific justification
        justification = self._generate_scientific_justification(gap, gap_info)

        # Alternative approaches if main proposal rejected
        alternatives = self._generate_alternatives(gap, gap_info)

        return ObservationProposal(
            proposal_id=proposal_id,
            title=title,
            abstract=abstract,
            theory_being_tested=", ".join(gap.theory_names),
            scientific_justification=justification,
            target_objects={
                'object_types': gap_info.get('object_types', []),
                'parameter_range': gap_info.get('range_str'),
                'sample_size': gap_info.get('sample_size', 50)
            },
            observational_requirements={
                'observables': gap_info.get('observables', []),
                'precision': gap_info.get('precision', 0.1),
                'time_baseline': gap_info.get('time_baseline', 'single epoch')
            },
            facility_recommendations=facilities,
            time_requirements=time_reqs,
            expected_results=expected,
            alternative_approaches=alternatives,
            proposal_status=ProposalStatus.DRAFT,
            date_created=datetime.now().isoformat(),
            date_modified=datetime.now().isoformat()
        )

    def _parse_gap_type(self, gap_type: str) -> Dict:
        """Parse gap type string into structured information."""
        # Parse: "acceleration: 1e-12 - 1e-8"
        # or: "mass: 1e8 - 1e12"

        parts = gap_type.split(":")
        param_name = parts[0].strip()

        if "-" in parts[1]:
            range_parts = parts[1].split("-")
            range_min = float(range_parts[0].strip())
            range_max = float(range_parts[1].strip())
        else:
            range_min, range_max = 0, 1

        return {
            'parameter': param_name,
            'range_min': range_min,
            'range_max': range_max,
            'range_str': f"{range_min:.2e} - {range_max:.2e}",
            'object_types': self._infer_object_types(param_name, range_min, range_max)
        }

    def _infer_object_types(self, param_name: str, range_min: float, range_max: float) -> List[str]:
        """Infer what astronomical objects would have this parameter range."""
        if param_name == "acceleration":
            if range_max < 1e-10:
                return ["dwarf_galaxies", "low_surface_brightness_galaxies"]
            elif range_min > 1e-6:
                return ["stars", "stellar_clusters"]

        elif param_name == "mass":
            if range_max < 1.0:
                return ["brown_dwarfs", "planets"]
            elif range_max < 10:
                return ["low_mass_stars"]
            elif range_max < 100:
                return ["solar_mass_stars"]
            else:
                return ["massive_stars"]

        return ["astrophysical_objects"]

    def _generate_proposal_title(self, gap: DataGap, gap_info: Dict) -> str:
        """Generate title for observation proposal."""
        param = gap_info['parameter']
        range_str = gap_info['range_str']

        theories = ", ".join([t.split()[0] for t in gap.theory_names])

        return f"Observational Test of {theories} via {param} in Range [{range_str}]"

    def _generate_abstract(self, gap: DataGap, gap_info: Dict) -> str:
        """Generate abstract for proposal."""
        theories = ", ".join(gap.theory_names)
        param = gap_info['parameter']
        range_str = gap_info['range_str']

        abstract = f"We propose observational tests of {theories} predictions for {param} "
        abstract += f"in the range {range_str}. Current data coverage in this regime is "
        abstract += f"only {gap.existing_coverage:.0%}, leaving theoretical predictions "
        abstract += f"untested. We will observe {gap_info.get('object_types', ['objects'])[0]} "
        abstract += f"to provide the necessary data. This will fill a critical gap in our "
        abstract += f"observational coverage and test fundamental theoretical predictions."

        return abstract[:500]  # Limit to 500 chars

    def _recommend_facilities(self, gap: DataGap, gap_info: Dict) -> List[str]:
        """Recommend appropriate telescopes/facilities."""
        facilities = []

        param = gap_info['parameter']
        range_min = gap_info['range_min']
        range_max = gap_info['range_max']
        objects = gap_info.get('object_types', [])

        # Low acceleration → need sensitive velocity measurements
        if param == "acceleration" and range_max < 1e-10:
            facilities.append("Keck Observatory (HIRESpec for low accelerations)")
            facilities.append("Very Large Array (radio interferometry for gas kinematics)")

        # Dwarf galaxies → need deep imaging
        if "dwarf" in " ".join(objects).lower():
            facilities.append("Hubble Space Telescope (deep imaging)")
            facilities.append("James Webb Space Telescope (if nearby)")
            facilities.append("VLT MUSE (IFU spectroscopy)")

        # High precision → need spectroscopy
        if gap_info.get('precision', 0.1) < 0.05:
            facilities.append("High-resolution spectrographs (Keck/DEIMOS, VLT)")

        return facilities

    def _generate_time_requirements(self, gap: DataGap, gap_info: Dict) -> Dict:
        """Generate time requirements for observation."""
        return {
            'exposure_time_per_object': '2 hours' if gap.feasibility > 0.5 else '10 hours',
            'sample_size': gap_info.get('sample_size', 50),
            'timeline': 'Single 6-month observing run or spread over 2 semesters',
            'urgency': gap.urgency if hasattr(gap, 'urgency') else 'medium'
        }

    def _generate_expected_results(self, gap: DataGap, gap_info: Dict) -> Dict:
        """Generate expected results from this observation."""
        return {
            'outcomes': [
                f"Validate/invalidate {', '.join(gap.theory_names)}",
                f"Fill data gap in {gap_info['parameter']} range"
            ],
            'data_products': [
                f"Catalog of {gap_info.get('sample_size', 50)} objects with "
                f"{gap_info['parameter']} measurements"
            ],
            'scientific_impact': f"Confidence in theories will increase from "
                                f"{1.0 - gap.existing_coverage:.1%} to >95%"
        }

    def _generate_scientific_justification(self, gap: DataGap, gap_info: Dict) -> str:
        """Generate scientific justification for proposal."""
        theories = ", ".join(gap.theory_names)
        gap_pct = (1.0 - gap.existing_coverage) * 100

        justification = f"Testing {theories} predictions is critical for "
        justification += f"understanding fundamental physics. Currently we lack "
        justification += f"observational data in the {gap_info['range_str']} regime "
        justification += f"({gap_pct:.0f}% gap). This observation would fill that gap "
        justification += f"and provide the first test of these theoretical predictions "
        justification += f"in this regime. The scientific impact is high: it would "
        justification += f"either validate revolutionary new physics or place "
        justification += f"strong constraints on existing theories."

        return justification

    def _generate_alternatives(self, gap: DataGap, gap_info: Dict) -> List[str]:
        """Generate alternative approaches if main proposal is rejected."""
        alternatives = []

        param = gap_info['parameter']

        alternatives.append(
            f"If {param} observations are infeasible, consider archival data "
            f"reanalysis to search for rare objects in the {gap_info['range_str']} regime"
        )

        alternatives.append(
            f"If observations too expensive, conduct theoretical sensitivity "
            f"analysis to determine if upcoming facilities (e.g., ELT, Roman) will "
            f"enable this test within 5 years"
        )

        alternatives.append(
            f"Consider lab/simulation analogues that can provide "
            f"preliminary validation before committing to telescope time"
        )

        return alternatives

    def batch_generate_proposals(self, n_proposals: int = 10) -> List[ObservationProposal]:
        """
        Generate multiple observation proposals for prioritized gaps.

        This is the main entry point for generating observation proposals.
        """
        proposals = []

        # Get current data gaps
        if not self.data_gaps:
            # Need to identify gaps first
            # For now, create example gaps
            self.data_gaps = [
                DataGap(
                    gap_type="acceleration: 1e-12 - 1e-10",
                    theory_names=["Entropic Gravity", "MOND"],
                    missing_range="1e-12 - 1e-10 m/s²",
                    existing_coverage=0.1,
                    priority_impact=0.9,
                    feasibility=0.5,
                    estimated_cost="20 hours Keck time"
                ),
                DataGap(
                    gap_type="mass: 0.5 - 2.0",
                    theory_names=["Initial Mass Function"],
                    missing_range="0.5 - 2.0 M_sun",
                    existing_coverage=0.3,
                    priority_impact=0.7,
                    feasibility=0.8,
                    estimated_cost="Standard star formation survey"
                ),
                DataGap(
                    gap_type="redshift: 8 - 12",
                    theory_names=["Hubble Tension variant"],
                    missing_range="z = 8 - 12 (cosmic noon)",
                    existing_coverage=0.4,
                    priority_impact=0.95,
                    feasibility=0.3,
                    estimated_cost="1000 hours telescope time"
                )
            ]

        # Prioritize gaps
        prioritized = self.prioritize_observations(self.data_gaps)

        # Generate proposals for top N gaps
        for i, gap_info in enumerate(prioritized[:n_proposals]):
            proposal = self.generate_proposal(self.data_gaps[self.data_gaps.index(gap_info)])

            # Update status
            proposal.proposal_status = ProposalStatus.PROPOSED

            proposals.append(proposal)

        self.proposals_generated = len(proposals)
        return proposals

    def track_proposal_status(self, proposal_id: str, new_status: ProposalStatus,
                           results: Optional[Dict] = None) -> bool:
        """
        Track the status of a proposal as it moves through the proposal pipeline.

        This would be called by astronomers as they review/accept/execute proposals.
        """
        if proposal_id not in self.proposals:
            return False

        proposal = self.proposals[proposal_id]
        proposal.proposal_status = new_status
        proposal.date_modified = datetime.now().isoformat()

        if results:
            # Update theory confidences based on results
            self._update_theories_based_on_results(proposal, results)

        if new_status == ProposalStatus.COMPLETED:
            self.proposals_completed += 1

        return True

    def _update_theories_based_on_results(self, proposal: ObservationProposal,
                                           results: Dict):
        """
        Update theoretical confidences based on returned observation results.
        """
        theory_names = proposal.theory_being_tested.split(", ")

        for theory_name in theory_names:
            # Look up the theory and update its confidence
            # This would connect to the theory evolution tracking
            pass

    def generate_proposal_summary(self, proposal_id: str) -> Optional[Dict]:
        """Get a summary of a proposal for review."""
        if proposal_id not in self.proposals:
            return None

        proposal = self.proposals[proposal_id]

        return {
            'proposal_id': proposal.proposal_id,
            'title': proposal.title,
            'abstract': proposal.abstract,
            'status': proposal.proposal_status.value,
            'theories_tested': proposal.theory_being_tested,
            'facilities': proposal.facility_recommendations,
            'time_estimate': proposal.time_requirements.get('timeline'),
            'scientific_impact': proposal.expected_results.get('scientific_impact', ''),
            'created_date': proposal.date_created
        }

    def get_proposal_statistics(self) -> Dict:
        """Get statistics on generated proposals."""
        statuses = [p.proposal_status.value for p in self.proposals.values()]

        return {
            'total_proposals': len(self.proposals),
            'by_status': {status: statuses.count(status) for status in ProposalStatus},
            'acceptance_rate': (self.proposals_accepted /
                                 len(self.proposals) if self.proposals else 1),
            'completion_rate': (self.proposals_completed /
                                len(self.proposals) if self.proposals else 1)
        }


# Demonstration
if __name__ == "__main__":
    print("=" * 80)
    print("AUTOMATED EXPERIMENT DESIGN & PROPOSAL ENGINE")
    print("=" * 80)

    engine = ExperimentDesignEngine()

    print("\n1. IDENTIFY DATA GAPS")
    print("-" * 80)

    # Example: Analyze theoretical requirements
    theory_requirements = [
        {
            'name': 'Entropic Gravity Low Acceleration Test',
            'parameter_range': {
                'range': (1e-12, 1e-10),
                'parameter': 'acceleration',
                'objects': ['dwarf_galaxies'],
                'precision': 0.05,
                'urgency': 'high'
            }
        },
        {
            'name': 'Initial Mass Function Low Mass',
            'parameter_range': {
                'range': (0.5, 2.0),
                'parameter': 'mass',
                'objects': ['young_stars', 'protostars'],
                'precision': 0.1,
                'urgency': 'medium'
            }
        }
    ]

    requirements = engine.identify_observation_requirements(theory_requirements)

    for req in requirements:
        print(f"\nRequirement: {req.theory_name}")
        print(f"  Parameter: {req.parameter_name} ∈ [{req.parameter_range[0]:.2e}, {req.parameter_range[1]:.2e}]")
        print(f"  Objects: {', '.join(req.object_types)}")
        print(f"  Precision needed: {req.precision_required*100:.0f}%")
        print(f"  Sample size: {req.sample_size_needed}")

    print(f"\nTotal requirements identified: {len(requirements)}")

    # Find data gaps
    print("\n2. FIND DATA GAPS")
    print("-" * 80)

    gaps = engine.find_data_gaps(requirements)

    for gap in gaps:
        print(f"\nGap: {gap.gap_type}")
        print(f"  Theories affected: {', '.join(gap.theory_names)}")
        print(f"  Missing range: {gap.missing_range}")
        print(f"  Current coverage: {gap.existing_coverage*100:.0f}%")
        print(f"  Priority: {gap.priority_impact:.2f} (impact) × {gap.feasibility:.2f} (feasibility)")
        print(f"  Estimated cost: {gap.estimated_cost}")

    print(f"\nTotal gaps found: {len(gaps)}")

    # Prioritize observations
    print("\n3. PRIORITIZE OBSERVATIONS")
    print("-" * 80)

    prioritized = engine.prioritize_observations(gaps)

    print(f"Priority ranking (by scientific impact × feasibility):")
    for i, item in enumerate(prioritized[:5], 1):
        print(f"  {i}. {item['gap_type']}")
        print(f"     Priority score: {item['priority_score']:.3f}")
        print(f"     Impact: {item['impact']:.2f}, Feasibility: {item['feasibility']:.2f}")
        print(f"     Cost: {item['estimated_cost']}")

    # Generate proposals
    print("\n4. GENERATE PROPOSALS")
    print("-" * 80)

    proposals = engine.batch_generate_proposals(n_proposals=3)

    print(f"Generated {len(proposals)} observation proposals:")

    for proposal in proposals:
        print(f"\nProposal ID: {proposal.proposal_id}")
        print(f"Status: {proposal.proposal_status.value}")
        print(f"Title: {proposal.title}")
        print(f"Facilities: {', '.join(proposal.facility_recommendations[:3])}")
        print(f"Timeline: {proposal.time_requirements.get('timeline')}")
        print(f"Abstract: {proposal.abstract[:200]}...")

    # Get statistics
    print("\n5. PROPOSAL STATISTICS")
    print("-" * 80)

    stats = engine.get_proposal_statistics()
    print(f"Total proposals: {stats['total_proposals']}")
    print(f"By status: {stats['by_status']}")
    print(f"Acceptance rate: {stats['acceptance_rate']:.1%}")
    print(f"Completion rate: {stats['completion_rate']:.1%}")

    print("\n" + "=" * 80)
    print("EXPERIMENT DESIGN ENGINE is operational!")
    print("Note: ASTRA PROPOSES, humans EXECUTE")
    print("=" * 80)
