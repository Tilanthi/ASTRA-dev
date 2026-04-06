"""
ISM Knowledge Base for STAN V43

Comprehensive database of ISM physics expertise including phase properties,
molecular tracers, dust characteristics, magnetic field constraints, and
star formation recipes. Encodes decades of astrophysical knowledge.

Author: STAN V43 Astrophysics Module
"""

import math
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple


class ISMPhase(Enum):
    """Interstellar medium phases."""
    CNM = auto()      # Cold Neutral Medium
    WNM = auto()      # Warm Neutral Medium
    WIM = auto()      # Warm Ionized Medium
    HIM = auto()      # Hot Ionized Medium
    MOLECULAR = auto()  # Molecular clouds
    CORONAL = auto()   # Coronal gas


@dataclass
class ISMPhaseProperties:
    """Properties of an ISM phase."""
    phase: ISMPhase
    temperature_range: Tuple[float, float]  # K
    density_range: Tuple[float, float]      # cm^-3
    ionization_fraction: float
    filling_factor: float
    scale_height: float                     # pc
    tracers: List[str]
    description: str


@dataclass
class MolecularTracer:
    """Properties of a molecular line tracer."""
    molecule: str
    transition: str
    rest_frequency_ghz: float
    critical_density: float           # cm^-3
    energy_upper_K: float            # K
    traces: str                      # What physics it traces
    optical_depth: str               # 'thin', 'thick', 'variable'
    depletion_factor: float          # At high density
    notes: str


@dataclass
class DustProperties:
    """Dust grain properties."""
    model_name: str
    grain_composition: str
    size_distribution: str           # 'MRN', 'WD01', etc.
    kappa_850um: float               # cm^2/g at 850 micron
    beta: float                      # Spectral index
    T_sublimation: float            # K
    polarization_efficiency: float


@dataclass
class MagneticFieldMethod:
    """Method for measuring magnetic fields."""
    method_name: str
    component_measured: str          # 'LOS', 'POS', 'total'
    applicable_phases: List[ISMPhase]
    uncertainty_typical: float       # Fractional
    equation: str
    notes: str


# ISM Phase Database
ISM_PHASES = {
    ISMPhase.CNM: ISMPhaseProperties(
        phase=ISMPhase.CNM,
        temperature_range=(50, 100),
        density_range=(20, 50),
        ionization_fraction=1e-4,
        filling_factor=0.02,
        scale_height=100,
        tracers=['HI_21cm_absorption', 'CI_609um', 'CII_158um'],
        description='Cold, dense atomic gas in pressure equilibrium with WNM'
    ),
    ISMPhase.WNM: ISMPhaseProperties(
        phase=ISMPhase.WNM,
        temperature_range=(5000, 8000),
        density_range=(0.2, 0.5),
        ionization_fraction=0.01,
        filling_factor=0.3,
        scale_height=300,
        tracers=['HI_21cm_emission', 'Halpha_faint'],
        description='Warm atomic gas, dominant volume filler'
    ),
    ISMPhase.WIM: ISMPhaseProperties(
        phase=ISMPhase.WIM,
        temperature_range=(6000, 10000),
        density_range=(0.1, 0.3),
        ionization_fraction=0.9,
        filling_factor=0.25,
        scale_height=1000,
        tracers=['Halpha', 'pulsar_DM', 'NII_6583'],
        description='Diffuse ionized gas, Reynolds layer'
    ),
    ISMPhase.HIM: ISMPhaseProperties(
        phase=ISMPhase.HIM,
        temperature_range=(1e5, 1e7),
        density_range=(1e-3, 1e-2),
        ionization_fraction=1.0,
        filling_factor=0.5,
        scale_height=3000,
        tracers=['OVI_absorption', 'soft_Xray', 'OVII', 'OVIII'],
        description='Hot coronal gas from SNe, fills most volume'
    ),
    ISMPhase.MOLECULAR: ISMPhaseProperties(
        phase=ISMPhase.MOLECULAR,
        temperature_range=(10, 50),
        density_range=(1e2, 1e6),
        ionization_fraction=1e-7,
        filling_factor=0.01,
        scale_height=75,
        tracers=['CO', 'HCN', 'N2H+', 'dust_continuum'],
        description='Dense molecular clouds, star formation sites'
    ),
}

