"""llm_gateway.py — ASTRA's canonical Anthropic LLM gateway.

This module is the ONE place in ASTRA that owns a real Anthropic client.
Every ASTRA subsystem that needs a genuine LLM completion (not a symbolic /
template string) should go through :class:`LLMGateway` or :func:`get_gateway`.

Design notes
------------
* The STAN component's ``answer()`` (see ``astra_core/core/unified.py``) is a
  symbolic / hardcoded template layer — it is NOT an LLM brain and is NOT wired
  up here. This gateway is the real LLM path.
* Authentication is read from the environment:
      - ``ANTHROPIC_AUTH_TOKEN`` (preferred) or ``ANTHROPIC_API_KEY`` for the
        token (auth_token).
      - ``ANTHROPIC_BASE_URL`` for an alternate API base URL (may be unset /
        None, in which case the SDK default is used).
* The default model is taken from ``ASTRA_LLM_MODEL`` if set, otherwise
  ``claude-sonnet-5-20250929``.
* ``anthropic`` is imported lazily inside ``__init__`` / methods so that this
  module can be imported safely even when the ``anthropic`` package is not
  installed.
"""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Tuple


class LLMGateway:
    """Canonical Anthropic client wrapper used across ASTRA.

    Construction does NOT make a network call; it only reads credentials from
    the environment and builds the SDK client object.
    """

    def __init__(self, model: Optional[str] = None,
                 max_tokens: int = 4096, timeout: float = 90.0):
        import anthropic  # local import: module imports even if SDK absent

        token = (os.environ.get("ANTHROPIC_AUTH_TOKEN")
                 or os.environ.get("ANTHROPIC_API_KEY"))
        base = os.environ.get("ANTHROPIC_BASE_URL")
        if not token:
            raise RuntimeError(
                "No ANTHROPIC_AUTH_TOKEN / ANTHROPIC_API_KEY set")
        # base_url may be None — the SDK accepts that and uses its default.
        self.client = anthropic.Anthropic(base_url=base, auth_token=token)
        self.model = (model
                      or os.environ.get("ASTRA_LLM_MODEL")
                      or "claude-sonnet-5-20250929")
        self.max_tokens = max_tokens
        self.timeout = timeout

    def complete(self, system: str, messages: List[Dict[str, Any]],
                 model: Optional[str] = None,
                 max_tokens: Optional[int] = None) -> Tuple[str, Dict[str, int]]:
        """Run a single messages.create call and return (text, usage).

        ``text`` is the concatenation of every text block in the response.
        ``usage`` is ``{"input_tokens": int, "output_tokens": int}`` (0 when
        the SDK does not report a value).
        """
        r = self.client.messages.create(
            model=model or self.model,
            max_tokens=max_tokens if max_tokens is not None else self.max_tokens,
            system=system,
            messages=messages,
        )
        text = "".join(b.text for b in r.content if hasattr(b, "text"))
        usage = {
            "input_tokens": getattr(r.usage, "input_tokens", 0),
            "output_tokens": getattr(r.usage, "output_tokens", 0),
        }
        return text, usage


# --------------------------------------------------------------------------- #
# lazy module-level singleton                                                  #
# --------------------------------------------------------------------------- #
_GATEWAY: Optional[LLMGateway] = None


def get_gateway() -> LLMGateway:
    """Return a cached default :class:`LLMGateway`, creating it on first use."""
    global _GATEWAY
    if _GATEWAY is None:
        _GATEWAY = LLMGateway()
    return _GATEWAY
