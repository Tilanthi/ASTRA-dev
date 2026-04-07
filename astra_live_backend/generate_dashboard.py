"""
Generate a self-contained ASTRA Live dashboard with all API data embedded inline.
This makes the dashboard work at any URL without needing a live API connection.

Uses marker-based injection: everything between /* SNAPSHOT_START */ and /* SNAPSHOT_END */
is replaced on each refresh, making the process fully idempotent.

Usage: python3 generate_dashboard.py
"""
import json
import re
import sys
import time
import requests

API_BASE = "http://localhost:8787"
OUTPUT_PATH = "/shared/public/astra-live/index.html"

SNAPSHOT_START = "/* __SNAPSHOT_DATA_START__ */"
SNAPSHOT_END = "/* __SNAPSHOT_DATA_END__ */"

ENDPOINTS = [
    'status', 'state', 'hypotheses', 'activity', 'decisions', 'charts',
    'metrics', 'engine/safety-status', 'engine/state-space', 'engine/alignment',
    'engine/anomalies', 'engine/pending', 'system/health',
    'literature/papers', 'literature/citation-graph', 'literature/citation-metrics',
    'pheromones/status', 'pheromones/ab-test',
    'stigmergy/gaps', 'stigmergy/exploration', 'swarm/status',
    'persistence',
    'ecdlp/status', 'ecdlp/parameters', 'ecdlp/approaches',
    'cognitive/status', 'cognitive/dashboard',
    'knowledge-graph/statistics', 'knowledge-graph/gaps', 'knowledge-graph/analogies',
    'agents/status', 'metacognition/report',
    'agenda/status', 'agenda/goals', 'state/persistence',
]


def fetch_all_data():
    data = {}
    for ep in ENDPOINTS:
        try:
            r = requests.get(f"{API_BASE}/api/{ep}", timeout=15)
            data[ep] = r.json()
        except Exception as e:
            print(f"  Warning: /api/{ep} failed: {e}")
            data[ep] = None
    return data


def inject_snapshot(html: str, snapshot_data: dict) -> str:
    """Replace the snapshot block between markers. Fully idempotent."""
    snapshot_json = json.dumps(snapshot_data, indent=2, default=str)
    new_block = (
        f"{SNAPSHOT_START}\n"
        f"  window.__SNAPSHOT__ = {snapshot_json};\n"
        f"  window.__SNAPSHOT_TIME__ = {time.time()};\n"
        f"  {SNAPSHOT_END}"
    )

    if SNAPSHOT_START in html and SNAPSHOT_END in html:
        # Replace between markers (idempotent)
        pattern = re.escape(SNAPSHOT_START) + r'.*?' + re.escape(SNAPSHOT_END)
        # Use lambda to avoid \u in JSON being treated as regex backreference
        html = re.sub(pattern, lambda m: new_block, html, count=1, flags=re.DOTALL)
    else:
        # First-time injection: insert markers before the api() function
        marker = "  async function api(path) {"
        alt_marker = "  function snapshotFor(path) {"
        target = marker if marker in html else alt_marker
        if target in html:
            html = html.replace(target, new_block + "\n\n  " + target.lstrip(), 1)
        else:
            print("Warning: Could not find injection point for snapshot")

    return html


def ensure_snapshot_api(html: str) -> str:
    """Ensure the api() function has snapshot fallback. One-time transformation."""
    # Already has snapshotFor? Nothing to do
    if "function snapshotFor(path)" in html:
        return html

    old_api = """  async function api(path) {
    // Try live API first
    if (!apiConnected) {
      const ok = await detectApi();
      if (!ok) return null;
    }
    try {
      const r = await fetch(API + path);
      if (!r.ok) throw new Error(r.status);
      return await r.json();
    } catch (e) {
      console.warn('API error:', path, e);
      // Mark as disconnected so next call re-detects
      apiConnected = false;
      return null;
    }
  }"""

    new_api = """  function snapshotFor(path) {
    const s = window.__SNAPSHOT__;
    if (!s) return null;
    if (path.includes('/status')) return s.status;
    if (path.includes('/state')) return s.state;
    if (path.includes('/hypotheses')) return s.hypotheses;
    if (path.includes('/activity')) return s.activity;
    if (path.includes('/decisions')) return s.decisions;
    if (path.includes('/charts')) return s.charts;
    if (path.includes('/metrics')) return s.metrics;
    if (path.includes('/engine/state-space')) return s["engine/state-space"];
    if (path.includes('/engine/safety-status')) return s["engine/safety-status"];
    if (path.includes('/engine/anomalies')) return s["engine/anomalies"];
    if (path.includes('/engine/alignment')) return s["engine/alignment"];
    if (path.includes('/engine/pending')) return s["engine/pending"];
    if (path.includes('/system/health')) return s["system/health"];
    if (path.includes('/literature/papers')) return s["literature/papers"];
    if (path.includes('/literature/citation-graph')) return s["literature/citation-graph"];
    if (path.includes('/literature/citation-metrics')) return s["literature/citation-metrics"];
    if (path.includes('/pheromones/status')) return s["pheromones/status"];
    if (path.includes('/pheromones/ab-test')) return s["pheromones/ab-test"];
    if (path.includes('/stigmergy/gaps')) return s["stigmergy/gaps"];
    if (path.includes('/stigmergy/exploration')) return s["stigmergy/exploration"];
    if (path.includes('/swarm/status')) return s["swarm/status"];
    return null;
  }

  async function api(path) {
    // Try live API
    if (!apiConnected) {
      const ok = await detectApi();
      if (!ok) return snapshotFor(path);
    }
    try {
      const r = await fetch(API + path);
      if (!r.ok) throw new Error(r.status);
      return await r.json();
    } catch (e) {
      apiConnected = false;
      return snapshotFor(path);
    }
  }"""

    if old_api in html:
        html = html.replace(old_api, new_api)

    # Connection status: show CACHED when using snapshot
    old_status = """  function updateConnectionStatus(connected) {
    const dot = document.querySelector('.status-dot');
    const headerCenter = document.querySelector('.header-center');
    if (dot && headerCenter) {
      dot.style.background = connected ? 'var(--emerald)' : 'var(--coral)';
      headerCenter.querySelector('span:last-child').textContent = connected
        ? 'AUTONOMOUS MODE\\u00a0\\u00a0●\\u00a0\\u00a0ACTIVE'
        : 'RECONNECTING\\u00a0\\u00a0●\\u00a0\\u00a0STANDBY';
    }
  }"""

    new_status = """  function updateConnectionStatus(connected) {
    const dot = document.querySelector('.status-dot');
    const headerCenter = document.querySelector('.header-center');
    if (dot && headerCenter) {
      if (connected) {
        dot.style.background = 'var(--emerald)';
        headerCenter.querySelector('span:last-child').textContent = 'LIVE\\u00a0\\u00a0●\\u00a0\\u00a0CONNECTED';
      } else {
        dot.style.background = 'var(--amber)';
        headerCenter.querySelector('span:last-child').textContent = 'CACHED\\u00a0\\u00a0●\\u00a0\\u00a0STANDBY';
      }
    }
  }"""

    if old_status in html:
        html = html.replace(old_status, new_status)

    return html


