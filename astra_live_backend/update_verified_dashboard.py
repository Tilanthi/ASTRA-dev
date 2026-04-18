#!/usr/bin/env python3

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
Update the ASTRA Live dashboard with latest verified discoveries.

Fetches verified discoveries from the database and updates the
"Verified Discoveries" section in the dashboard HTML.

Usage: python3 update_verified_dashboard.py

The dashboard will auto-refresh when live, but this script forces an update.
"""
import sqlite3
import json
import time
from pathlib import Path

# Database path
DB_PATH = "astra_discoveries.db"
HTML_PATH = "astra_core/dashboard/index.html"


def get_verified_discoveries():
    """Get all verified discoveries from database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT
            id,
            hypothesis_id,
            domain,
            finding_type,
            variables,
            description,
            data_source,
            strength,
            effect_size,
            timestamp
        FROM discoveries
        WHERE verified = 1
        ORDER BY strength DESC, effect_size DESC
        LIMIT 10
    ''')

    discoveries = []
    for row in cursor.fetchall():
        discoveries.append({
            'id': row[0],
            'hypothesis_id': row[1],
            'domain': row[2],
            'finding_type': row[3],
            'variables': json.loads(row[4]),
            'description': row[5],
            'data_source': row[6],
            'strength': row[7],
            'effect_size': row[8],
            'timestamp': row[9],
        })

    conn.close()
    return discoveries


def generate_discovery_html(discovery):
    """Generate HTML for a single verified discovery."""
    domain_colors = {
        'Astrophysics': 'cyan',
        'Cosmology': 'amber',
        'Physics': 'violet',
    }

    color = domain_colors.get(discovery['domain'], 'emerald')

    # Format variables
    vars_str = ', '.join(discovery['variables'])

    # Truncate description if needed
    desc = discovery['description']
    if len(desc) > 100:
        desc = desc[:97] + '...'

    # Format date
    date_str = time.strftime('%Y-%m-%d', time.gmtime(discovery['timestamp']))

    # Format effect size
    effect_str = f"{discovery.get('effect_size', 'N/A'):.3f}" if discovery.get('effect_size') else 'N/A'

    return f'''    <div class="panel si-discovery-full-{color}">
      <div class="panel-header">
        <span class="panel-icon">🔬</span>
        <span class="panel-title">{discovery['hypothesis_id'].upper()} — VERIFIED</span>
      </div>
      <div class="discovery-body">
        <div class="discovery-detail-box discovery-box-{color}">
          {desc}
        </div>
        <div class="discovery-desc">
          Variables: <strong>{vars_str}</strong><br>
          Source: {discovery['data_source']}<br>
          Strength: {discovery['strength']:.3f} | Effect: {effect_str}
        </div>
        <div class="discovery-meta">
          <span>📡 {discovery['data_source']}</span>
          <span>🔢 Verified: {date_str}</span>
          <span>📊 Strength: {discovery['strength']:.3f}</span>
          <span class="discovery-stat-badge badge-verified">VERIFIED</span>
        </div>
      </div>
    </div>'''


def update_dashboard():
    """Update the dashboard HTML with verified discoveries."""
    # Get verified discoveries
    discoveries = get_verified_discoveries()

    if not discoveries:
        print("No verified discoveries found to add to dashboard.")
        return

    print(f"Found {len(discoveries)} verified discoveries to add to dashboard")

    # Read current dashboard HTML
    html_path = Path(HTML_PATH)
    if not html_path.exists():
        print(f"Dashboard HTML not found at {HTML_PATH}")
        return

    with open(html_path, 'r') as f:
        html = f.read()

    # Check if there's already a discoveries section
    if '<div class="discoveries-grid">' not in html:
        print("Dashboard doesn't have a discoveries-grid section. Cannot update.")
        return

    # Remove existing discoveries
    import re
    html = re.sub(
        r'<div class="discoveries-grid">.*?</div>\s*(?=<div class="hyp-pipeline">|$)',
        '<div class="discoveries-grid">\n    <p style="color:var(--text-tertiary);font-size:0.8rem;">Loading verified discoveries…</p>\n  </div>\n\n',
        html,
        flags=re.DOTALL
    )

    # Generate HTML for discoveries
    discoveries_html = '\n'.join([generate_discovery_html(d) for d in discoveries])

    # Insert discoveries before the hypothesis pipeline
    marker = '<div class="hyp-pipeline"'
    if marker not in html:
        print("Warning: Could not find insertion point in dashboard HTML")
        return

    # Find the discoveries-grid section end marker (or create it)
    discoveries_section = f'''    <div class="discoveries-grid">

{discoveries_html}
'''
    html = html.replace(marker, discoveries_section)

    # Write updated HTML
    with open(html_path, 'w') as f:
        f.write(html)

    print(f"✓ Updated {HTML_PATH} with {len(discoveries)} verified discoveries")
    print(f"  - Template regenerated: {time.strftime('%Y-%m-%d %H:%M:%S')}")


def main():
    """Main entry point."""
    print("ASTRA Live Dashboard - Verified Discoveries Update")
    print("=" * 60)
    print()

    update_dashboard()

    print()
    print("Next steps:")
    print("1. View the dashboard: file://" + str(Path(HTML_PATH.resolve())))
    print("2. Or start/restart the ASTRA server to see the updated dashboard")
    print("3. New discoveries will be added automatically on future cycles")


if __name__ == '__main__':
    main()
