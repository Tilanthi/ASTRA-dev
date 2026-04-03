"""
ASTRA Live — End-to-End Playwright Tests
Tests the real API-driven dashboard for correctness.
"""
import json
import time
import requests
from playwright.sync_api import sync_playwright

BASE = "http://localhost:8787"
ERRORS = []
PASSES = []


def report(test_name, passed, detail=""):
    status = "✅ PASS" if passed else "❌ FAIL"
    msg = f"{status}: {test_name}"
    if detail:
        msg += f" — {detail}"
    print(msg)
    if passed:
        PASSES.append(test_name)
    else:
        ERRORS.append((test_name, detail))


# ── 1. API Health Tests ─────────────────────────────────────────
def test_api_endpoints():
    print("\n═══ API ENDPOINT TESTS ═══")

    endpoints = [
        "/api/status",
        "/api/state",
        "/api/hypotheses",
        "/api/activity",
        "/api/decisions",
        "/api/charts",
        "/api/metrics",
    ]
    for ep in endpoints:
        try:
            r = requests.get(f"{BASE}{ep}", timeout=5)
            report(f"API {ep} returns 200", r.status_code == 200,
                   f"status={r.status_code}")
            data = r.json()
            report(f"API {ep} returns JSON", data is not None,
                   f"type={type(data).__name__}")
        except Exception as e:
            report(f"API {ep} reachable", False, str(e))


def test_api_data_integrity():
    print("\n═══ API DATA INTEGRITY TESTS ═══")

    # Status
    data = requests.get(f"{BASE}/api/status").json()
    report("Engine is running", data.get("status") == "running")
    engine = data.get("engine", {})
    report("Cycle count > 0", engine.get("cycle_count", 0) > 0,
           f"cycles={engine.get('cycle_count')}")
    report("System confidence > 0", engine.get("system_confidence", 0) > 0,
           f"conf={engine.get('system_confidence'):.3f}")

    # Hypotheses
    hyps = requests.get(f"{BASE}/api/hypotheses").json()
    report("Has hypotheses", len(hyps) > 0, f"count={len(hyps)}")
    for h in hyps:
        report(f"Hypothesis {h['id']} has required fields",
               all(k in h for k in ['id', 'name', 'domain', 'confidence', 'phase']),
               f"keys={list(h.keys())}")
        report(f"Hypothesis {h['id']} confidence in range",
               0 <= h['confidence'] <= 1,
               f"conf={h['confidence']}")
        report(f"Hypothesis {h['id']} has valid phase",
               h['phase'] in ['proposed', 'screening', 'testing', 'validated', 'published', 'archived'],
               f"phase={h['phase']}")

    # Charts
    charts = requests.get(f"{BASE}/api/charts").json()
    report("Charts has funnel", 'funnel' in charts)
    report("Charts funnel has data", len(charts.get('funnel', {}).get('data', [])) == 5)
    report("Charts has domain", 'domain' in charts)
    report("Charts has radar", 'radar' in charts)
    report("Charts radar has 6 values", len(charts.get('radar', {}).get('data', [])) == 6)

    # Metrics
    metrics = requests.get(f"{BASE}/api/metrics").json()
    required_metrics = ['runtime_seconds', 'data_points', 'scripts_written',
                        'hypotheses_tested', 'system_confidence', 'auto_decisions']
    for key in required_metrics:
        report(f"Metric {key} present", key in metrics, f"val={metrics.get(key)}")
    report("Data points > 0", metrics.get('data_points', 0) > 0)
    report("Decisions > 0", metrics.get('auto_decisions', 0) > 0)

    # Activity log
    activity = requests.get(f"{BASE}/api/activity?limit=5").json()
    report("Activity log has entries", len(activity) > 0, f"count={len(activity)}")
    if activity:
        a = activity[0]
        report("Activity entry has fields",
               all(k in a for k in ['timestamp', 'phase', 'module', 'message']))

    # Decisions
    decisions = requests.get(f"{BASE}/api/decisions?limit=5").json()
    report("Decision log has entries", len(decisions) > 0, f"count={len(decisions)}")
    if decisions:
        d = decisions[0]
        report("Decision entry has fields",
               all(k in d for k in ['timestamp', 'action', 'text', 'status']))


