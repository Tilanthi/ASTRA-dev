#!/usr/bin/env python3
"""
Joint Multi-Messenger Light Curve Modeling

Simultaneously models light curves across multiple messengers:
- Gravitational waves (strain)
- Electromagnetic (optical, IR, UV, X-ray, radio)
- Neutrinos (fluence)

Uses Bayesian inference to jointly fit all data streams and extract
physical parameters with proper uncertainty quantification.

Author: STAN Evolution Team
Date: 2025-03-18
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Callable
from dataclasses import dataclass, field
from scipy import stats, optimize, integrate
from scipy.signal import convolve
import warnings


@dataclass
class MultiMessengerData:
    """Data from multiple messengers"""
    # Times
    gw_times: Optional[np.ndarray] = None
    em_times: Optional[np.ndarray] = None
    neutrino_times: Optional[np.ndarray] = None

    # Measurements
    gw_strain: Optional[np.ndarray] = None
    em_flux: Optional[np.ndarray] = None  # or magnitude
    em_filter: Optional[List[str]] = None
    neutrino_fluence: Optional[np.ndarray] = None

    # Errors
    gw_strain_error: Optional[np.ndarray] = None
    em_flux_error: Optional[np.ndarray] = None
    neutrino_fluence_error: Optional[np.ndarray] = None

    # Metadata
    gw_frequency: Optional[np.ndarray] = None
    em_wavelengths: Optional[np.ndarray] = None  # For filters


@dataclass
class PhysicalParameters:
    """Physical parameters of the event"""
    # Source properties
    mass_1: float  # Primary mass (Msun)
    mass_2: float  # Secondary mass (Msun)
    inclination: float  # Inclination angle (rad)
    distance: float  # Luminosity distance (Mpc)

    # Kilonova properties
    ejecta_mass_dyn: float  # Dynamical ejecta mass (Msun)
    ejecta_mass_wind: float  # Wind ejecta mass (Msun)
    ejecta_velocity: float  # Ejecta velocity (c)
    lanthanide_fraction: float  # Lanthanide fraction [0, 1]

    # Afterglow properties (for GRB)
    jet_energy: float  # Isotropic equivalent energy (erg)
    jet_opening_angle: float  # Jet opening angle (rad)
    circumburst_density: float  # cm^-3
    electron_fraction: float  # epsilon_e
    magnetic_fraction: float  # epsilon_B

    # Neutrino properties
    neutrino_energy_total: float  # Total neutrino energy (erg)
    neutrino_spectrum_index: float  # Spectral index


class GWStrainModel:
    """
    Model gravitational wave strain from compact binary merger.

    Uses inspiral-merger-ringdown phenomenology.
    """

    def __init__(self):
        pass

    def strain_inspiral(
        self,
        times: np.ndarray,
        chirp_mass: float,
        time_to_merger: np.ndarray
    ) -> np.ndarray:
        """
        Strain during inspiral phase.

        Args:
            times: Time array
            chirp_mass: Chirp mass (Msun)
            time_to_merger: Time until merger for each point (positive before merger)

        Returns:
            Strain amplitude (dimensionless h)
        """
        # Simplified inspiral amplitude
        # h ~ (M_ch)^(5/3) * f^(2/3) / D

        # Convert to geometric units
        Mc_geo = chirp_mass * 4.925e-6  # Msun to seconds

        # Amplitude evolution
        # h ~ tau^(-1/4) where tau is time to merger
        tau = np.abs(time_to_merger)
        amplitude = (Mc_geo ** (5/4)) * (tau ** (-1/4))

        # Phase evolution (simplified)
        phase = -2 * (Mc_geo ** (-5/8)) * (tau ** (5/8))

        # Add distance dependence
        # This is simplified - real waveform depends on inclination, polarization
        h = amplitude * np.cos(phase)

        return h

    def frequency_evolution(
        self,
        time_to_merger: np.ndarray,
        chirp_mass: float
    ) -> np.ndarray:
        """
        GW frequency evolution during inspiral.

        Args:
            time_to_merger: Time until merger
            chirp_mass: Chirp mass

        Returns:
            Frequency (Hz)
        """
        Mc_geo = chirp_mass * 4.925e-6

        # f ~ tau^(-3/8)
        f = (1 / (8 * np.pi)) * (Mc_geo ** (-5/8)) * (time_to_merger ** (-3/8))

        return f


class KilonovaLightCurveModel:
    """
    Model kilonova emission across multiple wavelengths.

    Based on radioactive decay heating of r-process material.
    """

    def __init__(self):
        # Wavelength bands (nm)
        self.bands = {
            'u': 365,
            'g': 480,
            'r': 625,
            'i': 750,
            'z': 900,
            'Y': 1020,
            'J': 1250,
            'H': 1650,
            'K': 2200,
        }

    def thermalization_efficiency(
        self,
        time_days: np.ndarray,
        ejecta_mass: float,
        velocity: float
    ) -> np.ndarray:
        """
        Thermalization efficiency of radioactive decay.

        Args:
            time_days: Time since merger (days)
            ejecta_mass: Ejecta mass (Msun)
            velocity: Ejecta velocity (c)

        Returns:
            Thermalization efficiency
        """
        # Characteristic timescale for thermalization loss
        t0 = 0.5 * (ejecta_mass / 0.01)**0.5 * (velocity / 0.1)**-1

        # Efficiency decays as power law
        eth = 1.0 / (1 + (time_days / t0)**1.3)

        return eth

    def radioactive_heating_rate(
        self,
        time_days: np.ndarray,
        ejecta_mass: float
    ) -> np.ndarray:
        """
        Heating rate from radioactive decay.

        Args:
            time_days: Time since merger
            ejecta_mass: Ejecta mass

        Returns:
            Heating rate (erg/s/g)
        """
        # Approximate r-process heating
        # Q_dot ~ 2e10 * exp(-t/0.1 day) + 1e9 * exp(-t/5 day)

        qdot = 2e10 * np.exp(-time_days / 0.1) + 1e9 * np.exp(-time_days / 5.0)

        return qdot * ejecta_mass * 2e33  # Convert to erg/s

    def temperature_evolution(
        self,
        luminosity: np.ndarray,
        time_days: np.ndarray,
        ejecta_mass: float,
        velocity: float
    ) -> np.ndarray:
        """
        Photospheric temperature evolution.

        Args:
            luminosity: Luminosity (erg/s)
            time_days: Time
            ejecta_mass: Ejecta mass
            velocity: Ejecta velocity

        Returns:
            Temperature (K)
        """
        # Radius from homologously expanding ejecta
        c_light = 3e10  # cm/s
        day_to_sec = 86400

        radius = velocity * c_light * time_days * day_to_sec

        # Stefan-Boltzmann: L = 4*pi*R^2*sigma*T^4
        sigma = 5.67e-5  # erg/cm^2/s/K^4

        temperature = (luminosity / (4 * np.pi * radius**2 * sigma))**0.25

        return temperature

    def bolometric_light_curve(
        self,
        time_days: np.ndarray,
        params: PhysicalParameters
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Compute bolometric light curve.

        Args:
            time_days: Time array (days)
            params: Physical parameters

        Returns:
            Tuple of (luminosity, temperature, radius)
        """
        # Total ejecta mass
        m_ej = params.ejecta_mass_dyn + params.ejecta_mass_wind
        v_ej = params.ejecta_velocity

        # Heating rate
        qdot = self.radioactive_heating_rate(time_days, m_ej)

        # Thermalization
        eth = self.thermalization_efficiency(time_days, m_ej, v_ej)

        # Luminosity
        luminosity = qdot * eth

        # Temperature
        temperature = self.temperature_evolution(luminosity, time_days, m_ej, v_ej)

        # Radius
        c_light = 3e10  # cm/s
        radius = v_ej * c_light * time_days * 86400

        return luminosity, temperature, radius

    def band_light_curve(
        self,
        time_days: np.ndarray,
        params: PhysicalParameters,
        band: str
    ) -> np.ndarray:
        """
        Compute light curve in specific photometric band.

        Args:
            time_days: Time array
            params: Physical parameters
            band: Photometric band

        Returns:
            Flux or magnitude in band
        """
        # Get bolometric properties
        L_bol, T, R = self.bolometric_light_curve(time_days, params)

        # Band wavelength
        if band in self.bands:
            wavelength = self.bands[band] * 1e-7  # nm to cm
        else:
            wavelength = 500e-7  # Default green

        # Planck function for blackbody
        h = 6.626e-27  # erg*s
        c = 3e10  # cm/s
        k = 1.38e-16  # erg/K

        # Blackbody intensity
        x = h * c / (wavelength * k * T)
        # Avoid overflow
        x = np.clip(x, 0, 700)

        # Intensity (simplified Planck function)
        intensity = (2 * h * c**2 / wavelength**5) / (np.exp(x) - 1 + 1e-10)

        # Flux from surface area
        flux = intensity * (np.pi * (R / 1e10)**2)  # Rough scaling

        # Apply opacity effects based on lanthanide fraction
        # High lanthanide -> redder, dimmer optical
        if params.lanthanide_fraction > 0.1:
            # Optical suppression
            if band in ['u', 'g', 'r']:
                suppression = np.exp(-params.lanthanide_fraction * 5)
                flux *= suppression

        # Distance dimming
        distance_cm = params.distance * 3.086e24  # Mpc to cm
        flux_observed = flux / (4 * np.pi * distance_cm**2)

        return flux_observed


