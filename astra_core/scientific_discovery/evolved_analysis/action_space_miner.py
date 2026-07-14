"""action_space_miner.py — Sub-project C: literature-mined action-space discovery.

Biomni (Stanford SNAP, Science 2026) builds its biomedical agent's tool/database
environment not by hand but by mining the literature (PaperTaskExtractor over
bioRxiv) — letting the field's papers define which tasks, databases, and methods
the agent should know about. This is the astrophysics analogue: read recent
astro-ph abstracts and extract which surveys/datasets the field actually uses,
then SUGGEST which datasets to add to the data lake (data_lake.py).

This is an ON-DEMAND growth tool, NOT part of the hot discovery loop. Run it
occasionally (e.g. monthly) so the lake evolves with the literature.

Run:
    PYTHONPATH=astra_core/scientific_discovery python -m evolved_analysis.action_space_miner
"""
from __future__ import annotations

import json
import re
import time
import urllib.request
from typing import Callable, List

ARXIV_ENDPOINT = "https://export.arxiv.org/api/query"
RATE_SLEEP = 4.0  # be polite to the arXiv API (matches novelty_gate.py)

# Survey/archive keywords to recognise in abstracts (canonical name -> variants).
KNOWN_DATASETS = {
    "SDSS": ["sdss", "sloan digital sky survey"],
    "BOSS": [" boss ", "baryon oscillation spectroscopic"],
    "DESI": ["desi", "dark energy spectroscopic"],
    "Gaia": ["gaia"],
    "TESS": ["tess", "transiting exoplanet survey"],
    "Kepler": ["kepler"],
    "ZTF": ["ztf", "zwicky transient"],
    "LSST/Rubin": ["lsst", "rubin", "vera c. rubin"],
    "2MASS": ["2mass", "two micron"],
    "WISE": [" wise ", "wide-field infrared survey explorer"],
    "Chandra": ["chandra"],
    "XMM": ["xmm"],
    "HST": ["hubble", "hst"],
    "JWST": ["jwst"],
    "VLA": ["vla", "very large array"],
    "ALMA": ["alma"],
    "DECam": ["decam", "dark energy camera"],
    "Pan-STARRS": ["pan-starrs", "panstarrs"],
    "eROSITA": ["erosita"],
    "Euclid": ["euclid"],
}


def fetch_arxiv_abstracts(category: str = "astro-ph", max_results: int = 40,
                          timeout: int = 30) -> List[str]:
    """Fetch recent astro-ph abstracts from the arXiv Atom API. Returns a list of
    abstract strings. Network required — call OUTSIDE the sandbox."""
    url = (f"{ARXIV_ENDPOINT}?search_query=cat:{category}*&start=0"
           f"&max_results={max_results}&sortBy=submittedDate"
           f"&sortOrder=descending")
    raw = urllib.request.urlopen(url, timeout=timeout).read().decode(
        "utf-8", "replace")
    time.sleep(RATE_SLEEP)
    return re.findall(r"<summary>(.*?)</summary>", raw, re.DOTALL)


def extract_dataset_mentions(abstracts: List[str]) -> List[dict]:
    """Rule-based first pass: count known survey/archive mentions across the
    abstracts. No network. Returns [{dataset, count}], most frequent first."""
    text = " " + " \n ".join(abstracts).lower() + " "
    out = []
    for canon, variants in KNOWN_DATASETS.items():
        n = sum(text.count(v) for v in variants)
        if n:
            out.append({"dataset": canon, "count": int(n)})
    out.sort(key=lambda d: -d["count"])
    return out


def suggest_datasets(mentions: List[dict], have: List[str]) -> List[str]:
    """Suggest datasets to add to the lake: mentioned in the literature but not
    already registered. Pure data, no network."""
    have_lc = {h.lower() for h in have}
    return [m["dataset"] for m in mentions
            if m["dataset"].lower() not in have_lc]


def extract_via_llm(abstracts: List[str],
                    llm_complete: Callable[[str, str], str] = None) -> List[dict]:
    """Optional LLM pass (Biomni-style): given a batch of abstracts, ask the LLM
    to extract {dataset, analysis, method} triples the field uses. Pass a callable
    ``llm_complete(system_prompt, user_prompt) -> str`` (e.g. the LLM gateway).
    Returns a parsed list of dicts; [] if no callable or parse failure. Never
    raises — this is exploratory tooling, not a gate."""
    if llm_complete is None:
        return []
    try:
        joined = "\n\n---\n\n".join(abstracts)[:8000]
        system = ("You extract the concrete astronomical datasets/surveys and "
                  "analysis methods mentioned in research abstracts. Respond ONLY "
                  "with a JSON list of objects {dataset, analysis, method}.")
        txt = llm_complete(system, f"Abstracts:\n{joined}")
        m = re.search(r"\[.*\]", txt, re.DOTALL)
        items = json.loads(m.group(0)) if m else []
        return [it for it in items if isinstance(it, dict)]
    except Exception:
        return []


def mine_and_suggest(max_results: int = 40,
                     have: List[str] = None,
                     llm_complete: Callable[[str, str], str] = None) -> dict:
    """End-to-end: fetch astro-ph abstracts, extract mentions, suggest additions.
    Returns {mentions, suggestions, n_abstracts}. Network required."""
    abstracts = fetch_arxiv_abstracts(max_results=max_results)
    mentions = extract_dataset_mentions(abstracts)
    suggestions = suggest_datasets(mentions, have or [])
    return {"mentions": mentions, "suggestions": suggestions,
            "n_abstracts": len(abstracts)}


if __name__ == "__main__":
    from .data_lake import list_datasets
    registered = [ds.name for ds in list_datasets()]
    print(f"[miner] registered lake datasets: {registered}")
    print("[miner] fetching recent astro-ph abstracts ...")
    res = mine_and_suggest(have=registered)
    print(f"[miner] scanned {res['n_abstracts']} abstracts")
    print("[miner] dataset mentions:")
    for m in res["mentions"]:
        print(f"  {m['dataset']:14s} {m['count']}")
    print("[miner] suggested NEW datasets to add to the lake:")
    for s in res["suggestions"]:
        print(f"  - {s}")