# Molecular Tracer Database
MOLECULAR_TRACERS = {
    'CO_1-0': MolecularTracer(
        molecule='CO', transition='1-0', rest_frequency_ghz=115.271,
        critical_density=2e3, energy_upper_K=5.5,
        traces='bulk_molecular_gas', optical_depth='thick',
        depletion_factor=1.0, notes='Most common tracer, X_CO = 2e20'
    ),
    '13CO_1-0': MolecularTracer(
        molecule='13CO', transition='1-0', rest_frequency_ghz=110.201,
        critical_density=2e3, energy_upper_K=5.3,
        traces='column_density', optical_depth='variable',
        depletion_factor=1.0, notes='Optically thin, column tracer'
    ),
    'C18O_1-0': MolecularTracer(
        molecule='C18O', transition='1-0', rest_frequency_ghz=109.782,
        critical_density=2e3, energy_upper_K=5.3,
        traces='dense_cores', optical_depth='thin',
        depletion_factor=10.0, notes='Traces denser gas, depletes in centers'
    ),
    'HCN_1-0': MolecularTracer(
        molecule='HCN', transition='1-0', rest_frequency_ghz=88.632,
        critical_density=3e6, energy_upper_K=4.3,
        traces='dense_gas', optical_depth='thick',
        depletion_factor=1.0, notes='Dense gas tracer, star-forming regions'
    ),
    'HCO+_1-0': MolecularTracer(
        molecule='HCO+', transition='1-0', rest_frequency_ghz=89.189,
        critical_density=2e5, energy_upper_K=4.3,
        traces='ionization', optical_depth='variable',
        depletion_factor=1.0, notes='Ionization tracer, infall profiles'
    ),
    'N2H+_1-0': MolecularTracer(
        molecule='N2H+', transition='1-0', rest_frequency_ghz=93.174,
        critical_density=3e5, energy_upper_K=4.5,
        traces='cold_dense_cores', optical_depth='thin',
        depletion_factor=0.1, notes='Does not deplete, traces core centers'
    ),
    'NH3_11': MolecularTracer(
        molecule='NH3', transition='(1,1)', rest_frequency_ghz=23.694,
        critical_density=2e3, energy_upper_K=23.4,
        traces='temperature', optical_depth='variable',
        depletion_factor=1.0, notes='Thermometer molecule, HFS for tau'
    ),
    'SiO_2-1': MolecularTracer(
        molecule='SiO', transition='2-1', rest_frequency_ghz=86.847,
        critical_density=1e6, energy_upper_K=6.3,
        traces='shocks', optical_depth='thin',
        depletion_factor=0.001, notes='10^4 enhancement in shocks'
    ),
    'H2O_maser': MolecularTracer(
        molecule='H2O', transition='6_16-5_23', rest_frequency_ghz=22.235,
        critical_density=1e9, energy_upper_K=644,
        traces='shocks_outflows', optical_depth='maser',
        depletion_factor=0.0, notes='Maser in shocked gas, outflow tracer'
    ),
    'CH3OH_masers': MolecularTracer(
        molecule='CH3OH', transition='Class_II', rest_frequency_ghz=6.7,
        critical_density=1e7, energy_upper_K=100,
        traces='massive_star_formation', optical_depth='maser',
        depletion_factor=0.0, notes='Class II masers trace MYSOs'
    ),
}

# Dust Properties Database
DUST_MODELS = {
    'MRN': DustProperties(
        model_name='Mathis-Rumpl-Nordsieck',
        grain_composition='silicate+graphite',
        size_distribution='n(a) ~ a^-3.5, 5nm-250nm',
        kappa_850um=1.0, beta=2.0,
        T_sublimation=1500,
        polarization_efficiency=0.1
    ),
    'OH94': DustProperties(
        model_name='Ossenkopf-Henning 1994',
        grain_composition='coagulated_ice_mantles',
        size_distribution='coagulated at n=10^6',
        kappa_850um=1.85, beta=1.8,
        T_sublimation=100,
        polarization_efficiency=0.05
    ),
    'Draine2003': DustProperties(
        model_name='Draine 2003',
        grain_composition='astrosilicate+carbonaceous',
        size_distribution='updated MRN',
        kappa_850um=0.9, beta=1.7,
        T_sublimation=1500,
        polarization_efficiency=0.15
    ),
}

# Magnetic Field Methods
B_FIELD_METHODS = {
    'Zeeman': MagneticFieldMethod(
        method_name='Zeeman Splitting',
        component_measured='LOS',
        applicable_phases=[ISMPhase.CNM, ISMPhase.MOLECULAR],
        uncertainty_typical=0.3,
        equation='Delta_nu = 2.8 * B_LOS * Hz/microG',
        notes='Direct measurement, requires strong lines (HI, OH, CN)'
    ),
    'DCF': MagneticFieldMethod(
        method_name='Davis-Chandrasekhar-Fermi',
        component_measured='POS',
        applicable_phases=[ISMPhase.MOLECULAR],
        uncertainty_typical=0.5,
        equation='B_POS = sqrt(4*pi*rho) * sigma_v / delta_phi',
        notes='From polarization dispersion, factor of 2 uncertainty'
    ),
    'Faraday': MagneticFieldMethod(
        method_name='Faraday Rotation',
        component_measured='LOS',
        applicable_phases=[ISMPhase.WIM, ISMPhase.HIM],
        uncertainty_typical=0.3,
        equation='RM = 0.81 * integral(n_e * B_LOS * dl)',
        notes='Requires background polarized source, RM synthesis'
    ),
    'Polarization': MagneticFieldMethod(
        method_name='Dust Polarization',
        component_measured='POS',
        applicable_phases=[ISMPhase.MOLECULAR],
        uncertainty_typical=0.2,
        equation='E_pol perpendicular to B_POS',
        notes='Maps field morphology, grain alignment assumed'
    ),
}


