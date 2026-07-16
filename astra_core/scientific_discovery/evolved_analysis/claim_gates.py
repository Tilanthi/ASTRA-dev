"""claim_gates.py — extra rigor gates for the Phase-2 claim search (Fixes 3/4/5).

These sit alongside Gate-1 (real-data significance) and Gate-2 (literature
novelty) and close the holes exposed by the 2026-07-12 record-8 audit:

  * ``triviality_check``  (Fix 3) — reject "discoveries" that are arithmetic,
    not physics: a near-deterministic correlation (|rho| >= 0.98) means the two
    constructed quantities are the same axis (e.g. (g-r) vs (g-i)); and a very
    high correlation built from only one or two photometric bands is almost
    certainly a trivial colour identity.
  * ``consistency_check`` (Fix 4) — reject claims whose NARRATED correlation
    magnitude contradicts the MEASURED one (e.g. abstract says "rho ~ 0.15" but
    the code measured 0.469). Catches the LLM-narrates-one-number /
    code-measures-another failure mode.
  * ``bonferroni_pmax`` / ``bump_family_counter`` (Fix 5) — correct the Gate-1
    p-value threshold for the size of the search family. The search tries many
    candidate relationships and keeps the survivors; without correction the
    nominal p <= 1e-3 bar is far too lenient.

Stdlib-only on purpose (no ``evolved_analysis`` / ``astra_core`` imports) so this
stays decoupled and cheap to load from the sandboxed worker / orchestrator.
"""
from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

PERSIST_DIR = Path.home() / ".astra_persistent"
FAMILY_COUNTER = PERSIST_DIR / "evolved_programs" / "claim_family_counter.json"
NOVELTY_CACHE = PERSIST_DIR / "evolved_programs" / "novelty_cache.json"

# Floor for the family size: even on the first run we assume a non-trivial
# search space so the correction is never a no-op (Bonferroni with n=1 would
# leave PMAX untouched and re-admit the problem).
MIN_FAMILY = 50

# Triviality thresholds (conservative — only flag glaring cases to avoid false
# positives; Gate-2 novelty remains the broad-spectrum filter).
TRIVIAL_RHO_ABS = 0.98      # |rho| at/above this = the two quantities are identical
TRIVIAL_RHO_FEWBAND = 0.85  # ...combined with <=2 distinct bands
TRIVIAL_RHO_SHARED = 0.92   # ...combined with a shared band between the two args

# Consistency: a narrated correlation magnitude is "contradictory" if it differs
# from the measured |effect| by more than this and no narrated magnitude matches.
CONSISTENCY_TOL = 0.20

# Fix 6 — holdout distinctness. The worker computes holdout = fn(test, eval) and
# insample = fn(train, eval); if a run_claim IGNORES df_train and computes on
# df_eval alone, both calls run the identical computation on eval, so the held-out
# and in-sample effects match to float precision. That means the 'test' split was
# never touched and the headline statistic is an eval-set number the search
# selected on — not a held-out result. |effect - effect_insample| below this is
# treated as "the code ignored the split". (Genuine splits differ by ~1e-3+.)
HOLDOUT_DISTINCT_EPS = 1e-9

BANDS = ("u", "g", "r", "i", "z")


# --------------------------------------------------------------------------- #
# Fix 3 — triviality                                                          #
# --------------------------------------------------------------------------- #
def _bands_used(src: str) -> set:
    """Return the set of photometric bands {u,g,r,i,z} the source references.

    Looks for dataframe access patterns (``df["g"]``, ``d.r``, ``gr = ...`` is
    *not* a band) so a constructed colour like ``df["g"] - df["r"]`` counts as
    {g, r}. ``z_spec`` / ``z_mag`` are excluded so spectroscopic redshift does
    not register as the z-band. This is a heuristic — it can under-count when a
    claim stores colours in opaquely-named variables, which only makes the gate
    more conservative (it will miss some trivial claims, not falsely kill real
    ones)."""
    bands: set = set()
    # df["g"] / d["u"] style
    for m in re.finditer(r'\[\s*["\']([ugriz])["\']\s*\]', src):
        bands.add(m.group(1))
    # df.g / d.r style (word boundary; not z_spec / z_mag / .real / .ravel)
    for m in re.finditer(r'\.([ugriz])\b(?!_)\b', src):
        tok = m.group(1)
        # avoid matching the correlation variable `r` when used as `.r` on a
        # scipy result (e.g. `res.r`) — require it follows a dataframe-ish name.
        # Cheap guard: only count if the same band also appears in a [...] access
        # OR the source has no scipy-style `.correlation`/`rho` assignment to it.
        bands.add(tok)
    return bands


