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
ASTRA Live — Information-Theoretic Physics
Derive physical laws from information principles.

Based on the insight that information is physical:
- Landauer's principle: Information processing has thermodynamic cost
- Bekenstein-Hawking entropy: Black hole entropy proportional to area
- Holographic principle: Universe as quantum information processor
- Entropic gravity: Gravity emerges from information maximization
- ER=EPR: Entanglement ≡ Wormholes (information-geometry correspondence)
"""
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum


class InformationPrinciple(Enum):
    """Fundamental principles of information physics."""
    MAXIMUM_ENTROPY = "maximum_entropy"
    HOLOGRAPHIC_BOUND = "holographic_bound"
    ENTROPIC_FORCE = "entropic_force"
    IT_FROM_BIT = "it_from_bit"
    ER_EPR = "er_epr"
    INFORMATION_CONSERVATION = "information_conservation"


@dataclass
class InformationTheoreticFramework:
    """A theoretical framework derived from information principles."""
    name: str
    principle: InformationPrinciple
    mathematical_form: str
    predictions: List[str]
    testable_consequences: List[str]
    confidence: float


@dataclass
class EntropicPrediction:
    """Prediction from entropic gravity or information theory."""
    system: str
    parameters: Dict[str, float]
    prediction: str
    newtonian_acceleration: float
    entropic_acceleration: float
    ratio: float
    regime: str
    observational_test: str


class InformationTheoreticPhysics:
    """
    Derive physical laws from information-theoretic principles.

    Core idea: Many physical laws can be derived from the principle that
    systems maximize their entropy subject to constraints.

    Key results:
    - Newton's second law F = ma from entropic force (Verlinde, 2010)
    - MOND-like behavior at low accelerations from information maximization
    - Holographic bounds from information capacity limits
    - Black hole thermodynamics from information theory
    """

    def __init__(self):
        # Physical constants
        self.G = 6.67430e-11  # Gravitational constant (m^3 kg^-1 s^-2)
        self.c = 299792458    # Speed of light (m/s)
        self.hbar = 1.054571817e-34  # Reduced Planck constant (J s)
        self.kB = 1.380649e-23  # Boltzmann constant (J/K)

        # MOND acceleration scale (from observations)
        self.a0 = 1.2e-10  # m/s^2

    def derive_entropic_gravity(self) -> InformationTheoreticFramework:
        """
        Derive gravity as an entropic force.

        Verlinde (2010) showed that Newton's law of gravitation can be derived
        from thermodynamic considerations: F = T ∇S where T is temperature
        and S is entropy associated with position.

        Key insight: Gravity is not a fundamental force but emerges from
        information maximization.
        """
        return InformationTheoreticFramework(
            name="Entropic Gravity",
            principle=InformationPrinciple.ENTROPIC_FORCE,
            mathematical_form=(
                "F = T ∇S (entropic force)\n"
                "For gravity: F = G m1 m2 / r^2 (emerges)\n"
                "Temperature: T = (hbar a) / (2π c kB)\n"
                "Entropy gradient: ∇S = 2π kB / (hbar)"
            ),
            predictions=[
                "Newton's law of gravitation emerges from thermodynamics",
                "Einstein's equations from entropic considerations",
                "Inertia is entropic: m = (∇S / ∇x) / (2π c)",
            ],
            testable_consequences=[
                "Deviations from Newtonian gravity at low accelerations",
                "MOND-like behavior without dark matter particle",
                "Temperature associated with gravitational acceleration",
            ],
            confidence=0.85
        )

    def derive_holographic_principle(self) -> InformationTheoreticFramework:
        """
        Derive the holographic principle from information bounds.

        Bekenstein-Hawking entropy: S = A / (4 l_p^2)
        where A is horizon area and l_p is Planck length.

        This implies all information in a volume is encoded on its boundary.
        """
        return InformationTheoreticFramework(
            name="Holographic Principle",
            principle=InformationPrinciple.HOLOGRAPHIC_BOUND,
            mathematical_form=(
                "S_BH = A / (4 l_p^2) (Bekenstein-Hawking)\n"
                "where l_p = sqrt(G hbar / c^3)\n\n"
                "Implication: N_bits ≤ A / (4 l_p^2)\n"
                "Maximum information in region ∝ surface area"
            ),
            predictions=[
                "Universal entropy bound for any system",
                "Black hole entropy is maximum entropy for given volume",
                "AdS/CFT correspondence: QFT on boundary ≡ Gravity in bulk",
            ],
            testable_consequences=[
                "Black hole thermodynamics verified",
                "Holographic cosmology: CMB constraints on information content",
                "Bounds on quantum computing from holography",
            ],
            confidence=0.90
        )

    def derive_it_from_bit(self) -> InformationTheoreticFramework:
        """
        Derive the "it from bit" principle: physical reality from information.

        Wheeler's insight: The universe is fundamentally informational.
        Physical laws emerge from information processing.
        """
        return InformationTheoreticFramework(
            name="It From Bit",
            principle=InformationPrinciple.IT_FROM_BIT,
            mathematical_form=(
                "Physical states = Information states\n"
                "Physical laws = Information processing rules\n\n"
                "Quantum mechanics: Natural framework for information\n"
                "Measurement = Information extraction\n"
                "Wave function collapse = Bayesian update"
            ),
            predictions=[
                "Quantum mechanics is fundamental to physics",
                "Spacetime emerges from quantum information",
                "Consciousness as integrated information (IIT)",
            ],
            testable_consequences=[
                "Quantum information protocols testable",
                "Holographic duality verified in string theory",
                "Quantum computing demonstrates information physics",
            ],
            confidence=0.75
        )

    def derive_er_epr_correspondence(self) -> InformationTheoreticFramework:
        """
        Derive ER=EPR: Entanglement is equivalent to wormholes.

        Maldacena & Susskind (2013): Entangled particles are connected by
        microscopic wormholes (Einstein-Rosen bridges).

        This unifies quantum mechanics (entanglement) with general relativity (geometry).
        """
        return InformationTheoreticFramework(
            name="ER=EPR Correspondence",
            principle=InformationPrinciple.ER_EPR,
            mathematical_form=(
                "|EPR⟩ = |ER⟩\n\n"
                "Entangled state (EPR) ↔ Einstein-Rosen bridge (ER)\n"
                "Quantum information ≡ Geometric connection\n\n"
                "Implication: Spacetime emerges from entanglement"
            ),
            predictions=[
                "Spacetime connectivity from quantum entanglement",
                "Traversable wormholes from entanglement (Gao, Jafferis, Wall)",
                "Holographic emergence of space from entanglement entropy",
            ],
            testable_consequences=[
                "Quantum teleportation experiments",
                "Holographic entanglement entropy in AdS/CFT",
                "Quantum gravity corrections from ER=EPR",
            ],
            confidence=0.80
        )

    def test_entropic_force_prediction(self, system: str, parameters: Dict) -> Dict:
        """
        Test entropic gravity prediction for a specific system.

        This generates predictions that differ from Newtonian gravity,
        particularly at low accelerations (where MOND-like behavior emerges).

        Args:
            system: Type of system ("galaxy", "cluster", "dwarf", etc.)
            parameters: System parameters (mass, radius, etc.)

        Returns:
            Dictionary with predictions and comparison to Newtonian gravity.
        """
        mass = parameters.get("mass", 1e11)  # kg
        radius = parameters.get("radius", 10)  # kpc (convert to meters)

        # Convert kpc to meters
        r_meters = radius * 3.086e19

        # Newtonian acceleration: a = GM/r^2
        a_newton = self.G * mass / (r_meters ** 2)

        # Entropic correction (simplified Verlinde formula)
        # At low accelerations: a_entropic ≈ sqrt(a_newton * a0)
        a_entropic = a_newton  # Start with Newtonian

        if a_newton < self.a0:
            # MOND regime: entropic correction
            a_entropic = np.sqrt(a_newton * self.a0)
            regime = "Deep-MOND (Entropic)"
        elif a_newton < 10 * self.a0:
            # Transition regime
            interpolation = a_newton / (a_newton + self.a0)
            a_entropic = a_newton * interpolation
            regime = "Transition (Entropic)"
        else:
            regime = "Newtonian (Entropic ≈ Newtonian)"

        # Calculate ratio
        ratio = a_entropic / (a_newton + 1e-20)

        # Generate prediction text
        if ratio > 1.1:
            prediction = f"At a = {a_newton:.3e} m/s²: Entropic enhancement (MOND-like behavior)"
        elif ratio < 0.9:
            prediction = f"At a = {a_newton:.3e} m/s²: Entropic suppression"
        else:
            prediction = f"At a = {a_newton:.3e} m/s²: Newtonian regime"

        return {
            "system": system,
            "newtonian_acceleration": float(a_newton),
            "entropic_acceleration": float(a_entropic),
            "ratio": float(ratio),
            "regime": regime,
            "prediction": prediction,
            "observational_test": f"Compare with {system} rotation curves at radius {radius} kpc"
        }

    def derive_holographic_bounds_for_system(self, system_mass: float,
                                            system_radius: float) -> Dict:
        """
        Calculate holographic information bounds for a system.

        Bekenstein bound: S ≤ 2π E R / (hbar c)
        Universal entropy bound: S ≤ A / (4 l_p^2)
        """
        # System energy (E = mc^2)
        energy = system_mass * self.c**2

        # Bekenstein bound
        s_bekenstein = 2 * np.pi * energy * system_radius / (self.hbar * self.c)

        # Holographic bound (using Planck area)
        l_p = np.sqrt(self.G * self.hbar / self.c**3)
        area = 4 * np.pi * system_radius**2
        s_holographic = area / (4 * l_p**2)

        # Information capacity (bits)
        I_bekenstein = s_bekenstein / (np.log(2) * self.kB)
        I_holographic = s_holographic / (np.log(2) * self.kB)

        return {
            "system_mass_kg": system_mass,
            "system_radius_m": system_radius,
            "bekenstein_bound_J_K": float(s_bekenstein),
            "holographic_bound_J_K": float(s_holographic),
            "max_information_bekenstein_bits": float(I_bekenstein),
            "max_information_holographic_bits": float(I_holographic),
            "binding_constraint": "Bekenstein" if I_bekenstein < I_holographic else "Holographic"
        }

    def apply_er_epr_to_black_holes(self) -> Dict:
        """
        Apply ER=EPR correspondence to black hole information paradox.

        Resolution: Information is not lost because it's encoded in the
        entanglement between Hawking radiation particles (EPR) which
        corresponds to geometry behind the horizon (ER).
        """
        return {
            "paradox": "Black hole information loss",
            "er_epr_resolution": "Information preserved in entanglement",
            "mechanism": "Hawking radiation particles are EPR-entangled",
            "geometric_interpretation": "Entanglement ≡ Microscopic wormholes (ER)",
            "prediction": "Page curve: Information emerges after Page time",
            "testable": "Correlations in late-time Hawking radiation",
            "confidence": 0.85
        }


# Demonstration
if __name__ == "__main__":
    print("=" * 80)
    print("INFORMATION-THEORETIC PHYSICS")
    print("=" * 80)

    info_phys = InformationTheoreticPhysics()

    # Example 1: Derive entropic gravity
    print("\n1. ENTROPIC GRAVITY")
    print("-" * 80)

    framework = info_phys.derive_entropic_gravity()
    print(f"Framework: {framework.name}")
    print(f"Principle: {framework.principle.value}")
    print(f"\nMathematical Form:")
    for line in framework.mathematical_form.split('\n'):
        print(f"  {line}")
    print(f"\nPredictions:")
    for pred in framework.predictions[:3]:
        print(f"  • {pred}")

    # Example 2: Test entropic force for galaxy
    print("\n2. ENTROPIC FORCE PREDICTION for Galaxy")
    print("-" * 80)

    result = info_phys.test_entropic_force_prediction(
        "galaxy",
        {"mass": 1e11, "radius": 10}  # Milky Way mass, 10 kpc
    )

    print(f"System: {result['system']}")
    print(f"Newtonian a = {result['newtonian_acceleration']:.3e} m/s²")
    print(f"Entropic a = {result['entropic_acceleration']:.3e} m/s²")
    print(f"Ratio: {result['ratio']:.3f}")
    print(f"Regime: {result['regime']}")
    print(f"Prediction: {result['prediction']}")
    print(f"Test: {result['observational_test']}")

    # Example 3: Holographic bounds
    print("\n3. HOLOGRAPHIC BOUNDS for Black Hole")
    print("-" * 80)

    bh_mass = 1.989e30 * 10  # 10 solar masses
    bh_radius = 2 * info_phys.G * bh_mass / info_phys.c**2  # Schwarzschild radius

    bounds = info_phys.derive_holographic_bounds_for_system(bh_mass, bh_radius)

    print(f"Mass: {bounds['system_mass_kg']:.3e} kg")
    print(f"Radius: {bounds['system_radius_m']:.3e} m")
    print(f"Max information (holographic): {bounds['max_information_holographic_bits']:.3e} bits")
    print(f"Binding constraint: {bounds['binding_constraint']}")
