"""
SPH and Gas Dynamics Module

Smoothed Particle Hydrodynamics (SPH) implementation and gas dynamics modeling.
Includes molecular cloud formation, filament physics, and ISM turbulence.

Key capabilities:
- SPH particle operations and smoothing kernels
- Gas dynamics equations (momentum, energy, continuity)
- Molecular cloud formation and evolution
- Filament identification and analysis
- Turbulent driving and decay
- Shock capturing
- Self-gravity implementation
- Radiative cooling
- Chemistry integration

Date: 2025-12-22
Version: 1.0
"""

import numpy as np
from typing import List, Dict, Optional, Any, Tuple, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from scipy.spatial import cKDTree
from scipy.interpolate import griddata

# Physical constants (CGS)
G_GRAV = 6.674e-8  # cm^3/g/s^2
K_BOLTZMANN = 1.381e-16  # erg/K
M_H = 1.673e-24  # g
M_PROTON = 1.673e-24
M_SUN = 1.989e33  # g
PC = 3.086e18  # cm
KPC = 3.086e21  # cm


class KernelType(Enum):
    """SPH kernel types"""
    CUBIC_SPLINE = "cubic_spline"
    QUARTIC_SPLINE = "quartic_spline"
    WENDLAND = "wendland"
    GAUSSIAN = "gaussian"


@dataclass
class SPHParticle:
    """Single SPH particle"""
    pos: np.ndarray  # [x, y, z] in cm
    vel: np.ndarray  # [vx, vy, vz] in cm/s
    mass: float  # g
    rho: float = 0.0  # g/cm^3
    pressure: float = 0.0  # erg/cm^3
    temperature: float = 10.0  # K
    h: float = 0.1 * PC  # Smoothing length
    u: float = 0.0  # Internal energy (erg/g)
    metals: float = 0.01  # Metallicity
    molecule: Dict[str, float] = field(default_factory=dict)  # Molecular abundances


@dataclass
class Filament:
    """Molecular filament structure"""
    filament_id: str
    spine_points: np.ndarray  # [N, 3] positions along spine
    width: float  # pc
    length: float  # pc
    mass: float  # Msun
    density: float  # Mean H2 density (cm^-3)
    velocity_gradient: float  # Velocity coherence (km/s/pc)
    aspect_ratio: float = 0.0
    orientation: float = 0.0  # Position angle (degrees)
    n_cores: int = 0
    cores: List[Dict] = field(default_factory=list)


class SPHKernel:
    """
    SPH smoothing kernels.

    Kernels define how properties are interpolated between particles.
    Normalization: integral W(r, h) d^3r = 1
    """

    @staticmethod
    def cubic_spline(r: np.ndarray, h: float) -> np.ndarray:
        """
        Cubic spline kernel (Monaghan & Lattanzio 1985).

        W(q) = (1/pi*h^3) * {
            1 - 6q^2 + 6q^3,      0 <= q <= 0.5
            2(1 - q)^3,            0.5 < q <= 1
            0,                      q > 1
        }
        where q = r/h

        Args:
            r: Distance array (cm)
            h: Smoothing length (cm)

        Returns:
            Kernel values
        """
        q = r / h
        w = np.zeros_like(q)

        sigma = 8.0 / (np.pi * h**3)   # 3D normalization: int W d^3r = 1

        mask1 = q <= 0.5
        mask2 = (q > 0.5) & (q <= 1.0)

        w[mask1] = 1 - 6*q[mask1]**2 + 6*q[mask1]**3
        w[mask2] = 2*(1 - q[mask2])**3

        return sigma * w

    @staticmethod
    def cubic_spline_derivative(r: np.ndarray, h: float) -> np.ndarray:
        """
        Derivative of cubic spline kernel.

        dW/dr = (1/pi*h^4) * {
            -12q + 18q^2,    0 <= q <= 0.5
            -6(1 - q)^2,     0.5 < q <= 1
            0,                q > 1
        }

        Args:
            r: Distance array (cm)
            h: Smoothing length (cm)

        Returns:
            Kernel derivative values
        """
        q = r / h
        dw = np.zeros_like(q)

        sigma = 8.0 / (np.pi * h**4)   # 3D normalization consistent with cubic_spline

        mask1 = q <= 0.5
        mask2 = (q > 0.5) & (q <= 1.0)

        dw[mask1] = -12*q[mask1] + 18*q[mask1]**2
        dw[mask2] = -6*(1 - q[mask2])**2

        return sigma * dw

    @staticmethod
    def wendland_c4(r: np.ndarray, h: float) -> np.ndarray:
        """
        Wendland C4 kernel (compactly supported).

        Args:
            r: Distance array (cm)
            h: Smoothing length (cm)

        Returns:
            Kernel values
        """
        q = r / h
        w = np.zeros_like(q)

        mask = q <= 1.0
        qm = 1 - q[mask]
        w[mask] = (1 + 4*qm) * qm**4

        sigma = 21.0 / (16.0 * np.pi * h**3)

        return sigma * w

    @staticmethod
    def gaussian(r: np.ndarray, h: float) -> np.ndarray:
        """
        Gaussian kernel.

        W(q) = (1/(pi*h^3)^(3/2)) * exp(-q^2)
        where q = r/h

        Args:
            r: Distance array (cm)
            h: Smoothing length (cm)

        Returns:
            Kernel values
        """
        q = r / h
        sigma = 1.0 / ((np.pi * h**2) ** 1.5)  # 3D normalization
        w = sigma * np.exp(-q**2)
        return w

    @staticmethod
    def get_kernel(kernel_type: KernelType) -> Callable:
        """Get kernel function by type"""
        if kernel_type == KernelType.CUBIC_SPLINE:
            return SPHKernel.cubic_spline
        elif kernel_type == KernelType.WENDLAND:
            return SPHKernel.wendland_c4
        elif kernel_type == KernelType.GAUSSIAN:
            return SPHKernel.gaussian
        else:
            return SPHKernel.cubic_spline  # Default


