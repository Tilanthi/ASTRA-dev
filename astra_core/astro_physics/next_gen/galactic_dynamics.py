"""
Galactic Dynamics Module

Stellar dynamics, orbit integration, chemical evolution,
and stellar stream analysis.

Date: 2025-12-15
"""

import numpy as np
from typing import List, Dict, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import warnings

# Physical constants (CGS and galactic units)
G_GRAV = 6.674e-8  # cm^3/g/s^2
M_SUN = 1.989e33  # g
PC = 3.086e18  # cm
KPC = 3.086e21  # cm
KM_S = 1e5  # cm/s
GYR = 3.156e16  # s
M_PROTON = 1.673e-24  # g

# Galactic units: 1 kpc, 1 km/s, 1 M_sun
# G = 4.302e-6 kpc (km/s)^2 / M_sun
G_GALACTIC = 4.302e-6


@dataclass
class PhaseSpacePoint:
    """6D phase space position"""
    x: float  # kpc
    y: float  # kpc
    z: float  # kpc
    vx: float  # km/s
    vy: float  # km/s
    vz: float  # km/s

    def position(self) -> np.ndarray:
        return np.array([self.x, self.y, self.z])

    def velocity(self) -> np.ndarray:
        return np.array([self.vx, self.vy, self.vz])

    def r(self) -> float:
        return np.sqrt(self.x**2 + self.y**2 + self.z**2)

    def R(self) -> float:
        return np.sqrt(self.x**2 + self.y**2)


@dataclass
class Orbit:
    """Container for integrated orbit"""
    t: np.ndarray  # Gyr
    x: np.ndarray  # kpc
    y: np.ndarray  # kpc
    z: np.ndarray  # kpc
    vx: np.ndarray  # km/s
    vy: np.ndarray  # km/s
    vz: np.ndarray  # km/s
    energy: float = None
    Lz: float = None  # Angular momentum z-component

    def R(self) -> np.ndarray:
        return np.sqrt(self.x**2 + self.y**2)

    def r(self) -> np.ndarray:
        return np.sqrt(self.x**2 + self.y**2 + self.z**2)

    def apocentre(self) -> float:
        return np.max(self.r())

    def pericentre(self) -> float:
        return np.min(self.r())

    def eccentricity(self) -> float:
        r_apo = self.apocentre()
        r_peri = self.pericentre()
        return (r_apo - r_peri) / (r_apo + r_peri)


# =============================================================================
# GALACTIC POTENTIAL
# =============================================================================

class GalacticPotential(ABC):
    """Base class for galactic potentials"""

    @abstractmethod
    def potential(self, x: float, y: float, z: float) -> float:
        """Calculate potential at position (kpc), returns (km/s)^2"""
        pass

    @abstractmethod
    def acceleration(self, x: float, y: float, z: float) -> Tuple[float, float, float]:
        """Calculate acceleration at position, returns km/s / Gyr"""
        pass

    def circular_velocity(self, R: float, z: float = 0) -> float:
        """Calculate circular velocity at cylindrical radius R"""
        # v_c = sqrt(R * |dPhi/dR|)
        eps = 1e-6
        Phi_plus = self.potential(R + eps, 0, z)
        Phi_minus = self.potential(R - eps, 0, z)
        dPhi_dR = (Phi_plus - Phi_minus) / (2 * eps)
        return np.sqrt(R * np.abs(dPhi_dR))