class GRBAfterglowModel:
    """
    Model GRB afterglow emission across wavelengths.

    Uses synchrotron emission from relativistic shock.
    """

    def __init__(self):
        pass

    def flux_density(
        self,
        frequency: float,
        time_days: float,
        params: PhysicalParameters
    ) -> float:
        """
        Compute afterglow flux density.

        Args:
            frequency: Observing frequency (Hz)
            time_days: Time since burst (days)
            params: Physical parameters

        Returns:
            Flux density (mJy)
        """
        # Simplified afterglow model

        # Normalize time to 1 day
        t = time_days

        # Peak frequency
        nu_m = 1e13 * (t / 1.0)**(-3/2)  # Hz
        nu_c = 1e15 * (t / 1.0)**(-1/2)  # Hz

        # Peak flux
        F_peak = 1.0 * (params.jet_energy / 1e52) * (params.distance / 100)**-2

        # Spectral regime
        if frequency < nu_m:
            # Self-absorption regime
            spectral_index = 2.0
        elif frequency < nu_c:
            # Slow cooling regime
            spectral_index = -1.0/3.0
        else:
            # Fast cooling regime
            spectral_index = -0.5

        # Temporal decay
        temporal_index = -1.2  # Typical post-jet-break

        # Flux
        flux = F_peak * (frequency / nu_m)**spectral_index * (t / 1.0)**temporal_index

        return max(flux, 1e-10)  # mJy


