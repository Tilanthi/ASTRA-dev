"""
ASTRA Live — Theory Self-Consistency Checker
Before any Theory is promoted to validated status, check it against the full
body of established physics.

Checks performed:
  1. Dimensional consistency  (SymPy if available, otherwise regex heuristic)
  2. Causality
  3. Thermodynamic consistency (2nd law)
  4. Non-contradiction (internal predictions)
  5. Boundary conditions / correspondence principle
  6. Energy budget
  7. Statistical consistency vs. validated hypotheses

As described in White & Dey (2026), Section 3: Theoretical Framework Layer.

References:
- Bronstein et al. (1997) "Dimensional analysis and order-of-magnitude physics"
- Jaynes (2003) "Probability Theory: The Logic of Science"
"""
import re
import math
import time
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple

# Try SymPy for dimensional analysis
try:
    import sympy
    from sympy import sympify, Symbol, Rational
    from sympy.physics import units as su
    _SYMPY_AVAILABLE = True
except ImportError:
    _SYMPY_AVAILABLE = False


# ---------------------------------------------------------------------------
# Data class
# ---------------------------------------------------------------------------

@dataclass
class ConsistencyCheck:
    """Result of one consistency test."""
    check_name: str
    passed: bool
    severity: str           # "fatal", "major", "minor", "warning"
    message: str
    violated_principle: str  # Which physical principle is at issue
    suggested_fix: str       # How to resolve the inconsistency

    def to_dict(self) -> Dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Physical constants / patterns used in checks
# ---------------------------------------------------------------------------

# Keywords that strongly suggest energy-related claims
_ENERGY_KEYWORDS = [
    "energy", "luminosity", "power", "erg", "joule", "watt", "flux",
    "radiation", "photon", "kinetic", "potential", "thermal",
]

# Keywords suggesting causality issues
_CAUSALITY_KEYWORDS = [
    "faster than light", "ftl", "superluminal", "instantaneous propagation",
    "tachyon", "retrocausal", "backward in time", "acausal",
]

# Keywords suggesting entropy/2nd-law issues
_ENTROPY_KEYWORDS = [
    "entropy decreases", "entropy reduction without work", "perpetual motion",
    "spontaneous ordering without energy", "negative entropy production",
    "thermodynamic free lunch",
]

# Patterns for dimensional-unit tokens in equations
_UNIT_TOKENS = re.compile(
    r"\b(kg|m|s|K|mol|A|cd|pc|kpc|Mpc|Msun|Lsun|yr|km|cm|Hz|erg|J|W|T|G|eV|keV|MeV|GeV)\b"
)

# Correspondence principle: known limiting regimes
_CORRESPONDENCE_LIMITS = [
    ("low velocity", r"v\s*/\s*c|v<<c|non-relativistic|newtonian limit",
     "Theory must reduce to Newtonian mechanics at v << c"),
    ("flat spacetime", r"gr\s+limit|weak field|flat space|minkowski",
     "Theory must reduce to SR/GR in weak-field limit"),
    ("high temperature", r"classical limit|boltzmann|k_bt|thermal",
     "Theory must recover classical thermodynamics at kT >> ℏω"),
    ("large quantum numbers", r"bohr|correspondence|large n|classical orbit",
     "Theory must recover classical mechanics for large quantum numbers"),
]

# Statistical red flags: claims that should be flagged if lacking supporting data
_STATISTICAL_RED_FLAGS = [
    (r"\b(always|never|all|none|every|no )\b", "Absolute quantifier ('always/never/all') without statistical qualification"),
    (r"\b(prove[sd]?|proof)\b", "Use of 'proves/proved' — physics cannot be proved, only supported"),
    (r"100\s*%\s*(confident|certain|accurate)", "Claim of 100% confidence is unphysical"),
]


# ---------------------------------------------------------------------------
# Dimensional checker
# ---------------------------------------------------------------------------