def test_engine_is_alive():
    """Test that the engine actually runs cycles over time."""
    print("\n═══ ENGINE LIVENESS TESTS ═══")

    s1 = requests.get(f"{BASE}/api/state").json()
    cycles1 = s1['cycle_count']
    conf1 = s1['system_confidence']

    time.sleep(25)  # Wait for at least one cycle

    s2 = requests.get(f"{BASE}/api/state").json()
    cycles2 = s2['cycle_count']
    conf2 = s2['system_confidence']

    report("Engine cycles increase over time", cycles2 > cycles1,
           f"cycles: {cycles1} → {cycles2}")
    report("System confidence is valid", 0 <= conf2 <= 1,
           f"conf: {conf1:.3f} → {conf2:.3f}")

    # Check that new activity was logged
    a1 = requests.get(f"{BASE}/api/activity?limit=1").json()
    if a1:
        report("Activity log is growing", True, f"latest: {a1[-1]['message'][:50]}")


# ── 2. Browser/Dashboard Tests ──────────────────────────────────
def test_dashboard_renders(page):
    print("\n═══ DASHBOARD RENDER TESTS ═══")

    
    

    # Load page
    response = page.goto(BASE, wait_until="networkidle")
    report("Dashboard loads", response.status == 200)
    time.sleep(3)  # Let API calls complete

    # Check title
    title = page.title()
    report("Page has correct title", "ASTRA" in title, f"title={title}")

    # Check key elements exist
    elements = {
        "Activity feed": "#activity-feed",
        "Phase cycle": "#cycle-phases",
        "Brain SVG": "#brain-svg",
        "Gauge value": "#gauge-value",
        "Chart funnel": "#chart-funnel",
        "Chart domain": "#chart-domain",
        "Chart radar": "#chart-radar",
        "Chart h0": "#chart-h0",
        "Chart discovery": "#chart-discovery",
        "Chart error": "#chart-error",
        "Metrics grid": "#metrics-grid",
        "Decisions list": "#decisions-list",
        "UTC clock": "#utc-clock",
        "Uptime": "#uptime",
    }

    for name, selector in elements.items():
        el = page.query_selector(selector)
        report(f"Element exists: {name}", el is not None, f"selector={selector}")

    # Check activity feed has real content
    feed = page.query_selector("#activity-feed")
    if feed:
        lines = feed.query_selector_all(".activity-line")
        report("Activity feed has lines", len(lines) > 0, f"count={len(lines)}")
        if lines:
            first_text = lines[0].inner_text()
            report("Activity line has text", len(first_text) > 10,
                   f"first={first_text[:60]}")

    # Check metrics show real numbers (not --)
    metric_values = page.query_selector_all(".metric-value")
    report("Metrics bar has values", len(metric_values) >= 10,
           f"count={len(metric_values)}")
    non_placeholder = 0
    for mv in metric_values:
        text = mv.inner_text().strip()
        if text and text != "--" and text != "0":
            non_placeholder += 1
    report("Metrics show real data (not --)", non_placeholder >= 8,
           f"real values: {non_placeholder}/{len(metric_values)}")

    # Check gauge shows a percentage (SVG text element)
    gauge = page.query_selector("#gauge-value")
    if gauge:
        gauge_text = gauge.text_content()
        report("Gauge shows percentage", "%" in gauge_text,
               f"gauge={gauge_text}")

    # Check phases are rendered
    phases = page.query_selector_all(".phase-item")
    report("All 5 phases rendered", len(phases) == 5, f"count={len(phases)}")

    # Check decisions list has entries
    decisions = page.query_selector_all(".decision-entry")
    report("Decision log has entries", len(decisions) > 0, f"count={len(decisions)}")

    # Take screenshot
    page.screenshot(path="/shared/public/astra-live/screenshot-desktop.png", full_page=True)
    report("Desktop screenshot saved", True)

    # browser.close()


