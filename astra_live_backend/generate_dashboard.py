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
Generate a self-contained ASTRA Live dashboard with all API data embedded inline.
This makes the dashboard work at any URL without needing a live API connection.

Usage: python3 generate_dashboard.py
The dashboard auto-refreshes by attempting live API calls; falls back to embedded data.
"""
import json
import sys
import time
import requests
from pathlib import Path

API_BASE = "http://localhost:8787"
OUTPUT_PATH = "astra_core/dashboard/index.html"


def _ensure_output_dir():
    """Ensure output directory exists."""
    output_path = Path(OUTPUT_PATH)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    return output_path


def fetch_all_data():
    data = {}
    endpoints = [
        'status', 'state', 'hypotheses', 'activity', 'decisions', 'charts', 'metrics',
        'engine/safety-status', 'engine/state-space', 'engine/alignment', 'engine/anomalies', 'engine/pending',
        'system/health',
        'literature/papers', 'literature/citation-graph', 'literature/citation-metrics',
        # Stigmergy endpoints
        'pheromones/status', 'stigmergy/gaps', 'swarm/status', 'pheromones/ab-test', 'stigmergy/gordon',
        # Self-improve endpoints
        'discovery-memory', 'discovery-memory/discoveries',
        # Verified discoveries
        'verification/verified'
    ]
    for ep in endpoints:
        try:
            r = requests.get(f"{API_BASE}/api/{ep}", timeout=15)
            data[ep] = r.json()
        except Exception as e:
            print(f"  Warning: /api/{ep} failed: {e}")
            data[ep] = None
    return data


def build_dashboard_html(snapshot_data):
    """Read the template HTML and inject snapshot data."""
    # Ensure output directory exists
    _ensure_output_dir()

    # Try to read the template file
    template_path = Path(__file__).parent / "dashboard_template.html"
    if template_path.exists():
        with open(template_path, 'r') as f:
            html = f.read()
    else:
        # Return minimal HTML if template doesn't exist
        return _generate_minimal_dashboard()

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
    if (path.includes('/literature/papers')) return s["literature/papers"];
    if (path.includes('/literature/citation-graph')) return s["literature/citation-graph"];
    if (path.includes('/literature/citation-metrics')) return s["literature/citation-metrics"];
    // Stigmergy endpoints
    if (path.includes('/pheromones/status')) return s["pheromones/status"];
    if (path.includes('/stigmergy/gaps')) return s["stigmergy/gaps"];
    if (path.includes('/swarm/status')) return s["swarm/status"];
    if (path.includes('/pheromones/ab-test')) return s["pheromones/ab-test"];
    if (path.includes('/stigmergy/gordon')) return s["stigmergy/gordon"];
    // Self-improve endpoints
    if (path.includes('/discovery-memory') && path.includes('/discoveries')) return s["discovery-memory/discoveries"];
    if (path.includes('/discovery-memory')) return s["discovery-memory"];
    // Verified discoveries
    if (path.includes('/verification/verified')) return s["verification/verified"];
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

    # Update hardcoded discovery and outcome counts with live data
    import re

    # Get discovery count (total, not unique)
    discovery_count = (snapshot_data.get('discovery-memory') or {}).get('discovery_count', 0)
    if discovery_count == 0:
        discovery_count = (snapshot_data.get('discovery-memory') or {}).get('improvement', {}).get('total_discoveries', 0)

    # Get method outcomes count
    outcomes_count = (snapshot_data.get('discovery-memory') or {}).get('improvement', {}).get('total_outcomes', 0)

    if discovery_count > 0:
        # Update the key metric value (si-km-discoveries)
        html = re.sub(
            r'id="si-km-discoveries">[0-9]+</div>',
            f'id="si-km-discoveries">{discovery_count}</div>',
            html
        )
        # Also update the summary section (si-discoveries-count)
        html = re.sub(
            r'id="si-discoveries-count">.*?</div>',
            f'id="si-discoveries-count">{discovery_count}</div>',
            html
        )

    if outcomes_count > 0:
        # Update the method outcomes count
        html = re.sub(
            r'id="si-km-outcomes">[0-9]+</div>',
            f'id="si-km-outcomes">{outcomes_count}</div>',
            html
        )

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
    # Ensure output directory exists first
    _ensure_output_dir()

    # Check if template exists
    template_path = Path(__file__).parent / "dashboard_template.html"
    if template_path.exists():
        with open(template_path, 'r') as f:
            html = f.read()
        print(f"   Template: {len(html)} bytes")
    else:
        print("   Template not found, using minimal dashboard...")
        html = """<!DOCTYPE html>