class NFWHalo(GalacticPotential):
    """
    Navarro-Frenk-White dark matter halo.
    """

    def __init__(self, M_vir: float = 1e12, c: float = 12.0, r_vir: float = None):
        """
        Initialize NFW halo.

        Args:
            M_vir: Virial mass (M_sun)
            c: Concentration parameter
            r_vir: Virial radius (kpc), calculated if None
        """
        self.M_vir = M_vir
        self.c = c

        # Virial radius from mass (assuming z=0, Delta=200)
        if r_vir is None:
            # r_vir = (3 * M_vir / (4 * pi * 200 * rho_crit))^(1/3)
            rho_crit = 1.36e-7  # M_sun / kpc^3 (z=0)
            r_vir = (3 * M_vir / (4 * np.pi * 200 * rho_crit))**(1/3)

        self.r_vir = r_vir
        self.r_s = r_vir / c

        # Scale density
        f_c = np.log(1 + c) - c / (1 + c)
        self.rho_s = M_vir / (4 * np.pi * self.r_s**3 * f_c)

    def potential(self, x: float, y: float, z: float) -> float:
        r = np.sqrt(x**2 + y**2 + z**2)
        r = max(r, 1e-10)  # Avoid singularity

        Phi = -4 * np.pi * G_GALACTIC * self.rho_s * self.r_s**3 * \
              np.log(1 + r / self.r_s) / r

        return Phi

    def acceleration(self, x: float, y: float, z: float) -> Tuple[float, float, float]:
        r = np.sqrt(x**2 + y**2 + z**2)
        r = max(r, 1e-10)

        # M(<r) for NFW
        M_r = 4 * np.pi * self.rho_s * self.r_s**3 * \
              (np.log(1 + r / self.r_s) - r / (self.r_s + r))

        # a = -G * M(<r) / r^2 * r_hat
        a_mag = -G_GALACTIC * M_r / r**2

        # Convert to km/s per Gyr
        a_mag *= 1.022  # Unit conversion factor

        ax = a_mag * x / r
        ay = a_mag * y / r
        az = a_mag * z / r

        return ax, ay, az


class MiyamotoNagaiDisk(GalacticPotential):
    """
    Miyamoto-Nagai disk potential.
    """

    def __init__(self, M: float = 6.5e10, a: float = 3.0, b: float = 0.28):
        """
        Initialize disk potential.

        Args:
            M: Disk mass (M_sun)
            a: Scale length (kpc)
            b: Scale height (kpc)
        """
        self.M = M
        self.a = a
        self.b = b

    def potential(self, x: float, y: float, z: float) -> float:
        R = np.sqrt(x**2 + y**2)
        zb = np.sqrt(z**2 + self.b**2)

        Phi = -G_GALACTIC * self.M / np.sqrt(R**2 + (self.a + zb)**2)

        return Phi

    def acceleration(self, x: float, y: float, z: float) -> Tuple[float, float, float]:
        R = np.sqrt(x**2 + y**2)
        zb = np.sqrt(z**2 + self.b**2)
        denom = (R**2 + (self.a + zb)**2)**1.5

        # Accelerations in km/s per Gyr
        factor = G_GALACTIC * self.M * 1.022

        ax = -factor * x / denom
        ay = -factor * y / denom
        az = -factor * z * (self.a + zb) / (zb * denom)

        return ax, ay, az


class HernquistBulge(GalacticPotential):
    """
    Hernquist bulge potential.
    """

    def __init__(self, M: float = 1e10, a: float = 0.5):
        """
        Initialize bulge potential.

        Args:
            M: Bulge mass (M_sun)
            a: Scale radius (kpc)
        """
        self.M = M
        self.a = a

    def potential(self, x: float, y: float, z: float) -> float:
        r = np.sqrt(x**2 + y**2 + z**2)

        Phi = -G_GALACTIC * self.M / (r + self.a)

        return Phi

    def acceleration(self, x: float, y: float, z: float) -> Tuple[float, float, float]:
        r = np.sqrt(x**2 + y**2 + z**2)
        r = max(r, 1e-10)

        factor = G_GALACTIC * self.M * 1.022 / (r + self.a)**2

        ax = -factor * x / r
        ay = -factor * y / r
        az = -factor * z / r

        return ax, ay, az


