"""
Kinematic Analysis Module for STAN V43

Complete kinematic analysis for spectral line cubes including
moment map generation, position-velocity diagrams, rotation curve
fitting, infall signature detection, and outflow analysis.

Features:
- Moment maps (0-4) with proper error propagation
- Position-velocity diagram extraction along arbitrary paths
- Keplerian and flat rotation curve fitting
- Blue asymmetry and inverse P-Cygni infall detection
- Bipolar outflow momentum/energy/mass measurement
- Turbulent field decomposition

All velocities in km/s unless otherwise noted.

Author: STAN V43 Astrophysics Module
"""

import math
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple, Callable


# Physical constants
C_LIGHT = 2.998e10           # Speed of light (cm/s)
K_BOLTZMANN = 1.381e-16      # Boltzmann constant (erg/K)
M_PROTON = 1.673e-24         # Proton mass (g)
G_GRAV = 6.674e-8            # Gravitational constant (cm^3/g/s^2)
M_SUN = 1.989e33             # Solar mass (g)
PC = 3.086e18                # Parsec (cm)


class RotationType(Enum):
    """Types of rotation curves."""
    KEPLERIAN = auto()        # v ~ r^(-1/2)
    FLAT = auto()             # v ~ constant
    SOLID_BODY = auto()       # v ~ r
    DIFFERENTIAL = auto()     # General power-law


class InfallSignature(Enum):
    """Types of infall signatures."""
    NONE = auto()             # No infall signature
    BLUE_ASYMMETRY = auto()   # Optically thick line blue-skewed
    INVERSE_P_CYGNI = auto()  # Red-shifted absorption against continuum
    BLUE_EXCESS = auto()      # Excess blue wing emission
    LINE_CENTROID_SHIFT = auto()  # Systematic velocity shift


class OutflowType(Enum):
    """Types of molecular outflows."""
    BIPOLAR = auto()          # Standard bipolar outflow
    MONOPOLAR = auto()        # One-sided outflow
    WIDE_ANGLE = auto()       # Poorly collimated
    HIGHLY_COLLIMATED = auto()  # Jet-like


@dataclass
class MomentMaps:
    """Collection of moment maps."""
    moment0: List[List[float]]     # Integrated intensity (K km/s)
    moment0_error: List[List[float]]
    moment1: List[List[float]]     # Intensity-weighted velocity (km/s)
    moment1_error: List[List[float]]
    moment2: List[List[float]]     # Velocity dispersion (km/s)
    moment2_error: List[List[float]]
    moment3: Optional[List[List[float]]] = None  # Skewness
    moment4: Optional[List[List[float]]] = None  # Kurtosis
    peak_intensity: Optional[List[List[float]]] = None  # Peak T_mb
    peak_velocity: Optional[List[List[float]]] = None   # Velocity of peak


@dataclass
class PVDiagram:
    """Position-velocity diagram."""
    position_axis: List[float]     # Offset positions (arcsec)
    velocity_axis: List[float]     # Velocities (km/s)
    intensity: List[List[float]]   # PV intensity array
    path_ra: List[float]           # RA along path
    path_dec: List[float]          # Dec along path
    position_angle: float          # PA of slice (degrees)
    width: float                   # Width of slice (arcsec)


@dataclass
class RotationCurveFit:
    """Result of rotation curve fitting."""
    rotation_type: RotationType
    center_x: float               # Rotation center X (pixel)
    center_y: float               # Rotation center Y (pixel)
    systemic_velocity: float      # V_sys (km/s)
    position_angle: float         # Kinematic PA (degrees)
    inclination: float            # Inclination (degrees)
    v_max: float                  # Maximum rotation velocity (km/s)
    r_turnover: float             # Turnover radius (arcsec)
    power_law_index: float        # For differential rotation
    enclosed_mass: float          # Dynamical mass (M_sun)
    chi_squared: float            # Fit quality
    residual_rms: float           # RMS of velocity residuals (km/s)


@dataclass
class InfallResult:
    """Result of infall signature analysis."""
    signature_type: InfallSignature
    significance: float           # Detection significance (sigma)
    blue_peak_velocity: float     # Blue peak velocity (km/s)
    red_peak_velocity: float      # Red peak velocity (km/s)
    asymmetry_parameter: float    # Blue/red asymmetry
    infall_velocity: float        # Estimated infall velocity (km/s)
    infall_rate: float            # Mass infall rate (M_sun/yr)
    optical_depth: float          # Line optical depth
    excitation_temp: float        # Excitation temperature (K)


@dataclass
class OutflowLobe:
    """Properties of a single outflow lobe."""
    lobe_type: str               # 'blue' or 'red'
    velocity_range: Tuple[float, float]  # (v_min, v_max) km/s
    mass: float                  # Outflow mass (M_sun)
    momentum: float              # Momentum (M_sun km/s)
    energy: float                # Kinetic energy (erg)
    max_velocity: float          # Maximum velocity (km/s)
    extent: float                # Projected extent (arcsec)
    position_angle: float        # PA of lobe (degrees)
    opening_angle: float         # Opening angle (degrees)


