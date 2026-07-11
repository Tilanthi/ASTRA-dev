"""narrate.py — turn a machine-verified finding into an ASTRA discovery record.

narrate_with_stan(): delegates the title+abstract to ASTRA's STAN system.answer()
(in a subprocess, auto-start patched, timeout-protected) — STAN is good at
scientific prose. Falls back to template_narrate() if STAN is unavailable/slow.

Both return the ASTRA-schema fields {title, abstract, discovery_type}; the caller
adds timestamp + verification and persists via discovery_emit.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
WORKER = "astra_core.scientific_discovery.evolved_analysis.stan_narrate_worker"


def template_narrate(facts: dict) -> dict:
    """Honest, factual title+abstract built straight from the verified numbers."""
    task = facts["task"]
    title = (f"Evolved {task} pipeline ({facts.get('method_family','ML')}) — "
             f"{facts['metric_name']}={facts['metric_value']}")
    eta = facts.get("eta")
    eta_clause = f", outlier fraction {eta}" if eta is not None else ""
    abstract = (
        f"An analysis pipeline for {task} ({facts.get('method','an evolvable ML model')}) "
        f"was evolved and machine-graded on REAL {facts['data_source']}: "
        f"{facts['metric_name']}={facts['metric_value']} on {facts['n_eval']} held-out eval "
        f"objects (independent held-out TEST={facts['held_out_value']}{eta_clause}), "
        f"cross-validated (split {facts['n_train']}/{facts['n_eval']}/{facts['n_test']} "
        f"train/eval/test). Verified by code execution on real archival data, not by "
        f"LLM self-judgment — the {facts['metric_name']} value is computed, not asserted.")
    return {"title": title, "abstract": abstract,
            "discovery_type": "machine_verified_analysis", "stan_used": False}


def narrate_with_stan(facts: dict, timeout: float = 150.0,
                      python: str | None = None) -> dict:
    """Try STAN narration; fall back to the template. Never raises."""
    py = python or sys.executable
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tf:
        json.dump(facts, tf); tf.flush(); fp = tf.name
    try:
        env = {**os.environ, "PYTHONPATH": str(REPO_ROOT)}
        proc = subprocess.run([py, "-m", WORKER, fp], capture_output=True,
                              text=True, timeout=timeout, cwd=str(REPO_ROOT), env=env)
    except subprocess.TimeoutExpired:
        return _with_fallback(template_narrate(facts), "stan_timeout")
    except Exception as e:
        return _with_fallback(template_narrate(facts), f"spawn:{type(e).__name__}")
    finally:
        try: Path(fp).unlink()
        except OSError: pass
    out = proc.stdout.strip().splitlines()
    if not out:
        return _with_fallback(template_narrate(facts), "no_stdout")
    try:
        r = json.loads(out[-1])
    except json.JSONDecodeError:
        return _with_fallback(template_narrate(facts), "unparseable")
    if not r.get("stan_used") or not r.get("title"):
        # STAN failed inside the worker -> use template content, keep the reason
        fb = template_narrate(facts)
        fb["stan_error"] = r.get("error", "no_title")
        return fb
    r.setdefault("discovery_type", "machine_verified_analysis")
    return r


def _with_fallback(template: dict, reason: str) -> dict:
    template["stan_error"] = reason
    return template