def _correlation_args(src: str) -> Tuple[str, str]:
    """Best-effort extraction of the two arguments to the correlation call.

    Returns ("", "") if it cannot find them (the shared-band test is then
    skipped). Handles spearmanr(a, b) / pearsonr(a, b) on a single line."""
    m = re.search(r"(?:spearmanr|pearsonr|kendalltau)\s*\((.{1,120}?)\)\s*\[?",
                  src, re.DOTALL)
    if not m:
        return "", ""
    inner = m.group(1)
    # split on the top-level comma (arguments are usually simple expressions)
    parts = _split_top_comma(inner)
    if len(parts) < 2:
        return "", ""
    return parts[0].strip(), parts[1].strip()


def _split_top_comma(s: str) -> list:
    out, depth, cur = [], 0, ""
    for ch in s:
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        if ch == "," and depth == 0:
            out.append(cur)
            cur = ""
        else:
            cur += ch
    if cur.strip():
        out.append(cur)
    return out


def triviality_check(src: str, holdout_effect: float) -> Tuple[bool, str]:
    """Fix 3. Return (ok, reason). ``ok=False`` means the claim is trivially
    arithmetic and must NOT be emitted as a discovery.

    Three objective signals, all conservative:
      1. |effect| >= 0.98         — near-deterministic (same axis).
      2. <=2 distinct bands AND |effect| >= 0.85 — a high correlation built from
         one or two bands is a colour identity, not a finding.
      3. the two correlation args share a band AND |effect| >= 0.92.
    """
    try:
        rho = abs(float(holdout_effect))
    except (TypeError, ValueError):
        return True, "triviality:skipped (no numeric hold-out effect)"

    if rho >= TRIVIAL_RHO_ABS:
        return False, (f"triviality:reject |rho|={rho:.3f}>={TRIVIAL_RHO_ABS} "
                       "(near-deterministic — the two quantities are the same axis)")

    bands = _bands_used(src or "")
    if len(bands) <= 2 and rho >= TRIVIAL_RHO_FEWBAND:
        return False, (f"triviality:reject |rho|={rho:.3f} from only {len(bands)} "
                       f"band(s) {sorted(bands)} (trivial colour identity)")

    a, b = _correlation_args(src or "")
    if a and b:
        ba = _bands_used(a)
        bb = _bands_used(b)
        if ba and bb and (ba & bb) and rho >= TRIVIAL_RHO_SHARED:
            return False, (f"triviality:reject |rho|={rho:.3f}; correlation args "
                           f"share band(s) {sorted(ba & bb)} (same photometric axis)")

    return True, f"triviality:pass (|rho|={rho:.3f}, bands={sorted(bands)})"


# --------------------------------------------------------------------------- #
# Fix 4 — narrated-vs-measured consistency                                    #
# --------------------------------------------------------------------------- #
# Patterns where the claim TEXT states a correlation magnitude. The number is
# captured so we can compare it to the measured |effect|. We match only explicit
# correlation keywords (rho / pearson / spearman / correlation) — NOT a bare
# ``r``, which would mis-read a colour expression like ``u-r = 0.8`` as a stated
# correlation and false-reject real claims.
_RHO_PATTERN = re.compile(
    r"(?:rho|pearson|spearman|correlation)\s*(?:~|≈|=|of|:)?\s*"
    r"([-+]?\d*\.\d+|[-+]?\d+\.\d*)",
    re.IGNORECASE,
)


def consistency_check(claim: str, holdout_metrics: dict) -> Tuple[bool, str]:
    """Fix 4. Return (ok, reason). ``ok=False`` when the claim narrates a
    correlation magnitude that contradicts the measured one.

    Logic: collect every correlation-looking number the claim states; if any is
    within CONSISTENCY_TOL of the measured |effect| the claim is self-consistent.
    If the claim states at least one such magnitude and NONE matches, it is
    contradictory (LLM narrated one value, code measured another). Claims that
    state no correlation magnitude pass (nothing to contradict)."""
    try:
        measured = abs(float((holdout_metrics or {}).get("effect", 0.0)))
    except (TypeError, ValueError):
        return True, "consistency:skipped (no numeric effect)"

    stated = []
    for m in _RHO_PATTERN.finditer(claim or ""):
        try:
            v = abs(float(m.group(1)))
        except ValueError:
            continue
        if 0.0 <= v <= 1.0:  # a plausible correlation magnitude
            stated.append(v)
    if not stated:
        return True, "consistency:pass (no stated correlation magnitude)"

    closest = min(stated, key=lambda v: abs(v - measured))
    if abs(closest - measured) <= CONSISTENCY_TOL:
        return True, (f"consistency:pass (stated {closest:.3f} ~ measured "
                      f"{measured:.3f})")
    return False, (f"consistency:reject — claim states rho~{closest:.3f} but code "
                   f"measured |effect|={measured:.3f} (delta {abs(closest-measured):.3f} "
                   f"> {CONSISTENCY_TOL})")