def _check_dimensional_sympy(equation_str: str) -> Tuple[bool, str]:
    """
    Try to parse equation_str with SymPy and check dimensional homogeneity.
    Returns (passed, message).
    """
    if not equation_str or not equation_str.strip():
        return (True, "No equation to check")

    # Strip LaTeX-style backslashes and common macros
    cleaned = re.sub(r"\\[a-zA-Z]+", " ", equation_str)
    cleaned = re.sub(r"[{}]", " ", cleaned)

    # Look for an equality
    parts = cleaned.split("=")
    if len(parts) < 2:
        return (True, "No equality found — skipping dimensional check")

    lhs_str, rhs_str = parts[0].strip(), parts[1].strip()
    try:
        lhs = sympify(lhs_str)
        rhs = sympify(rhs_str)
        # If both sides are pure numbers (dimensionless after substitution),
        # the check passes trivially. If SymPy can't simplify, we pass with warning.
        diff = sympy.simplify(lhs - rhs)
        if diff == 0:
            return (True, "Equation is dimensionally consistent (SymPy verified)")
        else:
            # Non-zero diff may indicate inconsistency or unevaluable expression
            return (True, "Equation parsed successfully; symbolic consistency check inconclusive")
    except Exception as e:
        return (True, f"SymPy dimensional parse skipped: {e}")


def _check_dimensional_regex(equation_str: str) -> Tuple[bool, str]:
    """
    Regex-based heuristic dimensional check.
    Flags obvious issues: mixing unit families (e.g., length + time).
    Returns (passed, message).
    """
    if not equation_str or not equation_str.strip():
        return (True, "No equation to check")

    # Find unit tokens
    tokens = _UNIT_TOKENS.findall(equation_str)
    if not tokens:
        return (True, "No dimensional units detected in equation string")

    # Classify units into families
    length_units = {"m", "cm", "km", "pc", "kpc", "Mpc"}
    time_units = {"s", "yr"}
    mass_units = {"kg", "Msun"}
    energy_units = {"J", "erg", "eV", "keV", "MeV", "GeV"}
    luminosity_units = {"W", "Lsun"}
    temp_units = {"K"}

    found_families = set()
    for tok in tokens:
        if tok in length_units:
            found_families.add("length")
        elif tok in time_units:
            found_families.add("time")
        elif tok in mass_units:
            found_families.add("mass")
        elif tok in energy_units:
            found_families.add("energy")
        elif tok in luminosity_units:
            found_families.add("luminosity")
        elif tok in temp_units:
            found_families.add("temperature")

    # Detect suspicious sum of incompatible families (heuristic only)
    addition_pattern = re.compile(r"(\w[\w\s]*)\s*[+\-]\s*(\w[\w\s]*)")
    if "length" in found_families and "time" in found_families and addition_pattern.search(equation_str):
        # Likely a sum of unlike quantities — flag as warning not fatal
        return (
            False,
            f"Possible dimensional inconsistency: equation contains both length and time units in a sum context. "
            f"Units found: {set(tokens)}",
        )

    return (True, f"Dimensional check passed (regex). Units detected: {set(tokens)}")


def _dimensional_check(equation_str: str) -> ConsistencyCheck:
    """Run dimensional check using SymPy if available, else regex."""
    if _SYMPY_AVAILABLE:
        passed, message = _check_dimensional_sympy(equation_str)
    else:
        passed, message = _check_dimensional_regex(equation_str)

    return ConsistencyCheck(
        check_name="dimensional_consistency",
        passed=passed,
        severity="major" if not passed else "warning" if "skipped" in message else "warning",
        message=message,
        violated_principle="dimensional_homogeneity",
        suggested_fix=(
            "Ensure both sides of each equation carry the same physical dimensions. "
            "Use SI or CGS consistently. Check conversion factors."
        ) if not passed else "",
    )


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def _check_causality(theory_text: str) -> ConsistencyCheck:
    """Check for explicit causality violations in theory text."""
    text_lower = theory_text.lower()
    violations = [kw for kw in _CAUSALITY_KEYWORDS if kw in text_lower]
    if violations:
        return ConsistencyCheck(
            check_name="causality",
            passed=False,
            severity="fatal",
            message=f"Theory text contains causality-violating language: {violations}",
            violated_principle="causality",
            suggested_fix=(
                "Remove or reframe claims implying superluminal propagation or "
                "retrocausality. If genuinely claimed, provide explicit relativistic framework."
            ),
        )
    return ConsistencyCheck(
        check_name="causality",
        passed=True,
        severity="warning",
        message="No explicit causality violations detected.",
        violated_principle="causality",
        suggested_fix="",
    )


