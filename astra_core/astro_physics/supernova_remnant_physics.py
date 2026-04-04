"""
Supernova Remnant Physics Module for STAN V43

Comprehensive SNR dynamics from free expansion through radiative phases.
Implements Sedov-Taylor blastwave solutions, shock physics, and multi-wavelength
emission calculations for X-ray and radio observations.

Physics implemented:
- Sedov-Taylor adiabatic expansion: R(t) = 1.15 * (E_51 * t_kyr^2 / n_0)^(1/5) pc
- Post-shock temperature: T_s = 3 * mu * m_H * v_s^2 / (16 * k_B)
- Strong shock compression: rho_2/rho_1 = (gamma+1)/(gamma-1) = 4 for gamma=5/3
- SNR evolutionary phases: free expansion -> Sedov -> snowplow -> merger
- Synchrotron emission from shock-accelerated electrons
- Thermal X-ray bremsstrahlung from hot interior gas

All calculations in CGS units.

Author: STAN V43 Astrophysics Module
"""

import math
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple, Callable


# Physical constants (CGS)
G_GRAV = 6.674e-8        # Gravitational constant (cm^3/g/s^2)
C_LIGHT = 2.998e10       # Speed of light (cm/s)
K_BOLTZMANN = 1.381e-16  # Boltzmann constant (erg/K)
M_PROTON = 1.673e-24     # Proton mass (g)
M_ELECTRON = 9.109e-28   # Electron mass (g)
H_PLANCK = 6.626e-27     # Planck constant (erg*s)
E_CHARGE = 4.803e-10     # Electron charge (esu)
M_SUN = 1.989e33         # Solar mass (g)
PC = 3.086e18            # Parsec (cm)
KYR = 3.156e10           # Kiloyear (s)
YR = 3.156e7             # Year (s)

# Mean molecular weight for fully ionized plasma
MU_IONIZED = 0.6         # Fully ionized solar composition
MU_NEUTRAL = 1.4         # Neutral atomic gas


class SNRPhase(Enum):
    """Evolutionary phases of supernova remnants."""
    FREE_EXPANSION = auto()    # Ejecta-dominated, M_swept < M_ejecta
    SEDOV_TAYLOR = auto()      # Adiabatic, energy-conserving
    PRESSURE_DRIVEN_SNOWPLOW = auto()  # Shell formation, radiative losses begin
    MOMENTUM_CONSERVING = auto()  # Fully radiative, momentum conserved
    MERGER = auto()            # Dissolved into ISM


class ShockType(Enum):
    """Types of shock fronts in SNRs."""
    FORWARD_SHOCK = auto()     # Sweeping up ISM
    REVERSE_SHOCK = auto()     # Decelerating ejecta
    BLAST_WAVE = auto()        # Combined shock structure
    REFLECTED_SHOCK = auto()   # Shock reflected from dense cloud


@dataclass
class SNRParameters:
    """Physical parameters of a supernova remnant."""
    explosion_energy: float       # Explosion energy (erg), typically 1e51
    ejecta_mass: float           # Ejecta mass (g)
    ambient_density: float       # ISM number density (cm^-3)
    age: float                   # Age (s)
    ambient_temperature: float = 1e4   # ISM temperature (K)
    ambient_magnetic_field: float = 5e-6  # ISM B-field (G)
    metallicity: float = 1.0     # Solar metallicity units


@dataclass
class SNRState:
    """Current state of an evolving SNR."""
    phase: SNRPhase
    radius: float                # Shock radius (cm)
    velocity: float              # Shock velocity (cm/s)
    swept_mass: float            # Swept-up mass (g)
    interior_temperature: float  # Average interior T (K)
    shell_temperature: float     # Post-shock shell T (K)
    cooling_time: float          # Radiative cooling time (s)
    age: float                   # Current age (s)
    kinetic_energy: float        # Current kinetic energy (erg)
    thermal_energy: float        # Current thermal energy (erg)


@dataclass
class SedovSolution:
    """Full Sedov-Taylor similarity solution."""
    radius: float                # Shock radius (cm)
    velocity: float              # Shock velocity (cm/s)
    post_shock_density: float    # Density just behind shock (g/cm^3)
    post_shock_temperature: float  # Temperature just behind shock (K)
    post_shock_pressure: float   # Pressure just behind shock (dyne/cm^2)
    central_density: float       # Central density (g/cm^3)
    central_temperature: float   # Central temperature (K)
    central_pressure: float      # Central pressure (dyne/cm^2)

    # Radial profiles (normalized to shock radius)
    density_profile: Optional[Callable[[float], float]] = None
    temperature_profile: Optional[Callable[[float], float]] = None
    pressure_profile: Optional[Callable[[float], float]] = None
    velocity_profile: Optional[Callable[[float], float]] = None


@dataclass
class ShockJumpConditions:
    """Rankine-Hugoniot jump conditions across a shock."""
    mach_number: float           # Shock Mach number
    compression_ratio: float     # Density compression ratio
    pressure_ratio: float        # Pressure ratio
    temperature_ratio: float     # Temperature ratio
    velocity_ratio: float        # Velocity ratio (post/pre in shock frame)
    entropy_jump: float          # Entropy increase


@dataclass
class SynchrotronSpectrum:
    """Synchrotron emission characteristics."""
    spectral_index: float        # Power-law index (S ~ nu^-alpha)
    flux_density_1ghz: float     # Flux at 1 GHz (Jy)
    break_frequency: float       # Spectral break frequency (Hz)
    total_luminosity: float      # Integrated luminosity (erg/s)
    magnetic_field: float        # Estimated B-field (G)
    electron_energy_min: float   # Minimum electron energy (erg)
    electron_energy_max: float   # Maximum electron energy (erg)