<html>
<head>
    <title>ASTRA Live</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
        .status { background: #f0f8ff; padding: 20px; border-radius: 5px; margin: 20px 0; border: 1px solid #cce5ff; }
        .cognitive { background: #f0fff0; padding: 20px; border-radius: 5px; margin: 20px 0; border: 1px solid #c3e6cb; }
        .endpoints { background: #fff8f0; padding: 20px; border-radius: 5px; margin: 20px 0; border: 1px solid #ffe6cc; }
        h1 { color: #333; }
        h2 { color: #444; margin-top: 30px; }
        a { color: #0066cc; }
        .endpoint { margin: 10px 0; }
        .endpoint::before { content: "🔹 "; }
    </style>
</head>
<body>
    <h1>🧠 ASTRA Live — Autonomous Scientific Discovery</h1>
    <p>With Cognitive Architecture (Phase 15: Scientific AGI)</p>

    <div class="status">
        <h2>System Status</h2>
        <p><strong>Server:</strong> Running at <a href="http://localhost:8787">http://localhost:8787</a></p>
        <p><strong>API Status:</strong> <a href="/api/status">/api/status</a></p>
        <p><strong>API Docs:</strong> <a href="/docs">/docs</a></p>
    </div>

    <div class="cognitive">
        <h2>🧠 Cognitive Architecture (New!)</h2>
        <div class="endpoint"><a href="/api/cognitive/status">/api/cognitive/status</a> - Cognitive architecture overview</div>
        <div class="endpoint"><a href="/api/cognitive/dashboard">/api/cognitive/dashboard</a> - Unified cognitive dashboard</div>
        <div class="endpoint"><a href="/api/knowledge-graph/statistics">/api/knowledge-graph/statistics</a> - Knowledge graph stats</div>
        <div class="endpoint"><a href="/api/knowledge-graph/gaps">/api/knowledge-graph/gaps</a> - Knowledge gaps</div>
        <div class="endpoint"><a href="/api/knowledge-graph/analogies">/api/knowledge-graph/analogies</a> - Cross-domain analogies</div>
        <div class="endpoint"><a href="/api/metacognition/report">/api/metacognition/report</a> - Self-awareness report</div>
        <div class="endpoint"><a href="/api/cognitive/discoveries">/api/cognitive/discoveries</a> - Cognitive discoveries</div>
        <div class="endpoint"><a href="/api/state/persistence">/api/state/persistence</a> - State persistence status</div>
    </div>

    <div class="endpoints">
        <h2>Key API Endpoints</h2>
        <div class="endpoint"><a href="/api/hypotheses">/api/hypotheses</a> - All hypotheses</div>
        <div class="endpoint"><a href="/api/activity">/api/activity</a> - Activity log</div>
        <div class="endpoint"><a href="/api/decisions">/api/decisions</a> - Decision log</div>
        <div class="endpoint"><a href="/api/engine/state-space">/api/engine/state-space</a> - State space</div>
        <div class="endpoint"><a href="/api/discovery-memory">/api/discovery-memory</a> - Discovery memory</div>
    </div>

    <p><em>ASTRA is running with Scientific AGI capabilities enabled.</em></p>
    <p><small>Refresh this page for updated data.</small></p>
</body>
</html>"""
        print(f"   Using minimal dashboard: {len(html)} bytes")

    print("\n3. Injecting snapshot data...")
    html = build_dashboard_html(data)
    print(f"   Result: {len(html)} bytes")

    print(f"\n4. Writing to {OUTPUT_PATH}...")
    with open(str(_ensure_output_dir()), 'w') as f:
        f.write(html)

    print("\n✅ Dashboard generated successfully!")
    print(f"   File: {OUTPUT_PATH}")
    print(f"   Size: {len(html)} bytes")

def _generate_minimal_dashboard():
    """Generate minimal dashboard when template is not available."""
    return """<!DOCTYPE html>
<html>
<head>
    <title>ASTRA Live</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { border-bottom: 2px solid #0066cc; padding-bottom: 20px; margin-bottom: 30px; }
        .status { background: #f0f8ff; padding: 20px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #0066cc; }
        .cognitive { background: #f0fff0; padding: 20px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #28a745; }
        .endpoints { background: #fff8f0; padding: 20px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #ffc107; }
        h1 { color: #333; margin: 0; }
        h2 { color: #444; margin-top: 30px; border-bottom: 1px solid #ddd; padding-bottom: 10px; }
        a { color: #0066cc; text-decoration: none; }
        a:hover { text-decoration: underline; }
        .endpoint { margin: 10px 0; }
        .endpoint::before { content: "🔹 "; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        @media (max-width: 768px) { .grid { grid-template-columns: 1fr; } }
    </style>
    <script>
        async function refreshData() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                document.getElementById('cycle-count').textContent = data.engine.cycle_count;
                document.getElementById('confidence').textContent = (data.engine.system_confidence * 100).toFixed(1) + '%';
            } catch (e) {
                console.log('Could not refresh data');
            }
        }
        setInterval(refreshData, 5000);
    </script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧠 ASTRA Live — Autonomous Scientific Discovery</h1>
            <p>With Cognitive Architecture (Phase 15: Scientific AGI)</p>
        </div>

        <div class="status">
            <h2>⚡ System Status</h2>
            <p><strong>Cycle:</strong> <span id="cycle-count">Loading...</span></p>
            <p><strong>Confidence:</strong> <span id="confidence">Loading...</span></p>
            <p><strong>Server:</strong> Running at <a href="http://localhost:8787">http://localhost:8787</a></p>
            <p><strong>API:</strong> <a href="/api/status">/api/status</a></p>
            <p><strong>Docs:</strong> <a href="/docs">/docs</a></p>
        </div>

        <div class="cognitive">
            <h2>🧠 Cognitive Architecture (New!)</h2>
            <div class="grid">
                <div>
                    <h3>Core Systems</h3>
                    <div class="endpoint"><a href="/api/cognitive/status">/api/cognitive/status</a> - Overview</div>
                    <div class="endpoint"><a href="/api/cognitive/dashboard">/api/cognitive/dashboard</a> - Dashboard</div>
                    <div class="endpoint"><a href="/api/knowledge-graph/statistics">/api/knowledge-graph/statistics</a> - Stats</div>
                    <div class="endpoint"><a href="/api/metacognition/report">/api/metacognition/report</a> - Self-awareness</div>
                </div>
                <div>
                    <h3>Knowledge Graph</h3>
                    <div class="endpoint"><a href="/api/knowledge-graph/gaps">/api/knowledge-graph/gaps</a> - Gaps</div>
                    <div class="endpoint"><a href="/api/knowledge-graph/analogies">/api/knowledge-graph/analogies</a> - Analogies</div>
                </div>
            </div>
        </div>

        <div class="endpoints">
            <h2>🔬 Key API Endpoints</h2>
            <div class="grid">
                <div>
                    <h3>Core</h3>
                    <div class="endpoint"><a href="/api/hypotheses">/api/hypotheses</a></div>
                    <div class="endpoint"><a href="/api/activity">/api/activity</a></div>
                    <div class="endpoint"><a href="/api/decisions">/api/decisions</a></div>
                </div>
                <div>
                    <h3>Discovery</h3>
                    <div class="endpoint"><a href="/api/discovery-memory">/api/discovery-memory</a></div>
                    <div class="endpoint"><a href="/api/engine/state-space">/api/engine/state-space</a></div>
                </div>
            </div>
        </div>

        <p style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #666;">
            <small>ASTRA is running with Scientific AGI capabilities enabled. Refresh for updates.</small>
        </p>
    </div>
</body>
</html>"""
