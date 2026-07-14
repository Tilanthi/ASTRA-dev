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
import subprocess
import sys
import tempfile
from pathlib import Path

from .claim_task import (NAIVE_CLAIM_SEED, TASK_SYSTEM, ENTRY_POINT,
                         parse_claim, gate1_significant, PMAX)
from .claim_gates import (triviality_check, consistency_check,
                          holdout_distinct_check, claim_uses_train_split,
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
try:
    import shutil
    _SANDBOX_EXEC = shutil.which("sandbox-exec")
except Exception:
    _SANDBOX_EXEC = None
_PROFILE = Path(__file__).resolve().parent / "astra_worker.sb"


def _program_hash(src: str) -> str:
    return hashlib.sha1(src.encode()).hexdigest()[:10]


# --------------------------------------------------------------------------- #
# Gate 1: sandboxed real-data test                                             #
# --------------------------------------------------------------------------- #
def gate1_run(src: str, seed: int = 42, timeout: float = 90.0,
              source: str = "legacy") -> dict:
    """Run the candidate's run_claim in a sandboxed subprocess on real data.

    ``source`` selects the dataset: 'legacy' (default, SDSS photo-z via
    real_data.py) or a data-lake dataset name (data_lake.py, Sub-project C).
    The worker only reads a cached CSV — it never fetches."""
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
    g1_pass, g1_reason = gate1_significant(g1_metrics, pmax=corrected_pmax)

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
        "gate2": None,
        "both_pass": False,
        "dataset": source,
    }

    if not (g1_pass and triv_ok and cons_ok and hold_ok):
        return result  # significance / triviality / consistency / holdout stop here

    if run_gate2:
        try:
            from .novelty_gate import check_novelty
            nr = check_novelty(claim)
            result["gate2"] = {
                "pass": nr.novel, "status": nr.status, "n_retrieved": nr.n_retrieved,
                "reasoning": nr.reasoning[:200],
                "entailed_by": nr.entailed_by.title[:80] if nr.entailed_by else None,
            }
        except Exception as e:
            # Gate-2 failure is conservative: do NOT promote as novel.
            result["gate2"] = {"pass": False, "status": "gate2-error",
                               "reasoning": f"{type(e).__name__}: {str(e)[:120]}"}
    else:
        result["gate2"] = {"pass": None, "status": "skipped"}

    result["both_pass"] = bool(
        g1_pass and triv_ok and cons_ok and hold_ok and result["gate2"]
        and result["gate2"]["pass"] is True)
    return result


# --------------------------------------------------------------------------- #
# emit (only both-gate survivors, through the chokepoint-compatible shape)     #
# --------------------------------------------------------------------------- #
def _emit(verdict: dict) -> None:
    """Append a both-gate survivor to evolved_discoveries.json (bare list)."""
    if not verdict["both_pass"]:
        return
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
        data = json.loads(EVOLVED_STORE.read_text()) if EVOLVED_STORE.exists() else []
        if not isinstance(data, list):
            data = []
        if not any((r.get("verification") or {}).get("program_hash")
                   == verdict["program_hash"] for r in data if isinstance(r, dict)):
            data.append(record)
            EVOLVED_STORE.write_text(json.dumps(data, indent=2))
            logger.info("[claim_search] ✅ EMITTED both-gate survivor: %s", claim[:70])
    except Exception as e:
        logger.warning("[claim_search] emit failed: %s", e)


def _now_iso() -> str:
    import datetime
    return datetime.datetime.now().isoformat()


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

    logger.info("[claim_search] === seed claim through both gates (sanity) ===")
    verdict = two_gate_eval(NAIVE_CLAIM_SEED, run_gate2=not args.no_gate2,
                            source=source)
    _log_verdict(verdict)
    _append_verdict_log(verdict, label="seed")
    # The seed is a KNOWN effect: expect gate1 pass + gate2 'known' (no emit).
    if verdict["both_pass"]:
        logger.warning("[claim_search] seed unexpectedly passed both gates — "
                       "novelty gate may be too permissive")

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
    parent = NAIVE_CLAIM_SEED
    parent_metrics = verdict["gate1"]["metrics"]
    for i in range(args.steps):
        # Split-discipline fix: re-propose until the candidate computes on df_train
        # (not df_eval alone), so the holdout-distinctness gate does not reject it
        # and we don't waste a sandbox run on split-incorrect code.
        child, info = None, {}
        for _attempt in range(max(1, args.propose_retries)):
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
        v = two_gate_eval(child, run_gate2=not args.no_gate2, source=source)
        logger.info("[claim_search] step %d claim: %s", i, (v["claim"] or "")[:70])
        _log_verdict(v, prefix=f"  step {i}: ")
        _append_verdict_log(v, label=f"step{i}")
        _emit(v)
        # adopt as parent if it passed gate 1 (a real effect to build on)
        if v["gate1"]["pass"]:
            parent, parent_metrics = child, v["gate1"]["metrics"]


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
            "gate1": {"pass": g1.get("pass"),
                      "effect": g1m.get("effect"),
                      "pvalue": g1m.get("pvalue"),
                      "reason": (g1.get("reason") or "")[:160]},
            "triviality": (verdict.get("triviality") or {}).get("pass"),
            "consistency": (verdict.get("consistency") or {}).get("pass"),
            "holdout": (verdict.get("holdout") or {}).get("pass"),
            "gate2": {"status": g2.get("status"), "pass": g2.get("pass"),
                      "n_retrieved": g2.get("n_retrieved"),
                      "reasoning": (g2.get("reasoning") or "")[:160]},
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
