"""run_claim_search.py — Phase-2 open-ended Eureka search driver.

Runs the two-gate EVALUATE on (CLAIM, run_claim) candidate artifacts:

    Gate 1 (real-data, SANDBOXED, no network)  -> claim_eval_worker
    Gate 2 (literature novelty, WITH network)  -> novelty_gate.check_novelty

A candidate is emitted to ``evolved_discoveries.json`` ONLY if it passes BOTH
gates. The supervisor's consumer then folds it into the genuine store through
the discovery_store chokepoint — so a claim can never bypass verification.

Run (decoupled, like the Phase-1 engine):
    PYTHONPATH=astra_core/scientific_discovery python -m evolved_analysis.run_claim_search [--steps N]

If no LLM token is set, it runs the deterministic seed through both gates
(sanity check: the known seed passes Gate 1 and is caught by Gate 2) and exits.
With a token, it also evolves N LLM-proposed candidates looking for a
significant AND novel relationship.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from .claim_task import (NAIVE_CLAIM_SEED, TASK_SYSTEM, ENTRY_POINT,
                         parse_claim, gate1_significant, PMAX)
from .claim_gates import (triviality_check, consistency_check,
                          holdout_distinct_check, claim_uses_train_split,
                          circularity_check, precision_check,
                          geometry_narration_check,
                          bonferroni_pmax, bump_family_counter, family_size)
from .proposer import LLMProposer, apply_diff

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[3]
WORKER = "evolved_analysis.claim_eval_worker"
EVOLVED_STORE = Path.home() / ".astra_persistent" / "evolved_discoveries.json"
# Structured per-candidate verdict log (observability). The supervisor runs this
# module as a subprocess with stdout/stderr -> DEVNULL, so without an explicit
# file write the gate verdicts are lost and we cannot diagnose where candidates
# die (Gate-1 significance / triviality / consistency / holdout / Gate-2
# novelty). JSONL; rotated at VERDICT_LOG_CAP_BYTES to avoid unbounded growth
# (the failure mode that produced the 1.26 GB legacy autonomous log).
VERDICT_LOG = (Path.home() / ".astra_persistent" / "evolved_programs"
               / "claim_verdicts.jsonl")
VERDICT_LOG_CAP_BYTES = 20 * 1024 * 1024
# F2 pilot-before-scale (2026-09-08): a dataset is COLD when no gate1 pass
# appears in its last PILOT_HISTORY_WINDOW verdict rows (windowed on purpose —
# every rotated dataset has thousands of lifetime passes, but liveness is a
# property of the recent search: niche exhaustion, a tightened family bar, or
# a degenerate proposer all show up as a barren recent window).
PILOT_HISTORY_WINDOW = 120
PILOT_DEFAULT_STEPS = 3
try:
    import shutil
    _SANDBOX_EXEC = shutil.which("sandbox-exec")
except Exception:
    _SANDBOX_EXEC = None
_PROFILE = Path(__file__).resolve().parent / "astra_worker.sb"


def _program_hash(src: str) -> str:
    return hashlib.sha1(src.encode()).hexdigest()[:10]


def _finding_key(effect, pvalue) -> tuple:
    """(rounded effect, p-value) fingerprint for emit-time dedup, or None to fall
    back to program_hash. Regenerated duplicates of the same finding share
    effect+p-value (the ``run_claim`` computation is identical) even though
    program_hash and claim wording differ — so this reliably catches them. Mirrors
    discovery_store.dedup_key."""
    try:
        return ("fp", round(float(effect), 4), float(f"{float(pvalue):.6g}"))
    except (TypeError, ValueError):
        return None


# --------------------------------------------------------------------------- #
# Gate 1: sandboxed real-data test                                             #
# --------------------------------------------------------------------------- #
def gate1_run(src: str, seed: int = 42, timeout: float = 90.0,
              source: str = "legacy", permute_seed: int = None) -> dict:
    """Run the candidate's run_claim in a sandboxed subprocess on real data.

    ``source`` selects the dataset: 'legacy' (default, SDSS photo-z via
    real_data.py) or a data-lake dataset name (data_lake.py, Sub-project C).
    The worker only reads a cached CSV — it never fetches. ``permute_seed``
    (fresh-attacker mode, Phase 2) asks the worker to independently shuffle
    every column first — the generic permutation null."""
    if not src or f"def {ENTRY_POINT}" not in src:
        return {"effect": 0.0, "pvalue": 1.0, "error": f"no {ENTRY_POINT}"}
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False,
                                     dir=str(Path.cwd())) as tf:
        tf.write(src)
        tf.flush()
        src_path = tf.name
    try:
        env = {**os.environ,
               "PYTHONPATH": str(Path(__file__).resolve().parents[1])}
        if permute_seed is not None:
            env["ASTRA_ATTACK_PERMUTE"] = str(permute_seed)
        cmd = [sys.executable, "-m", WORKER, src_path, str(seed)]
        if source and source != "legacy":
            cmd.append(source)
        # Wrap in sandbox-exec when available (no-network, temp-writes-only).
        if _SANDBOX_EXEC and _PROFILE.is_file():
            cmd = [_SANDBOX_EXEC, "-f", str(_PROFILE)] + cmd
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              timeout=timeout, cwd=str(REPO_ROOT), env=env,
                              check=False)
    except subprocess.TimeoutExpired:
        return {"effect": 0.0, "pvalue": 1.0, "error": "timeout"}
    except Exception as e:
        return {"effect": 0.0, "pvalue": 1.0,
                "error": f"spawn:{type(e).__name__}:{str(e)[:80]}"}
    finally:
        try:
            Path(src_path).unlink()
        except OSError:
            pass
    out = proc.stdout.strip().splitlines()
    if not out:
        return {"effect": 0.0, "pvalue": 1.0,
                "error": (proc.stderr.strip()[:160] or "no stdout")}
    try:
        return json.loads(out[-1])
    except json.JSONDecodeError:
        return {"effect": 0.0, "pvalue": 1.0,
                "error": f"unparseable: {out[-1][:120]}"}


# --------------------------------------------------------------------------- #
# Two-gate evaluation                                                          #
# --------------------------------------------------------------------------- #
def two_gate_eval(src: str, seed: int = 42, run_gate2: bool = True,
                  source: str = "legacy") -> dict:
    """Run Gate 1 (significance on HELD-OUT data, Bonferroni-corrected), the
    triviality + consistency sub-gates, then (if all pass) Gate 2 (novelty).

    Returns a full verdict dict. A claim is emitted only if every gate passes:
      gate1 (real-data, hold-out, |effect|>=EFFECT_MIN and p<=bonferroni_pmax)
        AND triviality (not a near-deterministic / few-band identity — Fix 3)
        AND consistency (narrated rho matches measured — Fix 4)
        AND gate2 (not already in the literature).

    ``source`` selects the dataset (Sub-project C); default 'legacy'."""
    claim = parse_claim(src) or ""
    bump_family_counter()                      # Fix 5: count this trial
    corrected_pmax = bonferroni_pmax(PMAX)     # Fix 5: PMAX / family_size
    g1_metrics = gate1_run(src, seed=seed, source=source)  # hold-out primary
    g1_pass, g1_reason = gate1_significant(g1_metrics, pmax=corrected_pmax,
                                           dataset=source)

    # Fix 3 (triviality) + Fix 4 (consistency) on the held-out metric.
    metrics_for_gates = g1_metrics if isinstance(g1_metrics, dict) else {}
    holdout_effect = metrics_for_gates.get("effect", 0.0)
    try:
        holdout_effect = float(holdout_effect)
    except (TypeError, ValueError):
        holdout_effect = 0.0
    triv_ok, triv_reason = triviality_check(src, holdout_effect)
    cons_ok, cons_reason = consistency_check(claim, metrics_for_gates)
    hold_ok, hold_reason = holdout_distinct_check(metrics_for_gates)  # Fix 6
    circ_ok, circ_reason = circularity_check(src)  # anti-circularity (2026-07-16)
    prec_ok, prec_reason = precision_check(claim, metrics_for_gates)  # IOAA sig-figs
    geom_ok, geom_reason = geometry_narration_check(claim, metrics_for_gates)  # code-only-geometry

    result = {
        "claim": claim,
        "source": src,                          # Fix 1: persist program source
        "program_hash": _program_hash(src),
        "gate1": {"pass": g1_pass, "reason": g1_reason,
                  "metrics": {k: v for k, v in g1_metrics.items() if k != "trace"},
                  "bonferroni_pmax": corrected_pmax,
                  "family_size": family_size()},
        "triviality": {"pass": triv_ok, "reason": triv_reason},
        "consistency": {"pass": cons_ok, "reason": cons_reason},
        "holdout": {"pass": hold_ok, "reason": hold_reason},
        "circularity": {"pass": circ_ok, "reason": circ_reason},
        "precision": {"pass": prec_ok, "reason": prec_reason},
        "geometry": {"pass": geom_ok, "reason": geom_reason},
        "gate2": None,
        "both_pass": False,
        "dataset": source,
    }

    if not (g1_pass and triv_ok and cons_ok and hold_ok and circ_ok
            and prec_ok and geom_ok):
        return result  # significance / triviality / consistency / holdout / circularity stop here

    if run_gate2:
        try:
            from .novelty_gate import check_novelty
            nr = check_novelty(claim)
            result["gate2"] = {
                "pass": nr.novel, "status": nr.status, "n_retrieved": nr.n_retrieved,
                "reasoning": nr.reasoning[:200],
                "confidence": nr.confidence,
                "entailed_by": nr.entailed_by.title[:80] if nr.entailed_by else None,
                # F4 (2026-09-08): False when check_novelty re-verified against
                # live sources (fresh, or a stale cache falling through to the
                # live path) — the emitted invariant is "novel => live-verified
                # within LIVE_CHECK_TTL".
                "from_cache": nr.from_cache,
            }
            result["novelty_revision"] = nr.revision
        except Exception as e:
            # Gate-2 failure is conservative: do NOT promote as novel.
            result["gate2"] = {"pass": False, "status": "gate2-error",
                               "reasoning": f"{type(e).__name__}: {str(e)[:120]}"}
    else:
        result["gate2"] = {"pass": None, "status": "skipped"}

    # token-free novelty prior (ALS concept graph): ranking signal only,
    # recorded beside the verdict — it never gates (see concept_prior.py)
    try:
        from .concept_prior import score_cached
        result["concept_prior"] = score_cached(claim)
    except Exception:
        result["concept_prior"] = None

    result["both_pass"] = bool(
        g1_pass and triv_ok and cons_ok and hold_ok and result["gate2"]
        and result["gate2"]["pass"] is True)
    return result


# --------------------------------------------------------------------------- #
# emit (only both-gate survivors, through the chokepoint-compatible shape)     #
# --------------------------------------------------------------------------- #
def _load_store_list() -> list:
    """Read evolved_discoveries.json as a list ([] on missing/corrupt)."""
    try:
        data = json.loads(EVOLVED_STORE.read_text()) if EVOLVED_STORE.exists() else []
        return data if isinstance(data, list) else []
    except Exception as e:
        logger.warning("[claim_search] store read failed: %s", e)
        raise


def _emit_is_duplicate(verdict: dict) -> bool:
    """True if an equivalent finding is already in the evolved store.

    Dedup: a regenerated duplicate has a different program_hash + wording but
    the SAME held-out effect + p-value (identical computation)."""
    g1m = verdict["gate1"]["metrics"]
    nk = _finding_key(g1m.get("effect"), g1m.get("pvalue"))

    def _is_dup(r):
        rv = (r.get("verification") or {}) if isinstance(r, dict) else {}
        rk = _finding_key(rv.get("effect"), rv.get("pvalue"))
        if nk is not None and rk is not None:
            return rk == nk
        return rv.get("program_hash") == verdict["program_hash"]

    return any(_is_dup(r) for r in _load_store_list())


def _emit(verdict: dict) -> bool:
    """Append a both-gate survivor to evolved_discoveries.json (bare list).

    The promotion OUTCOME is written back into ``verdict`` — ``emitted``,
    ``emit_reason``, ``fresh_attacker``, ``second_judge`` — so the verdict log
    (appended by the caller AFTER ``_emit``) records what actually happened at
    the chokepoint, not only what the gates said. Returns True iff the record
    reached the store."""
    if not verdict["both_pass"]:
        verdict["emitted"], verdict["emit_reason"] = False, "not-both-pass"
        verdict.setdefault("fresh_attacker", None)
        return False
    # Emit-time dedup BEFORE any promotion spend (5 attacker sandbox runs, a
    # possible second-judge call): a duplicate dropped only at the write would
    # mean paying the attacker for a no-op.
    try:
        _dup = _emit_is_duplicate(verdict)
    except Exception:
        _dup = False  # unreadable store: let the write block's guard handle it
    if _dup:
        verdict["emitted"], verdict["emit_reason"] = False, "duplicate"
        verdict.setdefault("fresh_attacker", None)
        return False
    # Phase 2 hard rule (Eureka plan, 2026-08-30): every finding crossing the
    # promotion threshold is attacked by an empty-context copy BEFORE the
    # store write — before anyone hears of it — even when the proposer is sure
    # it is fine. killed/not-runnable findings are never emitted.
    try:
        from .fresh_attacker import attack_claim
        attack = attack_claim(verdict["source"], verdict.get("dataset", "legacy"))
    except Exception as e:  # attacker itself failing is a not-runnable verdict
        attack = {"disposition": "not-runnable",
                  "error": f"{type(e).__name__}: {str(e)[:160]}"}
    verdict["fresh_attacker"] = attack
    if attack.get("disposition") in ("killed", "not-runnable"):
        logger.warning("[claim_search] ⚔ fresh-attacker %s — NOT emitted: %s",
                       attack.get("disposition"), str(attack.get("detail"))[:120])
        verdict["emitted"] = False
        verdict["emit_reason"] = f"attacker-{attack.get('disposition')}"
        return False
    # Cross-model audit at the promotion threshold ONLY (2026-09-08): one
    # empty-context novelty judge from a DIFFERENT model family, after the
    # (zero-spend) attacker and before the store write. An unconfigured or
    # failing audit is recorded as itself and never blocks (fiction rule);
    # the single blocking ground is an abstract-entailed "known".
    try:
        from .second_judge import audit_claim
        sj = audit_claim(verdict["claim"], dataset=verdict.get("dataset", "legacy"))
    except Exception as e:  # the audit failing is its own honest record
        sj = {"status": "error", "block": False,
              "error": f"{type(e).__name__}: {str(e)[:160]}"}
    verdict["second_judge"] = sj
    if sj.get("status") == "error":
        # an audit malfunction is its own honest record, never a pass
        try:
            from .evidence_ledger import safe_append
            safe_append("note", "second-judge-error",
                        claim=(verdict.get("claim") or "")[:200],
                        dataset=verdict.get("dataset"),
                        detail=(sj.get("error") or "")[:200])
        except Exception:
            pass
    if sj.get("block"):
        logger.warning("[claim_search] ⚖ second-judge known (entailed) — NOT "
                       "emitted: %s", (sj.get("reasoning") or "")[:120])
        verdict["emitted"], verdict["emit_reason"] = False, "second-judge-known"
        # the register's blocked-at-promotion stream reads exactly this ledger
        # line (kind=attack — the empty-context adversarial check family; the
        # clock treats it as new evidence, unlike kind=register)
        try:
            from .evidence_ledger import safe_append
            safe_append("attack", "second-judge-known",
                        claim=verdict.get("claim"),
                        dataset=verdict.get("dataset"),
                        program_hash=verdict.get("program_hash"),
                        detail="second-family judge marked known-entailed: "
                               f"{(sj.get('reasoning') or '')[:160]}")
        except Exception:
            pass
        return False
    claim = verdict["claim"]
    g1m = verdict["gate1"]["metrics"]
    record = {
        "title": f"Novel verified claim: {claim[:80]}",
        "abstract": claim,
        "discovery_type": "machine_verified_claim",
        "timestamp": _now_iso(),
        "source": "evolved_analysis",
        # Fix 1: persist the actual run_claim source so every emitted claim is
        # independently reproducible/verifiable (the 2026-07-12 record-8 audit
        # found the source was ephemeral -> claims were unverifiable).
        "program_source": verdict["source"],
        "verification": {
            "program_hash": verdict["program_hash"],
            "metric_name": "two_gate_claim",
            # real_data_result now carries the HELD-OUT metric as primary
            # 'effect'/'pvalue' plus the in-sample values for transparency (Fix 2).
            "real_data_result": g1m,
            "gate": {
                "gate1_real_data": "pass",
                "gate2_novelty": verdict["gate2"]["status"],
                "triviality": "pass",
                "consistency": "pass",
                "holdout": "pass",
                "bonferroni_pmax": verdict["gate1"]["bonferroni_pmax"],
                "family_size": verdict["gate1"]["family_size"],
            },
            "claim": claim,
            # Phase 2: the empty-context attack report travels with the claim.
            "fresh_attacker": attack,
            # Cross-model audit outcome travels beside it — including the
            # honest "not-configured" when no second-family endpoint exists.
            "second_judge": sj,
            # Fix 2: headline statistic is the held-out one (test split).
            "effect": g1m.get("effect"),
            "pvalue": g1m.get("pvalue"),
            "effect_insample": g1m.get("effect_insample"),
            "pvalue_insample": g1m.get("pvalue_insample"),
            "held_out_split": "test",
        },
    }
    try:
        EVOLVED_STORE.parent.mkdir(parents=True, exist_ok=True)
        data = _load_store_list()
        if not any(_is_dup_rec(r, verdict) for r in data):
            data.append(record)
            EVOLVED_STORE.write_text(json.dumps(data, indent=2))
            logger.info("[claim_search] ✅ EMITTED both-gate survivor: %s", claim[:70])
            verdict["emitted"], verdict["emit_reason"] = True, None
        else:
            verdict["emitted"], verdict["emit_reason"] = False, "duplicate"
    except Exception as e:
        logger.warning("[claim_search] emit failed: %s", e)
        verdict["emitted"], verdict["emit_reason"] = False, "store-write-failed"
    return bool(verdict.get("emitted"))


def _is_dup_rec(r, verdict: dict) -> bool:
    """Store-record-vs-verdict duplicate test (emit-write guard)."""
    rv = (r.get("verification") or {}) if isinstance(r, dict) else {}
    g1m = verdict["gate1"]["metrics"]
    nk = _finding_key(g1m.get("effect"), g1m.get("pvalue"))
    rk = _finding_key(rv.get("effect"), rv.get("pvalue"))
    if nk is not None and rk is not None:
        return rk == nk
    return rv.get("program_hash") == verdict["program_hash"]


def _now_iso() -> str:
    import datetime
    return datetime.datetime.now().isoformat()


# --------------------------------------------------------------------------- #
# F2: pilot-before-scale (cold-dataset episode early-stop)                     #
# --------------------------------------------------------------------------- #
def _dataset_gate1_history(name: str, window: int = PILOT_HISTORY_WINDOW) -> dict:
    """Gate-1 history for one dataset over its last ``window`` verdict rows.

    Defensive by design: never raises, returns zeros when the log is absent."""
    out = {"dataset": name, "window": window, "n_trials": 0, "n_gate1_pass": 0}
    try:
        if not VERDICT_LOG.exists():
            return out
        recs = []
        for line in VERDICT_LOG.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("dataset") == name:
                recs.append(rec)
        for rec in recs[-window:]:
            out["n_trials"] += 1
            if (rec.get("gate1") or {}).get("pass") is True:
                out["n_gate1_pass"] += 1
    except Exception as e:
        logger.warning("[claim_search] pilot history read failed: %s", e)
    return out


def _pilot_should_stop(pilot: dict):
    """Pure predicate: the reason the pilot says stop, or None to continue.

    Never stops when anything passed gate1 (alive — nothing can be emitted
    without a gate1 pass, so a pass means the lane is producing) or when any
    worker error occurred (a machine failure is not evidence about the
    dataset). Two stop reasons, kept distinct because their remedies differ:
    'degenerate-proposals' — the window burned on at most one distinct program
    (the proposer fell back to the parent verbatim); 'cold-dataset-no-gate1-
    pass' — genuinely distinct candidates and none passed on a cold dataset."""
    if pilot["gate1_pass"] > 0 or pilot["errors"] > 0:
        return None
    if pilot["trials"] + pilot["unchanged"] < pilot["window"]:
        return None
    if len(pilot["hashes"]) <= 1:
        return "degenerate-proposals"
    return "cold-dataset-no-gate1-pass"


