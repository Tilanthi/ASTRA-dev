"""
ASTRA Live — Active Observational Design (Critical Experiment Designer)
Given two competing theories or contradictory hypotheses, design the optimal
discriminating observation.

The ideal critical experiment is one where:
  - Theory A and Theory B make maximally different predictions
  - The discriminating observable is accessible with current or near-future instrumentation
  - The required precision is achievable in reasonable observing time

As described in White & Dey (2026), Section 3: Theoretical Framework Layer.

References:
- Popper, K. (1959) "The Logic of Scientific Discovery"
- Box, G.E.P. (1980) "Sampling and Bayes' inference in scientific modelling"
"""
import time
import uuid
import re
import math
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Data class
# ---------------------------------------------------------------------------

@dataclass
class CriticalExperiment:
    """An optimal discriminating observation between two competing theories."""
    id: str
    theory_a_id: str                    # First competing theory/hypothesis
    theory_b_id: str                    # Second competing theory/hypothesis
    discriminating_observable: str      # What to measure
    parameter_regime: Dict              # Where to look, e.g. {"mass": ">1e12 Msun"}
    predicted_value_a: str              # Theory A's prediction
    predicted_value_b: str              # Theory B's prediction
    divergence_magnitude: float         # How different the predictions are (0-1)
    feasibility: str                    # "current_technology", "near_future", "speculative"
    required_precision: str             # What precision is needed to discriminate
    suggested_instruments: List[str]    # e.g. ["ALMA", "JWST", "SKA"]
    estimated_observing_time: str       # Rough estimate
    scientific_value: float             # divergence × feasibility_weight
    generated_at: float

    def to_dict(self) -> Dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Instrument database
# ---------------------------------------------------------------------------

# Instrument capabilities: domain → list of instruments
INSTRUMENTS: Dict[str, List[str]] = {
    "radio_continuum":      ["VLA", "ALMA", "SKA", "LOFAR", "MeerKAT", "VLBI"],
    "submm_fir":            ["ALMA", "Herschel/SPIRE", "SOFIA", "JCMT", "SCUBA-2"],
    "optical_spectroscopy": ["VLT/MUSE", "Keck/DEIMOS", "DESI", "4MOST", "WEAVE"],
    "optical_imaging":      ["HST/ACS", "JWST/NIRCam", "Rubin/LSST", "Euclid/VIS"],
    "nir_spectroscopy":     ["JWST/NIRSpec", "VLT/KMOS", "Keck/MOSFIRE", "Magellan/FIRE"],
    "x_ray":                ["Chandra/ACIS", "XMM-Newton/EPIC", "eROSITA", "Athena"],
    "gamma_ray":            ["Fermi/LAT", "INTEGRAL", "CTA"],
    "gravitational_waves":  ["LIGO", "Virgo", "LISA", "Einstein Telescope"],
    "astrometry":           ["Gaia/DR4", "VLBI", "HST/FGS"],
    "molecular_lines":      ["ALMA", "IRAM 30m", "Nobeyama 45m", "GBT", "APEX"],
    "hi_21cm":              ["VLA", "MeerKAT", "SKA", "WSRT/APERTIF"],
    "polarimetry":          ["ALMA/PolCal", "JCMT/POL-2", "SOFIA/HAWC+", "VLA"],
    "uv_optical":           ["HST/COS", "XMM/OM", "GALEX", "Swift/UVOT"],
    "time_domain":          ["Rubin/LSST", "ZTF", "TESS", "Gaia"],
}

# Feasibility tiers by instrument
_CURRENT_INSTRUMENTS = {
    "VLA", "ALMA", "LOFAR", "MeerKAT", "VLBI",
    "Herschel/SPIRE", "JCMT", "SCUBA-2",
    "VLT/MUSE", "Keck/DEIMOS", "DESI",
    "HST/ACS", "JWST/NIRCam", "JWST/NIRSpec", "VLT/KMOS",
    "Chandra/ACIS", "XMM-Newton/EPIC", "eROSITA",
    "Fermi/LAT", "LIGO", "Virgo",
    "Gaia/DR4", "IRAM 30m", "Nobeyama 45m", "GBT", "APEX",
    "VLA", "Rubin/LSST", "ZTF", "TESS",
    "JCMT/POL-2", "SOFIA/HAWC+", "HST/COS", "GALEX",
    "4MOST",
}
_NEAR_FUTURE_INSTRUMENTS = {
    "SKA", "Euclid/VIS", "WEAVE", "CTA", "Athena",
    "LISA", "Einstein Telescope", "SOFIA",
}