class MilkyWayPotential(GalacticPotential):
    """
    Composite Milky Way potential.

    Default parameters similar to MWPotential2014.
    """

    def __init__(self, M_halo: float = 8e11, c_halo: float = 15.3,
                 M_disk: float = 6.8e10, a_disk: float = 3.0, b_disk: float = 0.28,
                 M_bulge: float = 5e9, a_bulge: float = 0.5):
        """
        Initialize MW potential.

        Args:
            M_halo: Halo mass (M_sun)
            c_halo: Halo concentration
            M_disk: Disk mass (M_sun)
            a_disk, b_disk: Disk scale parameters (kpc)
            M_bulge: Bulge mass (M_sun)
            a_bulge: Bulge scale radius (kpc)
        """
        self.halo = NFWHalo(M_halo, c_halo)
        self.disk = MiyamotoNagaiDisk(M_disk, a_disk, b_disk)
        self.bulge = HernquistBulge(M_bulge, a_bulge)

    def potential(self, x: float, y: float, z: float) -> float:
        return (self.halo.potential(x, y, z) +
                self.disk.potential(x, y, z) +
                self.bulge.potential(x, y, z))

    def acceleration(self, x: float, y: float, z: float) -> Tuple[float, float, float]:
        a_halo = self.halo.acceleration(x, y, z)
        a_disk = self.disk.acceleration(x, y, z)
        a_bulge = self.bulge.acceleration(x, y, z)

        return (a_halo[0] + a_disk[0] + a_bulge[0],
                a_halo[1] + a_disk[1] + a_bulge[1],
                a_halo[2] + a_disk[2] + a_bulge[2])


# =============================================================================
# ORBIT INTEGRATOR
# =============================================================================