def _pilot_stop(pilot: dict, reason: str, source: str, skipped: int) -> None:
    """Record the pilot decision and end the episode.

    A ledger NOTE, not a trial: a pilot decision is bookkeeping, not a
    statistical look, and kind='trial' would tighten the lifetime Bonferroni
    correction for nothing. The note carries what a reader needs to tell the
    three causes apart (bar too tight / dataset dead / degenerate proposer):
    distinct-program count, skip count, and the pmax in force."""
    detail = (f"pilot window {pilot['window']} exhausted with no gate1 pass: "
              f"{pilot['trials']} evaluated, {pilot['unchanged']} unchanged-"
              f"proposal skips, {len(pilot['hashes'])} distinct programs, "
              f"{pilot['errors']} worker errors")
    try:
        from .evidence_ledger import safe_append
        safe_append("note", "pilot-stop", dataset=source, reason=reason,
                    detail=detail, window=pilot["window"],
                    n_trials=pilot["trials"],
                    n_unchanged_skips=pilot["unchanged"],
                    n_distinct_programs=len(pilot["hashes"]),
                    n_gate1_errors=pilot["errors"],
                    skipped_steps=skipped,
                    bonferroni_pmax=bonferroni_pmax(PMAX),
                    history=pilot.get("history"))
    except Exception as e:
        logger.warning("[claim_search] pilot-stop ledger note failed: %s", e)
    logger.warning("[claim_search] 🛑 pilot-stop (%s) on %s — skipping %d "
                   "remaining step(s): %s", reason, source, skipped, detail)