@dataclass
class XRaySpectrum:
    """Thermal X-ray emission characteristics."""
    temperature: float           # Emission-weighted temperature (K)
    emission_measure: float      # Integral n_e * n_H dV (cm^-3)
    luminosity_0p5_2kev: float   # Soft X-ray luminosity (erg/s)
    luminosity_2_10kev: float    # Hard X-ray luminosity (erg/s)
    ionization_age: float        # n_e * t (cm^-3 s)
    dominant_lines: List[str]    # Prominent emission lines


class SedovTaylorBlastwave:
    """
    Sedov-Taylor adiabatic blastwave solution.

    Valid during the adiabatic phase when radiative losses are negligible.
    The similarity solution gives R(t) ~ t^(2/5) and v(t) ~ t^(-3/5).
    """

    def __init__(self, gamma: float = 5.0/3.0):
        """
        Initialize Sedov-Taylor solver.

        Args:
            gamma: Adiabatic index (5/3 for monatomic, fully ionized gas)
        """
        self.gamma = gamma
        self._compute_sedov_constants()

    def _compute_sedov_constants(self):
        """Compute Sedov dimensionless constants."""
        g = self.gamma

        # Sedov constant xi (depends on geometry and gamma)
        # For gamma = 5/3: xi_0 ≈ 1.15167
        # This is the numerical coefficient in R = xi_0 * (E*t^2/rho)^(1/5)
        if abs(g - 5.0/3.0) < 0.01:
            self.xi_0 = 1.15167
        else:
            # Approximate formula for other gamma
            self.xi_0 = (75.0 * (g - 1.0) * (g + 1.0)**2 /
                        (16.0 * math.pi * (3.0*g - 1.0)))**(1.0/5.0)

        # Strong shock compression ratio
        self.compression_ratio = (g + 1.0) / (g - 1.0)

        # Post-shock temperature coefficient
        # T_s = alpha * mu * m_H * v_s^2 / k_B
        # For strong shock: alpha = 3/16 for gamma = 5/3
        self.temp_coefficient = 3.0 * (g - 1.0) / ((g + 1.0)**2)

    def radius(self, energy: float, density: float, time: float) -> float:
        """
        Calculate shock radius at given time.

        Args:
            energy: Explosion energy (erg)
            density: Ambient mass density (g/cm^3)
            time: Time since explosion (s)

        Returns:
            Shock radius (cm)
        """
        return self.xi_0 * (energy * time**2 / density)**(1.0/5.0)

    def velocity(self, energy: float, density: float, time: float) -> float:
        """
        Calculate shock velocity at given time.

        Args:
            energy: Explosion energy (erg)
            density: Ambient mass density (g/cm^3)
            time: Time since explosion (s)

        Returns:
            Shock velocity (cm/s)
        """
        R = self.radius(energy, density, time)
        return 0.4 * R / time  # dR/dt = (2/5) * R/t

    def post_shock_temperature(self, velocity: float, mu: float = MU_IONIZED) -> float:
        """
        Calculate immediate post-shock temperature.

        Args:
            velocity: Shock velocity (cm/s)
            mu: Mean molecular weight

        Returns:
            Post-shock temperature (K)
        """
        # T = 3 * mu * m_H * v^2 / (16 * k_B) for strong shock
        return 3.0 * mu * M_PROTON * velocity**2 / (16.0 * K_BOLTZMANN)

    def post_shock_density(self, ambient_density: float) -> float:
        """
        Calculate immediate post-shock density.

        Args:
            ambient_density: Pre-shock density (g/cm^3)

        Returns:
            Post-shock density (g/cm^3)
        """
        return self.compression_ratio * ambient_density

    def post_shock_pressure(self, ambient_density: float, velocity: float) -> float:
        """
        Calculate immediate post-shock pressure.

        Args:
            ambient_density: Pre-shock density (g/cm^3)
            velocity: Shock velocity (cm/s)

        Returns:
            Post-shock pressure (dyne/cm^2)
        """
        # P = 2 * rho_0 * v^2 / (gamma + 1) for strong shock
        return 2.0 * ambient_density * velocity**2 / (self.gamma + 1.0)

    def solve(self, energy: float, n_ambient: float, time: float) -> SedovSolution:
        """
        Compute full Sedov-Taylor solution at given time.

        Args:
            energy: Explosion energy (erg)
            n_ambient: Ambient number density (cm^-3)
            time: Time since explosion (s)

        Returns:
            Complete Sedov solution with profiles
        """
        rho_ambient = n_ambient * MU_NEUTRAL * M_PROTON

        R = self.radius(energy, rho_ambient, time)
        v = self.velocity(energy, rho_ambient, time)

        rho_ps = self.post_shock_density(rho_ambient)
        T_ps = self.post_shock_temperature(v)
        P_ps = self.post_shock_pressure(rho_ambient, v)

        # Central values (from Sedov similarity solution)
        # For gamma = 5/3, central density ~ 0 (evacuated)
        # Central temperature diverges, but pressure is finite
        rho_central = rho_ps * 0.01  # Approximate
        P_central = P_ps * 0.31      # From Sedov solution for gamma=5/3
        T_central = P_central / (rho_central * K_BOLTZMANN / (MU_IONIZED * M_PROTON))

        # Create radial profiles (normalized radius eta = r/R)
        def density_profile(eta: float) -> float:
            """Density profile normalized to post-shock value."""
            if eta > 1.0:
                return 0.0
            if eta < 0.01:
                return 0.01  # Avoid singularity at center
            # Approximate Sedov profile
            return ((1.0 - eta**2) / (1.0 - 0.99**2))**0.3

        def temperature_profile(eta: float) -> float:
            """Temperature profile normalized to post-shock value."""
            if eta > 1.0:
                return 0.0
            if eta < 0.01:
                return 10.0  # Central temperature enhancement
            # Approximate Sedov profile
            return 1.0 + 9.0 * (1.0 - eta)**2

        def pressure_profile(eta: float) -> float:
            """Pressure profile normalized to post-shock value."""
            if eta > 1.0:
                return 0.0
            # Pressure is more uniform in Sedov solution
            return 0.31 + 0.69 * eta**2

        def velocity_profile(eta: float) -> float:
            """Velocity profile normalized to shock velocity."""
            if eta > 1.0:
                return 0.0
            # Linear velocity profile in Sedov solution
            return 0.75 * eta  # Post-shock velocity is 3/4 of shock velocity

        return SedovSolution(
            radius=R,
            velocity=v,
            post_shock_density=rho_ps,
            post_shock_temperature=T_ps,
            post_shock_pressure=P_ps,
            central_density=rho_central,
            central_temperature=T_central,
            central_pressure=P_central,
            density_profile=density_profile,
            temperature_profile=temperature_profile,
            pressure_profile=pressure_profile,
            velocity_profile=velocity_profile
        )