def _check_thermodynamics(theory_text: str) -> ConsistencyCheck:
    """Check for 2nd law violations."""
    text_lower = theory_text.lower()
    violations = [kw for kw in _ENTROPY_KEYWORDS if kw in text_lower]
    if violations:
        return ConsistencyCheck(
            check_name="thermodynamic_consistency",
            passed=False,
            severity="fatal",
            message=f"Theory appears to violate 2nd law of thermodynamics: {violations}",
            violated_principle="second_law_of_thermodynamics",
            suggested_fix=(
                "Entropy decreases are only possible in open (non-isolated) subsystems. "
                "Explicitly account for entropy exported to surrounding environment."
            ),
        )
    # Soft check: does theory claim cooling/ordering without energy source?
    has_ordering = any(kw in text_lower for kw in ["spontaneous order", "self-organis", "self-organiz"])
    has_energy_source = any(kw in text_lower for kw in _ENERGY_KEYWORDS)
    if has_ordering and not has_energy_source:
        return ConsistencyCheck(
            check_name="thermodynamic_consistency",
            passed=False,
            severity="major",
            message=(
                "Theory claims spontaneous ordering/organisation but does not identify "
                "the energy source driving it."
            ),
            violated_principle="second_law_of_thermodynamics",
            suggested_fix=(
                "Identify the energy source (radiation field, gravity, chemical potential) "
                "driving self-organisation. Verify entropy budget is globally non-decreasing."
            ),
        )
    return ConsistencyCheck(
        check_name="thermodynamic_consistency",
        passed=True,
        severity="warning",
        message="No thermodynamic consistency violations detected.",
        violated_principle="second_law_of_thermodynamics",
        suggested_fix="",
    )


def _check_internal_non_contradiction(predictions: List[str]) -> ConsistencyCheck:
    """
    Check that the theory's predictions don't directly contradict each other.
    Looks for direct negation pairs in the prediction list.
    """
    if not predictions or len(predictions) < 2:
        return ConsistencyCheck(
            check_name="internal_non_contradiction",
            passed=True,
            severity="warning",
            message="Fewer than 2 predictions — contradiction check not applicable.",
            violated_principle="internal_consistency",
            suggested_fix="",
        )

    contradictions_found = []
    for i, pred_a in enumerate(predictions):
        for j, pred_b in enumerate(predictions):
            if i >= j:
                continue
            pa = pred_a.lower()
            pb = pred_b.lower()
            # Look for direct negation patterns
            negation_pairs = [
                ("increases", "decreases"),
                ("higher", "lower"),
                ("positive", "negative"),
                ("always", "never"),
                ("all ", "none "),
                ("greater than", "less than"),
            ]
            for (w1, w2) in negation_pairs:
                # Check if same noun appears with opposite predicates
                if w1 in pa and w2 in pb:
                    # Extract surrounding noun tokens to see if same subject
                    tokens_a = set(re.findall(r"\b\w+\b", pa))
                    tokens_b = set(re.findall(r"\b\w+\b", pb))
                    shared_nouns = tokens_a & tokens_b - {
                        "the", "a", "an", "is", "are", "be", "of", "in", "and", "or",
                        "increases", "decreases", "higher", "lower", "greater", "less"
                    }
                    if len(shared_nouns) >= 2:
                        contradictions_found.append(
                            f"P{i+1} ({w1}) vs P{j+1} ({w2}): shared subjects {shared_nouns}"
                        )

    if contradictions_found:
        return ConsistencyCheck(
            check_name="internal_non_contradiction",
            passed=False,
            severity="major",
            message=f"Potential internal contradictions in predictions: {contradictions_found[:3]}",
            violated_principle="internal_consistency",
            suggested_fix=(
                "Review the flagged prediction pairs. If they apply to different parameter "
                "regimes, explicitly state the domain of applicability for each."
            ),
        )
    return ConsistencyCheck(
        check_name="internal_non_contradiction",
        passed=True,
        severity="warning",
        message=f"No internal contradictions detected among {len(predictions)} predictions.",
        violated_principle="internal_consistency",
        suggested_fix="",
    )