class OrbitIntegrator:
    """
    Orbit integration in galactic potentials.

    Supports leapfrog and RK4 methods.
    """

    def __init__(self, potential: GalacticPotential = None):
        """
        Initialize integrator.

        Args:
            potential: Galactic potential
        """
        self.potential = potential or MilkyWayPotential()

    def integrate_leapfrog(self, initial: PhaseSpacePoint,
                          t_total: float, dt: float = 0.001) -> Orbit:
        """
        Integrate orbit using leapfrog method.

        Args:
            initial: Initial phase space point
            t_total: Total integration time (Gyr)
            dt: Time step (Gyr)

        Returns:
            Integrated orbit
        """
        n_steps = int(t_total / dt)

        t = np.zeros(n_steps)
        x = np.zeros(n_steps)
        y = np.zeros(n_steps)
        z = np.zeros(n_steps)
        vx = np.zeros(n_steps)
        vy = np.zeros(n_steps)
        vz = np.zeros(n_steps)

        # Initial conditions
        x[0] = initial.x
        y[0] = initial.y
        z[0] = initial.z
        vx[0] = initial.vx
        vy[0] = initial.vy
        vz[0] = initial.vz

        # Initial half-step for velocity
        ax, ay, az = self.potential.acceleration(x[0], y[0], z[0])
        vx_half = vx[0] + 0.5 * dt * ax
        vy_half = vy[0] + 0.5 * dt * ay
        vz_half = vz[0] + 0.5 * dt * az

        for i in range(1, n_steps):
            t[i] = t[i-1] + dt

            # Position update
            x[i] = x[i-1] + dt * vx_half
            y[i] = y[i-1] + dt * vy_half
            z[i] = z[i-1] + dt * vz_half

            # Acceleration at new position
            ax, ay, az = self.potential.acceleration(x[i], y[i], z[i])

            # Velocity update
            vx_half_new = vx_half + dt * ax
            vy_half_new = vy_half + dt * ay
            vz_half_new = vz_half + dt * az

            # Store velocity at integer step
            vx[i] = 0.5 * (vx_half + vx_half_new)
            vy[i] = 0.5 * (vy_half + vy_half_new)
            vz[i] = 0.5 * (vz_half + vz_half_new)

            vx_half = vx_half_new
            vy_half = vy_half_new
            vz_half = vz_half_new

        # Calculate energy and angular momentum
        E = self._calculate_energy(x[0], y[0], z[0], vx[0], vy[0], vz[0])
        Lz = x[0] * vy[0] - y[0] * vx[0]

        return Orbit(t, x, y, z, vx, vy, vz, energy=E, Lz=Lz)

    def integrate_rk4(self, initial: PhaseSpacePoint,
                      t_total: float, dt: float = 0.001) -> Orbit:
        """
        Integrate orbit using 4th-order Runge-Kutta.

        Args:
            initial: Initial phase space point
            t_total: Total integration time (Gyr)
            dt: Time step (Gyr)

        Returns:
            Integrated orbit
        """
        n_steps = int(t_total / dt)

        t = np.zeros(n_steps)
        x = np.zeros(n_steps)
        y = np.zeros(n_steps)
        z = np.zeros(n_steps)
        vx = np.zeros(n_steps)
        vy = np.zeros(n_steps)
        vz = np.zeros(n_steps)

        x[0], y[0], z[0] = initial.x, initial.y, initial.z
        vx[0], vy[0], vz[0] = initial.vx, initial.vy, initial.vz

        def derivs(pos, vel):
            ax, ay, az = self.potential.acceleration(*pos)
            return np.array([vel[0], vel[1], vel[2], ax, ay, az])

        for i in range(1, n_steps):
            t[i] = t[i-1] + dt

            pos = np.array([x[i-1], y[i-1], z[i-1]])
            vel = np.array([vx[i-1], vy[i-1], vz[i-1]])

            k1 = derivs(pos, vel)
            k2 = derivs(pos + 0.5*dt*k1[:3], vel + 0.5*dt*k1[3:])
            k3 = derivs(pos + 0.5*dt*k2[:3], vel + 0.5*dt*k2[3:])
            k4 = derivs(pos + dt*k3[:3], vel + dt*k3[3:])

            k = (k1 + 2*k2 + 2*k3 + k4) / 6

            x[i] = x[i-1] + dt * k[0]
            y[i] = y[i-1] + dt * k[1]
            z[i] = z[i-1] + dt * k[2]
            vx[i] = vx[i-1] + dt * k[3]
            vy[i] = vy[i-1] + dt * k[4]
            vz[i] = vz[i-1] + dt * k[5]

        E = self._calculate_energy(x[0], y[0], z[0], vx[0], vy[0], vz[0])
        Lz = x[0] * vy[0] - y[0] * vx[0]

        return Orbit(t, x, y, z, vx, vy, vz, energy=E, Lz=Lz)

    def _calculate_energy(self, x, y, z, vx, vy, vz) -> float:
        """Calculate total energy"""
        KE = 0.5 * (vx**2 + vy**2 + vz**2)
        PE = self.potential.potential(x, y, z)
        return KE + PE


# =============================================================================
# STELLAR STREAM FINDER
# =============================================================================