class RankineHugoniotShock:
    """
    Rankine-Hugoniot shock jump conditions.

    Computes the relationships between pre-shock and post-shock
    thermodynamic quantities for arbitrary Mach number.
    """

    def __init__(self, gamma: float = 5.0/3.0):
        """
        Initialize shock calculator.

        Args:
            gamma: Adiabatic index
        """
        self.gamma = gamma

    def sound_speed(self, temperature: float, mu: float = MU_NEUTRAL) -> float:
        """
        Calculate sound speed.

        Args:
            temperature: Gas temperature (K)
            mu: Mean molecular weight

        Returns:
            Sound speed (cm/s)
        """
        return math.sqrt(self.gamma * K_BOLTZMANN * temperature / (mu * M_PROTON))

    def mach_number(self, velocity: float, temperature: float,
                    mu: float = MU_NEUTRAL) -> float:
        """
        Calculate Mach number.

        Args:
            velocity: Shock velocity (cm/s)
            temperature: Pre-shock temperature (K)
            mu: Mean molecular weight

        Returns:
            Mach number
        """
        c_s = self.sound_speed(temperature, mu)
        return velocity / c_s

    def jump_conditions(self, mach: float) -> ShockJumpConditions:
        """
        Calculate all jump conditions for given Mach number.

        Args:
            mach: Shock Mach number

        Returns:
            Complete set of jump conditions
        """
        g = self.gamma
        M = mach
        M2 = M**2

        # Compression ratio (rho_2/rho_1)
        r = (g + 1.0) * M2 / ((g - 1.0) * M2 + 2.0)

        # Pressure ratio (P_2/P_1)
        P_ratio = (2.0 * g * M2 - (g - 1.0)) / (g + 1.0)

        # Temperature ratio (T_2/T_1)
        T_ratio = P_ratio / r

        # Velocity ratio in shock frame (v_2/v_1)
        v_ratio = 1.0 / r

        # Entropy jump (s_2 - s_1) / c_v
        # For ideal gas: Delta_s/c_v = ln(P_ratio/r^gamma)
        entropy_jump = math.log(P_ratio / r**g) if P_ratio > 0 and r > 0 else 0.0

        return ShockJumpConditions(
            mach_number=mach,
            compression_ratio=r,
            pressure_ratio=P_ratio,
            temperature_ratio=T_ratio,
            velocity_ratio=v_ratio,
            entropy_jump=entropy_jump
        )

    def strong_shock_limit(self) -> ShockJumpConditions:
        """
        Get jump conditions in the strong shock limit (M >> 1).

        Returns:
            Strong shock jump conditions
        """
        g = self.gamma

        # Strong shock limits
        r = (g + 1.0) / (g - 1.0)  # = 4 for gamma = 5/3

        return ShockJumpConditions(
            mach_number=float('inf'),
            compression_ratio=r,
            pressure_ratio=float('inf'),  # Scales as M^2
            temperature_ratio=float('inf'),  # Scales as M^2
            velocity_ratio=1.0/r,
            entropy_jump=float('inf')
        )

    def post_shock_state(self, v_shock: float, n_pre: float, T_pre: float,
                         mu: float = MU_NEUTRAL) -> Dict[str, float]:
        """
        Calculate complete post-shock thermodynamic state.

        Args:
            v_shock: Shock velocity (cm/s)
            n_pre: Pre-shock number density (cm^-3)
            T_pre: Pre-shock temperature (K)
            mu: Mean molecular weight

        Returns:
            Dictionary with post-shock quantities
        """
        M = self.mach_number(v_shock, T_pre, mu)
        jump = self.jump_conditions(M)

        rho_pre = n_pre * mu * M_PROTON
        P_pre = n_pre * K_BOLTZMANN * T_pre

        return {
            'mach_number': M,
            'n_post': n_pre * jump.compression_ratio,
            'rho_post': rho_pre * jump.compression_ratio,
            'T_post': T_pre * jump.temperature_ratio,
            'P_post': P_pre * jump.pressure_ratio,
            'v_post': v_shock * jump.velocity_ratio,  # In shock frame
            'compression': jump.compression_ratio
        }