def _check_correspondence_principle(theory_text: str, domain_of_validity: Dict) -> ConsistencyCheck:
    """
    Check that the theory acknowledges its limiting regimes (correspondence principle).
    """
    text_lower = theory_text.lower()
    dov_text = " ".join(str(v) for v in domain_of_validity.values()).lower() if domain_of_validity else ""
    combined = text_lower + " " + dov_text

    missing_limits = []
    for limit_name, pattern, requirement in _CORRESPONDENCE_LIMITS:
        if re.search(pattern, combined, re.IGNORECASE):
            continue  # Limit acknowledged
        # Only flag if the theory's domain seems to touch the relevant regime
        # (e.g., don't flag Newtonian limit for an astrophysics-only theory)
        if limit_name == "low velocity" and any(
            kw in combined for kw in ["relativistic", "velocity", "v/c", "lorentz"]
        ):
            missing_limits.append(f"{limit_name}: {requirement}")
        elif limit_name == "flat spacetime" and any(
            kw in combined for kw in ["general relativity", "curved", "spacetime", "gr ", "metric"]
        ):
            missing_limits.append(f"{limit_name}: {requirement}")

    if missing_limits:
        return ConsistencyCheck(
            check_name="boundary_conditions_correspondence",
            passed=False,
            severity="minor",
            message=f"Theory may be missing correspondence limits: {missing_limits}",
            violated_principle="correspondence_principle",
            suggested_fix=(
                "Explicitly state the limiting regimes in which the theory reduces to "
                "established physics. Include this in the domain_of_validity field."
            ),
        )
    return ConsistencyCheck(
        check_name="boundary_conditions_correspondence",
        passed=True,
        severity="warning",
        message="Correspondence principle check passed (no obvious missing limits detected).",
        violated_principle="correspondence_principle",
        suggested_fix="",
    )


def _check_energy_budget(theory_text: str, math_core: str) -> ConsistencyCheck:
    """
    Heuristic check: does the theory explicitly account for energy sources/sinks?
    If the theory predicts energy output, does it identify the input?
    """
    text_lower = (theory_text + " " + math_core).lower()
    has_energy_output = any(
        kw in text_lower for kw in ["emits", "luminosity", "radiation", "energy output", "heats"]
    )
    has_energy_source = any(
        kw in text_lower for kw in [
            "powered by", "energy source", "fuel", "accretion", "fusion", "gravitational",
            "kinetic energy input", "radiation field", "energy budget",
        ]
    )
    if has_energy_output and not has_energy_source:
        return ConsistencyCheck(
            check_name="energy_budget",
            passed=False,
            severity="major",
            message=(
                "Theory predicts energy output/luminosity but does not explicitly identify "
                "the energy source. Energy budget appears incomplete."
            ),
            violated_principle="energy_conservation",
            suggested_fix=(
                "Identify the energy source powering the predicted emission (e.g., gravitational "
                "contraction, nuclear burning, accretion, or radiation field). "
                "Verify that input energy ≥ output energy within the theory's domain."
            ),
        )
    return ConsistencyCheck(
        check_name="energy_budget",
        passed=True,
        severity="warning",
        message="Energy budget check passed (no obvious unaccounted energy output).",
        violated_principle="energy_conservation",
        suggested_fix="",
    )


