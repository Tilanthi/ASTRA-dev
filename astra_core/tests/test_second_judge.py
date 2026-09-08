"""Tests for second_judge.py — F1 (2026-09-08): cross-model judge at promotion.

Pins the honesty contract of the promotion-time second-family audit:
  * unconfigured is unconfigured — status "not-configured", block False, and
    the gateway loader / retrieval are NEVER touched (no fabricated pass, no
    accidental spend);
  * only the GROUNDED ground blocks: known + "entailed" + an in-range
    by_abstract citation. A "foundational" judgement (known but ungrounded)
    records and never blocks;
  * retrieval-failed / judge-failed / exceptions are recorded as themselves,
    never upgraded to a pass;
  * empty-context: the judge sees the claim and the retrieved abstracts ONLY
    — no proposer reasoning, no program source — and the call is ledgered
    under caller="second_judge" with the configured model + token override.

All external touchpoints (novelty retrieval, the LLM gateway) are faked; no
network, no token spend, no persistent store is touched.

Run: python3 astra_core/tests/test_second_judge.py
"""
import json
import os
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from astra_core.scientific_discovery.evolved_analysis import second_judge as sj  # noqa: E402
from astra_core.scientific_discovery.evolved_analysis import novelty_gate as ng  # noqa: E402
from astra_core.scientific_discovery.evolved_analysis import _llm  # noqa: E402


CLAIM = "Galaxies with redder g-r colour reside at higher redshift in SDSS"
PAPERS = [
    ng.Paper("arxiv", "Photometric redshifts from galaxy colours",
             "We show galaxy colour correlates with redshift.", "1001.0001", "2010"),
    ng.Paper("arxiv", "Unrelated paper about pulsar timing",
             "Pulsar timing residuals constrain planet masses.", "1001.0002", "2011"),
]

_JUDGE_ENV = {"ASTRA_JUDGE2_TOKEN": "test-token-xyz",
              "ASTRA_JUDGE2_MODEL": "other-family-x",
              "ASTRA_JUDGE2_BASE_URL": "https://judge2.example/api"}


class _Env:
    """Set/restore the judge-2 environment for one test."""

    def __init__(self, env=None):
        self.env = env if env is not None else _JUDGE_ENV

    def __enter__(self):
        self.backup = {k: os.environ.pop(k) for k in list(_JUDGE_ENV)
                       if k in os.environ}
        os.environ.update(self.env)
        return self

    def __exit__(self, *exc):
        for k in _JUDGE_ENV:
            os.environ.pop(k, None)
        os.environ.update(self.backup)
        return False