def _arm_pilot(steps: int, pilot_steps: int, source: str):
    """F2 arming rule (extracted from main for testability).

    The pilot window arms only when it could bite: enough steps to outlive the
    window, a real data-lake source (the legacy path is the maintained sanity
    lane), and a COLD dataset — zero gate1 passes in its last
    PILOT_HISTORY_WINDOW verdict rows. Warm datasets and short runs return None
    (warm -> logged, not silent)."""
    if pilot_steps <= 0 or steps <= pilot_steps or source == "legacy":
        return None
    hist = _dataset_gate1_history(source)
    if hist["n_gate1_pass"] == 0:
        logger.info("[claim_search] pilot armed for cold dataset %s "
                    "(0 gate1 passes / %d trials in its last %d rows)",
                    source, hist["n_trials"], hist["window"])
        return {"window": pilot_steps, "trials": 0, "gate1_pass": 0,
                "errors": 0, "unchanged": 0, "hashes": set(),
                "history": hist}
    logger.info("[claim_search] pilot not armed: %s is warm "
                "(%d gate1 passes / %d trials in its last %d rows)",
                source, hist["n_gate1_pass"], hist["n_trials"], hist["window"])
    return None


def _evolve_steps(proposer, parent: str, parent_metrics: dict, steps: int,
                  source: str, run_gate2: bool = True,
                  propose_retries: int = 3, pilot: dict = None) -> None:
    """The LLM-proposal step loop (extracted from main for testability).

    Per step: propose (re-proposing until the candidate computes on df_train),
    evaluate through both gates, EMIT, then append the verdict log — in that
    order, so the log line records the promotion outcome (``emitted`` /
    ``emit_reason`` / ``fresh_attacker`` / ``second_judge``), not just the
    gate outcomes. ``pilot`` is the armed F2 cold-dataset window or None."""
    for i in range(steps):
        # Split-discipline fix: re-propose until the candidate computes on df_train
        # (not df_eval alone), so the holdout-distinctness gate does not reject it
        # and we don't waste a sandbox run on split-incorrect code.
        child, info = None, {}
        for _attempt in range(max(1, propose_retries)):
            cand, _spec, info = proposer.propose(
                parent, parent_metrics, None, [], context_level="rich")
            if not cand:
                break
            ok, why = claim_uses_train_split(cand)
            if ok:
                child = cand
                break
            logger.info("[claim_search] step %d attempt %d: %s; re-proposing",
                        i, _attempt, why)
        if not child:
            logger.info("[claim_search] step %d: no split-correct proposal (%s)",
                        i, info.get("error", "all attempts computed on df_eval"))
            continue
        if info.get("mode") == "unchanged":
            # The proposer fell back to the parent verbatim (unparseable LLM
            # response): re-evaluating an identical program is pure spend —
            # the family counter would tighten on a no-op and the verdict row
            # would say nothing the seed row has not already said. Skip the
            # evaluation; the pilot window counts the degeneracy.
            logger.info("[claim_search] step %d: proposal unchanged from parent "
                        "(mode=unchanged) — skipping evaluation", i)
            if pilot is not None and i < pilot["window"]:
                pilot["unchanged"] += 1
                reason = _pilot_should_stop(pilot)
                if reason:
                    _pilot_stop(pilot, reason, source=source,
                                skipped=steps - (i + 1))
                    return
            continue
        v = two_gate_eval(child, run_gate2=run_gate2, source=source)
        logger.info("[claim_search] step %d claim: %s", i, (v["claim"] or "")[:70])
        _log_verdict(v, prefix=f"  step {i}: ")
        _emit(v)
        _append_verdict_log(v, label=f"step{i}")
        # adopt as parent if it passed gate 1 (a real effect to build on)
        if v["gate1"]["pass"]:
            parent, parent_metrics = child, v["gate1"]["metrics"]
        if pilot is not None and i < pilot["window"]:
            pilot["trials"] += 1
            if v["gate1"]["pass"]:
                pilot["gate1_pass"] += 1
            if (v["gate1"].get("metrics") or {}).get("error"):
                pilot["errors"] += 1
            pilot["hashes"].add(v.get("program_hash"))
            reason = _pilot_should_stop(pilot)
            if reason:
                _pilot_stop(pilot, reason, source=source,
                            skipped=steps - (i + 1))
                return


