"""cls_program.py — WP5 classification task: program artifact + task system prompt.

Fixed entry point:
    def classify_object(df_train, df_eval) -> np.ndarray
        df_train: u,g,r,i,z AND spec_class in {STAR, GALAXY, QSO}
        df_eval : u,g,r,i,z
        returns : 1-D array of predicted class label strings for df_eval rows
"""
from __future__ import annotations

from typing import Dict, Any

ENTRY = "classify_object"

NAIVE_SEED_SOURCE = '''import numpy as np


def classify_object(df_train, df_eval):
    """Naive baseline: always predict the majority training class."""
    maj = df_train["spec_class"].value_counts().idxmax()
    return np.array([maj] * len(df_eval))
'''

NAIVE_SPEC: Dict[str, Any] = {
    "color_pairs": [], "include_r": False, "degree": 1, "scale": "none",
    "model": "majority", "n_neighbors": 5, "n_estimators": 100, "max_depth": 6,
}

SYSTEM = (
    "You are an expert astronomer and ML engineer. You improve a Python function "
    "`classify_object(df_train, df_eval)` that classifies SDSS objects into STAR, "
    "GALAXY, or QSO from u,g,r,i,z model magnitudes. It is graded on REAL held-out "
    "objects by BALANCED ACCURACY (mean per-class recall; 1/3 = chance/majority). "
    "Higher is better.\n"
    "HARD RULES:\n"
    "- Keep the EXACT signature: def classify_object(df_train, df_eval)\n"
    "- df_train has columns u,g,r,i,z AND spec_class. df_eval has u,g,r,i,z.\n"
    "- Return a 1-D numpy array of strings ('STAR'/'GALAXY'/'QSO') for df_eval rows.\n"
    "- You may import ONLY: numpy, scipy, sklearn, pandas (already available).\n"
    "- No file I/O, no network, no plotting, no global side effects.\n"
    "Colours (u-g, g-r, r-i, i-z), colour-colour cuts, and classifiers "
    "(GaussianNB, KNN, RandomForest, GradientBoosting, LogisticRegression) are "
    "known to separate stars/galaxies/QSOs well. The u-g vs g-r plane is classic.\n"
    "RESPOND WITH EITHER:\n"
    "  (a) one or more diff blocks (exact format):\n"
    "<<<SEARCH>>>\nexact existing code\n<<<REPLACE>>>\nnew code\n<<<END>>>\n"
    "  (b) a single complete rewritten function in one ```python``` block.\n"
    "Output ONLY the diff or code, no explanation."
)
