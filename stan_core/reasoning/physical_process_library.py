"""
Physical Process Library for STAN V43

Encyclopedia of astrophysical mechanisms for reasoning about ISM physics.
Provides a searchable database of physical processes with equations,
inputs/outputs, validity conditions, and causal relationships.

Features:
- ~100 ISM physical processes with full documentation
- Searchable by category, observable, timescale
- Causal chain building (A -> B -> C)
- Mechanism matching from observations
- Process validity checking

Author: STAN V43 Astrophysics Module
"""

import math
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple, Set, Callable, Any


class ProcessCategory(Enum):
    """Categories of physical processes."""
    RADIATIVE = auto()        # Emission/absorption processes
    DYNAMICAL = auto()        # Motion and forces
    THERMAL = auto()          # Heating and cooling
    CHEMICAL = auto()         # Chemical reactions
    MAGNETIC = auto()         # Magnetic field processes
    NUCLEAR = auto()          # Nuclear reactions
    GRAVITATIONAL = auto()    # Gravity-related
    TURBULENT = auto()        # Turbulence-related


class ProcessTimescale(Enum):
    """Characteristic timescales."""
    INSTANTANEOUS = auto()    # < 1 yr
    FAST = auto()             # 1 - 1000 yr
    INTERMEDIATE = auto()     # 1000 yr - 1 Myr
    SLOW = auto()             # 1 Myr - 100 Myr
    VERY_SLOW = auto()        # > 100 Myr


class EnergyScale(Enum):
    """Energy scales of processes."""
    THERMAL = auto()          # k_B * T ~ 1 meV - 1 eV
    CHEMICAL = auto()         # ~1 eV
    IONIZATION = auto()       # 1 - 100 eV
    X_RAY = auto()            # 0.1 - 10 keV
    GAMMA = auto()            # > 100 keV
    NUCLEAR = auto()          # MeV


@dataclass
class PhysicalQuantity:
    """A physical quantity with units."""
    name: str
    symbol: str
    units: str
    typical_range: Tuple[float, float]  # (min, max)
    description: str = ""


@dataclass
class ProcessEquation:
    """Mathematical representation of a process."""
    equation: str             # LaTeX-style equation
    python_form: str          # Python expression
    dependencies: List[str]   # Required input quantities
    output: str               # Output quantity name


@dataclass
class ValidityCondition:
    """Condition for process applicability."""
    parameter: str            # Parameter to check
    condition: str            # 'gt', 'lt', 'between', 'eq'
    value: float              # Threshold value
    value_max: Optional[float] = None  # For 'between'
    units: str = ""
    explanation: str = ""


@dataclass
class PhysicalProcess:
    """Complete specification of a physical process."""
    process_id: str           # Unique identifier
    name: str                 # Human-readable name
    category: ProcessCategory
    subcategory: str          # More specific classification
    description: str          # Full description

    # Physics
    equation: ProcessEquation
    rate_equation: Optional[ProcessEquation] = None  # For time-dependent

    # Inputs and outputs
    inputs: List[PhysicalQuantity] = field(default_factory=list)
    outputs: List[PhysicalQuantity] = field(default_factory=list)

    # Validity
    validity_conditions: List[ValidityCondition] = field(default_factory=list)
    domain: str = "ISM"       # Physical domain

    # Timescales
    timescale: ProcessTimescale = ProcessTimescale.INTERMEDIATE
    timescale_equation: Optional[str] = None  # Formula for timescale

    # Observables
    observational_signatures: List[str] = field(default_factory=list)
    tracer_molecules: List[str] = field(default_factory=list)

    # Connections
    causes: List[str] = field(default_factory=list)  # Process IDs this causes
    caused_by: List[str] = field(default_factory=list)  # Process IDs that cause this

    # Metadata
    references: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)