# --------------------------------------------------------------------------- #
# main                                                                         #
# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser(description="Phase-2 two-gate claim search")
    ap.add_argument("--steps", type=int, default=5,
                    help="LLM-proposed candidates to try (needs token)")
    ap.add_argument("--seed-only", action="store_true",
                    help="just run the deterministic seed through both gates and exit")
    ap.add_argument("--no-gate2", action="store_true",
                    help="run Gate 1 only (skip network/novelty)")
    ap.add_argument("--data-source", default="legacy",
                    help="data-lake dataset to mine (Sub-project C). Default "
                         "'legacy' (SDSS photo-z via real_data.py). Use "
                         "--list-sources to see available datasets.")
    ap.add_argument("--list-sources", action="store_true",
                    help="list available data sources and exit")
    ap.add_argument("--propose-retries", type=int, default=3,
                    help="max re-proposals per step when the candidate computes "
                         "on df_eval instead of df_train (split-discipline fix)")
    ap.add_argument("--pilot-steps", type=int,
                    default=int(os.environ.get("ASTRA_PILOT_STEPS",
                                               str(PILOT_DEFAULT_STEPS))),
                    help="F2 pilot-before-scale: on a dataset with no gate1 "
                         "pass in its recent verdict history, stop the episode "
                         "early when the first K steps show nothing alive "
                         "(0 disables the pilot window)")
    ap.add_argument("--no-pilot", action="store_true",
                    help="skip the F2 cold-dataset pilot window; the skip is "
                         "recorded as a ledger note (the documented-reason "
                         "skip path)")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    # Sub-project C: resolve the data source. 'legacy' leaves behaviour unchanged.
    source = "legacy"
    task_system = TASK_SYSTEM
    if args.list_sources:
        from .data_lake import list_datasets
        print("  legacy (default)   SDSS u,g,r,i,z + z_spec galaxies (real_data.py)")
        for ds in list_datasets():
            cached = "cached" if ds.cache_path().exists() else "NOT-cached"
            risk = "SKIP(textbook)" if ds.textbook_risk == "high" else "mine"
            print(f"  {ds.name:20s} [{cached}/{risk}]  {', '.join(ds.columns)}")
        return
    if args.data_source and args.data_source != "legacy":
        from .data_lake import fetch_and_cache, task_system_for, get_dataset
        if get_dataset(args.data_source) is None:
            logger.warning("[claim_search] unknown --data-source %r; "
                           "falling back to legacy", args.data_source)
        else:
            source = args.data_source
            fetch_and_cache(source)  # pre-fetch OUTSIDE the sandbox (network)
            ts = task_system_for(source)
            if ts:
                task_system = ts
            logger.info("[claim_search] data source: %s", source)

    # --- F2 pilot arming (zero spend; before the seed sanity) ---
    pilot = None
    if args.no_pilot:
        try:
            from .evidence_ledger import safe_append
            safe_append("note", "pilot-skipped", dataset=source,
                        detail="--no-pilot: cold-dataset pilot window skipped "
                               "by explicit flag (documented-reason skip path)")
        except Exception:
            pass
    else:
        pilot = _arm_pilot(args.steps, args.pilot_steps, source)

    logger.info("[claim_search] === seed claim through both gates (sanity) ===")
    verdict = two_gate_eval(NAIVE_CLAIM_SEED, run_gate2=not args.no_gate2,
                            source=source)
    _log_verdict(verdict)
    _append_verdict_log(verdict, label="seed")
    # The seed is a KNOWN effect: expect gate1 pass + gate2 'known' (no emit).
    if verdict["both_pass"]:
        logger.warning("[claim_search] seed unexpectedly passed both gates — "
                       "novelty gate may be too permissive")
    elif not verdict["gate1"]["pass"]:
        # Canary (2026-09-08): the seed is a known gate1-passer on real data;
        # if it fails gate1 the data path itself is broken and every downstream
        # "not significant" verdict — and any pilot-stop this run — is an
        # artefact of that, not of the dataset or the novelty search.
        logger.warning("[claim_search] seed sanity: seed FAILED gate1 (%s) — "
                       "expected a pass; investigate the data path before "
                       "reading any pilot-stop this run",
                       verdict["gate1"].get("reason"))

    if args.seed_only or not os.environ.get("ANTHROPIC_AUTH_TOKEN"):
        if not args.seed_only:
            logger.info("[claim_search] no LLM token — seed-only run done")
        return

    logger.info("[claim_search] === evolving %d LLM-proposed claim(s) ===",
                args.steps)
    try:
        proposer = LLMProposer(task_system=task_system, entry_point=ENTRY_POINT)
    except Exception as e:
        logger.warning("[claim_search] LLM proposer unavailable: %s", e)
        return
    _evolve_steps(proposer, NAIVE_CLAIM_SEED, verdict["gate1"]["metrics"],
                  steps=args.steps, source=source,
                  run_gate2=not args.no_gate2,
                  propose_retries=args.propose_retries, pilot=pilot)


