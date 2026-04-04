"""
Smoothed Particle Hydrodynamics (SPH) Simulation for Astrophysics

This module implements SPH simulations for astronomical gas dynamics,
filament formation, stellar collapse, and other astrophysical phenomena.

Key capabilities:
- Gas dynamics simulation with particle-based methods
- Filament formation from turbulent molecular clouds
- Gravitational collapse and star formation
- Radiative cooling integration
- Magnetic field effects (ideal MHD)
- Multi-wavelength observables calculation

Version: 3.0.0
Date: 2026-03-16
"""

import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json


class PhysicsRegime(Enum):
    """Different astrophysical regimes for SPH simulation."""
    MOLECULAR_CLOUD = "molecular_cloud"
    FILAMENT_FORMATION = "filament_formation"
    STELLAR_COLLAPSE = "stellar_collapse"
    ACCRETION_DISK = "accretion_disk"
    SUPERNOVA_REMNANT = "supernova_remnant"
    GALAXY_CLUSTER = "galaxy_cluster"


@dataclass
class SPHParticle:
    """A single SPH particle."""
    position: np.ndarray  # [x, y, z]
    velocity: np.ndarray  # [vx, vy, vz]
    mass: float
    density: float = 0.0
    pressure: float = 0.0
    temperature: float = 0.0
    internal_energy: float = 0.0
    smoothing_length: float = 0.0
    particle_id: int = 0
    particle_type: str = "gas"  # gas, star, dm
    metals: float = 0.0  # Metallicity
    magnetic_field: Optional[np.ndarray] = None


@dataclass
class SPHConfig:
    """Configuration for SPH simulation."""
    num_particles: int = 1000
    box_size: float = 10.0  # parsecs
    dt: float = 0.001  # Time step (Myr)
    total_time: float = 1.0  # Total simulation time (Myr)
    smoothing_length_ratio: float = 0.5  # h relative to inter-particle separation
    viscosity_alpha: float = 1.0  # Artificial viscosity parameter
    viscosity_beta: float = 2.0
    gravity_constant: float = 1.0  # Normalized G
    eos_gamma: float = 5.0/3.0  # Adiabatic index
    cooling_enabled: bool = True
    magnetic_enabled: bool = False
    self_gravity: bool = True
    periodic_boundaries: bool = True


@dataclass
class SimulationSnapshot:
    """A snapshot of the SPH simulation at a given time."""
    time: float
    particles: List[SPHParticle]
    total_mass: float
    total_energy: float
    total_momentum: np.ndarray
    max_density: float
    min_density: float
    mean_temperature: float
    filamentarity: float = 0.0  # Measure of filament structure
    virial_parameter: float = 0.0
    star_formation_rate: float = 0.0


class SPHKernels:
    """SPH kernel functions for interpolation."""

    @staticmethod
    def cubic_spline(r: float, h: float) -> float:
        """Cubic spline kernel function."""
        q = r / h
        sigma = 1.0 / (np.pi * h**3)

        if q < 1.0:
            return sigma * (1 - 1.5 * q**2 + 0.75 * q**3)
        elif q < 2.0:
            return sigma * 0.25 * (2 - q)**3
        else:
            return 0.0

    @staticmethod
    def cubic_spline_derivative(r: float, h: float) -> float:
        """Derivative of cubic spline kernel."""
        q = r / h
        sigma = 1.0 / (np.pi * h**3)

        if q < 1.0:
            return sigma * (-3 * q + 2.25 * q**2) / h
        elif q < 2.0:
            return -sigma * 0.75 * (2 - q)**2 / h
        else:
            return 0.0

    @staticmethod
    def gaussian(r: float, h: float) -> float:
        """Gaussian kernel function."""
        return (1.0 / (np.pi * h**3)) * np.exp(-q**2)