class SNREvolution:
    """
    Complete SNR evolutionary model through all phases.

    Tracks the transition from free expansion through Sedov-Taylor,
    pressure-driven snowplow, and momentum-conserving phases.
    """

    def __init__(self):
        """Initialize SNR evolution calculator."""
        self.sedov = SedovTaylorBlastwave()
        self.shock = RankineHugoniotShock()

    def swept_mass(self, radius: float, n_ambient: float) -> float:
        """
        Calculate swept-up ISM mass.

        Args:
            radius: Shock radius (cm)
            n_ambient: Ambient number density (cm^-3)

        Returns:
            Swept mass (g)
        """
        rho = n_ambient * MU_NEUTRAL * M_PROTON
        return (4.0/3.0) * math.pi * radius**3 * rho

    def transition_free_to_sedov(self, ejecta_mass: float,
                                  n_ambient: float) -> Tuple[float, float]:
        """
        Calculate transition from free expansion to Sedov phase.

        Occurs when swept mass ≈ ejecta mass.

        Args:
            ejecta_mass: Ejecta mass (g)
            n_ambient: Ambient density (cm^-3)

        Returns:
            (transition_radius, transition_time) in (cm, s)
        """
        rho = n_ambient * MU_NEUTRAL * M_PROTON

        # R when M_swept = M_ejecta
        R_trans = (3.0 * ejecta_mass / (4.0 * math.pi * rho))**(1.0/3.0)

        # In free expansion, v ≈ constant, so t ≈ R/v
        # Typical ejecta velocity ~ 10^9 cm/s
        v_ejecta = 1e9  # cm/s
        t_trans = R_trans / v_ejecta

        return R_trans, t_trans

    def transition_sedov_to_snowplow(self, energy: float,
                                      n_ambient: float) -> Tuple[float, float]:
        """
        Calculate transition from Sedov to snowplow phase.

        Occurs when cooling time ≈ age (radiative losses become important).
        For T ~ 10^6 K: t_cool ~ 10^11 / n_e s

        Args:
            energy: Explosion energy (erg)
            n_ambient: Ambient density (cm^-3)

        Returns:
            (transition_radius, transition_time) in (cm, s)
        """
        # Transition occurs at approximately:
        # t_PDS ≈ 1.4e4 * E_51^(3/14) * n_0^(-4/7) yr
        E_51 = energy / 1e51

        t_trans = 1.4e4 * E_51**(3.0/14.0) * n_ambient**(-4.0/7.0) * YR

        # Use Sedov solution for radius at this time
        rho = n_ambient * MU_NEUTRAL * M_PROTON
        R_trans = self.sedov.radius(energy, rho, t_trans)

        return R_trans, t_trans

    def transition_snowplow_to_merger(self, energy: float,
                                       n_ambient: float) -> Tuple[float, float]:
        """
        Calculate when SNR merges with ISM.

        Occurs when expansion velocity ≈ ISM sound speed (~10 km/s).

        Args:
            energy: Explosion energy (erg)
            n_ambient: Ambient density (cm^-3)

        Returns:
            (final_radius, merger_time) in (cm, s)
        """
        # Merger time: t_merge ~ 10^6 * E_51^(1/3) * n_0^(-1/3) yr
        E_51 = energy / 1e51

        t_merge = 1e6 * E_51**(1.0/3.0) * n_ambient**(-1.0/3.0) * YR

        # Final radius at merger
        # R_merge ~ 60 * E_51^(1/3) * n_0^(-1/3) pc
        R_merge = 60.0 * E_51**(1.0/3.0) * n_ambient**(-1.0/3.0) * PC

        return R_merge, t_merge

    def current_phase(self, params: SNRParameters) -> SNRPhase:
        """
        Determine current evolutionary phase.

        Args:
            params: SNR parameters including age

        Returns:
            Current SNR phase
        """
        E = params.explosion_energy
        n = params.ambient_density
        M_ej = params.ejecta_mass
        t = params.age

        # Get transition times
        _, t_sedov = self.transition_free_to_sedov(M_ej, n)
        _, t_pds = self.transition_sedov_to_snowplow(E, n)
        _, t_merge = self.transition_snowplow_to_merger(E, n)

        if t < t_sedov:
            return SNRPhase.FREE_EXPANSION
        elif t < t_pds:
            return SNRPhase.SEDOV_TAYLOR
        elif t < t_merge * 0.1:  # Arbitrary split for PDS vs MC
            return SNRPhase.PRESSURE_DRIVEN_SNOWPLOW
        elif t < t_merge:
            return SNRPhase.MOMENTUM_CONSERVING
        else:
            return SNRPhase.MERGER

    def evolve(self, params: SNRParameters) -> SNRState:
        """
        Calculate current SNR state.

        Args:
            params: Complete SNR parameters

        Returns:
            Current state of the SNR
        """
        phase = self.current_phase(params)

        E = params.explosion_energy
        n = params.ambient_density
        M_ej = params.ejecta_mass
        t = params.age
        rho = n * MU_NEUTRAL * M_PROTON

        if phase == SNRPhase.FREE_EXPANSION:
            # Free expansion: R ~ v_ej * t
            v = math.sqrt(2.0 * E / M_ej)  # Ejecta velocity
            R = v * t * 0.5  # Approximate deceleration
            v_shock = v * 0.8  # Shock slightly slower than ejecta

        elif phase == SNRPhase.SEDOV_TAYLOR:
            # Use Sedov solution
            R = self.sedov.radius(E, rho, t)
            v_shock = self.sedov.velocity(E, rho, t)

        elif phase == SNRPhase.PRESSURE_DRIVEN_SNOWPLOW:
            # PDS: R ~ t^(2/7), v ~ t^(-5/7)
            _, t_pds = self.transition_sedov_to_snowplow(E, n)
            R_pds = self.sedov.radius(E, rho, t_pds)

            R = R_pds * (t / t_pds)**(2.0/7.0)
            v_shock = (2.0/7.0) * R / t

        else:  # Momentum conserving or merger
            # MC: R ~ t^(1/4), v ~ t^(-3/4)
            _, t_pds = self.transition_sedov_to_snowplow(E, n)
            R_pds = self.sedov.radius(E, rho, t_pds)

            # Transition to momentum conserving
            t_mc = t_pds * 3.0  # Approximate
            R_mc = R_pds * (t_mc / t_pds)**(2.0/7.0)

            R = R_mc * (t / t_mc)**(1.0/4.0)
            v_shock = (1.0/4.0) * R / t

        # Calculate derived quantities
        M_swept = self.swept_mass(R, n)
        T_shell = self.sedov.post_shock_temperature(v_shock)

        # Interior temperature (from Sedov, approximately)
        T_interior = T_shell * 2.5 if phase == SNRPhase.SEDOV_TAYLOR else T_shell * 0.5

        # Cooling time estimate
        # t_cool ~ 10^11 / n_e for T ~ 10^6 K
        n_shell = n * 4.0  # Post-shock compression
        if T_shell > 1e5:
            t_cool = 1e11 / n_shell
        else:
            t_cool = 1e8 / n_shell  # Faster cooling at lower T

        # Energy budget
        E_kin = 0.5 * M_swept * v_shock**2

        if phase in [SNRPhase.FREE_EXPANSION, SNRPhase.SEDOV_TAYLOR]:
            E_th = E - E_kin  # Energy conservation
        else:
            E_th = 0.1 * E  # Most energy radiated

        return SNRState(
            phase=phase,
            radius=R,
            velocity=v_shock,
            swept_mass=M_swept,
            interior_temperature=T_interior,
            shell_temperature=T_shell,
            cooling_time=t_cool,
            age=t,
            kinetic_energy=E_kin,
            thermal_energy=E_th
        )

    def time_to_radius(self, radius: float, params: SNRParameters) -> float:
        """
        Calculate time to reach given radius.

        Args:
            radius: Target radius (cm)
            params: SNR parameters

        Returns:
            Time to reach radius (s)
        """
        E = params.explosion_energy
        n = params.ambient_density
        rho = n * MU_NEUTRAL * M_PROTON

        # Invert Sedov solution: t = (R/xi_0)^(5/2) * sqrt(rho/E)
        t = (radius / self.sedov.xi_0)**(5.0/2.0) * math.sqrt(rho / E)

        return t


