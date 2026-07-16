"""Tests for the Phase-2 claim-search rigor gates (Fixes 1-5, 2026-07-12).

These pin the behavior added in response to the record-8 hold-out audit:
  * Fix 1 — emitted claims persist their program source (reproducible).
  * Fix 2 — the headline statistic is the HELD-OUT one; in-sample is kept too.
  * Fix 3 — triviality: near-deterministic / few-band colour identities rejected.
  * Fix 4 — consistency: narrated rho contradicting the measured effect rejected.
  * Fix 5 — Bonferroni: the Gate-1 p-value bar shrinks with the search family.

Run: python3 astra_core/tests/test_claim_gates.py
"""
import json
import os
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from astra_core.scientific_discovery.evolved_analysis import claim_gates  # noqa: E402
from astra_core.scientific_discovery.evolved_analysis import run_claim_search as rcs  # noqa: E402
from astra_core.scientific_discovery.evolved_analysis.claim_task import (  # noqa: E402
    gate1_significant, PMAX)


# --------------------------------------------------------------------------- #
# Fix 3 — triviality                                                          #
# --------------------------------------------------------------------------- #
def test_triviality_rejects_near_deterministic():
    """|rho| >= 0.98 means the two constructed quantities are the same axis
    (e.g. (g-r) vs (g-i)) — not a discovery."""
    src = 'r,_=spearmanr(df["g"]-df["r"], df["g"]-df["i"])'
    ok, reason = claim_gates.triviality_check(src, 0.991)
    assert ok is False, f"near-deterministic should be rejected: {reason}"


def test_triviality_passes_real_relationship():
    """A genuine multi-band relationship at moderate rho must pass."""
    src = ('gr=df["g"]-df["r"]; ri=df["r"]-df["i"]; iz=df["i"]-df["z"];'
           'r,_=spearmanr(gr+ri, df["z_spec"])')
    ok, reason = claim_gates.triviality_check(src, 0.55)
    assert ok is True, f"real relationship rejected: {reason}"


def test_triviality_rejects_two_band_identity():
    """A very high correlation built from only two bands is a colour identity."""
    src = 'r,_=spearmanr(df["g"]-df["r"], df["u"]-df["g"])'  # bands {g,r,u}
    # 3 bands here -> should pass at 0.9. Force the few-band case explicitly:
    src2 = 'r,_=spearmanr(df["g"]-df["r"], 0.5*df["g"]-0.5*df["r"])'  # {g,r}
    ok2, _ = claim_gates.triviality_check(src2, 0.90)
    assert ok2 is False, "two-band high-rho identity should be rejected"
    ok1, _ = claim_gates.triviality_check(src, 0.90)
    assert ok1 is True, "three-band relationship at 0.9 should pass"


def test_triviality_handles_nonnumeric():
    ok, _ = claim_gates.triviality_check("src", None)
    assert ok is True  # skip safely when no numeric effect


# --------------------------------------------------------------------------- #
# Fix 4 — consistency                                                         #
# --------------------------------------------------------------------------- #
def test_consistency_rejects_contradiction():
    """Claim says 'rho ~ 0.15' but code measured 0.469 (record 10's failure)."""
    claim = "...exhibits a positive correlation (rho ~ 0.15) with redshift..."
    ok, reason = claim_gates.consistency_check(claim, {"effect": 0.469})
    assert ok is False, f"contradiction should be rejected: {reason}"


def test_consistency_passes_matching():
    ok, reason = claim_gates.consistency_check(
        "correlation (rho ~ 0.45) with redshift", {"effect": 0.469})
    assert ok is True, f"matching magnitude rejected: {reason}"


def test_consistency_passes_when_no_magnitude_stated():
    """No stated rho -> nothing to contradict -> pass (conservative)."""
    ok, _ = claim_gates.consistency_check("galaxies with redder colors are at higher z",
                                          {"effect": 0.6})
    assert ok is True