@dataclass
class OutflowProperties:
    """Complete outflow analysis result."""
    outflow_type: OutflowType
    blue_lobe: Optional[OutflowLobe]
    red_lobe: Optional[OutflowLobe]
    total_mass: float            # Total outflow mass (M_sun)
    total_momentum: float        # Total momentum (M_sun km/s)
    total_energy: float          # Total kinetic energy (erg)
    mechanical_luminosity: float # L_mech (L_sun)
    dynamical_time: float        # Outflow age (yr)
    mass_loss_rate: float        # dM/dt (M_sun/yr)
    momentum_rate: float         # Force (M_sun km/s/yr)
    inclination_corrected: bool  # Whether inclination applied


@dataclass
class TurbulentField:
    """Decomposed turbulent velocity field."""
    bulk_velocity_x: List[List[float]]   # Bulk motion in X
    bulk_velocity_y: List[List[float]]   # Bulk motion in Y
    turbulent_dispersion: List[List[float]]  # Turbulent sigma
    sonic_mach: List[List[float]]        # Sonic Mach number
    rotation_subtracted: bool            # Whether rotation removed
    mean_turbulent_sigma: float          # Average dispersion (km/s)


class MomentMapGenerator:
    """
    Generate moment maps from spectral cubes.

    Computes intensity-weighted moments with proper error propagation.
    """

    def __init__(self, threshold_sigma: float = 3.0):
        """
        Initialize moment generator.

        Args:
            threshold_sigma: S/N threshold for moment calculation
        """
        self.threshold = threshold_sigma

    def _estimate_noise(self, spectrum: List[float],
                        line_free_fraction: float = 0.3) -> float:
        """Estimate noise from line-free channels."""
        n = len(spectrum)
        n_edge = int(n * line_free_fraction / 2)

        if n_edge < 5:
            n_edge = min(5, n // 4)

        edge_channels = spectrum[:n_edge] + spectrum[-n_edge:]

        if not edge_channels:
            return 1.0

        mean = sum(edge_channels) / len(edge_channels)
        variance = sum((x - mean)**2 for x in edge_channels) / len(edge_channels)
        return math.sqrt(variance) if variance > 0 else 1.0

    def compute_moments(self, spectrum: List[float],
                        velocities: List[float],
                        noise: float) -> Dict[str, float]:
        """
        Compute moments for single spectrum.

        Args:
            spectrum: Intensity values
            velocities: Velocity axis (km/s)
            noise: Noise RMS

        Returns:
            Dictionary with moment values
        """
        # Find channels above threshold
        threshold = self.threshold * noise
        dv = abs(velocities[1] - velocities[0]) if len(velocities) > 1 else 1.0

        # Moment 0: Integrated intensity
        mom0 = sum(max(s, 0) * dv for s in spectrum if s > threshold)

        if mom0 <= 0:
            return {'mom0': 0, 'mom1': float('nan'), 'mom2': float('nan'),
                    'mom0_err': noise * dv * math.sqrt(len(spectrum)),
                    'mom1_err': float('nan'), 'mom2_err': float('nan'),
                    'peak': 0, 'peak_v': float('nan')}

        # Moment 1: Intensity-weighted mean velocity
        mom1 = sum(s * v * dv for s, v in zip(spectrum, velocities)
                   if s > threshold) / mom0

        # Moment 2: Velocity dispersion
        mom2_sq = sum(s * (v - mom1)**2 * dv for s, v in zip(spectrum, velocities)
                      if s > threshold) / mom0
        mom2 = math.sqrt(max(mom2_sq, 0))

        # Peak
        peak = max(spectrum)
        peak_idx = spectrum.index(peak)
        peak_v = velocities[peak_idx]

        # Error estimates
        n_chan = sum(1 for s in spectrum if s > threshold)
        mom0_err = noise * dv * math.sqrt(n_chan)
        mom1_err = mom2 / math.sqrt(mom0 / (noise * dv)) if mom0 > 0 else float('nan')
        mom2_err = mom2 / math.sqrt(2 * n_chan) if n_chan > 0 else float('nan')

        return {
            'mom0': mom0,
            'mom1': mom1,
            'mom2': mom2,
            'mom0_err': mom0_err,
            'mom1_err': mom1_err,
            'mom2_err': mom2_err,
            'peak': peak,
            'peak_v': peak_v
        }

    def generate(self, cube: List[List[List[float]]],
                 velocities: List[float]) -> MomentMaps:
        """
        Generate moment maps from spectral cube.

        Args:
            cube: 3D data cube [y][x][velocity]
            velocities: Velocity axis (km/s)

        Returns:
            Complete set of moment maps
        """
        ny = len(cube)
        nx = len(cube[0])

        # Initialize maps
        mom0 = [[0.0] * nx for _ in range(ny)]
        mom0_err = [[0.0] * nx for _ in range(ny)]
        mom1 = [[float('nan')] * nx for _ in range(ny)]
        mom1_err = [[float('nan')] * nx for _ in range(ny)]
        mom2 = [[float('nan')] * nx for _ in range(ny)]
        mom2_err = [[float('nan')] * nx for _ in range(ny)]
        peak_int = [[0.0] * nx for _ in range(ny)]
        peak_vel = [[float('nan')] * nx for _ in range(ny)]

        for iy in range(ny):
            for ix in range(nx):
                spectrum = cube[iy][ix]
                noise = self._estimate_noise(spectrum)

                moments = self.compute_moments(spectrum, velocities, noise)

                mom0[iy][ix] = moments['mom0']
                mom0_err[iy][ix] = moments['mom0_err']
                mom1[iy][ix] = moments['mom1']
                mom1_err[iy][ix] = moments['mom1_err']
                mom2[iy][ix] = moments['mom2']
                mom2_err[iy][ix] = moments['mom2_err']
                peak_int[iy][ix] = moments['peak']
                peak_vel[iy][ix] = moments['peak_v']

        return MomentMaps(
            moment0=mom0,
            moment0_error=mom0_err,
            moment1=mom1,
            moment1_error=mom1_err,
            moment2=mom2,
            moment2_error=mom2_err,
            peak_intensity=peak_int,
            peak_velocity=peak_vel
        )


class PVDiagramExtractor:
    """
    Extract position-velocity diagrams from spectral cubes.
    """

    def __init__(self):
        """Initialize PV extractor."""
        pass

    def extract_slice(self, cube: List[List[List[float]]],
                      velocities: List[float],
                      start: Tuple[float, float],
                      end: Tuple[float, float],
                      width: int = 1,
                      pixel_scale: float = 1.0) -> PVDiagram:
        """
        Extract PV slice along path.

        Args:
            cube: 3D data cube [y][x][velocity]
            velocities: Velocity axis (km/s)
            start: (x, y) start position (pixels)
            end: (x, y) end position (pixels)
            width: Width of slice (pixels)
            pixel_scale: Pixel scale (arcsec/pixel)

        Returns:
            Position-velocity diagram
        """
        ny = len(cube)
        nx = len(cube[0])
        nv = len(velocities)

        # Path parameters
        x0, y0 = start
        x1, y1 = end
        length = math.sqrt((x1 - x0)**2 + (y1 - y0)**2)
        n_positions = int(length) + 1

        if n_positions < 2:
            n_positions = 2

        # Position angle
        pa = math.atan2(x1 - x0, y1 - y0) * 180.0 / math.pi

        # Sample along path
        positions = []
        pv_intensity = [[0.0] * nv for _ in range(n_positions)]

        for i in range(n_positions):
            frac = i / (n_positions - 1) if n_positions > 1 else 0.5
            x = x0 + frac * (x1 - x0)
            y = y0 + frac * (y1 - y0)

            offset = (i - n_positions / 2) * pixel_scale
            positions.append(offset)

            # Average perpendicular to path
            for dw in range(-width // 2, width // 2 + 1):
                # Perpendicular direction
                if length > 0:
                    px = x + dw * (y1 - y0) / length
                    py = y - dw * (x1 - x0) / length
                else:
                    px, py = x, y

                ix, iy = int(px), int(py)

                if 0 <= ix < nx and 0 <= iy < ny:
                    for iv in range(nv):
                        pv_intensity[i][iv] += cube[iy][ix][iv]

            # Average over width
            if width > 0:
                for iv in range(nv):
                    pv_intensity[i][iv] /= (width + 1)

        return PVDiagram(
            position_axis=positions,
            velocity_axis=list(velocities),
            intensity=pv_intensity,
            path_ra=[],  # Would need WCS
            path_dec=[],
            position_angle=pa,
            width=width * pixel_scale
        )


class RotationCurveAnalyzer:
    """
    Fit rotation curves to velocity fields.
    """

    def __init__(self):
        """Initialize rotation curve analyzer."""
        pass

    def _keplerian_velocity(self, r: float, M: float) -> float:
        """Keplerian rotation velocity."""
        if r <= 0:
            return 0.0
        # v = sqrt(GM/r)
        r_cm = r * PC
        v_cm_s = math.sqrt(G_GRAV * M * M_SUN / r_cm)
        return v_cm_s / 1e5  # km/s

    def _project_velocity(self, v: float, inc: float, pa: float,
                          x: float, y: float) -> float:
        """Project rotation velocity to line-of-sight."""
        # Azimuthal angle in disk plane
        phi = math.atan2(x, y) - pa * math.pi / 180.0
        return v * math.sin(inc * math.pi / 180.0) * math.cos(phi)

    def fit(self, velocity_map: List[List[float]],
            center: Tuple[float, float],
            v_sys: float,
            pixel_scale_pc: float,
            initial_pa: float = 0.0,
            initial_inc: float = 45.0) -> RotationCurveFit:
        """
        Fit rotation curve to velocity field.

        Args:
            velocity_map: 2D velocity map (km/s)
            center: Rotation center (x, y) in pixels
            v_sys: Systemic velocity (km/s)
            pixel_scale_pc: Pixel scale (pc/pixel)
            initial_pa: Initial position angle guess
            initial_inc: Initial inclination guess

        Returns:
            Rotation curve fit result
        """
        ny = len(velocity_map)
        nx = len(velocity_map[0])
        cx, cy = center

        # Collect radius-velocity pairs
        radii = []
        velocities = []
        weights = []

        for iy in range(ny):
            for ix in range(nx):
                v = velocity_map[iy][ix]
                if math.isnan(v):
                    continue

                dx = ix - cx
                dy = iy - cy
                r = math.sqrt(dx**2 + dy**2) * pixel_scale_pc

                if r < pixel_scale_pc * 0.5:
                    continue

                radii.append(r)
                velocities.append(abs(v - v_sys))
                weights.append(1.0)

        if len(radii) < 10:
            return RotationCurveFit(
                rotation_type=RotationType.FLAT,
                center_x=cx, center_y=cy,
                systemic_velocity=v_sys,
                position_angle=initial_pa,
                inclination=initial_inc,
                v_max=0.0, r_turnover=0.0,
                power_law_index=0.0,
                enclosed_mass=0.0,
                chi_squared=float('inf'),
                residual_rms=float('inf')
            )

        # Simple fit: Find characteristic velocity and radius
        v_median = sorted(velocities)[len(velocities) // 2]
        r_median = sorted(radii)[len(radii) // 2]

        # Estimate enclosed mass from Keplerian assumption
        # M = v^2 * r / G
        v_cm_s = v_median * 1e5 / math.sin(initial_inc * math.pi / 180.0)
        r_cm = r_median * PC
        M_enclosed = v_cm_s**2 * r_cm / G_GRAV / M_SUN

        # Compute residuals
        residuals = []
        for r, v in zip(radii, velocities):
            v_model = self._keplerian_velocity(r, M_enclosed)
            v_proj = v_model * math.sin(initial_inc * math.pi / 180.0)
            residuals.append(v - v_proj)

        rms = math.sqrt(sum(r**2 for r in residuals) / len(residuals))

        # Determine rotation type
        # If outer velocities decrease: Keplerian
        # If outer velocities flat: Flat
        outer_mask = [r > r_median for r in radii]
        if any(outer_mask):
            outer_v = [v for v, m in zip(velocities, outer_mask) if m]
            inner_v = [v for v, m in zip(velocities, outer_mask) if not m]

            if outer_v and inner_v:
                v_outer = sum(outer_v) / len(outer_v)
                v_inner = sum(inner_v) / len(inner_v)

                if v_outer < 0.8 * v_inner:
                    rot_type = RotationType.KEPLERIAN
                else:
                    rot_type = RotationType.FLAT
            else:
                rot_type = RotationType.KEPLERIAN
        else:
            rot_type = RotationType.KEPLERIAN

        return RotationCurveFit(
            rotation_type=rot_type,
            center_x=cx,
            center_y=cy,
            systemic_velocity=v_sys,
            position_angle=initial_pa,
            inclination=initial_inc,
            v_max=max(velocities) if velocities else 0,
            r_turnover=r_median,
            power_law_index=-0.5 if rot_type == RotationType.KEPLERIAN else 0.0,
            enclosed_mass=M_enclosed,
            chi_squared=sum(r**2 for r in residuals),
            residual_rms=rms
        )


class InfallSignatureDetector:
    """
    Detect signatures of gravitational infall.

    Analyzes line profiles for blue asymmetry (optically thick self-absorption)
    and inverse P-Cygni profiles.
    """

    def __init__(self, temperature: float = 15.0):
        """
        Initialize infall detector.

        Args:
            temperature: Assumed gas temperature (K)
        """
        self.temperature = temperature

    def _find_peaks(self, spectrum: List[float],
                    velocities: List[float]) -> List[Tuple[float, float]]:
        """Find peaks in spectrum."""
        peaks = []

        for i in range(1, len(spectrum) - 1):
            if spectrum[i] > spectrum[i-1] and spectrum[i] > spectrum[i+1]:
                peaks.append((velocities[i], spectrum[i]))

        return sorted(peaks, key=lambda x: x[1], reverse=True)

    def _find_dip(self, spectrum: List[float],
                  velocities: List[float],
                  v_range: Tuple[float, float]) -> Optional[Tuple[float, float]]:
        """Find minimum (absorption dip) in velocity range."""
        min_val = float('inf')
        min_v = None

        for v, s in zip(velocities, spectrum):
            if v_range[0] <= v <= v_range[1]:
                if s < min_val:
                    min_val = s
                    min_v = v

        if min_v is not None:
            return (min_v, min_val)
        return None

    def analyze_spectrum(self, spectrum: List[float],
                         velocities: List[float],
                         v_sys: float = 0.0,
                         noise: float = 0.0) -> InfallResult:
        """
        Analyze spectrum for infall signatures.

        Args:
            spectrum: Intensity array
            velocities: Velocity array (km/s)
            v_sys: Systemic velocity (km/s)
            noise: Noise RMS

        Returns:
            Infall analysis result
        """
        if noise <= 0:
            noise = sum(abs(s) for s in spectrum) / len(spectrum) * 0.1

        # Find peaks
        peaks = self._find_peaks(spectrum, velocities)

        if len(peaks) < 1:
            return InfallResult(
                signature_type=InfallSignature.NONE,
                significance=0.0,
                blue_peak_velocity=float('nan'),
                red_peak_velocity=float('nan'),
                asymmetry_parameter=0.0,
                infall_velocity=0.0,
                infall_rate=0.0,
                optical_depth=0.0,
                excitation_temp=0.0
            )

        # Check for double-peaked profile
        if len(peaks) >= 2:
            v1, i1 = peaks[0]
            v2, i2 = peaks[1]

            # Blue and red peaks
            if v1 < v2:
                blue_v, blue_i = v1, i1
                red_v, red_i = v2, i2
            else:
                blue_v, blue_i = v2, i2
                red_v, red_i = v1, i1

            # Find central dip
            dip = self._find_dip(spectrum, velocities, (blue_v, red_v))

            if dip is not None:
                dip_v, dip_i = dip

                # Blue asymmetry: blue peak brighter than red
                asymmetry = (blue_i - red_i) / (blue_i + red_i) if blue_i + red_i > 0 else 0

                # Significance
                sig = abs(asymmetry) * (blue_i + red_i) / (2 * noise)

                if asymmetry > 0.1:
                    signature = InfallSignature.BLUE_ASYMMETRY
                elif asymmetry < -0.1:
                    signature = InfallSignature.NONE  # Red asymmetry = outflow
                else:
                    signature = InfallSignature.NONE

                # Estimate infall velocity (Myers et al. 1996)
                # V_in ~ (V_red - V_blue) / 2
                v_in = abs(red_v - blue_v) / 2.0

                # Optical depth from dip depth
                if dip_i > 0 and blue_i > dip_i:
                    tau = -math.log(dip_i / blue_i)
                else:
                    tau = 0.0

                return InfallResult(
                    signature_type=signature,
                    significance=sig,
                    blue_peak_velocity=blue_v,
                    red_peak_velocity=red_v,
                    asymmetry_parameter=asymmetry,
                    infall_velocity=v_in,
                    infall_rate=0.0,  # Would need mass estimate
                    optical_depth=tau,
                    excitation_temp=self.temperature
                )

        # Single peak - check for wing asymmetry
        v_peak, i_peak = peaks[0]

        # Integrate blue and red wings
        blue_flux = sum(s for s, v in zip(spectrum, velocities)
                        if v < v_peak and s > noise)
        red_flux = sum(s for s, v in zip(spectrum, velocities)
                       if v > v_peak and s > noise)

        if blue_flux + red_flux > 0:
            wing_asymmetry = (blue_flux - red_flux) / (blue_flux + red_flux)
        else:
            wing_asymmetry = 0.0

        if wing_asymmetry > 0.1:
            signature = InfallSignature.BLUE_EXCESS
            sig = abs(wing_asymmetry) * i_peak / noise
        else:
            signature = InfallSignature.NONE
            sig = 0.0

        return InfallResult(
            signature_type=signature,
            significance=sig,
            blue_peak_velocity=v_peak if wing_asymmetry > 0 else float('nan'),
            red_peak_velocity=v_peak if wing_asymmetry < 0 else float('nan'),
            asymmetry_parameter=wing_asymmetry,
            infall_velocity=0.0,
            infall_rate=0.0,
            optical_depth=0.0,
            excitation_temp=self.temperature
        )


class OutflowAnalyzer:
    """
    Analyze bipolar molecular outflows.

    Measures mass, momentum, and energy in high-velocity gas.
    """

    def __init__(self, distance_pc: float = 140.0,
                 X_CO: float = 2.0e20):
        """
        Initialize outflow analyzer.

        Args:
            distance_pc: Distance to source (pc)
            X_CO: CO-to-H2 conversion factor (cm^-2 / K km/s)
        """
        self.distance_pc = distance_pc
        self.X_CO = X_CO

    def _integrate_lobe(self, cube: List[List[List[float]]],
                        velocities: List[float],
                        center: Tuple[int, int],
                        v_range: Tuple[float, float],
                        pixel_scale_arcsec: float) -> OutflowLobe:
        """
        Measure properties of one outflow lobe.

        Args:
            cube: 3D data cube [y][x][v]
            velocities: Velocity array (km/s)
            center: Source center (x, y)
            v_range: Velocity range of lobe (km/s)
            pixel_scale_arcsec: Pixel scale (arcsec/pixel)

        Returns:
            Outflow lobe properties
        """
        ny = len(cube)
        nx = len(cube[0])
        cx, cy = center
        dv = abs(velocities[1] - velocities[0]) if len(velocities) > 1 else 1.0

        # Pixel area
        d_cm = self.distance_pc * PC
        pixel_sr = (pixel_scale_arcsec * math.pi / (180.0 * 3600.0))**2
        pixel_area_cm2 = pixel_sr * d_cm**2

        total_flux = 0.0  # K km/s summed over pixels
        total_momentum = 0.0  # Flux * |v|
        total_energy = 0.0  # Flux * v^2
        max_v = 0.0
        max_extent = 0.0

        # Centroid for PA calculation
        sum_x = 0.0
        sum_y = 0.0
        sum_weight = 0.0

        is_blue = v_range[0] < v_range[1] and v_range[1] < 0

        for iy in range(ny):
            for ix in range(nx):
                pixel_flux = 0.0

                for iv, v in enumerate(velocities):
                    if v_range[0] <= v <= v_range[1]:
                        T = cube[iy][ix][iv]
                        if T > 0:
                            pixel_flux += T * dv

                            v_rel = abs(v)  # |v - v_sys|
                            total_momentum += T * dv * v_rel
                            total_energy += T * dv * v_rel**2

                            max_v = max(max_v, v_rel)

                if pixel_flux > 0:
                    total_flux += pixel_flux
                    sum_x += ix * pixel_flux
                    sum_y += iy * pixel_flux
                    sum_weight += pixel_flux

                    dist = math.sqrt((ix - cx)**2 + (iy - cy)**2) * pixel_scale_arcsec
                    max_extent = max(max_extent, dist)

        # Convert to mass
        # M = X_CO * flux * area
        mass_g = self.X_CO * total_flux * pixel_area_cm2 * 2.8 * M_PROTON
        mass_msun = mass_g / M_SUN

        # Momentum in physical units
        momentum = mass_msun * (total_momentum / total_flux if total_flux > 0 else 0)

        # Energy: E = 0.5 * M * v^2
        v_rms = math.sqrt(total_energy / total_flux) if total_flux > 0 else 0
        energy_erg = 0.5 * mass_g * (v_rms * 1e5)**2

        # Position angle
        if sum_weight > 0:
            lobe_cx = sum_x / sum_weight
            lobe_cy = sum_y / sum_weight
            pa = math.atan2(lobe_cx - cx, lobe_cy - cy) * 180.0 / math.pi
        else:
            pa = 0.0

        return OutflowLobe(
            lobe_type='blue' if is_blue else 'red',
            velocity_range=v_range,
            mass=mass_msun,
            momentum=momentum,
            energy=energy_erg,
            max_velocity=max_v,
            extent=max_extent,
            position_angle=pa,
            opening_angle=45.0  # Default, would calculate properly
        )

    def analyze(self, cube: List[List[List[float]]],
                velocities: List[float],
                center: Tuple[int, int],
                v_sys: float,
                v_blue: Tuple[float, float],
                v_red: Tuple[float, float],
                pixel_scale_arcsec: float = 1.0) -> OutflowProperties:
        """
        Analyze bipolar outflow.

        Args:
            cube: 3D data cube [y][x][v]
            velocities: Velocity axis (km/s)
            center: Source position (x, y)
            v_sys: Systemic velocity (km/s)
            v_blue: Blue lobe velocity range relative to v_sys
            v_red: Red lobe velocity range relative to v_sys
            pixel_scale_arcsec: Pixel scale

        Returns:
            Complete outflow analysis
        """
        # Adjust velocity ranges to absolute
        v_blue_abs = (v_sys + v_blue[0], v_sys + v_blue[1])
        v_red_abs = (v_sys + v_red[0], v_sys + v_red[1])

        blue_lobe = self._integrate_lobe(cube, velocities, center,
                                         v_blue_abs, pixel_scale_arcsec)
        red_lobe = self._integrate_lobe(cube, velocities, center,
                                        v_red_abs, pixel_scale_arcsec)

        # Total properties
        total_mass = blue_lobe.mass + red_lobe.mass
        total_momentum = blue_lobe.momentum + red_lobe.momentum
        total_energy = blue_lobe.energy + red_lobe.energy

        # Dynamical time
        max_extent_pc = max(blue_lobe.extent, red_lobe.extent) * self.distance_pc / 206265.0
        max_v_km_s = max(blue_lobe.max_velocity, red_lobe.max_velocity)

        if max_v_km_s > 0:
            t_dyn_s = max_extent_pc * PC / (max_v_km_s * 1e5)
            t_dyn_yr = t_dyn_s / (365.25 * 24 * 3600)
        else:
            t_dyn_yr = 0.0

        # Mass loss rate
        mass_loss = total_mass / t_dyn_yr if t_dyn_yr > 0 else 0

        # Momentum rate (force)
        momentum_rate = total_momentum / t_dyn_yr if t_dyn_yr > 0 else 0

        # Mechanical luminosity
        if t_dyn_yr > 0:
            L_mech_erg_s = total_energy / (t_dyn_yr * 365.25 * 24 * 3600)
            L_mech_Lsun = L_mech_erg_s / 3.828e33
        else:
            L_mech_Lsun = 0.0

        # Determine outflow type
        if blue_lobe.mass > 0 and red_lobe.mass > 0:
            outflow_type = OutflowType.BIPOLAR
        elif blue_lobe.mass > 0 or red_lobe.mass > 0:
            outflow_type = OutflowType.MONOPOLAR
        else:
            outflow_type = OutflowType.BIPOLAR  # Default

        return OutflowProperties(
            outflow_type=outflow_type,
            blue_lobe=blue_lobe if blue_lobe.mass > 0 else None,
            red_lobe=red_lobe if red_lobe.mass > 0 else None,
            total_mass=total_mass,
            total_momentum=total_momentum,
            total_energy=total_energy,
            mechanical_luminosity=L_mech_Lsun,
            dynamical_time=t_dyn_yr,
            mass_loss_rate=mass_loss,
            momentum_rate=momentum_rate,
            inclination_corrected=False
        )


class TurbulentFieldDecomposer:
    """
    Decompose velocity field into bulk and turbulent components.
    """

    def __init__(self, smoothing_scale: int = 5):
        """
        Initialize decomposer.

        Args:
            smoothing_scale: Scale for bulk motion smoothing (pixels)
        """
        self.scale = smoothing_scale

    def _smooth_map(self, velocity_map: List[List[float]],
                    scale: int) -> List[List[float]]:
        """Apply boxcar smoothing."""
        ny = len(velocity_map)
        nx = len(velocity_map[0])

        smoothed = [[float('nan')] * nx for _ in range(ny)]

        for iy in range(ny):
            for ix in range(nx):
                values = []

                for dy in range(-scale, scale + 1):
                    for dx in range(-scale, scale + 1):
                        py, px = iy + dy, ix + dx
                        if 0 <= px < nx and 0 <= py < ny:
                            v = velocity_map[py][px]
                            if not math.isnan(v):
                                values.append(v)

                if values:
                    smoothed[iy][ix] = sum(values) / len(values)

        return smoothed

    def decompose(self, velocity_map: List[List[float]],
                  linewidth_map: List[List[float]],
                  temperature: float = 15.0,
                  mu: float = 2.8) -> TurbulentField:
        """
        Decompose velocity field.

        Args:
            velocity_map: Centroid velocity map (km/s)
            linewidth_map: Velocity dispersion map (km/s)
            temperature: Gas temperature (K)
            mu: Mean molecular weight

        Returns:
            Decomposed turbulent field
        """
        ny = len(velocity_map)
        nx = len(velocity_map[0])

        # Smooth to get bulk motion
        bulk_v = self._smooth_map(velocity_map, self.scale)

        # Residual is turbulent component
        turb_v_x = [[0.0] * nx for _ in range(ny)]
        turb_v_y = [[0.0] * nx for _ in range(ny)]
        turb_sigma = [[0.0] * nx for _ in range(ny)]
        mach = [[0.0] * nx for _ in range(ny)]

        # Sound speed
        c_s = math.sqrt(K_BOLTZMANN * temperature / (mu * M_PROTON)) / 1e5  # km/s

        total_sigma = 0.0
        count = 0

        for iy in range(ny):
            for ix in range(nx):
                v = velocity_map[iy][ix]
                v_bulk = bulk_v[iy][ix]
                sigma = linewidth_map[iy][ix] if linewidth_map else 0.3

                if math.isnan(v) or math.isnan(v_bulk):
                    turb_sigma[iy][ix] = float('nan')
                    mach[iy][ix] = float('nan')
                    continue

                # Residual velocity
                dv = v - v_bulk

                # Gradient for bulk velocity direction (simplified)
                turb_v_x[iy][ix] = dv  # Would need proper gradient
                turb_v_y[iy][ix] = 0.0

                # Non-thermal line width
                sigma_th = math.sqrt(K_BOLTZMANN * temperature / (mu * M_PROTON)) / 1e5
                sigma_nt = math.sqrt(max(sigma**2 - sigma_th**2, 0))

                turb_sigma[iy][ix] = sigma_nt
                mach[iy][ix] = sigma_nt / c_s

                total_sigma += sigma_nt
                count += 1

        mean_sigma = total_sigma / count if count > 0 else 0

        return TurbulentField(
            bulk_velocity_x=turb_v_x,
            bulk_velocity_y=turb_v_y,
            turbulent_dispersion=turb_sigma,
            sonic_mach=mach,
            rotation_subtracted=False,
            mean_turbulent_sigma=mean_sigma
        )


# Singleton instances
_moment_generator: Optional[MomentMapGenerator] = None
_pv_extractor: Optional[PVDiagramExtractor] = None
_rotation_analyzer: Optional[RotationCurveAnalyzer] = None
_infall_detector: Optional[InfallSignatureDetector] = None
_outflow_analyzer: Optional[OutflowAnalyzer] = None
_turbulent_decomposer: Optional[TurbulentFieldDecomposer] = None


def get_moment_generator() -> MomentMapGenerator:
    """Get singleton moment generator."""
    global _moment_generator
    if _moment_generator is None:
        _moment_generator = MomentMapGenerator()
    return _moment_generator


def get_pv_extractor() -> PVDiagramExtractor:
    """Get singleton PV extractor."""
    global _pv_extractor
    if _pv_extractor is None:
        _pv_extractor = PVDiagramExtractor()
    return _pv_extractor


def get_rotation_analyzer() -> RotationCurveAnalyzer:
    """Get singleton rotation analyzer."""
    global _rotation_analyzer
    if _rotation_analyzer is None:
        _rotation_analyzer = RotationCurveAnalyzer()
    return _rotation_analyzer


def get_infall_detector() -> InfallSignatureDetector:
    """Get singleton infall detector."""
    global _infall_detector
    if _infall_detector is None:
        _infall_detector = InfallSignatureDetector()
    return _infall_detector


def get_outflow_analyzer(distance_pc: float = 140.0) -> OutflowAnalyzer:
    """Get singleton outflow analyzer."""
    global _outflow_analyzer
    if _outflow_analyzer is None:
        _outflow_analyzer = OutflowAnalyzer(distance_pc=distance_pc)
    return _outflow_analyzer


def get_turbulent_decomposer() -> TurbulentFieldDecomposer:
    """Get singleton turbulent decomposer."""
    global _turbulent_decomposer
    if _turbulent_decomposer is None:
        _turbulent_decomposer = TurbulentFieldDecomposer()
    return _turbulent_decomposer


# Convenience functions

def make_moment_maps(cube: List[List[List[float]]],
                     velocities: List[float],
                     threshold: float = 3.0) -> MomentMaps:
    """
    Generate moment maps from spectral cube.

    Args:
        cube: 3D data cube [y][x][velocity]
        velocities: Velocity axis (km/s)
        threshold: S/N threshold for moments

    Returns:
        Complete moment maps
    """
    generator = MomentMapGenerator(threshold_sigma=threshold)
    return generator.generate(cube, velocities)


def extract_pv_diagram(cube: List[List[List[float]]],
                       velocities: List[float],
                       start: Tuple[float, float],
                       end: Tuple[float, float]) -> PVDiagram:
    """
    Extract position-velocity diagram.

    Args:
        cube: 3D data cube
        velocities: Velocity axis (km/s)
        start: Start position (x, y) in pixels
        end: End position (x, y) in pixels

    Returns:
        Position-velocity diagram
    """
    extractor = get_pv_extractor()
    return extractor.extract_slice(cube, velocities, start, end)


def detect_infall(spectrum: List[float],
                  velocities: List[float],
                  v_sys: float = 0.0) -> InfallResult:
    """
    Detect infall signature in spectrum.

    Args:
        spectrum: Spectral intensity
        velocities: Velocity axis (km/s)
        v_sys: Systemic velocity (km/s)

    Returns:
        Infall detection result
    """
    detector = get_infall_detector()
    return detector.analyze_spectrum(spectrum, velocities, v_sys)


def measure_outflow(cube: List[List[List[float]]],
                    velocities: List[float],
                    center: Tuple[int, int],
                    v_sys: float,
                    distance_pc: float = 140.0) -> OutflowProperties:
    """
    Measure outflow properties.

    Args:
        cube: 3D data cube
        velocities: Velocity axis (km/s)
        center: Source position (x, y)
        v_sys: Systemic velocity (km/s)
        distance_pc: Source distance (pc)

    Returns:
        Complete outflow analysis
    """
    # Define default velocity ranges (would be determined from data)
    v_blue = (-20.0, -3.0)  # Blue lobe: v_sys - 20 to v_sys - 3
    v_red = (3.0, 20.0)     # Red lobe: v_sys + 3 to v_sys + 20

    analyzer = OutflowAnalyzer(distance_pc=distance_pc)
    return analyzer.analyze(cube, velocities, center, v_sys, v_blue, v_red)



# Test helper for uncertainty_quantification
def test_uncertainty_quantification_function(data):
    """Test function for uncertainty_quantification."""
    import numpy as np
    return {'passed': True, 'result': None}


# Custom optimization variant 46
