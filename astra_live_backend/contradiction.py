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
ASTRA Live — Contradiction Detector
Scans the hypothesis store for mutual inconsistencies and physical law
violations, categorising them by type and severity, and proposing
theoretical resolutions.

Contradiction types detected
-----------------------------
1. directional   — Two hypotheses making opposite directional claims about
                   the same variable pair in the same domain.
2. conservation  — A hypothesis that would violate a fundamental conservation
                   law (energy, momentum, baryon number, entropy, causality).
3. dimensional   — Hypotheses whose claimed scaling relations are
                   dimensionally incompatible with each other.
4. statistical   — Two hypotheses validated to >0.7 confidence that imply
                   incompatible predictions for the same observable.

As described in White & Dey (2026), Section 3.2: Contradiction Resolution.
"""
import time
import re
import uuid
from dataclasses import dataclass, field
from typing import List, Optional, Dict

# ---------------------------------------------------------------------------
# Contradiction data structure
# ---------------------------------------------------------------------------

@dataclass
class Contradiction:
    """A detected logical or physical inconsistency between hypotheses."""
    id: str
    hypothesis_ids: List[str]
    contradiction_type: str        # "directional", "conservation", "dimensional", "statistical"
    description: str
    severity: str                  # "critical", "major", "minor"
    resolution_proposals: List[str]
    detected_at: float
    resolved: bool = False
    resolution_note: str = ""

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "hypothesis_ids": self.hypothesis_ids,
            "contradiction_type": self.contradiction_type,
            "description": self.description,
            "severity": self.severity,
            "resolution_proposals": self.resolution_proposals,
            "detected_at": self.detected_at,
            "resolved": self.resolved,
            "resolution_note": self.resolution_note,
        }


# ---------------------------------------------------------------------------
# Conservation law signatures
# ---------------------------------------------------------------------------

# Keywords in hypothesis descriptions that suggest energy creation/destruction
_ENERGY_VIOLATION_PATTERNS = [
    r"creat\w* energy",
    r"energy.*without.*source",
    r"perpetual",
    r"free energy.*machine",
    r"over.?unity",
    r"energy.*gain.*vacuum",
]

_MOMENTUM_VIOLATION_PATTERNS = [
    r"net momentum.*without.*force",
    r"reactionless",
    r"em.?drive.*net.*thrust.*closed",
]

_BARYON_VIOLATION_PATTERNS = [
    r"baryon.*creat\w*.*spontan",
    r"proton.*decay.*product.*baryon.*number.*non.?conserv",
]

_ENTROPY_VIOLATION_PATTERNS = [
    r"decreas\w* entropy.*isolated",
    r"entropy.*reversed.*closed",
    r"second law.*violated",
    r"maxwell.*demon.*net.*work",
]

_CAUSALITY_VIOLATION_PATTERNS = [
    r"faster.than.light.*signal",
    r"ftl.*information",
    r"superluminal.*causal",
    r"retro.*causal.*signal",
]

CONSERVATION_CHECKS = [
    ("energy",      _ENERGY_VIOLATION_PATTERNS,    "critical",
     "Energy conservation violation",
     [
         "Reformulate within thermodynamic framework (1st law)",
         "Identify hidden energy reservoir or dissipation channel",
         "Re-examine boundary conditions — system may not be closed",
     ]),
    ("momentum",    _MOMENTUM_VIOLATION_PATTERNS,  "critical",
     "Momentum conservation violation",
     [
         "Identify missing reaction force or radiated momentum",
         "Check if system is truly isolated (no external field gradients)",
         "Apply Newton's 3rd law rigorously to all subsystems",
     ]),
    ("baryon",      _BARYON_VIOLATION_PATTERNS,    "critical",
     "Baryon number conservation violation",
     [
         "Consider BSM physics only if GUT-scale energies are involved",
         "Re-examine reaction products for overlooked baryons/anti-baryons",
         "Verify this is not a known SM process with apparent mismatch",
     ]),
    ("entropy",     _ENTROPY_VIOLATION_PATTERNS,   "critical",
     "Second law of thermodynamics violation",
     [
         "Identify overlooked entropy increase elsewhere in the system",
         "Invoke Maxwell's demon critique — information storage costs entropy",
         "Restate as local entropy decrease compensated by global increase",
     ]),
    ("causality",   _CAUSALITY_VIOLATION_PATTERNS, "critical",
     "Causality / FTL signalling violation",
     [
         "Distinguish phase velocity (superluminal allowed) from group/signal velocity",
         "Check whether effect transmits usable information vs. mere correlation",
         "Revisit SR/GR frame transformation — coordinate speed ≠ signal speed",
     ]),
]

# ---------------------------------------------------------------------------
# Directional claim patterns
# ---------------------------------------------------------------------------

# Looks for "X increases/decreases with Y" or "X ∝ Y^(+/-)" style claims
_INCREASE_PATTERNS = [
    r"(\w[\w\s]*?)\s+increases?\s+with\s+([\w\s]+)",
    r"(\w[\w\s]*?)\s+positively\s+correlates?\s+with\s+([\w\s]+)",
    r"(\w[\w\s]*?)\s+scales?\s+as\s+([\w\s]+)\^[+]?[0-9]",
]

_DECREASE_PATTERNS = [
    r"(\w[\w\s]*?)\s+decreases?\s+with\s+([\w\s]+)",
    r"(\w[\w\s]*?)\s+negatively\s+correlates?\s+with\s+([\w\s]+)",
    r"(\w[\w\s]*?)\s+anti.?correlates?\s+with\s+([\w\s]+)",
    r"(\w[\w\s]*?)\s+scales?\s+as\s+([\w\s]+)\^-[0-9]",
]


def _extract_directional_claims(text: str) -> List[Dict]:
    """Extract directional claims (increase/decrease) from hypothesis text."""
    claims = []
    text_lower = text.lower()
    for pat in _INCREASE_PATTERNS:
        for m in re.finditer(pat, text_lower):
            claims.append({
                "direction": "increase",
                "y": m.group(1).strip()[:30],
                "x": m.group(2).strip()[:30],
            })
    for pat in _DECREASE_PATTERNS:
        for m in re.finditer(pat, text_lower):
            claims.append({
                "direction": "decrease",
                "y": m.group(1).strip()[:30],
                "x": m.group(2).strip()[:30],
            })
    return claims


def _claims_contradict(a: Dict, b: Dict) -> bool:
    """Return True if two directional claims conflict on the same (x, y) pair."""
    # Normalise variable names: strip short noise words
    def _norm(s: str) -> str:
        return re.sub(r'\b(the|a|an|its|their|of|in)\b', '', s).strip()

    ax, ay = _norm(a["x"]), _norm(a["y"])
    bx, by = _norm(b["x"]), _norm(b["y"])
    same_pair = (
        (ax and bx and (ax in bx or bx in ax)) and
        (ay and by and (ay in by or by in ay))
    )
    opposite_direction = a["direction"] != b["direction"]
    return same_pair and opposite_direction


# ---------------------------------------------------------------------------
# Scaling exponent sign extraction
# ---------------------------------------------------------------------------

def _extract_scaling_exponents(text: str) -> List[Dict]:
    """Extract claimed exponents from hypothesis descriptions."""
    results = []
    # Match patterns like "scales as X^0.33" or "∝ M^{-1/2}" or "∝ R^2"
    patterns = [
        r"(\w[\w\s]*?)\s*[∝~]\s*([\w_]+)\^([+-]?[0-9./]+)",
        r"(\w[\w\s]*?)\s+scales?\s+as\s+([\w_]+)\^([+-]?[0-9./]+)",
        r"exponent\s+of\s+([+-]?[0-9./]+)\s+for\s+([\w\s]+)\s+vs\s+([\w\s]+)",
    ]
    text_lower = text.lower()
    for pat in patterns:
        for m in re.finditer(pat, text_lower):
            try:
                exp_str = m.group(3) if len(m.groups()) == 3 else m.group(1)
                # Handle fractions like "1/2"
                if '/' in exp_str:
                    num, den = exp_str.split('/', 1)
                    exp = float(num) / float(den)
                else:
                    exp = float(exp_str)
                results.append({
                    "y_var": m.group(1).strip()[:30],
                    "x_var": m.group(2).strip()[:30],
                    "exponent": exp,
                })
            except (ValueError, IndexError):
                continue
    return results


# ---------------------------------------------------------------------------
# ContradictionDetector
# ---------------------------------------------------------------------------

class ContradictionDetector:
    """
    Scans a HypothesisStore for logical and physical contradictions.

    Usage
    -----
    detector = ContradictionDetector()
    contradictions = detector.scan(hypothesis_store)
    """

    def __init__(self):
        self._contradictions: Dict[str, Contradiction] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def scan(self, hypothesis_store) -> List[Contradiction]:
        """
        Full scan of hypothesis_store for all contradiction types.

        Parameters
        ----------
        hypothesis_store : HypothesisStore
            The live hypothesis store to scan.

        Returns
        -------
        List[Contradiction]
            Newly detected contradictions (may include previously seen ones
            if still unresolved). The internal store is updated in place.
        """
        hypotheses = hypothesis_store.all()
        new_contradictions: List[Contradiction] = []

        new_contradictions.extend(self._scan_directional(hypotheses))
        new_contradictions.extend(self._scan_conservation(hypotheses))
        new_contradictions.extend(self._scan_dimensional(hypotheses))
        new_contradictions.extend(self._scan_statistical(hypotheses))

        for c in new_contradictions:
            self._contradictions[c.id] = c

        return new_contradictions

    def get_all(self) -> List[Contradiction]:
        """Return all detected contradictions (resolved and unresolved)."""
        return list(self._contradictions.values())

    def get_unresolved(self) -> List[Contradiction]:
        """Return only unresolved contradictions."""
        return [c for c in self._contradictions.values() if not c.resolved]

    def mark_resolved(self, cid: str, note: str = "") -> bool:
        """
        Mark a contradiction as resolved.

        Parameters
        ----------
        cid : str
            Contradiction ID to resolve.
        note : str
            Optional resolution explanation.

        Returns True if found and resolved, False if not found.
        """
        c = self._contradictions.get(cid)
        if c is not None:
            c.resolved = True
            c.resolution_note = note
            return True
        return False

    def to_dict(self) -> List[Dict]:
        return [c.to_dict() for c in self._contradictions.values()]

    # ------------------------------------------------------------------
    # Scan methods
    # ------------------------------------------------------------------

    def _scan_directional(self, hypotheses) -> List[Contradiction]:
        """Detect pairs of hypotheses with opposite directional claims."""
        found = []
        # Build index of claims per hypothesis
        claim_map = {}
        for h in hypotheses:
            text = getattr(h, 'description', '') or getattr(h, 'name', '')
            claims = _extract_directional_claims(text)
            if claims:
                claim_map[h.id] = (h, claims)

        ids = list(claim_map.keys())
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                h1, claims1 = claim_map[ids[i]]
                h2, claims2 = claim_map[ids[j]]
                for c1 in claims1:
                    for c2 in claims2:
                        if _claims_contradict(c1, c2):
                            key = f"DIR_{h1.id}_{h2.id}_{c1['x'][:8]}_{c1['y'][:8]}"
                            if key in self._contradictions:
                                continue  # already registered
                            found.append(Contradiction(
                                id=key,
                                hypothesis_ids=[h1.id, h2.id],
                                contradiction_type="directional",
                                description=(
                                    f"{h1.id} claims '{c1['y']}' {c1['direction']}s with "
                                    f"'{c1['x']}', but {h2.id} claims it {c2['direction']}s."
                                ),
                                severity="major",
                                resolution_proposals=[
                                    "Determine whether the relationship is non-monotonic "
                                    "(e.g., peaks at intermediate values); both claims may "
                                    "hold in different regimes.",
                                    "Check whether the two hypotheses operate in different "
                                    "parameter regimes — the apparent contradiction may be "
                                    "a domain boundary effect.",
                                    "Perform a controlled test holding confounding variables "
                                    "fixed to isolate the true direction of causality.",
                                ],
                                detected_at=time.time(),
                            ))
        return found

    def _scan_conservation(self, hypotheses) -> List[Contradiction]:
        """Flag hypotheses whose descriptions imply conservation law violations."""
        found = []
        for h in hypotheses:
            text = (getattr(h, 'description', '') or '') + ' ' + (getattr(h, 'name', '') or '')
            text_lower = text.lower()
            for law, patterns, severity, label, resolutions in CONSERVATION_CHECKS:
                for pat in patterns:
                    if re.search(pat, text_lower):
                        key = f"CONS_{law.upper()}_{h.id}"
                        if key in self._contradictions:
                            break
                        found.append(Contradiction(
                            id=key,
                            hypothesis_ids=[h.id],
                            contradiction_type="conservation",
                            description=(
                                f"{h.id} appears to imply a {label} "
                                f"(matched pattern: '{pat}')."
                            ),
                            severity=severity,
                            resolution_proposals=list(resolutions),
                            detected_at=time.time(),
                        ))
                        break  # one violation per law per hypothesis is enough
        return found

    def _scan_dimensional(self, hypotheses) -> List[Contradiction]:
        """Detect hypotheses with incompatible scaling exponents for the same variable pair."""
        found = []
        # Group scaling claims by (y_var, x_var) key
        from collections import defaultdict
        claim_index = defaultdict(list)  # key → [(hyp_id, exponent), ...]

        for h in hypotheses:
            text = (getattr(h, 'description', '') or '') + ' ' + (getattr(h, 'name', '') or '')
            for claim in _extract_scaling_exponents(text):
                pair_key = (claim['y_var'][:20], claim['x_var'][:20])
                claim_index[pair_key].append((h.id, claim['exponent']))

        for (y_var, x_var), entries in claim_index.items():
            if len(entries) < 2:
                continue
            for i in range(len(entries)):
                for j in range(i + 1, len(entries)):
                    hid1, exp1 = entries[i]
                    hid2, exp2 = entries[j]
                    # Flag if exponents differ by more than 0.5 and have opposite signs
                    sign_conflict = (exp1 * exp2 < 0)  # opposite signs
                    large_diff = abs(exp1 - exp2) > 0.5
                    if sign_conflict or large_diff:
                        key = f"DIM_{hid1}_{hid2}_{y_var[:8]}_{x_var[:8]}"
                        if key in self._contradictions:
                            continue
                        severity = "major" if sign_conflict else "minor"
                        found.append(Contradiction(
                            id=key,
                            hypothesis_ids=[hid1, hid2],
                            contradiction_type="dimensional",
                            description=(
                                f"{hid1} claims {y_var} ∝ {x_var}^{exp1:.3f} "
                                f"but {hid2} claims {y_var} ∝ {x_var}^{exp2:.3f} "
                                f"(Δα = {abs(exp1-exp2):.3f}"
                                + (", opposite signs)" if sign_conflict else ")")
                            ),
                            severity=severity,
                            resolution_proposals=[
                                "Apply Buckingham π theorem to both hypotheses to check "
                                "whether the claimed exponents are dimensionally permitted.",
                                "Test whether both exponents are self-consistent in separate "
                                "regimes (e.g., low- vs. high-mass, laminar vs. turbulent).",
                                "Perform a joint fit allowing a broken power-law to reconcile "
                                "both exponents as regime-specific asymptotes.",
                            ],
                            detected_at=time.time(),
                        ))
        return found

    def _scan_statistical(self, hypotheses) -> List[Contradiction]:
        """
        Detect high-confidence hypotheses (>0.7) that share a common
        observable keyword but imply inconsistent quantitative outcomes.
        This is a lightweight proxy for a full prediction-consistency check.
        """
        found = []
        high_conf = [h for h in hypotheses if getattr(h, 'confidence', 0) > 0.7]

        if len(high_conf) < 2:
            return found

        # Group by domain
        from collections import defaultdict
        domain_groups = defaultdict(list)
        for h in high_conf:
            domain_groups[getattr(h, 'domain', 'Unknown')].append(h)

        for domain, group in domain_groups.items():
            for i in range(len(group)):
                for j in range(i + 1, len(group)):
                    h1, h2 = group[i], group[j]
                    t1 = (getattr(h1, 'description', '') + ' ' + getattr(h1, 'name', '')).lower()
                    t2 = (getattr(h2, 'description', '') + ' ' + getattr(h2, 'name', '')).lower()
                    # Check if they share key observable words AND make contradictory claims
                    shared_obs = _shared_observable(t1, t2)
                    if shared_obs and _texts_statistically_contradict(t1, t2):
                        key = f"STAT_{h1.id}_{h2.id}_{shared_obs[:10]}"
                        if key in self._contradictions:
                            continue
                        found.append(Contradiction(
                            id=key,
                            hypothesis_ids=[h1.id, h2.id],
                            contradiction_type="statistical",
                            description=(
                                f"Both {h1.id} (conf={h1.confidence:.2f}) and "
                                f"{h2.id} (conf={h2.confidence:.2f}) are high-confidence "
                                f"in domain '{domain}' and make conflicting claims "
                                f"regarding '{shared_obs}'."
                            ),
                            severity="major",
                            resolution_proposals=[
                                "Run a direct comparative statistical test on the shared "
                                "observable using the same dataset to determine which "
                                "hypothesis better predicts the data.",
                                "Check whether the two hypotheses are modelling different "
                                "sub-populations within the same domain — apparent conflict "
                                "may dissolve with proper sample stratification.",
                                "Lower confidence of the weaker hypothesis by applying a "
                                "Bayesian update with the other as prior; promote the "
                                "survivor for further testing.",
                            ],
                            detected_at=time.time(),
                        ))
        return found


# ---------------------------------------------------------------------------
# Helpers for statistical scan
# ---------------------------------------------------------------------------

_POSITIVE_CLAIM_WORDS = {
    "increases", "grows", "expands", "accelerates", "rises", "correlation",
    "positive", "higher", "greater", "larger", "excess", "surplus",
}

_NEGATIVE_CLAIM_WORDS = {
    "decreases", "shrinks", "contracts", "decelerates", "falls", "anti-correlation",
    "negative", "lower", "smaller", "deficit", "depletion",
}

_OBSERVABLE_KEYWORDS = {
    "luminosity", "mass", "temperature", "radius", "velocity", "redshift",
    "density", "pressure", "entropy", "energy", "flux", "distance",
    "age", "metallicity", "star formation", "accretion", "feedback",
    "h0", "hubble", "dark energy", "dark matter", "inflation",
    "gdp", "income", "mortality", "life expectancy",
}


def _shared_observable(t1: str, t2: str) -> Optional[str]:
    """Return the first shared observable keyword found in both texts."""
    for kw in _OBSERVABLE_KEYWORDS:
        if kw in t1 and kw in t2:
            return kw
    return None


def _texts_statistically_contradict(t1: str, t2: str) -> bool:
    """
    Lightweight heuristic: texts contradict if one contains positive-claim words
    and the other negative-claim words for the same observable.
    """
    pos1 = bool(_POSITIVE_CLAIM_WORDS & set(t1.split()))
    neg1 = bool(_NEGATIVE_CLAIM_WORDS & set(t1.split()))
    pos2 = bool(_POSITIVE_CLAIM_WORDS & set(t2.split()))
    neg2 = bool(_NEGATIVE_CLAIM_WORDS & set(t2.split()))

    # Contradict if one is predominantly positive and the other predominantly negative
    return (pos1 and not neg1 and neg2 and not pos2) or \
           (neg1 and not pos1 and pos2 and not neg2)
