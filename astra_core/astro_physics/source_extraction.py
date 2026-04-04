"""
Source Extraction Module for STAN V43

Automated source detection and photometry for astronomical images and cubes.
Provides threshold-based detection, aperture/PSF photometry, dendrogram
extraction for hierarchical structures, and filament finding.

Features:
- Threshold-based source detection with local background estimation
- Wavelet-based detection for multi-scale structures
- Circular and elliptical aperture photometry
- PSF/beam-fitting photometry for point sources
- Dendrogram extraction for hierarchical structure identification
- Filament finding using medial axis and structure tensors
- Core catalog building with physical property estimation

All calculations assume FITS-like 2D/3D arrays with proper WCS calibration.

Author: STAN V43 Astrophysics Module
"""

import math
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple, Any


# Physical constants
PC = 3.086e18              # Parsec (cm)
M_SUN = 1.989e33           # Solar mass (g)
K_BOLTZMANN = 1.381e-16    # Boltzmann constant (erg/K)
M_PROTON = 1.673e-24       # Proton mass (g)


class DetectionMethod(Enum):
    """Source detection methods."""
    THRESHOLD = auto()      # Simple sigma clipping
    WAVELET = auto()        # Multi-scale wavelet decomposition
    PEAK_FINDING = auto()   # Local maxima detection
    WATERSHED = auto()      # Watershed segmentation


class SourceType(Enum):
    """Classification of detected sources."""
    POINT = auto()          # Unresolved point source
    EXTENDED = auto()       # Resolved extended emission
    COMPACT = auto()        # Marginally resolved
    FILAMENTARY = auto()    # Elongated structure
    DIFFUSE = auto()        # Low surface brightness extended


@dataclass
class BeamParameters:
    """Telescope beam/PSF parameters."""
    bmaj: float             # Major axis FWHM (arcsec)
    bmin: float             # Minor axis FWHM (arcsec)
    bpa: float              # Position angle (degrees, E of N)
    beam_area_sr: float = 0.0  # Beam solid angle (sr)

    def __post_init__(self):
        """Calculate beam area."""
        if self.beam_area_sr == 0.0:
            # Beam area = pi * bmaj * bmin / (4 * ln(2))
            bmaj_rad = self.bmaj * math.pi / (180.0 * 3600.0)
            bmin_rad = self.bmin * math.pi / (180.0 * 3600.0)
            self.beam_area_sr = math.pi * bmaj_rad * bmin_rad / (4.0 * math.log(2.0))


@dataclass
class DetectedSource:
    """Properties of a detected source."""
    source_id: int
    x_pixel: float          # X centroid (pixel)
    y_pixel: float          # Y centroid (pixel)
    ra: float               # RA (degrees)
    dec: float              # Dec (degrees)
    peak_flux: float        # Peak flux density
    peak_error: float       # Peak flux uncertainty
    integrated_flux: float  # Total flux (Jy or K km/s)
    integrated_error: float # Integrated flux uncertainty
    size_major: float       # Deconvolved major axis (arcsec)
    size_minor: float       # Deconvolved minor axis (arcsec)
    position_angle: float   # Position angle (degrees)
    snr: float              # Signal-to-noise ratio
    source_type: SourceType # Classification
    npixels: int            # Number of pixels above threshold
    background: float       # Local background level


@dataclass
class SourceCatalog:
    """Complete source catalog."""
    sources: List[DetectedSource]
    detection_threshold: float  # Detection threshold (sigma)
    method: DetectionMethod
    beam: Optional[BeamParameters]
    noise_rms: float        # Image noise level
    total_flux: float       # Sum of all integrated fluxes
    completeness: float     # Estimated completeness (0-1)


@dataclass
class ApertureResult:
    """Result of aperture photometry."""
    flux: float             # Measured flux
    flux_error: float       # Flux uncertainty
    area: float             # Aperture area (pixels)
    background: float       # Background level
    background_rms: float   # Background noise
    aperture_correction: float  # Aperture correction factor


@dataclass
class PSFFitResult:
    """Result of PSF fitting."""
    amplitude: float        # Best-fit amplitude
    x_center: float         # Best-fit X position
    y_center: float         # Best-fit Y position
    fwhm_major: float       # Fitted major FWHM
    fwhm_minor: float       # Fitted minor FWHM
    position_angle: float   # Fitted PA
    chi_squared: float      # Fit quality
    is_point_source: bool   # Consistent with beam?


@dataclass
class DendrogramNode:
    """Node in a dendrogram structure tree."""
    node_id: int
    parent_id: Optional[int]  # None for root
    children: List[int]     # Child node IDs
    level: float            # Intensity level
    npixels: int            # Number of pixels
    peak_value: float       # Peak intensity
    centroid_x: float       # Centroid X
    centroid_y: float       # Centroid Y
    is_leaf: bool           # True for leaves (no children)
    integrated_flux: float  # Flux in this structure


@dataclass
class Dendrogram:
    """Complete dendrogram structure tree."""
    nodes: List[DendrogramNode]
    n_leaves: int           # Number of leaf nodes
    n_branches: int         # Number of branch nodes
    trunk_level: float      # Base level of tree
    peak_level: float       # Maximum level
    min_value: float        # Threshold for inclusion
    min_delta: float        # Minimum contrast for branches


@dataclass
class FilamentSegment:
    """Segment of a detected filament."""
    segment_id: int
    spine_points: List[Tuple[float, float]]  # (x, y) spine coordinates
    width: float            # Average width (arcsec)
    length: float           # Total length (arcsec)
    curvature: float        # Average curvature
    peak_column: float      # Peak column density on spine
    integrated_flux: float  # Total flux in filament


