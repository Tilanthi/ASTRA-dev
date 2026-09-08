"""second_judge.py — F1 (2026-09-08): cross-model judge at the promotion chokepoint.

ASTRA's fresh-attacker rule buys "no self-approval" via context isolation, but every
attacker is still the same model family as the proposer. A second model family has
independent blind spots, so at promotion — and ONLY at promotion, never the daily
loop — one additional empty-context judge from a DIFFERENT family re-checks the
claim against freshly retrieved abstracts.

Honesty guarantees (the fiction rules apply here in full)
---------------------------------------------------------
- Unconfigured is recorded honestly: with no ``ASTRA_JUDGE2_TOKEN`` /
  ``ASTRA_JUDGE2_MODEL`` this returns ``status="not-configured"`` and ``block=False``
  WITHOUT importing the gateway or touching the network. It is non-blocking
  metadata, never a fabricated pass.
- Empty-context: the judge sees the claim and freshly retrieved abstracts ONLY —
  never proposer reasoning, program source, or ASTRA's own prior verdicts (same
  grounding discipline as gate 2's ``_judge_known``).
- Failure is non-blocking: retrieval-failed / judge-failed / error are recorded,
  never silently upgraded to a pass.
- Blocking requires the GROUNDED ground: the judge must mark the claim known AND
  cite a specific retrieved abstract (``reason == "entailed"`` with an in-range
  ``by_abstract``). A "foundational" judgement is ungrounded domain knowledge —
  exactly the fiction-adjacent class this family-split exists to contain — so it
  records and marks but never blocks.

Config (the supervisor merges ``~/.astra_persistent/llm_env`` into episode env, so
wiring a real endpoint later is config-only): ``ASTRA_JUDGE2_TOKEN`` +
``ASTRA_JUDGE2_MODEL`` both required (a same-model second call is spend without
information), ``ASTRA_JUDGE2_BASE_URL`` optional (defaults to the shared
``ANTHROPIC_BASE_URL``). Both endpoints speak the Anthropic protocol, so the
canonical ``LLMGateway`` serves both; the overrides added for this module keep it
the ONE place owning a real client.

Public API: ``audit_claim(claim, dataset=None) -> dict`` — never raises.
"""
from __future__ import annotations

import json
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

CALLER = "second_judge"   # token-ledger caller id (see intelligence/token_ledger)


def _config() -> dict:
    """Read the judge-2 endpoint config from the environment (never raises)."""
    return {
        "token": (os.environ.get("ASTRA_JUDGE2_TOKEN") or "").strip(),
        "model": (os.environ.get("ASTRA_JUDGE2_MODEL") or "").strip(),
        "base_url": (os.environ.get("ASTRA_JUDGE2_BASE_URL") or "").strip() or None,
    }


def configured() -> bool:
    """True when a second-family endpoint is fully configured."""
    c = _config()
    return bool(c["token"] and c["model"])


def audit_claim(claim: str, dataset: Optional[str] = None) -> dict:
    """Empty-context second-family audit of ``claim`` at promotion time.

    Returns a dict (never raises) with at least ``status`` and ``block``.
    Statuses: ``not-configured`` | ``retrieval-failed`` | ``judge-failed`` |
    ``judged`` | ``error``. Only ``judged`` with a grounded entailed-known
    citation sets ``block=True``.
    """
    base = {"block": False, "claim": (claim or "")[:200], "dataset": dataset or ""}
    cfg = _config()
    if not (cfg["token"] and cfg["model"]):
        return {**base, "status": "not-configured",
                "detail": "set ASTRA_JUDGE2_TOKEN + ASTRA_JUDGE2_MODEL to enable"}

    try:
        # gate-2 parity for retrieval: same query extraction, same sources,
        # FRESH papers (this judge never reads the novelty cache — a second
        # family that rubber-stamps our own cached verdicts is no second check)
        from . import novelty_gate as ng
        papers = ng._retrieve_papers(ng._extract_query(claim or ""), use_s2=True)
        if not papers:
            return {**base, "status": "retrieval-failed", "model": cfg["model"],
                    "detail": "no papers retrieved for the empty-context sweep"}

        from ._llm import gateway_module
        gw = gateway_module().LLMGateway(
            model=cfg["model"], auth_token=cfg["token"], base_url=cfg["base_url"])

        abstracts = "\n\n".join(
            f"[{i}] {p.title} ({p.year})\n{p.abstract[:900]}"
            for i, p in enumerate(papers))
        system = (
            "You are an independent scientific novelty auditor. A candidate "
            "astrophysical CLAIM is ALREADY-KNOWN (not a new discovery) if EITHER "
            "(a) one of the RETRIEVED ABSTRACTS states or directly implies it — "
            "cite that abstract's index; OR (b) it is a well-established "
            "foundational / textbook result the field treats as given. Use "
            "retrieved text for (a) and standard domain knowledge for (b). You "
            "are seeing ONLY the claim and these abstracts — judge exactly what "
            "is in front of you, nothing else.")
        user = (f"CANDIDATE CLAIM:\n{claim}\n\n"
                f"RETRIEVED ABSTRACTS:\n{abstracts}\n\n"
                "Respond with ONLY JSON: "
                '{"known": true|false, "reason": "entailed"|"foundational"|"novel", '
                '"by_abstract": <int|null>, "confidence": <0.0-1.0>, '
                '"reasoning": "<one sentence>"}')
        text, _usage = gw.complete(
            system=system, messages=[{"role": "user", "content": user}],
            max_tokens=300, caller=CALLER)
        conf, verdict = ng._parse_judge_text(text)
        if not verdict:
            return {**base, "status": "judge-failed", "model": cfg["model"],
                    "n_retrieved": len(papers),
                    "detail": "second-family judge returned no JSON verdict"}

        known = bool(verdict.get("known"))
        label = str(verdict.get("reason", ""))[:24]
        idx = verdict.get("by_abstract")
        # Grounded ground only: a cited, in-range abstract (gate-2's own
        # entailing semantics). Out-of-range citation = judge malfunction ->
        # recorded, not blocking.
        entailed = (known and label == "entailed"
                    and isinstance(idx, int) and 0 <= idx < len(papers))
        return {**base, "status": "judged", "model": cfg["model"],
                "known": known, "reason": label,
                "by_abstract": idx if isinstance(idx, int) else None,
                "n_retrieved": len(papers),
                "confidence": conf,
                "reasoning": str(verdict.get("reasoning", ""))[:300],
                "entailed_by": (papers[idx].title[:160] if entailed else None),
                "block": entailed}
    except Exception as e:  # never raises out of the promotion path
        logger.warning("[second-judge] audit failed: %s", e)
        return {**base, "status": "error",
                "error": f"{type(e).__name__}: {str(e)[:200]}"}


def main() -> int:
    """Zero-spend config smoke; with a claim argument, one real audit."""
    import sys
    cfg = _config()
    print(json.dumps({
        "configured": bool(cfg["token"] and cfg["model"]),
        "model": cfg["model"] or None,
        "base_url": cfg["base_url"] or "(env default)",
        "token_set": bool(cfg["token"]),
    }, indent=2))
    if len(sys.argv) > 1:
        print(json.dumps(audit_claim(" ".join(sys.argv[1:])), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
