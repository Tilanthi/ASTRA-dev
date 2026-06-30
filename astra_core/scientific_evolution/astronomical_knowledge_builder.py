"""
ASTRA Astronomical Knowledge Builder
====================================

Phase 1.4: Domain knowledge system for building astrophysical expertise.

This module helps ASTRA develop astronomical domain knowledge during idle moments,
building the foundation for becoming an autonomous astrophysical scientist.

Key Capabilities:
- Stellar astrophysics knowledge base
- Galactic astronomy fundamentals
- Cosmological principles
- Observational astronomy capabilities
- Instrument limitations and feasibility
- Literature integration and context

Date: 2025-06-29
Phase: 1.4 - Astronomical Knowledge Foundation
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path


class Astronomical_Domain(Enum):
    """Major astronomical domains for knowledge building"""
    STELLAR_ASTROPHYSICS = "stellar"
    GALACTIC_ASTRONOMY = "galactic"
    COSMOLOGY = "cosmology"
    EXOPLANETS = "exoplanets"
    ISM_PHYSICS = "ism"
    HIGH_ENERGY_ASTROPHYSICS = "high_energy"
    OBSERVATIONAL_ASTRONOMY = "observational"
    THEORETICAL_ASTROPHYSICS = "theoretical"


class Knowledge_Component(Enum):
    """Types of astronomical knowledge components"""
    PHYSICAL_PRINCIPLES = "principles"
    CHARACTERISTIC_SCALES = "scales"
    OBSERVATIONAL_METHODS = "methods"
    KEY_OBJECTS = "objects"
    FUNDAMENTAL_RELATIONS = "relations"
    COMMON_MISCONCEPTIONS = "misconceptions"


@dataclass
class Astronomical_Knowledge_Item:
    """A single piece of astronomical knowledge"""
    domain: Astronomical_Domain
    component: Knowledge_Component
    topic: str
    knowledge: str
    quantitative_relation: Optional[str] = None
    observational_signature: Optional[str] = None
    common_errors: Optional[List[str]] = None
    reference: str = ""


@dataclass
class Knowledge_Assessment:
    """Assessment of current astronomical knowledge"""
    domain: Astronomical_Domain
    knowledge_level: float  # 0.0 to 1.0
    known_topics: List[str]
    unknown_topics: List[str]
    misconceptions: List[str]
    recommended_study: List[str]


class Astronomical_Knowledge_Base:
    """
    Knowledge base of fundamental astronomical concepts and principles.

    This class contains the core astronomical knowledge that ASTRA should
    master to become an autonomous astrophysical scientist.
    """

    def __init__(self):
        self.knowledge_items = self._initialize_knowledge_base()

    def _initialize_knowledge_base(self) -> Dict[Astronomical_Domain, List[Astronomical_Knowledge_Item]]:
        """Initialize the astronomical knowledge base"""
        knowledge = {}

        # Stellar Astrophysics
        knowledge[Astronomical_Domain.STELLAR_ASTROPHYSICS] = [
            Astronomical_Knowledge_Item(
                domain=Astronomical_Domain.STELLAR_ASTROPHYSICS,
                component=Knowledge_Component.CHARACTERISTIC_SCALES,
                topic="HR Diagram Temperature Range",
                knowledge="Main sequence stars span surface temperatures from ~3,000 K (M dwarfs) to ~40,000 K (O stars)",
                quantitative_relation="T_eff range: 3,000-40,000 K",
                observational_signature="Spectral types O B A F G K M with distinct absorption lines",
                common_errors=["Assuming all stars have solar temperatures", "Ignoring spectral classification"]
            ),
            Astronomical_Knowledge_Item(
                domain=Astronomical_Domain.STELLAR_ASTROPHYSICS,
                component=Knowledge_Component.PHYSICAL_PRINCIPLES,
                topic="Stellar Mass Limits",
                knowledge="Stable stars exist between 0.08-150 solar masses. Below 0.08 M_sun: insufficient for hydrogen fusion. Above 150 M_sun: radiation pressure prevents stability.",
                quantitative_relation="M_stable: 0.08-150 M_sun",
                observational_signature="Brown dwarfs below 0.08 M_sun, Eddington-limited massive stars",
                common_errors=["Assuming any mass can form a star", "Ignoring radiation pressure effects"]
            ),
            Astronomical_Knowledge_Item(
                domain=Astronomical_Domain.STELLAR_ASTROPHYSICS,
                component=Knowledge_Component.FUNDAMENTAL_RELATIONS,
                topic="Mass-Luminosity Relation",
                knowledge="Main sequence luminosity scales strongly with mass: L ∝ M^3.5 for solar-type stars",
                quantitative_relation="L/L_sun ≈ (M/M_sun)^3.5",
                observational_signature="More massive stars are much brighter and shorter-lived",
                common_errors=["Assuming linear mass-luminosity relation", "Ignoring spectral type dependencies"]
            ),
            Astronomical_Knowledge_Item(
                domain=Astronomical_Domain.STELLAR_ASTROPHYSICS,
                component=Knowledge_Component.OBSERVATIONAL_METHODS,
                topic="Stellar Parameter Determination",
                knowledge="Stellar parameters determined from photometry (colors, magnitudes) and spectroscopy (absorption lines, radial velocities)",
                quantitative_relation="T_eff from colors, log(g) from line widths, [Fe/H] from line strengths",
                observational_signature="Multi-wavelength observations needed for full characterization",
                common_errors=["Relying on single-band photometry", "Ignoring interstellar reddening effects"]
            )
        ]

        # Galactic Astronomy
        knowledge[Astronomical_Domain.GALACTIC_ASTRONOMY] = [
            Astronomical_Knowledge_Item(
                domain=Astronomical_Domain.GALACTIC_ASTRONOMY,
                component=Knowledge_Component.CHARACTERISTIC_SCALES,
                topic="Galaxy Size Range",
                knowledge="Galaxies span from dwarf galaxies (10^6 M_sun) to massive clusters (10^15 M_sun)",
                quantitative_relation="M_galaxies: 10^6-10^15 M_sun",
                observational_signature="Dwarf galaxies are faint and metal-poor, massive galaxies are bright and structured",
                common_errors=["Assuming all galaxies are Milky Way-like", "Ignoring dwarf galaxy population"]
            ),
            Astronomical_Knowledge_Item(
                domain=Astronomical_Domain.GALACTIC_ASTRONOMY,
                component=Knowledge_Component.PHYSICAL_PRINCIPLES,
                topic="Star Formation Thresholds",
                knowledge="Star formation requires gas density/temperature criteria: Jeans mass and Toomre stability",
                quantitative_relation="ρ_crit ~ 100-10,000 M_sun/pc^3, Q_toomre > 1 for stability",
                observational_signature="Star formation occurs in dense, cold molecular clouds",
                common_errors=["Assuming star formation happens anywhere there's gas", "Ignoring stability criteria"]
            )
        ]

        # Cosmology
        knowledge[Astronomical_Domain.COSMOLOGY] = [
            Astronomical_Knowledge_Item(
                domain=Astronomical_Domain.COSMOLOGY,
                component=Knowledge_Component.CHARACTERISTIC_SCALES,
                topic="Cosmological Timescales",
                knowledge="Age of universe 13.8 Gyr sets maximum timescale for any astrophysical process",
                quantitative_relation="t_universe = 13.8 Gyr (ΛCDM)",
                observational_signature="No stellar populations or structures can be older than universe",
                common_errors=["Finding objects older than universe", "Ignoring cosmological constraints"]
            ),
            Astronomical_Knowledge_Item(
                domain=Astronomical_Domain.COSMOLOGY,
                component=Knowledge_Component.FUNDAMENTAL_RELATIONS,
                topic="Hubble Law",
                knowledge="Galaxy recession velocity proportional to distance: v = H_0 × d",
                quantitative_relation="v = H_0 × d, H_0 ≈ 70 km/s/Mpc",
                observational_signature="Redshift increases with distance for cosmological objects",
                common_errors=["Applying Hubble law to nearby galaxies", "Confusing redshift with velocity"]
            )
        ]

        # Observational Astronomy
        knowledge[Astronomical_Domain.OBSERVATIONAL_ASTRONOMY] = [
            Astronomical_Knowledge_Item(
                domain=Astronomical_Domain.OBSERVATIONAL_ASTRONOMY,
                component=Knowledge_Component.CHARACTERISTIC_SCALES,
                topic="Telescope Sensitivity Limits",
                knowledge="Modern telescopes can detect fluxes from 10^-19 to 10^-12 erg/s/cm^2/Hz",
                quantitative_relation="F_min: 10^-19-10^-12 erg/s/cm^2/Hz",
                observational_signature="Deeper observations require longer exposure times or larger apertures",
                common_errors=["Assuming infinite sensitivity", "Ignoring background and confusion limits"]
            ),
            Astronomical_Knowledge_Item(
                domain=Astronomical_Domain.OBSERVATIONAL_ASTRONOMY,
                component=Knowledge_Component.PHYSICAL_PRINCIPLES,
                topic="Angular Resolution Limit",
                knowledge="Diffraction limit: θ = 1.22 λ/D determines maximum angular resolution",
                quantitative_relation="θ_min = 1.22 λ/D (radians)",
                observational_signature="Larger telescopes and shorter wavelengths give better resolution",
                common_errors=["Ignoring diffraction limit", "Assuming perfect resolution possible"]
            ),
            Astronomical_Knowledge_Item(
                domain=Astronomical_Domain.OBSERVATIONAL_ASTRONOMY,
                component=Knowledge_Component.KEY_OBJECTS,
                topic="Major Astronomical Facilities",
                knowledge="Current facilities: JWST (infrared), Gaia (astrometry), ALMA (mm), SDSS (optical spectroscopy), DESI (spectroscopic survey)",
                quantitative_relation="Wavelength coverage: radio (m) to gamma-ray (<pm)",
                observational_signature="Each facility optimized for specific wavelength range and science",
                common_errors=["Assuming one telescope can observe everything", "Ignoring wavelength limitations"]
            )
        ]

        return knowledge


class Astronomical_Knowledge_Learner:
    """
    System for ASTRA to learn and build astronomical knowledge.

    This helps ASTRA develop domain expertise systematically during idle moments,
    which is essential for becoming an autonomous astrophysical scientist.
    """

    def __init__(self):
        self.knowledge_base = Astronomical_Knowledge_Base()
        self.learned_topics = set()
        self.learning_progress = {}

    def assess_knowledge(self, domain: Astronomical_Domain) -> Knowledge_Assessment:
        """Assess current knowledge level in a specific astronomical domain"""
        domain_knowledge = self.knowledge_base.knowledge_items.get(domain, [])

        known_topics = [item.topic for item in domain_knowledge if item.topic in self.learned_topics]
        unknown_topics = [item.topic for item in domain_knowledge if item.topic not in self.learned_topics]

        # Calculate knowledge level
        if len(domain_knowledge) > 0:
            knowledge_level = len(known_topics) / len(domain_knowledge)
        else:
            knowledge_level = 0.0

        # Identify misconceptions (this would be filled in during learning)
        misconceptions = []

        # Recommend study topics
        recommended_study = unknown_topics[:3] if unknown_topics else []

        return Knowledge_Assessment(
            domain=domain,
            knowledge_level=knowledge_level,
            known_topics=known_topics,
            unknown_topics=unknown_topics,
            misconceptions=misconceptions,
            recommended_study=recommended_study
        )

    def learn_topic(self, domain: Astronomical_Domain, topic: str) -> Astronomical_Knowledge_Item:
        """Learn about a specific astronomical topic"""
        domain_knowledge = self.knowledge_base.knowledge_items.get(domain, [])

        # Find the knowledge item
        knowledge_item = None
        for item in domain_knowledge:
            if item.topic == topic:
                knowledge_item = item
                break

        if knowledge_item:
            # Mark as learned
            self.learned_topics.add(topic)
            self.learning_progress[topic] = {
                'domain': domain.value,
                'learned': True,
                'timestamp': '2025-06-29'  # In practice, would use actual timestamp
            }

            return knowledge_item

        return None

    def get_study_plan(self) -> Dict[str, List[str]]:
        """Get a study plan across all astronomical domains"""
        study_plan = {}

        for domain in Astronomical_Domain:
            assessment = self.assess_knowledge(domain)
            if assessment.recommended_study:
                study_plan[domain.value] = assessment.recommended_study

        return study_plan

    def practice_knowledge_application(self, domain: Astronomical_Domain) -> List[str]:
        """Generate practice scenarios for applying astronomical knowledge"""
        practice_scenarios = {
            Astronomical_Domain.STELLAR_ASTROPHYSICS: [
                "A star with 50 M_sun is discovered - what are its properties and lifetime?",
                "An object has T_eff = 2,500 K - what spectral type and main sequence status?",
                "A claim describes a 200 M_sun star - evaluate this claim"
            ],
            Astronomical_Domain.GALACTIC_ASTRONOMY: [
                "A paper claims star formation at 1 K gas temperature - evaluate plausibility",
                "A dwarf galaxy with 10^5 M_sun is studied - what are expected properties?",
                "Star formation threshold of 10^3 M_sun/pc^3 is claimed - assess feasibility"
            ],
            Astronomical_Domain.OBSERVATIONAL_ASTRONOMY: [
                "A telescope claims 0.001 arcsec resolution at optical wavelengths - what diameter is required?",
                "Detection of 10^-20 erg/s/cm^2 flux is claimed - evaluate feasibility with current instruments",
                "An observation claims to detect exoplanets at 100 kpc distance - assess observational feasibility"
            ]
        }

        return practice_scenarios.get(domain, ["No practice scenarios available for this domain"])


class Idle_Moment_Learning:
    """
    System for structured astronomical learning during idle moments.

    This provides the framework for ASTRA to use idle time productively for
    building astronomical domain knowledge.
    """

    def __init__(self):
        self.learner = Astronomical_Knowledge_Learner()
        self.learning_queue = []
        self.session_goals = {}

    def plan_learning_session(self, time_available: int = 5) -> List[str]:
        """Plan what to learn during an idle moment"""
        # Get current knowledge gaps
        study_plan = self.learner.get_study_plan()

        # Prioritize topics based on importance and time available
        priorities = {
            'stellar': 1,  # Highest priority - fundamental domain
            'observational': 2,  # Critical for validating discoveries
            'galactic': 3,  # Important domain
            'cosmology': 4,  # Important but more specialized
            'exoplanets': 5,  # Specialized domain
            'ism': 6,  # Specialized domain
            'high_energy': 7,  # Specialized domain
            'theoretical': 8  # Important but can be learned later
        }

        # Generate learning queue
        learning_tasks = []
        for domain_value, topics in study_plan.items():
            priority = priorities.get(domain_value, 9)
            for topic in topics:
                learning_tasks.append({
                    'domain': domain_value,
                    'topic': topic,
                    'priority': priority,
                    'estimated_time': 2  # 2 minutes per topic
                })

        # Sort by priority
        learning_tasks.sort(key=lambda x: x['priority'])

        # Select tasks for available time
        selected_tasks = []
        total_time = 0
        for task in learning_tasks:
            if total_time + task['estimated_time'] <= time_available:
                selected_tasks.append(f"{task['domain']}: {task['topic']}")
                total_time += task['estimated_time']
            else:
                break

        return selected_tasks if selected_tasks else ["No specific learning tasks - review fundamentals"]

    def execute_learning_session(self, tasks: List[str]) -> Dict[str, Any]:
        """Execute a learning session during idle moments"""
        learning_results = {}

        for task in tasks:
            # Parse task
            if ':' in task:
                domain_value, topic = task.split(':', 1)
                domain = Astronomical_Domain(domain_value)

                # Learn the topic
                knowledge_item = self.learner.learn_topic(domain, topic.strip())

                if knowledge_item:
                    learning_results[task] = {
                        'learned': True,
                        'knowledge': knowledge_item.knowledge,
                        'quantitative': knowledge_item.quantitative_relation,
                        'common_errors': knowledge_item.common_errors
                    }

        return learning_results

    def generate_progress_report(self) -> Dict[str, Any]:
        """Generate a progress report on astronomical knowledge development"""
        progress = {
            'total_topics_learned': len(self.learner.learned_topics),
            'domain_progress': {},
            'recommended_next_steps': []
        }

        for domain in Astronomical_Domain:
            assessment = self.learner.assess_knowledge(domain)
            progress['domain_progress'][domain.value] = {
                'knowledge_level': assessment.knowledge_level,
                'known': len(assessment.known_topics),
                'unknown': len(assessment.unknown_topics),
                'recommended_study': assessment.recommended_study
            }

        # Generate overall recommendations
        study_plan = self.learner.get_study_plan()
        for domain_value, topics in study_plan.items():
            if topics:
                progress['recommended_next_steps'].append(f"{domain_value}: {topics[0]}")

        return progress


# Convenience functions for idle moment learning
def get_astronomical_knowledge(domain: Astronomical_Domain, topic: str) -> Astronomical_Knowledge_Item:
    """Get specific astronomical knowledge"""
    learner = Astronomical_Knowledge_Learner()
    return learner.learn_topic(domain, topic)


def plan_idle_learning(time_available: int = 5) -> List[str]:
    """Plan astronomical learning for idle moments"""
    learning_system = Idle_Moment_Learning()
    return learning_system.plan_learning_session(time_available)


if __name__ == "__main__":
    # Example usage - astronomical knowledge building
    print("ASTRA Astronomical Knowledge Builder - Phase 1.4")
    print("=" * 60)

    # Plan a learning session
    learning_plan = plan_idle_learning(time_available=10)

    print("Planned Learning Session (10 minutes):")
    for i, task in enumerate(learning_plan, 1):
        print(f"{i}. {task}")

    # Generate progress report
    learning_system = Idle_Moment_Learning()
    progress = learning_system.generate_progress_report()

    print(f"\nAstronomical Knowledge Progress:")
    print(f"Topics Learned: {progress['total_topics_learned']}")
    print(f"\nDomain Progress:")
    for domain, domain_progress in progress['domain_progress'].items():
        print(f"  {domain}: {domain_progress['knowledge_level']:.1%} knowledge level")

    print("\nNext Steps:", progress['recommended_next_steps'][:3])

    print("\n" + "=" * 60)
    print("Phase 1.4 complete: Astronomical knowledge foundation operational")