# Observable keyword → relevant instrument domains
_OBSERVABLE_DOMAIN_MAP: List[Tuple[List[str], List[str]]] = [
    (["dust", "fir", "far-infrared", "continuum submm", "thermal", "column density", "temperature map"],
     ["submm_fir"]),
    (["molecular line", "co ", "hcn", "cs ", "nh3", "n2h", "h2co", "water maser", "maser"],
     ["molecular_lines"]),
    (["radio continuum", "synchrotron", "free-free", "spectral index", "flux density"],
     ["radio_continuum"]),
    (["hi ", "21 cm", "21cm", "neutral hydrogen"],
     ["hi_21cm"]),
    (["magnetic field", "polarisation", "polarization", "b-field", "faraday"],
     ["polarimetry"]),
    (["x-ray", "x ray", "hot gas", "plasma", "chandra", "xmm"],
     ["x_ray"]),
    (["redshift", "spectroscopy", "velocity", "emission line", "absorption line"],
     ["optical_spectroscopy"]),
    (["proper motion", "parallax", "astrometry"],
     ["astrometry"]),
    (["optical", "visual", "magnitude", "photometry", "colour"],
     ["optical_imaging"]),
    (["infrared", "nir", "k-band", "h-band", "j-band"],
     ["nir_spectroscopy"]),
    (["gravitational wave"],
     ["gravitational_waves"]),
    (["gamma", "mev", "gev"],
     ["gamma_ray"]),
    (["transient", "variability", "light curve"],
     ["time_domain"]),
    (["uv", "ultraviolet"],
     ["uv_optical"]),
]


# ---------------------------------------------------------------------------
# Observable suggestion knowledge base
# (principle pair → discriminating observable, parameter regime, predictions A/B)
# ---------------------------------------------------------------------------

