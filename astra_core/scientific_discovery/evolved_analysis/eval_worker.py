"""eval_worker.py — isolated subprocess that executes one candidate program.

Invoked by the evaluator as:
    python -m evolved_analysis.eval_worker <source_file> [seed] [split]

It loads the program source, calls estimate_redshift(df_train, df_eval) on REAL
SDSS data, computes the photo-z metrics on the requested split (eval by default;
'train' or 'test' for final reporting), and prints ONE line of JSON to stdout.

Runs in its own process so that LLM-generated code which hangs, crashes, or
allocates wildly is contained and can be hard-killed on timeout. It never writes
mock data and never calls out to the network.
"""
from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import numpy as np  # noqa: E402
from .real_data import load_split  # noqa: E402


def kfold_indices(n: int, K: int, seed: int):
    """Deterministic K-fold partition of [0,n). Returns list of K index arrays."""
    rng = np.random.default_rng(seed)
    perm = rng.permutation(n)
    return [perm[i::K] for i in range(K)]


def run_cv(fn, pool_df: "pandas.DataFrame", K: int, seed: int,
           only_fold: int = None) -> dict:
    """Out-of-fold CV over pool_df. For each fold, train on the other K-1 folds
    and predict the held-out fold; accumulate out-of-fold predictions for the
    whole pool, then compute metrics. If only_fold is set, report just that fold
    (used as a cheap cascade stage-1 probe)."""
    n = len(pool_df)
    folds = kfold_indices(n, K, seed)
    if only_fold is not None:
        val_idx = folds[only_fold]
        tr_idx = np.concatenate([folds[j] for j in range(K) if j != only_fold])
        tr = pool_df.iloc[tr_idx].reset_index(drop=True)
        val = pool_df.iloc[val_idx].reset_index(drop=True)
        pred = np.asarray(fn(tr, val), dtype=float)
        return metrics(pred, val["z_spec"].to_numpy(float))
    # full out-of-fold
    ztrue = np.zeros(n); pred = np.zeros(n)
    for i in range(K):
        val_idx = folds[i]
        tr_idx = np.concatenate([folds[j] for j in range(K) if j != i])
        tr = pool_df.iloc[tr_idx].reset_index(drop=True)
        val = pool_df.iloc[val_idx].reset_index(drop=True)
        p = np.asarray(fn(tr, val), dtype=float)
        pred[val_idx] = p
        ztrue[val_idx] = val["z_spec"].to_numpy(float)
    m = metrics(pred, ztrue)
    # per-fold spread (stability signal for selection)
    fold_sigmas = []
    for i in range(K):
        vi = folds[i]
        fold_sigmas.append(float(1.4826 * np.median(np.abs(pred[vi] - ztrue[vi]))))
    m["cv_sigma_std"] = float(np.std(fold_sigmas))
    m["cv_K"] = K
    return m


def metrics(pred: np.ndarray, z_true: np.ndarray) -> dict:
    """Photo-z metrics + a coarse residual error profile (binned in z_true).

    The binned profile is the 'rendered evaluation result' fed back to the LLM
    proposer (AlphaEvolve §1.1): it tells the proposer WHERE the current program
    is systematically wrong, not just an aggregate score."""
    delta = pred - z_true
    out = {
        "sigma_nmad": float(1.4826 * np.median(np.abs(delta))),
        "eta": float(np.mean(np.abs(delta) / (1.0 + z_true) > 0.15)),
        "bias": float(np.median(delta)),
    }
    # 4 quantile bins in z_true; per-bin median residual + count + bin centre
    qs = np.quantile(z_true, [0.25, 0.5, 0.75])
    edges = [z_true.min(), *qs, z_true.max()]
    bins = []
    for i in range(4):
        lo, hi = edges[i], edges[i + 1]
        mask = (z_true >= lo) & (z_true <= hi if i == 3 else z_true < hi)
        if mask.sum() > 0:
            bins.append({
                "z": round(float(0.5 * (lo + hi)), 3),
                "n": int(mask.sum()),
                "med_dz": round(float(np.median(delta[mask])), 4),
            })
    out["profile"] = bins
    return out


def main():
    # Defence-in-depth layer 2: resource caps. Applied before ANY candidate work
    # so that a runaway loop / fork-bomb / giant-file write is bounded by the OS
    # even if the AST gate and sandbox somehow miss it. Each is best-effort:
    # macOS rlimits differ subtly from Linux, so failures are swallowed rather
    # than aborting the worker. RLIMIT_AS is intentionally NOT set — on macOS it
    # can kill the process prematurely during normal numpy/sklearn operation.
    import resource
    try:
        resource.setrlimit(resource.RLIMIT_CPU, (60, 60))            # 60s CPU
    except Exception:
        pass
    try:
        resource.setrlimit(resource.RLIMIT_FSIZE,
                           (512 * 1024 * 1024, 512 * 1024 * 1024))   # 512MB files
    except Exception:
        pass
    try:
        resource.setrlimit(resource.RLIMIT_NPROC, (64, 64))          # cap forks/threads
    except Exception:
        pass

    src_path = sys.argv[1]
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 42
    split = sys.argv[3] if len(sys.argv) > 3 else "eval"

    try:
        splits = load_split(seed=seed)
        src = Path(src_path).read_text()
        # Defence-in-depth layer 1: static AST gate. Run BEFORE exec so a blocked
        # candidate is rejected as a structured -inf metric instead of executing.
        from .safety import check_source
        ok, reason = check_source(src)
        if not ok:
            print(json.dumps({"sigma_nmad": 9.99, "eta": 1.0,
                              "error": f"blocked:{reason}"}))
            return
        ns: dict = {}
        exec(compile(src, src_path, "exec"), ns)   # trusted-libs sandbox
        fn = ns.get("estimate_redshift")
        if not callable(fn):
            raise RuntimeError("source does not define estimate_redshift(df_train, df_eval)")

        if split.startswith("cv:"):                # K-fold CV over TRAIN+EVAL pool
            parts = split.split(":")
            K = int(parts[1])
            only_fold = int(parts[2]) if len(parts) > 2 else None
            import pandas as pd
            pool = pd.concat([splits["train"], splits["eval"]], ignore_index=True)
            m = run_cv(fn, pool, K, seed, only_fold=only_fold)
            print(json.dumps(m))
        else:                                       # plain eval / test split
            if split not in splits:
                raise ValueError(f"bad split {split!r}")
            pred = np.asarray(fn(splits["train"], splits[split]), dtype=float)
            z_true = splits[split]["z_spec"].to_numpy(float)
            if pred.shape != z_true.shape or not np.all(np.isfinite(pred)):
                raise RuntimeError(f"bad prediction: shape={pred.shape}, "
                                   f"finite={np.isfinite(pred).all()}")
            print(json.dumps(metrics(pred, z_true)))
    except Exception as e:                          # any failure -> structured -inf
        print(json.dumps({
            "sigma_nmad": 9.99, "eta": 1.0, "bias": 0.0,
            "error": f"{type(e).__name__}: {str(e)[:160]}",
            "trace": traceback.format_exc(limit=2),
        }))


if __name__ == "__main__":
    main()