# --------------------------------------------------------------------------- #
# Fix 6 — holdout distinctness (the code must actually use the test split)     #
# --------------------------------------------------------------------------- #
def holdout_distinct_check(metrics: dict) -> Tuple[bool, str]:
    """Fix 6. Return (ok, reason). ``ok=False`` when the held-out effect equals
    the in-sample effect to float precision — proof the candidate's ``run_claim``
    ignored ``df_train`` and computed on ``df_eval`` alone.

    The sandboxed worker evaluates each candidate twice:
      * insample = run_claim(train, eval)
      * holdout  = run_claim(test,  eval)   <- the headline statistic
    A correct claim uses its first arg, so train vs test give different effects.
    A claim that does ``df = df_eval`` runs the identical computation on eval in
    both calls -> effect == effect_insample exactly, the 'test' split is never
    used, and the stored ``held_out_split: "test"`` is false. The 2026-07-13
    store re-run found 6/9 source-bearing records doing exactly this.

    Claims with no in-sample metric (worker error on the insample call) pass —
    there is nothing to compare against (gate1_significance still applies)."""
    m = metrics or {}
    try:
        eff = float(m.get("effect"))
        ins = float(m.get("effect_insample"))
    except (TypeError, ValueError):
        return True, "holdout:skipped (no in-sample effect to compare)"
    if abs(eff - ins) < HOLDOUT_DISTINCT_EPS:
        return False, (f"holdout:reject effect={eff:.4f} == effect_insample={ins:.4f} "
                       "(run_claim ignores df_train; the held-out statistic is not "
                       "genuine — computed on eval, mislabeled as test)")
    return True, (f"holdout:pass (|effect - effect_insample|={abs(eff - ins):.2e})")


def claim_uses_train_split(src: str) -> Tuple[bool, str]:
    """Static pre-check (defence-in-depth BEFORE the sandbox): does the candidate
    compute on df_train (the FIRST argument) rather than df_eval alone?

    Rationale: the sandboxed worker runs run_claim twice — once with the train
    split first, once with the test split first. A claim that ignores df_train and
    computes on df_eval yields an identical effect both times, so
    holdout_distinct_check (above) rejects it. This cheap STATIC check catches the
    same flaw BEFORE a sandbox run is spent, letting the proposer re-generate
    instead of wasting a Gate-1 eval. Revealed by the 2026-07-14 pilot: 12/12
    Gate-1 passers on the new data-lake datasets were df_eval-only.

    Heuristic: drop the signature line, then require df_train to appear in the
    BODY. If it does, the code depends on the train split (so train vs test give
    different effects). holdout_distinct_check remains the authoritative runtime
    check (defence in depth)."""
    body = re.sub(r"def\s+run_claim\s*\([^)]*\)\s*:", "", src or "", count=1)
    if "df_train" in body:
        return True, "uses df_train in body"
    return False, ("df_train not referenced in body — computes on df_eval alone "
                   "(holdout-distinct would reject)")


# --------------------------------------------------------------------------- #
# Anti-circularity (a constructed quantity correlated with one of its inputs)  #
# --------------------------------------------------------------------------- #
_NONSTRING_INDEX = re.compile(r'\[[^\[\]"\']*\]')  # [mask] / [0:5], but NOT ["col"]


def _definition_of(src: str, var: str) -> Optional[str]:
    """The RHS of the last ``<var> = <rhs>`` assignment in src, else None."""
    rhs = None
    for line in (src or "").splitlines():
        m = re.match(r'\s*' + re.escape(var) + r'\s*=\s*(.*)', line)
        if m:
            rhs = m.group(1)
    return rhs


def _columns_in(expr: str, src: str, _seen=None) -> set:
    """Set of base DATA COLUMNS an expression ultimately depends on, resolving
    intermediate variables transitively (so a residual built from short var aliases
    like ``ur``/``zs`` resolves to its real constituent columns). Boolean/integer
    indexing ``[mask]`` is stripped; string column access ``df["C"]`` is kept."""
    if _seen is None:
        _seen = set()
    s = _NONSTRING_INDEX.sub('', (expr or "").strip())       # drop [mask], keep ["col"]
    cols = set(re.findall(r'\[\s*["\']([A-Za-z_]\w*)["\']\s*\]', s))
    for v in set(re.findall(r'\b([A-Za-z_]\w*)\b', s)):
        if v in _seen:
            continue
        defn = _definition_of(src, v)
        if defn is not None:
            _seen.add(v)
            cols |= _columns_in(defn, src, _seen)
    return cols


