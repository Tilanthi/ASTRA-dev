"""
ASTRA Live — Analogy Engine
Detects cross-domain structural isomorphisms between validated hypotheses
and generates theoretical unification proposals.

Phase 2 of the ASTRA theoretical framework infrastructure.
As described in White & Dey (2026), Section 5 (Theory Synthesis).
"""
import re
import time
import uuid
import math
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple

try:
    from .theory import Theory  # noqa: F401
except ImportError:
    pass  # theory.py may be written in parallel; not required here


# ─── Dataclass ────────────────────────────────────────────────────────────────

@dataclass
class Analogy:
    id: str
    domain_a: str
    domain_b: str
    hypothesis_id_a: str
    hypothesis_id_b: str
    mathematical_form: str          # The shared mathematical structure
    structural_similarity: float    # 0–1
    unification_proposal: str       # Theoretical statement unifying both
    novel: bool                     # Not in known analogies library
    detected_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "domain_a": self.domain_a,
            "domain_b": self.domain_b,
            "hypothesis_id_a": self.hypothesis_id_a,
            "hypothesis_id_b": self.hypothesis_id_b,
            "mathematical_form": self.mathematical_form,
            "structural_similarity": self.structural_similarity,
            "unification_proposal": self.unification_proposal,
            "novel": self.novel,
            "detected_at": self.detected_at,
        }


# ─── Known cross-domain analogies (reference library) ────────────────────────

_KNOWN_ANALOGIES: List[Dict] = [
    {
        "label": "Gravity ↔ Electrostatics",
        "form": "power_law",
        "exponent": -2.0,
        "domains": {"Physics", "Electromagnetism"},
        "description": "Both obey an inverse-square 1/r² force law.",
    },
    {
        "label": "Thermodynamics ↔ Information Theory",
        "form": "linear",
        "exponent": 1.0,
        "domains": {"Thermodynamics", "Information Theory"},
        "description": "Boltzmann entropy S = k ln Ω is isomorphic to Shannon entropy.",
    },
    {
        "label": "Turbulence ↔ Galaxy Clustering",
        "form": "power_law",
        "exponent": -1.667,
        "domains": {"Fluid Dynamics", "Astrophysics", "Cosmology"},
        "description": "Kolmogorov 5/3 energy spectrum mirrors galaxy clustering power spectrum.",
    },
    {
        "label": "Random Walk ↔ Brownian Motion ↔ Stock Prices",
        "form": "power_law",
        "exponent": 0.5,
        "domains": {"Statistics", "Physics", "Economics"},
        "description": "Diffusive processes share σ ∝ t^0.5 scaling.",
    },
    {
        "label": "Diffusion ↔ Heat Conduction",
        "form": "power_law",
        "exponent": 0.5,
        "domains": {"Physics", "Chemistry"},
        "description": "Both governed by second-order parabolic PDE; root-mean-square displacement ∝ √t.",
    },
    {
        "label": "Neural Networks ↔ Statistical Mechanics",
        "form": "exponential",
        "exponent": 1.0,
        "domains": {"Computer Science", "Physics"},
        "description": "Boltzmann machines formally identical to Ising spin-glass energy function.",
    },
    {
        "label": "Population Growth ↔ Galaxy Star Formation",
        "form": "exponential",
        "exponent": 1.0,
        "domains": {"Biology", "Astrophysics"},
        "description": "Exponential growth in limiting-resource regime mirrors quenching-free SFR.",
    },
    {
        "label": "Predator-Prey ↔ Stellar Feedback Cycles",
        "form": "periodic",
        "exponent": 1.0,
        "domains": {"Biology", "Astrophysics"},
        "description": "Lotka-Volterra oscillations structurally analogous to star formation / ISM feedback cycles.",
    },
    {
        "label": "Fractal Coastline ↔ ISM Density Structure",
        "form": "power_law",
        "exponent": -1.5,
        "domains": {"Geometry", "Astrophysics"},
        "description": "Self-similar hierarchical structure with same fractal dimension ≈ 2.3–2.7.",
    },
    {
        "label": "Black-Body Radiation ↔ Cosmic Microwave Background",
        "form": "exponential",
        "exponent": 1.0,
        "domains": {"Thermodynamics", "Cosmology"},
        "description": "CMB spectrum is a perfect Planck black-body; analogous to laboratory thermal emission.",
    },
]


# ─── Mathematical fingerprinting helpers ─────────────────────────────────────