class StellarStreamFinder:
    """
    Algorithms for detecting and characterizing stellar streams.
    """

    def __init__(self):
        """Initialize stream finder"""
        pass

    def great_circle_count(self, ra: np.ndarray, dec: np.ndarray,
                           pm_ra: np.ndarray, pm_dec: np.ndarray,
                           n_poles: int = 1000,
                           width: float = 2.0) -> Tuple[np.ndarray, np.ndarray]:
        """
        Great circle cell count method for stream detection.

        Args:
            ra, dec: Positions (degrees)
            pm_ra, pm_dec: Proper motions (mas/yr)
            n_poles: Number of pole positions to test
            width: Stream width (degrees)

        Returns:
            (pole_coords, counts) for each pole
        """
        # Generate pole positions
        pole_phi = np.random.uniform(0, 2*np.pi, n_poles)
        pole_theta = np.arccos(np.random.uniform(-1, 1, n_poles))

        # Convert positions to Cartesian
        ra_rad = np.radians(ra)
        dec_rad = np.radians(dec)

        x = np.cos(dec_rad) * np.cos(ra_rad)
        y = np.cos(dec_rad) * np.sin(ra_rad)
        z = np.sin(dec_rad)

        counts = np.zeros(n_poles)

        for i in range(n_poles):
            # Pole normal vector
            nx = np.sin(pole_theta[i]) * np.cos(pole_phi[i])
            ny = np.sin(pole_theta[i]) * np.sin(pole_phi[i])
            nz = np.cos(pole_theta[i])

            # Distance from great circle
            dist = np.abs(x * nx + y * ny + z * nz)
            dist_deg = np.degrees(np.arcsin(dist))

            # Count stars within width
            counts[i] = np.sum(dist_deg < width)

        poles = np.column_stack([pole_phi, pole_theta])

        return poles, counts

    def matched_filter(self, coords: np.ndarray, pm: np.ndarray,
                       template_track: np.ndarray,
                       template_dispersion: float = 0.5) -> np.ndarray:
        """
        Apply matched filter for stream detection.

        Args:
            coords: Star coordinates (N, 2) in degrees
            pm: Proper motions (N, 2) in mas/yr
            template_track: Expected stream track (M, 2)
            template_dispersion: Expected width (degrees)

        Returns:
            Filter response at each star position
        """
        n_stars = len(coords)
        response = np.zeros(n_stars)

        for i in range(n_stars):
            # Distance to nearest track point
            dists = np.sqrt(np.sum((template_track - coords[i])**2, axis=1))
            min_dist = np.min(dists)

            # Gaussian filter response
            response[i] = np.exp(-0.5 * (min_dist / template_dispersion)**2)

        return response

    def velocity_dispersion(self, vx: np.ndarray, vy: np.ndarray,
                           vz: np.ndarray) -> Dict[str, float]:
        """
        Calculate velocity dispersion tensor.

        Args:
            vx, vy, vz: Velocity components (km/s)

        Returns:
            Dispersion statistics
        """
        mean_vx = np.mean(vx)
        mean_vy = np.mean(vy)
        mean_vz = np.mean(vz)

        sigma_x = np.std(vx)
        sigma_y = np.std(vy)
        sigma_z = np.std(vz)

        sigma_total = np.sqrt(sigma_x**2 + sigma_y**2 + sigma_z**2)

        return {
            'sigma_x': sigma_x,
            'sigma_y': sigma_y,
            'sigma_z': sigma_z,
            'sigma_total': sigma_total,
            'mean_velocity': np.sqrt(mean_vx**2 + mean_vy**2 + mean_vz**2)
        }


# =============================================================================
# CHEMICAL EVOLUTION MODEL
# =============================================================================

