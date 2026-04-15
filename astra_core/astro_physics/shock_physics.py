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
Shock Physics for ISM Interactions

This module provides comprehensive shock physics for interstellar medium
interactions including:
- J-shocks (jump discontinuity, high velocity)
- C-shocks (continuous, magnetically mediated)
- Shock chemistry (molecule destruction/formation)
- Outflow-cloud interactions
- Cloud-cloud collisions

Physical constants in CGS units throughout.

Date: 2025-12-11
Version: 43.0
"""

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Callable
from enum import Enum, auto

# Physical constants (CGS)
G_GRAV = 6.674e-8       # Gravitational constant (cm³/g/s²)
K_BOLTZMANN = 1.381e-16  # Boltzmann constant (erg/K)
M_PROTON = 1.673e-24    # Proton mass (g)
M_SUN = 1.989e33        # Solar mass (g)
PC = 3.086e18           # Parsec (cm)
AU = 1.496e13           # Astronomical unit (cm)
YEAR = 3.156e7          # Year (seconds)
KM_S = 1e5              # km/s to cm/s

# Mean molecular weights
MU_ATOMIC = 1.27        # Atomic gas (H + 10% He)
MU_MOLECULAR = 2.37     # Molecular gas (H2 + 10% He)
MU_IONIZED = 0.62       # Fully ionized (H + 10% He)


class ShockType(Enum):
    """Types of astrophysical shocks."""
    J_SHOCK = auto()        # Jump shock (adiabatic, high velocity)
    C_SHOCK = auto()        # Continuous shock (magnetic, ion-neutral)
    CJ_SHOCK = auto()       # Combined C-shock with J-discontinuity
    ISOTHERMAL = auto()     # Radiatively cooled isothermal shock
    RADIATIVE = auto()      # Radiative shock with cooling zone


class ShockStrength(Enum):
    """Shock strength classification."""
    WEAK = auto()           # Mach < 2
    MODERATE = auto()       # 2 < Mach < 10
    STRONG = auto()         # 10 < Mach < 100
    HYPERSONIC = auto()     # Mach > 100


@dataclass
class ShockJumpConditions:
    """Rankine-Hugoniot jump conditions across shock front."""
    # Pre-shock (1) and post-shock (2) conditions
    rho_1: float            # Pre-shock density (g/cm³)
    rho_2: float            # Post-shock density (g/cm³)
    v_1: float              # Pre-shock velocity (cm/s) - shock frame
    v_2: float              # Post-shock velocity (cm/s) - shock frame
    p_1: float              # Pre-shock pressure (dyne/cm²)
    p_2: float              # Post-shock pressure (dyne/cm²)
    T_1: float              # Pre-shock temperature (K)
    T_2: float              # Post-shock temperature (K)

    # Derived quantities
    compression_ratio: float  # ρ₂/ρ₁
    mach_number: float       # Shock Mach number
    shock_velocity: float    # Shock velocity in lab frame (cm/s)
    shock_type: ShockType
    shock_strength: ShockStrength

    @property
    def velocity_jump(self) -> float:
        """Velocity change across shock (cm/s)."""
        return self.v_1 - self.v_2

    @property
    def temperature_ratio(self) -> float:
        """Temperature jump T₂/T₁."""
        return self.T_2 / self.T_1 if self.T_1 > 0 else float('inf')


@dataclass
class CShockProfile:
    """C-shock continuous structure."""
    positions: List[float]      # Position through shock (cm)
    densities: List[float]      # Density profile (g/cm³)
    ion_velocities: List[float]  # Ion velocity (cm/s)
    neutral_velocities: List[float]  # Neutral velocity (cm/s)
    temperatures: List[float]   # Temperature profile (K)
    ion_fractions: List[float]  # Ionization fraction

    shock_width: float          # Total shock width (cm)
    ion_neutral_drift: float    # Maximum ion-neutral drift velocity (cm/s)
    peak_temperature: float     # Maximum temperature in shock (K)
    magnetic_field: float       # Magnetic field strength (Gauss)


@dataclass
class ShockChemistryResult:
    """Chemical abundances through shock."""
    # Molecule abundances (relative to H₂)
    h2_fraction: float          # H₂ survival fraction
    co_fraction: float          # CO abundance
    h2o_fraction: float         # H₂O abundance
    sio_fraction: float         # SiO abundance (shock tracer!)
    oh_fraction: float          # OH abundance
    ch_fraction: float          # CH abundance

    # Enhancement factors relative to ambient
    sio_enhancement: float      # SiO enhancement (can be >10⁴)
    h2o_enhancement: float      # H₂O enhancement

    # Destruction/formation
    h2_dissociated: bool        # Whether H₂ significantly dissociated
    dust_sputtered: bool        # Whether dust grains sputtered

    shock_velocity: float       # Shock velocity (cm/s)
    shock_type: ShockType


@dataclass
class OutflowProperties:
    """Protostellar outflow properties from shock analysis."""
    # Measured quantities
    momentum: float             # Total momentum (g cm/s)
    kinetic_energy: float       # Total kinetic energy (erg)
    mass: float                 # Outflow mass (g)
    velocity: float             # Characteristic velocity (cm/s)

    # Derived quantities
    mass_loss_rate: float       # Ṁ_out (g/s)
    momentum_rate: float        # Momentum injection rate (g cm/s²)
    mechanical_luminosity: float  # L_mech = (1/2) Ṁ v² (erg/s)
    dynamical_age: float        # t_dyn = length / velocity (s)

    # Classification
    is_collimated: bool         # Jet-like vs wide-angle
    opening_angle: float        # Opening angle (radians)

    @property
    def mass_msun(self) -> float:
        """Outflow mass in solar masses."""
        return self.mass / M_SUN

    @property
    def momentum_rate_msun_km_s_yr(self) -> float:
        """Momentum rate in M_sun km/s / yr."""
        return self.momentum_rate * YEAR / (M_SUN * KM_S)


class RankineHugoniot:
    """
    Rankine-Hugoniot shock jump conditions.

    Solves the conservation equations across a shock discontinuity:
    - Mass: ρ₁v₁ = ρ₂v₂
    - Momentum: P₁ + ρ₁v₁² = P₂ + ρ₂v₂²
    - Energy: (γ/(γ-1))(P₁/ρ₁) + v₁²/2 = (γ/(γ-1))(P₂/ρ₂) + v₂²/2
    """

    def __init__(self, gamma: float = 5/3, mu: float = MU_ATOMIC):
        """
        Initialize Rankine-Hugoniot solver.

        Args:
            gamma: Adiabatic index (5/3 for monoatomic, 7/5 for diatomic)
            mu: Mean molecular weight
        """
        self.gamma = gamma
        self.mu = mu

    def sound_speed(self, temperature: float) -> float:
        """
        Adiabatic sound speed.

        c_s = √(γ k T / μ m_H)

        Args:
            temperature: Gas temperature (K)

        Returns:
            Sound speed (cm/s)
        """
        return math.sqrt(self.gamma * K_BOLTZMANN * temperature / (self.mu * M_PROTON))

    def mach_number(self, velocity: float, temperature: float) -> float:
        """
        Calculate Mach number.

        Args:
            velocity: Flow velocity (cm/s)
            temperature: Gas temperature (K)

        Returns:
            Mach number
        """
        c_s = self.sound_speed(temperature)
        return abs(velocity) / c_s

    def compression_ratio(self, mach: float) -> float:
        """
        Density compression ratio for strong shock.

        r = ρ₂/ρ₁ = (γ+1)M² / ((γ-1)M² + 2)

        For γ = 5/3 and M >> 1: r → 4

        Args:
            mach: Mach number

        Returns:
            Compression ratio
        """
        g = self.gamma
        m2 = mach**2
        return (g + 1) * m2 / ((g - 1) * m2 + 2)

    def pressure_ratio(self, mach: float) -> float:
        """
        Pressure jump ratio.

        P₂/P₁ = (2γM² - (γ-1)) / (γ+1)

        Args:
            mach: Mach number

        Returns:
            Pressure ratio P₂/P₁
        """
        g = self.gamma
        return (2 * g * mach**2 - (g - 1)) / (g + 1)

    def temperature_ratio(self, mach: float) -> float:
        """
        Temperature jump ratio.

        T₂/T₁ = (P₂/P₁) / (ρ₂/ρ₁)

        Args:
            mach: Mach number

        Returns:
            Temperature ratio T₂/T₁
        """
        return self.pressure_ratio(mach) / self.compression_ratio(mach)

    def post_shock_temperature(self, shock_velocity: float,
                               pre_shock_temp: float = 10.0) -> float:
        """
        Post-shock temperature.

        For strong shocks: T₂ ≈ 3μm_H v_s² / (16 k_B)

        Args:
            shock_velocity: Shock velocity (cm/s)
            pre_shock_temp: Pre-shock temperature (K)

        Returns:
            Post-shock temperature (K)
        """
        mach = self.mach_number(shock_velocity, pre_shock_temp)
        t_ratio = self.temperature_ratio(mach)
        return pre_shock_temp * t_ratio

    def strong_shock_temperature(self, shock_velocity: float) -> float:
        """
        Post-shock temperature in strong shock limit.

        T_s = 3 μ m_H v_s² / (16 k_B)

        Args:
            shock_velocity: Shock velocity (cm/s)

        Returns:
            Post-shock temperature (K)
        """
        return 3 * self.mu * M_PROTON * shock_velocity**2 / (16 * K_BOLTZMANN)

    def solve(self, shock_velocity: float, pre_shock_density: float,
              pre_shock_temperature: float) -> ShockJumpConditions:
        """
        Solve complete Rankine-Hugoniot jump conditions.

        Args:
            shock_velocity: Shock velocity in lab frame (cm/s)
            pre_shock_density: Pre-shock density (g/cm³)
            pre_shock_temperature: Pre-shock temperature (K)

        Returns:
            ShockJumpConditions with all quantities
        """
        # Pre-shock conditions
        rho_1 = pre_shock_density
        T_1 = pre_shock_temperature
        c_s = self.sound_speed(T_1)
        p_1 = rho_1 * c_s**2 / self.gamma

        # Mach number
        mach = abs(shock_velocity) / c_s

        # Jump ratios
        r = self.compression_ratio(mach)
        p_ratio = self.pressure_ratio(mach)
        t_ratio = self.temperature_ratio(mach)

        # Post-shock conditions
        rho_2 = rho_1 * r
        p_2 = p_1 * p_ratio
        T_2 = T_1 * t_ratio

        # Velocities in shock frame
        v_1 = shock_velocity
        v_2 = v_1 / r

        # Classify shock
        if mach < 2:
            strength = ShockStrength.WEAK
        elif mach < 10:
            strength = ShockStrength.MODERATE
        elif mach < 100:
            strength = ShockStrength.STRONG
        else:
            strength = ShockStrength.HYPERSONIC

        return ShockJumpConditions(
            rho_1=rho_1, rho_2=rho_2,
            v_1=v_1, v_2=v_2,
            p_1=p_1, p_2=p_2,
            T_1=T_1, T_2=T_2,
            compression_ratio=r,
            mach_number=mach,
            shock_velocity=shock_velocity,
            shock_type=ShockType.J_SHOCK,
            shock_strength=strength
        )


class JShock:
    """
    J-type (Jump) shock model.

    High-velocity shocks where the magnetic field is not strong enough
    to mediate the shock. Results in a sharp discontinuity with
    strong heating and potential molecule dissociation.
    """

    def __init__(self, gamma: float = 5/3, mu: float = MU_ATOMIC):
        """
        Initialize J-shock model.

        Args:
            gamma: Adiabatic index
            mu: Mean molecular weight
        """
        self.rh = RankineHugoniot(gamma, mu)
        self.gamma = gamma
        self.mu = mu

    def critical_velocity_h2_dissociation(self) -> float:
        """
        Critical shock velocity for H₂ dissociation.

        H₂ binding energy ~ 4.5 eV → T ~ 50,000 K → v_s ~ 25 km/s

        Returns:
            Critical velocity (cm/s)
        """
        # T_dissoc ~ 2000-4000 K for significant dissociation
        # v_s ~ sqrt(16 k T / 3 μ m_H)
        t_dissoc = 3000  # K
        return math.sqrt(16 * K_BOLTZMANN * t_dissoc / (3 * self.mu * M_PROTON))

    def cooling_length(self, shock_velocity: float, density: float) -> float:
        """
        Estimate cooling length behind shock.

        L_cool ~ v_s t_cool where t_cool ~ 3kT / (n Λ(T))

        Args:
            shock_velocity: Shock velocity (cm/s)
            density: Pre-shock density (g/cm³)

        Returns:
            Cooling length (cm)
        """
        # Post-shock temperature
        T_2 = self.rh.strong_shock_temperature(shock_velocity)

        # Number density
        n = density / (self.mu * M_PROTON)

        # Cooling function approximation (erg cm³/s)
        # For T > 10^4 K: Λ ~ 10^-23 (T/10^4)^0.5
        if T_2 > 1e4:
            lambda_cool = 1e-23 * math.sqrt(T_2 / 1e4)
        else:
            # Lower temperature: Λ ~ 10^-26 (atomic cooling)
            lambda_cool = 1e-26

        # Cooling time
        t_cool = 3 * K_BOLTZMANN * T_2 / (n * lambda_cool)

        # Cooling length
        v_post = shock_velocity / self.rh.compression_ratio(
            self.rh.mach_number(shock_velocity, 100))
        return v_post * t_cool

    def compute(self, shock_velocity: float, pre_shock_density: float,
                pre_shock_temperature: float = 10.0) -> ShockJumpConditions:
        """
        Compute J-shock structure.

        Args:
            shock_velocity: Shock velocity (cm/s)
            pre_shock_density: Pre-shock density (g/cm³)
            pre_shock_temperature: Pre-shock temperature (K)

        Returns:
            ShockJumpConditions
        """
        return self.rh.solve(shock_velocity, pre_shock_density, pre_shock_temperature)


class CShock:
    """
    C-type (Continuous) shock model.

    Low-velocity shocks in magnetized, partially ionized gas where
    the magnetic field is strong enough to couple ions to neutrals
    via ion-neutral collisions. Results in a smooth transition.

    C-shocks occur when v_s < v_A (Alfvén velocity).
    """

    def __init__(self, mu_neutral: float = MU_MOLECULAR,
                 mu_ion: float = 29.0):  # HCO+ typical
        """
        Initialize C-shock model.

        Args:
            mu_neutral: Mean molecular weight of neutrals
            mu_ion: Mean molecular weight of ions
        """
        self.mu_n = mu_neutral
        self.mu_i = mu_ion

    def alfven_velocity(self, magnetic_field: float, density: float) -> float:
        """
        Alfvén velocity in partially ionized gas.

        v_A = B / √(4π ρ_ion) ≈ B / √(4π x_i ρ)

        Args:
            magnetic_field: Magnetic field (Gauss)
            density: Total density (g/cm³)

        Returns:
            Alfvén velocity (cm/s)
        """
        return magnetic_field / math.sqrt(4 * math.pi * density)

    def critical_velocity(self, magnetic_field: float, density: float) -> float:
        """
        Critical velocity for C-shock vs J-shock.

        C-shock exists when v_s < v_crit ≈ min(v_A, v_ms)
        where v_ms is magnetosonic velocity.

        Args:
            magnetic_field: Magnetic field (Gauss)
            density: Density (g/cm³)

        Returns:
            Critical velocity (cm/s)
        """
        v_a = self.alfven_velocity(magnetic_field, density)
        # Sound speed at 10 K
        c_s = math.sqrt(K_BOLTZMANN * 10 / (self.mu_n * M_PROTON))
        # Magnetosonic velocity
        v_ms = math.sqrt(v_a**2 + c_s**2)
        return v_ms

    def ion_neutral_coupling_rate(self, density: float,
                                  ionization_fraction: float) -> float:
        """
        Ion-neutral collision rate.

        ν_in = <σv>_in n_n ≈ 2×10^-9 n_n s^-1

        Args:
            density: Total density (g/cm³)
            ionization_fraction: Ionization fraction x_i

        Returns:
            Collision rate (s^-1)
        """
        n_total = density / (self.mu_n * M_PROTON)
        n_neutral = n_total * (1 - ionization_fraction)
        sigma_v = 2e-9  # cm³/s, typical ion-neutral rate
        return sigma_v * n_neutral

    def shock_width(self, shock_velocity: float, magnetic_field: float,
                    density: float, ionization_fraction: float) -> float:
        """
        C-shock width estimate.

        L_shock ~ v_A / ν_in

        Args:
            shock_velocity: Shock velocity (cm/s)
            magnetic_field: Magnetic field (Gauss)
            density: Density (g/cm³)
            ionization_fraction: Ionization fraction

        Returns:
            Shock width (cm)
        """
        v_a = self.alfven_velocity(magnetic_field, density)
        nu_in = self.ion_neutral_coupling_rate(density, ionization_fraction)
        return v_a / nu_in if nu_in > 0 else float('inf')

    def maximum_temperature(self, shock_velocity: float,
                            ionization_fraction: float) -> float:
        """
        Maximum temperature in C-shock.

        For C-shocks, heating is from ion-neutral friction.
        T_max ~ μ m_H v_drift² / (3 k_B)

        Args:
            shock_velocity: Shock velocity (cm/s)
            ionization_fraction: Ionization fraction

        Returns:
            Maximum temperature (K)
        """
        # Ion-neutral drift is comparable to shock velocity
        v_drift = shock_velocity * 0.5  # Approximate
        return self.mu_n * M_PROTON * v_drift**2 / (3 * K_BOLTZMANN)

    def compute(self, shock_velocity: float, magnetic_field: float,
                density: float, ionization_fraction: float = 1e-7,
                pre_shock_temperature: float = 10.0,
                n_points: int = 100) -> CShockProfile:
        """
        Compute C-shock profile (simplified model).

        Args:
            shock_velocity: Shock velocity (cm/s)
            magnetic_field: Magnetic field (Gauss)
            density: Pre-shock density (g/cm³)
            ionization_fraction: Ionization fraction
            pre_shock_temperature: Pre-shock temperature (K)
            n_points: Number of points in profile

        Returns:
            CShockProfile with full structure
        """
        # Check if C-shock is valid
        v_crit = self.critical_velocity(magnetic_field, density)
        if shock_velocity > v_crit:
            # Will be J-shock instead
            pass  # Continue anyway for comparison

        # Shock width
        width = self.shock_width(shock_velocity, magnetic_field,
                                 density, ionization_fraction)

        # Generate profile
        positions = [i * width / (n_points - 1) for i in range(n_points)]

        # Simplified model: smooth transitions
        densities = []
        ion_velocities = []
        neutral_velocities = []
        temperatures = []
        ion_fractions = []

        # Compression ratio (less than J-shock due to magnetic support)
        r_final = 2.0  # Typical C-shock compression

        for i, x in enumerate(positions):
            # Normalized position
            xi = x / width

            # Smooth transition functions (tanh-like)
            transition = 0.5 * (1 + math.tanh(4 * (xi - 0.5)))

            # Density increases
            rho = density * (1 + (r_final - 1) * transition)
            densities.append(rho)

            # Ion velocity drops first (magnetic)
            v_i = shock_velocity * (1 - 0.8 * transition)
            ion_velocities.append(v_i)

            # Neutral velocity lags
            v_n = shock_velocity * (1 - 0.8 * 0.5 * (1 + math.tanh(4 * (xi - 0.7))))
            neutral_velocities.append(v_n)

            # Temperature peaks in middle
            t_peak = self.maximum_temperature(shock_velocity, ionization_fraction)
            t_profile = pre_shock_temperature + (t_peak - pre_shock_temperature) * \
                        4 * xi * (1 - xi)  # Parabolic profile
            temperatures.append(t_profile)

            # Ionization fraction roughly constant
            ion_fractions.append(ionization_fraction)

        # Maximum drift velocity
        max_drift = max(abs(vi - vn) for vi, vn in
                        zip(ion_velocities, neutral_velocities))

        return CShockProfile(
            positions=positions,
            densities=densities,
            ion_velocities=ion_velocities,
            neutral_velocities=neutral_velocities,
            temperatures=temperatures,
            ion_fractions=ion_fractions,
            shock_width=width,
            ion_neutral_drift=max_drift,
            peak_temperature=max(temperatures),
            magnetic_field=magnetic_field
        )


class ShockChemistry:
    """
    Chemical effects of shocks on ISM gas.

    Key processes:
    - H₂ dissociation (J-shocks, v_s > 25 km/s)
    - Grain sputtering releasing Si, Fe (v_s > 20 km/s)
    - Endothermic reactions enhanced (SiO, H₂O formation)
    - Ice mantle evaporation
    """

    def __init__(self):
        """Initialize shock chemistry model."""
        # Critical velocities for various processes
        self.v_h2_dissoc = 25 * KM_S      # H₂ dissociation
        self.v_grain_sputter = 20 * KM_S  # Grain sputtering onset
        self.v_ice_evap = 10 * KM_S       # Ice mantle evaporation
        self.v_sio_enhance = 15 * KM_S    # SiO enhancement

    def h2_survival_fraction(self, shock_velocity: float,
                             shock_type: ShockType) -> float:
        """
        Fraction of H₂ surviving shock passage.

        Args:
            shock_velocity: Shock velocity (cm/s)
            shock_type: Type of shock (J or C)

        Returns:
            H₂ survival fraction (0-1)
        """
        v_s = abs(shock_velocity)

        if shock_type == ShockType.C_SHOCK:
            # C-shocks preserve H₂ better
            if v_s < 40 * KM_S:
                return 1.0
            elif v_s < 60 * KM_S:
                return 0.5
            else:
                return 0.1
        else:
            # J-shocks dissociate H₂
            if v_s < self.v_h2_dissoc:
                return 1.0
            elif v_s < 40 * KM_S:
                return 0.3
            elif v_s < 60 * KM_S:
                return 0.05
            else:
                return 0.01

    def sio_enhancement(self, shock_velocity: float,
                        shock_type: ShockType) -> float:
        """
        SiO abundance enhancement factor.

        SiO is a key shock tracer because Si is released from
        grain cores by sputtering.

        Args:
            shock_velocity: Shock velocity (cm/s)
            shock_type: Type of shock

        Returns:
            Enhancement factor relative to ambient (~10⁻¹²)
        """
        v_s = abs(shock_velocity)

        if v_s < self.v_sio_enhance:
            return 1.0  # No enhancement

        # Enhancement increases with velocity
        if shock_type == ShockType.C_SHOCK:
            # C-shocks: moderate enhancement
            factor = 10**((v_s / KM_S - 15) / 5)
            return min(factor, 1e4)
        else:
            # J-shocks: strong enhancement
            factor = 10**((v_s / KM_S - 15) / 3)
            return min(factor, 1e5)

    def h2o_enhancement(self, shock_velocity: float,
                        shock_type: ShockType) -> float:
        """
        H₂O abundance enhancement factor.

        H₂O forms efficiently in warm shocked gas via:
        O + H₂ → OH + H (barrier ~2000 K)
        OH + H₂ → H₂O + H (barrier ~2000 K)

        Args:
            shock_velocity: Shock velocity (cm/s)
            shock_type: Type of shock

        Returns:
            Enhancement factor
        """
        v_s = abs(shock_velocity)

        if v_s < 10 * KM_S:
            return 1.0

        # Enhancement from warm gas chemistry
        if shock_type == ShockType.C_SHOCK:
            factor = 10**(v_s / (20 * KM_S))
            return min(factor, 1e4)
        else:
            # J-shocks: H₂O destroyed at high T
            if v_s < 30 * KM_S:
                return 1e3
            else:
                return 1e2  # Reduced by dissociation

    def grain_sputtering(self, shock_velocity: float) -> Dict[str, float]:
        """
        Grain sputtering yields for various elements.

        Args:
            shock_velocity: Shock velocity (cm/s)

        Returns:
            Dict of element yields (fraction released from grains)
        """
        v_s = abs(shock_velocity)

        yields = {
            'Si': 0.0,  # Silicon
            'Fe': 0.0,  # Iron
            'Mg': 0.0,  # Magnesium
            'C': 0.0,   # Carbon (from carbonaceous grains)
        }

        if v_s < self.v_grain_sputter:
            return yields

        # Sputtering increases with velocity
        fraction = min(1.0, (v_s / self.v_grain_sputter - 1) / 2)

        yields['Si'] = 0.1 * fraction  # Silicates
        yields['Fe'] = 0.05 * fraction  # Fe inclusions
        yields['Mg'] = 0.1 * fraction  # Silicates
        yields['C'] = 0.2 * fraction   # Carbonaceous

        return yields

    def compute_chemistry(self, shock_velocity: float,
                          shock_type: ShockType,
                          ambient_abundances: Optional[Dict[str, float]] = None
                          ) -> ShockChemistryResult:
        """
        Compute post-shock chemical abundances.

        Args:
            shock_velocity: Shock velocity (cm/s)
            shock_type: Type of shock
            ambient_abundances: Pre-shock abundances (relative to H₂)

        Returns:
            ShockChemistryResult
        """
        # Default ambient abundances
        if ambient_abundances is None:
            ambient_abundances = {
                'co': 1e-4,
                'h2o': 1e-8,  # Ice depleted
                'sio': 1e-12,  # Very depleted
                'oh': 1e-8,
                'ch': 1e-9
            }

        # H₂ survival
        h2_frac = self.h2_survival_fraction(shock_velocity, shock_type)

        # Enhancement factors
        sio_enh = self.sio_enhancement(shock_velocity, shock_type)
        h2o_enh = self.h2o_enhancement(shock_velocity, shock_type)

        # Post-shock abundances
        sio_frac = ambient_abundances['sio'] * sio_enh
        h2o_frac = ambient_abundances['h2o'] * h2o_enh

        # CO survives most shocks
        co_frac = ambient_abundances['co'] * (0.5 + 0.5 * h2_frac)

        # OH and CH enhanced in warm gas
        oh_frac = ambient_abundances['oh'] * (1 + h2o_enh * 0.1)
        ch_frac = ambient_abundances['ch'] * (1 + 0.1 * h2o_enh)

        return ShockChemistryResult(
            h2_fraction=h2_frac,
            co_fraction=co_frac,
            h2o_fraction=h2o_frac,
            sio_fraction=sio_frac,
            oh_fraction=oh_frac,
            ch_fraction=ch_frac,
            sio_enhancement=sio_enh,
            h2o_enhancement=h2o_enh,
            h2_dissociated=h2_frac < 0.5,
            dust_sputtered=abs(shock_velocity) > self.v_grain_sputter,
            shock_velocity=shock_velocity,
            shock_type=shock_type
        )


class OutflowShockAnalysis:
    """
    Analysis of protostellar outflow shocks.

    Outflows from young stellar objects drive shocks into
    the ambient molecular cloud, creating observable signatures.
    """

    def __init__(self):
        """Initialize outflow analysis."""
        self.j_shock = JShock()
        self.chemistry = ShockChemistry()

    def momentum_from_co(self, integrated_intensity: float,
                         velocity_extent: float,
                         distance: float,
                         beam_size: float,
                         x_co: float = 1e-4) -> float:
        """
        Estimate outflow momentum from CO emission.

        P = M × v where M estimated from CO intensity

        Args:
            integrated_intensity: CO integrated intensity (K km/s)
            velocity_extent: Velocity range of outflow (km/s)
            distance: Distance to source (cm)
            beam_size: Beam size (radians)
            x_co: CO/H₂ abundance ratio

        Returns:
            Momentum (g cm/s)
        """
        # Column density from CO (assuming optically thin, LTE)
        # N_CO ≈ 2.5×10^14 × T_ex × ∫T_mb dv cm^-2
        # Assuming T_ex = 20 K
        t_ex = 20.0
        n_co = 2.5e14 * t_ex * integrated_intensity  # cm^-2

        # H₂ column density
        n_h2 = n_co / x_co

        # Mass in beam
        beam_area = math.pi * (distance * beam_size / 2)**2
        mass = n_h2 * (2 * M_PROTON) * beam_area

        # Momentum
        velocity = velocity_extent * KM_S / 2  # Characteristic velocity
        return mass * velocity

    def dynamical_age(self, length: float, velocity: float) -> float:
        """
        Estimate outflow dynamical age.

        t_dyn = L / v

        Args:
            length: Outflow length (cm)
            velocity: Characteristic velocity (cm/s)

        Returns:
            Dynamical age (s)
        """
        return length / velocity if velocity > 0 else float('inf')

    def mechanical_luminosity(self, momentum_rate: float,
                              velocity: float) -> float:
        """
        Mechanical luminosity of outflow.

        L_mech = (1/2) Ṗ × v = (1/2) Ṁ v²

        Args:
            momentum_rate: Momentum injection rate (g cm/s²)
            velocity: Outflow velocity (cm/s)

        Returns:
            Mechanical luminosity (erg/s)
        """
        return 0.5 * momentum_rate * velocity

    def analyze_outflow(self, mass: float, velocity: float,
                        length: float, opening_angle: float = 0.3
                        ) -> OutflowProperties:
        """
        Complete outflow analysis.

        Args:
            mass: Total outflow mass (g)
            velocity: Characteristic velocity (cm/s)
            length: Outflow length (cm)
            opening_angle: Opening angle (radians)

        Returns:
            OutflowProperties
        """
        # Basic quantities
        momentum = mass * velocity
        kinetic_energy = 0.5 * mass * velocity**2

        # Dynamical age
        t_dyn = self.dynamical_age(length, velocity)

        # Rates (assuming steady-state)
        mass_rate = mass / t_dyn if t_dyn > 0 else 0
        momentum_rate = momentum / t_dyn if t_dyn > 0 else 0

        # Mechanical luminosity
        l_mech = self.mechanical_luminosity(momentum_rate, velocity)

        # Classification
        is_collimated = opening_angle < 0.2  # ~ 10 degrees

        return OutflowProperties(
            momentum=momentum,
            kinetic_energy=kinetic_energy,
            mass=mass,
            velocity=velocity,
            mass_loss_rate=mass_rate,
            momentum_rate=momentum_rate,
            mechanical_luminosity=l_mech,
            dynamical_age=t_dyn,
            is_collimated=is_collimated,
            opening_angle=opening_angle
        )


class CloudCollisionShock:
    """
    Cloud-cloud collision shock analysis.

    When molecular clouds collide, shocks compress the gas and
    can trigger star formation.
    """

    def __init__(self):
        """Initialize cloud collision model."""
        self.rh = RankineHugoniot(gamma=5/3, mu=MU_MOLECULAR)

    def collision_velocity(self, cloud1_velocity: float,
                           cloud2_velocity: float) -> float:
        """
        Relative collision velocity.

        Args:
            cloud1_velocity: Cloud 1 velocity (cm/s)
            cloud2_velocity: Cloud 2 velocity (cm/s)

        Returns:
            Collision velocity (cm/s)
        """
        return abs(cloud1_velocity - cloud2_velocity)

    def interface_density(self, rho1: float, rho2: float,
                          v_collision: float,
                          temperature: float = 10.0) -> float:
        """
        Post-shock density at collision interface.

        Args:
            rho1: Cloud 1 density (g/cm³)
            rho2: Cloud 2 density (g/cm³)
            v_collision: Collision velocity (cm/s)
            temperature: Pre-shock temperature (K)

        Returns:
            Interface density (g/cm³)
        """
        # Each cloud sees shock at half collision velocity
        v_shock = v_collision / 2

        # Compression ratio
        mach = self.rh.mach_number(v_shock, temperature)
        r = self.rh.compression_ratio(mach)

        # Both clouds compressed
        rho_interface = (rho1 + rho2) * r / 2
        return rho_interface

    def triggered_star_formation(self, interface_density: float,
                                 temperature: float,
                                 cloud_mass: float) -> Dict[str, float]:
        """
        Estimate star formation triggered by collision.

        Args:
            interface_density: Post-shock density (g/cm³)
            temperature: Post-shock temperature (K)
            cloud_mass: Total cloud mass involved (g)

        Returns:
            Dict with Jeans mass, number of cores, SF efficiency
        """
        from .gravitational_collapse import JeansAnalysis

        jeans = JeansAnalysis()
        m_j = jeans.jeans_mass_thermal(temperature, interface_density)

        # Potential cores
        n_cores = cloud_mass / m_j

        # Efficiency (compressed gas more efficient)
        sf_efficiency = min(0.3, 0.01 * (interface_density / 1e-20))

        return {
            'jeans_mass': m_j,
            'jeans_mass_msun': m_j / M_SUN,
            'potential_cores': int(n_cores),
            'sf_efficiency': sf_efficiency,
            'expected_stars': int(n_cores * sf_efficiency)
        }


# Singleton accessors
_j_shock: Optional[JShock] = None
_c_shock: Optional[CShock] = None
_shock_chemistry: Optional[ShockChemistry] = None
_outflow_analysis: Optional[OutflowShockAnalysis] = None
_cloud_collision: Optional[CloudCollisionShock] = None


def get_j_shock(gamma: float = 5/3, mu: float = MU_ATOMIC) -> JShock:
    """Get or create J-shock singleton."""
    global _j_shock
    if _j_shock is None:
        _j_shock = JShock(gamma, mu)
    return _j_shock


def get_c_shock() -> CShock:
    """Get or create C-shock singleton."""
    global _c_shock
    if _c_shock is None:
        _c_shock = CShock()
    return _c_shock


def get_shock_chemistry() -> ShockChemistry:
    """Get or create shock chemistry singleton."""
    global _shock_chemistry
    if _shock_chemistry is None:
        _shock_chemistry = ShockChemistry()
    return _shock_chemistry


def get_outflow_analysis() -> OutflowShockAnalysis:
    """Get or create outflow analysis singleton."""
    global _outflow_analysis
    if _outflow_analysis is None:
        _outflow_analysis = OutflowShockAnalysis()
    return _outflow_analysis


def get_cloud_collision() -> CloudCollisionShock:
    """Get or create cloud collision singleton."""
    global _cloud_collision
    if _cloud_collision is None:
        _cloud_collision = CloudCollisionShock()
    return _cloud_collision


# Convenience functions
def post_shock_temperature(shock_velocity: float, mu: float = MU_ATOMIC) -> float:
    """
    Quick calculation of post-shock temperature.

    T_s = 3 μ m_H v_s² / (16 k_B)

    Args:
        shock_velocity: Shock velocity (cm/s)
        mu: Mean molecular weight

    Returns:
        Post-shock temperature (K)
    """
    return 3 * mu * M_PROTON * shock_velocity**2 / (16 * K_BOLTZMANN)


def shock_compression_ratio(mach: float, gamma: float = 5/3) -> float:
    """
    Compression ratio for given Mach number.

    Args:
        mach: Mach number
        gamma: Adiabatic index

    Returns:
        Compression ratio ρ₂/ρ₁
    """
    return (gamma + 1) * mach**2 / ((gamma - 1) * mach**2 + 2)


def is_c_shock(shock_velocity: float, magnetic_field: float,
               density: float) -> bool:
    """
    Determine if shock will be C-type or J-type.

    Args:
        shock_velocity: Shock velocity (cm/s)
        magnetic_field: Magnetic field (Gauss)
        density: Density (g/cm³)

    Returns:
        True if C-shock, False if J-shock
    """
    c_shock = get_c_shock()
    v_crit = c_shock.critical_velocity(magnetic_field, density)
    return shock_velocity < v_crit