def test_consistency_does_not_misread_color_expression():
    """A colour value 'u-r = 0.8' must NOT be read as a stated correlation."""
    ok, _ = claim_gates.consistency_check("...with u-r = 0.8 ...", {"effect": 0.45})
    assert ok is True, "colour expression mis-read as rho (false rejection)"


# --------------------------------------------------------------------------- #
# Fix 6 — holdout distinctness                                                #
# --------------------------------------------------------------------------- #
def test_holdout_distinct_rejects_identical():
    """effect == effect_insample to float precision => run_claim ignored df_train
    and computed on df_eval for both calls (the record-14 failure mode)."""
    ok, reason = claim_gates.holdout_distinct_check(
        {"effect": 0.38017294, "effect_insample": 0.38017294})
    assert ok is False, f"identical held-out/in-sample should be rejected: {reason}"
    assert "ignores df_train" in reason


def test_holdout_distinct_passes_when_genuinely_different():
    """A real train/test difference (record 20: 0.8510 vs 0.8528) must pass."""
    ok, reason = claim_gates.holdout_distinct_check(
        {"effect": 0.8510, "effect_insample": 0.8528})
    assert ok is True, f"genuine held-out difference rejected: {reason}"


def test_holdout_distinct_skips_without_insample():
    """No in-sample metric (worker error) -> nothing to compare -> pass."""
    ok, _ = claim_gates.holdout_distinct_check({"effect": 0.5})
    assert ok is True


# --------------------------------------------------------------------------- #
# Fix 5 — Bonferroni / family counter                                         #
# --------------------------------------------------------------------------- #
def test_bonferroni_pmax_is_stricter_than_nominal():
    """With a non-trivial family the corrected threshold must be << PMAX."""
    pmax = claim_gates.bonferroni_pmax(PMAX)
    assert pmax < PMAX, f"bonferroni_pmax {pmax} not stricter than nominal {PMAX}"
    assert pmax <= PMAX / claim_gates.MIN_FAMILY


def test_gate1_uses_corrected_pmax():
    """gate1_significant(pmax=...) must reject a p between corrected and nominal."""
    # effect fine, p=1e-4: passes nominal PMAX=1e-3 but fails a stricter 1e-5 bar
    ok_nominal, _ = gate1_significant({"effect": 0.5, "pvalue": 1e-4}, pmax=1e-3)
    ok_strict, _ = gate1_significant({"effect": 0.5, "pvalue": 1e-4}, pmax=1e-5)
    assert ok_nominal is True and ok_strict is False


def test_bump_family_counter_increments_and_persists():
    """Bumping must increment the persistent counter (tolerant of env)."""
    before = claim_gates._read_counter()
    after = claim_gates.bump_family_counter()
    assert after >= before + 1
    assert claim_gates._read_counter() == after


# --------------------------------------------------------------------------- #
# Fix 1 + Fix 2 — emit persists source + hold-out (unit test on a synthetic
# both-pass verdict; _emit's store path is redirected to a temp file).
# --------------------------------------------------------------------------- #
def test_emit_persists_source_and_holdout():
    """_emit must record the program source and the held-out headline metric."""
    # redirect the module's store to a temp file
    fd, tmppath = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    Path(tmppath).write_text("[]")
    orig = rcs.EVOLVED_STORE
    rcs.EVOLVED_STORE = Path(tmppath)
    try:
        verdict = {
            "both_pass": True,
            "claim": "A novel claim about galaxies.",
            "source": "CLAIM='...'\ndef run_claim(a,b):\n    return {'effect':0.5}\n",
            "program_hash": "deadbeef00",
            "gate1": {"metrics": {"effect": 0.47, "pvalue": 1e-20,
                                  "effect_insample": 0.49, "pvalue_insample": 1e-22},
                      "bonferroni_pmax": 1.06e-5, "family_size": 94},
            "gate2": {"status": "novel"},
        }
        rcs._emit(verdict)
        records = json.loads(Path(tmppath).read_text())
        assert len(records) == 1
        r = records[0]
        # Fix 1: source persisted + reproducible
        assert r.get("program_source", "").startswith("CLAIM="), "source not persisted"
        assert r["source"] == "evolved_analysis"  # origin tag intact (consumer dedup)
        # Fix 2: held-out headline + in-sample retained
        v = r["verification"]
        assert v["effect"] == 0.47, "headline effect should be held-out"
        assert v["effect_insample"] == 0.49
        assert v["held_out_split"] == "test"
        # chokepoint still satisfied
        assert v["program_hash"] and v["metric_name"] and v["real_data_result"]
        # Fix 5 accounting recorded
        assert v["gate"]["bonferroni_pmax"] == 1.06e-5
        assert v["gate"]["family_size"] == 94
    finally:
        rcs.EVOLVED_STORE = orig
        os.unlink(tmppath)


