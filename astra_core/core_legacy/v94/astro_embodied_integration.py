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
Astrophysics Embodied Learning Integration

This extends V94's embodied learning capabilities to astrophysics domains,
enabling the system to develop intuitive understanding of cosmic phenomena
through simulated "embodied" interaction with astronomical environments.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
import time
import logging

from .sensorimotor_system import VirtualEnvironment, WorldAction, Experience, ActionResult, SensoryInput, ModalityType
from .embodied_learning_engine import EmbodiedLearningEngine
from .common_sense_engine import PhysicsIntuitionModule, WorldScenario


@dataclass
class CosmicPhenomenon:
    """Representation of a cosmic phenomenon for embodied learning"""
    name: str
    type: str  # star, galaxy, nebula, black_hole, etc.
    properties: Dict[str, Any]
    scale: str  # stellar, galactic, cosmic
    observables: List[str]
    interactions: List[str]

@dataclass
class EmbodiedCosmicExperience:
    """Embodied experience with cosmic phenomena"""
    phenomenon: CosmicPhenomenon
    interaction_type: str
    sensory_data: Dict[str, np.ndarray]
    physical_insights: List[str]
    theoretical_connection: str
    confidence: float


class CosmicVirtualEnvironment(VirtualEnvironment):
    """Virtual environment simulating cosmic phenomena for embodied learning"""

    def __init__(self):
        super().__init__()
        self.cosmic_objects: List[CosmicPhenomenon] = []
        self.physical_laws = {
            "gravity": self._gravitational_interaction,
            "electromagnetism": self._electromagnetic_interaction,
            "nuclear": self._nuclear_interaction
        }
        self.observational_data = {}
        self._initialize_cosmic_environment()

    def _initialize_cosmic_environment(self):
        """Initialize cosmic objects and phenomena"""
        self.cosmic_objects = [
            CosmicPhenomenon(
                name="Main Sequence Star",
                type="star",
                properties={
                    "mass": 1.0,  # Solar masses
                    "temperature": 5778,  # Kelvin
                    "luminosity": 1.0,  # Solar luminosities
                    "radius": 1.0  # Solar radii
                },
                scale="stellar",
                observables=["light_spectrum", "luminosity", "temperature"],
                interactions=["nuclear_fusion", "gravitational_collapse", "radiation_pressure"]
            ),
            CosmicPhenomenon(
                name="Black Hole",
                type="black_hole",
                properties={
                    "mass": 10.0,  # Solar masses
                    "schwarzschild_radius": 30.0,  # km
                    "event_horizon": True,
                    "accretion_disk": True
                },
                scale="stellar",
                observables=["gravitational_lensing", "accretion_disk_emission", "hawking_radiation"],
                interactions=["gravitational_capture", "spacetime_curvature", "matter_accretion"]
            ),
            CosmicPhenomenon(
                name="Spiral Galaxy",
                type="galaxy",
                properties={
                    "mass": 1e12,  # Solar masses
                    "diameter": 100000,  # Light years
                    "spiral_arms": 4,
                    "central_bulge": True,
                    "dark_matter_halo": True
                },
                scale="galactic",
                observables=["rotation_curve", "stellar_populations", "gas_distribution"],
                interactions=["gravitational_dynamics", "star_formation", "galactic_mergers"]
            )
        ]

    def apply_cosmic_action(self, action: WorldAction) -> Dict[str, Any]:
        """Apply action to cosmic environment"""
        result = {"success": True, "changes": [], "insights": []}

        if action.action_type == "observe":
            # Simulate astronomical observation
            phenomenon = self._select_phenomenon(action.parameters.get("target", "star"))
            observation = self._observe_phenomenon(phenomenon)
            result["changes"].append({"observation": observation})
            result["insights"] = observation["insights"]

        elif action.action_type == "interact":
            # Simulate interaction with cosmic phenomenon
            phenomenon = self._select_phenomenon(action.parameters.get("target", "star"))
            interaction = self._interact_with_phenomenon(phenomenon, action.parameters)
            result["changes"].append({"interaction": interaction})
            result["insights"] = interaction.get("insights", [])

        return result

    def _select_phenomenon(self, target: str) -> CosmicPhenomenon:
        """Select cosmic phenomenon by type or name"""
        for phenomenon in self.cosmic_objects:
            if target.lower() in phenomenon.type.lower() or target.lower() in phenomenon.name.lower():
                return phenomenon
        return self.cosmic_objects[0]  # Default to first phenomenon

    def _observe_phenomenon(self, phenomenon: CosmicPhenomenon) -> Dict[str, Any]:
        """Simulate observation of cosmic phenomenon"""
        observation = {
            "phenomenon": phenomenon.name,
            "observables": {},
            "insights": []
        }

        for observable in phenomenon.observables:
            if observable == "light_spectrum":
                observation["observables"][observable] = self._generate_spectrum(phenomenon)
                observation["insights"].append(f"Spectral analysis reveals composition and temperature")
            elif observable == "luminosity":
                observation["observables"][observable] = phenomenon.properties.get("luminosity", 1.0)
                observation["insights"].append(f"Luminosity indicates energy output and mass")
            elif observable == "rotation_curve":
                observation["observables"][observable] = self._generate_rotation_curve(phenomenon)
                observation["insights"].append(f"Rotation curve reveals mass distribution and dark matter")

        return observation

    def _interact_with_phenomenon(self, phenomenon: CosmicPhenomenon, parameters: Dict) -> Dict[str, Any]:
        """Simulate interaction with cosmic phenomenon"""
        interaction = {
            "phenomenon": phenomenon.name,
            "interaction_type": parameters.get("interaction", "observe"),
            "results": {},
            "insights": []
        }

        for physical_law in self.physical_laws:
            result = self.physical_laws[physical_law](phenomenon, parameters)
            interaction["results"][physical_law] = result
            if result.get("insight"):
                interaction["insights"].append(result["insight"])

        return interaction

    def _generate_spectrum(self, phenomenon: CosmicPhenomenon) -> np.ndarray:
        """Generate synthetic spectrum for phenomenon"""
        # Simplified spectrum generation
        wavelengths = np.linspace(400, 700, 100)  # Visible light range
        temperature = phenomenon.properties.get("temperature", 5778)

        # Blackbody radiation (simplified)
        spectrum = (wavelengths / 550) ** -5 * np.exp(-((wavelengths - 550) / (temperature / 100)) ** 2)
        return spectrum / np.max(spectrum)

    def _generate_rotation_curve(self, phenomenon: CosmicPhenomenon) -> np.ndarray:
        """Generate rotation curve for galaxy"""
        radii = np.linspace(0, 50, 50)  # kpc
        # Simplified rotation curve with dark matter effect
        v_flat = 220  # km/s typical flat rotation velocity
        rotation_curve = v_flat * np.tanh(radii / 10)
        return rotation_curve

    def _gravitational_interaction(self, phenomenon: CosmicPhenomenon, parameters: Dict) -> Dict[str, Any]:
        """Simulate gravitational interaction"""
        mass = phenomenon.properties.get("mass", 1.0)

        if phenomenon.type == "black_hole":
            escape_velocity = np.sqrt(2 * 6.67e-11 * mass * 1.989e30 / (phenomenon.properties.get("schwarzschild_radius", 10) * 1000))
            return {
                "escape_velocity": escape_velocity,
                "insight": f"Strong gravity prevents light escape from {phenomenon.name}"
            }
        else:
            return {
                "gravitational_binding": True,
                "insight": f"Gravity governs structure and dynamics of {phenomenon.name}"
            }

    def _electromagnetic_interaction(self, phenomenon: CosmicPhenomenon, parameters: Dict) -> Dict[str, Any]:
        """Simulate electromagnetic interaction"""
        if phenomenon.type == "star":
            luminosity = phenomenon.properties.get("luminosity", 1.0)
            return {
                "radiation_pressure": luminosity * 3.828e26 / (4 * np.pi * (phenomenon.properties.get("radius", 1.0) * 6.96e8) ** 2),
                "insight": "Radiation pressure balances gravitational collapse in stars"
            }
        return {"interaction": "weak", "insight": "Minimal electromagnetic effects"}

    def _nuclear_interaction(self, phenomenon: CosmicPhenomenon, parameters: Dict) -> Dict[str, Any]:
        """Simulate nuclear interaction"""
        if phenomenon.type == "star":
            return {
                "fusion_reactions": True,
                "energy_source": "hydrogen to helium fusion",
                "insight": "Nuclear fusion powers stellar luminosity and evolution"
            }
        return {"interaction": "none", "insight": "No nuclear processes in this phenomenon"}

    def get_cosmic_sensory_feedback(self) -> List[SensoryInput]:
        """Get sensory feedback from cosmic environment"""
        feedback = []

        # Visual sensory input (astronomical observations)
        visual_data = np.array([obj.properties for obj in self.cosmic_objects])
        feedback.append(SensoryInput(
            modality=ModalityType.VISION,
            data=visual_data,
            timestamp=time.time(),
            metadata={"type": "astronomical_observations"}
        ))

        # Add other sensory modalities for cosmic phenomena
        for phenomenon in self.cosmic_objects:
            # "Touch" - gravitational effects
            gravity_data = np.array([phenomenon.properties.get("mass", 1.0)])
            feedback.append(SensoryInput(
                modality=ModalityType.TOUCH,
                data=gravity_data,
                timestamp=time.time(),
                metadata={"phenomenon": phenomenon.name, "type": "gravitational_effect"}
            ))

        return feedback


