"""discovery_emit.py — emit machine-verified findings as ASTRA-schema discoveries.

When the evolutionary loop produces a program that passes its machine-graded
metric on REAL held-out data, this writes an ASTRA discovery record in ASTRA's
{title, abstract, discovery_type, timestamp} schema — PLUS a `verification` field
carrying the machine-computed metric. That verification field is the whole point:
it is what the current ASTRA discovery store LACKS (its "genuine discoveries" are
unverified textbook prose). Every record here is backed by code execution on real
archival data.

Records go to ~/.astra_persistent/evolved_discoveries.json (a SEPARATE file from
the live genuine_discoveries.json that the running auto-start service writes) to
avoid write races. A merge_into_genuine() helper is provided for when the service
is stopped.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from pathlib import Path
from typing import Any, Dict

from .narrate import narrate_with_stan, template_narrate

PERSIST = Path.home() / ".astra_persistent"
STORE = PERSIST / "evolved_discoveries.json"
GENUINE = PERSIST / "genuine_discoveries.json"

_FAMILY = [("GradientBoosting", re.compile(r"GradientBoosting|XGBoost|HistGradient")),
           ("RandomForest", re.compile(r"RandomForest|ExtraTrees")),
           ("Ridge", re.compile(r"\bRidge\b")), ("Lasso", re.compile(r"\bLasso\b")),
           ("Linear", re.compile(r"LinearRegression")),
           (" LombScargle", re.compile(r"LombScargle|astropy\.periodogram")),
           ("Majority", re.compile(r"value_counts\(\)\.idxmax"))]


def sniff_family(src: str) -> str:
    for name, pat in _FAMILY:
        if pat.search(src):
            return name.strip()
    return "ML"


def program_hash(src: str) -> str:
    return hashlib.sha1(src.encode()).hexdigest()[:12]


def _metric_from(metrics: dict, task: str) -> tuple[str, float]:
    if task == "classification":
        return "balanced_accuracy", float(metrics.get("balanced_accuracy", 0.0))
    return "sigma_NMAD", float(metrics.get("sigma_nmad", 0.0))


def emit_verified_discovery(*, task: str, program_source: str, eval_metrics: dict,
                            held_out_metrics: dict, data_source: str,
                            n_train: int, n_eval: int, n_test: int,
                            use_stan: bool = True) -> dict:
    """Narrate + persist one verified discovery. Returns the record."""
    metric_name, metric_value = _metric_from(eval_metrics, task)
    _, held_out_value = _metric_from(held_out_metrics, task)
    eta = eval_metrics.get("eta") or held_out_metrics.get("eta")
    family = sniff_family(program_source)
    facts = {"task": task, "method": f"{family}-class pipeline (evolved)",
             "method_family": family, "metric_name": metric_name,
             "metric_value": round(metric_value, 4),
             "held_out_value": round(held_out_value, 4),
             "eta": round(eta, 4) if eta is not None else None,
             "n_train": n_train, "n_eval": n_eval, "n_test": n_test,
             "data_source": data_source}
    narrated = narrate_with_stan(facts) if use_stan else template_narrate(facts)

    record = {
        "title": narrated["title"],
        "abstract": narrated["abstract"],
        "discovery_type": narrated.get("discovery_type", "machine_verified_analysis"),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "verification": {
            "by": "code execution on real archival data (NOT LLM self-judgment)",
            "metric_name": metric_name,
            "eval_value": round(metric_value, 4),
            "held_out_test_value": round(held_out_value, 4),
            "eta": round(eta, 4) if eta is not None else None,
            "cv_sigma_std": eval_metrics.get("cv_sigma_std"),
            "n_train": n_train, "n_eval": n_eval, "n_test": n_test,
            "data_source": data_source, "program_hash": program_hash(program_source),
            "stan_narrated": bool(narrated.get("stan_used")),
            "stan_error": narrated.get("stan_error"),
        },
        "program_source": program_source,
    }
    _append(record)
    return record


def _append(record: dict) -> None:
    PERSIST.mkdir(parents=True, exist_ok=True)
    data = json.loads(STORE.read_text()) if STORE.exists() else []
    data.append(record)
    STORE.write_text(json.dumps(data, indent=2))


def list_discoveries() -> list[dict]:
    return json.loads(STORE.read_text()) if STORE.exists() else []


def merge_into_genuine(dry_run: bool = True) -> dict:
    """Fold evolved_discoveries into the live genuine_discoveries.json store.
    Defaults to dry_run (the service may be writing that file). Returns a plan."""
    plan = {"would_add": 0, "reason": "dry_run" if dry_run else "applied"}
    if not STORE.exists():
        plan["reason"] = "no evolved_discoveries.json"
        return plan
    new = json.loads(STORE.read_text())
    plan["would_add"] = len(new)
    if dry_run:
        return plan
    cur = json.loads(GENUINE.read_text()) if GENUINE.exists() else {}
    if not isinstance(cur, dict):
        cur = {}
    for r in new:
        cur[f"evolved_{r['verification']['program_hash']}_{r['timestamp']}"] = {
            k: r[k] for k in ("title", "abstract", "discovery_type", "timestamp")}
    GENUINE.write_text(json.dumps(cur, indent=2))
    plan["reason"] = "applied"
    return plan


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--merge-genuine", action="store_true",
                    help="fold evolved_discoveries into genuine_discoveries.json")
    ap.add_argument("--apply", action="store_true",
                    help="with --merge-genuine: actually write (default dry-run)")
    args = ap.parse_args()
    if args.merge_genuine:
        print(json.dumps(merge_into_genuine(dry_run=not args.apply), indent=2)); return
    for r in list_discoveries():
        v = r.get("verification", {})
        print(f"- [{r.get('timestamp','?')}] {r.get('title','')}")
        print(f"    {v.get('metric_name')}: eval={v.get('eval_value')} "
              f"TEST={v.get('held_out_test_value')} (n={v.get('n_test')}) "
              f"data={v.get('data_source')} stan={v.get('stan_narrated')}")


if __name__ == "__main__":
    main()
