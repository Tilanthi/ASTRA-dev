"""
Generate a self-contained ASTRA Live dashboard with all API data embedded inline.
This makes the dashboard work at any URL without needing a live API connection.

Usage: python3 generate_dashboard.py
The dashboard auto-refreshes by attempting live API calls; falls back to embedded data.
"""
import json
import sys
import time
import requests

API_BASE = "http://localhost:8787"
OUTPUT_PATH = "/shared/public/astra-live/index.html"


def fetch_all_data():
    data = {}
    for ep in ['status', 'state', 'hypotheses', 'activity', 'decisions', 'charts', 'metrics', 'engine/safety-status', 'engine/state-space', 'engine/alignment', 'engine/anomalies', 'engine/pending', 'system/health']:
        try:
            r = requests.get(f"{API_BASE}/api/{ep}", timeout=5)
            data[ep] = r.json()
        except Exception as e:
            print(f"  Warning: /api/{ep} failed: {e}")
            data[ep] = None
    return data


def build_dashboard_html(snapshot_data):
    """Read the template HTML and inject snapshot data."""
    with open(OUTPUT_PATH, 'r') as f:
        html = f.read()

    # Build the snapshot injection script
    snapshot_json = json.dumps(snapshot_data, indent=2, default=str)
    snapshot_block = f"""
  // ── Embedded snapshot data (auto-generated, fallback when API unreachable) ──
  window.__SNAPSHOT__ = {snapshot_json};
  window.__SNAPSHOT_TIME__ = {time.time()};
"""

    # Remove any old snapshot blocks first
    import re
    html = re.sub(
        r'\n\s*// ── Embedded snapshot data.*?window\.__SNAPSHOT__\s*=\s*\{.*?\};\s*\n',
        '\n',
        html,
        flags=re.DOTALL
    )
    # Also remove older style snapshot blocks
    html = re.sub(
        r'\n\s*window\.__SNAPSHOT__\s*=\s*\{[^}]*"status".*?\n\s*\};\s*\n',
        '\n',
        html,
        flags=re.DOTALL
    )

    # Find the injection point — right before the api() function
    marker = "  async function api(path) {"
    if marker in html:
        html = html.replace(marker, snapshot_block + "\n" + marker)
    else:
        print("Warning: Could not find injection marker")
        return html

    # Now patch the api() function to use snapshot fallback
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

    html = html.replace(old_api, new_api)

    # Also fix the connection status to show "LIVE" when connected, "CACHED" when using snapshot
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

    html = html.replace(old_status, new_status)
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

    print("\n2. Reading template...")
    with open(OUTPUT_PATH, 'r') as f:
        html = f.read()
    print(f"   Template: {len(html)} bytes")

    print("\n3. Injecting snapshot data...")
    html = build_dashboard_html(data)
    print(f"   Result: {len(html)} bytes")

    print(f"\n4. Writing to {OUTPUT_PATH}...")
    with open(OUTPUT_PATH, 'w') as f:
        f.write(html)

    print("\n✅ Dashboard generated successfully!")
    print(f"   File: {OUTPUT_PATH}")
    print(f"   Size: {len(html)} bytes")