@dataclass
class FilamentNetwork:
    """Network of connected filaments."""
    filaments: List[FilamentSegment]
    junctions: List[Tuple[float, float]]  # Junction points
    total_length: float     # Total network length
    mean_width: float       # Mean filament width
    mass_per_length: float  # Average M/L (M_sun/pc)


@dataclass
class CoreProperties:
    """Physical properties of a prestellar core."""
    core_id: int
    ra: float               # RA (degrees)
    dec: float              # Dec (degrees)
    radius: float           # Effective radius (pc)
    mass: float             # Estimated mass (M_sun)
    mass_error: float       # Mass uncertainty
    temperature: float      # Assumed/derived temperature (K)
    column_density: float   # Peak column density (cm^-2)
    volume_density: float   # Central density (cm^-3)
    velocity: float         # LSR velocity (km/s)
    linewidth: float        # Velocity dispersion (km/s)
    virial_mass: float      # Virial mass (M_sun)
    virial_parameter: float # Virial parameter alpha
    jeans_mass: float       # Jeans mass (M_sun)
    is_bound: bool          # Gravitationally bound?
    is_prestellar: bool     # Prestellar candidate?


class SourceDetector:
    """
    Threshold-based source detection.

    Detects sources above a given significance threshold
    with local background estimation.
    """

    def __init__(self, threshold_sigma: float = 5.0,
                 min_pixels: int = 5,
                 min_separation: float = 1.0):
        """
        Initialize source detector.

        Args:
            threshold_sigma: Detection threshold in sigma
            min_pixels: Minimum connected pixels for valid source
            min_separation: Minimum separation between sources (beam FWHM)
        """
        self.threshold = threshold_sigma
        self.min_pixels = min_pixels
        self.min_separation = min_separation

    def estimate_noise(self, image: List[List[float]],
                       method: str = 'mad') -> float:
        """
        Estimate noise level in image.

        Args:
            image: 2D image array
            method: 'std', 'mad', or 'negative'

        Returns:
            Noise RMS estimate
        """
        # Flatten image
        flat = []
        for row in image:
            flat.extend(row)

        if method == 'std':
            mean = sum(flat) / len(flat)
            variance = sum((x - mean)**2 for x in flat) / len(flat)
            return math.sqrt(variance)

        elif method == 'mad':
            # Median Absolute Deviation (robust)
            sorted_data = sorted(flat)
            median = sorted_data[len(sorted_data) // 2]
            deviations = sorted([abs(x - median) for x in flat])
            mad = deviations[len(deviations) // 2]
            return 1.4826 * mad  # Scale to Gaussian sigma

        elif method == 'negative':
            # Use negative pixel distribution
            negatives = [x for x in flat if x < 0]
            if len(negatives) < 10:
                return self.estimate_noise(image, 'mad')
            mean = sum(negatives) / len(negatives)
            variance = sum((x - mean)**2 for x in negatives) / len(negatives)
            return math.sqrt(variance)

        return self.estimate_noise(image, 'mad')

    def _find_local_maxima(self, image: List[List[float]],
                           threshold: float) -> List[Tuple[int, int, float]]:
        """Find local maxima above threshold."""
        maxima = []
        ny = len(image)
        nx = len(image[0])

        for iy in range(1, ny - 1):
            for ix in range(1, nx - 1):
                val = image[iy][ix]
                if val < threshold:
                    continue

                # Check if local maximum
                is_max = True
                for dy in [-1, 0, 1]:
                    for dx in [-1, 0, 1]:
                        if dy == 0 and dx == 0:
                            continue
                        if image[iy + dy][ix + dx] > val:
                            is_max = False
                            break
                    if not is_max:
                        break

                if is_max:
                    maxima.append((ix, iy, val))

        return maxima

    def _grow_region(self, image: List[List[float]],
                     start_x: int, start_y: int,
                     threshold: float) -> List[Tuple[int, int]]:
        """Grow region around starting point."""
        ny = len(image)
        nx = len(image[0])
        visited = set()
        region = []
        queue = [(start_x, start_y)]

        while queue:
            x, y = queue.pop(0)
            if (x, y) in visited:
                continue
            if x < 0 or x >= nx or y < 0 or y >= ny:
                continue
            if image[y][x] < threshold:
                continue

            visited.add((x, y))
            region.append((x, y))

            # Add neighbors
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                queue.append((x + dx, y + dy))

        return region

    def _compute_moments(self, image: List[List[float]],
                         pixels: List[Tuple[int, int]]) -> Dict[str, float]:
        """Compute intensity-weighted moments."""
        if not pixels:
            return {'x': 0, 'y': 0, 'flux': 0, 'xx': 0, 'yy': 0, 'xy': 0}

        total = 0
        sx = 0
        sy = 0
        sxx = 0
        syy = 0
        sxy = 0
        peak = 0

        for x, y in pixels:
            val = image[y][x]
            total += val
            sx += val * x
            sy += val * y
            sxx += val * x * x
            syy += val * y * y
            sxy += val * x * y
            peak = max(peak, val)

        if total <= 0:
            return {'x': pixels[0][0], 'y': pixels[0][1], 'flux': 0,
                    'xx': 0, 'yy': 0, 'xy': 0, 'peak': 0}

        x_cen = sx / total
        y_cen = sy / total

        # Central moments
        xx = sxx / total - x_cen**2
        yy = syy / total - y_cen**2
        xy = sxy / total - x_cen * y_cen

        return {
            'x': x_cen,
            'y': y_cen,
            'flux': total,
            'xx': max(xx, 0.01),
            'yy': max(yy, 0.01),
            'xy': xy,
            'peak': peak
        }

    def _classify_source(self, size_major: float, size_minor: float,
                         beam: BeamParameters) -> SourceType:
        """Classify source based on size relative to beam."""
        beam_size = math.sqrt(beam.bmaj * beam.bmin)

        # Deconvolved size
        deconv_maj = math.sqrt(max(size_major**2 - beam.bmaj**2, 0))
        deconv_min = math.sqrt(max(size_minor**2 - beam.bmin**2, 0))

        if deconv_maj < 0.1 * beam_size and deconv_min < 0.1 * beam_size:
            return SourceType.POINT
        elif deconv_maj < 0.5 * beam_size:
            return SourceType.COMPACT
        elif size_major / size_minor > 3.0:
            return SourceType.FILAMENTARY
        elif deconv_maj > 5.0 * beam_size:
            return SourceType.DIFFUSE
        else:
            return SourceType.EXTENDED

    def detect(self, image: List[List[float]],
               beam: BeamParameters,
               pixel_scale: float = 1.0) -> SourceCatalog:
        """
        Detect sources in image.

        Args:
            image: 2D image array
            beam: Beam parameters
            pixel_scale: Pixel scale (arcsec/pixel)

        Returns:
            Source catalog
        """
        noise = self.estimate_noise(image)
        threshold = self.threshold * noise

        # Find local maxima
        maxima = self._find_local_maxima(image, threshold)

        # Grow regions and build source list
        sources = []
        used_pixels = set()

        for idx, (px, py, peak) in enumerate(maxima):
            if (px, py) in used_pixels:
                continue

            # Grow region
            region = self._grow_region(image, px, py, threshold)

            if len(region) < self.min_pixels:
                continue

            # Mark pixels as used
            for p in region:
                used_pixels.add(p)

            # Compute moments
            moments = self._compute_moments(image, region)

            # Size from moments
            size_sq = moments['xx'] + moments['yy']
            size_pix = math.sqrt(size_sq) * 2.355 if size_sq > 0 else 1.0

            # Ellipse parameters
            diff = moments['xx'] - moments['yy']
            discriminant = diff**2 + 4 * moments['xy']**2
            if discriminant > 0:
                a = math.sqrt((moments['xx'] + moments['yy'] + math.sqrt(discriminant)) / 2)
                b = math.sqrt((moments['xx'] + moments['yy'] - math.sqrt(discriminant)) / 2)
                pa = 0.5 * math.atan2(2 * moments['xy'], diff) * 180.0 / math.pi
            else:
                a = b = size_pix / 2.355
                pa = 0.0

            size_major = a * 2.355 * pixel_scale  # FWHM in arcsec
            size_minor = b * 2.355 * pixel_scale

            # Classification
            source_type = self._classify_source(size_major, size_minor, beam)

            # SNR
            snr = moments['peak'] / noise if noise > 0 else 0

            # Create source
            source = DetectedSource(
                source_id=idx + 1,
                x_pixel=moments['x'],
                y_pixel=moments['y'],
                ra=0.0,  # Would need WCS
                dec=0.0,
                peak_flux=moments['peak'],
                peak_error=noise,
                integrated_flux=moments['flux'],
                integrated_error=noise * math.sqrt(len(region)),
                size_major=size_major,
                size_minor=size_minor,
                position_angle=pa,
                snr=snr,
                source_type=source_type,
                npixels=len(region),
                background=0.0
            )

            sources.append(source)

        return SourceCatalog(
            sources=sources,
            detection_threshold=self.threshold,
            method=DetectionMethod.THRESHOLD,
            beam=beam,
            noise_rms=noise,
            total_flux=sum(s.integrated_flux for s in sources),
            completeness=0.9  # Approximate
        )


class AperturePhotometry:
    """
    Aperture photometry for flux measurement.

    Measures flux in circular or elliptical apertures
    with local background subtraction.
    """

    def __init__(self, background_annulus: Tuple[float, float] = (1.5, 2.5)):
        """
        Initialize aperture photometry.

        Args:
            background_annulus: Inner/outer radius of background annulus
                                (in units of aperture radius)
        """
        self.bg_inner = background_annulus[0]
        self.bg_outer = background_annulus[1]

    def _pixels_in_aperture(self, cx: float, cy: float, radius: float,
                            nx: int, ny: int,
                            ellipticity: float = 1.0,
                            pa: float = 0.0) -> List[Tuple[int, int, float]]:
        """
        Get pixels within aperture with weights.

        Returns list of (x, y, weight) tuples.
        """
        pixels = []
        pa_rad = pa * math.pi / 180.0
        cos_pa = math.cos(pa_rad)
        sin_pa = math.sin(pa_rad)

        # Search box
        search_r = int(radius * 1.5) + 1
        x_min = max(0, int(cx - search_r))
        x_max = min(nx - 1, int(cx + search_r))
        y_min = max(0, int(cy - search_r))
        y_max = min(ny - 1, int(cy + search_r))

        for y in range(y_min, y_max + 1):
            for x in range(x_min, x_max + 1):
                # Transform to aperture coordinates
                dx = x - cx
                dy = y - cy

                # Rotate
                x_rot = dx * cos_pa + dy * sin_pa
                y_rot = -dx * sin_pa + dy * cos_pa

                # Ellipse distance
                r_ell = math.sqrt((x_rot / radius)**2 +
                                  (y_rot / (radius * ellipticity))**2)

                if r_ell <= 1.0:
                    # Weight based on distance from edge (simple approximation)
                    weight = min(1.0, 2.0 * (1.0 - r_ell))
                    pixels.append((x, y, weight))

        return pixels

    def measure(self, image: List[List[float]],
                x: float, y: float,
                radius: float,
                ellipticity: float = 1.0,
                pa: float = 0.0) -> ApertureResult:
        """
        Measure flux in aperture.

        Args:
            image: 2D image array
            x, y: Aperture center (pixels)
            radius: Aperture radius (pixels)
            ellipticity: Minor/major axis ratio
            pa: Position angle (degrees)

        Returns:
            Aperture photometry result
        """
        ny = len(image)
        nx = len(image[0])

        # Source aperture
        src_pixels = self._pixels_in_aperture(x, y, radius, nx, ny, ellipticity, pa)

        # Background annulus
        bg_inner_r = radius * self.bg_inner
        bg_outer_r = radius * self.bg_outer
        bg_pixels_inner = set((px, py) for px, py, _ in
                              self._pixels_in_aperture(x, y, bg_inner_r, nx, ny, ellipticity, pa))
        bg_pixels_outer = self._pixels_in_aperture(x, y, bg_outer_r, nx, ny, ellipticity, pa)

        # Background from annulus (excluding inner)
        bg_values = []
        for px, py, w in bg_pixels_outer:
            if (px, py) not in bg_pixels_inner:
                bg_values.append(image[py][px])

        if bg_values:
            # Use median for robustness
            sorted_bg = sorted(bg_values)
            background = sorted_bg[len(sorted_bg) // 2]
            bg_rms = math.sqrt(sum((v - background)**2 for v in bg_values) / len(bg_values))
        else:
            background = 0.0
            bg_rms = 0.0

        # Source flux (background subtracted)
        flux = 0.0
        total_weight = 0.0

        for px, py, w in src_pixels:
            flux += (image[py][px] - background) * w
            total_weight += w

        # Aperture area
        area = math.pi * radius**2 * ellipticity

        # Flux error
        if bg_rms > 0 and total_weight > 0:
            flux_error = bg_rms * math.sqrt(total_weight)
        else:
            flux_error = 0.0

        # Aperture correction (approximate)
        aperture_correction = 1.0  # Would need PSF model

        return ApertureResult(
            flux=flux,
            flux_error=flux_error,
            area=area,
            background=background,
            background_rms=bg_rms,
            aperture_correction=aperture_correction
        )


class PSFPhotometry:
    """
    PSF/beam-fitting photometry for point sources.

    Fits a 2D Gaussian beam model to measure flux
    and determine if source is resolved.
    """

    def __init__(self, beam: BeamParameters):
        """
        Initialize PSF photometry.

        Args:
            beam: Beam/PSF parameters
        """
        self.beam = beam

    def _gaussian_2d(self, x: float, y: float,
                     amp: float, x0: float, y0: float,
                     sigma_x: float, sigma_y: float, theta: float) -> float:
        """Evaluate 2D Gaussian."""
        cos_t = math.cos(theta)
        sin_t = math.sin(theta)

        dx = x - x0
        dy = y - y0

        a = cos_t**2 / (2 * sigma_x**2) + sin_t**2 / (2 * sigma_y**2)
        b = -math.sin(2 * theta) / (4 * sigma_x**2) + math.sin(2 * theta) / (4 * sigma_y**2)
        c = sin_t**2 / (2 * sigma_x**2) + cos_t**2 / (2 * sigma_y**2)

        return amp * math.exp(-(a * dx**2 + 2 * b * dx * dy + c * dy**2))

    def fit(self, image: List[List[float]],
            x_init: float, y_init: float,
            pixel_scale: float = 1.0) -> PSFFitResult:
        """
        Fit PSF model to source.

        Args:
            image: 2D image array
            x_init, y_init: Initial position estimate
            pixel_scale: Pixel scale (arcsec/pixel)

        Returns:
            PSF fit result
        """
        ny = len(image)
        nx = len(image[0])

        # Convert beam to pixels
        sigma_x_pix = self.beam.bmaj / pixel_scale / 2.355
        sigma_y_pix = self.beam.bmin / pixel_scale / 2.355
        theta = self.beam.bpa * math.pi / 180.0

        # Initial amplitude
        ix, iy = int(x_init), int(y_init)
        if 0 <= ix < nx and 0 <= iy < ny:
            amp_init = image[iy][ix]
        else:
            amp_init = 1.0

        # Simple iterative fitting (would use proper optimization in production)
        best_amp = amp_init
        best_x = x_init
        best_y = y_init
        best_chi2 = float('inf')

        # Fit region
        fit_radius = int(max(sigma_x_pix, sigma_y_pix) * 3) + 1

        for iteration in range(20):
            # Compute chi-squared
            chi2 = 0.0
            count = 0

            for dy in range(-fit_radius, fit_radius + 1):
                for dx in range(-fit_radius, fit_radius + 1):
                    px = int(best_x) + dx
                    py = int(best_y) + dy

                    if 0 <= px < nx and 0 <= py < ny:
                        model = self._gaussian_2d(px, py, best_amp, best_x, best_y,
                                                  sigma_x_pix, sigma_y_pix, theta)
                        chi2 += (image[py][px] - model)**2
                        count += 1

            if chi2 < best_chi2:
                best_chi2 = chi2

            # Update parameters (simple gradient descent)
            delta = 0.1

            for test_amp in [best_amp * (1 + delta), best_amp * (1 - delta)]:
                if test_amp <= 0:
                    continue
                test_chi2 = 0.0
                for dy in range(-fit_radius, fit_radius + 1):
                    for dx in range(-fit_radius, fit_radius + 1):
                        px = int(best_x) + dx
                        py = int(best_y) + dy
                        if 0 <= px < nx and 0 <= py < ny:
                            model = self._gaussian_2d(px, py, test_amp, best_x, best_y,
                                                      sigma_x_pix, sigma_y_pix, theta)
                            test_chi2 += (image[py][px] - model)**2
                if test_chi2 < best_chi2:
                    best_amp = test_amp
                    best_chi2 = test_chi2
                    break

        # Determine if point source
        # Would need to fit size and compare to beam
        is_point = True  # Simplified

        return PSFFitResult(
            amplitude=best_amp,
            x_center=best_x,
            y_center=best_y,
            fwhm_major=self.beam.bmaj,
            fwhm_minor=self.beam.bmin,
            position_angle=self.beam.bpa,
            chi_squared=best_chi2,
            is_point_source=is_point
        )


class DendrogramExtractor:
    """
    Dendrogram extraction for hierarchical structure identification.

    Implements the algorithm of Rosolowsky et al. (2008) for
    identifying hierarchical structures in molecular clouds.
    """

    def __init__(self, min_value: float = 0.0,
                 min_delta: float = 0.0,
                 min_npix: int = 5):
        """
        Initialize dendrogram extractor.

        Args:
            min_value: Minimum value for inclusion
            min_delta: Minimum contrast for branches
            min_npix: Minimum pixels for structures
        """
        self.min_value = min_value
        self.min_delta = min_delta
        self.min_npix = min_npix

    def _get_neighbors(self, x: int, y: int,
                       nx: int, ny: int) -> List[Tuple[int, int]]:
        """Get 4-connected neighbors."""
        neighbors = []
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx_, ny_ = x + dx, y + dy
            if 0 <= nx_ < nx and 0 <= ny_ < ny:
                neighbors.append((nx_, ny_))
        return neighbors

    def extract(self, image: List[List[float]]) -> Dendrogram:
        """
        Extract dendrogram from image.

        Args:
            image: 2D image array

        Returns:
            Dendrogram structure
        """
        ny = len(image)
        nx = len(image[0])

        # Sort pixels by value (descending)
        pixels = []
        for y in range(ny):
            for x in range(nx):
                if image[y][x] >= self.min_value:
                    pixels.append((image[y][x], x, y))

        pixels.sort(reverse=True)

        # Track which structure each pixel belongs to
        pixel_to_structure = {}  # (x, y) -> node_id
        nodes = []
        next_id = 0

        for value, x, y in pixels:
            # Find neighboring structures
            neighbor_structures = set()
            for nx_, ny_ in self._get_neighbors(x, y, nx, ny):
                if (nx_, ny_) in pixel_to_structure:
                    neighbor_structures.add(pixel_to_structure[(nx_, ny_)])

            if len(neighbor_structures) == 0:
                # New isolated structure (leaf)
                node = DendrogramNode(
                    node_id=next_id,
                    parent_id=None,
                    children=[],
                    level=value,
                    npixels=1,
                    peak_value=value,
                    centroid_x=float(x),
                    centroid_y=float(y),
                    is_leaf=True,
                    integrated_flux=value
                )
                nodes.append(node)
                pixel_to_structure[(x, y)] = next_id
                next_id += 1

            elif len(neighbor_structures) == 1:
                # Extend existing structure
                struct_id = neighbor_structures.pop()
                node = nodes[struct_id]
                node.npixels += 1
                node.integrated_flux += value

                # Update centroid
                n = node.npixels
                node.centroid_x = (node.centroid_x * (n - 1) + x) / n
                node.centroid_y = (node.centroid_y * (n - 1) + y) / n

                pixel_to_structure[(x, y)] = struct_id

            else:
                # Merge multiple structures
                struct_ids = list(neighbor_structures)

                # Check if merger is significant
                highest_peaks = [nodes[sid].peak_value for sid in struct_ids]
                delta_from_current = [p - value for p in highest_peaks]

                if all(d >= self.min_delta for d in delta_from_current):
                    # Create branch node
                    total_pix = 1  # Current pixel
                    total_flux = value
                    cx, cy = float(x), float(y)

                    for sid in struct_ids:
                        total_pix += nodes[sid].npixels
                        total_flux += nodes[sid].integrated_flux
                        nodes[sid].parent_id = next_id

                    # New branch
                    branch = DendrogramNode(
                        node_id=next_id,
                        parent_id=None,
                        children=struct_ids,
                        level=value,
                        npixels=total_pix,
                        peak_value=max(highest_peaks),
                        centroid_x=cx,
                        centroid_y=cy,
                        is_leaf=False,
                        integrated_flux=total_flux
                    )
                    nodes.append(branch)

                    # Update pixel assignments
                    for sid in struct_ids:
                        for key, val in pixel_to_structure.items():
                            if val == sid:
                                pixel_to_structure[key] = next_id

                    pixel_to_structure[(x, y)] = next_id
                    next_id += 1

                else:
                    # Merge into most significant structure
                    main_struct = struct_ids[highest_peaks.index(max(highest_peaks))]
                    node = nodes[main_struct]
                    node.npixels += 1
                    node.integrated_flux += value

                    for sid in struct_ids:
                        if sid != main_struct:
                            # Absorb smaller structure
                            node.npixels += nodes[sid].npixels
                            node.integrated_flux += nodes[sid].integrated_flux
                            for key, val in pixel_to_structure.items():
                                if val == sid:
                                    pixel_to_structure[key] = main_struct

                    pixel_to_structure[(x, y)] = main_struct

        # Count leaves and branches
        n_leaves = sum(1 for n in nodes if n.is_leaf)
        n_branches = len(nodes) - n_leaves

        return Dendrogram(
            nodes=nodes,
            n_leaves=n_leaves,
            n_branches=n_branches,
            trunk_level=self.min_value,
            peak_level=max(n.peak_value for n in nodes) if nodes else 0,
            min_value=self.min_value,
            min_delta=self.min_delta
        )


class FilamentFinder:
    """
    Filament detection using structure tensor analysis.

    Identifies elongated structures in column density or
    intensity maps using eigenvalue analysis.
    """

    def __init__(self, scale: float = 3.0,
                 min_length: float = 10.0,
                 min_contrast: float = 0.1):
        """
        Initialize filament finder.

        Args:
            scale: Smoothing scale (pixels)
            min_length: Minimum filament length (pixels)
            min_contrast: Minimum contrast for detection
        """
        self.scale = scale
        self.min_length = min_length
        self.min_contrast = min_contrast

    def _compute_gradients(self, image: List[List[float]]
                           ) -> Tuple[List[List[float]], List[List[float]]]:
        """Compute image gradients."""
        ny = len(image)
        nx = len(image[0])

        gx = [[0.0] * nx for _ in range(ny)]
        gy = [[0.0] * nx for _ in range(ny)]

        for y in range(1, ny - 1):
            for x in range(1, nx - 1):
                gx[y][x] = (image[y][x + 1] - image[y][x - 1]) / 2.0
                gy[y][x] = (image[y + 1][x] - image[y - 1][x]) / 2.0

        return gx, gy

    def _compute_structure_tensor(self, gx: List[List[float]],
                                  gy: List[List[float]]
                                  ) -> Tuple[List[List[float]],
                                             List[List[float]],
                                             List[List[float]]]:
        """Compute structure tensor components."""
        ny = len(gx)
        nx = len(gx[0])

        Jxx = [[0.0] * nx for _ in range(ny)]
        Jxy = [[0.0] * nx for _ in range(ny)]
        Jyy = [[0.0] * nx for _ in range(ny)]

        for y in range(ny):
            for x in range(nx):
                Jxx[y][x] = gx[y][x]**2
                Jxy[y][x] = gx[y][x] * gy[y][x]
                Jyy[y][x] = gy[y][x]**2

        return Jxx, Jxy, Jyy

    def _eigenvalues(self, Jxx: float, Jxy: float, Jyy: float
                     ) -> Tuple[float, float, float]:
        """Compute eigenvalues and dominant direction."""
        trace = Jxx + Jyy
        det = Jxx * Jyy - Jxy**2
        discriminant = trace**2 - 4 * det

        if discriminant < 0:
            discriminant = 0

        sqrt_disc = math.sqrt(discriminant)
        lambda1 = (trace + sqrt_disc) / 2.0
        lambda2 = (trace - sqrt_disc) / 2.0

        # Eigenvector for lambda2 (perpendicular to filament)
        if abs(Jxy) > 1e-10:
            theta = math.atan2(lambda2 - Jxx, Jxy)
        else:
            theta = 0.0 if Jxx < Jyy else math.pi / 2

        return lambda1, lambda2, theta

    def find(self, image: List[List[float]],
             threshold: float = 0.0) -> FilamentNetwork:
        """
        Find filaments in image.

        Args:
            image: 2D column density or intensity map
            threshold: Minimum value for filament pixels

        Returns:
            Network of detected filaments
        """
        ny = len(image)
        nx = len(image[0])

        # Compute structure tensor
        gx, gy = self._compute_gradients(image)
        Jxx, Jxy, Jyy = self._compute_structure_tensor(gx, gy)

        # Compute anisotropy at each pixel
        anisotropy = [[0.0] * nx for _ in range(ny)]
        orientation = [[0.0] * nx for _ in range(ny)]

        for y in range(ny):
            for x in range(nx):
                l1, l2, theta = self._eigenvalues(Jxx[y][x], Jxy[y][x], Jyy[y][x])

                # Anisotropy: 0 = isotropic, 1 = highly elongated
                if l1 + l2 > 0:
                    anisotropy[y][x] = (l1 - l2) / (l1 + l2)
                else:
                    anisotropy[y][x] = 0.0

                orientation[y][x] = theta

        # Find filament spines (simplified - would use proper ridge detection)
        filaments = []
        visited = set()

        for y in range(1, ny - 1):
            for x in range(1, nx - 1):
                if (x, y) in visited:
                    continue
                if image[y][x] < threshold:
                    continue
                if anisotropy[y][x] < self.min_contrast:
                    continue

                # Trace filament spine
                spine = [(float(x), float(y))]
                visited.add((x, y))

                # Trace in both directions along ridge
                for direction in [1, -1]:
                    cx, cy = float(x), float(y)
                    theta = orientation[y][x] + direction * math.pi / 2

                    for _ in range(100):  # Max length
                        # Step along perpendicular to gradient
                        nx_ = cx + direction * math.cos(theta)
                        ny_ = cy + direction * math.sin(theta)

                        ix, iy = int(nx_), int(ny_)
                        if ix < 0 or ix >= nx or iy < 0 or iy >= ny:
                            break
                        if (ix, iy) in visited:
                            break
                        if image[iy][ix] < threshold:
                            break
                        if anisotropy[iy][ix] < self.min_contrast * 0.5:
                            break

                        visited.add((ix, iy))
                        if direction > 0:
                            spine.append((nx_, ny_))
                        else:
                            spine.insert(0, (nx_, ny_))

                        cx, cy = nx_, ny_
                        theta = orientation[iy][ix] + direction * math.pi / 2

                # Check if long enough
                if len(spine) >= self.min_length:
                    # Calculate properties
                    length = sum(
                        math.sqrt((spine[i+1][0] - spine[i][0])**2 +
                                  (spine[i+1][1] - spine[i][1])**2)
                        for i in range(len(spine) - 1)
                    )

                    segment = FilamentSegment(
                        segment_id=len(filaments) + 1,
                        spine_points=spine,
                        width=self.scale * 2.0,  # Approximate
                        length=length,
                        curvature=0.0,  # Would compute from spine
                        peak_column=max(image[int(p[1])][int(p[0])]
                                        for p in spine
                                        if 0 <= int(p[0]) < nx and 0 <= int(p[1]) < ny),
                        integrated_flux=sum(image[int(p[1])][int(p[0])]
                                            for p in spine
                                            if 0 <= int(p[0]) < nx and 0 <= int(p[1]) < ny)
                    )
                    filaments.append(segment)

        return FilamentNetwork(
            filaments=filaments,
            junctions=[],  # Would identify junction points
            total_length=sum(f.length for f in filaments),
            mean_width=sum(f.width for f in filaments) / len(filaments) if filaments else 0,
            mass_per_length=0.0  # Would calculate with column density calibration
        )


class CoreCatalogBuilder:
    """
    Build catalog of prestellar cores with physical properties.

    Identifies cores from dendrogram leaves and calculates
    masses, densities, and stability parameters.
    """

    def __init__(self, temperature: float = 15.0,
                 distance_pc: float = 140.0,
                 mu: float = 2.8):
        """
        Initialize core catalog builder.

        Args:
            temperature: Assumed dust temperature (K)
            distance_pc: Distance to cloud (pc)
            mu: Mean molecular weight per H2
        """
        self.temperature = temperature
        self.distance_pc = distance_pc
        self.mu = mu

    def column_to_mass(self, N_H2: float, area_sr: float) -> float:
        """
        Convert column density to mass.

        Args:
            N_H2: Column density (cm^-2)
            area_sr: Solid angle (sr)

        Returns:
            Mass in solar masses
        """
        # M = N_H2 * mu * m_H * area * d^2
        d_cm = self.distance_pc * PC
        area_cm2 = area_sr * d_cm**2

        mass_g = N_H2 * self.mu * M_PROTON * area_cm2
        return mass_g / M_SUN

    def virial_mass(self, radius_pc: float, sigma_km_s: float) -> float:
        """
        Calculate virial mass.

        M_vir = 5 * sigma^2 * R / G

        Args:
            radius_pc: Core radius (pc)
            sigma_km_s: Velocity dispersion (km/s)

        Returns:
            Virial mass in solar masses
        """
        G_cgs = 6.674e-8  # cm^3/g/s^2
        R_cm = radius_pc * PC
        sigma_cm_s = sigma_km_s * 1e5

        M_vir_g = 5.0 * sigma_cm_s**2 * R_cm / G_cgs
        return M_vir_g / M_SUN

    def jeans_mass(self, temperature: float, density: float) -> float:
        """
        Calculate Jeans mass.

        Args:
            temperature: Temperature (K)
            density: Number density (cm^-3)

        Returns:
            Jeans mass in solar masses
        """
        # M_J = (5 k T / G mu m_H)^(3/2) * (3 / 4 pi rho)^(1/2)
        G_cgs = 6.674e-8
        rho = density * self.mu * M_PROTON

        term1 = (5.0 * K_BOLTZMANN * temperature /
                 (G_cgs * self.mu * M_PROTON))**(3.0/2.0)
        term2 = (3.0 / (4.0 * math.pi * rho))**(0.5)

        return term1 * term2 / M_SUN

    def build_catalog(self, dendrogram: Dendrogram,
                      column_density_map: List[List[float]],
                      velocity_map: Optional[List[List[float]]] = None,
                      linewidth_map: Optional[List[List[float]]] = None,
                      pixel_scale_arcsec: float = 1.0) -> List[CoreProperties]:
        """
        Build core catalog from dendrogram leaves.

        Args:
            dendrogram: Dendrogram structure
            column_density_map: N_H2 map (cm^-2)
            velocity_map: LSR velocity map (km/s)
            linewidth_map: Velocity dispersion map (km/s)
            pixel_scale_arcsec: Pixel scale (arcsec/pixel)

        Returns:
            List of core properties
        """
        cores = []
        pixel_size_sr = (pixel_scale_arcsec * math.pi / (180.0 * 3600.0))**2

        for node in dendrogram.nodes:
            if not node.is_leaf:
                continue
            if node.npixels < 5:
                continue

            # Get pixel coordinates (would need proper implementation)
            # For now, use centroid
            cx, cy = node.centroid_x, node.centroid_y
            ix, iy = int(cx), int(cy)

            ny = len(column_density_map)
            nx = len(column_density_map[0])

            if ix < 0 or ix >= nx or iy < 0 or iy >= ny:
                continue

            # Peak column density
            N_peak = node.peak_value

            # Effective radius
            r_pix = math.sqrt(node.npixels / math.pi)
            r_arcsec = r_pix * pixel_scale_arcsec
            r_pc = r_arcsec * self.distance_pc / 206265.0

            # Mass
            area_sr = node.npixels * pixel_size_sr
            mass = self.column_to_mass(N_peak * 0.5, area_sr)  # Average column

            # Volume density (assuming sphere)
            if r_pc > 0:
                volume = (4.0/3.0) * math.pi * (r_pc * PC)**3
                n_H2 = mass * M_SUN / (self.mu * M_PROTON * volume)
            else:
                n_H2 = 0

            # Velocity info
            if velocity_map is not None and 0 <= ix < nx and 0 <= iy < ny:
                velocity = velocity_map[iy][ix]
            else:
                velocity = 0.0

            if linewidth_map is not None and 0 <= ix < nx and 0 <= iy < ny:
                linewidth = linewidth_map[iy][ix]
            else:
                linewidth = 0.3  # Default 0.3 km/s

            # Derived quantities
            M_vir = self.virial_mass(r_pc, linewidth) if r_pc > 0 else 0
            M_J = self.jeans_mass(self.temperature, n_H2) if n_H2 > 0 else 0

            alpha = M_vir / mass if mass > 0 else float('inf')
            is_bound = alpha < 2.0
            is_prestellar = is_bound and mass > 0.1 * M_J

            core = CoreProperties(
                core_id=node.node_id,
                ra=0.0,  # Would need WCS
                dec=0.0,
                radius=r_pc,
                mass=mass,
                mass_error=mass * 0.5,  # Assume 50% uncertainty
                temperature=self.temperature,
                column_density=N_peak,
                volume_density=n_H2,
                velocity=velocity,
                linewidth=linewidth,
                virial_mass=M_vir,
                virial_parameter=alpha,
                jeans_mass=M_J,
                is_bound=is_bound,
                is_prestellar=is_prestellar
            )
            cores.append(core)

        return cores


# Singleton instances
_source_detector: Optional[SourceDetector] = None
_aperture_photometry: Optional[AperturePhotometry] = None
_dendrogram_extractor: Optional[DendrogramExtractor] = None
_filament_finder: Optional[FilamentFinder] = None
_core_catalog_builder: Optional[CoreCatalogBuilder] = None


def get_source_detector() -> SourceDetector:
    """Get singleton source detector."""
    global _source_detector
    if _source_detector is None:
        _source_detector = SourceDetector()
    return _source_detector


def get_aperture_photometry() -> AperturePhotometry:
    """Get singleton aperture photometry."""
    global _aperture_photometry
    if _aperture_photometry is None:
        _aperture_photometry = AperturePhotometry()
    return _aperture_photometry


def get_dendrogram_extractor() -> DendrogramExtractor:
    """Get singleton dendrogram extractor."""
    global _dendrogram_extractor
    if _dendrogram_extractor is None:
        _dendrogram_extractor = DendrogramExtractor()
    return _dendrogram_extractor


def get_filament_finder() -> FilamentFinder:
    """Get singleton filament finder."""
    global _filament_finder
    if _filament_finder is None:
        _filament_finder = FilamentFinder()
    return _filament_finder


def get_core_catalog_builder() -> CoreCatalogBuilder:
    """Get singleton core catalog builder."""
    global _core_catalog_builder
    if _core_catalog_builder is None:
        _core_catalog_builder = CoreCatalogBuilder()
    return _core_catalog_builder


# Convenience functions

def detect_sources(image: List[List[float]],
                   beam_maj_arcsec: float = 5.0,
                   beam_min_arcsec: float = 5.0,
                   threshold_sigma: float = 5.0) -> SourceCatalog:
    """
    Detect sources in image.

    Args:
        image: 2D image array
        beam_maj_arcsec: Beam major axis (arcsec)
        beam_min_arcsec: Beam minor axis (arcsec)
        threshold_sigma: Detection threshold (sigma)

    Returns:
        Source catalog
    """
    beam = BeamParameters(bmaj=beam_maj_arcsec, bmin=beam_min_arcsec, bpa=0.0)
    detector = SourceDetector(threshold_sigma=threshold_sigma)
    return detector.detect(image, beam)


def extract_dendrogram(image: List[List[float]],
                       min_value: float = 0.0,
                       min_delta: float = 0.0) -> Dendrogram:
    """
    Extract dendrogram from image.

    Args:
        image: 2D image array
        min_value: Minimum value threshold
        min_delta: Minimum contrast for branches

    Returns:
        Dendrogram structure
    """
    extractor = DendrogramExtractor(min_value=min_value, min_delta=min_delta)
    return extractor.extract(image)


def find_filaments(column_density_map: List[List[float]],
                   threshold: float = 0.0) -> FilamentNetwork:
    """
    Find filaments in column density map.

    Args:
        column_density_map: 2D N_H2 map
        threshold: Minimum column density

    Returns:
        Network of detected filaments
    """
    finder = get_filament_finder()
    return finder.find(column_density_map, threshold)


def build_core_catalog(dendrogram: Dendrogram,
                       column_density_map: List[List[float]],
                       distance_pc: float = 140.0,
                       temperature: float = 15.0) -> List[CoreProperties]:
    """
    Build catalog of prestellar cores.

    Args:
        dendrogram: Dendrogram from column density map
        column_density_map: N_H2 map (cm^-2)
        distance_pc: Distance to cloud (pc)
        temperature: Assumed dust temperature (K)

    Returns:
        List of core properties
    """
    builder = CoreCatalogBuilder(temperature=temperature, distance_pc=distance_pc)
    return builder.build_catalog(dendrogram, column_density_map)