class ISMKnowledgeBase:
    """Access point for ISM knowledge."""

    def __init__(self):
        """Initialize knowledge base."""
        self.phases = ISM_PHASES
        self.tracers = MOLECULAR_TRACERS
        self.dust = DUST_MODELS
        self.b_methods = B_FIELD_METHODS

    def get_phase_properties(self, phase: ISMPhase) -> Optional[ISMPhaseProperties]:
        """Get properties for ISM phase."""
        return self.phases.get(phase)

    def get_tracer(self, tracer_id: str) -> Optional[MolecularTracer]:
        """Get tracer by ID."""
        return self.tracers.get(tracer_id)

    def find_tracers_for(self, what: str) -> List[MolecularTracer]:
        """Find tracers for a given purpose."""
        what_lower = what.lower()
        return [t for t in self.tracers.values() if what_lower in t.traces.lower()]

    def recommend_tracer(self, target: str, density: float) -> List[str]:
        """Recommend tracers for given target and density."""
        recommendations = []
        for tid, tracer in self.tracers.items():
            if target.lower() in tracer.traces.lower():
                if tracer.critical_density <= density * 10:
                    recommendations.append(tid)
        return recommendations

    def get_dust_opacity(self, model: str, wavelength_um: float) -> float:
        """Get dust opacity at wavelength."""
        if model not in self.dust:
            model = 'MRN'
        dust = self.dust[model]
        # kappa ~ kappa_850 * (850/wavelength)^beta
        return dust.kappa_850um * (850.0 / wavelength_um)**dust.beta

    def pressure_equilibrium(self, T1: float, n1: float) -> Dict[str, Tuple[float, float]]:
        """Find phases in pressure equilibrium."""
        P = n1 * T1  # P/k
        equilibrium = {}
        for phase, props in self.phases.items():
            T_mid = (props.temperature_range[0] + props.temperature_range[1]) / 2
            n_eq = P / T_mid
            if props.density_range[0] <= n_eq <= props.density_range[1]:
                equilibrium[phase.name] = (T_mid, n_eq)
        return equilibrium


# Star Formation Relations
@dataclass
class SFRelation:
    """Star formation relation."""
    name: str
    equation: str
    normalization: float
    exponent: float
    scatter_dex: float
    applicable_range: str
    reference: str


SF_RELATIONS = {
    'Schmidt-Kennicutt': SFRelation(
        name='Schmidt-Kennicutt',
        equation='Sigma_SFR = A * Sigma_gas^N',
        normalization=2.5e-4,  # M_sun/yr/kpc^2
        exponent=1.4,
        scatter_dex=0.3,
        applicable_range='Sigma_gas > 10 M_sun/pc^2',
        reference='Kennicutt 1998'
    ),
    'Bigiel': SFRelation(
        name='Bigiel Molecular',
        equation='Sigma_SFR = A * Sigma_H2^N',
        normalization=5.25e-2,  # Gyr^-1
        exponent=1.0,
        scatter_dex=0.2,
        applicable_range='Molecular dominated',
        reference='Bigiel et al. 2008'
    ),
    'Lada': SFRelation(
        name='Lada Dense Gas',
        equation='SFR = epsilon * M_dense / t_ff',
        normalization=0.02,  # epsilon
        exponent=1.0,
        scatter_dex=0.3,
        applicable_range='n > 10^4 cm^-3',
        reference='Lada et al. 2010'
    ),
}


def get_ism_knowledge_base() -> ISMKnowledgeBase:
    """Get ISM knowledge base instance."""
    return ISMKnowledgeBase()


def what_traces(phenomenon: str) -> List[str]:
    """Find which tracers are useful for a phenomenon."""
    kb = get_ism_knowledge_base()
    return [t.molecule + '_' + t.transition for t in kb.find_tracers_for(phenomenon)]


def get_critical_density(tracer: str) -> float:
    """Get critical density for a tracer."""
    kb = get_ism_knowledge_base()
    t = kb.get_tracer(tracer)
    return t.critical_density if t else 1e4


def is_phase_transition(T1: float, n1: float, T2: float, n2: float) -> bool:
    """Check if temperature/density change indicates phase transition."""
    kb = get_ism_knowledge_base()

    phase1 = None
    phase2 = None

    for phase, props in kb.phases.items():
        if props.temperature_range[0] <= T1 <= props.temperature_range[1]:
            if props.density_range[0] <= n1 <= props.density_range[1]:
                phase1 = phase
        if props.temperature_range[0] <= T2 <= props.temperature_range[1]:
            if props.density_range[0] <= n2 <= props.density_range[1]:
                phase2 = phase

    return phase1 != phase2 and phase1 is not None and phase2 is not None