_FORM_PATTERNS = [
    ("power_law",   [r"power.law", r"scaling", r"exponent", r"α\s*=", r"β\s*=",
                     r"mass.radius", r"period.mass", r"luminosity.mass"]),
    ("exponential", [r"exponential", r"e-fold", r"exp\(", r"decay\s+time",
                     r"growth\s+rate"]),
    ("linear",      [r"linear\s+relation", r"linearly\s+correl", r"proportional",
                     r"slope\s*=", r"constant\s+fraction"]),
    ("bimodal",     [r"bimodal", r"two.peak", r"double.gaussian", r"red\s+sequence",
                     r"blue\s+cloud", r"bimodality"]),
    ("causal_chain",[r"causal", r"trigger", r"feedback", r"cascade",
                     r"drives\b", r"leads\s+to"]),
    ("periodic",    [r"period", r"oscillat", r"cycl", r"sinusoid"]),
    ("lognormal",   [r"log.normal", r"lognormal"]),
]


def _fingerprint_hypothesis(hypothesis) -> Dict:
    """
    Build a mathematical fingerprint dict for a single hypothesis.
    """
    desc = hypothesis.description.lower()

    # Form classification
    form = "unknown"
    for fname, patterns in _FORM_PATTERNS:
        if any(re.search(p, desc) for p in patterns):
            form = fname
            break

    # Crude exponent extraction — look for numeric values following α, β, ~, ≈, =
    exponent = None
    m = re.search(r"(?:exponent|α|β|index|slope)\s*[=≈~]\s*([-+]?\d+\.?\d*)", desc)
    if m:
        try:
            exponent = float(m.group(1))
        except ValueError:
            pass
    if exponent is None:
        # Default form exponents
        _defaults = {
            "power_law": 1.0, "exponential": 1.0, "linear": 1.0,
            "bimodal": 1.0, "causal_chain": 1.0, "periodic": 1.0,
            "lognormal": 1.0, "unknown": 1.0,
        }
        exponent = _defaults.get(form, 1.0)

    # Variable count — split on delimiters and count distinct capitalised tokens
    var_pattern = r"\b[A-Z][a-z]{0,3}\b|α|β|γ|σ|λ|ρ|ε|μ|ν"
    variables = len(set(re.findall(var_pattern, hypothesis.description)))
    variables = max(1, variables)

    # Causal
    causal = bool(re.search(r"causal|trigger|feedback|drives\b|leads\s+to", desc))

    # Correlation direction
    direction = "positive"
    if re.search(r"anti.correl|inverse|negat|decreas|reduc", desc):
        direction = "negative"

    return {
        "form": form,
        "exponent": exponent,
        "variables": variables,
        "domain": hypothesis.domain,
        "causal": causal,
        "direction": direction,
    }


def _structural_similarity(fp_a: Dict, fp_b: Dict) -> float:
    """
    Compute 0–1 structural similarity between two fingerprints.
    Returns ≥ 0.7 when the two hypotheses are considered analogous.
    """
    score = 0.0
    weights = 0.0

    # Form match (weight 0.4)
    w = 0.4
    if fp_a["form"] == fp_b["form"] and fp_a["form"] != "unknown":
        score += w
    elif fp_a["form"] == "unknown" or fp_b["form"] == "unknown":
        score += w * 0.3
    weights += w

    # Exponent within 15% (weight 0.3)
    w = 0.3
    if fp_a["exponent"] != 0 and fp_b["exponent"] != 0:
        rel_diff = abs(fp_a["exponent"] - fp_b["exponent"]) / max(
            abs(fp_a["exponent"]), abs(fp_b["exponent"]), 1e-9
        )
        if rel_diff <= 0.15:
            score += w
        elif rel_diff <= 0.30:
            score += w * 0.5
    weights += w

    # Same causal direction (weight 0.2)
    w = 0.2
    if fp_a["direction"] == fp_b["direction"]:
        score += w
    weights += w

    # Both causal or both non-causal (weight 0.1)
    w = 0.1
    if fp_a["causal"] == fp_b["causal"]:
        score += w
    weights += w

    return round(score / weights, 4) if weights > 0 else 0.0


def _is_known_analogy(domain_a: str, domain_b: str, form: str) -> bool:
    """Check whether this cross-domain pair is already catalogued."""
    domain_pair = {domain_a, domain_b}
    for known in _KNOWN_ANALOGIES:
        if (known["form"] == form
                and domain_pair & known["domains"]):
            return True
    return False