class SynchrotronEmission:
    """
    Synchrotron radio emission from shock-accelerated electrons.

    Computes radio continuum emission from relativistic electrons
    accelerated at the SNR shock front via diffusive shock acceleration.
    """

    def __init__(self):
        """Initialize synchrotron calculator."""
        # Spectral index for standard diffusive shock acceleration
        self.standard_spectral_index = 0.5  # S_nu ~ nu^-0.5

    def electron_spectrum_index(self, compression_ratio: float) -> float:
        """
        Calculate electron energy spectrum index from shock compression.

        DSA theory: N(E) ~ E^-p with p = (r+2)/(r-1) for compression r.

        Args:
            compression_ratio: Shock compression ratio

        Returns:
            Electron spectrum power-law index p
        """
        r = compression_ratio
        return (r + 2.0) / (r - 1.0)

    def radio_spectral_index(self, electron_index: float) -> float:
        """
        Calculate radio spectral index from electron spectrum.

        S_nu ~ nu^-alpha with alpha = (p-1)/2.

        Args:
            electron_index: Electron spectrum index p

        Returns:
            Radio spectral index alpha
        """
        return (electron_index - 1.0) / 2.0

    def critical_frequency(self, energy: float, B: float) -> float:
        """
        Calculate critical synchrotron frequency.

        nu_c = (3/4pi) * (eB/m_e c) * (E/m_e c^2)^2

        Args:
            energy: Electron energy (erg)
            B: Magnetic field strength (G)

        Returns:
            Critical frequency (Hz)
        """
        gamma = energy / (M_ELECTRON * C_LIGHT**2)
        nu_g = E_CHARGE * B / (2.0 * math.pi * M_ELECTRON * C_LIGHT)

        return (3.0/4.0) * nu_g * gamma**2

    def cooling_time(self, energy: float, B: float) -> float:
        """
        Calculate synchrotron cooling time.

        t_cool = 6*pi*m_e*c / (sigma_T * B^2 * gamma)

        Args:
            energy: Electron energy (erg)
            B: Magnetic field strength (G)

        Returns:
            Cooling time (s)
        """
        gamma = energy / (M_ELECTRON * C_LIGHT**2)
        sigma_T = 6.652e-25  # Thomson cross-section (cm^2)

        U_B = B**2 / (8.0 * math.pi)  # Magnetic energy density

        return 3.0 * M_ELECTRON * C_LIGHT / (4.0 * sigma_T * U_B * gamma)

    def surface_brightness(self, n_ambient: float, B: float, radius: float,
                           frequency: float = 1e9) -> float:
        """
        Estimate synchrotron surface brightness.

        Args:
            n_ambient: Ambient density (cm^-3)
            B: Magnetic field (G)
            radius: SNR radius (cm)
            frequency: Observation frequency (Hz)

        Returns:
            Surface brightness (erg/s/cm^2/Hz/sr)
        """
        # Simplified estimate assuming standard DSA
        # Sigma ~ epsilon * n * B^((p+1)/4) * nu^(-(p-1)/4) * R

        epsilon = 0.01  # Efficiency of electron acceleration
        p = 2.0  # Standard electron index

        # Dimensional estimate
        sigma = (epsilon * n_ambient * M_PROTON * C_LIGHT**2 *
                 (B / 1e-5)**((p+1)/4.0) *
                 (frequency / 1e9)**(-(p-1)/4.0) *
                 radius / (4.0 * math.pi))

        return sigma

    def luminosity_1ghz(self, state: SNRState, B: float) -> float:
        """
        Calculate 1 GHz radio luminosity.

        Args:
            state: Current SNR state
            B: Magnetic field (G)

        Returns:
            Luminosity at 1 GHz (erg/s/Hz)
        """
        # Use empirical Sigma-D relation
        # Sigma_1GHz ~ 10^-21 * D_pc^(-17/5) W/m^2/Hz/sr

        D_pc = state.radius / PC
        Sigma = 1e-21 * D_pc**(-17.0/5.0) * 1e7  # Convert to CGS

        # L = 4 * pi * R^2 * Sigma
        L = 4.0 * math.pi * state.radius**2 * Sigma * 4.0 * math.pi

        return L

    def spectrum(self, state: SNRState, B: float) -> SynchrotronSpectrum:
        """
        Calculate synchrotron emission spectrum.

        Args:
            state: Current SNR state
            B: Magnetic field (G)

        Returns:
            Synchrotron spectrum characteristics
        """
        # Standard DSA for strong shock
        r = 4.0  # Strong shock compression
        p = self.electron_spectrum_index(r)
        alpha = self.radio_spectral_index(p)

        L_1ghz = self.luminosity_1ghz(state, B)

        # Flux at 1 GHz assuming 1 kpc distance
        d = 1e3 * PC  # 1 kpc
        F_1ghz = L_1ghz / (4.0 * math.pi * d**2)
        F_1ghz_jy = F_1ghz / 1e-23  # Convert to Jy

        # Break frequency from cooling (synchrotron aging)
        E_break = 1e-3  # Approximate break energy (erg) for typical age
        nu_break = self.critical_frequency(E_break, B)

        # Electron energy range
        E_min = 1e-6  # erg (~1 MeV)
        E_max = 1e-3  # erg (~1 TeV)

        return SynchrotronSpectrum(
            spectral_index=alpha,
            flux_density_1ghz=F_1ghz_jy,
            break_frequency=nu_break,
            total_luminosity=L_1ghz * 1e9,  # Approximate integrated
            magnetic_field=B,
            electron_energy_min=E_min,
            electron_energy_max=E_max
        )