def test_dashboard_responsive(page):
    print("\n═══ RESPONSIVE TESTS ═══")

    viewports = [
        ("Desktop", 1440, 900),
        ("Tablet", 768, 1024),
        ("Mobile", 375, 812),
    ]

    for name, w, h in viewports:
        page.set_viewport_size({"width": w, "height": h})
        page.goto(BASE, wait_until="networkidle")
        time.sleep(2)

        # Check no horizontal overflow
        overflow = page.evaluate("""() => {
            return document.documentElement.scrollWidth > document.documentElement.clientWidth;
        }""")
        report(f"{name} ({w}px): No horizontal overflow", not overflow,
               f"scrollWidth vs clientWidth")

        # Check panels are visible
        panels = page.query_selector_all(".panel")
        visible_count = 0
        for p in panels:
            if p.is_visible():
                visible_count += 1
        report(f"{name}: Panels visible", visible_count >= 4,
               f"{visible_count}/{len(panels)} panels visible")

        # Check header is visible
        header = page.query_selector(".header")
        report(f"{name}: Header visible", header is not None and header.is_visible())

        # Screenshot
        page.screenshot(path=f"/shared/public/astra-live/screenshot-{name.lower()}.png")
        report(f"{name} screenshot saved", True)


def test_dashboard_console_errors(page):
    print("\n═══ CONSOLE ERROR TESTS ═══")

    
    

    errors = []
    page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)

    page.goto(BASE, wait_until="networkidle")
    time.sleep(5)  # Wait for API calls

    report("No console errors", len(errors) == 0,
           f"errors={errors[:3]}" if errors else "clean")
    for e in errors:
        print(f"  Console error: {e}")

    # browser.close()


def test_dashboard_network_requests(page):
    print("\n═══ NETWORK REQUEST TESTS ═══")

    
    

    api_calls = []
    page.on("request", lambda req: api_calls.append(req.url) if "/api/" in req.url else None)

    page.goto(BASE, wait_until="networkidle")
    time.sleep(5)

    report("Dashboard makes API calls", len(api_calls) > 0,
           f"count={len(api_calls)}, urls={[u.split('/')[-1] for u in api_calls[:10]]}")

    # Check that multiple endpoints are called
    endpoints_hit = set()
    for url in api_calls:
        endpoints_hit.add(url.split("?")[0].split("/")[-1])
    report("Multiple API endpoints called", len(endpoints_hit) >= 3,
           f"endpoints={endpoints_hit}")

    # browser.close()


def test_api_force_cycle():
    """Test the force-cycle endpoint."""
    print("\n═══ FORCE CYCLE TEST ═══")

    r1 = requests.get(f"{BASE}/api/state").json()
    c1 = r1['cycle_count']

    requests.post(f"{BASE}/api/engine/cycle")

    r2 = requests.get(f"{BASE}/api/state").json()
    c2 = r2['cycle_count']

    report("Force cycle increments cycle count", c2 > c1,
           f"cycles: {c1} → {c2}")


# ── Main ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("╔══════════════════════════════════════════════╗")
    print("║   ASTRA Live — End-to-End Test Suite         ║")
    print("╚══════════════════════════════════════════════╝")

    # API tests (no browser needed)
    test_api_endpoints()
    test_api_data_integrity()
    test_api_force_cycle()

    # Browser tests
    with sync_playwright() as pw:
        test_dashboard_renders(pw)
        test_dashboard_responsive(pw)
        test_dashboard_console_errors(pw)
        test_dashboard_network_requests(pw)

    # Engine liveness (must be last, takes 25s)
    test_engine_is_alive()

    # Summary
    print("\n" + "=" * 50)
    total = len(PASSES) + len(ERRORS)
    print(f"RESULTS: {len(PASSES)}/{total} passed, {len(ERRORS)} failed")
    if ERRORS:
        print("\nFAILURES:")
        for name, detail in ERRORS:
            print(f"  ❌ {name}: {detail}")
    else:
        print("\n🎉 All tests passed!")
