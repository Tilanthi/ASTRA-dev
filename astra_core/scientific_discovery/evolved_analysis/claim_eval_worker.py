"""claim_eval_worker.py — isolated subprocess that runs ONE claim candidate's
real-data test (Gate 1 of the two-gate EVALUATE).

Invoked as:
    python -m evolved_analysis.claim_eval_worker <source_file> [seed]

It loads the candidate (a module-level CLAIM + a ``run_claim(df_train, df_eval)``
function), runs it on REAL SDSS data, and prints ONE line of JSON to stdout:
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
    try:
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

        result = fn(splits["train"], splits["eval"])
        if not isinstance(result, dict):
            raise RuntimeError("run_claim must return a dict")
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