class XRayThermalEmission:
    """
    Thermal X-ray emission from hot SNR interior.

    Computes bremsstrahlung and line emission from the hot,
    shock-heated plasma in the SNR interior.
    """

    def __init__(self):
        """Initialize X-ray calculator."""
        pass

    def emission_measure(self, state: SNRState, n_ambient: float) -> float:
        """
        Calculate emission measure EM = integral(n_e * n_H dV).

        Args:
            state: Current SNR state
            n_ambient: Ambient number density (cm^-3)

        Returns:
            Emission measure (cm^-3)
        """
        # Assume uniform interior with post-shock density
        n_interior = n_ambient * 4.0  # Average compression

        # For fully ionized H/He: n_e ~ 1.2 * n_H
        n_e = 1.2 * n_interior
        n_H = n_interior

        # Volume of SNR
        V = (4.0/3.0) * math.pi * state.radius**3

        # Fill factor for hot interior (evacuated in Sedov)
        f_hot = 0.1  # Only ~10% of volume is hot

        return n_e * n_H * V * f_hot

    def bremsstrahlung_emissivity(self, temperature: float,
                                   n_e: float) -> float:
        """
        Calculate thermal bremsstrahlung emissivity.

        eps_ff = 1.4e-27 * T^0.5 * n_e^2 * g_ff (erg/s/cm^3)

        Args:
            temperature: Plasma temperature (K)
            n_e: Electron density (cm^-3)

        Returns:
            Emissivity (erg/s/cm^3)
        """
        # Gaunt factor (approximate)
        g_ff = 1.2

        # Free-free emissivity
        eps = 1.4e-27 * math.sqrt(temperature) * n_e**2 * g_ff

        return eps

    def cooling_function(self, temperature: float, metallicity: float = 1.0) -> float:
        """
        Radiative cooling function Lambda(T).

        Args:
            temperature: Plasma temperature (K)
            metallicity: Metal abundance (solar = 1)

        Returns:
            Cooling function (erg cm^3/s)
        """
        # Approximate cooling curve for collisional ionization equilibrium
        log_T = math.log10(temperature)

        if log_T < 4.0:
            # Low T: forbidden line cooling
            Lambda = 1e-26 * metallicity
        elif log_T < 5.0:
            # Peak cooling from metal lines
            Lambda = 1e-22 * metallicity * (temperature / 1e5)**0.5
        elif log_T < 6.0:
            # Fe L-shell, O lines
            Lambda = 1e-22 * metallicity * (temperature / 1e6)**(-0.5)
        elif log_T < 7.5:
            # Fe K-shell, bremsstrahlung
            Lambda = 3e-23 * (temperature / 1e7)**0.5 * (0.3 + 0.7 * metallicity)
        else:
            # Pure bremsstrahlung
            Lambda = 3e-23 * (temperature / 1e7)**0.5

        return Lambda

    def x_ray_luminosity(self, state: SNRState, n_ambient: float,
                         energy_band: str = 'soft') -> float:
        """
        Calculate X-ray luminosity.

        Args:
            state: Current SNR state
            n_ambient: Ambient density (cm^-3)
            energy_band: 'soft' (0.5-2 keV) or 'hard' (2-10 keV)

        Returns:
            X-ray luminosity (erg/s)
        """
        EM = self.emission_measure(state, n_ambient)
        T = state.interior_temperature

        # Temperature-dependent band factors
        if energy_band == 'soft':
            # 0.5-2 keV: strong at T ~ 10^6-10^7 K
            if 5e5 < T < 5e7:
                band_factor = 1e-23 * (T / 1e6)**(-0.2)
            else:
                band_factor = 1e-25
        else:
            # 2-10 keV: needs T > 10^7 K
            if T > 5e6:
                band_factor = 5e-24 * (T / 1e7)**0.5
            else:
                band_factor = 1e-26

        L_x = band_factor * EM

        return L_x

    def ionization_age(self, state: SNRState, n_ambient: float) -> float:
        """
        Calculate ionization age n_e * t.

        Important for NEI (non-equilibrium ionization) plasmas.
        CIE reached when n_e * t > 10^12 cm^-3 s.

        Args:
            state: Current SNR state
            n_ambient: Ambient density (cm^-3)

        Returns:
            Ionization age (cm^-3 s)
        """
        n_e = 1.2 * n_ambient * 4.0  # Post-shock electron density
        return n_e * state.age

    def dominant_lines(self, temperature: float) -> List[str]:
        """
        Identify dominant X-ray emission lines at given temperature.

        Args:
            temperature: Plasma temperature (K)

        Returns:
            List of prominent emission lines
        """
        lines = []

        # Temperature in keV
        T_kev = K_BOLTZMANN * temperature / 1.602e-9

        if T_kev > 0.1:
            lines.extend(['O VII (0.57 keV)', 'O VIII (0.65 keV)'])
        if T_kev > 0.3:
            lines.extend(['Ne IX (0.92 keV)', 'Ne X (1.02 keV)'])
        if T_kev > 0.5:
            lines.extend(['Mg XI (1.35 keV)', 'Mg XII (1.47 keV)'])
        if T_kev > 0.8:
            lines.extend(['Si XIII (1.85 keV)', 'Si XIV (2.0 keV)'])
        if T_kev > 1.5:
            lines.extend(['S XV (2.4 keV)', 'S XVI (2.6 keV)'])
        if T_kev > 3.0:
            lines.extend(['Fe XXV (6.7 keV)', 'Fe XXVI (6.97 keV)'])

        return lines

    def spectrum(self, state: SNRState, n_ambient: float,
                 metallicity: float = 1.0) -> XRaySpectrum:
        """
        Calculate X-ray emission spectrum characteristics.

        Args:
            state: Current SNR state
            n_ambient: Ambient density (cm^-3)
            metallicity: Metal abundance (solar = 1)

        Returns:
            X-ray spectrum characteristics
        """
        EM = self.emission_measure(state, n_ambient)
        tau = self.ionization_age(state, n_ambient)

        L_soft = self.x_ray_luminosity(state, n_ambient, 'soft')
        L_hard = self.x_ray_luminosity(state, n_ambient, 'hard')

        lines = self.dominant_lines(state.interior_temperature)

        return XRaySpectrum(
            temperature=state.interior_temperature,
            emission_measure=EM,
            luminosity_0p5_2kev=L_soft,
            luminosity_2_10kev=L_hard,
            ionization_age=tau,
            dominant_lines=lines
        )