class _FakeGatewayModule:
    """Stand-in for the canonical gateway module: records the constructor's
    endpoint overrides and the complete() call, replays canned responses."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.captured = []

    class LLMGateway:
        captured = None  # set on the module instance below

        def __init__(self, model=None, auth_token=None, base_url=None, **kw):
            self._m = type(self)._mod
            self._m.captured.append(
                {"what": "init", "model": model, "auth_token": auth_token,
                 "base_url": base_url})

        def complete(self, system, messages, model=None, max_tokens=None,
                     caller=None, ledger_path=None):
            self._m.captured.append(
                {"what": "complete", "system": system,
                 "content": messages[0]["content"], "model": model,
                 "max_tokens": max_tokens, "caller": caller})
            return self._m.responses.pop(0), {"input_tokens": 10,
                                              "output_tokens": 10}


def _fake_gateway(monkeypatch, responses):
    """Patch _llm.gateway_module with a recording fake; returns the recorder."""
    mod_holder = _FakeGatewayModule(responses)

    class _GW(_FakeGatewayModule.LLMGateway):
        _mod = mod_holder
    mod_holder.LLMGateway = _GW

    def loader():
        return mod_holder
    monkeypatch.setattr(_llm, "gateway_module", loader)
    # second_judge does `from ._llm import gateway_module` at call time
    return mod_holder


def _fake_retrieval(monkeypatch, papers):
    calls = {"n": 0}

    def fake(query, use_s2=True, max_results=5):
        calls["n"] += 1
        return list(papers)
    monkeypatch.setattr(ng, "_retrieve_papers", fake)
    return calls


def _judge_json(known, reason, by_abstract, confidence=0.9):
    return json.dumps({"known": known, "reason": reason,
                       "by_abstract": by_abstract, "confidence": confidence,
                       "reasoning": f"judge says {reason}"})


class _SimpleMonkey:
    """Minimal monkeypatch for the plain (non-pytest) runner."""

    def __init__(self):
        self._undo = []

    def setattr(self, obj, name, value):
        self._undo.append((obj, name, getattr(obj, name)))
        setattr(obj, name, value)

    def undo(self):
        for obj, name, old in reversed(self._undo):
            setattr(obj, name, old)
        self._undo = []


# --------------------------------------------------------------------------- #
# unconfigured: honest, zero-touch                                             #
# --------------------------------------------------------------------------- #
def test_not_configured_is_honest_and_touches_nothing(monkeypatch):
    def _never_loader():
        raise AssertionError("gateway loader invoked while unconfigured")
    monkeypatch.setattr(_llm, "gateway_module", _never_loader)
    calls = _fake_retrieval(monkeypatch, PAPERS)
    with _Env(env={}):                      # nothing configured
        res = sj.audit_claim(CLAIM, dataset="sdss_qso")
    assert res["status"] == "not-configured"
    assert res["block"] is False
    assert calls["n"] == 0, "retrieval ran while unconfigured"


def test_partial_config_is_still_not_configured(monkeypatch):
    """Token without model (or model without token) is NOT a second family —
    a same-model second call is spend without information."""
    monkeypatch.setattr(_llm, "gateway_module",
                        lambda: (_ for _ in ()).throw(
                            AssertionError("loader invoked")))
    with _Env(env={"ASTRA_JUDGE2_TOKEN": "t"}):
        assert sj.audit_claim(CLAIM)["status"] == "not-configured"
    with _Env(env={"ASTRA_JUDGE2_MODEL": "m"}):
        assert sj.audit_claim(CLAIM)["status"] == "not-configured"


# --------------------------------------------------------------------------- #
# blocking: the grounded ground only                                           #
# --------------------------------------------------------------------------- #
def test_entailed_known_with_citation_blocks(monkeypatch):
    _fake_retrieval(monkeypatch, PAPERS)
    rec = _fake_gateway(monkeypatch, [_judge_json(True, "entailed", 0)])
    with _Env():
        res = sj.audit_claim(CLAIM, dataset="sdss_qso")
    assert res["status"] == "judged"
    assert res["block"] is True
    assert res["known"] is True and res["reason"] == "entailed"
    assert res["by_abstract"] == 0
    assert res["entailed_by"] == PAPERS[0].title
    assert res["model"] == "other-family-x"
    assert res["dataset"] == "sdss_qso"


def test_foundational_known_does_not_block(monkeypatch):
    """known=true, reason='foundational', no abstract citation: ungrounded
    domain knowledge — recorded, never blocking (fiction-adjacent class)."""
    _fake_retrieval(monkeypatch, PAPERS)
    _fake_gateway(monkeypatch, [_judge_json(True, "foundational", None)])
    with _Env():
        res = sj.audit_claim(CLAIM)
    assert res["status"] == "judged"
    assert res["block"] is False
    assert res["known"] is True and res["reason"] == "foundational"


def test_entailed_with_out_of_range_citation_does_not_block(monkeypatch):
    """A citation that points past the retrieved set is a judge malfunction,
    not a ground — recorded, not blocking (gate-2's own entailing semantics)."""
    _fake_retrieval(monkeypatch, PAPERS)
    _fake_gateway(monkeypatch, [_judge_json(True, "entailed", 99)])
    with _Env():
        res = sj.audit_claim(CLAIM)
    assert res["block"] is False
    assert res["by_abstract"] == 99


def test_novel_verdict_does_not_block(monkeypatch):
    _fake_retrieval(monkeypatch, PAPERS)
    _fake_gateway(monkeypatch, [_judge_json(False, "novel", None)])
    with _Env():
        res = sj.audit_claim(CLAIM)
    assert res["status"] == "judged"
    assert res["block"] is False and res["known"] is False


# --------------------------------------------------------------------------- #
# failure honesty                                                              #
# --------------------------------------------------------------------------- #
def test_retrieval_failure_is_honest_nonblocking(monkeypatch):
    _fake_retrieval(monkeypatch, [])
    def _never():
        raise AssertionError("gateway reached with no papers")
    monkeypatch.setattr(_llm, "gateway_module", _never)
    with _Env():
        res = sj.audit_claim(CLAIM)
    assert res["status"] == "retrieval-failed"
    assert res["block"] is False


def test_judge_failure_is_honest_nonblocking(monkeypatch):
    _fake_retrieval(monkeypatch, PAPERS)
    _fake_gateway(monkeypatch, ["no json here at all"])
    with _Env():
        res = sj.audit_claim(CLAIM)
    assert res["status"] == "judge-failed"
    assert res["block"] is False
    assert res["n_retrieved"] == len(PAPERS)


def test_exception_is_recorded_never_raised(monkeypatch):
    _fake_retrieval(monkeypatch, PAPERS)

    class _Boom:
        class LLMGateway:
            def __init__(self, **kw):
                raise RuntimeError("endpoint down")
    monkeypatch.setattr(_llm, "gateway_module", lambda: _Boom())
    with _Env():
        res = sj.audit_claim(CLAIM)
    assert res["status"] == "error"
    assert res["block"] is False
    assert "endpoint down" in res["error"]


# --------------------------------------------------------------------------- #
# empty-context + provenance                                                   #
# --------------------------------------------------------------------------- #
def test_prompt_is_empty_context_and_ledgered_correctly(monkeypatch):
    """The judge sees the claim and the retrieved abstracts ONLY: no proposer
    reasoning, no program source, no dataset verdict history. And the call is
    ledgered under caller='second_judge' with the configured model."""
    _fake_retrieval(monkeypatch, PAPERS)
    rec = _fake_gateway(monkeypatch, [_judge_json(False, "novel", None)])
    with _Env():
        sj.audit_claim(CLAIM, dataset="sdss_qso")
    init = [c for c in rec.captured if c["what"] == "init"][0]
    call = [c for c in rec.captured if c["what"] == "complete"][0]
    # endpoint overrides flow through the canonical gateway constructor
    assert init["model"] == "other-family-x"
    assert init["auth_token"] == "test-token-xyz"
    assert init["base_url"] == "https://judge2.example/api"
    assert call["caller"] == "second_judge"      # token-ledger id
    # no per-call model override: the audit relies on the gateway constructed
    # with the judge-2 model (asserted above via init["model"])
    assert call["model"] is None
    # empty-context contract: claim + abstracts, nothing else
    assert CLAIM in call["content"]
    assert PAPERS[0].title in call["content"] and PAPERS[1].title in call["content"]
    assert "df_train" not in call["content"]      # no program source
    assert "sdss_qso" not in call["content"]      # no dataset context in the prompt
    assert "proposer" not in call["content"].lower()


def test_main_smoke_without_claim_is_zero_spend(monkeypatch, capsys=None):
    """The __main__ config smoke prints configuration state and makes no
    call at all (config printed without any network/gateway touch)."""
    import io
    import contextlib
    monkeypatch.setattr(_llm, "gateway_module",
                        lambda: (_ for _ in ()).throw(
                            AssertionError("loader invoked")))
    monkeypatch.setattr(sys, "argv", ["second_judge"])
    with _Env(env={}):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = sj.main()
    out = buf.getvalue()
    assert rc == 0
    assert '"configured": false' in out
    # and the full audit smoke (claim arg) with no env returns not-configured
    monkeypatch.setattr(sys, "argv", ["second_judge", CLAIM])
    with _Env(env={}):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = sj.main()
    assert rc == 0
    assert '"status": "not-configured"' in buf.getvalue()


if __name__ == "__main__":
    import inspect
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in fns:
        monkey = _SimpleMonkey()
        kwargs = {}
        if "monkeypatch" in inspect.signature(fn).parameters:
            kwargs["monkeypatch"] = monkey
        try:
            fn(**kwargs)
        except AssertionError as ex:
            failed += 1
            print(f"FAIL {fn.__name__}: {ex}")
        except Exception as ex:  # noqa: BLE001
            failed += 1
            print(f"ERROR {fn.__name__}: {type(ex).__name__}: {ex}")
        else:
            print(f"PASS {fn.__name__}")
        finally:
            monkey.undo()
    print(f"\n{len(fns) - failed}/{len(fns)} passed")
    sys.exit(1 if failed else 0)