class AstroEmbodiedIntegrator:
    """
    Integrates V94 embodied learning with astrophysics knowledge.

    This enables the system to develop intuitive understanding of cosmic phenomena
    through simulated embodied interaction with astronomical environments.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.cosmic_environment = CosmicVirtualEnvironment()
        self.embodied_engine = EmbodiedLearningEngine()
        self.cosmic_experiences: List[EmbodiedCosmicExperience] = []
        self.developed_intuitions: Dict[str, float] = {}

    def explore_cosmic_phenomenon(self, phenomenon_name: str, interaction_types: List[str]) -> Dict[str, Any]:
        """Explore a cosmic phenomenon through embodied interaction"""
        self.logger.info(f"Exploring cosmic phenomenon: {phenomenon_name}")

        results = {
            "phenomenon": phenomenon_name,
            "interactions": [],
            "insights": [],
            "developed_intuitions": {}
        }

        for interaction_type in interaction_types:
            # Create action for cosmic interaction
            action = WorldAction(
                action_id=f"cosmic_{interaction_type}_{int(time.time())}",
                perception=[],
                decision={"type": "cosmic_exploration", "phenomenon": phenomenon_name},
                motor_commands=[],
                goal=f"explore_{phenomenon_name}"
            )

            # Apply interaction
            cosmic_result = self.cosmic_environment.apply_cosmic_action(action)

            # Process through embodied learning
            experience = Experience(
                action=action,
                result=ActionResult(
                    success=cosmic_result["success"],
                    sensory_feedback=self.cosmic_environment.get_cosmic_sensory_feedback(),
                    physical_changes=cosmic_result["changes"]
                ),
                timestamp=time.time(),
                context={"cosmic_phenomenon": phenomenon_name, "interaction": interaction_type}
            )

            # Process through embodied learning engine
            processed_experience = self.embodied_engine.interact_with_world(action)

            # Create cosmic experience record
            cosmic_experience = EmbodiedCosmicExperience(
                phenomenon=self.cosmic_environment._select_phenomenon(phenomenon_name),
                interaction_type=interaction_type,
                sensory_data=self._extract_sensory_data(processed_experience),
                physical_insights=cosmic_result.get("insights", []),
                theoretical_connection=self._generate_theoretical_connection(phenomenon_name, interaction_type),
                confidence=0.8 if cosmic_result["success"] else 0.3
            )

            self.cosmic_experiences.append(cosmic_experience)
            results["interactions"].append({
                "type": interaction_type,
                "success": cosmic_result["success"],
                "insights": cosmic_result.get("insights", []),
                "confidence": cosmic_experience.confidence
            })

            results["insights"].extend(cosmic_result.get("insights", []))

        # Update developed intuitions
        self._update_cosmic_intuitions(phenomenon_name, results)
        results["developed_intuitions"] = self.developed_intuitions

        return results

    def develop_cosmic_intuition(self, phenomenon_type: str) -> Dict[str, float]:
        """Develop intuitive understanding of cosmic phenomena"""
        self.logger.info(f"Developing cosmic intuition for: {phenomenon_type}")

        # Collect relevant experiences
        relevant_experiences = [
            exp for exp in self.cosmic_experiences
            if phenomenon_type.lower() in exp.phenomenon.type.lower()
        ]

        if not relevant_experiences:
            return {}

        # Develop intuition through experience aggregation
        intuitions = {}

        # Physics intuition
        physics_confidence = np.mean([exp.confidence for exp in relevant_experiences if "gravity" in exp.physical_insights])
        if physics_confidence > 0:
            intuitions[f"{phenomenon_type}_physics"] = physics_confidence

        # Scale intuition
        scale_insights = [exp for exp in relevant_experiences if exp.phenomenon.scale in exp.theoretical_connection]
        if scale_insights:
            intuitions[f"{phenomenon_type}_scale"] = np.mean([exp.confidence for exp in scale_insights])

        # Process intuition
        process_insights = [exp for exp in relevant_experiences if any(process in exp.theoretical_connection for process in ["fusion", "collapse", "accretion"])]
        if process_insights:
            intuitions[f"{phenomenon_type}_processes"] = np.mean([exp.confidence for exp in process_insights])

        # Update global intuitions
        self.developed_intuitions.update(intuitions)

        return intuitions

    def apply_embodied_reasoning_to_astrophysics(self, problem: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Apply embodied reasoning to astrophysics problems"""
        self.logger.info(f"Applying embodied reasoning to: {problem}")

        # Analyze problem for relevant phenomena
        relevant_phenomena = self._identify_relevant_phenomena(problem)

        reasoning_result = {
            "problem": problem,
            "embodied_insights": [],
            "intuitive_predictions": [],
            "confidence": 0.0,
            "reasoning_path": []
        }

        for phenomenon in relevant_phenomena:
            if phenomenon in self.developed_intuitions:
                intuition_strength = self.developed_intuitions[phenomenon]
                reasoning_result["embodied_insights"].append({
                    "phenomenon": phenomenon,
                    "intuition": f"Embodied understanding of {phenomenon} at {intuition_strength:.2f} confidence",
                    "strength": intuition_strength
                })

                # Generate intuitive predictions
                predictions = self._generate_intuitive_predictions(phenomenon, problem, context)
                reasoning_result["intuitive_predictions"].extend(predictions)

        # Combine insights into reasoning
        if reasoning_result["embodied_insights"]:
            reasoning_result["confidence"] = np.mean([insight["strength"] for insight in reasoning_result["embodied_insights"]])
            reasoning_result["reasoning_path"].append("Applied embodied cosmic intuition")

        return reasoning_result

    def get_cosmic_learning_status(self) -> Dict[str, Any]:
        """Get comprehensive cosmic learning status"""
        return {
            "total_cosmic_experiences": len(self.cosmic_experiences),
            "developed_intuitions": self.developed_intuitions,
            "phenomena_explored": list(set(exp.phenomenon.name for exp in self.cosmic_experiences)),
            "average_confidence": np.mean([exp.confidence for exp in self.cosmic_experiences]) if self.cosmic_experiences else 0.0,
            "embodied_learning_stats": self.embodied_engine.get_learning_statistics()
        }

    # Private methods

    def _extract_sensory_data(self, experience: Experience) -> Dict[str, np.ndarray]:
        """Extract sensory data from experience"""
        sensory_data = {}
        for sensory_input in experience.result.sensory_feedback:
            sensory_data[sensory_input.modality.value] = sensory_input.data
        return sensory_data

    def _generate_theoretical_connection(self, phenomenon: str, interaction: str) -> str:
        """Generate theoretical physics connection"""
        connections = {
            "star": "nuclear_fusion_gravitational_equilibrium",
            "black_hole": "general_relativity_spacetime_curvature",
            "galaxy": "gravitational_dynamics_dark_matter",
            "nebula": "stellar_formation_chemical_evolution"
        }

        base_connection = connections.get(phenomenon, "physical_laws")
        if interaction == "observe":
            return f"observational_{base_connection}"
        elif interaction == "interact":
            return f"interactive_{base_connection}"
        else:
            return base_connection

    def _update_cosmic_intuitions(self, phenomenon_name: str, results: Dict[str, Any]):
        """Update cosmic intuitions based on exploration results"""
        base_intuition = np.mean([interaction["confidence"] for interaction in results["interactions"]])
        current_intuition = self.developed_intuitions.get(phenomenon_name, 0.0)

        # Update with exponential moving average
        new_intuition = 0.7 * current_intuition + 0.3 * base_intuition
        self.developed_intuitions[phenomenon_name] = new_intuition

    def _identify_relevant_phenomena(self, problem: str) -> List[str]:
        """Identify cosmic phenomena relevant to problem"""
        phenomena = []
        problem_lower = problem.lower()

        if any(word in problem_lower for word in ["star", "stellar", "fusion", "sun"]):
            phenomena.append("star_physics")
        if any(word in problem_lower for word in ["black", "hole", "event", "horizon", "gravity"]):
            phenomena.append("black_hole")
        if any(word in problem_lower for word in ["galaxy", "galactic", "rotation", "dark"]):
            phenomena.append("galaxy_dynamics")
        if any(word in problem_lower for word in ["nebula", "formation", "birth"]):
            phenomena.append("stellar_formation")

        return phenomena

    def _generate_intuitive_predictions(self, phenomenon: str, problem: str, context: Dict[str, Any]) -> List[Dict]:
        """Generate intuitive predictions based on embodied understanding"""
        predictions = []

        if phenomenon == "star_physics":
            predictions.append({
                "prediction": "Stellar equilibrium maintained by balance of gravity and radiation pressure",
                "confidence": self.developed_intuitions.get(phenomenon, 0.0),
                "basis": "embodied understanding of stellar physics"
            })
        elif phenomenon == "black_hole":
            predictions.append({
                "prediction": "Strong gravitational effects will dominate nearby dynamics",
                "confidence": self.developed_intuitions.get(phenomenon, 0.0),
                "basis": "embodied understanding of extreme gravity"
            })
        elif phenomenon == "galaxy_dynamics":
            predictions.append({
                "prediction": "Rotation curve will show dark matter presence",
                "confidence": self.developed_intuitions.get(phenomenon, 0.0),
                "basis": "embodied understanding of galactic structure"
            })

        return predictions