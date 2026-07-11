"""cls_eval_worker.py — isolated subprocess scorer for WP5 classification.

Loads a candidate program defining classify_object(df_train, df_eval), runs it on
REAL balanced SDSS data, and prints balanced accuracy (overall + per-class recall
as the error profile fed back to the proposer). Same isolation contract as the
photo-z worker.
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
from sklearn.metrics import balanced_accuracy_score, recall_score  # noqa: E402
from .cls_data import load_split, CLASSES  # noqa: E402


def profile(y_true, y_pred) -> dict:
    bal = float(balanced_accuracy_score(y_true, y_pred))
    per = {c: float(recall_score(y_true, y_pred, labels=[c], average="macro",
                                 zero_division=0)) for c in CLASSES}
    # accuracy too for context
    acc = float(np.mean(np.asarray(y_true) == np.asarray(y_pred)))
    return {"balanced_accuracy": bal, "accuracy": acc,
            "recall_STAR": per["STAR"], "recall_GALAXY": per["GALAXY"],
            "recall_QSO": per["QSO"]}


def main():
    src_path = sys.argv[1]
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 42
    split = sys.argv[3] if len(sys.argv) > 3 else "eval"
    try:
        splits = load_split(seed=seed)
        src = Path(src_path).read_text()
        ns: dict = {}
        exec(compile(src, src_path, "exec"), ns)
        fn = ns.get("classify_object")
        if not callable(fn):
            raise RuntimeError("no classify_object(df_train, df_eval)")
        pred = np.asarray(fn(splits["train"], splits[split]))
        yt = splits[split]["spec_class"].to_numpy()
        if pred.shape != yt.shape:
            raise RuntimeError(f"shape {pred.shape} != {yt.shape}")
        print(json.dumps(profile(yt, pred)))
    except Exception as e:
        print(json.dumps({"balanced_accuracy": -1.0, "accuracy": -1.0,
                          "error": f"{type(e).__name__}: {str(e)[:160]}",
                          "trace": traceback.format_exc(limit=2)}))


if __name__ == "__main__":
    main()
