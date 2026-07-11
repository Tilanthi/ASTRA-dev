"""stan_narrate_worker.py — use ASTRA's STAN system.answer() to NARRATE a
machine-verified finding into a scientific title + abstract.

Why narration (not code): the STAN probe showed system.answer() returns scientific
PROSE and ignores code-generation instructions, and is slow/fragile to instantiate
(~44s, recursion fallback). So STAN is the wrong tool for the code-diff proposer
but the RIGHT tool for turning a verified numeric result into ASTRA-voice prose —
combining both systems' strengths (Claude writes code; the evaluator verifies;
STAN narrates).

Isolated subprocess + auto-start patched to a no-op so it cannot spawn a
conflicting discovery loop. Hard-killed by the caller after `timeout`.

Args: <facts_json_file>   -> prints {"title":..., "abstract":...} as one JSON line.
"""
from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def main():
    facts = json.loads(Path(sys.argv[1]).read_text())
    # patch auto-start BEFORE constructing STAN -> no conflicting discovery loop
    import astra_core.core.auto_start_discovery as asd  # noqa: E402
    asd.auto_start_discovery = lambda *a, **k: False
    from astra_core import create_stan_system  # noqa: E402
    stan = create_stan_system()

    prompt = (
        "A machine-learning analysis pipeline was EVOLVED and VERIFIED on real "
        "astronomical data. Write a concise scientific discovery record for it.\n\n"
        f"Task: {facts['task']}.\n"
        f"Method discovered: {facts['method']}.\n"
        f"Verification metric ({facts['metric_name']}): {facts['metric_value']} "
        f"on {facts['n_eval']} held-out eval objects; independent held-out TEST "
        f"value {facts['held_out_value']}; outlier fraction {facts.get('eta','n/a')}.\n"
        f"Data: REAL {facts['data_source']} ({facts['n_train']} train / "
        f"{facts['n_eval']} eval / {facts['n_test']} test). Cross-validated.\n\n"
        "Reply with EXACTLY two lines:\n"
        "Title: <one-line scientific title>\n"
        "Abstract: <2-3 sentence abstract stating the method, the verified "
        "metric, and that it was machine-graded on real held-out data>. "
        "No preamble, no extra lines.")
    r = stan.answer(prompt)
    ans = (r.get("answer", "") if isinstance(r, dict) else str(r)).strip()
    lines = [ln.strip() for ln in ans.splitlines() if ln.strip()]
    title, abstract = "", ""
    for i, ln in enumerate(lines):
        low = ln.lower()
        if low.startswith("title:") and not title:
            title = ln.split(":", 1)[1].strip()
        elif low.startswith("abstract:") and not abstract:
            abstract = ln.split(":", 1)[1].strip()
    if not title:                       # fallback parsing
        title = lines[0][:120] if lines else facts["task"]
    if not abstract:
        abstract = " ".join(lines[1:])[:600] or ans[:600]
    print(json.dumps({"title": title, "abstract": abstract,
                      "stan_used": True, "raw_len": len(ans)}))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # always emit valid JSON so the caller can fall back gracefully
        print(json.dumps({"title": None, "abstract": None, "stan_used": False,
                          "error": f"{type(e).__name__}: {str(e)[:160]}",
                          "trace": traceback.format_exc(limit=1)}))
