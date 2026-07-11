"""autonomous_discovery_supervisor.py — the always-on, user-yielding discovery
supervisor that REPLACES the legacy fiction emitter.

Why this exists
---------------
The legacy ``FixedGenuineDiscoverySystem`` (autonomous_startup_discovery_v2.py)
ran the loop ``template-query -> STAN answer() -> hardcoded string -> 'discovery'``
and wrote the result to the genuine store ~once per 60 s. Because STAN's
``answer()`` returns a hardcoded string (astra_core/core/unified.py), every
record it produced was fiction — a direct violation of ASTRA's prime directive
("NO FICTIONAL/SYNTHETIC DISCOVERIES"). See
docs/superpowers/specs/2026-07-11-astra-autonomous-discovery-rearchitecture-design.md.

This supervisor does the opposite by construction. It has exactly two activities,
both machine-graded:

  1. **Ingest** machine-verified discoveries from ``evolved_discoveries.json``
     into the genuine store, through the ``discovery_store`` chokepoint (a
     record without a ``verification`` block CANNOT be written).
  2. **Produce** new candidates by periodically launching the proven
     AlphaEvolve-style evolutionary engine as an ISOLATED subprocess on real
     SDSS data. Its verified outputs flow back via ``evolved_discoveries.json``.

There is no text-generation path. If nothing verifies, nothing is written; the
loop simply waits. "Cannot emit fiction" is structural.

Assistant-first, autonomous-second
----------------------------------
Before launching a new evolution subprocess, the supervisor checks a user-active
heartbeat (``~/.astra_persistent/user_active`` mtime). If the assistant is in
use, it holds off starting new work (an in-progress subprocess finishes
naturally). The yield is a plain mtime check — NO threading primitives —
deliberately avoiding the pause/resume deadlock surface (CLAUDE.md v5.0).

Module loading is kept light (no heavy ``astra_core`` import at top level) so
the LaunchAgent starts fast and cannot deadlock on ASTRA's heavy ``__init__``.
"""
from __future__ import annotations

import logging
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

PERSIST_DIR = Path.home() / ".astra_persistent"
GENUINE_PATH = PERSIST_DIR / "genuine_discoveries.json"
USER_ACTIVE_FILE = PERSIST_DIR / "user_active"
# Optional KEY=VALUE file the supervisor sources for the evolution subprocess's
# LLM credentials. Lets autonomous evolution run under launchd (which does NOT
# inherit shell env vars) WITHOUT putting a secret in the LaunchAgent plist.
LLM_ENV_FILE = PERSIST_DIR / "llm_env"
REPO_ROOT = Path(__file__).resolve().parents[1]

# Default evolution subprocess module (the proven Phase-1 engine). The actual
# module is resolved per-instance from os.environ OR the llm_env file (see
# __init__), so ASTRA_EVOLUTION_MODULE set in ~/.astra_persistent/llm_env works
# under launchd (where shell env vars are not inherited). Runs with
# PYTHONPATH=astra_core/scientific_discovery so it imports without triggering
# astra_core/__init__ (decoupled — deadlock history).
_DEFAULT_EVOLUTION_MODULE = "evolved_analysis.run_engine"
_EVOLUTION_PYTHONPATH = str(REPO_ROOT / "astra_core" / "scientific_discovery")


def touch_user_active() -> None:
    """Mark the assistant as in-use (called by the CLI / assistant layer).

    The supervisor treats the user as active for ``USER_ACTIVE_WINDOW_S`` after
    each call, and yields discovery work during that window.
    """
    try:
        PERSIST_DIR.mkdir(parents=True, exist_ok=True)
        # utime updates mtime/atime without needing to open for write
        os.utime(USER_ACTIVE_FILE, None) if USER_ACTIVE_FILE.exists() else \
            USER_ACTIVE_FILE.touch()
    except Exception as e:  # never let a heartbeat update crash the caller
        logger.debug("[Supervisor] touch_user_active failed: %s", e)


def is_user_active(window_seconds: int = 300) -> bool:
    """True iff the assistant heartbeat is fresher than ``window_seconds``."""
    try:
        if not USER_ACTIVE_FILE.exists():
            return False
        age = time.time() - USER_ACTIVE_FILE.stat().st_mtime
        return age < window_seconds
    except Exception:
        return False


