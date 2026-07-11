"""program.py — the evolved artifact is EXECUTABLE CODE.

Every program implements ONE fixed entry point:

    def estimate_redshift(df_train, df_eval) -> np.ndarray
        df_train: pandas DataFrame with columns u,g,r,i,z and z_spec
        df_eval : pandas DataFrame with columns u,g,r,i,z (and z_spec, ignored)
        returns : 1-D numpy array of predicted z for df_eval rows, same order

The LLM proposer edits this source directly (AlphaEvolve-style). The genetic
fallback mutates a structured ``spec`` and re-renders source via render_source().
"""
from __future__ import annotations

from typing import Dict, Any

# Naive but COMPLETE seed (AlphaEvolve: "the initial implementation must be
# complete, it can be rudimentary"). r-band-only linear regression -> weak.
NAIVE_SEED_SOURCE = '''import numpy as np
from sklearn.linear_model import LinearRegression


def estimate_redshift(df_train, df_eval):
    """Predict z_spec from SDSS photometry. Rudimentary r-band-only baseline."""
    Xtr = df_train[["r"]].to_numpy(float)
    ytr = df_train["z_spec"].to_numpy(float)
    Xev = df_eval[["r"]].to_numpy(float)
    return LinearRegression().fit(Xtr, ytr).predict(Xev)
'''

# Structured spec that the genetic fallback mutates. Mirrors rec 1's gene space.
NAIVE_SPEC: Dict[str, Any] = {
    "color_pairs": [],          # subset of ["ug","gr","ri","iz"]
    "include_r": True,
    "degree": 1,                # polynomial feature degree (1..3)
    "scale": "none",            # none | standard | robust
    "model": "linear",          # linear | ridge | rf
    "alpha": 1.0,               # ridge alpha
    "rf_trees": 50,
    "rf_depth": 6,
}


def render_source(spec: Dict[str, Any]) -> str:
    """Render a structured spec into a complete estimate_redshift source string.

    This lets the (offline) GeneticProposer explore the same strategy space as
    rec 1 by mutating the spec and re-rendering, with no LLM call required."""
    pairs = spec.get("color_pairs", [])
    include_r = bool(spec.get("include_r", False))
    degree = int(spec.get("degree", 1))
    scale = spec.get("scale", "none")
    model = spec.get("model", "linear")
    alpha = float(spec.get("alpha", 1.0))
    trees = int(spec.get("rf_trees", 50))
    depth = int(spec.get("rf_depth", 6))

    feature_lines = [f'        ({a!r}, {b!r}),' for (a, b) in pairs]
    if include_r:
        feature_lines.append('        ("r", None),  # raw magnitude')
    if not feature_lines:
        feature_lines.append('        ("r", None),  # fallback: need >=1 feature')

    imports = ["import numpy as np"]
    if model == "ridge":
        imports.append("from sklearn.linear_model import Ridge")
        fit = f"Ridge(alpha={alpha!r}).fit(Xtr, ytr)"
    elif model == "rf":
        imports.append("from sklearn.ensemble import RandomForestRegressor")
        fit = (f"RandomForestRegressor(n_estimators={trees}, max_depth={depth}, "
               "n_jobs=-1, random_state=0).fit(Xtr, ytr)")
    else:
        imports.append("from sklearn.linear_model import LinearRegression")
        fit = "LinearRegression().fit(Xtr, ytr)"

    scale_block = ""
    if scale == "standard":
        imports.append("from sklearn.preprocessing import StandardScaler")
        scale_block = ("    sc = StandardScaler().fit(Xtr)\n"
                       "    Xtr, Xev = sc.transform(Xtr), sc.transform(Xev)\n")
    elif scale == "robust":
        imports.append("from sklearn.preprocessing import RobustScaler")
        scale_block = ("    sc = RobustScaler().fit(Xtr)\n"
                       "    Xtr, Xev = sc.transform(Xtr), sc.transform(Xev)\n")
    if degree > 1:
        imports.append("from sklearn.preprocessing import PolynomialFeatures")
        scale_block += (f"    pf = PolynomialFeatures({degree}, include_bias=False).fit(Xtr)\n"
                        "    Xtr, Xev = pf.transform(Xtr), pf.transform(Xev)\n")

    return (
        "\n".join(imports) + "\n\n\n"
        "def _features(df):\n"
        "    # (band_a, band_b) -> colour a-b ; (band, None) -> raw magnitude\n"
        "    feats = []\n"
        "    for a, b in [\n"
        + "\n".join(feature_lines) + "\n"
        "    ]:\n"
        "        if b is None:\n"
        "            feats.append(df[a].to_numpy(float))\n"
        "        else:\n"
        "            feats.append(df[a].to_numpy(float) - df[b].to_numpy(float))\n"
        "    return np.column_stack(feats)\n"
        "\n\n"
        "def estimate_redshift(df_train, df_eval):\n"
        "    Xtr = _features(df_train)\n"
        "    ytr = df_train['z_spec'].to_numpy(float)\n"
        "    Xev = _features(df_eval)\n"
        + scale_block +
        "    return " + fit + ".predict(Xev)\n"
    )


SIGNATURE_NAME = "estimate_redshift"


def validate_source(src: str, entry_point: str = SIGNATURE_NAME) -> bool:
    """Cheap static check that the source defines the required entry point."""
    return f"def {entry_point}" in src