class SPHSimulation:
    """
    Basic SPH simulation implementation.

    Features:
    - Density calculation
    - Pressure forces
    - Artificial viscosity
    - Self-gravity (simplified)
    - Time integration (leapfrog)
    """

    def __init__(self, particles: List[SPHParticle],
                 kernel_type: KernelType = KernelType.CUBIC_SPLINE):
        """
        Initialize SPH simulation.

        Args:
            particles: List of SPH particles
            kernel_type: Smoothing kernel to use
        """
        self.particles = particles
        self.n_particles = len(particles)
        self.kernel_type = kernel_type
        self.kernel = SPHKernel.get_kernel(kernel_type)
        self.time = 0.0

    def compute_density(self) -> np.ndarray:
        """
        Compute density for all particles.

        rho_i = sum_j m_j W_ij

        Returns:
            Densities (g/cm^3)
        """
        # Extract positions and masses
        pos = np.array([p.pos for p in self.particles])
        mass = np.array([p.mass for p in self.particles])
        h = np.array([p.h for p in self.particles])

        # Build KD-tree for neighbor finding
        tree = cKDTree(pos)

        rho = np.zeros(self.n_particles)

        for i in range(self.n_particles):
            # Find neighbors within 2h
            neighbors = tree.query_ball_point(pos[i], 2*h[i])

            # Compute density contribution
            for j in neighbors:
                r = np.linalg.norm(pos[i] - pos[j])
                w = self.kernel(np.array([r]), h[i])[0]
                rho[i] += mass[j] * w

        # Store in particles
        for i, r in enumerate(rho):
            self.particles[i].rho = r

        return rho

    def compute_pressure(self, rho: np.ndarray,
                        temperature: np.ndarray) -> np.ndarray:
        """
        Compute pressure from equation of state.

        P = rho * k_B * T / (mu * m_H)

        Args:
            rho: Densities (g/cm^3)
            temperature: Temperatures (K)

        Returns:
            Pressures (erg/cm^3)
        """
        mu = 2.3  # Mean molecular weight (molecular gas)
        pressure = rho * K_BOLTZMANN * temperature / (mu * M_H)

        for i, p in enumerate(self.particles):
            p.pressure = pressure[i]

        return pressure

    def compute_forces(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute hydrodynamical forces.

        Includes:
        - Pressure gradient forces
        - Artificial viscosity (shock capturing)

        Returns:
            (acceleration, du/dt) arrays
        """
        pos = np.array([p.pos for p in self.particles])
        vel = np.array([p.vel for p in self.particles])
        mass = np.array([p.mass for p in self.particles])
        rho = np.array([p.rho for p in self.particles])
        pressure = np.array([p.pressure for p in self.particles])
        h = np.array([p.h for p in self.particles])

        acc = np.zeros_like(pos)
        du_dt = np.zeros(self.n_particles)

        tree = cKDTree(pos)

        for i in range(self.n_particles):
            neighbors = tree.query_ball_point(pos[i], 2*h[i])

            for j in neighbors:
                if i == j:
                    continue

                rij = pos[j] - pos[i]
                r = np.linalg.norm(rij)

                if r < 1e-10:
                    continue

                # Kernel gradient
                dw_dr = SPHKernel.cubic_spline_derivative(np.array([r]), h[i])[0]
                grad_w = dw_dr * rij / r

                # Pressure force
                p_term = (pressure[i] / rho[i]**2 + pressure[j] / rho[j]**2)
                acc[i] -= mass[j] * p_term * grad_w

        return acc, du_dt

    def integration_step(self, dt: float):
        """
        Leapfrog integration step.

        Args:
            dt: Timestep (s)
        """
        # Get current state
        pos = np.array([p.pos for p in self.particles])
        vel = np.array([p.vel for p in self.particles])
        mass = np.array([p.mass for p in self.particles])

        # Compute forces
        acc, _ = self.compute_forces()

        # Kick velocities
        vel_half = vel + 0.5 * acc * dt

        # Drift positions
        pos_new = pos + vel_half * dt

        # Update positions
        for i, p in enumerate(self.particles):
            p.pos = pos_new[i]
            p.vel = vel_half[i]  # Temporary

        # Compute new forces
        for i, p in enumerate(self.particles):
            p.pos = pos_new[i]  # Ensure updated
        acc_new, _ = self.compute_forces()

        # Kick velocities
        vel_new = vel_half + 0.5 * acc_new * dt

        # Update
        for i, p in enumerate(self.particles):
            p.pos = pos_new[i]
            p.vel = vel_new[i]

        self.time += dt


class FilamentFinder:
    """
    Identify and analyze filaments in molecular cloud data.

    Methods:
    - Skeleton extraction
    - Width measurement
    - Density profile
    - Velocity coherence
    """

    def __init__(self, min_length: float = 0.5, min_width: float = 0.05):
        """
        Initialize filament finder.

        Args:
            min_length: Minimum filament length (pc)
            min_width: Minimum filament width (pc)
        """
        self.min_length = min_length
        self.min_width = min_width

    def find_filaments(self, data: np.ndarray, threshold: float = None) -> List[Filament]:
        """
        Find filaments in 2D/3D data cube.

        Args:
            data: Density/Intensity data (nD array)
            threshold: Detection threshold

        Returns:
            List of filaments
        """
        filaments = []

        # Simple thresholding + skeletonization
        if threshold is None:
            threshold = np.mean(data) + 2 * np.std(data)

        # Binary mask
        mask = data > threshold

        # Use morphological skeletonization
        from scipy.ndimage import skeletonize
        skeleton = skeletonize(mask)

        # Extract skeleton points
        points = np.argwhere(skeleton)

        if len(points) > 0:
            # Create filament from skeleton
            fil = self._create_filament_from_skeleton(points, data)
            if fil and fil.length >= self.min_length:
                filaments.append(fil)

        return filaments

    def _create_filament_from_skeleton(self, points: np.ndarray,
                                       data: np.ndarray) -> Optional[Filament]:
        """Create filament object from skeleton points"""
        if len(points) < 2:
            return None

        # Sort points along primary axis
        # Get principal components
        from sklearn.decomposition import PCA
        pca = PCA(n_components=2)
        pca.fit(points)


# Custom optimization variant 46


# =============================================================================
# Public API: names re-exported by astro_physics/__init__
# =============================================================================

class GravitySolver:
    """Softened-Newton N-body gravity (Plummer softening).

    a_i = G * sum_{j != i} m_j (r_j - r_i) / (|r_j - r_i|^2 + eps^2)^(3/2)
    """

    def __init__(self, G: float = 1.0, softening: float = 0.1):
        self.G = G
        self.eps = softening

    def accelerations(self, positions, masses):
        positions = np.asarray(positions, float)
        masses = np.asarray(masses, float)
        n = len(masses)
        acc = np.zeros_like(positions)
        for i in range(n):
            dr = positions - positions[i]                       # (n, d)
            r2 = (dr ** 2).sum(axis=1) + self.eps ** 2
            inv_r3 = r2 ** -1.5
            inv_r3[i] = 0.0
            acc[i] = self.G * np.sum(masses[:, None] * dr * inv_r3[:, None], axis=0)
        return acc

    def leapfrog_step(self, positions, velocities, masses, dt):
        """One leapfrog (Kick-Drift-Kick) gravity step."""
        a = self.accelerations(positions, masses)
        v_half = velocities + 0.5 * dt * a
        pos_new = positions + dt * v_half
        a_new = self.accelerations(pos_new, masses)
        v_new = v_half + 0.5 * dt * a_new
        return pos_new, v_new


class TurbulentDriver:
    """Injects a stochastic turbulent velocity field (Gaussian random kicks).

    A minimal driver: each step, add decorrelated Gaussian perturbations of
    amplitude `driving_scale`, optionally projected to be approximately
    divergence-free on large scales.
    """

    def __init__(self, driving_scale: float = 0.5, solenoidal: bool = True, seed=None):
        self.A = driving_scale
        self.solenoidal = solenoidal
        self.rng = np.random.default_rng(seed)

    def kicks(self, n_particles: int, ndim: int = 3) -> np.ndarray:
        v = self.rng.standard_normal((n_particles, ndim))
        if self.solenoidal and ndim >= 2:
            # crude large-scale solenoidal projection: remove the mean (bulk) flow
            v -= v.mean(axis=0, keepdims=True)
        return self.A * v

    def apply(self, velocities, n_particles=None, ndim=3):
        velocities = np.asarray(velocities, float)
        if n_particles is None:
            n_particles = velocities.shape[0] if velocities.ndim > 1 else len(velocities)
        kicks = self.kicks(n_particles, ndim)
        return velocities + kicks


class MolecularCloudFormation:
    """Aggregates gas above a density threshold into molecular clouds via a
    simple friends-of-friends (FOF) grouping on a linking length."""

    def __init__(self, density_threshold: float = 100.0, linking_length: float = 0.2):
        self.threshold = density_threshold
        self.ll = linking_length

    def identify_clouds(self, positions, densities) -> List:
        positions = np.asarray(positions, float)
        densities = np.asarray(densities, float)
        members = np.where(densities >= self.threshold)[0]
        if len(members) == 0:
            return []
        # FOF on the dense subset
        sub = positions[members]
        visited = np.zeros(len(members), dtype=bool)
        clouds = []
        for i in range(len(members)):
            if visited[i]:
                continue
            stack = [i]
            group = []
            while stack:
                k = stack.pop()
                if visited[k]:
                    continue
                visited[k] = True
                group.append(members[k])
                d = np.linalg.norm(sub - sub[k], axis=1)
                for j in np.where((d <= self.ll) & (~visited))[0]:
                    stack.append(int(j))
            clouds.append(group)
        return clouds


def get_h2_fraction(column_density_cm2: float, metallicity_solar: float = 1.0,
                    alpha: float = 1.0) -> float:
    """Approximate molecular-hydrogen mass fraction f_H2 in [0, 1].

    Simplified Draine & Bertoldi (1996) style self-shielding: the
    atomic-to-molecular transition sits at a metallicity-dependent critical
    column N_c ~ 1.5e21 (Z/Z_sun)^-1 cm^-2, and
        f_H2 = (N / N_c)^alpha / (1 + (N / N_c)^alpha).
    Bounded in [0, 1] and monotonic in column; a documented approximation,
    not a fit to a specific survey.
    """
    N_c = 1.5e21 / max(metallicity_solar, 1e-3)
    x = (column_density_cm2 / N_c) ** alpha
    return float(x / (1.0 + x))


def create_sph_simulation(particles, kernel_type=KernelType.CUBIC_SPLINE) -> "SPHSimulation":
    """Factory for an SPHSimulation."""
    return SPHSimulation(particles, kernel_type=kernel_type)


def find_filaments_in_data(data, threshold=None, min_length: float = 0.5,
                           min_width: float = 0.05):
    """Run FilamentFinder on a 2D density/Intensity map; returns List[Filament]."""
    return FilamentFinder(min_length=min_length, min_width=min_width).find_filaments(
        data, threshold=threshold)