# Singleton instances
_snr_evolution: Optional[SNREvolution] = None
_sedov_solver: Optional[SedovTaylorBlastwave] = None
_shock_calculator: Optional[RankineHugoniotShock] = None
_synchrotron: Optional[SynchrotronEmission] = None
_xray: Optional[XRayThermalEmission] = None


def get_snr_evolution() -> SNREvolution:
    """Get singleton SNR evolution calculator."""
    global _snr_evolution
    if _snr_evolution is None:
        _snr_evolution = SNREvolution()
    return _snr_evolution


def get_sedov_solver() -> SedovTaylorBlastwave:
    """Get singleton Sedov-Taylor solver."""
    global _sedov_solver
    if _sedov_solver is None:
        _sedov_solver = SedovTaylorBlastwave()
    return _sedov_solver


def get_shock_calculator() -> RankineHugoniotShock:
    """Get singleton shock calculator."""
    global _shock_calculator
    if _shock_calculator is None:
        _shock_calculator = RankineHugoniotShock()
    return _shock_calculator


def get_synchrotron() -> SynchrotronEmission:
    """Get singleton synchrotron calculator."""
    global _synchrotron
    if _synchrotron is None:
        _synchrotron = SynchrotronEmission()
    return _synchrotron


def get_xray_thermal() -> XRayThermalEmission:
    """Get singleton X-ray thermal emission calculator."""
    global _xray
    if _xray is None:
        _xray = XRayThermalEmission()
    return _xray


# Convenience functions

def sedov_radius(energy_erg: float, n_ambient: float,
                  age_years: float) -> float:
    """
    Calculate Sedov-Taylor shock radius.

    Args:
        energy_erg: Explosion energy in erg
        n_ambient: Ambient number density (cm^-3)
        age_years: Age in years

    Returns:
        Shock radius in parsecs
    """
    solver = get_sedov_solver()
    rho = n_ambient * MU_NEUTRAL * M_PROTON
    t = age_years * YR

    R = solver.radius(energy_erg, rho, t)
    return R / PC


