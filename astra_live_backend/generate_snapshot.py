# Copyright 2024-2026 Glenn J. White (The Open University / RAL Space)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Generate a self-contained dashboard HTML snapshot with embedded API data.
Run this periodically to update the deployed dashboard.
"""
import json
import sys
import time
import requests

API_BASE = "http://localhost:8787"
DASHBOARD_PATH = "astra_core/dashboard/index.html"
SNAPSHOT_PATH = "astra_core/dashboard/index.html"


def fetch_all_data():
    """Fetch all API data."""
    data = {}
    endpoints = ['status', 'state', 'hypotheses', 'activity', 'decisions', 'charts', 'metrics', 'engine/safety-status', 'engine/state-space', 'engine/alignment', 'engine/anomalies', 'engine/pending', 'system/health']
    for ep in endpoints:
        try:
            r = requests.get(f"{API_BASE}/api/{ep}", timeout=3)
            data[ep] = r.json()
        except Exception as e:
            print(f"Warning: Failed to fetch /api/{ep}: {e}")
            data[ep] = None
    return data


def inject_snapshot_data(html: str, data: dict) -> str:
    """Inject API data as a JS constant into the HTML."""
    snapshot_js = f"""
  /* ═══ EMBEDDED SNAPSHOT DATA (auto-generated) ═══ */
  const SNAPSHOT_DATA = {json.dumps(data, indent=2, default=str)};
  const SNAPSHOT_TIME = {time.time()};
  /* ═══ END SNAPSHOT DATA ═══ */
"""
    # Insert right after the API auto-detect block
    marker = "  /* ── API Helper with auto-detect and reconnect ──────────── */"
    if marker in html:
        html = html.replace(marker, snapshot_js + "\n" + marker)
    else:
        # Fallback: insert after the const API line
        html = html.replace("  const API_CANDIDATES", snapshot_js + "\n  const API_CANDIDATES")
    return html


def patch_api_helper(html: str) -> str:
    """Patch the api() helper to use snapshot data as fallback."""
    old_api_func = """  async function api(path) {
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

    new_api_func = """  async function api(path) {
    // Try live API first
    if (!apiConnected) {
      const ok = await detectApi();
      if (!ok) return apiFromSnapshot(path);
    }
    try {
      const r = await fetch(API + path);
      if (!r.ok) throw new Error(r.status);
      return await r.json();
    } catch (e) {
      apiConnected = false;
      return apiFromSnapshot(path);
    }
  }

  function apiFromSnapshot(path) {
    if (!window.SNAPSHOT_DATA) return null;
    const d = window.SNAPSHOT_DATA;
    if (path.includes('/api/status')) return d.status;
    if (path.includes('/api/state')) return d.state;
    if (path.includes('/api/hypotheses')) return d.hypotheses;
    if (path.includes('/api/activity')) return d.activity;
    if (path.includes('/api/decisions')) return d.decisions;
    if (path.includes('/api/charts')) return d.charts;
    if (path.includes('/api/metrics')) return d.metrics;
    if (path.includes('/api/engine/state-space')) return d["engine/state-space"];
    return null;
  }"""

    return html.replace(old_api_func, new_api_func)


if __name__ == "__main__":
    print("Fetching live API data...")
    data = fetch_all_data()

    print("Reading dashboard HTML...")
    with open(DASHBOARD_PATH, 'r') as f:
        html = f.read()

    print("Injecting snapshot data...")
    html = inject_snapshot_data(html, data)

    print("Patching API helper...")
    html = patch_api_helper(html)

    print(f"Writing to {SNAPSHOT_PATH}...")
    with open(SNAPSHOT_PATH, 'w') as f:
        f.write(html)

    print(f"Done! Dashboard size: {len(html)} bytes")
    print(f"Snapshot contains: {list(data.keys())}")
    if data.get('hypotheses'):
        print(f"  {len(data['hypotheses'])} hypotheses")
    if data.get('activity'):
        print(f"  {len(data['activity'])} activity entries")