class ProcessLibrary:
    """
    Searchable database of astrophysical processes.
    """

    def __init__(self):
        """Initialize process library."""
        self.processes: Dict[str, PhysicalProcess] = {}
        self._build_library()

    def _build_library(self):
        """Build the complete process library."""
        self._add_radiative_processes()
        self._add_dynamical_processes()
        self._add_thermal_processes()
        self._add_chemical_processes()
        self._add_magnetic_processes()
        self._add_gravitational_processes()

    def _add_radiative_processes(self):
        """Add radiative transfer processes."""

        # Thermal dust emission
        self.processes['thermal_dust_emission'] = PhysicalProcess(
            process_id='thermal_dust_emission',
            name='Thermal Dust Emission',
            category=ProcessCategory.RADIATIVE,
            subcategory='continuum',
            description='Modified blackbody emission from heated dust grains',
            equation=ProcessEquation(
                equation=r'I_\nu = B_\nu(T_d) (1 - e^{-\tau_\nu})',
                python_form='B_nu(T_d) * (1 - exp(-tau_nu))',
                dependencies=['T_dust', 'tau_dust', 'frequency'],
                output='intensity'
            ),
            inputs=[
                PhysicalQuantity('dust_temperature', 'T_d', 'K', (10, 1000), 'Dust grain temperature'),
                PhysicalQuantity('dust_opacity', 'kappa', 'cm^2/g', (0.1, 100), 'Mass opacity'),
            ],
            outputs=[
                PhysicalQuantity('intensity', 'I_nu', 'erg/s/cm^2/Hz/sr', (1e-20, 1e-10), 'Specific intensity'),
            ],
            validity_conditions=[
                ValidityCondition('T_dust', 'gt', 3.0, units='K', explanation='Above CMB'),
                ValidityCondition('wavelength', 'gt', 1.0, units='micron', explanation='FIR/submm regime'),
            ],
            timescale=ProcessTimescale.INSTANTANEOUS,
            observational_signatures=['FIR continuum', 'submm continuum', 'SED peak'],
            keywords=['dust', 'continuum', 'thermal', 'FIR', 'submm']
        )

        # Free-free (Bremsstrahlung) emission
        self.processes['free_free_emission'] = PhysicalProcess(
            process_id='free_free_emission',
            name='Free-Free (Bremsstrahlung) Emission',
            category=ProcessCategory.RADIATIVE,
            subcategory='continuum',
            description='Thermal radiation from electron-ion encounters in ionized gas',
            equation=ProcessEquation(
                equation=r'\epsilon_{ff} = 6.8 \times 10^{-38} T^{-0.5} n_e n_i g_{ff}',
                python_form='6.8e-38 * T**(-0.5) * n_e * n_i * g_ff',
                dependencies=['T_e', 'n_e', 'n_i'],
                output='emissivity'
            ),
            inputs=[
                PhysicalQuantity('electron_temperature', 'T_e', 'K', (1e3, 1e8), 'Electron temperature'),
                PhysicalQuantity('electron_density', 'n_e', 'cm^-3', (0.01, 1e6), 'Electron density'),
            ],
            outputs=[
                PhysicalQuantity('emissivity', 'epsilon_ff', 'erg/s/cm^3/Hz', (1e-40, 1e-20), 'Volume emissivity'),
            ],
            validity_conditions=[
                ValidityCondition('T_e', 'gt', 1000, units='K', explanation='Requires ionized gas'),
            ],
            timescale=ProcessTimescale.INSTANTANEOUS,
            observational_signatures=['radio continuum', 'X-ray continuum', 'flat spectrum'],
            tracer_molecules=['HII region radio', 'SNR radio'],
            keywords=['ionized', 'continuum', 'radio', 'X-ray', 'HII']
        )

        # Line emission (general)
        self.processes['spectral_line_emission'] = PhysicalProcess(
            process_id='spectral_line_emission',
            name='Spectral Line Emission',
            category=ProcessCategory.RADIATIVE,
            subcategory='line',
            description='Photon emission from atomic/molecular transitions',
            equation=ProcessEquation(
                equation=r'j_\nu = \frac{h\nu}{4\pi} n_u A_{ul} \phi(\nu)',
                python_form='h_nu / (4 * pi) * n_upper * A_ul * phi_nu',
                dependencies=['n_upper', 'A_ul', 'line_profile'],
                output='line_emissivity'
            ),
            inputs=[
                PhysicalQuantity('upper_population', 'n_u', 'cm^-3', (1e-3, 1e10), 'Upper level population'),
                PhysicalQuantity('einstein_A', 'A_ul', 's^-1', (1e-10, 1e10), 'Einstein A coefficient'),
            ],
            outputs=[
                PhysicalQuantity('line_emissivity', 'j_nu', 'erg/s/cm^3/Hz/sr', (1e-30, 1e-10), 'Line emissivity'),
            ],
            timescale=ProcessTimescale.INSTANTANEOUS,
            observational_signatures=['emission lines', 'absorption lines'],
            keywords=['line', 'molecular', 'atomic', 'spectroscopy']
        )

        # Synchrotron emission
        self.processes['synchrotron_emission'] = PhysicalProcess(
            process_id='synchrotron_emission',
            name='Synchrotron Emission',
            category=ProcessCategory.RADIATIVE,
            subcategory='non-thermal',
            description='Radiation from relativistic electrons in magnetic fields',
            equation=ProcessEquation(
                equation=r'P_{sync} \propto B^2 \gamma^2',
                python_form='const * B**2 * gamma**2',
                dependencies=['B_field', 'electron_gamma'],
                output='synchrotron_power'
            ),
            inputs=[
                PhysicalQuantity('magnetic_field', 'B', 'G', (1e-6, 1e-2), 'Magnetic field strength'),
                PhysicalQuantity('lorentz_factor', 'gamma', '', (1, 1e7), 'Electron Lorentz factor'),
            ],
            outputs=[
                PhysicalQuantity('power', 'P_sync', 'erg/s', (1e-20, 1e40), 'Synchrotron power'),
            ],
            validity_conditions=[
                ValidityCondition('gamma', 'gt', 1, explanation='Relativistic electrons'),
            ],
            timescale=ProcessTimescale.FAST,
            timescale_equation='t_cool = 6*pi*m_e*c / (sigma_T * B^2 * gamma)',
            observational_signatures=['radio continuum', 'power-law spectrum', 'polarization'],
            keywords=['non-thermal', 'radio', 'SNR', 'jets', 'polarization']
        )

    def _add_dynamical_processes(self):
        """Add dynamical processes."""

        # Gravitational collapse
        self.processes['gravitational_collapse'] = PhysicalProcess(
            process_id='gravitational_collapse',
            name='Gravitational Collapse',
            category=ProcessCategory.DYNAMICAL,
            subcategory='contraction',
            description='Self-gravitating contraction of gas clouds',
            equation=ProcessEquation(
                equation=r't_{ff} = \sqrt{\frac{3\pi}{32 G \rho}}',
                python_form='sqrt(3 * pi / (32 * G * rho))',
                dependencies=['density'],
                output='freefall_time'
            ),
            rate_equation=ProcessEquation(
                equation=r'\dot{M} \approx c_s^3 / G',
                python_form='c_s**3 / G',
                dependencies=['sound_speed'],
                output='accretion_rate'
            ),
            inputs=[
                PhysicalQuantity('density', 'rho', 'g/cm^3', (1e-24, 1e-10), 'Gas mass density'),
                PhysicalQuantity('sound_speed', 'c_s', 'cm/s', (1e4, 1e6), 'Isothermal sound speed'),
            ],
            outputs=[
                PhysicalQuantity('freefall_time', 't_ff', 's', (1e10, 1e15), 'Free-fall timescale'),
                PhysicalQuantity('accretion_rate', 'Mdot', 'g/s', (1e15, 1e25), 'Mass accretion rate'),
            ],
            validity_conditions=[
                ValidityCondition('virial_parameter', 'lt', 2.0, explanation='Gravitationally bound'),
            ],
            timescale=ProcessTimescale.INTERMEDIATE,
            causes=['protostar_formation', 'disk_formation'],
            caused_by=['jeans_instability', 'turbulence_dissipation'],
            observational_signatures=['infall signature', 'blue asymmetry', 'density profile'],
            tracer_molecules=['N2H+', 'NH3', 'H2D+'],
            keywords=['collapse', 'star formation', 'cores', 'infall']
        )

        # Outflow/jet launching
        self.processes['protostellar_outflow'] = PhysicalProcess(
            process_id='protostellar_outflow',
            name='Protostellar Outflow',
            category=ProcessCategory.DYNAMICAL,
            subcategory='ejection',
            description='Bipolar mass ejection from accreting protostars',
            equation=ProcessEquation(
                equation=r'\dot{M}_{out} \approx 0.1 \dot{M}_{acc}',
                python_form='0.1 * Mdot_acc',
                dependencies=['accretion_rate'],
                output='outflow_rate'
            ),
            inputs=[
                PhysicalQuantity('accretion_rate', 'Mdot_acc', 'M_sun/yr', (1e-8, 1e-4), 'Accretion rate'),
            ],
            outputs=[
                PhysicalQuantity('outflow_rate', 'Mdot_out', 'M_sun/yr', (1e-9, 1e-5), 'Mass outflow rate'),
                PhysicalQuantity('momentum_flux', 'F_out', 'M_sun km/s/yr', (1e-8, 1e-3), 'Momentum flux'),
            ],
            timescale=ProcessTimescale.FAST,
            causes=['shock_heating', 'turbulence_injection'],
            caused_by=['gravitational_collapse', 'magnetocentrifugal_acceleration'],
            observational_signatures=['bipolar lobes', 'high-velocity wings', 'Herbig-Haro objects'],
            tracer_molecules=['CO', 'SiO', 'H2'],
            keywords=['outflow', 'jets', 'Class 0/I', 'feedback']
        )

        # Turbulence
        self.processes['turbulent_cascade'] = PhysicalProcess(
            process_id='turbulent_cascade',
            name='Turbulent Cascade',
            category=ProcessCategory.TURBULENT,
            subcategory='energy_transfer',
            description='Energy transfer from large to small scales',
            equation=ProcessEquation(
                equation=r'\epsilon \sim \sigma^3 / L',
                python_form='sigma**3 / L',
                dependencies=['velocity_dispersion', 'scale'],
                output='dissipation_rate'
            ),
            inputs=[
                PhysicalQuantity('velocity_dispersion', 'sigma', 'km/s', (0.1, 10), 'Turbulent velocity'),
                PhysicalQuantity('scale', 'L', 'pc', (0.01, 100), 'Injection scale'),
            ],
            outputs=[
                PhysicalQuantity('dissipation_rate', 'epsilon', 'erg/g/s', (1e-5, 1e5), 'Energy dissipation'),
            ],
            timescale=ProcessTimescale.INTERMEDIATE,
            timescale_equation='t_turb = L / sigma',
            causes=['turbulent_fragmentation', 'line_broadening'],
            caused_by=['supernovae', 'stellar_winds', 'outflows', 'cloud_collisions'],
            observational_signatures=['supersonic linewidths', 'structure functions', 'filaments'],
            keywords=['turbulence', 'supersonic', 'energy cascade', 'ISM']
        )

    def _add_thermal_processes(self):
        """Add heating and cooling processes."""

        # Cosmic ray heating
        self.processes['cosmic_ray_heating'] = PhysicalProcess(
            process_id='cosmic_ray_heating',
            name='Cosmic Ray Heating',
            category=ProcessCategory.THERMAL,
            subcategory='heating',
            description='Gas heating by cosmic ray ionization',
            equation=ProcessEquation(
                equation=r'\Gamma_{CR} = \zeta n_H \times 20 \, eV',
                python_form='zeta * n_H * 3.2e-11',  # 20 eV in erg
                dependencies=['zeta_CR', 'n_H'],
                output='heating_rate'
            ),
            inputs=[
                PhysicalQuantity('ionization_rate', 'zeta', 's^-1', (1e-17, 1e-15), 'CR ionization rate'),
                PhysicalQuantity('H_density', 'n_H', 'cm^-3', (1, 1e6), 'Hydrogen number density'),
            ],
            outputs=[
                PhysicalQuantity('heating_rate', 'Gamma_CR', 'erg/s/cm^3', (1e-28, 1e-22), 'Volume heating rate'),
            ],
            timescale=ProcessTimescale.SLOW,
            causes=['gas_ionization', 'chemical_reactions'],
            observational_signatures=['ionization fraction', 'H3+ abundance'],
            tracer_molecules=['H3+', 'HCO+', 'DCO+'],
            keywords=['cosmic rays', 'heating', 'ionization', 'dense gas']
        )

        # Radiative cooling
        self.processes['line_cooling'] = PhysicalProcess(
            process_id='line_cooling',
            name='Atomic/Molecular Line Cooling',
            category=ProcessCategory.THERMAL,
            subcategory='cooling',
            description='Radiative cooling through line emission',
            equation=ProcessEquation(
                equation=r'\Lambda = n^2 \Lambda(T)',
                python_form='n**2 * Lambda_T',
                dependencies=['density', 'temperature'],
                output='cooling_rate'
            ),
            inputs=[
                PhysicalQuantity('density', 'n', 'cm^-3', (0.1, 1e8), 'Number density'),
                PhysicalQuantity('temperature', 'T', 'K', (10, 1e4), 'Gas temperature'),
            ],
            outputs=[
                PhysicalQuantity('cooling_rate', 'Lambda', 'erg/s/cm^3', (1e-30, 1e-20), 'Volume cooling rate'),
            ],
            validity_conditions=[
                ValidityCondition('temperature', 'between', 10, value_max=1e4, units='K'),
            ],
            timescale=ProcessTimescale.FAST,
            causes=['thermal_instability', 'cloud_formation'],
            observational_signatures=['[CII] 158um', '[OI] 63um', 'CO lines'],
            tracer_molecules=['[CII]', '[OI]', '[CI]', 'CO'],
            keywords=['cooling', 'ISM', 'thermal equilibrium']
        )

        # Shock heating
        self.processes['shock_heating'] = PhysicalProcess(
            process_id='shock_heating',
            name='Shock Heating',
            category=ProcessCategory.THERMAL,
            subcategory='heating',
            description='Gas heating by passage through shock front',
            equation=ProcessEquation(
                equation=r'T_s = \frac{3 \mu m_H v_s^2}{16 k_B}',
                python_form='3 * mu * m_H * v_s**2 / (16 * k_B)',
                dependencies=['shock_velocity', 'mu'],
                output='post_shock_temperature'
            ),
            inputs=[
                PhysicalQuantity('shock_velocity', 'v_s', 'km/s', (1, 1000), 'Shock velocity'),
            ],
            outputs=[
                PhysicalQuantity('temperature', 'T_s', 'K', (1e3, 1e8), 'Post-shock temperature'),
            ],
            validity_conditions=[
                ValidityCondition('mach_number', 'gt', 1.0, explanation='Supersonic shock'),
            ],
            timescale=ProcessTimescale.INSTANTANEOUS,
            causes=['molecule_destruction', 'grain_sputtering', 'line_emission'],
            caused_by=['supernovae', 'outflows', 'cloud_collisions', 'stellar_winds'],
            observational_signatures=['broad lines', 'SiO emission', 'H2 emission'],
            tracer_molecules=['SiO', 'H2O', 'SO', 'CH3OH'],
            keywords=['shocks', 'J-shock', 'C-shock', 'heating']
        )

    def _add_chemical_processes(self):
        """Add chemical processes."""

        # Ion-molecule chemistry
        self.processes['ion_molecule_reactions'] = PhysicalProcess(
            process_id='ion_molecule_reactions',
            name='Ion-Molecule Reactions',
            category=ProcessCategory.CHEMICAL,
            subcategory='gas_phase',
            description='Fast reactions between ions and neutral molecules',
            equation=ProcessEquation(
                equation=r'k \sim 10^{-9} \, cm^3/s',
                python_form='1e-9',  # Langevin rate
                dependencies=[],
                output='reaction_rate'
            ),
            inputs=[
                PhysicalQuantity('ion_density', 'n_i', 'cm^-3', (1e-4, 1e3), 'Ion number density'),
                PhysicalQuantity('molecule_density', 'n_m', 'cm^-3', (1, 1e8), 'Molecule density'),
            ],
            outputs=[
                PhysicalQuantity('reaction_rate', 'R', 'cm^-3 s^-1', (1e-15, 1e5), 'Reaction rate'),
            ],
            timescale=ProcessTimescale.FAST,
            causes=['molecular_complexity', 'isotope_fractionation'],
            caused_by=['cosmic_ray_ionization', 'uv_photoionization'],
            observational_signatures=['molecular abundances', 'deuteration'],
            tracer_molecules=['HCO+', 'N2H+', 'H3+'],
            keywords=['chemistry', 'ions', 'molecules', 'cold gas']
        )

        # Grain surface chemistry
        self.processes['grain_surface_reactions'] = PhysicalProcess(
            process_id='grain_surface_reactions',
            name='Grain Surface Reactions',
            category=ProcessCategory.CHEMICAL,
            subcategory='grain_surface',
            description='Chemical reactions on dust grain surfaces',
            equation=ProcessEquation(
                equation=r'R = n_X n_Y \sigma_g v_{th} S',
                python_form='n_X * n_Y * sigma_g * v_th * S',
                dependencies=['gas_densities', 'grain_cross_section', 'thermal_velocity', 'sticking'],
                output='formation_rate'
            ),
            inputs=[
                PhysicalQuantity('gas_density', 'n', 'cm^-3', (1e2, 1e8), 'Gas density'),
                PhysicalQuantity('temperature', 'T', 'K', (10, 100), 'Gas/grain temperature'),
            ],
            outputs=[
                PhysicalQuantity('formation_rate', 'R_H2', 'cm^-3 s^-1', (1e-20, 1e-10), 'H2 formation rate'),
            ],
            validity_conditions=[
                ValidityCondition('temperature', 'lt', 100, units='K', explanation='Efficient sticking'),
            ],
            timescale=ProcessTimescale.INTERMEDIATE,
            causes=['h2_formation', 'ice_mantle_growth', 'complex_molecules'],
            observational_signatures=['ice features', 'H2 abundance', 'complex organics'],
            tracer_molecules=['H2', 'H2O ice', 'CH3OH ice', 'CO2 ice'],
            keywords=['grains', 'ice', 'H2', 'surface chemistry']
        )

        # Photodissociation
        self.processes['photodissociation'] = PhysicalProcess(
            process_id='photodissociation',
            name='Photodissociation',
            category=ProcessCategory.CHEMICAL,
            subcategory='destruction',
            description='Molecular destruction by UV photons',
            equation=ProcessEquation(
                equation=r'R_{pd} = k_0 G_0 e^{-\gamma A_V}',
                python_form='k0 * G0 * exp(-gamma * A_V)',
                dependencies=['unshielded_rate', 'UV_field', 'extinction'],
                output='photodissociation_rate'
            ),
            inputs=[
                PhysicalQuantity('UV_field', 'G0', '', (1, 1e5), 'UV field in Habing units'),
                PhysicalQuantity('extinction', 'A_V', 'mag', (0, 100), 'Visual extinction'),
            ],
            outputs=[
                PhysicalQuantity('rate', 'k_pd', 's^-1', (1e-12, 1e-8), 'Photodissociation rate'),
            ],
            validity_conditions=[
                ValidityCondition('A_V', 'lt', 10, units='mag', explanation='UV penetration'),
            ],
            timescale=ProcessTimescale.FAST,
            causes=['pdr_structure', 'atomic_abundances'],
            caused_by=['stellar_radiation', 'isrf'],
            observational_signatures=['PDR edges', 'molecular boundaries'],
            tracer_molecules=['CO photodissociation', 'H2 self-shielding'],
            keywords=['UV', 'photodissociation', 'PDR', 'molecular cloud edges']
        )

    def _add_magnetic_processes(self):
        """Add magnetic field processes."""

        # Ambipolar diffusion
        self.processes['ambipolar_diffusion'] = PhysicalProcess(
            process_id='ambipolar_diffusion',
            name='Ambipolar Diffusion',
            category=ProcessCategory.MAGNETIC,
            subcategory='diffusion',
            description='Drift of neutrals through ions/magnetic field',
            equation=ProcessEquation(
                equation=r't_{AD} = \frac{\rho \rho_i \langle\sigma v\rangle}{B^2/(4\pi)}',
                python_form='rho * rho_i * sigma_v / (B**2 / (4 * pi))',
                dependencies=['density', 'ionization', 'B_field'],
                output='diffusion_time'
            ),
            inputs=[
                PhysicalQuantity('density', 'rho', 'g/cm^3', (1e-22, 1e-16), 'Gas density'),
                PhysicalQuantity('B_field', 'B', 'G', (1e-6, 1e-3), 'Magnetic field'),
                PhysicalQuantity('ionization', 'x_i', '', (1e-8, 1e-4), 'Ionization fraction'),
            ],
            outputs=[
                PhysicalQuantity('timescale', 't_AD', 'yr', (1e5, 1e8), 'Ambipolar diffusion time'),
            ],
            timescale=ProcessTimescale.SLOW,
            causes=['magnetic_flux_loss', 'core_contraction'],
            observational_signatures=['B-rho relation', 'hourglass morphology'],
            keywords=['magnetic', 'diffusion', 'star formation', 'cores']
        )

        # Flux freezing
        self.processes['flux_freezing'] = PhysicalProcess(
            process_id='flux_freezing',
            name='Magnetic Flux Freezing',
            category=ProcessCategory.MAGNETIC,
            subcategory='coupling',
            description='Magnetic field frozen into ionized gas',
            equation=ProcessEquation(
                equation=r'B \propto \rho^{2/3}',
                python_form='B0 * (rho / rho0)**(2/3)',
                dependencies=['density'],
                output='B_field'
            ),
            inputs=[
                PhysicalQuantity('density', 'rho', 'g/cm^3', (1e-24, 1e-16), 'Gas density'),
            ],
            outputs=[
                PhysicalQuantity('B_field', 'B', 'G', (1e-6, 1e-2), 'Magnetic field strength'),
            ],
            validity_conditions=[
                ValidityCondition('ionization', 'gt', 1e-7, explanation='Sufficient coupling'),
            ],
            timescale=ProcessTimescale.INSTANTANEOUS,
            causes=['field_amplification', 'magnetic_support'],
            observational_signatures=['B-n correlation', 'Zeeman measurements'],
            keywords=['magnetic', 'ideal MHD', 'flux freezing']
        )

    def _add_gravitational_processes(self):
        """Add gravitational processes."""

        # Jeans instability
        self.processes['jeans_instability'] = PhysicalProcess(
            process_id='jeans_instability',
            name='Jeans Instability',
            category=ProcessCategory.GRAVITATIONAL,
            subcategory='instability',
            description='Gravitational instability for self-gravitating gas',
            equation=ProcessEquation(
                equation=r'M_J = \left(\frac{5 k_B T}{G \mu m_H}\right)^{3/2} \left(\frac{3}{4\pi\rho}\right)^{1/2}',
                python_form='(5 * k_B * T / (G * mu * m_H))**1.5 * (3 / (4 * pi * rho))**0.5',
                dependencies=['temperature', 'density'],
                output='jeans_mass'
            ),
            inputs=[
                PhysicalQuantity('temperature', 'T', 'K', (5, 1000), 'Gas temperature'),
                PhysicalQuantity('density', 'rho', 'g/cm^3', (1e-24, 1e-16), 'Gas density'),
            ],
            outputs=[
                PhysicalQuantity('jeans_mass', 'M_J', 'M_sun', (0.01, 100), 'Jeans mass'),
                PhysicalQuantity('jeans_length', 'L_J', 'pc', (0.01, 10), 'Jeans length'),
            ],
            timescale=ProcessTimescale.INTERMEDIATE,
            causes=['gravitational_collapse', 'fragmentation'],
            observational_signatures=['core mass function', 'fragmentation scale'],
            keywords=['instability', 'fragmentation', 'star formation', 'Jeans']
        )

        # Virial equilibrium
        self.processes['virial_equilibrium'] = PhysicalProcess(
            process_id='virial_equilibrium',
            name='Virial Equilibrium',
            category=ProcessCategory.GRAVITATIONAL,
            subcategory='equilibrium',
            description='Balance of kinetic, gravitational, and magnetic energies',
            equation=ProcessEquation(
                equation=r'2K + W + M = 0',
                python_form='2 * E_kinetic + E_gravitational + E_magnetic',
                dependencies=['mass', 'radius', 'velocity_dispersion', 'B_field'],
                output='virial_parameter'
            ),
            inputs=[
                PhysicalQuantity('mass', 'M', 'M_sun', (0.1, 1e6), 'Cloud mass'),
                PhysicalQuantity('radius', 'R', 'pc', (0.01, 100), 'Cloud radius'),
                PhysicalQuantity('velocity_dispersion', 'sigma', 'km/s', (0.1, 10), 'Velocity dispersion'),
            ],
            outputs=[
                PhysicalQuantity('virial_parameter', 'alpha', '', (0.1, 10), 'Virial parameter'),
            ],
            timescale=ProcessTimescale.INTERMEDIATE,
            observational_signatures=['Larson relations', 'cloud structure'],
            keywords=['virial', 'equilibrium', 'cloud stability']
        )

    def get_process(self, process_id: str) -> Optional[PhysicalProcess]:
        """Get process by ID."""
        return self.processes.get(process_id)

    def search_by_category(self, category: ProcessCategory) -> List[PhysicalProcess]:
        """Find all processes in a category."""
        return [p for p in self.processes.values() if p.category == category]

    def search_by_keyword(self, keyword: str) -> List[PhysicalProcess]:
        """Find processes matching a keyword."""
        keyword_lower = keyword.lower()
        results = []
        for p in self.processes.values():
            if any(keyword_lower in kw.lower() for kw in p.keywords):
                results.append(p)
            elif keyword_lower in p.name.lower():
                results.append(p)
            elif keyword_lower in p.description.lower():
                results.append(p)
        return results

    def search_by_observable(self, observable: str) -> List[PhysicalProcess]:
        """Find processes that produce an observable."""
        obs_lower = observable.lower()
        return [p for p in self.processes.values()
                if any(obs_lower in sig.lower() for sig in p.observational_signatures)]

    def search_by_tracer(self, tracer: str) -> List[PhysicalProcess]:
        """Find processes traced by a molecule."""
        return [p for p in self.processes.values()
                if any(tracer.upper() in t.upper() for t in p.tracer_molecules)]

    def get_causes(self, process_id: str) -> List[PhysicalProcess]:
        """Get processes caused by this process."""
        process = self.get_process(process_id)
        if process is None:
            return []
        return [self.processes[pid] for pid in process.causes if pid in self.processes]

    def get_caused_by(self, process_id: str) -> List[PhysicalProcess]:
        """Get processes that cause this process."""
        process = self.get_process(process_id)
        if process is None:
            return []
        return [self.processes[pid] for pid in process.caused_by if pid in self.processes]