def _unification_proposal(fp_a: Dict, fp_b: Dict,
                           hyp_a, hyp_b) -> str:
    """Generate a natural-language theoretical unification statement."""
    form = fp_a["form"] if fp_a["form"] != "unknown" else fp_b["form"]
    _templates = {
        "power_law": (
            f"Both '{hyp_a.name}' ({hyp_a.domain}) and '{hyp_b.name}' ({hyp_b.domain}) "
            f"obey power-law scaling with exponent ≈ {(fp_a['exponent']+fp_b['exponent'])/2:.2f}. "
            f"A common underlying scale-free process may govern both systems — "
            f"candidate mechanisms include self-organised criticality or hierarchical fragmentation."
        ),
        "exponential": (
            f"The exponential {fp_a['direction']} trends in '{hyp_a.name}' and '{hyp_b.name}' "
            f"suggest a shared e-folding growth/decay mechanism. "
            f"Unification via a master rate equation coupling {hyp_a.domain} and {hyp_b.domain} "
            f"timescales is proposed."
        ),
        "linear": (
            f"The linear proportionality found independently in '{hyp_a.name}' ({hyp_a.domain}) "
            f"and '{hyp_b.name}' ({hyp_b.domain}) may reflect a universal conservation law "
            f"or energy budget argument valid across both domains."
        ),
        "bimodal": (
            f"Both '{hyp_a.name}' and '{hyp_b.name}' show bimodal distributions, "
            f"suggesting a phase-transition or threshold mechanism common to "
            f"{hyp_a.domain} and {hyp_b.domain}. "
            f"A unified bifurcation model is proposed."
        ),
        "causal_chain": (
            f"The causal cascade in '{hyp_a.name}' ({hyp_a.domain}) is structurally "
            f"isomorphic to that in '{hyp_b.name}' ({hyp_b.domain}). "
            f"A cross-domain dynamical systems model may encompass both."
        ),
        "periodic": (
            f"Oscillatory behaviour in '{hyp_a.name}' and '{hyp_b.name}' share "
            f"the same mathematical form, suggesting a resonance or limit-cycle "
            f"mechanism transferable between {hyp_a.domain} and {hyp_b.domain}."
        ),
    }
    return _templates.get(
        form,
        f"'{hyp_a.name}' ({hyp_a.domain}) and '{hyp_b.name}' ({hyp_b.domain}) share "
        f"structural form '{form}'. A unifying theoretical framework is warranted.",
    )


# ─── AnalogyEngine ────────────────────────────────────────────────────────────

class AnalogyEngine:
    """
    Scans the hypothesis store for cross-domain pairs that share mathematical
    structure, and proposes theoretical unification statements.
    """

    # Minimum structural similarity to flag as analogy
    SIMILARITY_THRESHOLD = 0.70

    def __init__(self):
        self._all_analogies: List[Analogy] = []

    # ── Public API ────────────────────────────────────────────────────────────

    def scan(self, hypothesis_store) -> List[Analogy]:
        """
        Full scan of hypothesis_store.  Returns all detected analogies
        (cross-domain structural isomorphisms).
        """
        try:
            from .hypotheses import Phase  # type: ignore[attr-defined]
            candidates = [
                h for h in hypothesis_store.all()
                if h.phase in (Phase.VALIDATED, Phase.PUBLISHED)
                or h.confidence >= 0.65
            ]
        except Exception:
            candidates = list(hypothesis_store.all())

        analogies: List[Analogy] = []
        seen_pairs: set = set()

        fingerprints = {h.id: _fingerprint_hypothesis(h) for h in candidates}

        for i, ha in enumerate(candidates):
            for j, hb in enumerate(candidates):
                if j <= i:
                    continue
                # Must be different domains for cross-domain analogy
                if ha.domain == hb.domain:
                    continue
                pair_key = tuple(sorted([ha.id, hb.id]))
                if pair_key in seen_pairs:
                    continue
                seen_pairs.add(pair_key)

                fp_a = fingerprints[ha.id]
                fp_b = fingerprints[hb.id]
                sim = _structural_similarity(fp_a, fp_b)

                if sim < self.SIMILARITY_THRESHOLD:
                    continue

                shared_form = fp_a["form"] if fp_a["form"] != "unknown" else fp_b["form"]
                novel = not _is_known_analogy(ha.domain, hb.domain, shared_form)

                analogy = Analogy(
                    id=f"AN-{uuid.uuid4().hex[:8].upper()}",
                    domain_a=ha.domain,
                    domain_b=hb.domain,
                    hypothesis_id_a=ha.id,
                    hypothesis_id_b=hb.id,
                    mathematical_form=shared_form,
                    structural_similarity=sim,
                    unification_proposal=_unification_proposal(fp_a, fp_b, ha, hb),
                    novel=novel,
                    detected_at=time.time(),
                )
                analogies.append(analogy)

        self._all_analogies = analogies
        return analogies

    def get_novel_analogies(self) -> List[Analogy]:
        """Return only analogies not present in the known reference library."""
        return [a for a in self._all_analogies if a.novel]

    def get_all_analogies(self) -> List[Analogy]:
        return list(self._all_analogies)

    def known_analogies_library(self) -> List[Dict]:
        """Expose the hardcoded reference library for inspection."""
        return list(_KNOWN_ANALOGIES)