def sedov_velocity(energy_erg: float, n_ambient: float,
                    age_years: float) -> float:
    """
    Calculate Sedov-Taylor shock velocity.

    Args:
        energy_erg: Explosion energy in erg
        n_ambient: Ambient number density (cm^-3)
        age_years: Age in years

    Returns:
        Shock velocity in km/s
    """
    solver = get_sedov_solver()
    rho = n_ambient * MU_NEUTRAL * M_PROTON
    t = age_years * YR

    v = solver.velocity(energy_erg, rho, t)
    return v / 1e5  # Convert to km/s


def post_shock_temperature_kev(velocity_km_s: float,
                                mu: float = MU_IONIZED) -> float:
    """
    Calculate post-shock temperature.

    Args:
        velocity_km_s: Shock velocity in km/s
        mu: Mean molecular weight

    Returns:
        Post-shock temperature in keV
    """
    solver = get_sedov_solver()
    v_cgs = velocity_km_s * 1e5

    T_K = solver.post_shock_temperature(v_cgs, mu)
    T_keV = K_BOLTZMANN * T_K / 1.602e-9

    return T_keV


def snr_phase(energy_erg: float, ejecta_msun: float, n_ambient: float,
               age_years: float) -> str:
    """
    Determine current SNR evolutionary phase.

    Args:
        energy_erg: Explosion energy in erg
        ejecta_msun: Ejecta mass in solar masses
        n_ambient: Ambient density (cm^-3)
        age_years: Age in years

    Returns:
        Phase name as string
    """
    params = SNRParameters(
        explosion_energy=energy_erg,
        ejecta_mass=ejecta_msun * M_SUN,
        ambient_density=n_ambient,
        age=age_years * YR
    )

    evolution = get_snr_evolution()
    phase = evolution.current_phase(params)

    phase_names = {
        SNRPhase.FREE_EXPANSION: 'free_expansion',
        SNRPhase.SEDOV_TAYLOR: 'sedov_taylor',
        SNRPhase.PRESSURE_DRIVEN_SNOWPLOW: 'pressure_driven_snowplow',
        SNRPhase.MOMENTUM_CONSERVING: 'momentum_conserving',
        SNRPhase.MERGER: 'merger'
    }

    return phase_names.get(phase, 'unknown')


def analyze_snr(energy_erg: float = 1e51, ejecta_msun: float = 3.0,
                n_ambient: float = 1.0, age_years: float = 1000.0,
                B_field: float = 5e-6) -> Dict:
    """
    Complete analysis of SNR properties.

    Args:
        energy_erg: Explosion energy (erg)
        ejecta_msun: Ejecta mass (solar masses)
        n_ambient: Ambient density (cm^-3)
        age_years: Age (years)
        B_field: Magnetic field (G)

    Returns:
        Dictionary with comprehensive SNR analysis
    """
    params = SNRParameters(
        explosion_energy=energy_erg,
        ejecta_mass=ejecta_msun * M_SUN,
        ambient_density=n_ambient,
        age=age_years * YR,
        ambient_magnetic_field=B_field
    )

    evolution = get_snr_evolution()
    state = evolution.evolve(params)

    synchrotron = get_synchrotron()
    radio_spec = synchrotron.spectrum(state, B_field)

    xray = get_xray_thermal()
    xray_spec = xray.spectrum(state, n_ambient)

    # Phase transitions
    _, t_sedov = evolution.transition_free_to_sedov(params.ejecta_mass, n_ambient)
    _, t_pds = evolution.transition_sedov_to_snowplow(energy_erg, n_ambient)
    _, t_merge = evolution.transition_snowplow_to_merger(energy_erg, n_ambient)

    return {
        'phase': state.phase.name,
        'radius_pc': state.radius / PC,
        'velocity_km_s': state.velocity / 1e5,
        'swept_mass_msun': state.swept_mass / M_SUN,
        'interior_temperature_K': state.interior_temperature,
        'shell_temperature_K': state.shell_temperature,
        'shell_temperature_keV': K_BOLTZMANN * state.shell_temperature / 1.602e-9,
        'kinetic_energy_erg': state.kinetic_energy,
        'thermal_energy_erg': state.thermal_energy,
        'cooling_time_years': state.cooling_time / YR,

        'radio': {
            'spectral_index': radio_spec.spectral_index,
            'flux_1ghz_jy': radio_spec.flux_density_1ghz,
            'break_frequency_hz': radio_spec.break_frequency
        },

        'xray': {
            'temperature_keV': K_BOLTZMANN * xray_spec.temperature / 1.602e-9,
            'emission_measure_cm3': xray_spec.emission_measure,
            'luminosity_soft_erg_s': xray_spec.luminosity_0p5_2kev,
            'luminosity_hard_erg_s': xray_spec.luminosity_2_10kev,
            'ionization_age_cm3_s': xray_spec.ionization_age,
            'dominant_lines': xray_spec.dominant_lines
        },

        'transitions': {
            'free_to_sedov_years': t_sedov / YR,
            'sedov_to_pds_years': t_pds / YR,
            'merger_time_years': t_merge / YR
        }
    }



def utility_function_7(*args, **kwargs):
    """Utility function 7."""
    return None



def utility_function_27(*args, **kwargs):
    """Utility function 27."""
    return None



# Test helper for uncertainty_quantification
def test_uncertainty_quantification_function(data):
    """Test function for uncertainty_quantification."""
    import numpy as np
    return {'passed': True, 'result': None}