TEMPLATE_PATH = "/shared/ASTRA/shared/public/astra-live/index.html"


def build_dashboard_html(snapshot_data: dict) -> str:
    """Read the HTML, inject snapshot data, ensure API fallback. Idempotent."""
    import os, shutil
    # Safety: if output is missing, empty, or corrupted, restore from template
    if not os.path.exists(OUTPUT_PATH) or os.path.getsize(OUTPUT_PATH) < 10000:
        if os.path.exists(TEMPLATE_PATH) and os.path.getsize(TEMPLATE_PATH) > 10000:
            os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
            shutil.copy2(TEMPLATE_PATH, OUTPUT_PATH)
            print(f"  Restored dashboard from template ({os.path.getsize(TEMPLATE_PATH)} bytes)")
        else:
            print(f"  ERROR: Dashboard template missing at {TEMPLATE_PATH}")
            return ""
    with open(OUTPUT_PATH, 'r') as f:
        html = f.read()

    # Clean up legacy cruft: remove any stray __SNAPSHOT_TIME__ lines not inside markers
    # (from the old broken generator that kept appending)
    html = re.sub(
        r'^\s*window\.__SNAPSHOT_TIME__\s*=\s*[\d.]+;\s*$\n',
        '', html, flags=re.MULTILINE
    )
    # Remove old-style snapshot blocks (no markers)
    html = re.sub(
        r'\n\s*// ── Embedded snapshot data[^\n]*\n'
        r'(?:\s*window\.__SNAPSHOT__\s*=\s*\{.*?\};\s*\n)?',
        '\n', html, flags=re.DOTALL
    )
    # Remove any orphaned window.__SNAPSHOT__ = { ... }; blocks not inside markers
    if SNAPSHOT_START not in html:
        # Only clean if we haven't placed markers yet
        html = re.sub(
            r'\n\s*window\.__SNAPSHOT__\s*=\s*\{[^;]{100,}\};\s*\n',
            '\n', html, flags=re.DOTALL
        )

    # Ensure API fallback (one-time)
    html = ensure_snapshot_api(html)

    # Inject snapshot data (idempotent with markers)
    html = inject_snapshot(html, snapshot_data)

    return html


if __name__ == "__main__":
    print("╔══════════════════════════════════════════════╗")
    print("║   ASTRA Live Dashboard Generator             ║")
    print("╚══════════════════════════════════════════════╝")

    print("\n1. Fetching live API data...")
    data = fetch_all_data()

    hyps = data.get('hypotheses') or []
    activity = data.get('activity') or []
    metrics = data.get('metrics') or {}
    print(f"   {len(hyps)} hypotheses, {len(activity)} activity entries")
    if metrics:
        print(f"   {metrics.get('data_points', 0)} data points, "
              f"{metrics.get('auto_decisions', 0)} decisions, "
              f"confidence {metrics.get('system_confidence', 0):.3f}")

    print("\n2. Reading template & cleaning up...")
    html = build_dashboard_html(data)
    print(f"   Result: {len(html)} bytes")

    print(f"\n3. Writing to {OUTPUT_PATH}...")
    with open(OUTPUT_PATH, 'w') as f:
        f.write(html)

    print("\n✅ Dashboard generated successfully!")
    print(f"   File: {OUTPUT_PATH}")
    print(f"   Size: {len(html)} bytes")
