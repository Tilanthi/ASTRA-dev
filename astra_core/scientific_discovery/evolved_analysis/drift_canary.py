#!/usr/bin/env python3
"""drift_canary.py — freeze-frame drift alarm for the novelty judge.

AstroMLab lesson: when the judge model (or its prompt path) changes, verdict
behaviour silently changes; you must re-validate, not assume. This canary:

1. Holds a FROZEN set of (claim, synthetic abstracts) pairs. These abstracts
   are calibration fixtures ONLY — hand-written probe text for measuring judge
   stability. They are never discovery inputs, never retrieved from arXiv,
   and never emitted anywhere.
2. Runs each pair through the exact judge path (_judge_known: same system
   prompt, same JSON spec, same parser) with NO retrieval and NO cache.
3. Compares verdicts to a pinned baseline (``--pin``) and raises a drift
   alarm when agreement drops below threshold on identical inputs.

Run weekly, after any model/gateway change, or before trusting a trend in
novelty rates:

    PYTHONPATH=. python3 -m astra_core.scientific_discovery.evolved_analysis.drift_canary --pin   # first time
    PYTHONPATH=. python3 -m astra_core.scientific_discovery.evolved_analysis.drift_canary         # check

Cost: len(canary_cases()) judge calls (~6 x ~3k tokens) — manual, not in-loop.
Output: ~/.astra_persistent/evolved_programs/drift_canary.jsonl
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path

from .novelty_gate import Paper, _judge_known

logger = logging.getLogger(__name__)

BASELINE_PATH = (Path.home() / ".astra_persistent" / "evolved_programs"
                 / "drift_canary_baseline.json")
OUT_PATH = (Path.home() / ".astra_persistent" / "evolved_programs"
            / "drift_canary.jsonl")
DRIFT_THRESHOLD = 0.8  # agreement on identical inputs below this = drift

# Frozen calibration fixtures (see module docstring: never discovery inputs).
# Mix of textbook-obvious claims (expect 'known') and relation-shaped claims
# with no support in the provided abstracts (expect 'novel').
_CANARY_FIXTURES = [
    {
        "id": "canary_tully_fisher",
        "claim": ("Spiral galaxy rotation velocity scales with total luminosity "
                  "as a power law (the Tully-Fisher relation)"),
        "expect_hint": "known",
        "abstracts": [
            ("Calibration of the Tully-Fisher relation with Spitzer 3.6um photometry",
             "2016",
             "We recalibrate the Tully-Fisher relation between luminosity and "
             "rotation velocity using 3.6um photometry, finding a tight power-law "
             "scaling L ~ V^4 used for distance estimation of spiral galaxies."),
            ("The baryonic Tully-Fisher relation",
             "2015",
             "The baryonic mass of spiral galaxies follows a tight power-law "
             "relation with rotation velocity over five decades in mass."),
        ],
    },
    {
        "id": "canary_color_redshift",
        "claim": ("Galaxies with redder g-r colour lie at higher redshift in "
                  "wide-field photometric surveys"),
        "expect_hint": "known",
        "abstracts": [
            ("Photometric redshifts from galaxy colours in SDSS",
             "2010",
             "Galaxy colour correlates strongly with redshift: redder g-r colours "
             "trace higher redshift and older stellar populations, the basis of "
             "photometric redshift estimation."),
            ("The cosmic evolution of galaxy colours",
             "2012",
             "We quantify the colour-redshift relation for luminous red galaxies, "
             "confirming systematic reddening with distance."),
        ],
    },
    {
        "id": "canary_lum_function",
        "claim": ("The number density of galaxies per unit luminosity decreases "
                  "steeply at the bright end (Schechter luminosity function)"),
        "expect_hint": "known",
        "abstracts": [
            ("The galaxy luminosity function from SDSS",
             "2009",
             "We fit Schechter functions to the galaxy luminosity function, "
             "showing the steep exponential decline in number density at the "
             "bright end and the power-law faint end."),
            ("Deep field galaxy number counts",
             "2013",
             "Galaxy number counts per magnitude bin flatten towards the faint "
             "end, consistent with Schechter-function luminosity distributions "
             "in deep imaging surveys."),
        ],
    },
    {
        "id": "canary_unsupported_filament",
        "claim": ("The width of molecular filaments in the Polaris cloud "
                  "anticorrelates with the local dust temperature gradient "
                  "measured perpendicular to the filament spine"),
        "expect_hint": "novel",
        "abstracts": [
            ("Herschel observations of the Polaris Cloud",
             "2014",
             "We present dust emission maps of the Polaris cloud, measuring "
             "filament widths and column densities, and noting their similarity "
             "to filaments in other quiescent regions."),
            ("Dust temperature variations in translucent clouds",
             "2011",
             "Dust temperatures in translucent clouds are influenced by the "
             "interstellar radiation field; we map temperature variations across "
             "several nearby clouds."),
        ],
    },
    {
        "id": "canary_unsupported_pulsar",
        "claim": ("Pulsars in globular clusters show a significant excess of "
                  "mode changes during periastron passages of companion stars"),
        "expect_hint": "novel",
        "abstracts": [
            ("Pulse profile variations in recycled pulsars",
             "2018",
             "We survey mode-changing behaviour in recycled pulsars, finding "
             "occurrence rates comparable to the field population."),
            ("Globular cluster pulsar surveys",
             "2017",
             "A review of pulsar searches in globular clusters, with updates on "
             "new discoveries and orbital characteristics."),
        ],
    },
    {
        "id": "canary_unsupported_agn",
        "claim": ("The mid-infrared colour of obscured AGN host galaxies varies "
                  "periodically with the 11-year solar cycle"),
        "expect_hint": "novel",
        "abstracts": [
            ("Mid-infrared colours of AGN hosts",
             "2019",
             "Obscured AGN show redder mid-infrared colours than inactive "
             "galaxies of similar mass, driven by torus dust emission."),
            ("Variability of AGN in the mid-infrared",
             "2021",
             "Mid-infrared variability in AGN is stochastic over year "
             "timescales, tracing reverberating dust in the torus."),
        ],
    },
]


def canary_cases():
    """The frozen (claim, abstracts) fixtures. Calibration-only, never discovery."""
    return [dict(c) for c in _CANARY_FIXTURES]


def run_canary(judge=None):
    """Run every fixture through the judge path; return per-case verdicts.

    No retrieval, no novelty cache — inputs are frozen, so any verdict change
    between runs is judge-side drift, not input drift.
    """
    judge = judge or _judge_known
    out = []
    for c in canary_cases():
        papers = [Paper("canary", t, a, c["id"], y)
                  for (t, y, a) in c["abstracts"]]
        known, _p, label, _r, confidence = judge(c["claim"], papers)
        out.append({"id": c["id"], "expect_hint": c["expect_hint"],
                    "known": bool(known), "label": label or "",
                    "confidence": confidence})
    return out


def compare(baseline, current, threshold: float = DRIFT_THRESHOLD) -> dict:
    """Verdict agreement between a pinned baseline and a fresh canary run."""
    base = {v["id"]: v for v in baseline}
    n = same = 0
    changed = []
    for v in current:
        b = base.get(v["id"])
        if b is None:
            changed.append({"id": v["id"], "issue": "missing-from-baseline"})
            continue
        n += 1
        if b.get("known") == v["known"] and b.get("label") == v["label"]:
            same += 1
        else:
            changed.append({"id": v["id"],
                            "baseline": [b.get("known"), b.get("label")],
                            "now": [v["known"], v["label"]]})
    agreement = (same / n) if n else 0.0
    return {"agreement": round(agreement, 3), "n": n, "changed": changed,
            "threshold": threshold, "drift": bool(n and agreement < threshold)}


def _current_model() -> str:
    env = os.environ.get("ASTRA_LLM_MODEL")
    if env:
        return env
    try:
        from .novelty_gate import _get_gateway
        gw = _get_gateway()
        if gw is not None:
            return str(getattr(gw, "model", "unknown"))
    except Exception:
        pass
    return "unknown"


def pin_baseline(path: Path = None, judge=None, model: str = None) -> dict:
    """Run the canary and pin the verdicts as the drift baseline."""
    path = path or BASELINE_PATH
    model = model or _current_model()
    verdicts = run_canary(judge=judge)
    doc = {"model": model, "n": len(verdicts), "verdicts": verdicts,
           "note": "pinned drift baseline; calibration fixtures only"}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=2))
    print(f"[canary] pinned baseline ({len(verdicts)} cases, model={model}) -> {path}")
    return doc


def check_drift(path: Path = None, judge=None, model: str = None,
                out_path: Path = None) -> dict:
    """Compare a fresh canary run against the pinned baseline."""
    path = path or BASELINE_PATH
    if not path.exists():
        print(f"[canary] no baseline at {path} — run with --pin first")
        return {"error": "no-baseline"}
    baseline = json.loads(path.read_text())
    model = model or _current_model()
    current = run_canary(judge=judge)
    res = compare(baseline.get("verdicts", []), current)
    res["model_changed"] = bool(baseline.get("model") not in (None, model))
    res["baseline_model"] = baseline.get("model")
    res["model"] = model
    row = dict(res, ts=__import__("time").strftime("%Y-%m-%dT%H:%M:%S"))
    try:
        (out_path or OUT_PATH).parent.mkdir(parents=True, exist_ok=True)
        with (out_path or OUT_PATH).open("a") as f:
            f.write(json.dumps(row) + "\n")
    except Exception:
        pass
    print(f"[canary] agreement={res['agreement']} over {res['n']} case(s) "
          f"(threshold {res['threshold']}; baseline model={baseline.get('model')}, "
          f"now={model})")
    if res["model_changed"]:
        print("[canary] WARNING: judge model differs from baseline — "
              "re-validate before trusting novelty-rate trends")
    if res["drift"]:
        print("[canary] DRIFT ALARM: verdicts on identical inputs changed "
              "beyond threshold")
        for ch in res["changed"]:
            print(f"  changed: {ch}")
    return res


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--pin", action="store_true",
                    help="pin current verdicts as the drift baseline")
    ap.add_argument("--baseline", type=Path, default=None)
    args = ap.parse_args(argv)
    if args.pin:
        pin_baseline(args.baseline)
    else:
        res = check_drift(args.baseline)
        if res.get("drift"):
            sys.exit(2)


if __name__ == "__main__":
    main()
