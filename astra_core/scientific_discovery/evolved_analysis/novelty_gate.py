"""novelty_gate.py — Gate 2 of the two-gate EVALUATE: is a candidate scientific
claim ALREADY in the literature?

This is the "do not simply repeat things we already know from textbooks or the
scientific literature (incl. arXiv)" gate that the prime directive requires for
open-ended Eureka search (design doc §5.3).

How it works
------------
1. Retrieve the most similar papers from arXiv (primary; no API key needed) and,
   if reachable, Semantic Scholar — for terms extracted from the claim.
2. Ask the LLM, GROUNDED ONLY in the retrieved abstracts, whether the SPECIFIC
   claim is stated or directly implied by any of them. The LLM must cite which
   abstract entails it, or say "none".

Honesty guarantees
------------------
- The entailment judgment is constrained to retrieved text — the LLM is given the
  abstracts and asked to point at the entailing one. It is NOT a free-form
  "is this novel?" judgement (that would re-introduce the circular LLM-as-judge
  fiction problem this whole effort removes).
- Retrieval/judge failures are CONSERVATIVE: if novelty cannot be checked, the
  claim is NOT promoted as a novel Eureka. It returns status ``retrieval-failed``
  / ``judge-failed`` with ``novel=False``.
- Retrieved papers are persisted to a provenance manifest; nothing is fabricated.

Caching: results are keyed by a normalized claim hash in
``~/.astra_persistent/evolved_programs/novelty_cache.json`` so repeated claims do
not re-hit the APIs.

Public API: ``check_novelty(claim, min_effect_description="") -> NoveltyResult``.
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[3]
_GATEWAY = None  # cached llm gateway (loaded decoupled from astra_core/__init__)


def _get_gateway():
    """Return the canonical LLM gateway via the shared decoupled loader
    (see ``_llm.py``). Returns None on failure."""
    global _GATEWAY
    if _GATEWAY is not None:
        return _GATEWAY
    try:
        from ._llm import get_gateway as _gg
        _GATEWAY = _gg()
        return _GATEWAY
    except Exception as e:
        logger.warning("[novelty] could not load LLM gateway: %s", e)
        return None

CACHE_PATH = Path.home() / ".astra_persistent" / "evolved_programs" / "novelty_cache.json"
ARXIV_ENDPOINT = "https://export.arxiv.org/api/query"
S2_ENDPOINT = "https://api.semanticscholar.org/graph/v1/paper/search"
_RATE_SLEEP = 4.0  # arXiv asks for >=3s between calls


@dataclass
class Paper:
    source: str        # "arxiv" | "s2"
    title: str
    abstract: str
    identifier: str    # arxiv id or s2 paperId
    year: Optional[str] = None


@dataclass
class NoveltyResult:
    novel: bool
    status: str        # novel | known | retrieval-failed | judge-failed
    claim: str
    entailed_by: Optional[Paper] = None
    n_retrieved: int = 0
    reasoning: str = ""
    retrieved: List[Paper] = None
    confidence: Optional[float] = None      # judge self-report, ranking signal only
    revision: int = 0                       # times this claim's novelty was re-judged

    def to_dict(self) -> dict:
        d = asdict(self)
        if self.entailed_by:
            d["entailed_by"] = asdict(self.entailed_by)
        return d


# --------------------------------------------------------------------------- #
# retrieval                                                                    #
# --------------------------------------------------------------------------- #
def _http_get(url: str, timeout: int = 25, retries: int = 3) -> Optional[str]:
    """GET with retry/backoff. arXiv/S2 transiently rate-limit or drop requests
    (the 2026-07-14 pilot saw whole batches return empty), so retry a few times
    before giving up. Returns None if all attempts fail."""
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "ASTRA-novelty-gate/1.0"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read().decode("utf-8", errors="replace")
        except Exception as e:
            logger.debug("[novelty] GET failed (attempt %d/%d) %s: %s",
                         attempt + 1, retries, url[:80], e)
            if attempt < retries - 1:
                time.sleep(2 * (attempt + 1))  # 2s, 4s backoff between attempts
    return None


def retrieve_arxiv(query: str, max_results: int = 5) -> List[Paper]:
    """Query arXiv Atom API. Returns papers (title+abstract). Rate-limited."""
    q = urllib.parse.quote(query)
    url = (f"{ARXIV_ENDPOINT}?search_query=all:{q}&start=0&max_results={max_results}"
           f"&sortBy=relevance")
    raw = _http_get(url)
    time.sleep(_RATE_SLEEP)  # respect arXiv's >=3s guideline
    if not raw:
        return []
    papers: List[Paper] = []
    try:
        ns = {"a": "http://www.w3.org/2005/Atom"}
        root = ET.fromstring(raw)
        for e in root.findall("a:entry", ns):
            title = (e.find("a:title", ns).text or "").strip().replace("\n", " ")
            summary = (e.find("a:summary", ns).text or "").strip().replace("\n", " ")
            arxiv_id = (e.find("a:id", ns).text or "").rsplit("/", 1)[-1]
            published = (e.find("a:published", ns).text or "")[:4]
            papers.append(Paper("arxiv", title, summary, arxiv_id, published))
    except Exception as e:
        logger.warning("[novelty] arXiv parse failed: %s", e)
    return papers


def retrieve_s2(query: str, max_results: int = 5) -> List[Paper]:
    """Query Semantic Scholar (optional; often rate-limited without a key)."""
    q = urllib.parse.quote(query)
    fields = "title,abstract,year,externalIds"
    url = (f"{S2_ENDPOINT}?query={q}&limit={max_results}&fields={fields}")
    raw = _http_get(url)
    time.sleep(_RATE_SLEEP)
    if not raw:
        return []
    try:
        data = json.loads(raw)
        if isinstance(data, dict) and data.get("code") == 429:
            return []  # rate-limited; silently skip
        papers = []
        for item in data.get("data", []) or []:
            papers.append(Paper(
                "s2",
                (item.get("title") or "").strip(),
                (item.get("abstract") or "").strip(),
                item.get("paperId", ""),
                str(item.get("year") or "")[:4]))
        return papers
    except Exception as e:
        logger.debug("[novelty] s2 parse failed: %s", e)
        return []


def _extract_query(claim: str) -> str:
    """Reduce a claim to arXiv-searchable terms, keeping DOMAIN NOUNS and
    dropping generic connective/statistical words.

    Earlier this kept the first 6 non-stopwords, which for a claim like
    "...galaxy's g-r color is positively correlated with ... redshift" yielded
    "sdss sample galaxy color positively correlated" — dropping 'redshift', the
    crucial term, so retrieval never fetched the photo-z papers that would entail
    it. We now drop generic stats words (correlated, significant, relation, …)
    and keep up to 8 domain-relevant terms.
    """
    stop = {"the", "a", "an", "of", "in", "with", "and", "to", "is", "are",
            "that", "this", "for", "on", "at", "by", "be", "from", "as", "it",
            "we", "show", "have", "has", "than", "more", "less", "very",
            "between", "into", "its", "their", "was", "were", "our", "these",
            "those", "such", "also", "using", "used", "use",
            # generic statistical / framing words — not useful as search terms
            "correlated", "correlation", "correlates", "positively", "negatively",
            "significant", "significantly", "strongly", "weakly", "relation",
            "relationship", "associated", "associate", "sample", "samples",
            "result", "results", "found", "find", "report", "reported",
            "higher", "lower", "greater", "fewer", "increase", "decrease",
            "evidence", "indicates", "indicate", "suggests", "suggest"}
    words = re.findall(r"[A-Za-z][A-Za-z0-9\-]+", claim.lower())
    terms = [w for w in words if w not in stop and len(w) > 2]
    # de-dup preserving order, keep up to 8
    seen, kept = set(), []
    for w in terms:
        if w not in seen:
            seen.add(w)
            kept.append(w)
    return " ".join(kept[:8]) or claim[:60]


# --------------------------------------------------------------------------- #
# the grounded entailment judge                                                #
# --------------------------------------------------------------------------- #
def _parse_judge_text(text: str) -> tuple:
    """Parse the judge's JSON verdict. Returns (confidence, verdict_dict);
    confidence is a float in [0, 1] or None when the judge did not state one.
    Returns (None, {}) when no JSON object is present."""
    m = re.search(r"\{.*\}", text or "", re.DOTALL)
    if not m:
        return None, {}
    try:
        verdict = json.loads(m.group(0))
    except ValueError:
        return None, {}
    conf = verdict.get("confidence")
    if isinstance(conf, (int, float)) and 0.0 <= float(conf) <= 1.0:
        conf = float(conf)
    else:
        conf = None
    return conf, verdict


def _judge_known(claim: str, papers: List[Paper]) -> tuple:
    """Ask the LLM whether ``claim`` is ALREADY-KNOWN (not a new discovery).

    A claim is already-known if EITHER:
      (a) one of the retrieved abstracts states or directly implies it (cite it), OR
      (b) it is a well-established foundational/textbook result the field treats as
          given (e.g. the Tully–Fisher relation, the basic colour–redshift
          correlation underpinning photometric redshifts, the luminosity function).

    (a) is grounded in retrieved text; (b) is a domain-knowledge judgement. Both
    are auditable via the returned ``reason_label`` and ``reasoning``. Be
    conservative: borderline claims lean toward 'known' (we would rather drop a
    marginal result than emit a textbook restatement as a 'discovery').

    Returns (known, entailing_paper, reason_label, reasoning, confidence).
    reason_label is 'entailed' | 'foundational' | 'novel'; confidence is the
    judge's self-reported [0, 1] calibration signal (recorded for ranking,
    never a verdict). On judge failure returns (False, None, '', '', None) —
    caller treats that conservatively (judge-failed)."""
    if not papers:
        return False, None, "", "", None
    gw = _get_gateway()
    if gw is None:
        return False, None, "", "", None
    abstracts = "\n\n".join(
        f"[{i}] {p.title} ({p.year})\n{p.abstract[:900]}"
        for i, p in enumerate(papers))
    system = (
        "You are a strict scientific novelty auditor. A candidate astrophysical "
        "CLAIM is ALREADY-KNOWN (not a new discovery) if EITHER (a) one of the "
        "RETRIEVED ABSTRACTS states or directly implies it — cite that abstract's "
        "index; OR (b) it is a well-established foundational / textbook result "
        "that the field treats as given (standard scaling relations, the basic "
        "colour–redshift correlation behind photometric redshifts, Tully–Fisher, "
        "the luminosity function, magnitude limits, K-corrections, etc.). Use "
        "retrieved text for (a) and standard domain knowledge for (b). When "
        "uncertain, lean toward already-known — a borderline claim should not be "
        "advertised as a new discovery.")
    user = (f"CANDIDATE CLAIM:\n{claim}\n\nRETRIEVED ABSTRACTS:\n{abstracts}\n\n"
            "Respond with ONLY JSON: "
            '{"known": true|false, "reason": "entailed"|"foundational"|"novel", '
            '"by_abstract": <int|null>, "confidence": <0.0-1.0>, '
            '"reasoning": "<one sentence>"}')
    try:
        text, _ = gw.complete(
            system=system, messages=[{"role": "user", "content": user}],
            max_tokens=300, caller="novelty_gate")
        conf, verdict = _parse_judge_text(text)
        if not verdict:
            return False, None, "", "", None
        known = bool(verdict.get("known"))
        label = str(verdict.get("reason", ""))[:24]
        idx = verdict.get("by_abstract")
        reasoning = str(verdict.get("reasoning", ""))[:300]
        entailing = None
        if known and isinstance(idx, int) and 0 <= idx < len(papers):
            entailing = papers[idx]
        return known, entailing, label, reasoning, conf
    except Exception as e:
        logger.warning("[novelty] judge failed: %s", e)
        return False, None, "", "", None


# --------------------------------------------------------------------------- #
# caching                                                                      #
# --------------------------------------------------------------------------- #
def _cache_key(claim: str) -> str:
    norm = re.sub(r"\s+", " ", re.sub(r"[^A-Za-z0-9 ]", " ", claim.lower())).strip()
    return hashlib.sha1(norm.encode()).hexdigest()[:16]


def _load_cache() -> dict:
    try:
        if CACHE_PATH.exists():
            return json.loads(CACHE_PATH.read_text())
    except Exception:
        pass
    return {}


def _save_cache(cache: dict) -> None:
    try:
        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        CACHE_PATH.write_text(json.dumps(cache, indent=2, default=str))
    except Exception as e:
        logger.debug("[novelty] cache save failed: %s", e)


# --------------------------------------------------------------------------- #
# public entry point                                                           #
# --------------------------------------------------------------------------- #
def _retrieve_papers(query: str, use_s2: bool, max_results: int = 5) -> List[Paper]:
    """Retrieve + de-dup papers from arXiv (and optionally S2) for a query."""
    papers = retrieve_arxiv(query, max_results=max_results)
    if use_s2:
        papers += retrieve_s2(query, max_results=max_results)
    seen, deduped = set(), []
    for p in papers:
        k = p.title.lower()[:80]
        if k and k not in seen:
            seen.add(k)
            deduped.append(p)
    return deduped[:8]


def check_novelty(claim: str, use_s2: bool = True, force: bool = False) -> NoveltyResult:
    """Gate 2: return whether ``claim`` is novel (not in the literature).

    Conservative on failure: retrieval- or judge-failures are NOT promoted as
    novel (``novel=False`` with a ``status`` explaining why).
    """
    if not claim or not claim.strip():
        return NoveltyResult(False, "judge-failed", claim, reasoning="empty claim")

    key = _cache_key(claim)
    cache = _load_cache()
    if not force and key in cache:
        c = cache[key]
        return NoveltyResult(c.get("novel", False), c.get("status", "?"),
                             claim, None, c.get("n_retrieved", 0),
                             c.get("reasoning", ""),
                             confidence=c.get("confidence"),
                             revision=int(c.get("revision", 0)))

    # forced re-judgement: archive the prior verdict so the iteration history
    # of how this claim's novelty assessment evolved is preserved (Egent
    # provenance rule — archive outputs, never assume a re-run reproduces)
    history = list(cache.get(key, {}).get("history", []))
    if key in cache:
        history.append({"status": cache[key].get("status"),
                        "ts": time.strftime("%Y-%m-%dT%H:%M:%S")})

    query = _extract_query(claim)
    logger.info("[novelty] retrieving for claim (query=%r)", query)
    papers = _retrieve_papers(query, use_s2)
    if not papers:
        # Transient rate-limiting can return empty on the first pass (the
        # 2026-07-14 pilot saw whole batches come back empty). Retry once after
        # backoff before declaring retrieval-failed.
        logger.info("[novelty] no papers on first pass; retrying after backoff")
        time.sleep(_RATE_SLEEP)
        papers = _retrieve_papers(query, use_s2)

    if not papers:
        # Retrieval genuinely failed. This is TRANSIENT — do NOT cache it, so the
        # next run retries instead of inheriting a permanent "failed" verdict.
        return NoveltyResult(False, "retrieval-failed", claim, n_retrieved=0,
                             reasoning="no papers retrieved after retry; novelty unverified")

    # deterministic pre-check tier: features are logged beside every verdict
    # so any future auto-known threshold is measured, not assumed (see
    # novelty_precheck.py for the 2026-08-20 calibration negative result)
    from . import novelty_precheck as _pc
    feats = _pc.precheck_features(claim, [asdict(p) for p in papers])
    if _pc.should_auto_known(feats):
        res = NoveltyResult(False, "known", claim, entailed_by=papers[feats.get(
            "top_similarity_idx", 0)] if feats.get("top_similarity_idx", -1) >= 0
            else None, n_retrieved=len(papers),
            reasoning="auto-known: top_similarity above armed tau",
            retrieved=papers)
        cache[key] = res.to_dict()
        _save_cache(cache)
        _pc.log_precheck(feats, "known-auto")
        logger.info("[novelty] known-auto (tau tier) — %s", claim[:60])
        return res

    known, entailing, label, reasoning, confidence = _judge_known(claim, papers)
    if not label and not reasoning:
        # judge itself failed -> conservative
        res = NoveltyResult(False, "judge-failed", claim, n_retrieved=len(papers),
                            reasoning="LLM novelty judge unavailable")
        cache[key] = res.to_dict()
        _save_cache(cache)
        return res

    if known:
        reason = (f"{label}: {reasoning}") if label else reasoning
        res = NoveltyResult(False, "known", claim, entailed_by=entailing,
                            n_retrieved=len(papers), reasoning=reason,
                            retrieved=papers)
    else:
        res = NoveltyResult(True, "novel", claim, n_retrieved=len(papers),
                            reasoning=reasoning, retrieved=papers)
    res.confidence = confidence
    res.revision = len(history)
    cache[key] = res.to_dict()
    if confidence is not None:
        cache[key]["confidence"] = confidence
    if history:
        cache[key]["history"] = history
        cache[key]["revision"] = len(history)
    _save_cache(cache)
    _pc.log_precheck(feats, res.status, confidence=confidence)
    logger.info("[novelty] %s — %s (n=%d)", res.status, claim[:60], len(papers))
    return res


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    claim = " ".join(sys.argv[1:]) or "Galaxies with redder g-r color are at higher redshift in SDSS"
    r = check_novelty(claim)
    print(json.dumps(r.to_dict(), indent=2)[:1500])
