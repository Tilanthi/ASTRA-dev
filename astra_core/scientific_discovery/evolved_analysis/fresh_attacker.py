"""fresh_attacker.py — the Phase-2 hard rule (Eureka plan, 2026-08-30).

"Every finding crossing a threshold is attacked by an empty-context copy
before anyone hears of it, even when the proposer is sure it is fine."

The threshold here is promotion: a both-gate survivor about to be written to
``evolved_discoveries.json`` (the store the human review surface ranks).
``run_claim_search._emit`` calls :func:`attack_claim` BEFORE the store write;
a claim killed by the attack is never emitted, and the attack report travels
with every survivor.

The attacker is deliberately EMPTY-CONTEXT and DETERMINISTIC — it knows only
the program source, the dataset name and the claimed numbers, never the
proposer's reasoning, and it spends no LLM tokens (bounded compute is the
Phase-2 budget; an LLM attacker belongs to the spend-gated Phase 3). Attacks:

  A1 re-split reproduction — the program is re-run in the sandbox on fresh
     train/eval/test splits (new seeds). A genuine relation reproduces; a
     split fluke dies. Any failure here KILLS the finding.
  A2 permutation null — every column of every split is independently shuffled
     (marginals preserved, all cross-column associations destroyed). A real
     association should COLLAPSE. An effect that survives permutation measures
     a single-column marginal, not a relation — that is a specification-gaming
     suspect (the CoastRunners lagoon): the finding may stand but carries the
     mark, visible on the review surface.

Outcomes (ledger kind=attack):
  survived      — all re-splits reproduce and the effect collapses under null
  suspect       — re-splits reproduce but the effect survives permutation
  killed        — some re-split failed to reproduce (or errored)
  not-runnable  — the attack itself could not execute; conservatively blocks

Run:
    PYTHONPATH=astra_core/scientific_discovery python -m evolved_analysis.fresh_attacker <program_source.py> [dataset]
"""
from __future__ import annotations

import sys
from pathlib import Path

# A1: fresh splits. Deliberately unrelated to the search's own seed family.
ATTACK_SEEDS = (1337, 9001, 4242)
# A2: permutation nulls.
PERMUTE_SEEDS = (777, 20461)
# Hard bound on one attack: 5 sandbox runs at 90 s each, only on promotion.
ATTACK_TIMEOUT = 90.0


def attack_claim(src: str, source: str = "legacy", *, corrected_pmax=None) -> dict:
    """Attack one claim with an empty-context copy. Returns the report dict.

    ``corrected_pmax`` optionally passes the family-corrected Gate-1 bar the
    original verdict used; when omitted it is recomputed the same way.
    """
    from .run_claim_search import gate1_run
    from .claim_task import gate1_significant
    from .claim_gates import bonferroni_pmax
    from .claim_task import PMAX
    from .evidence_ledger import safe_append

    pmax = corrected_pmax if corrected_pmax is not None else bonferroni_pmax(PMAX)
    attacks = []

    # A1 — fresh-split reproduction. Any miss kills.
    for seed in ATTACK_SEEDS:
        m = gate1_run(src, seed=seed, source=source, timeout=ATTACK_TIMEOUT)
        ok, why = gate1_significant(m, pmax=pmax, dataset=source)
        attacks.append({"attack": "re-split", "seed": seed,
                        "effect": m.get("effect"), "pvalue": m.get("pvalue"),
                        "ok": bool(ok), "why": str(why)[:120],
                        "error": m.get("error")})
    # A2 — permutation null. The effect should NOT survive these.
    perm_survivors = 0
    for pseed in PERMUTE_SEEDS:
        m = gate1_run(src, seed=42, source=source, timeout=ATTACK_TIMEOUT,
                      permute_seed=pseed)
        ok, _ = gate1_significant(m, pmax=pmax, dataset=source)
        if ok:
            perm_survivors += 1
        attacks.append({"attack": "permutation-null", "permute_seed": pseed,
                        "effect": m.get("effect"), "pvalue": m.get("pvalue"),
                        "effect_survived_null": bool(ok),
                        "error": m.get("error")})

    from .claim_task import parse_claim
    claim = parse_claim(src) or ""
    import hashlib
    program_hash = hashlib.sha1(src.encode()).hexdigest()[:10]

    resplit_errs = [a for a in attacks if a["attack"] == "re-split" and a.get("error")]
    resplit_misses = [a for a in attacks if a["attack"] == "re-split"
                      and not a.get("error") and not a["ok"]]
    if resplit_errs:
        disposition = "not-runnable"
        detail = (f"re-split seed {resplit_errs[0]['seed']} errored: "
                  f"{str(resplit_errs[0]['error'])[:120]} — reproducibility "
                  f"unproven, promotion blocked")
    elif resplit_misses:
        disposition = "killed"
        a = resplit_misses[0]
        detail = (f"re-split seed {a['seed']} failed to reproduce "
                  f"(effect={a['effect']}, p={a['pvalue']}; {a['why']})")
    elif perm_survivors:
        disposition = "suspect"
        detail = (f"effect survives the permutation null in {perm_survivors}/"
                  f"{len(PERMUTE_SEEDS)} shuffles — it may measure a single-"
                  f"column marginal rather than an association; marked, not "
                  f"blocked")
    else:
        disposition = "survived"
        detail = (f"reproduced on all {len(ATTACK_SEEDS)} fresh splits; "
                  f"collapses under both permutation nulls")

    report = {"disposition": disposition, "detail": detail, "attacks": attacks}
    safe_append("attack", disposition, dataset=source, claim=claim or None,
                program_hash=program_hash,
                value=attacks[0].get("effect") if attacks else None,
                detail=detail)
    return report


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        print(__doc__.splitlines()[0])
        print("usage: python -m evolved_analysis.fresh_attacker <src.py> [dataset]")
        return 1
    src = Path(argv[0]).read_text()
    source = argv[1] if len(argv) > 1 else "legacy"
    import json
    print(json.dumps(attack_claim(src, source), indent=2)[:2000])
    return 0


if __name__ == "__main__":
    sys.exit(main())
