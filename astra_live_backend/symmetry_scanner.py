# Copyright 2024-2026 Glenn J. White (The Open University / RAL Space)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
ASTRA Live — Symmetry Scanner
Tests datasets and validated results for symmetries and universal behaviour:
scale invariance, universal exponents, critical phenomena, and conservation laws.

Phase 2 of the ASTRA theoretical framework infrastructure.
As described in White & Dey (2026), Section 5 (Theory Synthesis).
"""
import re
import time
import math
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple, Any

import numpy as np
from scipy import stats

try:
    from .theory import Theory  # noqa: F401
except ImportError:
    pass  # theory.py may be written in parallel; not required here


# ─── Dataclasses ──────────────────────────────────────────────────────────────

@dataclass
class SymmetryFinding:
    symmetry_type: str          # "scale_invariant", "universal_exponent",
                                # "critical_point", "conservation"
    variable: str
    value: float                # The exponent, scaling parameter, etc.
    significance: float         # Statistical confidence (0–1)
    interpretation: str         # Physical interpretation
    theoretical_implications: List[str]  # What theories this supports/suggests

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symmetry_type": self.symmetry_type,
            "variable": self.variable,
            "value": self.value,
            "significance": self.significance,
            "interpretation": self.interpretation,
            "theoretical_implications": self.theoretical_implications,
        }


@dataclass
class SymmetryReport:
    findings: List[SymmetryFinding] = field(default_factory=list)
    scan_time: float = field(default_factory=time.time)
    n_datasets_scanned: int = 0
    n_hypotheses_scanned: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "findings": [f.to_dict() for f in self.findings],
            "scan_time": self.scan_time,
            "n_datasets_scanned": self.n_datasets_scanned,
            "n_hypotheses_scanned": self.n_hypotheses_scanned,
            "n_findings": len(self.findings),
        }


# ─── Known universal exponents ────────────────────────────────────────────────

_UNIVERSAL_EXPONENTS: List[Dict] = [
    {"value": 1/3,   "label": "Kolmogorov turbulence (velocity)",
     "interpretation": "Kolmogorov 1941 inertial-range velocity scaling",
     "implications": ["Incompressible turbulence", "Kolmogorov energy cascade"]},

    {"value": 5/3,   "label": "Kolmogorov turbulence (energy spectrum)",
     "interpretation": "Kolmogorov E(k) ∝ k^{-5/3} energy spectrum",
     "implications": ["ISM turbulence", "Solar wind", "Turbulent star formation"]},

    {"value": 4/3,   "label": "Adiabatic gas exponent",
     "interpretation": "Adiabatic index γ = 4/3 for ultra-relativistic or radiation-dominated gas",
     "implications": ["Stellar core collapse", "Radiation-dominated equation of state"]},

    {"value": 2/3,   "label": "Virial theorem scaling",
     "interpretation": "Virial equilibrium: T ∝ M^{2/3} for homogeneous sphere",
     "implications": ["Virial theorem", "Jeans mass", "Cluster dynamics"]},

    {"value": 1/2,   "label": "Diffusion / random walk",
     "interpretation": "Diffusive displacement σ ∝ t^{1/2}",
     "implications": ["Particle diffusion", "Magnetic field diffusion", "ISM random walks"]},

    {"value": 3/4,   "label": "Metabolic scaling (Kleiber)",
     "interpretation": "Basal metabolic rate ∝ M^{3/4} (Kleiber's law)",
     "implications": ["Biological network scaling", "Cross-domain universality"]},

    {"value": 1.0,   "label": "Linear proportionality",
     "interpretation": "Direct proportionality — simplest scaling",
     "implications": ["Conservation law", "Single power source"]},

    {"value": 2.0,   "label": "Quadratic scaling",
     "interpretation": "Area-like or kinetic energy scaling",
     "implications": ["Geometric area", "Kinetic energy", "Pressure scaling"]},

    {"value": -1.0,  "label": "Inverse proportionality",
     "interpretation": "Inverse scaling — conservative flux law",
     "implications": ["Flux conservation", "Pressure-volume relation"]},

    {"value": -2.0,  "label": "Inverse-square law",
     "interpretation": "1/r² geometry — gravity, electrostatics, radiation dilution",
     "implications": ["Gravity", "Electrostatics", "Radiative dilution"]},

    {"value": 3/2,   "label": "Kepler's third law",
     "interpretation": "Orbital period P ∝ a^{3/2} (Kepler's third law)",
     "implications": ["Keplerian orbits", "Disk dynamics", "Exoplanet architecture"]},

    {"value": 0.6,   "label": "Mass-radius (rocky planets)",
     "interpretation": "Planet radius ∝ M^{0.6} for rocky bodies",
     "implications": ["Planet interior structure", "Mass-radius relation"]},

    {"value": 1.4,   "label": "Kennicutt-Schmidt index",
     "interpretation": "SFR surface density ∝ Σ_gas^{1.4} (Kennicutt-Schmidt)",
     "implications": ["Star formation law", "ISM self-regulation"]},
]


def _nearest_simple_fraction(value: float,
                             max_p: int = 5,
                             max_q: int = 5) -> Tuple[int, int, float]:
    """
    Find nearest simple fraction p/q (p,q ≤ max_p/max_q) to value.
    Returns (p, q, relative_error).
    """
    best_p, best_q, best_err = 1, 1, float("inf")
    for q in range(1, max_q + 1):
        for p in range(-max_p, max_p + 1):
            if p == 0 and q == 1:
                continue
            frac = p / q
            err = abs(frac - value) / max(abs(value), 1e-9)
            if err < best_err:
                best_err = err
                best_p, best_q = p, q
    return best_p, best_q, best_err


def _find_universal_match(exponent: float,
                           tolerance: float = 0.05) -> Optional[Dict]:
    """Return the known universal exponent closest to value, if within tolerance."""
    for entry in _UNIVERSAL_EXPONENTS:
        if abs(entry["value"] - exponent) / max(abs(exponent), 1e-9) <= tolerance:
            return entry
    return None


# ─── Scale-invariance test ────────────────────────────────────────────────────

def _test_scale_invariance(
    data: np.ndarray,
    variable_name: str,
) -> Optional[SymmetryFinding]:
    """
    Test for power-law distribution using log-log OLS linearity.
    Also performs a KS goodness-of-fit test against the fitted power law.
    Returns a SymmetryFinding if the data is consistent with scale invariance.
    """
    data = data[np.isfinite(data) & (data > 0)]
    if len(data) < 20:
        return None

    # Rank-frequency (complementary CDF) for power-law fit
    sorted_data = np.sort(data)
    n = len(sorted_data)
    rank = np.arange(n, 0, -1)  # reverse rank
    ccdf = rank / n

    # Log-log linear fit
    log_x = np.log10(sorted_data)
    log_y = np.log10(ccdf + 1e-12)
    slope, intercept, r_value, p_value, _ = stats.linregress(log_x, log_y)

    r2 = r_value ** 2
    if r2 < 0.80:
        return None

    exponent = -slope  # CCDF slope = -(α-1) for Pareto; α ≈ |slope| + 1
    confidence = r2

    # KS test: compare to synthetic power-law sample
    if exponent > 1.0:
        # Generate theoretical power-law CDF samples
        xmin = sorted_data[0]
        alpha = exponent
        theoretical = xmin * (1 - np.random.uniform(0, 1, n)) ** (-1 / (alpha - 1))
        ks_stat, ks_p = stats.ks_2samp(sorted_data, theoretical)
        significance = max(0.0, min(1.0, 1.0 - ks_stat))
    else:
        significance = confidence

    if significance < 0.50:
        return None

    universal = _find_universal_match(exponent)
    p_num, p_den, frac_err = _nearest_simple_fraction(exponent)
    fraction_label = (
        f"{p_num}/{p_den}" if abs(p_den) > 1 and frac_err < 0.05
        else f"{exponent:.3f}"
    )

    interp = (
        f"{variable_name} follows a power-law distribution with exponent ≈ {exponent:.3f} "
        f"({fraction_label})."
    )
    if universal:
        interp += f" Matches known universal exponent: {universal['label']}."

    implications = [
        "Scale-free distribution consistent with self-organised criticality or hierarchical process.",
        f"Power-law exponent α ≈ {exponent:.3f} — no characteristic scale.",
    ]
    if universal:
        implications.extend(universal["implications"])

    return SymmetryFinding(
        symmetry_type="scale_invariant",
        variable=variable_name,
        value=round(exponent, 4),
        significance=round(significance, 4),
        interpretation=interp,
        theoretical_implications=implications,
    )


# ─── Universal-exponent check ─────────────────────────────────────────────────

def _check_universal_exponent(
    exponent: float,
    variable_name: str,
    tolerance: float = 0.05,
) -> Optional[SymmetryFinding]:
    """
    Given an observed exponent, check against known universal values.
    Also checks the nearest simple fraction.
    """
    universal = _find_universal_match(exponent, tolerance)
    p_num, p_den, frac_err = _nearest_simple_fraction(exponent)

    if universal is None and frac_err > tolerance:
        return None

    if universal:
        label = universal["label"]
        interp = (
            f"Exponent {exponent:.4f} for '{variable_name}' matches "
            f"universal value {universal['value']:.4f} ({label}). "
            f"Δ = {abs(exponent - universal['value']):.4f}."
        )
        significance = max(0.0, 1.0 - abs(exponent - universal["value"]) / tolerance)
        implications = list(universal["implications"])
    else:
        frac_str = f"{p_num}/{p_den} = {p_num/p_den:.4f}"
        interp = (
            f"Exponent {exponent:.4f} for '{variable_name}' is within {frac_err*100:.1f}% "
            f"of simple fraction {frac_str}. May indicate fundamental ratio."
        )
        significance = max(0.0, 1.0 - frac_err / tolerance)
        implications = [
            f"Rational exponent {frac_str} may reflect geometric or dimensional constraint.",
            "Warrants comparison against known scaling laws.",
        ]

    return SymmetryFinding(
        symmetry_type="universal_exponent",
        variable=variable_name,
        value=round(exponent, 4),
        significance=round(significance, 4),
        interpretation=interp,
        theoretical_implications=implications,
    )


# ─── Critical-point detector ──────────────────────────────────────────────────

def _test_critical_point(
    data: np.ndarray,
    variable_name: str,
) -> Optional[SymmetryFinding]:
    """
    Test for power-law variance scaling: Var(subsample) ∝ N^γ,
    indicative of critical phenomena (diverging susceptibility).
    """
    data = data[np.isfinite(data)]
    n = len(data)
    if n < 50:
        return None

    # Subsample at different sizes and measure variance
    sizes = np.linspace(10, n, num=min(20, n // 5), dtype=int)
    sizes = np.unique(sizes[sizes >= 10])
    if len(sizes) < 5:
        return None

    rng = np.random.default_rng(42)
    log_sizes = []
    log_vars = []
    for sz in sizes:
        idx = rng.choice(n, size=sz, replace=False)
        v = np.var(data[idx])
        if v > 0:
            log_sizes.append(math.log(sz))
            log_vars.append(math.log(v))

    if len(log_vars) < 4:
        return None

    slope, _, r_value, p_value, _ = stats.linregress(log_sizes, log_vars)
    r2 = r_value ** 2

    # Near-critical if variance grows super-linearly with system size
    if slope <= 0.1 or r2 < 0.70:
        return None

    gamma = slope
    significance = r2 * (1.0 - p_value) if p_value < 1.0 else r2

    interp = (
        f"Variance of '{variable_name}' scales as N^{gamma:.2f} with subsample size, "
        f"consistent with critical-point behaviour (diverging correlation length). "
        f"R² = {r2:.3f}."
    )

    implications = [
        f"Power-law variance scaling (γ ≈ {gamma:.2f}) is hallmark of critical phenomena.",
        "System may be near a phase transition or tipping point.",
        "Suggests universality class membership; critical exponents should be measured.",
        "Renormalisation group analysis warranted.",
    ]
    if 1.8 < gamma < 2.2:
        implications.append("γ ≈ 2 consistent with mean-field universality class.")

    return SymmetryFinding(
        symmetry_type="critical_point",
        variable=variable_name,
        value=round(gamma, 4),
        significance=round(min(significance, 1.0), 4),
        interpretation=interp,
        theoretical_implications=implications,
    )


# ─── Conservation-law symmetry (causal graph) ─────────────────────────────────

def _check_conservation_law(
    causal_graph,
    variable_name: str,
) -> Optional[SymmetryFinding]:
    """
    Given a CausalGraph (from causal.py), check whether the directed edge
    structure on 'variable_name' is consistent with a conserved quantity
    (no directed cycles involving that variable).
    """
    try:
        edges = causal_graph.edges  # list of CausalEdge
    except AttributeError:
        return None

    # Build adjacency set for directed edges only
    directed = {
        (e.source, e.target)
        for e in edges
        if e.edge_type in ("-->", "->", "x->")
    }

    # DFS cycle detection restricted to paths through variable_name
    def has_cycle_through(var: str) -> bool:
        # Find all nodes reachable from var via directed edges
        visited: set = set()
        stack = [var]
        while stack:
            node = stack.pop()
            if node in visited:
                continue
            visited.add(node)
            for (src, tgt) in directed:
                if src == node:
                    if tgt == var:
                        return True  # cycle back to var
                    stack.append(tgt)
        return False

    cycle_exists = has_cycle_through(variable_name)
    if cycle_exists:
        return None  # cycle means not conserved

    # Count in-edges and out-edges for variable_name
    in_edges = [e for e in edges if e.target == variable_name and e.edge_type in ("-->", "->")]
    out_edges = [e for e in edges if e.source == variable_name and e.edge_type in ("-->", "->")]

    significance = 0.75 if (len(in_edges) > 0 or len(out_edges) > 0) else 0.5

    interp = (
        f"'{variable_name}' has no directed cycles in the causal graph "
        f"(in-edges: {len(in_edges)}, out-edges: {len(out_edges)}), "
        f"consistent with a conserved quantity."
    )
    implications = [
        f"'{variable_name}' may satisfy a conservation law (energy, momentum, mass, charge).",
        "Noether's theorem: conservation law implies a continuous symmetry of the system.",
        "Directed acyclic structure: variable is not feedback-amplified.",
    ]

    return SymmetryFinding(
        symmetry_type="conservation",
        variable=variable_name,
        value=float(len(in_edges) + len(out_edges)),
        significance=significance,
        interpretation=interp,
        theoretical_implications=implications,
    )


# ─── Extract exponent from hypothesis description ─────────────────────────────

def _extract_exponent(description: str) -> Optional[float]:
    """Attempt to parse a numeric exponent from a hypothesis description string."""
    m = re.search(
        r"(?:exponent|α|β|index|slope|power|γ)\s*[=≈~]\s*([-+]?\d+\.?\d*)",
        description.lower(),
    )
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            pass
    # Also look for bare fractions like "5/3" or "2/3" near key words
    m2 = re.search(r"(\d+)\s*/\s*(\d+)\s+(?:exponent|scaling|index|slope)", description.lower())
    if m2:
        try:
            return int(m2.group(1)) / int(m2.group(2))
        except (ValueError, ZeroDivisionError):
            pass
    return None


# ─── SymmetryScanner ─────────────────────────────────────────────────────────

class SymmetryScanner:
    """
    Scans datasets and hypotheses for symmetries, universal exponents,
    critical phenomena, and conservation-law signatures.
    """

    def __init__(self):
        self._last_report: Optional[SymmetryReport] = None

    # ── Public API ────────────────────────────────────────────────────────────

    def scan_dataset(
        self,
        data: np.ndarray,
        variable_names: Optional[List[str]] = None,
    ) -> List[SymmetryFinding]:
        """
        Scan a numpy array (1-D or 2-D columns) for symmetry signatures.
        variable_names: list of column labels (default: col_0, col_1, …).
        """
        data = np.atleast_2d(data)
        if data.shape[0] < data.shape[1]:
            data = data.T  # ensure rows = observations, cols = variables

        n_cols = data.shape[1]
        if variable_names is None:
            variable_names = [f"col_{i}" for i in range(n_cols)]
        variable_names = list(variable_names) + [f"col_{i}" for i in range(len(variable_names), n_cols)]

        findings: List[SymmetryFinding] = []
        for i in range(n_cols):
            col = data[:, i]
            vname = variable_names[i]

            # Scale invariance
            f = _test_scale_invariance(col, vname)
            if f:
                findings.append(f)

            # Critical point
            f = _test_critical_point(col, vname)
            if f:
                findings.append(f)

            # Universal exponent: if scale-invariance exponent was found, check it
            for sf in findings:
                if sf.symmetry_type == "scale_invariant" and sf.variable == vname:
                    f2 = _check_universal_exponent(sf.value, vname)
                    if f2:
                        findings.append(f2)
                    break

        return findings

    def scan_hypothesis(self, hypothesis) -> List[SymmetryFinding]:
        """
        Scan a single Hypothesis object for symmetry signatures
        (currently: universal exponent detection from description).
        """
        findings: List[SymmetryFinding] = []
        exponent = _extract_exponent(hypothesis.description)
        if exponent is not None:
            f = _check_universal_exponent(exponent, hypothesis.name)
            if f:
                findings.append(f)
        return findings

    def full_scan(self, hypothesis_store) -> List[SymmetryFinding]:
        """
        Scan all hypotheses in the store for universal exponents.
        Returns combined SymmetryFindings.
        """
        findings: List[SymmetryFinding] = []
        hypotheses = hypothesis_store.all()
        for h in hypotheses:
            findings.extend(self.scan_hypothesis(h))
        return findings

    def scan_with_causal_graph(
        self,
        hypothesis_store,
        causal_graph,
        variables: Optional[List[str]] = None,
    ) -> SymmetryReport:
        """
        Full scan including causal-graph conservation-law checks.
        Returns a SymmetryReport.
        """
        report = SymmetryReport()

        # Hypothesis-level scan
        hyp_findings = self.full_scan(hypothesis_store)
        report.findings.extend(hyp_findings)
        report.n_hypotheses_scanned = len(hypothesis_store.all())

        # Conservation-law checks
        if causal_graph is not None and variables:
            for var in variables:
                f = _check_conservation_law(causal_graph, var)
                if f:
                    report.findings.append(f)

        self._last_report = report
        return report

    def get_last_report(self) -> Optional[SymmetryReport]:
        return self._last_report

    # ── Convenience wrappers ──────────────────────────────────────────────────

    @staticmethod
    def test_scale_invariance(data: np.ndarray, variable_name: str = "x") -> Optional[SymmetryFinding]:
        """Standalone wrapper for scale-invariance test."""
        return _test_scale_invariance(data, variable_name)

    @staticmethod
    def check_universal_exponent(exponent: float, variable_name: str = "x") -> Optional[SymmetryFinding]:
        """Standalone wrapper for universal-exponent check."""
        return _check_universal_exponent(exponent, variable_name)

    @staticmethod
    def test_critical_point(data: np.ndarray, variable_name: str = "x") -> Optional[SymmetryFinding]:
        """Standalone wrapper for critical-point test."""
        return _test_critical_point(data, variable_name)