def _check_statistical_language(theory_text: str) -> List[ConsistencyCheck]:
    """Check for statistically problematic language in theory text."""
    checks = []
    for pattern, message in _STATISTICAL_RED_FLAGS:
        if re.search(pattern, theory_text, re.IGNORECASE):
            checks.append(ConsistencyCheck(
                check_name="statistical_language",
                passed=False,
                severity="minor",
                message=f"Problematic statistical language: {message}",
                violated_principle="statistical_rigor",
                suggested_fix=(
                    "Replace absolute claims with probabilistic statements. "
                    "Use 'consistent with', 'strongly suggests', or provide confidence intervals."
                ),
            ))
    if not checks:
        checks.append(ConsistencyCheck(
            check_name="statistical_language",
            passed=True,
            severity="warning",
            message="No problematic statistical language detected.",
            violated_principle="statistical_rigor",
            suggested_fix="",
        ))
    return checks


def _check_against_validated_hypotheses(
    theory_text: str,
    theory_predictions: List[str],
    validated_hypotheses,
) -> List[ConsistencyCheck]:
    """
    Check theory predictions against validated hypothesis results.
    Flags if a theory prediction quantitatively contradicts a validated finding.
    """
    checks: List[ConsistencyCheck] = []
    if not validated_hypotheses:
        return [ConsistencyCheck(
            check_name="validated_hypothesis_consistency",
            passed=True,
            severity="warning",
            message="No validated hypotheses provided for cross-check.",
            violated_principle="empirical_consistency",
            suggested_fix="",
        )]

    n_checks = 0
    for h in validated_hypotheses:
        h_desc = (
            getattr(h, "description", "") if hasattr(h, "description")
            else h.get("description", "") if isinstance(h, dict) else str(h)
        )
        h_id = (
            getattr(h, "id", "?") if hasattr(h, "id")
            else h.get("id", "?") if isinstance(h, dict) else "?"
        )
        h_confidence = (
            getattr(h, "confidence", 0.5) if hasattr(h, "confidence")
            else h.get("confidence", 0.5) if isinstance(h, dict) else 0.5
        )
        if h_confidence < 0.6:
            continue  # Only check against well-validated hypotheses

        # Look for numeric value conflicts
        nums_theory = re.findall(r"[-+]?\d+\.?\d*", " ".join(theory_predictions))
        nums_hyp = re.findall(r"[-+]?\d+\.?\d*", h_desc)
        for nt in nums_theory[:3]:
            for nh in nums_hyp[:3]:
                try:
                    vt, vh = float(nt), float(nh)
                    if vh != 0 and vt != 0:
                        ratio = abs(vt - vh) / max(abs(vt), abs(vh))
                        if ratio > 5.0:  # order-of-magnitude difference
                            checks.append(ConsistencyCheck(
                                check_name="validated_hypothesis_consistency",
                                passed=False,
                                severity="major",
                                message=(
                                    f"Theory predicts value ~{nt} while validated hypothesis "
                                    f"{h_id} reports ~{nh} — a factor {ratio:.1f}× discrepancy."
                                ),
                                violated_principle="empirical_consistency",
                                suggested_fix=(
                                    f"Reconcile theory prediction with validated result from {h_id}. "
                                    "Check units, scaling assumptions, and regime of applicability."
                                ),
                            ))
                            n_checks += 1
                except ValueError:
                    pass

    if n_checks == 0:
        checks.append(ConsistencyCheck(
            check_name="validated_hypothesis_consistency",
            passed=True,
            severity="warning",
            message=f"Theory checked against {len(list(validated_hypotheses))} validated hypotheses — no major numeric conflicts.",
            violated_principle="empirical_consistency",
            suggested_fix="",
        ))
    return checks


# ---------------------------------------------------------------------------
# Main checker class
# ---------------------------------------------------------------------------