class ChemicalEvolutionModel:
    """
    One-zone galactic chemical evolution.

    Includes yields from AGB stars, SNe II, and SNe Ia.
    """

    # Solar abundances (by mass)
    SOLAR_Z = 0.0142
    SOLAR_FE_H = 0.0

    # IMF-averaged yields (simplified)
    YIELDS = {
        'O': {'SNII': 0.015, 'SNIa': 0.001, 'AGB': 0.001},
        'Mg': {'SNII': 0.005, 'SNIa': 0.0001, 'AGB': 0.0001},
        'Fe': {'SNII': 0.002, 'SNIa': 0.007, 'AGB': 0.0001},
        'C': {'SNII': 0.003, 'SNIa': 0.001, 'AGB': 0.003},
        'N': {'SNII': 0.001, 'SNIa': 0.0001, 'AGB': 0.002},
    }

    def __init__(self, infall_timescale: float = 5.0,
                 star_formation_efficiency: float = 0.5):
        """
        Initialize chemical evolution model.

        Args:
            infall_timescale: Gas infall timescale (Gyr)
            star_formation_efficiency: SF efficiency (Gyr^-1)
        """
        self.tau_infall = infall_timescale
        self.nu_sf = star_formation_efficiency

        # SN Ia delay time distribution
        self.t_delay_min = 0.04  # Gyr (40 Myr)
        self.t_delay_max = 13.0  # Gyr

    def infall_rate(self, t: float, M_total: float = 1e10) -> float:
        """
        Calculate gas infall rate.

        Args:
            t: Time (Gyr)
            M_total: Total infalling mass (M_sun)

        Returns:
            Infall rate (M_sun/Gyr)
        """
        return (M_total / self.tau_infall) * np.exp(-t / self.tau_infall)

    def star_formation_rate(self, M_gas: float) -> float:
        """
        Calculate star formation rate.

        Args:
            M_gas: Gas mass (M_sun)

        Returns:
            SFR (M_sun/Gyr)
        """
        return self.nu_sf * M_gas

    def sn_ia_rate(self, t: float, sfh: np.ndarray, times: np.ndarray) -> float:
        """
        Calculate SN Ia rate from delay time distribution.

        DTD ~ t^(-1) for t > t_delay_min

        Args:
            t: Current time (Gyr)
            sfh: Star formation history
            times: Time array for SFH

        Returns:
            SN Ia rate (per Gyr per M_sun formed)
        """
        if t < self.t_delay_min:
            return 0.0

        # Number of SNe Ia per unit mass formed
        A_Ia = 1e-3  # Normalization

        rate = 0.0
        for i, t_form in enumerate(times):
            delay = t - t_form
            if self.t_delay_min < delay < self.t_delay_max:
                # DTD ~ t^(-1)
                dtd = 1.0 / delay
                rate += sfh[i] * dtd * A_Ia

        return rate

    def evolve(self, t_final: float = 13.0, dt: float = 0.01,
               elements: List[str] = None) -> Dict[str, np.ndarray]:
        """
        Evolve chemical abundances over time.

        Args:
            t_final: Final time (Gyr)
            dt: Time step (Gyr)
            elements: Elements to track

        Returns:
            Dictionary of abundance evolution
        """
        elements = elements or ['Fe', 'O', 'Mg']
        n_steps = int(t_final / dt)

        times = np.linspace(0, t_final, n_steps)
        M_gas = np.zeros(n_steps)
        M_star = np.zeros(n_steps)
        SFR = np.zeros(n_steps)

        abundances = {el: np.zeros(n_steps) for el in elements}

        # Initial conditions
        M_gas[0] = 1e9  # Initial gas mass
        M_star[0] = 0

        for el in elements:
            abundances[el][0] = 1e-10  # Primordial (essentially zero)

        for i in range(1, n_steps):
            t = times[i]

            # Gas evolution
            infall = self.infall_rate(t) * dt
            sfr = self.star_formation_rate(M_gas[i-1])
            SFR[i] = sfr

            # Mass return from stars (instantaneous recycling approximation)
            R = 0.4  # Return fraction
            M_return = R * sfr * dt

            # Gas mass change
            M_gas[i] = M_gas[i-1] + infall - sfr * dt + M_return
            M_star[i] = M_star[i-1] + (1 - R) * sfr * dt

            # SN rates
            sn_ii_rate = sfr / 100  # ~1 SNII per 100 M_sun formed
            sn_ia_rate = self.sn_ia_rate(t, SFR[:i], times[:i])

            # Abundance evolution
            for el in elements:
                y_ii = self.YIELDS.get(el, {}).get('SNII', 0)
                y_ia = self.YIELDS.get(el, {}).get('SNIa', 0)

                # Mass of element produced
                dm_el = (sn_ii_rate * y_ii + sn_ia_rate * y_ia) * dt

                # Update abundance (mass fraction)
                M_el = abundances[el][i-1] * M_gas[i-1]
                M_el += dm_el
                abundances[el][i] = M_el / M_gas[i] if M_gas[i] > 0 else 0

        result = {
            'time': times,
            'M_gas': M_gas,
            'M_star': M_star,
            'SFR': SFR,
        }
        result.update(abundances)

        return result

    def fe_h_from_mass_fraction(self, X_Fe: float) -> float:
        """
        Convert Fe mass fraction to [Fe/H].

        Args:
            X_Fe: Fe mass fraction

        Returns:
            [Fe/H] value
        """
        X_Fe_sun = 0.00125  # Solar Fe mass fraction
        if X_Fe <= 0:
            return -10.0
        return np.log10(X_Fe / X_Fe_sun)


