"""claim_eval_worker.py — isolated subprocess that runs ONE claim candidate's
real-data test (Gate 1 of the two-gate EVALUATE).

Invoked as:
    python -m evolved_analysis.claim_eval_worker <source_file> [seed] [data_source]

An optional third arg ``data_source`` selects a data-lake dataset
(data_lake.py, Sub-project C); omit it (or pass 'legacy') to use the default
SDSS photo-z sample via real_data.py. The worker only ever READS a cached CSV —
it never fetches (no network from the sandbox); caches are populated by
data_lake.fetch_and_cache() outside the sandbox.

It loads the candidate (a module-level CLAIM + a ``run_claim(df_train, df_eval)``
function), runs it on REAL data, and prints ONE line of JSON to stdout:
    {"effect": ..., "pvalue": ..., "effect_type": ..., "summary": ..., "claim": ...}

Defence-in-depth (identical to eval_worker): ``resource`` caps + the AST safety
gate in safety.py + (when launched via sandbox-exec) the no-network profile. The
claim string is echoed back so the orchestrator can run Gate 2 (novelty) on it.
"""
from __future__ import annotations

import json
import resource
import sys
import traceback
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import numpy as np  # noqa: E402
from .real_data import load_split  # noqa: E402
from .claim_task import parse_claim, ENTRY_POINT  # noqa: E402

# Resource caps (defence-in-depth). RLIMIT_AS is skipped on macOS (premature kill).
try:
    resource.setrlimit(resource.RLIMIT_CPU, (60, 60))
except Exception:
    pass
try:
    resource.setrlimit(resource.RLIMIT_FSIZE, (512 * 1024 * 1024, 512 * 1024 * 1024))
except Exception:
    pass
try:
    resource.setrlimit(resource.RLIMIT_NPROC, (64, 64))
except Exception:
    pass


def main():
    src_path = sys.argv[1]
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 42
    source = sys.argv[3] if len(sys.argv) > 3 else "legacy"
    try:
        if source and source != "legacy":
            # Sub-project C: read a cached data-lake dataset (file read only,
            # never fetches — the sandbox has no network).
            from .data_lake import load_split as _lake_split
            splits = _lake_split(source, seed=seed)
        else:
            splits = load_split(seed=seed)
        src = Path(src_path).read_text()

        # AST safety gate BEFORE exec (catches os/subprocess/open/eval/...).
        from .safety import check_source
        ok, reason = check_source(src, entry_point=ENTRY_POINT)
        if not ok:
            print(json.dumps({"effect": 0.0, "pvalue": 1.0, "error": f"blocked:{reason}"}))
            return

        ns: dict = {}
        exec(compile(src, src_path, "exec"), ns)
        fn = ns.get(ENTRY_POINT)
        if not callable(fn):
            raise RuntimeError(f"source does not define {ENTRY_POINT}(df_train, df_eval)")

        def _call(split_first, split_second, label):
            """Run the claim fn on one split pair; return its dict or an error dict."""
            try:
                r = fn(splits[split_first], splits[split_second])
            except Exception as e:  # claim code fault on this split -> fail closed
                return {"effect": 0.0, "pvalue": 1.0,
                        "error": f"{label}:{type(e).__name__}:{str(e)[:120]}"}
            if not isinstance(r, dict):
                return {"effect": 0.0, "pvalue": 1.0,
                        "error": f"{label}:non-dict return"}
            return r

        # Fix 2 — the HEADLINE statistic is the held-out one. The search used to
        # report run_claim on df_train only (in-sample); df_eval/df_test were
        # passed but ignored. We now evaluate twice:
        #   * insample = fn(train, eval)  -> what the search effectively saw
        #   * holdout  = fn(test,  eval)  -> genuinely unseen galaxies (test)
        # Most claims compute on their FIRST arg (the seed does `df = df_train`),
        # so fn(test, ...) computes the statistic on the untouched test split.
        insample = _call("train", "eval", "insample")
        holdout = _call("test", "eval", "holdout")

        result = dict(holdout)  # hold-out is primary: effect / pvalue / summary
        if "error" not in result:
            result["effect_insample"] = float(insample.get("effect", 0.0))
            result["pvalue_insample"] = float(insample.get("pvalue", 1.0))
            if insample.get("effect_type"):
                result["effect_type_insample"] = insample.get("effect_type")
        # echo the claim text back for Gate 2
        result.setdefault("claim", parse_claim(src) or "")
        # sanity: numeric effect/pvalue
        for k in ("effect", "pvalue"):
            if k in result:
                result[k] = float(result[k])
        print(json.dumps(result))
    except Exception as e:
        print(json.dumps({
            "effect": 0.0, "pvalue": 1.0,
            "error": f"{type(e).__name__}: {str(e)[:160]}",
            "trace": traceback.format_exc(limit=2),
        }))


if __name__ == "__main__":
    main()