def circularity_check(src: str) -> Tuple[bool, str]:
    """Reject a circular claim: one side of the reported correlation is a single
    column C and the other is a quantity CONSTRUCTED FROM C. Classic failure mode —
    a residual built WITH z_spec, then ``Spearman(residual, z_spec)``: the strong rho
    is partly built-in by construction (such a claim even reproduces on an unrelated
    population, as the 2026-07-16 QSO curvature 'discovery' did when re-run on
    galaxies). Resolves intermediate var aliases transitively, so it catches real
    code (``residual = ur - ... - 0.6*zs; spearmanr(residual[mask], zs[mask])``).
    Conservative: flags only a single-column side embedded in the other;
    multi-column/multi-column pairs are left to the triviality gate. (ok, reason);
    ok=False => circular => reject."""
    a, b = _correlation_args(src or "")
    if not a or not b:
        return True, "circularity:skipped (no correlation args found)"
    ca, cb = _columns_in(a, src), _columns_in(b, src)
    if not ca or not cb:
        return True, "circularity:skipped (columns unresolved)"
    if len(cb) == 1 and next(iter(cb)) in ca and ca != cb:
        return False, (f"circularity:reject — '{b.strip()}' is a single column built "
                       f"into the other side ({sorted(ca)})")
    if len(ca) == 1 and next(iter(ca)) in cb and ca != cb:
        return False, (f"circularity:reject — '{a.strip()}' is a single column built "
                       f"into the other side ({sorted(cb)})")
    return True, "circularity:pass"


# --------------------------------------------------------------------------- #
# Fix 5 — multiple-testing (Bonferroni over the search family)                #
# --------------------------------------------------------------------------- #
def _read_counter() -> int:
    try:
        if FAMILY_COUNTER.exists():
            d = json.loads(FAMILY_COUNTER.read_text())
            if isinstance(d, dict):
                return int(d.get("n_gate1_evals", 0))
    except Exception:
        pass
    return 0


def _novelty_cache_size() -> int:
    try:
        if NOVELTY_CACHE.exists():
            d = json.loads(NOVELTY_CACHE.read_text())
            if isinstance(d, dict):
                return len(d)
    except Exception:
        pass
    return 0


def family_size() -> int:
    """Lower bound on the number of distinct relationships the search has tested
    for significance (Gate-1). Uses the max of the dedicated counter, the
    novelty-cache size (claims that reached Gate-2), and a conservative floor."""
    return max(_read_counter(), _novelty_cache_size(), MIN_FAMILY)


def bonferroni_pmax(nominal_pmax: float) -> float:
    """Bonferroni-corrected Gate-1 p-value threshold: nominal / family_size."""
    n = family_size()
    return max(nominal_pmax / n, 1e-300)  # guard against underflow


def bump_family_counter() -> int:
    """Increment the persistent Gate-1 evaluation counter; return the new value.

    Called once per candidate the search evaluates for significance, so the
    family size reflects how many relationships have been tried (the quantity a
    multiple-testing correction must account for)."""
    try:
        PERSIST_DIR.mkdir(parents=True, exist_ok=True)
        n = _read_counter() + 1
        (FAMILY_COUNTER.parent).mkdir(parents=True, exist_ok=True)
        FAMILY_COUNTER.write_text(json.dumps({"n_gate1_evals": n}))
        return n
    except Exception as e:  # never let accounting crash the search
        logger.debug("[claim_gates] family-counter bump failed: %s", e)
        return _read_counter()


if __name__ == "__main__":
    # quick self-check
    logging.basicConfig(level=logging.INFO)
    print("family_size:", family_size(), "| bonferroni_pmax(1e-3):",
          f"{bonferroni_pmax(1e-3):.2e}")
    print(triviality_check('r,_=spearmanr(df["g"]-df["r"], df["g"]-df["i"])', 0.991))
    print(triviality_check('r,_=spearmanr(df["u"]-df["r"], df["z_spec"])', 0.55))
    print(consistency_check("...correlation (rho ~ 0.15) with redshift...",
                            {"effect": 0.469}))
    print(consistency_check("...correlation (rho ~ 0.45) with redshift...",
                            {"effect": 0.469}))