# =============================================================================
# ACTION-ANGLE CALCULATOR
# =============================================================================

class ActionAngleCalculator:
    """
    Calculate action-angle coordinates using Stäckel approximation.
    """

    def __init__(self, potential: GalacticPotential = None):
        """
        Initialize calculator.

        Args:
            potential: Galactic potential
        """
        self.potential = potential or MilkyWayPotential()
        self.integrator = OrbitIntegrator(self.potential)

    def actions_staeckel(self, orbit: Orbit, delta: float = 0.45) -> Dict[str, float]:
        """
        Estimate actions using Stäckel fudge.

        Args:
            orbit: Integrated orbit
            delta: Focal distance parameter (kpc)

        Returns:
            Dictionary with Jr, Lz, Jz
        """
        # Angular momentum (exact)
        Lz = orbit.x * orbit.vy - orbit.y * orbit.vx
        Lz_mean = np.mean(Lz)

        # Radial action (approximate from orbit extent)
        R = orbit.R()
        vR = (orbit.x * orbit.vx + orbit.y * orbit.vy) / R

        # Simple approximation: Jr ~ integral of vR dR over one period
        # Use orbit apocentre/pericentre
        R_min = np.min(R)
        R_max = np.max(R)

        # Estimate from radial period
        E = orbit.energy
        Jr_approx = 0.5 * (R_max - R_min) * np.std(np.abs(vR))

        # Vertical action
        z = orbit.z
        vz = orbit.vz
        z_max = np.max(np.abs(z))

        Jz_approx = 0.5 * z_max * np.std(np.abs(vz))

        return {
            'Jr': Jr_approx,
            'Lz': Lz_mean,
            'Jz': Jz_approx,
            'E': E
        }

    def orbital_frequencies(self, orbit: Orbit) -> Dict[str, float]:
        """
        Estimate orbital frequencies from orbit.

        Args:
            orbit: Integrated orbit

        Returns:
            Dictionary with Omega_r, Omega_phi, Omega_z
        """
        from scipy.fft import fft, fftfreq

        dt = orbit.t[1] - orbit.t[0]
        n = len(orbit.t)

        # Radial frequency
        R = orbit.R()
        R_fft = fft(R - np.mean(R))
        freqs = fftfreq(n, dt)
        idx = np.argmax(np.abs(R_fft[1:n//2])) + 1
        Omega_r = 2 * np.pi * np.abs(freqs[idx])

        # Azimuthal frequency
        phi = np.arctan2(orbit.y, orbit.x)
        phi = np.unwrap(phi)
        Omega_phi = (phi[-1] - phi[0]) / (orbit.t[-1] - orbit.t[0])

        # Vertical frequency
        z_fft = fft(orbit.z - np.mean(orbit.z))
        idx_z = np.argmax(np.abs(z_fft[1:n//2])) + 1
        Omega_z = 2 * np.pi * np.abs(freqs[idx_z])

        return {
            'Omega_r': Omega_r,
            'Omega_phi': Omega_phi,
            'Omega_z': Omega_z
        }


# =============================================================================
# CLUSTER DISSOLUTION MODEL
# =============================================================================

class ClusterDissolutionModel:
    """
    Model for star cluster dissolution in galactic tidal field.
    """

    def __init__(self, potential: GalacticPotential = None):
        """
        Initialize dissolution model.

        Args:
            potential: Galactic potential
        """
        self.potential = potential or MilkyWayPotential()

    def jacobi_radius(self, M_cluster: float, R_gal: float) -> float:
        """
        Calculate Jacobi (tidal) radius.

        r_J = (G * M_cluster / (4 * Omega^2 - kappa^2))^(1/3)

        Args:
            M_cluster: Cluster mass (M_sun)
            R_gal: Galactocentric radius (kpc)

        Returns:
            Jacobi radius (pc)
        """
        # Circular velocity and angular frequency
        v_c = self.potential.circular_velocity(R_gal)
        Omega = v_c / R_gal  # rad/Gyr, approximately

        # Convert to rad/s for calculation
        Omega_s = Omega / (GYR / 1e9)  # rad/Gyr to rad/Myr

        # Approximate Oort constant A
        # kappa^2 = 4 * Omega^2 + R * d(Omega^2)/dR
        # For flat rotation curve: kappa ~ sqrt(2) * Omega
        kappa = np.sqrt(2) * Omega

        # Tidal term
        tidal = 4 * Omega**2 - kappa**2

        if tidal <= 0:
            return np.inf

        # Jacobi radius
        r_J = (G_GALACTIC * M_cluster / tidal)**(1/3)

        return r_J * 1000  # kpc to pc

    def relaxation_time(self, M_cluster: float, r_h: float,
                        m_star: float = 0.5) -> float:
        """
        Calculate two-body relaxation time.

        Args:
            M_cluster: Cluster mass (M_sun)
            r_h: Half-mass radius (pc)
            m_star: Mean stellar mass (M_sun)

        Returns:
            Relaxation time (Myr)
        """
        N = M_cluster / m_star
        ln_Lambda = np.log(0.4 * N)  # Coulomb logarithm

        # Spitzer (1987) formula
        r_h_kpc = r_h / 1000

        # Velocity dispersion from virial theorem
        sigma = np.sqrt(G_GALACTIC * M_cluster / (2 * r_h_kpc))  # km/s

        # Relaxation time
        t_rh = 0.138 * N * r_h_kpc**1.5 / \
               (m_star**0.5 * ln_Lambda * np.sqrt(G_GALACTIC * M_cluster))

        return t_rh * 1000  # Gyr to Myr

    def dissolution_time(self, M_cluster: float, R_gal: float) -> float:
        """
        Estimate cluster dissolution time.

        Args:
            M_cluster: Initial cluster mass (M_sun)
            R_gal: Galactocentric radius (kpc)

        Returns:
            Dissolution time (Gyr)
        """
        # Lamers et al. (2005) scaling
        # t_dis ~ t_4 * (M / 10^4)^gamma
        # where t_4 is dissolution time for 10^4 M_sun cluster

        # Environment-dependent t_4 (typical for solar neighborhood)
        gamma = 0.62
        t_4 = 1.3  # Gyr, for solar neighborhood

        # Scale with galactocentric radius (tidal field weakens outward)
        R_0 = 8.0  # Solar radius
        t_4_R = t_4 * (R_gal / R_0)**0.5

        t_dis = t_4_R * (M_cluster / 1e4)**gamma

        return t_dis


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'PhaseSpacePoint',
    'Orbit',
    'GalacticPotential',
    'NFWHalo',
    'MiyamotoNagaiDisk',
    'HernquistBulge',
    'MilkyWayPotential',
    'OrbitIntegrator',
    'StellarStreamFinder',
    'ChemicalEvolutionModel',
    'ActionAngleCalculator',
    'ClusterDissolutionModel',
]



def utility_function_27(*args, **kwargs):
    """Utility function 27."""
    return None



def utility_function_7(*args, **kwargs):
    """Utility function 7."""
    return None