class NeutrinoFluenceModel:
    """
    Model neutrino emission from compact mergers.

    """
    def __init__(self):
        pass

    def fluence(
        self,
        energy: float,
        time_since_merger: float,
        params: PhysicalParameters
    ) -> float:
        """
        Compute neutrino fluence at given energy.

        Args:
            energy: Neutrino energy (GeV)
            time_since_merger: Time since merger (s)
            params: Physical parameters

        Returns:
            Fluence (GeV^-1 cm^-2)
        """
        # Very simplified model
        # Real neutrino emission depends on:
        # - Disk geometry
        # - Magnetic fields
        # - Jet interactions

        # Power-law spectrum
        E0 = 1.0  # GeV
        spectral_index = params.neutrino_spectrum_index

        # Temporal decay
        t0 = 1.0  # seconds
        temporal = np.exp(-time_since_merger / t0)

        # Distance
        distance_cm = params.distance * 3.086e24

        # Fluence
        fluence = (params.neutrino_energy_total / distance_cm**2) * \
                  (energy / E0)**(-spectral_index) * temporal

        return fluence


class JointLikelihood:
    """
    Joint likelihood for multi-messenger observations.

    Combines likelihoods from all messengers with shared parameters.
    """

    def __init__(self):
        self.gw_model = GWStrainModel()
        self.kn_model = KilonovaLightCurveModel()
        self.grb_model = GRBAfterglowModel()
        self.neutrino_model = NeutrinoFluenceModel()

    def log_likelihood(
        self,
        params: PhysicalParameters,
        data: MultiMessengerData,
        gw_merger_time: float = 0.0
    ) -> float:
        """
        Compute joint log-likelihood.

        Args:
            params: Physical parameters
            data: Multi-messenger data
            gw_merger_time: GW merger time (reference)

        Returns:
            Log-likelihood
        """
        log_like = 0.0

        # GW likelihood
        if data.gw_strain is not None and data.gw_times is not None:
            time_to_merger = gw_merger_time - data.gw_times
            chirp_mass = (params.mass_1 * params.mass_2)**(3/5) / \
                         (params.mass_1 + params.mass_2)**(1/5)

            strain_pred = self.gw_model.strain_inspiral(
                data.gw_times, chirp_mass, time_to_merger
            )

            if data.gw_strain_error is not None:
                gw_loglike = np.sum(
                    -0.5 * ((data.gw_strain - strain_pred) / data.gw_strain_error)**2
                    - np.log(data.gw_strain_error * np.sqrt(2 * np.pi))
                )
            else:
                gw_loglike = -np.sum((data.gw_strain - strain_pred)**2)

            log_like += gw_loglike

        # EM likelihood
        if data.em_flux is not None and data.em_times is not None:
            em_loglike = 0.0

            for i, (time, flux) in enumerate(zip(data.em_times, data.em_flux)):
                time_days = time / 86400.0  # Convert to days

                # Get filter for this observation
                if data.em_filter and i < len(data.em_filter):
                    band = data.em_filter[i]
                else:
                    band = 'r'  # Default

                # Predict flux
                flux_pred = self.kn_model.band_light_curve(
                    np.array([time_days]), params, band
                )[0]

                # Gaussian likelihood
                if data.em_flux_error is not None:
                    error = data.em_flux_error[i]
                else:
                    error = 0.1 * flux  # 10% error

                em_loglike += -0.5 * ((flux - flux_pred) / error)**2 - np.log(error)

            log_like += em_loglike

        # Neutrino likelihood
        if data.neutrino_fluence is not None and data.neutrino_times is not None:
            neutrino_loglike = 0.0

            for i, (time, fluence) in enumerate(zip(data.neutrino_times, data.neutrino_fluence)):
                # Simplified - would need energy information
                fluence_pred = self.neutrino_model.fluence(
                    1.0,  # Assume 1 GeV neutrinos
                    time,
                    params
                )

                if data.neutrino_fluence_error is not None:
                    error = data.neutrino_fluence_error[i]
                else:
                    error = fluence_pred  # Order unity

                neutrino_loglike += -0.5 * ((fluence - fluence_pred) / error)**2 - np.log(error)

            log_like += neutrino_loglike

        return log_like