class GasDynamicsSPH:
    """
    SPH simulation for gas dynamics in molecular clouds.

    Simulates the evolution of gas under gravity, pressure, and
    artificial viscosity for shock capturing.
    """

    def __init__(self, config: Optional[SPHConfig] = None):
        self.config = config or SPHConfig()
        self.particles: List[SPHParticle] = []
        self.time = 0.0
        self.snapshots: List[SimulationSnapshot] = []
        self.kernel = SPHKernels()

    def initialize_molecular_cloud(
        self,
        num_particles: int,
        radius: float,
        temperature: float = 10.0,
        turbulent_energy: float = 1.0
    ) -> None:
        """
        Initialize a spherical molecular cloud with turbulence.

        Args:
            num_particles: Number of gas particles
            radius: Cloud radius in parsecs
            temperature: Initial temperature in Kelvin
            turbulent_energy: Turbulent velocity dispersion
        """
        self.particles = []

        # Create particles with uniform distribution
        for i in range(num_particles):
            # Random position in sphere
            r = radius * np.random.rand()**(1/3)
            theta = np.arccos(2 * np.random.rand() - 1)
            phi = 2 * np.pi * np.random.rand()

            pos = np.array([
                r * np.sin(theta) * np.cos(phi),
                r * np.sin(theta) * np.sin(phi),
                r * np.cos(theta)
            ])

            # Velocity with turbulence
            vel = np.random.randn(3) * turbulent_energy

            # Mass (equal mass particles)
            mass = 1.0 / num_particles

            particle = SPHParticle(
                position=pos,
                velocity=vel,
                mass=mass,
                temperature=temperature,
                internal_energy=temperature,
                particle_id=i,
                particle_type="gas"
            )

            self.particles.append(particle)

        # Calculate initial smoothing lengths
        self._update_smoothing_lengths()

    def _update_smoothing_lengths(self) -> None:
        """Update smoothing lengths based on local density."""
        n = len(self.particles)

        for i, p_i in enumerate(self.particles):
            # Find nearest neighbors
            distances = []
            for j, p_j in enumerate(self.particles):
                if i != j:
                    dist = np.linalg.norm(p_i.position - p_j.position)
                    distances.append(dist)

            distances.sort()

            # Smoothing length based on ~50 nearest neighbors
            if len(distances) > 50:
                p_i.smoothing_length = distances[50] * self.config.smoothing_length_ratio
            else:
                p_i.smoothing_length = self.config.box_size / 10.0

    def compute_density_pressure(self) -> None:
        """Compute density and pressure for all particles."""
        n = len(self.particles)

        for i, p_i in enumerate(self.particles):
            density = 0.0

            # Sum contributions from neighbors
            for j, p_j in enumerate(self.particles):
                r = np.linalg.norm(p_i.position - p_j.position)

                if r < 2 * p_i.smoothing_length:
                    W = self.kernel.cubic_spline(r, p_i.smoothing_length)
                    density += p_j.mass * W

            p_i.density = max(density, 1e-10)

            # Equation of state: ideal gas with adiabatic index
            # P = (gamma - 1) * rho * u
            p_i.pressure = (self.config.eos_gamma - 1) * p_i.density * p_i.internal_energy

    def compute_forces(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute acceleration and heating rate for all particles.

        Returns:
            (acceleration, heating_rate) for each particle
        """
        n = len(self.particles)
        acceleration = np.zeros((n, 3))
        heating_rate = np.zeros(n)

        for i in range(n):
            p_i = self.particles[i]

            # Pressure gradient force
            pressure_grad = np.zeros(3)
            viscosity_term = np.zeros(3)

            for j in range(n):
                if i == j:
                    continue

                p_j = self.particles[j]
                r_vec = p_i.position - p_j.position
                r = np.linalg.norm(r_vec)

                if r < 2 * p_i.smoothing_length and r > 1e-10:
                    r_hat = r_vec / r

                    # Kernel gradient
                    dW_dr = self.kernel.cubic_spline_derivative(r, p_i.smoothing_length)

                    # Pressure force
                    pressure_term = (
                        p_i.pressure / p_i.density**2 +
                        p_j.pressure / p_j.density**2
                    )
                    pressure_grad -= p_j.mass * pressure_term * dW_dr * r_hat

                    # Artificial viscosity (Monaghan 1992)
                    v_ij = p_i.velocity - p_j.velocity
                    if np.dot(v_ij, r_hat) < 0:  # Approaching
                        mu_ij = self.config.smoothing_length_ratio * \
                                np.dot(v_ij, r_hat) / (r / p_i.smoothing_length)
                        rho_ij = 0.5 * (p_i.density + p_j.density)

                        Pi_ij = -self.config.viscosity_alpha * mu_ij + \
                                self.config.viscosity_beta * mu_ij**2
                        Pi_ij = max(Pi_ij, 0)

                        visc_term = -Pi_ij / rho_ij
                        viscosity_term -= p_j.mass * visc_term * dW_dr * r_hat
                        heating_rate[i] += 0.5 * p_j.mass * visc_term * dW_dr

            # Add pressure and viscosity
            acceleration[i] += pressure_grad + viscosity_term

            # Self-gravity (simplified)
            if self.config.self_gravity:
                grav_accel = np.zeros(3)
                for j in range(n):
                    if i != j:
                        r_vec = p_j.position - p_i.position
                        r = np.linalg.norm(r_vec)
                        r_soft = 0.1  # Softening length
                        grav_accel += (
                            self.config.gravity_constant * p_j.mass * r_vec /
                            (r**2 + r_soft**2)**1.5
                        )
                acceleration[i] += grav_accel

        return acceleration, heating_rate

    def step(self) -> SimulationSnapshot:
        """Perform one time step using leapfrog integration."""
        # Compute current state
        self.compute_density_pressure()
        acceleration, heating_rate = self.compute_forces()

        n = len(self.particles)
        dt = self.config.dt

        # Leapfrog integration
        for i in range(n):
            # Update velocities (half step)
            self.particles[i].velocity += 0.5 * acceleration[i] * dt

            # Update positions
            self.particles[i].position += self.particles[i].velocity * dt

            # Update internal energy
            self.particles[i].internal_energy += heating_rate[i] * dt

            # Cooling (simplified)
            if self.config.cooling_enabled:
                cooling_rate = 0.1 * self.particles[i].density * \
                              (self.particles[i].temperature - 10.0)
                self.particles[i].internal_energy -= cooling_rate * dt
                self.particles[i].internal_energy = max(
                    self.particles[i].internal_energy, 0.1
                )

            # Update temperature from internal energy
            self.particles[i].temperature = self.particles[i].internal_energy

            # Periodic boundary conditions
            if self.config.periodic_boundaries:
                for dim in range(3):
                    if self.particles[i].position[dim] > self.config.box_size:
                        self.particles[i].position[dim] -= self.config.box_size
                    elif self.particles[i].position[dim] < 0:
                        self.particles[i].position[dim] += self.config.box_size

        # Recompute forces at new positions
        self.compute_density_pressure()
        acceleration_new, _ = self.compute_forces()

        # Complete velocity update
        for i in range(n):
            self.particles[i].velocity += 0.5 * acceleration_new[i] * dt

        # Update time
        self.time += dt

        # Create snapshot
        return self._create_snapshot()

    def _create_snapshot(self) -> SimulationSnapshot:
        """Create a snapshot of current simulation state."""
        n = len(self.particles)

        total_mass = sum(p.mass for p in self.particles)
        total_energy = sum(
            0.5 * p.mass * np.sum(p.velocity**2) +
            p.internal_energy * p.mass
            for p in self.particles
        )
        total_momentum = np.sum([p.mass * p.velocity for p in self.particles], axis=0)

        densities = [p.density for p in self.particles]
        temperatures = [p.temperature for p in self.particles]

        snapshot = SimulationSnapshot(
            time=self.time,
            particles=self.particles.copy(),
            total_mass=total_mass,
            total_energy=total_energy,
            total_momentum=total_momentum,
            max_density=max(densities),
            min_density=min(densities),
            mean_temperature=np.mean(temperatures)
        )

        # Compute derived properties
        snapshot.filamentarity = self._compute_filamentarity()
        snapshot.virial_parameter = self._compute_virial_parameter()

        return snapshot

    def _compute_filamentarity(self) -> float:
        """
        Compute filamentarity metric based on inertia tensor.

        Returns value between 0 (spherical) and 1 (highly filamentary).
        """
        positions = np.array([p.position for p in self.particles])
        masses = np.array([p.mass for p in self.particles])

        # Center of mass
        com = np.sum(positions * masses[:, None], axis=0) / np.sum(masses)
        centered = positions - com

        # Inertia tensor
        I = np.zeros((3, 3))
        for i in range(len(self.particles)):
            r = centered[i]
            I += masses[i] * (np.sum(r**2) * np.eye(3) - np.outer(r, r))

        # Eigenvalues of inertia tensor
        eigenvalues = np.linalg.eigvalsh(I)
        eigenvalues = np.sort(eigenvalues)

        # Filamentarity: ratio of smallest to largest eigenvalue
        if eigenvalues[2] > 1e-10:
            return 1.0 - eigenvalues[0] / eigenvalues[2]
        else:
            return 0.0

    def _compute_virial_parameter(self) -> float:
        """Compute virial parameter (2K/|U|)."""
        kinetic_energy = sum(
            0.5 * p.mass * np.sum(p.velocity**2)
            for p in self.particles
        )

        potential_energy = 0.0
        for i in range(len(self.particles)):
            for j in range(i + 1, len(self.particles)):
                r = np.linalg.norm(
                    self.particles[i].position - self.particles[j].position
                )
                potential_energy -= (
                    self.config.gravity_constant *
                    self.particles[i].mass * self.particles[j].mass / r
                )

        if abs(potential_energy) > 1e-10:
            return 2 * kinetic_energy / abs(potential_energy)
        else:
            return 0.0

    def run_simulation(
        self,
        num_steps: int,
        snapshot_interval: int = 10
    ) -> List[SimulationSnapshot]:
        """Run the simulation for a specified number of steps."""
        self.snapshots = []

        for step in range(num_steps):
            snapshot = self.step()

            if step % snapshot_interval == 0:
                self.snapshots.append(snapshot)
                print(f"Step {step}, Time: {self.time:.3f} Myr, "
                      f"T: {snapshot.mean_temperature:.1f} K, "
                      f"Fil: {snapshot.filamentarity:.3f}")

        return self.snapshots


class FilamentFormationSPH(GasDynamicsSPH):
    """
    Specialized SPH for filament formation in molecular clouds.

    Includes turbulence, magnetic fields, and radiative cooling
    to study filamentary structure formation.
    """

    def __init__(self, config: Optional[SPHConfig] = None):
        super().__init__(config)
        self.magnetic_field_strength = 0.0
        self.turbulent_spectrum = "burgers"  # burgers, kolmogorov

    def initialize_filament_cloud(
        self,
        num_particles: int,
        cloud_radius: float,
        magnetic_field: float = 1.0,
        mach_number: float = 5.0
    ) -> None:
        """
        Initialize cloud with conditions conducive to filament formation.

        Args:
            num_particles: Number of particles
            cloud_radius: Cloud radius
            magnetic_field: Initial magnetic field strength (microgauss)
            mach_number: Turbulent Mach number
        """
        self.initialize_molecular_cloud(
            num_particles,
            cloud_radius,
            temperature=10.0,
            turbulent_energy=mach_number * 0.2  # ~sound speed * Mach
        )

        self.magnetic_field_strength = magnetic_field

        # Add magnetic field to particles (uniform B field in z-direction)
        for p in self.particles:
            p.magnetic_field = np.array([0.0, 0.0, magnetic_field])

    def detect_filaments(self) -> List[Dict[str, Any]]:
        """
        Detect filaments in the current particle distribution.

        Uses density threshold and skeletonization approach.
        """
        filaments = []

        # Find high-density regions
        densities = np.array([p.density for p in self.particles])
        mean_density = np.mean(densities)
        threshold = 2.0 * mean_density

        high_density_indices = np.where(densities > threshold)[0]

        if len(high_density_indices) < 10:
            return filaments

        # Cluster high-density particles
        from scipy.cluster.hierarchy import fcluster, linkage

        positions = np.array([
            self.particles[i].position
            for i in high_density_indices
        ])

        # Hierarchical clustering
        Z = linkage(positions, method='ward')
        clusters = fcluster(Z, t=0.5, criterion='distance')

        # Analyze each cluster as potential filament
        for cluster_id in np.unique(clusters):
            cluster_indices = high_density_indices[clusters == cluster_id]

            if len(cluster_indices) < 10:
                continue

            cluster_positions = np.array([
                self.particles[i].position
                for i in cluster_indices
            ])

            # Compute principal axes
            centered = cluster_positions - np.mean(cluster_positions, axis=0)
            cov = np.cov(centered.T)
            eigenvalues, eigenvectors = np.linalg.eigh(cov)

            # Aspect ratio
            sorted_evals = np.sort(eigenvalues)
            aspect_ratio = sorted_evals[2] / (sorted_evals[0] + 1e-10)

            if aspect_ratio > 3.0:  # Filamentary structure
                filament = {
                    'id': len(filaments),
                    'num_particles': len(cluster_indices),
                    'center': np.mean(cluster_positions, axis=0).tolist(),
                    'length': 2 * np.sqrt(sorted_evals[2]),
                    'width': 2 * np.sqrt(sorted_evals[0]),
                    'aspect_ratio': aspect_ratio,
                    'orientation': eigenvectors[:, 2].tolist(),
                    'mean_density': np.mean([
                        self.particles[i].density for i in cluster_indices
                    ]),
                    'total_mass': np.sum([
                        self.particles[i].mass for i in cluster_indices
                    ])
                }
                filaments.append(filament)

        return filaments


class RadiativeTransferSolver:
    """
    Radiative transfer solver for SPH simulations.

    Computes observables at different wavelengths:
    - Radio (CO, HI lines)
    - Millimeter (dust continuum)
    - Sub-millimeter (JCMT, ALMA)
    - Infrared (Spitzer, JWST)
    """

    def __init__(self):
        self.frequencies = {
            'radio_21cm': 1.42e9,  # Hz
            'radio_co': 115.27e9,
            'mm_1mm': 300e9,
            'submm_850um': 353e9,
            'ir_3_6um': 83e12,
            'ir_70um': 4.3e12
        }

    def compute_co_emission(
        self,
        particles: List[SPHParticle],
        velocity_channel: float
    ) -> np.ndarray:
        """
        Compute CO emission map.

        Args:
            particles: SPH particles
            velocity_channel: Velocity channel width (km/s)

        Returns:
            2D emission map
        """
        # Project particles onto sky plane (x, y)
        # Use velocity along z-axis for Doppler shift

        grid_size = 100
        emission_map = np.zeros((grid_size, grid_size))

        for p in particles:
            # Position in grid coordinates
            x_idx = int((p.position[0] / self.config.box_size) * grid_size)
            y_idx = int((p.position[1] / self.config.box_size) * grid_size)

            if 0 <= x_idx < grid_size and 0 <= y_idx < grid_size:
                # CO intensity proportional to density and temperature
                intensity = p.density * p.temperature * np.exp(
                    -((p.velocity[2] - velocity_channel)**2) / (2 * 0.5**2)
                )
                emission_map[y_idx, x_idx] += intensity

        return emission_map

    def compute_dust_continuum(
        self,
        particles: List[SPHParticle],
        frequency: float
    ) -> np.ndarray:
        """
        Compute dust continuum emission.

        Dust emission follows modified blackbody law.
        """
        grid_size = 100
        emission_map = np.zeros((grid_size, grid_size))

        # Physical constants
        h = 6.626e-34  # Planck constant
        k = 1.381e-23  # Boltzmann constant
        c = 3e8  # Speed of light

        # Dust properties
        beta = 1.5  # Dust emissivity index
        kappa_0 = 0.1  # Dust opacity at reference frequency

        for p in particles:
            x_idx = int((p.position[0] / self.config.box_size) * grid_size)
            y_idx = int((p.position[1] / self.config.box_size) * grid_size)

            if 0 <= x_idx < grid_size and 0 <= y_idx < grid_size:
                # Modified blackbody
                x = h * frequency / (k * p.temperature)
                if x > 0:
                    B_nu = (2 * h * frequency**3 / c**2) / (np.exp(x) - 1)
                    tau = kappa_0 * (frequency / 1e12)**beta * p.density
                    intensity = B_nu * (1 - np.exp(-tau))
                    emission_map[y_idx, x_idx] += intensity

        return emission_map

    def compute_synchrotron_emission(
        self,
        particles: List[SPHParticle],
        frequency: float
    ) -> np.ndarray:
        """
        Compute synchrotron emission from relativistic electrons.

        Important for radio wavelengths.
        """
        grid_size = 100
        emission_map = np.zeros((grid_size, grid_size))

        for p in particles:
            x_idx = int((p.position[0] / self.config.box_size) * grid_size)
            y_idx = int((p.position[1] / self.config.box_size) * grid_size)

            if 0 <= x_idx < grid_size and 0 <= y_idx < grid_size:
                # Synchrotron intensity proportional to magnetic field
                if p.magnetic_field is not None:
                    B_perp = np.linalg.norm(p.magnetic_field[:2])  # Perpendicular component
                    intensity = p.density * B_perp**2 * (frequency / 1e9)**(-0.7)
                    emission_map[y_idx, x_idx] += intensity

        return emission_map

    def compute_multi_wavelength_observation(
        self,
        snapshot: SimulationSnapshot
    ) -> Dict[str, np.ndarray]:
        """
        Compute observables at multiple wavelengths.

        Returns:
            Dictionary of wavelength -> emission map
        """
        observations = {}

        # CO line emission (multiple velocity channels)
        for v_channel in np.linspace(-5, 5, 10):
            obs_key = f'co_v_{v_channel:.1f}'
            observations[obs_key] = self.compute_co_emission(
                snapshot.particles, v_channel
            )

        # Dust continuum at different wavelengths
        for wave_name, freq in self.frequencies.items():
            if 'mm' in wave_name or 'submm' in wave_name:
                observations[wave_name] = self.compute_dust_continuum(
                    snapshot.particles, freq
                )

        # Synchrotron at radio
        observations['radio_synchrotron'] = self.compute_synchrotron_emission(
            snapshot.particles, self.frequencies['radio_21cm']
        )

        return observations


class StarFormationSPH(GasDynamicsSPH):
    """
    SPH simulation for star formation in molecular clouds.

    Includes:
    - Sink particles for gravitationally bound regions
    - Jeans instability criterion
    - Stellar feedback
    """

    def __init__(self, config: Optional[SPHConfig] = None):
        super().__init__(config)
        self.sink_particles: List[SPHParticle] = []
        self.star_formation_threshold = 100.0  # Density threshold
        self.jeans_mass = 0.0

    def check_star_formation(self) -> List[SPHParticle]:
        """
        Check for star formation using Jeans instability criterion.

        Returns:
            List of newly formed star particles
        """
        new_stars = []

        for p in self.particles:
            # Skip if already a star
            if p.particle_type == "star":
                continue

            # Jeans instability: rho > rho_crit and T < T_crit
            if p.density > self.star_formation_threshold and p.temperature < 20.0:
                # Check gravitational binding (Virial parameter < 1)
                local_virial = self._compute_local_virial_parameter(p)

                if local_virial < 1.0:
                    # Convert to star particle
                    star = SPHParticle(
                        position=p.position.copy(),
                        velocity=p.velocity.copy(),
                        mass=p.mass,
                        particle_type="star",
                        temperature=p.temperature,
                        particle_id=len(self.sink_particles) + len(new_stars)
                    )
                    new_stars.append(star)

        return new_stars

    def _compute_local_virial_parameter(self, particle: SPHParticle) -> float:
        """Compute local virial parameter for a particle."""
        # Find neighbors within smoothing length
        neighbors = [
            p for p in self.particles
            if np.linalg.norm(p.position - particle.position) < particle.smoothing_length
        ]

        if len(neighbors) < 5:
            return 100.0  # Not bound

        # Local kinetic energy
        ke_local = sum(
            0.5 * p.mass * np.sum(p.velocity**2)
            for p in neighbors
        )

        # Local potential energy (simplified)
        pe_local = 0.0
        for i, p1 in enumerate(neighbors):
            for p2 in neighbors[i+1:]:
                r = np.linalg.norm(p1.position - p2.position)
                pe_local -= (
                    self.config.gravity_constant * p1.mass * p2.mass / (r + 0.01)
                )

        if abs(pe_local) > 1e-10:
            return 2 * ke_local / abs(pe_local)
        else:
            return 0.0

    def apply_stellar_feedback(self, stars: List[SPHParticle]) -> None:
        """
        Apply stellar feedback to surrounding gas.

        Includes:
        - Ionizing radiation (HII regions)
        - Stellar winds
        - Supernovae
        """
        for star in stars:
            # Find nearby gas particles
            for gas in self.particles:
                if gas.particle_type != "gas":
                    continue

                r = np.linalg.norm(star.position - gas.position)

                if r < 2.0:  # Feedback radius
                    # Heating from ionizing radiation
                    gas.temperature += 1000.0 * np.exp(-r / 0.5)

                    # Momentum kick from stellar wind
                    r_hat = (gas.position - star.position) / (r + 1e-10)
                    gas.velocity += 0.1 * r_hat * np.exp(-r / 0.5)

                    # Enrichment (metals)
                    gas.metals += 0.01 * np.exp(-r / 0.5)

    def compute_star_formation_rate(
        self,
        time_window: float = 0.1
    ) -> float:
        """Compute star formation rate over time window."""
        recent_stars = [
            s for s in self.sink_particles
            if hasattr(s, 'formation_time') and
            (self.time - s.formation_time) < time_window
        ]

        total_mass = sum(s.mass for s in recent_stars)
        return total_mass / time_window


class HIISimulation:
    """
    Simulation of HII region expansion around massive stars.

    Models the ionization front expansion and champagne flows.
    """

    def __init__(self, grid_size: int = 100):
        self.grid_size = grid_size
        self.box_size = 10.0  # parsecs
        self.ionization_map = np.zeros((grid_size, grid_size, grid_size))
        self.temperature_map = np.ones((grid_size, grid_size, grid_size)) * 10.0
        self.density_map = np.ones((grid_size, grid_size, grid_size)) * 100.0

    def place_massive_star(self, position: np.ndarray, luminosity: float) -> None:
        """Place a massive ionizing star."""
        # Convert position to grid indices
        x = int((position[0] / self.box_size) * self.grid_size)
        y = int((position[1] / self.box_size) * self.grid_size)
        z = int((position[2] / self.box_size) * self.grid_size)

        # Set ionization source
        self.ionization_map[x, y, z] = luminosity

    def evolve_ionization_front(self, dt: float) -> None:
        """
        Evolve ionization front using Strömgren sphere approximation.

        The ionization front expands until recombination balances ionization.
        """
        # Recombination coefficient (case B)
        alpha_B = 2.6e-13  # cm^3/s

        # Ionizing photon rate
        Q = self.ionization_map

        # Strömgren radius (simplified)
        # Rs = (3Q / 4pi n^2 alpha_B)^(1/3)

        # Propagate ionization front using simplified approach
        new_ionization = self.ionization_map.copy()

        for x in range(1, self.grid_size - 1):
            for y in range(1, self.grid_size - 1):
                for z in range(1, self.grid_size - 1):
                    if self.ionization_map[x, y, z] > 0:
                        # Ionization spreads to neighbors
                        for dx in [-1, 0, 1]:
                            for dy in [-1, 0, 1]:
                                for dz in [-1, 0, 1]:
                                    if dx == 0 and dy == 0 and dz == 0:
                                        continue

                                    nx, ny, nz = x + dx, y + dy, z + dz

                                    # Ionization rate proportional to source
                                    rate = self.ionization_map[x, y, z] * dt * 0.1

                                    # Recombination loss
                                    loss = alpha_B * self.density_map[nx, ny, nz]**2 * dt

                                    new_ionization[nx, ny, nz] += rate - loss

                                    # Temperature in ionized region
                                    if new_ionization[nx, ny, nz] > 0:
                                        self.temperature_map[nx, ny, nz] = 10000.0

        self.ionization_map = np.maximum(new_ionization, 0.0)

    def compute_radio_emission(self, frequency: float) -> np.ndarray:
        """
        Compute radio free-free emission from HII region.

        Free-free emission scales as T^(-0.35) at radio wavelengths.
        """
        emission = np.zeros((self.grid_size, self.grid_size))

        # Project onto 2D plane
        for x in range(self.grid_size):
            for y in range(self.grid_size):
                # Integrate along line of sight
                intensity = 0.0
                for z in range(self.grid_size):
                    if self.ionization_map[x, y, z] > 0:
                        # Free-free emission
                        intensity += (
                            self.temperature_map[x, y, z]**(-0.35) *
                            self.density_map[x, y, z]**2 *
                            self.ionization_map[x, y, z]
                        )

                emission[x, y] = intensity

        return emission


# =============================================================================
# Factory Functions
# =============================================================================

def create_gas_dynamics_simulation(
    num_particles: int = 1000,
    box_size: float = 10.0
) -> GasDynamicsSPH:
    """Create a basic gas dynamics SPH simulation."""
    config = SPHConfig(
        num_particles=num_particles,
        box_size=box_size,
        dt=0.001,
        smoothing_length_ratio=0.5
    )
    sim = GasDynamicsSPH(config)
    sim.initialize_molecular_cloud(num_particles, box_size / 2)
    return sim


def create_filament_simulation(
    num_particles: int = 2000,
    cloud_radius: float = 5.0,
    magnetic_field: float = 10.0,
    mach_number: float = 5.0
) -> FilamentFormationSPH:
    """Create a filament formation simulation."""
    config = SPHConfig(
        num_particles=num_particles,
        box_size=cloud_radius * 4,
        dt=0.0005,
        smoothing_length_ratio=0.5,
        magnetic_enabled=True
    )
    sim = FilamentFormationSPH(config)
    sim.initialize_filament_cloud(num_particles, cloud_radius, magnetic_field, mach_number)
    return sim


def create_star_formation_simulation(
    num_particles: int = 2000,
    cloud_radius: float = 5.0
) -> StarFormationSPH:
    """Create a star formation simulation."""
    config = SPHConfig(
        num_particles=num_particles,
        box_size=cloud_radius * 4,
        dt=0.0005,
        self_gravity=True,
        cooling_enabled=True
    )
    sim = StarFormationSPH(config)
    sim.initialize_molecular_cloud(num_particles, cloud_radius, temperature=10.0)
    return sim


# =============================================================================
# Self-Improving Integration
# =============================================================================

class SPHSelfImprovingSystem:
    """
    Self-improving SPH system that learns optimal parameters
    from simulation results.
    """

    def __init__(self):
        self.simulation_history: List[Dict] = []
        self.performance_metrics: List[Dict] = []
        self.best_parameters: Dict = {}

    def run_parameter_sweep(
        self,
        parameter_ranges: Dict[str, Tuple[float, float]],
        objective_fn: Callable,
        n_iterations: int = 20
    ) -> Dict:
        """
        Perform parameter sweep to find optimal SPH parameters.

        Args:
            parameter_ranges: Dictionary of parameter -> (min, max)
            objective_fn: Function that evaluates simulation quality
            n_iterations: Number of iterations

        Returns:
            Best parameters and their score
        """
        best_score = -np.inf
        best_params = None

        for iteration in range(n_iterations):
            # Sample parameters
            params = {}
            for param, (min_val, max_val) in parameter_ranges.items():
                params[param] = np.random.uniform(min_val, max_val)

            # Run simulation
            config = SPHConfig(**params)
            sim = GasDynamicsSPH(config)
            sim.initialize_molecular_cloud(
                config.num_particles,
                config.box_size / 2
            )

            snapshots = sim.run_simulation(num_steps=100, snapshot_interval=10)

            # Evaluate
            score = objective_fn(snapshots)

            self.simulation_history.append({
                'iteration': iteration,
                'parameters': params,
                'score': score,
                'final_filamentarity': snapshots[-1].filamentarity if snapshots else 0.0
            })

            if score > best_score:
                best_score = score
                best_params = params

        self.best_parameters = best_params
        return best_params
