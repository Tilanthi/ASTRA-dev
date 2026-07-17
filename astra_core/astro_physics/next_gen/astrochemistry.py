"""
Astrochemistry: gas-grain chemical networks and abundance analysis.

  * ChemicalNetwork: species + reactions with rate laws, integrated to give
    abundance evolution and steady state (scipy.integrate.solve_ivp).
  * UMISTNetwork / KIDANetwork: seed a small representative network using
    UMIST (McElroy+ 2013) / KIDA (Wakelam+ 2012) style rate coefficients.
  * GrainSurfaceChemistry: H2 formation on dust grains
    (Hollenbach & McKee 1979, 1989): R_H2 ~ 3e-18 T^0.5 cm^3 s^-1.
  * IsotopologueAnalyzer: isotopologue abundance ratios (e.g. 13CO/12CO).
  * COMFormationModel: complex-organic-molecule formation on grains.
  * DeuteriumFractionation: D/H enhancement at low T (H2D+ pathway).

The seed rate coefficients are representative literature values; for research
use, load the real UMIST/KIDA tables.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Tuple, Dict
from scipy.integrate import solve_ivp


@dataclass
class Reaction:
    reactants: Tuple[str, ...]
    products: Tuple[str, ...]
    k: float                       # rate coefficient (cm^3/s 2-body; s^-1 1-body)
    label: str = ""


class ChemicalNetwork:
    """A gas-phase chemical network with an ODE solver."""

    def __init__(self):
        self.species: List[str] = []
        self.reactions: List[Reaction] = []

    def add_species(self, *names: str) -> None:
        for n in names:
            if n not in self.species:
                self.species.append(n)

    def add_reaction(self, reactants, products, k, label="") -> None:
        self.add_species(*reactants, *products)
        self.reactions.append(Reaction(tuple(reactants), tuple(products), k, label))

    def derivatives(self, n: Dict[str, float]) -> Dict[str, float]:
        dn = {s: 0.0 for s in self.species}
        for r in self.reactions:
            rate = r.k
            for sp in r.reactants:
                rate *= n.get(sp, 0.0)
            for sp in r.reactants:
                dn[sp] -= rate
            for sp in r.products:
                dn[sp] += rate
        return dn

    def evolve(self, n0: Dict[str, float], t_final: float,
               n_steps: int = 200) -> Tuple[np.ndarray, Dict[str, np.ndarray]]:
        idx = {s: i for i, s in enumerate(self.species)}
        y0 = np.array([n0.get(s, 0.0) for s in self.species])

        def f(t, y):
            n = {s: y[i] for s, i in idx.items()}
            return [self.derivatives(n)[s] for s in self.species]

        t = np.linspace(0, t_final, n_steps)
        sol = solve_ivp(f, (0, t_final), y0, t_eval=t, method='LSODA', rtol=1e-6)
        return sol.t, {s: sol.y[i] for s, i in idx.items()}

    def steady_state(self, n0: Dict[str, float], t_final: float = 1e16,
                     atol: float = 1e-3) -> Dict[str, float]:
        _, hist = self.evolve(n0, t_final, n_steps=10)
        return {s: hist[s][-1] for s in self.species}


class UMISTNetwork(ChemicalNetwork):
    """A small representative UMIST-style (McElroy+ 2013) network."""

    def __init__(self, cosmic_ray_rate: float = 1.3e-17):
        super().__init__()
        zeta = cosmic_ray_rate
        # H2 formation on grains + photodissociation + cosmic-ray ionisation
        self.add_reaction(['H', 'grain'], ['H2'], 3.0e-18, 'H2_grain_formation')
        self.add_reaction(['H2'], ['H', 'H'], 5.0e-11 * 0.5, 'H2_photodissociation')
        self.add_reaction(['H'], ['H+', 'e-'], zeta, 'CR_ionisation')
        # C+ + H2 -> CH2+ ; CO formation chain (heavily simplified)
        self.add_reaction(['C+', 'H2'], ['CH2+', 'photon'], 1.0e-16, 'C+_H2')
        self.add_reaction(['CH2+', 'e-'], ['CH', 'H'], 1.0e-8, 'dissoc_recomb')
        self.add_reaction(['CH', 'O'], ['CO', 'H'], 6.6e-13, 'CH_O_CO')


class KIDANetwork(UMISTNetwork):
    """KIDA-style (Wakelam+ 2012) seed network; same representative rates here."""
    pass


class GrainSurfaceChemistry:
    """H2 formation on dust-grain surfaces (Hollenbach & McKee 1979, 1989).

    R_H2(T) ~ 3e-18 T^0.5 cm^3 s^-1 (per H nucleus).
    """

    NORM = 3.0e-18

    def h2_formation_rate_coeff(self, T_K: float) -> float:
        return self.NORM * np.sqrt(max(T_K, 1.0))

    def h2_formation_rate(self, n_H_cm3: float, T_K: float) -> float:
        """dn(H2)/dt from grain-surface formation (cm^-3 s^-1)."""
        return 0.5 * self.h2_formation_rate_coeff(T_K) * n_H_cm3 ** 2


class IsotopologueAnalyzer:
    """Isotopologue abundance ratios under fractionation + selective
    photodissociation (e.g. 13CO/12CO ~ 1/30-1/60 in local clouds; Visser+ 2009)."""

    def ratio_13CO_12CO(self, A_V: float, T_K: float = 20.0,
                        elemental_ratio: float = 69.0) -> float:
        """Approximate 13CO/12CO vs visual extinction (fractionation dominates
        at A_V < ~5, selective photodissociation raises it modestly)."""
        base = 1.0 / elemental_ratio
        # fractionation factor ~1-1.3 at low A_V, ~1 deep in (schematic)
        frac = 1.0 + 0.3 * np.exp(-A_V / 3.0)
        return base * frac


class COMFormationModel:
    """Complex-organic-molecule (COM) formation: grain-surface chemistry during
    the cold phase followed by ice desorption (Herbst & van Dishoeck 2009)."""

    DESORPTION_TEMP_K = 100.0

    def com_yield(self, A_V: float, T_K: float, time_yr: float) -> float:
        """Schematic COM abundance (relative to H2) after cold-surface chemistry
        + thermal desorption (vanishes once T exceeds the desorption T)."""
        surface_abund = 1e-9 * (1.0 - np.exp(-time_yr / 1e5)) * min(A_V / 5.0, 1.0)
        if T_K > self.DESORPTION_TEMP_K:
            return 0.0
        return surface_abund


class DeuteriumFractionation:
    """D/H fractionation via H2D+ at low T (Caselli+ 2008; Ceccarelli+ 2014).

    N2D+/N2H+ (and H2D+/H3+) rises sharply below ~30 K because the backward
    reaction H2D+ + H2 -> H3+ + HD has a ~230 K barrier.
    """

    def h2dplus_enhancement(self, T_K: float) -> float:
        """Approximate [H2D+]/[H3+] enhancement factor vs the cosmic D/H (~1.5e-5)."""
        if T_K <= 0:
            return 1.0
        # schematic exponential suppression of the back-reaction below ~30 K
        return np.exp(max(0.0, (30.0 - T_K) / 15.0)) * 1.5e-5


__all__ = [
    'ChemicalNetwork', 'UMISTNetwork', 'KIDANetwork', 'GrainSurfaceChemistry',
    'IsotopologueAnalyzer', 'COMFormationModel', 'DeuteriumFractionation',
    'Reaction',
]