class AutonomousDiscoverySupervisor:
    """Run forever: ingest verified discoveries + (when idle) evolve new ones.

    Attributes the evolved-discovery consumer expects on ``system``:
    ``genuine_discoveries`` (list). Hydrated from disk on init.
    """

    def __init__(self,
                 cycle_seconds: int = 300,
                 evolution_interval_seconds: int = 1800,
                 evolution_timeout_seconds: int = 1200,
                 user_active_window_seconds: int = 300):
        self.cycle_seconds = max(60, int(cycle_seconds))
        self.evolution_interval_seconds = int(evolution_interval_seconds)
        self.evolution_timeout_seconds = int(evolution_timeout_seconds)
        self.user_active_window_seconds = int(user_active_window_seconds)

        self.discoverystore_path = GENUINE_PATH
        self.genuine_discoveries: List[Dict[str, Any]] = []
        self.discovery_cycle = 0
        self.last_evolution_at = 0.0
        self.start_time = time.time()
        self.stop_requested = False

        self._evolution_disabled = (
            os.environ.get("ASTRA_DISCOVERY_EVOLUTION_DISABLED", "").lower()
            in ("1", "true", "yes")
        )
        # Resolve the evolution module from the process env OR the llm_env file
        # (launchd doesn't inherit shell vars, so ASTRA_EVOLUTION_MODULE in
        # llm_env must be honoured here, not just passed to the subprocess).
        self._evolution_module = (
            os.environ.get("ASTRA_EVOLUTION_MODULE")
            or self._load_llm_env().get("ASTRA_EVOLUTION_MODULE")
            or _DEFAULT_EVOLUTION_MODULE
        )
        if self._evolution_disabled:
            logger.info("[Supervisor] evolution episodes DISABLED by "
                        "ASTRA_DISCOVERY_EVOLUTION_DISABLED. Ingest-only mode.")
        elif not self._llm_token_available():
            self._evolution_disabled = True
            logger.info("[Supervisor] evolution episodes DISABLED: no LLM token "
                        "in env or %s. Ingest-only mode. Put ANTHROPIC_AUTH_TOKEN "
                        "(and ANTHROPIC_BASE_URL) in that file to enable.",
                        LLM_ENV_FILE.name)

        self._hydrate()
        logger.info("[Supervisor] initialised: cycle=%ds, evolution every=%ds "
                    "(timeout %ds), user-active window=%ds",
                    self.cycle_seconds, self.evolution_interval_seconds,
                    self.evolution_timeout_seconds, self.user_active_window_seconds)

    # ------------------------------------------------------------------ #
    # store hydration + persistence (through the chokepoint)             #
    # ------------------------------------------------------------------ #
    def _hydrate(self) -> None:
        try:
            from astra_core.scientific_discovery.discovery_store import (
                load_verified, dedup_verified)
            recs, dropped = dedup_verified(load_verified(self.discoverystore_path))
            self.genuine_discoveries = recs
            if dropped:
                logger.info("[Supervisor] dropped %d duplicate(s) on hydrate", dropped)
            logger.info("[Supervisor] hydrated %d machine-verified discovery(ies)",
                        len(recs))
        except Exception as e:
            logger.warning("[Supervisor] hydration failed (starting empty): %s", e)
            self.genuine_discoveries = []

    def _persist(self) -> None:
        """Write the verified, deduped store to disk (chokepoint writer)."""
        try:
            from astra_core.scientific_discovery.discovery_store import (
                has_machine_verification, dedup_verified, save_bucket)
            verified, dropped = dedup_verified(
                [d for d in self.genuine_discoveries if has_machine_verification(d)])
            if dropped:
                logger.info("[Supervisor] dropped %d duplicate(s) before persist",
                            dropped)
            save_bucket(self.discoverystore_path, verified)
        except Exception as e:
            logger.warning("[Supervisor] persist failed: %s", e)

    # ------------------------------------------------------------------ #
    # LLM credentials (env + optional llm_env file for the launchd case) #
    # ------------------------------------------------------------------ #
    @staticmethod
    def _load_llm_env() -> Dict[str, str]:
        """Read KEY=VALUE lines from ~/.astra_persistent/llm_env (if present)."""
        env: Dict[str, str] = {}
        try:
            if LLM_ENV_FILE.exists():
                for line in LLM_ENV_FILE.read_text().splitlines():
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip().strip('"').strip("'")
        except Exception:
            pass
        return env

    def _llm_token_available(self) -> bool:
        """True if a token is available from the process env or the llm_env file."""
        if os.environ.get("ANTHROPIC_AUTH_TOKEN") or os.environ.get("ANTHROPIC_API_KEY"):
            return True
        env = self._load_llm_env()
        return bool(env.get("ANTHROPIC_AUTH_TOKEN") or env.get("ANTHROPIC_API_KEY"))

    def _evolution_env(self) -> Dict[str, str]:
        """Env for the evolution subprocess: process env + llm_env file merges."""
        env = {**os.environ}
        env.update(self._load_llm_env())
        env["PYTHONPATH"] = _EVOLUTION_PYTHONPATH
        return env

    # ------------------------------------------------------------------ #
    # the two activities                                                 #
    # ------------------------------------------------------------------ #
    def _ingest(self) -> int:
        """Fold new machine-verified evolved discoveries into the store."""
        try:
            from astra_core.scientific_discovery.evolved_discovery_consumer import (
                consume_evolved_discoveries)
            n = consume_evolved_discoveries(self)
            if n:
                self._persist()
            return n
        except Exception as e:  # never crash the loop on a consume error
            logger.warning("[Supervisor] ingest skipped: %s", e)
            return 0

    def _maybe_evolve(self) -> None:
        """Launch one isolated evolution episode if idle and due. Never blocks
        the loop on failure; the subprocess is time-boxed and its stdout/stderr
        go to DEVNULL (the pipe-deadlock lesson, CLAUDE.md v7.0)."""
        if self._evolution_disabled:
            return
        if time.time() - self.last_evolution_at < self.evolution_interval_seconds:
            return
        if is_user_active(self.user_active_window_seconds):
            logger.info("[Supervisor] user active — deferring evolution episode")
            return

        self.last_evolution_at = time.time()
        logger.info("[Supervisor] launching evolution episode: python -m %s "
                    "(timeout %ds)", self._evolution_module, self.evolution_timeout_seconds)
        try:
            env = self._evolution_env()
            # DEVNULL, not PIPE: the parent never drains pipes (the v7.0 deadlock).
            proc = subprocess.run(
                [sys.executable, "-m", self._evolution_module],
                cwd=str(REPO_ROOT), env=env,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                timeout=self.evolution_timeout_seconds, check=False)
            logger.info("[Supervisor] evolution episode exited rc=%d", proc.returncode)
        except subprocess.TimeoutExpired:
            logger.warning("[Supervisor] evolution episode timed out after %ds "
                           "(partial results, if any, will be ingested next cycle)",
                           self.evolution_timeout_seconds)
        except Exception as e:
            logger.warning("[Supervisor] evolution episode failed: %s", e)

    # ------------------------------------------------------------------ #
    # the loop                                                           #
    # ------------------------------------------------------------------ #
    def run_forever(self) -> None:
        logger.info("[Supervisor] ========== AUTONOMOUS DISCOVERY SUPERVISOR "
                    "STARTED (fiction-free) ==========")
        while not self.stop_requested:
            self.discovery_cycle += 1
            try:
                ingested = self._ingest()
                self._maybe_evolve()
                logger.info("[Supervisor] cycle %d complete (ingested %d new; "
                            "store=%d)", self.discovery_cycle, ingested,
                            len(self.genuine_discoveries))
            except Exception as e:  # never let a cycle error kill the supervisor
                logger.error("[Supervisor] cycle %d error (continuing): %s",
                             self.discovery_cycle, e)

            # interruptible sleep between cycles (no blocking primitives)
            self._interruptible_sleep(self.cycle_seconds)

        logger.info("[Supervisor] stopped after %d cycles",
                    self.discovery_cycle)

    def _interruptible_sleep(self, seconds: int) -> None:
        """Sleep in small increments so stop_requested / signals are seen promptly."""
        end = time.time() + seconds
        while time.time() < end and not self.stop_requested:
            time.sleep(min(5, end - time.time()))

    def request_stop(self) -> None:
        self.stop_requested = True

    def status(self) -> Dict[str, Any]:
        return {
            "running": not self.stop_requested,
            "cycle": self.discovery_cycle,
            "verified_discoveries": len(self.genuine_discoveries),
            "evolution_enabled": not self._evolution_disabled,
            "user_active": is_user_active(self.user_active_window_seconds),
            "uptime_seconds": int(time.time() - self.start_time),
        }


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description="ASTRA fiction-free discovery supervisor")
    ap.add_argument("--cycle", type=int, default=300)
    ap.add_argument("--evolution-interval", type=int, default=1800)
    ap.add_argument("--evolution-timeout", type=int, default=1200)
    ap.add_argument("--once", action="store_true",
                    help="run a single cycle and exit (for testing)")
    args = ap.parse_args()

    # Force-configure the ROOT logger (basicConfig is a no-op if astra_core's
    # heavy __init__ already configured it — that left the dedicated log empty).
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    PERSIST_DIR.mkdir(parents=True, exist_ok=True)
    fh = logging.FileHandler(PERSIST_DIR / ".astra_supervisor.log")
    fh.setFormatter(fmt)
    root.addHandler(fh)
    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    root.addHandler(sh)

    sup = AutonomousDiscoverySupervisor(
        cycle_seconds=args.cycle,
        evolution_interval_seconds=args.evolution_interval,
        evolution_timeout_seconds=args.evolution_timeout)
    if args.once:
        ingested = sup._ingest()
        sup._maybe_evolve()
        print(f"single cycle done: ingested={ingested} store={len(sup.genuine_discoveries)}")
        return 0
    try:
        sup.run_forever()
    except KeyboardInterrupt:
        sup.request_stop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
