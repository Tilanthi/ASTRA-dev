"""Token-cost accounting for the LLM gateway.

The gateway has always received usage from the API and dropped it on the
floor — every token estimate for ASTRA was guesswork. These tests pin the
fix: usage is appended per call to a JSONL ledger, tagged by caller, and
daily totals are readable back.

Run: python3 astra_core/tests/test_token_ledger.py
"""
import json
import os
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from astra_core.intelligence import token_ledger  # noqa: E402
from astra_core.intelligence.llm_gateway import LLMGateway  # noqa: E402


class _Block:
    def __init__(self, text):
        self.text = text


class _Usage:
    def __init__(self, i, o):
        self.input_tokens = i
        self.output_tokens = o


class _Response:
    def __init__(self):
        self.content = [_Block("ok")]
        self.usage = _Usage(2500, 300)


class _Messages:
    def create(self, **kwargs):
        return _Response()


def _stub_gateway():
    gw = LLMGateway.__new__(LLMGateway)
    gw.client = type("C", (), {"messages": _Messages()})()
    gw.model = "test-model"
    gw.max_tokens = 4096
    gw.timeout = 90.0
    return gw


def test_record_usage_appends_tagged_line():
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "ledger.jsonl"
        token_ledger.record_usage("novelty_gate", "glm-4.6",
                                  {"input_tokens": 100, "output_tokens": 5},
                                  ledger_path=path)
        lines = [json.loads(x) for x in path.read_text().splitlines()]
        assert len(lines) == 1
        row = lines[0]
        assert row["caller"] == "novelty_gate"
        assert row["model"] == "glm-4.6"
        assert row["input_tokens"] == 100
        assert row["output_tokens"] == 5
        assert row["ts"]


def test_gateway_complete_records_when_caller_given():
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "ledger.jsonl"
        gw = _stub_gateway()
        text, usage = gw.complete(system="s", messages=[{"role": "user",
                                                         "content": "hi"}],
                                  caller="test_call", ledger_path=path)
        assert text == "ok" and usage["input_tokens"] == 2500
        row = json.loads(path.read_text().splitlines()[0])
        assert row["caller"] == "test_call"
        assert row["input_tokens"] == 2500 and row["output_tokens"] == 300


def test_gateway_complete_silent_without_caller():
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "ledger.jsonl"
        gw = _stub_gateway()
        gw.complete(system="s", messages=[{"role": "user", "content": "hi"}],
                    ledger_path=path)
        assert not path.exists() or not path.read_text().strip()


def test_daily_totals_aggregates_by_day():
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "ledger.jsonl"
        token_ledger.record_usage("a", "m", {"input_tokens": 10, "output_tokens": 1},
                                  ledger_path=path, ts="2026-08-19T10:00:00")
        token_ledger.record_usage("b", "m", {"input_tokens": 20, "output_tokens": 2},
                                  ledger_path=path, ts="2026-08-19T11:00:00")
        token_ledger.record_usage("a", "m", {"input_tokens": 5, "output_tokens": 0},
                                  ledger_path=path, ts="2026-08-18T09:00:00")
        totals = token_ledger.daily_totals(ledger_path=path)
        assert totals["2026-08-19"]["input_tokens"] == 30
        assert totals["2026-08-19"]["output_tokens"] == 3
        assert totals["2026-08-18"]["input_tokens"] == 5


def test_default_path_branch_does_not_crash():
    """Regression (2026-08-20): the ledger_path PARAMETER shadowed the
    module-level path function, so the default branch called None(). The live
    gateway never passes an explicit path — this crash turned every tagged
    LLM call into an exception (and the novelty judge into judge-failed)."""
    import os
    with tempfile.TemporaryDirectory() as d:
        os.environ["ASTRA_TOKEN_LEDGER"] = str(Path(d) / "led.jsonl")
        try:
            token_ledger.record_usage("x", "m", {"input_tokens": 1,
                                                 "output_tokens": 1},
                                      ts="2026-08-20T00:00:00")
            assert token_ledger.daily_totals()["2026-08-20"]["calls"] == 1
        finally:
            del os.environ["ASTRA_TOKEN_LEDGER"]


if __name__ == "__main__":
    for name, fn in sorted(list(globals().items())):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"PASS {name}")
    print("all tests passed")
