"""safety.py — static AST gate run on LLM-generated candidate code BEFORE exec().

This is the first layer of defence-in-depth for the ASTRA evolutionary discovery
loop. The eval worker takes an LLM-generated source string defining
``estimate_redshift(df_train, df_eval)`` and runs it on REAL SDSS data. Before
that string is ever compiled and executed, this module confirms that it only
uses a small allowlist of import roots and does not call (or attribute-reach
into) the Python builtins / stdlib modules that touch the OS, network, process
tree, or interpreter internals.

Combined with:
  * ``resource.setrlimit`` caps applied in ``eval_worker.py`` (CPU, file size,
    fork count), and
  * the macOS ``sandbox-exec`` profile (``astra_worker.sb``) that denies network
    and restricts writes,
this gate bounds what untrusted LLM code can do even when the proposer is
adversarial or buggy.

The checker is intentionally conservative: it parses with ``ast``, so it makes
no claim to defeat truly obfuscated source, but it does catch the obvious
escape hatches (``open``, ``eval``, ``os.system``, ``subprocess.run``,
``__import__``). The sandbox + rlimit layers backstop anything subtler.

Public API: ``check_source(src, entry_point="estimate_redshift") -> (ok, reason)``.
It NEVER raises: any internal failure returns ``(False, "check-failed: ...")`` so
the caller (the worker) can fail the candidate safely rather than crash.
"""
from __future__ import annotations

import ast

# Roots that may appear as the top-level module of an import. ``np``/``pd`` are
# included so that ``import numpy as np`` / ``import pandas as pd`` (whose root
# module name is what we check) are accepted; the *alias* is not separately
# restricted because a candidate can only USE an alias that was bound from an
# already-allowed root.
ALLOWED_IMPORT_ROOTS = {
    "numpy", "np",
    "pandas", "pd",
    "sklearn",
    "scipy",
    "math",
    "statistics",
    "numbers",
}

# Bare names that must never be CALLED. Catches ``open(...)`` (file I/O),
# ``eval/exec/compile`` (dynamic code), ``__import__`` (dynamic import), and the
# reflection builtins that can be used to escape a restricted namespace.
BLOCKED_CALL_NAMES = {
    "open", "exec", "eval", "compile", "__import__",
    "getattr", "setattr", "delattr",
    "globals", "locals", "vars",
    "input", "breakpoint", "exit", "quit",
}

# Roots whose attributes are off-limits. Catches ``os.system``,
# ``subprocess.run``, ``socket.socket``, ``__builtins__`` reaches, etc. We look
# at the base ``Name`` of any attribute chain, so ``os.path.join`` (root ``os``)
# is caught just like ``os.system`` would be.
BLOCKED_ATTR_ROOTS = {
    "os", "sys", "subprocess", "shutil", "socket", "pty",
    "ctypes", "multiprocessing",
    "pickle", "marshal",
    "builtins", "__builtins__",
    "pathlib", "glob", "importlib",
}


def _attr_root_and_path(node: "ast.Attribute"):
    """Walk an Attribute chain down to its base Name.

    Returns ``(root_id, dotted_path)`` where ``root_id`` is the base ``Name.id``
    (or ``None`` if the chain is not rooted on a bare name — e.g. a subscript or
    call result) and ``dotted_path`` is the reconstructed full path like
    ``os.path.join`` (or ``None``).
    """
    parts = []
    cur = node
    while isinstance(cur, ast.Attribute):
        parts.append(cur.attr)
        cur = cur.value
    if isinstance(cur, ast.Name):
        parts.append(cur.id)
        parts.reverse()
        return cur.id, ".".join(parts)
    return None, None


def check_source(src: str, entry_point: str = "estimate_redshift") -> tuple[bool, str]:
    """Statically vet a candidate program before it is exec()'d.

    Returns ``(True, "ok")`` if the source is acceptable, else
    ``(False, "<reason>")`` where reason is one of:
      * ``syntax-error: ...``       — source does not parse
      * ``missing entry point``     — no ``def <entry_point>``
      * ``blocked-import: <name>``  — imports a disallowed module root
      * ``blocked-attr: <path>``    — attribute access rooted on a blocked name
      * ``blocked-call: <name>``    — bare call to a blocked builtin
      * ``check-failed: ...``       — unexpected internal error (defensive)
    """
    try:
        # 1. Parse. A SyntaxError must fail the candidate, not crash the worker.
        try:
            tree = ast.parse(src)
        except SyntaxError as e:
            return (False, f"syntax-error: {e}")

        # 2. Require the contracted entry point. The downstream exec path also
        #    checks for a callable, but we short-circuit malformed candidates
        #    here before walking the tree.
        if f"def {entry_point}" not in src:
            return (False, "missing entry point")

        # 3. Walk the tree once and vet imports, attribute accesses, and calls.
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".")[0]
                    if root not in ALLOWED_IMPORT_ROOTS:
                        return (False, f"blocked-import: {alias.name}")

            elif isinstance(node, ast.ImportFrom):
                # Relative imports have module=None; candidates never legitimately
                # use these, and we cannot resolve their root — skip rather than
                # risk a false "ok".
                if node.module:
                    root = node.module.split(".")[0]
                    if root not in ALLOWED_IMPORT_ROOTS:
                        return (False, f"blocked-import: {node.module}")

            elif isinstance(node, ast.Attribute):
                root, path = _attr_root_and_path(node)
                if root is not None and root in BLOCKED_ATTR_ROOTS:
                    label = path or root
                    return (False, f"blocked-attr: {label}")

            elif isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name) and func.id in BLOCKED_CALL_NAMES:
                    return (False, f"blocked-call: {func.id}")

        return (True, "ok")
    except Exception as e:  # pragma: no cover — defensive; never crash caller
        return (False, f"check-failed: {type(e).__name__}: {e}")