class JointLightCurveFitter:
    """
    Fit joint multi-messenger light curves to extract parameters.

    Uses MCMC or nested sampling for Bayesian inference.
    """

    def __init__(self):
        self.likelihood = JointLikelihood()

    def fit(
        self,
        data: MultiMessengerData,
        initial_params: Optional[PhysicalParameters] = None,
        method: str = 'mcmc'
    ) -> Tuple[PhysicalParameters, np.ndarray]:
        """
        Fit multi-messenger data.

        Args:
            data: Multi-messenger observations
            initial_params: Initial parameter guess
            method: Fitting method ('mcmc', 'nested', 'optimize')

        Returns:
            Tuple of (best_fit_params, parameter_samples)
        """
        if initial_params is None:
            # Default initial parameters
            initial_params = PhysicalParameters(
                mass_1=1.4,
                mass_2=1.4,
                inclination=0.0,
                distance=100.0,
                ejecta_mass_dyn=0.01,
                ejecta_mass_wind=0.01,
                ejecta_velocity=0.1,
                lanthanide_fraction=0.01,
                jet_energy=1e52,
                jet_opening_angle=0.1,
                circumburst_density=1.0,
                electron_fraction=0.1,
                magnetic_fraction=0.01,
                neutrino_energy_total=1e51,
                neutrino_spectrum_index=2.0
            )

        if method == 'optimize':
            return self._optimize_fit(data, initial_params)
        elif method == 'mcmc':
            return self._mcmc_fit(data, initial_params)
        else:
            raise ValueError(f"Unknown method: {method}")

    def _optimize_fit(
        self,
        data: MultiMessengerData,
        initial_params: PhysicalParameters
    ) -> Tuple[PhysicalParameters, np.ndarray]:
        """Optimize likelihood using scipy."""
        params_array = self._params_to_array(initial_params)

        def objective(x):
            params = self._array_to_params(x)
            return -self.likelihood.log_likelihood(params, data)

        result = optimize.minimize(
            objective,
            params_array,
            method='Nelder-Mead',
            options={'maxiter': 10000}
        )

        best_params = self._array_to_params(result.x)

        return best_params, result.x.reshape(1, -1)

    def _mcmc_fit(
        self,
        data: MultiMessengerData,
        initial_params: PhysicalParameters,
        n_walkers: int = 32,
        n_steps: int = 1000
    ) -> Tuple[PhysicalParameters, np.ndarray]:
        """Run MCMC sampling."""
        try:
            import emcee
        except ImportError:
            warnings.warn("emcee not installed, falling back to optimization")
            return self._optimize_fit(data, initial_params)

        # Initialize walkers
        params_array = self._params_to_array(initial_params)
        n_params = len(params_array)

        # Small ball around initial parameters
        walkers = params_array + 0.01 * np.random.randn(n_walkers, n_params)

        # Define log probability
        def log_prob(x):
            params = self._array_to_params(x)

            # Priors (simple uniform priors)
            if not (0.1 < params.mass_1 < 50):
                return -np.inf
            if not (0.1 < params.mass_2 < 50):
                return -np.inf
            if not (1.0 < params.distance < 1000):
                return -np.inf
            if not (0.0 < params.ejecta_mass_dyn < 0.5):
                return -np.inf

            return self.likelihood.log_likelihood(params, data)

        # Create sampler
        sampler = emcee.EnsembleSampler(n_walkers, n_params, log_prob)

        # Run
        print("Running MCMC...")
        sampler.run_mcmc(walkers, n_steps, progress=True)

        # Get samples (remove burn-in)
        burnin = n_steps // 2
        samples = sampler.get_chain(discard=burnin, flat=True)

        # Best parameters (median of posterior)
        best_params_array = np.median(samples, axis=0)
        best_params = self._array_to_params(best_params_array)

        return best_params, samples

    def _params_to_array(self, params: PhysicalParameters) -> np.ndarray:
        """Convert parameters to array for optimization."""
        return np.array([
            params.mass_1,
            params.mass_2,
            params.inclination,
            params.distance,
            params.ejecta_mass_dyn,
            params.ejecta_mass_wind,
            params.ejecta_velocity,
            params.lanthanide_fraction,
            params.jet_energy,
            params.jet_opening_angle,
            params.circumburst_density,
            params.electron_fraction,
            params.magnetic_fraction,
            params.neutrino_energy_total,
            params.neutrino_spectrum_index
        ])

    def _array_to_params(self, array: np.ndarray) -> PhysicalParameters:
        """Convert array to PhysicalParameters."""
        return PhysicalParameters(
            mass_1=array[0],
            mass_2=array[1],
            inclination=array[2],
            distance=array[3],
            ejecta_mass_dyn=array[4],
            ejecta_mass_wind=array[5],
            ejecta_velocity=array[6],
            lanthanide_fraction=array[7],
            jet_energy=array[8],
            jet_opening_angle=array[9],
            circumburst_density=array[10],
            electron_fraction=array[11],
            magnetic_fraction=array[12],
            neutrino_energy_total=array[13],
            neutrino_spectrum_index=array[14]
        )


def create_joint_fitter(**kwargs) -> JointLightCurveFitter:
    """Factory function to create joint light curve fitter."""
    return JointLightCurveFitter(**kwargs)


if __name__ == "__main__":
    print("="*70)
    print("Joint Multi-Messenger Light Curve Modeling")
    print("="*70)
    print()
    print("Components:")
    print("  - JointLightCurveFitter: Main fitting system")
    print("  - GWStrainModel: Gravitational wave model")
    print("  - KilonovaLightCurveModel: Kilonova emission model")
    print("  - GRBAfterglowModel: GRB afterglow model")
    print("  - NeutrinoFluenceModel: Neutrino emission model")
    print("  - JointLikelihood: Combined likelihood function")
    print()
    print("Applications:")
    print("  - Kilonova parameter inference")
    print("  - Joint GW-EM-neutrino parameter estimation")
    print("  - Hubble constant measurement")
    print("  - Ejecta properties from multi-wavelength data")
    print("="*70)