_DISCRIMINATION_KB: List[Dict] = [
    {
        "keywords_a": ["jeans", "thermal", "gravitational collapse"],
        "keywords_b": ["turbulence", "mach", "supersonic"],
        "observable": "Dense core mass function (CMF) peak mass vs. turbulent linewidth",
        "parameter_regime": {"linewidth": ">1 km/s (supersonic)", "mass_range": "0.1–10 Msun"},
        "prediction_a": "CMF peak at thermal Jeans mass (independent of linewidth)",
        "prediction_b": "CMF peak scales with sonic mass ∝ σ_turb²",
        "domain": "submm_fir",
        "precision": "~15% accuracy in core masses; velocity resolution < 0.1 km/s",
        "time_estimate": "~20 hr JCMT/SCUBA-2 + ~10 hr ALMA follow-up",
    },
    {
        "keywords_a": ["salpeter", "imf", "universal"],
        "keywords_b": ["environment", "metallicity", "starburst"],
        "observable": "Stellar IMF slope in starburst vs. quiescent star-forming regions",
        "parameter_regime": {"SFR": ">10 Msun/yr (starburst) vs. <1 Msun/yr (normal)"},
        "prediction_a": "IMF slope = -2.35 universally",
        "prediction_b": "IMF flatter (top-heavy) in starbursts or metal-poor environments",
        "domain": "nir_spectroscopy",
        "precision": "IMF slope to ±0.15 dex; requires resolved stellar populations or spectral fitting",
        "time_estimate": "~30 hr JWST/NIRSpec per region × 3 regions",
    },
    {
        "keywords_a": ["kennicutt", "schmidt", "total gas"],
        "keywords_b": ["molecular", "h2", "co", "dense"],
        "observable": "KS relation using total HI+H₂ vs. CO-traced H₂ separately",
        "parameter_regime": {"Σ_gas": "1–1000 Msun/pc²", "galaxy_type": "spiral and dwarf"},
        "prediction_a": "KS index ≈ 1.4 with total gas",
        "prediction_b": "KS index ≈ 1.0 with molecular gas only; HI does not correlate",
        "domain": "molecular_lines",
        "precision": "Σ_SFR to 20%; CO-to-H₂ conversion factor uncertainty <30%",
        "time_estimate": "~50 hr VLA (HI) + ~40 hr ALMA (CO) per galaxy sample",
    },
    {
        "keywords_a": ["virial", "bound", "self-gravitating"],
        "keywords_b": ["pressure-confined", "unbound", "transient"],
        "observable": "Virial parameter α_vir = 2σ²R/GM as function of cloud size",
        "parameter_regime": {"size": "0.1–100 pc", "environment": "field and galactic centre"},
        "prediction_a": "α_vir ~ 1–2 for all clouds (gravitationally bound)",
        "prediction_b": "α_vir > 2 for small/diffuse clouds; external pressure confinement",
        "domain": "molecular_lines",
        "precision": "Cloud mass to 30%; linewidth to <0.2 km/s; size to 20%",
        "time_estimate": "~60 hr IRAM 30m mapping + ~20 hr ALMA resolution check",
    },
    {
        "keywords_a": ["magnetic", "field", "flux-freezing"],
        "keywords_b": ["turbulence", "ambipolar", "drift"],
        "observable": "Mass-to-flux ratio M/Φ vs. evolutionary stage of dense cores",
        "parameter_regime": {"density": ">10⁴ cm⁻³", "stage": "prestellar → protostellar"},
        "prediction_a": "M/Φ sub-critical initially; slow magnetic diffusion drives collapse",
        "prediction_b": "M/Φ super-critical from outset; turbulence, not B-field, regulates collapse",
        "domain": "polarimetry",
        "precision": "B-field strength to 30% via Davis–Chandrasekhar–Fermi; mass to 20%",
        "time_estimate": "~25 hr JCMT/POL-2 + ~15 hr ALMA/PolCal per region",
    },
    {
        "keywords_a": ["triggered", "sequential", "external pressure"],
        "keywords_b": ["spontaneous", "stochastic", "self-regulated"],
        "observable": "Age gradient of young stellar objects (YSOs) relative to ionisation front",
        "parameter_regime": {"distance": "<3 kpc", "hii_region": "RMS luminosity >10³ Lsun"},
        "prediction_a": "Systematic age gradient: youngest YSOs closest to ionisation front",
        "prediction_b": "No systematic age gradient; YSO ages randomly distributed",
        "domain": "nir_spectroscopy",
        "precision": "YSO age to 0.5 Myr accuracy; spatial resolution <0.1 pc at target distance",
        "time_estimate": "~40 hr Spitzer/IRAC archival + ~20 hr JWST/NIRCam new imaging",
    },
    {
        "keywords_a": ["hubble tension", "h0", "expansion rate"],
        "keywords_b": ["standard candle", "cepheid", "distance ladder"],
        "observable": "Independent H₀ measurement via gravitational wave standard sirens",
        "parameter_regime": {"z": "0.01–0.5", "event_type": "BNS merger + EM counterpart"},
        "prediction_a": "H₀ ≈ 73 km/s/Mpc (distance-ladder value)",
        "prediction_b": "H₀ ≈ 67 km/s/Mpc (CMB Planck value)",
        "domain": "gravitational_waves",
        "precision": "H₀ to 2% accuracy requires ~50 well-localised BNS events",
        "time_estimate": "~5 years LIGO O5 operations",
    },
    {
        "keywords_a": ["star formation efficiency", "feedback", "outflow"],
        "keywords_b": ["gravity", "collapse", "efficiency"],
        "observable": "Ratio of stellar to gas mass in embedded clusters vs. age",
        "parameter_regime": {"age": "<3 Myr", "mass": "10²–10⁴ Msun"},
        "prediction_a": "SFE rises then saturates as feedback disperses gas",
        "prediction_b": "SFE follows free-fall efficiency; no feedback signature",
        "domain": "submm_fir",
        "precision": "Stellar mass to 20% (near-IR photometry); gas mass to 30% (dust continuum)",
        "time_estimate": "~15 hr JWST + ~10 hr ALMA per cluster",
    },
]


# ---------------------------------------------------------------------------
# Designer
# ---------------------------------------------------------------------------