def test_emit_noop_unless_both_pass():
    """_emit must not write anything when both_pass is False (anti-fiction)."""
    fd, tmppath = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    Path(tmppath).write_text("[]")
    orig = rcs.EVOLVED_STORE
    rcs.EVOLVED_STORE = Path(tmppath)
    try:
        rcs._emit({"both_pass": False, "claim": "x", "source": "", "program_hash": "h",
                   "gate1": {"metrics": {}, "bonferroni_pmax": 1e-5, "family_size": 50},
                   "gate2": {"status": "known"}})
        assert json.loads(Path(tmppath).read_text()) == []
    finally:
        rcs.EVOLVED_STORE = orig
        os.unlink(tmppath)


# --------------------------------------------------------------------------- #
# Fix 2 (integration) — the seed claim computed on df_train AND df_test gives
# two distinct numeric effects (the hold-out mechanism). Needs the SDSS cache.
# --------------------------------------------------------------------------- #
def test_holdout_split_yields_numeric_effect():
    """The worker's double-call mechanism: fn(train,eval) and fn(test,eval) both
    return numeric effects. Skips gracefully if the real SDSS cache is absent."""
    try:
        from astra_core.scientific_discovery.evolved_analysis.real_data import load_split
        from astra_core.scientific_discovery.evolved_analysis.claim_task import (
            NAIVE_CLAIM_SEED)
        ns: dict = {}
        exec(NAIVE_CLAIM_SEED, ns)
        fn = ns["run_claim"]
    except Exception as e:
        print(f"  SKIP test_holdout_split_yields_numeric_effect (env: {e})")
        return
    splits = load_split(seed=42)
    m_in = fn(splits["train"], splits["eval"])
    m_out = fn(splits["test"], splits["eval"])
    assert isinstance(m_in, dict) and isinstance(m_out, dict)
    assert "effect" in m_in and "effect" in m_out
    assert abs(m_in["effect"]) > 0.2 and abs(m_out["effect"]) > 0.2, \
        "g-r vs z should be significantly correlated on both splits"


# --------------------------------------------------------------------------- #
# Split-discipline fix (2026-07-14) — proposer must compute on df_train        #
# --------------------------------------------------------------------------- #
def test_claim_uses_train_split_passes_df_train():
    src = ('CLAIM = "x"\n\n\n'
           'def run_claim(df_train, df_eval):\n'
           '    df = df_train\n'
           '    return {"effect": 0.5, "pvalue": 1e-9, "effect_type": "t", "summary": "s"}\n')
    ok, _ = claim_gates.claim_uses_train_split(src)
    assert ok is True


def test_claim_uses_train_split_rejects_df_eval_only():
    # Ignores df_train, computes on df_eval -> holdout-distinct would reject.
    src = ('CLAIM = "x"\n\n\n'
           'def run_claim(df_train, df_eval):\n'
           '    df = df_eval\n'
           '    return {"effect": 0.5, "pvalue": 1e-9, "effect_type": "t", "summary": "s"}\n')
    ok, why = claim_gates.claim_uses_train_split(src)
    assert ok is False
    assert "df_eval" in why


def test_claim_uses_train_split_accepts_direct_df_train_use():
    src = ('CLAIM = "x"\n\n\n'
           'def run_claim(df_train, df_eval):\n'
           '    r = df_train["g"].corr(df_train["r"])\n'
           '    return {"effect": float(r), "pvalue": 1e-9, "effect_type": "t", "summary": "s"}\n')
    ok, _ = claim_gates.claim_uses_train_split(src)
    assert ok is True