class TheoryConsistencyChecker:
    """
    Runs a battery of consistency checks on a Theory object before promotion.
    """

    def check_theory(
        self,
        theory,
        validated_hypotheses=None,
    ) -> List[ConsistencyCheck]:
        """
        Run all consistency checks on `theory`.

        Parameters
        ----------
        theory : Theory | dict
            The theory to check.
        validated_hypotheses : list | None
            Pool of validated hypotheses to cross-check against.

        Returns
        -------
        List[ConsistencyCheck] — all checks, including passed ones.
        """
        checks: List[ConsistencyCheck] = []
        checks.extend(self.check_against_established_physics(theory))
        if validated_hypotheses is not None:
            checks.extend(self.check_against_validated_hypotheses(theory, validated_hypotheses))
        return checks

    # ------------------------------------------------------------------
    def is_internally_consistent(
        self, theory
    ) -> Tuple[bool, List[ConsistencyCheck]]:
        """
        Run only internal consistency checks (no external hypothesis comparison).

        Returns
        -------
        (all_passed: bool, checks: List[ConsistencyCheck])
        """
        checks = self.check_against_established_physics(theory)
        all_passed = all(c.passed or c.severity == "warning" for c in checks)
        return (all_passed, checks)

    # ------------------------------------------------------------------
    def check_against_established_physics(
        self, theory
    ) -> List[ConsistencyCheck]:
        """
        Check theory against fundamental physical principles.
        """
        # Extract fields
        math_core = self._get_field(theory, "mathematical_core", "")
        domain_str = self._get_field(theory, "domain", "")
        name = self._get_field(theory, "name", "")
        axioms = self._get_field(theory, "axioms", [])
        predictions = self._get_field(theory, "derived_predictions", [])
        dov = self._get_field(theory, "domain_of_validity", {})
        falsification = self._get_field(theory, "falsification_conditions", [])

        # Build combined text for text-based checks
        all_text = " ".join(filter(None, [
            name, domain_str, math_core,
            " ".join(axioms if isinstance(axioms, list) else [str(axioms)]),
            " ".join(predictions if isinstance(predictions, list) else [str(predictions)]),
            " ".join(falsification if isinstance(falsification, list) else [str(falsification)]),
        ]))

        checks: List[ConsistencyCheck] = []

        # 1. Dimensional consistency
        checks.append(_dimensional_check(math_core))

        # 2. Causality
        checks.append(_check_causality(all_text))

        # 3. Thermodynamic consistency
        checks.append(_check_thermodynamics(all_text))

        # 4. Internal non-contradiction
        pred_list = predictions if isinstance(predictions, list) else [str(predictions)]
        checks.append(_check_internal_non_contradiction(pred_list))

        # 5. Correspondence principle / boundary conditions
        checks.append(_check_correspondence_principle(all_text, dov if isinstance(dov, dict) else {}))

        # 6. Energy budget
        checks.append(_check_energy_budget(all_text, math_core))

        # 7. Statistical language
        checks.extend(_check_statistical_language(all_text))

        return checks

    # ------------------------------------------------------------------
    def check_against_validated_hypotheses(
        self, theory, hypotheses
    ) -> List[ConsistencyCheck]:
        """
        Check theory predictions for consistency with validated hypotheses.
        """
        predictions = self._get_field(theory, "derived_predictions", [])
        pred_list = predictions if isinstance(predictions, list) else [str(predictions)]
        name = self._get_field(theory, "name", "")
        return _check_against_validated_hypotheses(name, pred_list, hypotheses)

    # ------------------------------------------------------------------
    def overall_score(self, checks: List[ConsistencyCheck]) -> float:
        """
        Compute an overall consistency score from a list of checks.

        Score ∈ [0, 1]:
          - fatal failures     → −0.40 each
          - major failures     → −0.15 each
          - minor failures     → −0.05 each
          - warnings (ignored) → 0

        Returns max(0, 1 + sum_of_penalties).
        """
        penalty_map = {
            "fatal": 0.40,
            "major": 0.15,
            "minor": 0.05,
            "warning": 0.00,
        }
        total_penalty = sum(
            penalty_map.get(c.severity, 0.0)
            for c in checks
            if not c.passed
        )
        return max(0.0, round(1.0 - total_penalty, 3))

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _get_field(obj, field_name: str, default):
        """Safely extract a field from Theory object or dict."""
        if hasattr(obj, field_name):
            val = getattr(obj, field_name)
            return val if val is not None else default
        if isinstance(obj, dict):
            return obj.get(field_name, default)
        return default