class ExperimentDesigner:
    """
    Designs critical experiments to discriminate between competing theories.
    """

    INSTRUMENTS = INSTRUMENTS

    # ------------------------------------------------------------------
    def design_critical_experiment(
        self,
        theory_a,
        theory_b,
    ) -> CriticalExperiment:
        """
        Design the best discriminating observation between theory_a and theory_b.

        Parameters
        ----------
        theory_a, theory_b : Theory | dict | Hypothesis
            Competing theories or hypotheses.

        Returns
        -------
        CriticalExperiment
        """
        id_a = self._get_id(theory_a)
        id_b = self._get_id(theory_b)
        text_a = self._get_text(theory_a)
        text_b = self._get_text(theory_b)
        combined = (text_a + " " + text_b).lower()

        # Try knowledge base match first
        best_kb = self._kb_lookup(combined)
        if best_kb:
            kb = best_kb
            domain = kb.get("domain", "submm_fir")
            instruments = self._instruments_for_domain(domain)
            feasibility, feas_weight = self._assess_feasibility(instruments, kb.get("precision", ""))
            divergence = self._estimate_divergence(kb["prediction_a"], kb["prediction_b"])
            return CriticalExperiment(
                id=f"EXP-{uuid.uuid4().hex[:8].upper()}",
                theory_a_id=id_a,
                theory_b_id=id_b,
                discriminating_observable=kb["observable"],
                parameter_regime=kb.get("parameter_regime", {}),
                predicted_value_a=kb["prediction_a"],
                predicted_value_b=kb["prediction_b"],
                divergence_magnitude=divergence,
                feasibility=feasibility,
                required_precision=kb.get("precision", "Moderate precision required"),
                suggested_instruments=instruments,
                estimated_observing_time=kb.get("time_estimate", "TBD"),
                scientific_value=round(divergence * feas_weight, 3),
                generated_at=time.time(),
            )

        # Fallback: generic discriminating design
        return self._generic_experiment(id_a, id_b, text_a, text_b, combined)

    # ------------------------------------------------------------------
    def design_from_contradiction(self, contradiction) -> CriticalExperiment:
        """
        Design a critical experiment from a Contradiction object (or dict).

        Parameters
        ----------
        contradiction : Contradiction | dict
            Object with .hypothesis_a_id, .hypothesis_b_id, .description or similar.
        """
        if hasattr(contradiction, "hypothesis_a_id"):
            id_a = contradiction.hypothesis_a_id
            id_b = contradiction.hypothesis_b_id
            description = getattr(contradiction, "description", "")
        elif isinstance(contradiction, dict):
            id_a = contradiction.get("hypothesis_a_id", contradiction.get("theory_a_id", "A"))
            id_b = contradiction.get("hypothesis_b_id", contradiction.get("theory_b_id", "B"))
            description = contradiction.get("description", "")
        else:
            id_a, id_b, description = "A", "B", str(contradiction)

        # Build minimal proxy objects from description
        proxy_a = {"id": id_a, "description": description}
        proxy_b = {"id": id_b, "description": description}
        return self.design_critical_experiment(proxy_a, proxy_b)

    # ------------------------------------------------------------------
    def prioritised_experiment_list(
        self,
        all_contradictions,
        all_theories,
    ) -> List[CriticalExperiment]:
        """
        Generate and rank a prioritised list of critical experiments from all
        known contradictions and theory pairs.

        Parameters
        ----------
        all_contradictions : list
            List of Contradiction objects or dicts.
        all_theories : list
            List of Theory objects or dicts (competing pairs identified automatically).

        Returns
        -------
        List[CriticalExperiment] sorted by scientific_value descending.
        """
        experiments: List[CriticalExperiment] = []

        # From contradictions
        for contradiction in (all_contradictions or []):
            try:
                exp = self.design_from_contradiction(contradiction)
                experiments.append(exp)
            except Exception:
                pass

        # From competing theory pairs
        theories = list(all_theories or [])
        for i, ta in enumerate(theories):
            competing_ids = []
            if hasattr(ta, "competing_theory_ids"):
                competing_ids = ta.competing_theory_ids or []
            elif isinstance(ta, dict):
                competing_ids = ta.get("competing_theory_ids", [])

            for j, tb in enumerate(theories):
                if i >= j:
                    continue
                tb_id = self._get_id(tb)
                if tb_id in competing_ids or not competing_ids:
                    try:
                        exp = self.design_critical_experiment(ta, tb)
                        experiments.append(exp)
                    except Exception:
                        pass

        # De-duplicate by observable text similarity and sort
        seen: set = set()
        unique: List[CriticalExperiment] = []
        for e in experiments:
            key = e.discriminating_observable[:60]
            if key not in seen:
                seen.add(key)
                unique.append(e)

        unique.sort(key=lambda e: e.scientific_value, reverse=True)
        return unique

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _get_id(obj) -> str:
        if hasattr(obj, "id"):
            return obj.id
        if isinstance(obj, dict):
            return obj.get("id", "unknown")
        return "unknown"

    @staticmethod
    def _get_text(obj) -> str:
        """Extract full textual content from a theory/hypothesis object."""
        parts = []
        for attr in ["name", "description", "axioms", "derived_predictions",
                     "mathematical_core", "domain"]:
            val = getattr(obj, attr, None) if hasattr(obj, attr) else (
                obj.get(attr) if isinstance(obj, dict) else None
            )
            if val:
                if isinstance(val, list):
                    parts.extend(str(v) for v in val)
                else:
                    parts.append(str(val))
        return " ".join(parts)

    def _kb_lookup(self, combined_text: str) -> Optional[Dict]:
        """Find the best matching KB entry for the combined theory texts."""
        best: Optional[Dict] = None
        best_score = 0
        for entry in _DISCRIMINATION_KB:
            kw_a = entry.get("keywords_a", [])
            kw_b = entry.get("keywords_b", [])
            score = sum(1 for kw in kw_a + kw_b if kw.lower() in combined_text)
            if score > best_score:
                best_score = score
                best = entry
        return best if best_score >= 1 else None

    def _instruments_for_domain(self, domain: str) -> List[str]:
        return INSTRUMENTS.get(domain, ["ALMA", "VLA", "JWST/NIRCam"])[:4]

    def _assess_feasibility(
        self, instruments: List[str], precision_text: str
    ) -> Tuple[str, float]:
        """
        Returns (feasibility_label, weight).
        weight: current=1.0, near_future=0.6, speculative=0.3
        """
        if not instruments:
            return ("speculative", 0.3)
        n_current = sum(1 for inst in instruments if inst in _CURRENT_INSTRUMENTS)
        n_future = sum(1 for inst in instruments if inst in _NEAR_FUTURE_INSTRUMENTS)
        if n_current > 0:
            return ("current_technology", 1.0)
        if n_future > 0:
            return ("near_future", 0.6)
        return ("speculative", 0.3)

    @staticmethod
    def _estimate_divergence(pred_a: str, pred_b: str) -> float:
        """
        Heuristic divergence from text: look for numeric differences or
        categorical opposites.
        """
        # Look for explicit numeric values
        nums_a = re.findall(r"[-+]?\d+\.?\d*", pred_a)
        nums_b = re.findall(r"[-+]?\d+\.?\d*", pred_b)
        if nums_a and nums_b:
            try:
                va = float(nums_a[0])
                vb = float(nums_b[0])
                if va != 0 and vb != 0:
                    ratio = abs(va - vb) / max(abs(va), abs(vb))
                    return min(1.0, ratio)
            except ValueError:
                pass
        # Categorical divergence
        opposites = [("universal", "environment"), ("bound", "unbound"),
                     ("thermal", "turbulent"), ("gradient", "random"),
                     ("increases", "decreases"), ("higher", "lower")]
        for (w1, w2) in opposites:
            if w1 in pred_a.lower() and w2 in pred_b.lower():
                return 0.85
            if w2 in pred_a.lower() and w1 in pred_b.lower():
                return 0.85
        return 0.60  # default moderate divergence

    def _generic_experiment(
        self, id_a: str, id_b: str, text_a: str, text_b: str, combined: str
    ) -> CriticalExperiment:
        """Fallback generic experiment when KB has no specific match."""
        # Choose domain from text
        domain = "submm_fir"
        for kws, domains in _OBSERVABLE_DOMAIN_MAP:
            if any(kw in combined for kw in kws):
                domain = domains[0]
                break

        instruments = self._instruments_for_domain(domain)
        feasibility, feas_weight = self._assess_feasibility(instruments, "")
        divergence = 0.60

        return CriticalExperiment(
            id=f"EXP-{uuid.uuid4().hex[:8].upper()}",
            theory_a_id=id_a,
            theory_b_id=id_b,
            discriminating_observable=(
                "Key observable distinguishing the two theories in their domain of overlap"
            ),
            parameter_regime={"regime": "intermediate — where predictions diverge most"},
            predicted_value_a="Consistent with standard model predictions",
            predicted_value_b="Requires modified physics or new physical process",
            divergence_magnitude=divergence,
            feasibility=feasibility,
            required_precision="High precision required to discriminate at 3σ",
            suggested_instruments=instruments,
            estimated_observing_time="10–50 hr depending on target brightness",
            scientific_value=round(divergence * feas_weight, 3),
            generated_at=time.time(),
        )