class MechanismMatcher:
    """
    Match observations to physical mechanisms.
    """

    def __init__(self, library: ProcessLibrary):
        """Initialize mechanism matcher."""
        self.library = library

    def match_observables(self, observables: List[str]) -> List[PhysicalProcess]:
        """
        Find processes that explain a set of observables.

        Args:
            observables: List of observed features

        Returns:
            Matching processes ranked by relevance
        """
        scores: Dict[str, int] = {}

        for obs in observables:
            matches = self.library.search_by_observable(obs)
            for proc in matches:
                scores[proc.process_id] = scores.get(proc.process_id, 0) + 1

        # Sort by score
        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
        return [self.library.get_process(pid) for pid in sorted_ids if self.library.get_process(pid)]


class ProcessChainBuilder:
    """
    Build causal chains of physical processes.
    """

    def __init__(self, library: ProcessLibrary):
        """Initialize chain builder."""
        self.library = library

    def find_chain(self, start: str, end: str,
                   max_length: int = 5) -> List[List[str]]:
        """
        Find causal chains connecting two processes.

        Args:
            start: Starting process ID
            end: Target process ID
            max_length: Maximum chain length

        Returns:
            List of process ID chains
        """
        if start not in self.library.processes or end not in self.library.processes:
            return []

        chains = []
        self._dfs(start, end, [start], chains, max_length)
        return chains

    def _dfs(self, current: str, target: str, path: List[str],
             chains: List[List[str]], max_length: int):
        """Depth-first search for chains."""
        if len(path) > max_length:
            return

        if current == target:
            chains.append(list(path))
            return

        process = self.library.get_process(current)
        if process is None:
            return

        for next_id in process.causes:
            if next_id not in path:  # Avoid cycles
                path.append(next_id)
                self._dfs(next_id, target, path, chains, max_length)
                path.pop()

    def explain_observation_chain(self, observation: str,
                                  initial_condition: str) -> List[str]:
        """
        Build explanation chain from initial condition to observation.

        Args:
            observation: Observed feature
            initial_condition: Initial physical state

        Returns:
            List of process IDs forming the explanation
        """
        # Find processes that produce the observation
        end_processes = self.library.search_by_observable(observation)
        if not end_processes:
            return []

        # Find processes matching initial condition
        start_processes = self.library.search_by_keyword(initial_condition)
        if not start_processes:
            return []

        # Find shortest chain
        best_chain = None
        for start in start_processes:
            for end in end_processes:
                chains = self.find_chain(start.process_id, end.process_id)
                for chain in chains:
                    if best_chain is None or len(chain) < len(best_chain):
                        best_chain = chain

        return best_chain if best_chain else []


# Singleton instance
_process_library: Optional[ProcessLibrary] = None


def get_process_library() -> ProcessLibrary:
    """Get singleton process library."""
    global _process_library
    if _process_library is None:
        _process_library = ProcessLibrary()
    return _process_library


def get_mechanism_matcher() -> MechanismMatcher:
    """Get mechanism matcher."""
    return MechanismMatcher(get_process_library())


def get_chain_builder() -> ProcessChainBuilder:
    """Get chain builder."""
    return ProcessChainBuilder(get_process_library())


# Convenience functions

def find_process(keyword: str) -> List[PhysicalProcess]:
    """Search for processes by keyword."""
    return get_process_library().search_by_keyword(keyword)


def explain_observable(observable: str) -> List[PhysicalProcess]:
    """Find processes that can explain an observable."""
    return get_process_library().search_by_observable(observable)


def get_process_chain(start: str, end: str) -> List[List[str]]:
    """Find causal chains between processes."""
    return get_chain_builder().find_chain(start, end)