def _log_verdict(v: dict, prefix: str = ""):
    logger.info("%sgate1: %s", prefix, v["gate1"]["reason"])
    g2 = v["gate2"]
    if g2:
        logger.info("%sgate2: %s (%s) n=%s", prefix, g2.get("status"),
                    (g2.get("reasoning") or "")[:90], g2.get("n_retrieved"))
    logger.info("%s=> both_pass=%s", prefix, v["both_pass"])


def _append_verdict_log(verdict: dict, label: str = "") -> None:
    """Append one compact JSONL line recording this candidate's gate outcomes.

    Observability for the autonomous claim search: the supervisor runs this
    module as a subprocess with stdout/stderr -> DEVNULL, so the per-candidate
    gate verdicts are otherwise unrecoverable (the 2026-07-14 diagnostic had to
    infer the failure funnel indirectly from the novelty cache). This writes the
    verdict to a structured file independent of stdout capture, so we can see
    WHERE candidates die (Gate-1 significance / triviality / consistency /
    holdout / Gate-2 novelty).

    Defensive by design: a logging failure must NEVER break the discovery loop
    or affect emission/verification, so the whole body is wrapped and never
    raises. The file rotates at VERDICT_LOG_CAP_BYTES to avoid unbounded growth.
    """
    try:
        g1 = verdict.get("gate1") or {}
        g2 = verdict.get("gate2") or {}
        g1m = g1.get("metrics") or {}
        line = json.dumps({
            "ts": _now_iso(),
            "label": label,
            "dataset": verdict.get("dataset"),
            "claim": (verdict.get("claim") or "")[:200],
            "program_hash": verdict.get("program_hash"),
            "both_pass": verdict.get("both_pass"),
            # promotion outcome (written back by _emit, which the caller runs
            # BEFORE this append): what actually happened at the chokepoint —
            # emitted, or the exact reason it was not (duplicate / attacker /
            # second-judge / store failure). Null on paths that never reach
            # _emit (the seed row, log-only replays).
            "emitted": verdict.get("emitted"),
            "emit_reason": verdict.get("emit_reason"),
            "fresh_attacker": {
                "disposition": (verdict.get("fresh_attacker") or {}).get(
                    "disposition"),
                "detail": ((verdict.get("fresh_attacker") or {}).get("detail")
                           or "")[:160]},
            "second_judge": {
                "status": (verdict.get("second_judge") or {}).get("status"),
                "model": (verdict.get("second_judge") or {}).get("model"),
                "n_retrieved": (verdict.get("second_judge") or {}).get(
                    "n_retrieved"),
                "confidence": (verdict.get("second_judge") or {}).get(
                    "confidence"),
                "reasoning": ((verdict.get("second_judge") or {}).get(
                    "reasoning") or "")[:160]},
            # provenance (Egent): which model judged, with what sampling, and
            # how many times this claim's novelty verdict has been revised
            "llm": {"judge_model": os.environ.get("ASTRA_LLM_MODEL",
                                                  "claude-sonnet-5-20250929"),
                    "judge_max_tokens": 300,
                    "judge_temperature": "api-default",
                    "novelty_revision": verdict.get("novelty_revision", 0)},
            "gate1": {"pass": g1.get("pass"),
                      "effect": g1m.get("effect"),
                      "pvalue": g1m.get("pvalue"),
                      "pmax": g1.get("bonferroni_pmax"),
                      "family_size": g1.get("family_size"),
                      "reason": (g1.get("reason") or "")[:160]},
            "triviality": (verdict.get("triviality") or {}).get("pass"),
            "consistency": (verdict.get("consistency") or {}).get("pass"),
            "holdout": (verdict.get("holdout") or {}).get("pass"),
            "circularity": (verdict.get("circularity") or {}).get("pass"),
            "precision": (verdict.get("precision") or {}).get("pass"),
            "geometry": (verdict.get("geometry") or {}).get("pass"),
            "gate2": {"status": g2.get("status"), "pass": g2.get("pass"),
                      "n_retrieved": g2.get("n_retrieved"),
                      "confidence": g2.get("confidence"),
                      "from_cache": g2.get("from_cache"),
                      "reasoning": (g2.get("reasoning") or "")[:160]},
            # token-free ALS concept-graph prior (crowding of the claim's
            # concept combination); ranking signal only — never a gate
            "concept_prior": {
                "crowding": (verdict.get("concept_prior") or {}).get("crowding"),
                "n_concepts": (verdict.get("concept_prior") or {}).get("n"),
                "concepts": [c.get("concept") for c in
                             (verdict.get("concept_prior") or {}).get(
                                 "concepts", [])][:6]},
        }, default=str)
        VERDICT_LOG.parent.mkdir(parents=True, exist_ok=True)
        try:
            if (VERDICT_LOG.exists()
                    and VERDICT_LOG.stat().st_size > VERDICT_LOG_CAP_BYTES):
                rot = VERDICT_LOG.with_suffix(".jsonl.1")
                try:
                    rot.unlink()
                except OSError:
                    pass
                VERDICT_LOG.rename(rot)
        except OSError:
            pass
        with VERDICT_LOG.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except Exception as e:  # never break the loop over a logging failure
        logger.warning("[claim_search] verdict-log append failed: %s", e)


if __name__ == "__main__":
    main()