def test_prompts_require_df_train_discipline():
    """Pin the prompt wording so the split-discipline rule can't silently regress."""
    from astra_core.scientific_discovery.evolved_analysis.claim_task import TASK_SYSTEM
    from astra_core.scientific_discovery.evolved_analysis.data_lake import task_system_for
    assert "df_train" in TASK_SYSTEM and "df_eval alone" in TASK_SYSTEM
    ts = task_system_for("gaia_nearby")
    assert ts and "df_train" in ts and "df_eval alone" in ts


def test_prompts_prime_higher_order_relations():
    """Pin the higher-order/conditional priming that raises the novel rate."""
    from astra_core.scientific_discovery.evolved_analysis.claim_task import TASK_SYSTEM
    from astra_core.scientific_discovery.evolved_analysis.data_lake import task_system_for
    assert "higher-order" in TASK_SYSTEM and "SUBSET" in TASK_SYSTEM
    ts = task_system_for("sdss_galaxy_extended")
    assert ts and "higher-order" in ts and "SUBSET" in ts


def test_circularity_rejects_quantity_built_from_a_correlated_column():
    """A residual constructed WITH a column, then correlated with that column, is
    circular (the strong rho is partly built-in). This is the QSO xi=(u-r)-2.2(g-i)-
    0.6*z_spec then Spearman(xi, z_spec) failure mode."""
    src = (
        'xi = df["u"] - df["r"] - 2.2*(df["g"]-df["i"]) - 0.6*df["z_spec"]\n'
        'r, p = spearmanr(xi, df["z_spec"])'
    )
    ok, reason = claim_gates.circularity_check(src)
    assert ok is False, f"z_spec embedded in xi then correlated with z_spec must reject: {reason}"


def test_circularity_rejects_inline_construction():
    """An inline expression that shares a column with a single-column counterpart is
    circular: spearmanr(df['a']-df['b'], df['b'])."""
    src = 'r, p = spearmanr(df["a"] - df["b"], df["b"])'
    ok, _ = claim_gates.circularity_check(src)
    assert ok is False


def test_circularity_passes_clean_colour_vs_other_column():
    """A colour built from g,r correlated with an unrelated column (z_spec) is fine."""
    src = 'r, p = spearmanr(df["g"] - df["r"], df["z_spec"])'
    ok, _ = claim_gates.circularity_check(src)
    assert ok is True


def test_circularity_passes_crossmodal_morphology_relation():
    """The verified cross-modal discovery pattern: a size/colour residual correlated
    with concentration must NOT be flagged (concentration is not in the residual)."""
    src = (
        'resid = df["r"] - df["w1"] - 0.3*df["log_r90"]\n'
        'r, p = spearmanr(resid, df["concentration_r"])'
    )
    ok, _ = claim_gates.circularity_check(src)
    assert ok is True


def test_circularity_rejects_intermediate_var_and_mask_indexing():
    """Real-world pattern (the exact QSO curvature failure mode): columns loaded into
    short aliases, a residual built from one alias, then correlated with that alias
    under boolean indexing. Must be caught via transitive alias resolution."""
    src = (
        'ur = df["u"] - df["r"]\n'
        'gi = df["g"] - df["i"]\n'
        'zs = df["z_spec"]\n'
        'residual = ur - 2.2*gi - 0.6*zs\n'
        'mask = np.isfinite(residual) & np.isfinite(zs)\n'
        'corr, p = spearmanr(residual[mask], zs[mask])'
    )
    ok, _ = claim_gates.circularity_check(src)
    assert ok is False


def _run():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS  {t.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL  {t.__name__}: {e}")
        except Exception as e:
            print(f"  ERROR {t.__name__}: {type(e).__name__}: {e}")
    print(f"\n{passed}/{len(tests)} passed")
    return 0 if passed == len(tests) else 1


if __name__ == "__main__":
    sys.exit(_run())
