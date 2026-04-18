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

from astra_live_backend.safety.health import SystemHealthReport
"""
ASTRA Live — FastAPI Server
Real-time API for the ASTRA Live dashboard.
"""
import time
import json
import os
import sys
import numpy as np
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from astra_live_backend.engine import DiscoveryEngine

app = FastAPI(title="ASTRA Live API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the discovery engine
engine = DiscoveryEngine()

# Start the engine on import (5s delay before first cycle)
engine.start(interval=25.0)

# ── Scheduled Dashboard Snapshots (Phase 10.2) ────────────────
import threading
import logging

_snap_logger = logging.getLogger(__name__ + ".snapshot")

_snapshot_lock = threading.Lock()
_snapshot_status = {
    "last_refresh": None,
    "last_refresh_iso": None,
    "auto_enabled": True,
    "refresh_count": 0,
    "last_error": None,
}


def _do_snapshot_refresh():
    """Generate dashboard snapshot by calling generate_dashboard."""
    try:
        from astra_live_backend.generate_dashboard import fetch_all_data, build_dashboard_html, OUTPUT_PATH
        data = fetch_all_data()
        html = build_dashboard_html(data)
        with open(OUTPUT_PATH, 'w') as f:
            f.write(html)
        with _snapshot_lock:
            _snapshot_status["last_refresh"] = time.time()
            _snapshot_status["last_refresh_iso"] = time.strftime(
                "%Y-%m-%dT%H:%M:%SZ", time.gmtime()
            )
            _snapshot_status["refresh_count"] += 1
            _snapshot_status["last_error"] = None
        _snap_logger.info(
            f"Dashboard snapshot #{_snapshot_status['refresh_count']} written ({len(html)} bytes)"
        )
    except Exception as e:
        with _snapshot_lock:
            _snapshot_status["last_error"] = str(e)
        _snap_logger.error(f"Snapshot refresh failed: {e}")


def _snapshot_thread_fn(interval=120):
    """Background thread: refresh dashboard every `interval` seconds."""
    time.sleep(30)  # Initial delay to let server fully start
    while True:
        with _snapshot_lock:
            if not _snapshot_status["auto_enabled"]:
                time.sleep(10)
                continue
        try:
            _do_snapshot_refresh()
        except Exception as e:
            _snap_logger.error(f"Snapshot thread error: {e}")
        time.sleep(interval)


_snapshot_thread = threading.Thread(
    target=_snapshot_thread_fn, args=(60,), daemon=True, name="snapshot-refresh"
)
_snapshot_thread.start()


# ── API Endpoints ────────────────────────────────────────────────

@app.get("/api/status")
def api_status():
    """Engine status — is it running, cycle count, uptime."""
    state = engine.get_state()
    stigmergy_summary = {
        "pheromone_weight": engine.stigmergy.pheromone_weight,
        "total_deposits": engine.stigmergy.metrics.get("total_deposits", 0),
        "success_deposits": engine.stigmergy.metrics.get("success_deposits", 0),
        "failure_deposits": engine.stigmergy.metrics.get("failure_deposits", 0),
        "novelty_deposits": engine.stigmergy.metrics.get("novelty_deposits", 0),
    }
    return {
        "status": "running" if engine.running else "stopped",
        "engine": state,
        "stigmergy": stigmergy_summary,
        "timestamp": time.time(),
    }


@app.get("/api/state")
def api_state():
    """Full engine state for dashboard."""
    return engine.get_state()


@app.get("/api/hypotheses")
def api_hypotheses():
    """All hypotheses with their current state."""
    return engine.get_hypotheses()


@app.get("/api/hypotheses/{hid}")
def api_hypothesis(hid: str):
    """Single hypothesis detail."""
    h = engine.store.get(hid)
    if not h:
        return JSONResponse({"error": "not found"}, 404)
    return h.to_dict()


@app.post("/api/hypotheses")
def api_create_hypothesis(name: str, domain: str, description: str,
                          confidence: float = 0.25):
    """Create a new hypothesis."""
    from astra_live_backend.hypotheses import Phase
    h = engine.store.add(name, domain, description, confidence=confidence)
    h.phase = Phase.PROPOSED
    return h.to_dict()


@app.get("/api/activity")
def api_activity(limit: int = 50):
    """Recent activity log entries."""
    return engine.get_activity_log(limit)


@app.get("/api/decisions")
def api_decisions(limit: int = 20):
    """Recent autonomous decision log."""
    return engine.get_decision_log(limit)


@app.get("/api/charts")
def api_charts():
    """Chart data computed from real engine state."""
    return engine.get_chart_data()


@app.get("/api/metrics")
def api_metrics():
    """Key metrics for the metrics bar."""
    state = engine.get_state()
    return {
        "runtime_seconds": state["uptime_seconds"],
        "data_points": state["total_data_points"],
        "scripts_written": state["total_scripts"],
        "plots_generated": state["total_plots"],
        "hypotheses_tested": state["hypotheses_tested"],
        "queue_depth": state["queue_depth"],
        "domains_active": state["domains_active"],
        "system_confidence": state["system_confidence"],
        "auto_decisions": state["total_decisions"],
        "papers_drafted": state["papers_drafted"],
        "cross_domain_links": state["cross_domain_links"],
        "gpu_utilization": state["gpu_utilization"],
    }


@app.post("/api/engine/cycle")
def api_force_cycle():
    """Force a discovery cycle to run now."""
    engine.run_cycle()
    return {"status": "cycle completed", "cycle_count": engine.cycle_count}


@app.post("/api/engine/start")
def api_start_engine():
    engine.start(interval=20.0)
    return {"status": "started"}


@app.post("/api/engine/stop")
def api_stop_engine():
    engine.stop()
    return {"status": "stopped"}


# ── Safety & Control Endpoints (Phase 1 AGI Transformation) ─────

@app.post("/api/engine/pause")
def api_pause_engine():
    """Pause the discovery engine OODA cycle."""
    result = engine.safety.pause("Manual pause via API")
    return result


@app.post("/api/engine/resume")
def api_resume_engine():
    """Resume the discovery engine from pause."""
    result = engine.safety.resume("Manual resume via API")
    return result


@app.post("/api/engine/emergency-stop")
def api_emergency_stop():
    """Emergency stop: halt engine, save state."""
    result = engine.safety.emergency_stop("Emergency stop via API")
    return result


@app.post("/api/engine/safe-mode")
def api_safe_mode():
    """Switch to safe mode: read-only analysis only."""
    result = engine.safety.safe_mode("Switched to safe mode via API")
    return result


# ── Discovery Verification Endpoints ─────────────────────────────────────

@app.get("/api/verification/status")
def api_verification_status():
    """Get verification system status and statistics."""
    try:
        from astra_live_backend.verification_auto import get_discovery_verifier

        verifier = get_discovery_verifier()
        report = verifier.get_verification_report()

        return {
            'status': 'active',
            'total_evaluated': report['total_evaluated'],
            'total_verified': report['total_verified'],
            'total_rejected': report['total_rejected'],
            'verification_rate': report['verification_rate'],
            'available': True
        }
    except ImportError:
        return {
            'status': 'unavailable',
            'message': 'Verification module not available',
            'available': False
        }


@app.post("/api/verification/run")
def api_run_verification():
    """
    Trigger automatic verification workflow.

    Evaluates pending discoveries and promotes those that pass
    verification criteria to "Verified" status.
    """
    try:
        from astra_live_backend.verification_auto import get_verified_manager

        manager = get_verified_manager()

        # Run verification workflow
        new_verified = manager.update_verified_discoveries()

        # Get all verified discoveries
        all_verified = manager.get_all_verified_discoveries()

        return {
            'status': 'completed',
            'newly_verified': len(new_verified),
            'total_verified': len(all_verified),
            'discoveries': new_verified
        }
    except ImportError:
        return {
            'status': 'unavailable',
            'message': 'Verification module not available',
            'newly_verified': 0,
            'total_verified': 0,
            'discoveries': []
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e),
            'newly_verified': 0,
            'total_verified': 0,
            'discoveries': []
        }


@app.get("/api/verification/verified")
def api_verified_discoveries():
    """Get all verified discoveries for dashboard display."""
    try:
        from astra_live_backend.verification_auto import get_verified_manager

        manager = get_verified_manager()
        discoveries = manager.get_all_verified_discoveries()

        return {
            'status': 'success',
            'count': len(discoveries),
            'discoveries': discoveries
        }
    except ImportError:
        return {
            'status': 'unavailable',
            'message': 'Verification module not available',
            'count': 0,
            'discoveries': []
        }


@app.get("/api/engine/safety-status")
def api_safety_status():
    """Get safety controller state + audit log."""
    return engine.safety.get_full_status()


@app.get("/api/engine/state-space")
def api_state_space():
    """Phase 3: PCA mapped state space and attractors."""
    from astra_live_backend.state_space import StateSpaceVisualizer, AttractorMapper

    history = engine.get_state_vector_with_history()["history"]
    visualizer = StateSpaceVisualizer()
    mapper = AttractorMapper()

    trajectory = visualizer.fit_transform(history) or []
    steady_state = mapper.identify_steady_state(history)

    return {
        "trajectory": trajectory,
        "steady_state_attractor": steady_state,
    }


@app.get("/api/engine/state-vector")
def api_state_vector():
    """Get current state vector + history (last 100 cycles)."""
    return engine.get_state_vector_with_history()


@app.get("/api/engine/alignment")
def api_alignment():
    """Get alignment metrics."""
    return engine.alignment_checker.compute(engine.store, engine)


@app.get("/api/engine/anomalies")
def api_anomalies():
    """Get current anomalies + alert history."""
    return engine.anomaly_detector.get_full_report()


@app.get("/api/engine/pending")
def api_pending_approvals():
    """Get hypotheses awaiting approval for publication."""
    pending = engine.store.pending_approvals()
    return {
        "count": len(pending),
        "hypotheses": [h.to_dict() for h in pending],
    }


@app.post("/api/hypothesis/{hid}/approve")
def api_approve_hypothesis(hid: str, reason: str = "Approved via API"):
    """Approve a hypothesis for VALIDATED → PUBLISHED advancement."""
    h = engine.store.get(hid)
    if not h:
        return JSONResponse({"error": "Hypothesis not found"}, 404)

    # Safety check
    if not engine.safety.can_advance_hypotheses():
        return JSONResponse({
            "error": f"Cannot approve hypotheses in safety state {engine.safety.state.value}"
        }, 403)

    if h.approve(reason):
        engine.safety._audit(
            _get_safety_action("APPROVE"),
            engine.safety.state,
            engine.safety.state,
            f"Approved hypothesis {hid} ({h.name}): {reason}",
            "api",
        )
        return {"success": True, "hypothesis": h.to_dict()}
    else:
        return JSONResponse({
            "error": f"Cannot approve hypothesis {hid} (phase={h.phase.value}, approval_status={h.approval_status})"
        }, 400)


@app.post("/api/hypothesis/{hid}/reject")
def api_reject_hypothesis(hid: str, reason: str = "Rejected via API"):
    """Reject a hypothesis — stays at VALIDATED, approval cleared."""
    h = engine.store.get(hid)
    if not h:
        return JSONResponse({"error": "Hypothesis not found"}, 404)

    if h.reject(reason):
        engine.safety._audit(
            _get_safety_action("REJECT"),
            engine.safety.state,
            engine.safety.state,
            f"Rejected hypothesis {hid} ({h.name}): {reason}",
            "api",
        )
        return {"success": True, "hypothesis": h.to_dict()}
    else:
        return JSONResponse({
            "error": f"Cannot reject hypothesis {hid} (approval_status={h.approval_status})"
        }, 400)


@app.post("/api/hypothesis/{hid}/archive")
def api_archive_hypothesis(hid: str, reason: str = "Archived via API"):
    """Force-archive a hypothesis regardless of current phase."""
    from astra_live_backend.hypotheses import Phase
    h = engine.store.get(hid)
    if not h:
        return JSONResponse({"error": "Hypothesis not found"}, 404)
    h.phase = Phase.ARCHIVED
    h.archived_at = __import__("time").time()
    h.updated_at = h.archived_at
    return {"success": True, "hypothesis": h.to_dict()}


@app.post("/api/hypotheses/cleanup")
def api_cleanup_hypotheses(pattern: str = "", min_version: int = 2):
    """Archive duplicate/versioned hypotheses matching a pattern."""
    import re
    from astra_live_backend.hypotheses import Phase
    archived = []
    for h in engine.store.all():
        name = h.name
        m = re.search(r'\(v(\d+)\)', name)
        if m and int(m.group(1)) >= min_version:
            if not pattern or pattern.lower() in name.lower():
                h.phase = Phase.ARCHIVED
                h.archived_at = __import__("time").time()
                h.updated_at = h.archived_at
                archived.append(name)
    return {"archived_count": len(archived), "archived": archived}


@app.get("/api/system/health_old")
def api_system_health_old():
    """System component health status."""
    components = {}

    # Engine
    components["engine"] = {
        "status": "healthy" if engine.running else "stopped",
        "cycle_count": engine.cycle_count,
        "uptime_seconds": time.time() - engine.start_time,
    }

    # Safety controller
    components["safety_controller"] = {
        "status": "healthy",
        "state": engine.safety.state.value,
        "audit_log_size": len(engine.safety._audit_log),
    }

    # Hypothesis store
    total_h = len(engine.store.all())
    active_h = len(engine.store.active())
    components["hypothesis_store"] = {
        "status": "healthy" if total_h > 0 else "empty",
        "total": total_h,
        "active": active_h,
        "pending_approvals": len(engine.store.pending_approvals()),
    }

    # Anomaly detector
    anomalies = engine.anomaly_detector.get_current_anomalies()
    critical = sum(1 for a in anomalies if a.get("severity") == "CRITICAL")
    components["anomaly_detector"] = {
        "status": "critical" if critical > 0 else ("warning" if anomalies else "healthy"),
        "current_anomalies": len(anomalies),
        "critical_count": critical,
        "total_alerts": len(engine.anomaly_detector._alerts),
    }

    # Alignment checker
    try:
        alignment = engine.alignment_checker.compute(engine.store, engine)
        components["alignment_checker"] = {
            "status": "healthy",
            "composite_score": alignment["composite_score"],
        }
    except Exception as e:
        components["alignment_checker"] = {
            "status": "error",
            "error": str(e),
        }

    # State vector
    components["state_vector"] = {
        "status": "healthy" if len(engine.state_vector_history) > 0 else "initializing",
        "history_length": len(engine.state_vector_history),
    }

    # Overall health
    statuses = [c["status"] for c in components.values()]
    if "critical" in statuses or "error" in statuses:
        overall = "degraded"
    elif all(s == "healthy" for s in statuses):
        overall = "healthy"
    else:
        overall = "operational"

    return {
        "overall": overall,
        "components": components,
        "timestamp": time.time(),
    }


def _get_safety_action(name: str):
    """Helper to get SafetyAction enum value."""
    from astra_live_backend.safety import SafetyAction
    return SafetyAction[name]


# ── Serve the Dashboard ──────────────────────────────────────────

DASHBOARD_DIR = Path("astra-live")


async def _ensure_dashboard_exists():
    """Ensure dashboard directory and file exist. Auto-generates if missing."""
    import subprocess
    import shutil
    from pathlib import Path

    # Create directory if it doesn't exist
    DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)

    dashboard_path = DASHBOARD_DIR / "index.html"

    if not dashboard_path.exists():
        # Copy template if available
        template_path = Path(__file__).parent / "dashboard_template.html"
        if template_path.exists():
            shutil.copy(str(template_path), str(dashboard_path))
        else:
            # Create minimal dashboard as fallback
            minimal_html = """<!DOCTYPE html>
<html>
<head>
    <title>ASTRA Live</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { border-bottom: 2px solid #0066cc; padding-bottom: 20px; margin-bottom: 30px; }
        .status { background: #f0f8ff; padding: 20px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #0066cc; }
        .cognitive { background: #f0fff0; padding: 20px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #28a745; }
        h1 { color: #333; margin: 0; }
        h2 { color: #444; margin-top: 30px; }
        a { color: #0066cc; }
        .endpoint { margin: 10px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧠 ASTRA Live — Autonomous Scientific Discovery</h1>
            <p>With Cognitive Architecture (Phase 15: Scientific AGI)</p>
        </div>
        <div class="status">
            <h2>⚡ System Status</h2>
            <p><strong>Server:</strong> Running at <a href="http://localhost:8787">http://localhost:8787</a></p>
            <p><strong>Dashboard:</strong> <a href="/api/status">API Status</a></p>
            <p><strong>Documentation:</strong> <a href="/docs">API Docs</a></p>
        </div>
        <div class="cognitive">
            <h2>🧠 Cognitive Architecture (New!)</h2>
            <div class="endpoint"><a href="/api/cognitive/status">/api/cognitive/status</a></div>
            <div class="endpoint"><a href="/api/cognitive/dashboard">/api/cognitive/dashboard</a></div>
            <div class="endpoint"><a href="/api/knowledge-graph/statistics">/api/knowledge-graph/statistics</a></div>
            <div class="endpoint"><a href="/api/knowledge-graph/gaps">/api/knowledge-graph/gaps</a></div>
            <div class="endpoint"><a href="/api/metacognition/report">/api/metacognition/report</a></div>
        </div>
        <p><em>ASTRA is running with Scientific AGI capabilities enabled.</em></p>
    </div>
</body>
</html>"""
            with open(dashboard_path, 'w') as f:
                f.write(minimal_html)


@app.get("/")
async def serve_dashboard():
    """ASTRA Live dashboard. Auto-generates if missing."""
    dashboard_path = DASHBOARD_DIR / "index.html"

    # Auto-generate dashboard if it doesn't exist
    if not dashboard_path.exists():
        await _ensure_dashboard_exists()

    return FileResponse(
        dashboard_path,
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )


# ── Phase 4: Operational Readiness Endpoints ──────────────────────

@app.get("/api/engine/arbiter")
def api_arbiter_status():
    """Safety Arbiter status and recent verdicts."""
    return engine.arbiter.get_status()


@app.get("/api/engine/arbiter/verdicts")
def api_arbiter_verdicts(limit: int = 50):
    """Safety Arbiter verdict history."""
    return engine.arbiter.get_verdict_history(limit)


@app.post("/api/engine/arbiter/override")
def api_arbiter_override(supervisor_id: str = "system", reason: str = "Manual override",
                         force: str = "GO", duration: float = 300.0):
    """Add a supervisor override to the arbiter."""
    return engine.arbiter.add_override(supervisor_id, reason, force, duration)


@app.get("/api/engine/supervisors")
def api_supervisors():
    """Supervisor of Record status."""
    return engine.supervisor_registry.get_status()


@app.get("/api/engine/supervisors/list")
def api_supervisors_list():
    """List all registered supervisors."""
    return engine.supervisor_registry.get_supervisors()


@app.get("/api/engine/supervisors/actions")
def api_supervisor_actions(limit: int = 50):
    """Supervisor action log."""
    return engine.supervisor_registry.get_action_log(limit)


@app.post("/api/engine/supervisors/shift/start")
def api_start_shift(supervisor_id: str = "system", handoff_notes: str = ""):
    """Start a new supervisor shift."""
    return engine.supervisor_registry.start_shift(supervisor_id, handoff_notes)


@app.post("/api/engine/supervisors/shift/end")
def api_end_shift(supervisor_id: str = "system", handoff_notes: str = ""):
    """End the current supervisor shift."""
    return engine.supervisor_registry.end_shift(supervisor_id, handoff_notes)


@app.get("/api/engine/ceremony")
def api_ceremony_status():
    """Phase Commencement Ceremony status."""
    return engine.ceremony_protocol.get_status()


@app.post("/api/engine/ceremony/initiate")
def api_ceremony_initiate(from_level: str = "SHADOW", to_level: str = "SUPERVISED",
                          supervisor_id: str = "system"):
    """Initiate a phase commencement ceremony."""
    return engine.ceremony_protocol.initiate(from_level, to_level, supervisor_id)


@app.get("/api/engine/orp")
def api_orp_status():
    """Operational Readiness Plan status."""
    return engine.orp.get_status()


@app.get("/api/engine/orp/checklist")
def api_orp_checklist():
    """Full ORP checklist."""
    return engine.orp.get_checklist()


@app.get("/api/engine/orp/assess")
def api_orp_assess():
    """Full readiness assessment with go/no-go."""
    return engine.orp.assess_readiness()


@app.get("/api/engine/safety-case")
def api_safety_case():
    """Safety Case status."""
    return engine.safety_case.get_status()


@app.get("/api/engine/safety-case/hazards")
def api_safety_hazards():
    """Hazard register."""
    return engine.safety_case.get_hazard_register()


@app.get("/api/engine/safety-case/claims")
def api_safety_claims():
    """Safety claims with evidence."""
    return engine.safety_case.get_safety_claims()


@app.get("/api/engine/safety-case/risk")
def api_safety_risk():
    """Risk summary with ALARP assessment."""
    return engine.safety_case.get_risk_summary()


@app.get("/api/engine/orp/rollback/{level}")
def api_rollback_procedure(level: str):
    """Get rollback procedure for given autonomy level."""
    return engine.orp.get_rollback_procedure(level)


@app.get("/api/engine/novelty")
def api_novelty_status():
    """Novelty detector status and recent signals."""
    return engine.novelty_detector.get_status()


@app.get("/api/engine/novelty/signals")
def api_novelty_signals(limit: int = 20, min_score: float = 0.0):
    """Novelty signals filtered by minimum novelty score."""
    return engine.novelty_detector.get_signals(limit, min_score)


@app.get("/api/engine/novelty/unexplored")
def api_novelty_unexplored():
    """Unexplored high-novelty signals."""
    return engine.novelty_detector.get_unexplored()


@app.get("/api/literature/search")
def api_literature_search(query: str = "galaxy", max_results: int = 5):
    """Search arXiv for related literature."""
    from astra_live_backend.data_fetcher import search_arxiv_astroph
    papers = search_arxiv_astroph(query, max_results)
    return {"query": query, "results": papers, "count": len(papers)}


# ── Literature Integration (Phase 9.1+9.2) ──────────────────────

@app.get("/api/literature/papers")
def api_literature_papers():
    """List all cached papers in the literature store."""
    from astra_live_backend.literature import get_literature_store
    store = get_literature_store()
    return {
        "papers": store.get_papers(),
        "total": store.paper_count,
        "backend": "sklearn" if store._vectorizer is not None else "custom",
        "timestamp": time.time(),
    }


@app.post("/api/literature/search-similar")
async def api_literature_search_similar(request: Request):
    """Find papers similar to a text query using TF-IDF cosine similarity."""
    body = await request.json()
    text = body.get("text", "")
    top_k = body.get("top_k", 5)

    if not text:
        return JSONResponse({"error": "'text' field is required"}, 400)

    from astra_live_backend.literature import get_literature_store
    store = get_literature_store()
    report = store.novelty_report(text, top_k=top_k)
    report["timestamp"] = time.time()
    return report


@app.get("/api/literature/novelty/{hid}")
def api_literature_novelty(hid: str):
    """Compute novelty score for a hypothesis by its ID."""
    h = engine.store.get(hid)
    if not h:
        return JSONResponse({"error": "Hypothesis not found"}, 404)

    from astra_live_backend.literature import get_literature_store
    store = get_literature_store()
    text = f"{h.name} {h.description}"
    report = store.novelty_report(text, top_k=5)
    report["hypothesis_id"] = hid
    report["hypothesis_name"] = h.name
    report["timestamp"] = time.time()
    return report


# ── Citation Network (Phase 9.4) ─────────────────────────────────

@app.get("/api/literature/citation-graph")
def api_citation_graph():
    """Return the citation graph as {nodes, edges} for visualization."""
    from astra_live_backend.literature import get_citation_graph, get_literature_store
    graph = get_citation_graph()
    graph.build_from_literature_store(get_literature_store())
    return graph.to_graph_json()


@app.get("/api/literature/citation-metrics")
def api_citation_metrics():
    """Return citation metrics: most cited papers, network stats, h-index."""
    from astra_live_backend.literature import get_citation_graph, get_literature_store
    graph = get_citation_graph()
    graph.build_from_literature_store(get_literature_store())
    store = get_literature_store()
    most_cited = graph.most_cited(10)
    enriched = []
    for pid, count in most_cited:
        paper = store._papers.get(pid)
        enriched.append({
            "paper_id": pid,
            "title": paper.title if paper else pid,
            "citation_count": count,
        })
    return {
        "most_cited": enriched,
        "network_stats": graph.network_stats(),
        "h_index": graph.h_index(),
        "timestamp": time.time(),
    }


# ── Dashboard Snapshots (Phase 10.2) ─────────────────────────────

@app.get("/api/system/snapshot-status")
def api_snapshot_status():
    """Return the current snapshot status."""
    with _snapshot_lock:
        return {**_snapshot_status, "timestamp": time.time()}


@app.post("/api/system/snapshot-refresh")
def api_snapshot_refresh():
    """Trigger an immediate dashboard snapshot refresh."""
    t = threading.Thread(target=_do_snapshot_refresh, daemon=True)
    t.start()
    return {"status": "refresh_triggered", "timestamp": time.time()}


# ── ASTRA Core Scientific Capabilities (White & Dey 2026) ───────

@app.post("/api/science/causal-discovery")
def api_causal_discovery(variables: str = "", method: str = "PC", alpha: float = 0.05):
    """
    Run causal discovery (PC or FCI algorithm).
    variables: comma-separated variable names to include
    """
    import numpy as np
    # Use cached SDSS data for demonstration
    from astra_live_backend.data_fetcher import get_cached_sdss
    sdss = get_cached_sdss()
    if sdss.data is None or len(sdss.data) < 10:
        return {"error": "No data available"}

    if variables:
        var_names = [v.strip() for v in variables.split(",")]
    else:
        var_names = ["redshift", "u", "g", "r", "i"]

    # Build data matrix
    available = [v for v in var_names if v in sdss.data.dtype.names]
    if len(available) < 2:
        return {"error": f"Not enough variables found. Available: {list(sdss.data.dtype.names)}"}

    data = np.column_stack([sdss.data[v] for v in available])
    valid = np.all(np.isfinite(data), axis=1)
    data = data[valid]

    return engine.run_causal_discovery(available, data, method, alpha)


@app.post("/api/science/dimensional-analysis")
def api_dimensional_analysis(variables: str = ""):
    """
    Apply Buckingham π theorem.
    variables: JSON dict of variable_name: dimension_type
    """
    import json
    if variables:
        try:
            var_dict = json.loads(variables)
        except:
            return {"error": "Invalid JSON for variables"}
    else:
        # Default: filament scaling relation
        var_dict = {
            "mass": "mass",
            "length": "length",
            "velocity_dispersion": "velocity",
            "gravitational_constant": "dimensionless",  # G appears in π groups
        }
    return engine.run_dimensional_analysis(var_dict)


@app.post("/api/science/scaling-relation")
def api_scaling_relation(x_col: str = "sma", y_col: str = "period"):
    """Discover power-law scaling relation between two variables."""
    import numpy as np
    from astra_live_backend.data_fetcher import get_cached_exoplanets, get_cached_sdss

    # Try exoplanets first
    exo = get_cached_exoplanets()
    if exo.data is not None and x_col in exo.data.dtype.names and y_col in exo.data.dtype.names:
        x = exo.data[x_col]
        y = exo.data[y_col]
        return engine.run_scaling_discovery(x, y, x_col, y_col)

    # Try SDSS
    sdss = get_cached_sdss()
    if sdss.data is not None and x_col in sdss.data.dtype.names and y_col in sdss.data.dtype.names:
        x = sdss.data[x_col]
        y = sdss.data[y_col]
        return engine.run_scaling_discovery(x, y, x_col, y_col)

    return {"error": f"Columns {x_col},{y_col} not found in available data"}


@app.post("/api/science/model-comparison")
def api_model_comparison(x_col: str = "sma", y_col: str = "period"):
    """Bayesian model comparison on two variables."""
    import numpy as np
    from astra_live_backend.data_fetcher import get_cached_exoplanets
    exo = get_cached_exoplanets()
    if exo.data is None:
        return {"error": "No exoplanet data available"}

    if x_col not in exo.data.dtype.names or y_col not in exo.data.dtype.names:
        return {"error": f"Columns not found. Available: {list(exo.data.dtype.names)}"}

    x = exo.data[x_col]
    y = exo.data[y_col]
    valid = (x > 0) & (y > 0) & np.isfinite(x) & np.isfinite(y)

    return engine.run_model_comparison(x[valid], y[valid])


@app.post("/api/science/knowledge-isolation")
def api_knowledge_isolation(target: str = "", variables: str = ""):
    """
    Full knowledge isolation discovery pipeline.
    Implements Test Case 6 from the paper.
    """
    import numpy as np
    from astra_live_backend.data_fetcher import get_cached_sdss
    sdss = get_cached_sdss()
    if sdss.data is None or len(sdss.data) < 10:
        return {"error": "No data available"}

    if variables:
        var_names = [v.strip() for v in variables.split(",")]
    else:
        var_names = ["redshift", "u", "g", "r", "i"]

    available = [v for v in var_names if v in sdss.data.dtype.names]
    if len(available) < 3:
        return {"error": "Need at least 3 variables"}

    data = np.column_stack([sdss.data[v] for v in available])
    valid = np.all(np.isfinite(data), axis=1)
    data = data[valid]

    target_var = target if target in available else available[0]

    return engine.run_knowledge_isolation(data, available, target_var)


@app.post("/api/science/intervention-test")
def api_intervention_test(cause: str = "g", effect: str = "r"):
    """Test a causal claim via intervention analysis."""
    import numpy as np
    from astra_live_backend.data_fetcher import get_cached_sdss
    sdss = get_cached_sdss()
    if sdss.data is None:
        return {"error": "No data available"}

    available = list(sdss.data.dtype.names)
    if cause not in available or effect not in available:
        return {"error": f"Variables not found. Available: {available}"}

    var_names = [cause, effect]
    data = np.column_stack([sdss.data[v] for v in var_names])
    valid = np.all(np.isfinite(data), axis=1)
    data = data[valid]

    return engine.run_intervention_test(data, var_names, cause, effect)


# ── Discovery Memory & Self-Improvement Endpoints ─────────────────

@app.get("/api/discovery-memory")
def api_discovery_memory():
    """Discovery memory state — tracks findings, method effectiveness, exploration."""
    return engine.discovery_memory.to_dict()


@app.get("/api/discovery-memory/discoveries")
def api_discovery_discoveries(min_strength: float = 0.0, limit: int = 50, sort_by: str = "timestamp"):
    """List recorded discoveries, optionally filtered by strength.

    Args:
        min_strength: Minimum strength threshold (default: 0.0)
        limit: Maximum number to return (default: 50)
        sort_by: Sort field - 'timestamp' for chronological, 'strength' for highest first (default: "timestamp")
    """
    discoveries = [d for d in engine.discovery_memory.discoveries
                   if d.strength >= min_strength]

    # Sort by timestamp (chronological) by default for proper timeline display
    if sort_by == "strength":
        discoveries.sort(key=lambda d: d.strength, reverse=True)
    else:
        discoveries.sort(key=lambda d: d.timestamp)

    from dataclasses import asdict
    return [asdict(d) for d in discoveries[:limit]]


@app.get("/api/discovery-memory/graph")
def api_discovery_graph():
    """Discovery relationship graph — how findings connect."""
    return engine.discovery_memory.get_discovery_graph()


@app.get("/api/discovery-memory/improvement")
def api_improvement_metrics():
    """Self-improvement metrics — how the system is evolving."""
    return engine.discovery_memory.compute_improvement_metrics()


@app.get("/api/strategy")
def api_strategy():
    """Current adaptive strategy state."""
    return engine.strategist.get_strategy_summary()


@app.get("/api/strategy/exploration")
def api_exploration():
    """Exploration coverage — which data/variable combinations have been tested."""
    result = {}
    for source in ["exoplanets", "sdss", "gaia", "pantheon"]:
        untested = engine.discovery_memory.get_unexplored_variable_pairs(source)
        es = engine.discovery_memory.exploration.get(source)
        result[source] = {
            "untested_pairs": len(untested),
            "sample_untested": untested[:5],
            "explored_count": es.total_explorations if es else 0,
            "novelty_rate": round(es.novelty_rate, 3) if es else 0,
        }
    return result


@app.post("/api/discovery-memory/generate")
def api_generate_hypotheses():
    """Force hypothesis generation from discovery memory."""
    from astra_live_backend.hypotheses import Phase
    existing_names = {h.name for h in engine.store.all()}
    candidates = engine.hypothesis_generator.generate_from_discoveries(
        current_cycle=engine.cycle_count,
        existing_names=existing_names,
        max_new=5,
    )
    # Also generate diversification hypotheses if one domain dominates
    diversification_candidates = engine.hypothesis_generator.generate_diversification_hypotheses(
        current_cycle=engine.cycle_count,
        existing_names=existing_names,
        max_new=3,
    )
    # Combine candidates (diversification get priority)
    all_candidates = diversification_candidates + candidates

    # If regular generation doesn't produce enough results, use continuous exploration
    if len(all_candidates) < 3:
        continuous_candidates = engine.hypothesis_generator.generate_continuous_exploration(
            current_cycle=engine.cycle_count,
            existing_names=existing_names,
            max_new=10,
        )
        all_candidates.extend(continuous_candidates)

    generated = []
    for c in all_candidates:
        h = engine.store.add(c["name"], c["domain"], c["description"],
                             confidence=c["confidence"],
                             variables=c.get("variables", []),
                             finding_type=c.get("finding_type", ""),
                             data_source=c.get("data_source", ""))
        h.phase = Phase.PROPOSED
        engine.discovery_memory.generation_count += 1
        generated.append({"id": h.id, "name": c["name"], "source": c.get("source_discovery_id")})
    return {"generated": generated, "total_memory_discoveries": len(engine.discovery_memory.discoveries)}


# ── Serve the Dashboard ──────────────────────────────────────────

DASHBOARD_DIR = Path("astra-live")


async def _ensure_dashboard_exists():
    """Ensure dashboard directory and file exist."""
    import subprocess
    import shutil

    # Create directory if it doesn't exist
    DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)

    dashboard_path = DASHBOARD_DIR / "index.html"

    if not dashboard_path.exists():
        # Copy template if available
        template_path = Path(__file__).parent / "dashboard_template.html"
        if template_path.exists():
            shutil.copy(template_path, dashboard_path)
        else:
            # Create minimal dashboard as fallback
            minimal_html = """<!DOCTYPE html>
<html>
<head>
    <title>ASTRA Live</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .status { background: #f0f8ff; padding: 20px; border-radius: 5px; margin: 20px 0; }
        .cognitive { background: #f0fff0; padding: 20px; border-radius: 5px; margin: 20px 0; }
        .endpoints { background: #fff8f0; padding: 20px; border-radius: 5px; margin: 20px 0; }
    </style>
</head>
<body>
    <h1>🧠 ASTRA Live — Autonomous Scientific Discovery</h1>
    <p>With Cognitive Architecture (Phase 15)</p>
    <div class="status">
        <h2>System Status</h2>
        <p><strong>Server:</strong> Running</p>
        <p><strong>Dashboard:</strong> <a href="/api/status">API Status</a></p>
        <p><strong>Documentation:</strong> <a href="/docs">API Docs</a></p>
    </div>
    <div class="cognitive">
        <h2>🧠 Cognitive Architecture (New!)</h2>
        <ul>
            <li><a href="/api/cognitive/status">Cognitive Status</a></li>
            <li><a href="/api/cognitive/dashboard">Cognitive Dashboard</a></li>
            <li><a href="/api/knowledge-graph/statistics">Knowledge Graph</a></li>
            <li><a href="/api/knowledge-graph/gaps">Knowledge Gaps</a></li>
            <li><a href="/api/metacognition/report">Meta-Cognition Report</a></li>
        </ul>
    </div>
    <div class="endpoints">
        <h2>Key API Endpoints</h2>
        <ul>
            <li><a href="/api/hypotheses">Hypotheses</a></li>
            <li><a href="/api/activity">Activity Log</a></li>
            <li><a href="/api/engine/state-space">State Space</a></li>
            <li><a href="/api/discovery-memory">Discovery Memory</a></li>
        </ul>
    </div>
    <p><em>ASTRA is running with Scientific AGI capabilities enabled.</em></p>
</body>
</html>"""
            with open(dashboard_path, 'w') as f:
                f.write(minimal_html)


@app.get("/api/system/health")
def api_system_health():
    """Component health for the Health tab (Phase 2 Update)."""
    health = SystemHealthReport()
    return health.get_report(engine.get_state())


# ═══════════════════════════════════════════════════════════════
# Data Registry Endpoints (Phase 6)
# ═══════════════════════════════════════════════════════════════

@app.get("/api/data-sources")
def api_data_sources():
    """List all registered data sources."""
    from astra_live_backend.data_registry import get_registry
    reg = get_registry()
    return {
        "sources": reg.list_sources(),
        "stats": reg.get_stats(),
        "timestamp": time.time(),
    }


@app.get("/api/data-sources/{source_id}")
def api_data_source_detail(source_id: str):
    """Get details and schema for a specific data source."""
    from astra_live_backend.data_registry import get_registry
    reg = get_registry()
    source = reg.get_source(source_id)
    if not source:
        return JSONResponse(status_code=404,
                            content={"error": f"Unknown source: {source_id}"})
    return {
        "id": source_id,
        "name": source.schema.name,
        "description": source.schema.description,
        "domain": source.schema.domain.value,
        "columns": [{"name": c.name, "dtype": c.dtype, "unit": c.unit,
                      "description": c.description} for c in source.schema.columns],
        "variables": source.variables,
        "api_url": source.schema.api_url,
        "reference": source.schema.reference,
        "cross_match_keys": source.schema.cross_match_keys,
        "priority": source.priority,
        "timestamp": time.time(),
    }


@app.get("/api/data-sources/{source_id}/fetch")
def api_fetch_data_source(source_id: str):
    """Fetch data from a specific source."""
    from astra_live_backend.data_registry import get_registry
    reg = get_registry()
    result = reg.fetch(source_id, use_cache=True)
    return {
        "source": result.source,
        "row_count": result.row_count,
        "fetch_time": result.fetch_time,
        "columns": list(result.data.dtype.names) if result.data is not None and result.data.dtype.names else [],
        "metadata": {k: v for k, v in result.metadata.items()
                     if k != 'records'},  # Don't return raw records in API
        "timestamp": time.time(),
    }


@app.get("/api/cross-matches")
def api_cross_matches():
    """Get all possible cross-source data links."""
    from astra_live_backend.data_registry import get_registry
    reg = get_registry()
    pairs = reg.get_cross_link_pairs()
    links = []
    for a, b, key in pairs:
        src_a = reg.get_source(a)
        src_b = reg.get_source(b)
        if src_a and src_b:
            links.append({
                "source_a": a,
                "source_a_name": src_a.schema.name,
                "source_b": b,
                "source_b_name": src_b.schema.name,
                "match_key": key,
                "common_variables": list(set(src_a.variables) & set(src_b.variables)),
            })
    return {
        "links": links,
        "total_pairs": len(links),
        "timestamp": time.time(),
    }


@app.get("/api/variables")
def api_variables():
    """Get all available variables with affinities."""
    from astra_live_backend.data_registry import get_registry, Domain
    reg = get_registry()
    return {
        "variables": reg.get_variables(),
        "affinities": reg.get_variable_affinities(),
        "by_domain": {
            "exoplanets": reg.get_variables(Domain.EXOPLANETS),
            "cosmology": reg.get_variables(Domain.COSMOLOGY),
            "stellar": reg.get_variables(Domain.STELLAR),
            "galaxies": reg.get_variables(Domain.GALAXIES),
        },
        "timestamp": time.time(),
    }


@app.get("/api/persistence")
def api_persistence():
    """SQLite persistence stats."""
    # Handle both DiscoveryMemory and GraphPalaceMemory
    if hasattr(engine.discovery_memory, 'get_persistence_stats'):
        return engine.discovery_memory.get_persistence_stats()
    elif hasattr(engine.discovery_memory, 'get_palace_status'):
        # GraphPalaceMemory uses get_palace_status
        return engine.discovery_memory.get_palace_status()
    elif hasattr(engine.discovery_memory, 'to_dict'):
        # Fallback to to_dict if available
        return engine.discovery_memory.to_dict()
    else:
        # Ultimate fallback: return basic stats
        return {
            "discovery_count": len(getattr(engine.discovery_memory, 'discoveries', [])),
            "memory_type": type(engine.discovery_memory).__name__
        }


@app.get("/api/engine/degradation-status")
def api_degradation_status():
    """Current degradation detection metrics and recommendations."""
    return engine.degradation_detector.get_status()


@app.get("/api/statistics/methods")
def api_statistics_methods():
    """Available advanced statistical methods and their status."""
    from astra_live_backend.statistics import (
        fdr_correction, cohen_d, cramers_v, eta_squared,
        detect_autocorrelation, change_point_detection,
    )
    return {
        "methods": {
            "fdr_correction": {"available": True, "description": "Benjamini-Hochberg FDR correction"},
            "cohen_d": {"available": True, "description": "Cohen's d effect size (continuous)"},
            "cramers_v": {"available": True, "description": "Cramér's V effect size (categorical)"},
            "eta_squared": {"available": True, "description": "η² effect size (ANOVA)"},
            "effect_size_report": {"available": True, "description": "Auto-select effect size measure"},
            "detect_autocorrelation": {"available": True, "description": "Ljung-Box autocorrelation test"},
            "change_point_detection": {"available": True, "description": "CUSUM change point detection"},
            "granger_causality": {"available": True, "description": "Granger causality F-test"},
            "compute_posterior_intervals": {"available": True, "description": "Laplace approximation posterior"},
            "confounder_detection": {"available": True, "description": "Backdoor criterion proxy — detect confounders"},
        },
        "timestamp": time.time(),
    }


@app.post("/api/statistics/confounder-analysis")
async def api_confounder_analysis(request: Request):
    """Detect confounders between a cause-effect pair in a data source."""
    body = await request.json()
    cause = body.get("cause")
    effect = body.get("effect")
    data_source = body.get("data_source", "sdss")
    alpha = body.get("alpha", 0.05)

    if not cause or not effect:
        return {"error": "Both 'cause' and 'effect' fields are required"}

    import pandas as pd
    import numpy as np
    from astra_live_backend.statistics import detect_confounders
    from astra_live_backend.data_fetcher import data_cache

    # Fetch data from shared cache
    try:
        # Map source name to cached fetch function
        source_map = {
            "sdss": "sdss",
            "exoplanets": "exoplanets",
            "gaia": "gaia",
            "pantheon": "pantheon",
        }
        cache_key = source_map.get(data_source, data_source)
        source_data = data_cache.get(cache_key)

        if source_data is None:
            # Trigger a fetch
            from astra_live_backend.data_fetcher import (
                get_cached_sdss, get_cached_exoplanets,
                get_cached_gaia, get_cached_pantheon,
            )
            fetch_map = {
                "sdss": get_cached_sdss,
                "exoplanets": get_cached_exoplanets,
                "gaia": get_cached_gaia,
                "pantheon": get_cached_pantheon,
            }
            fetcher = fetch_map.get(data_source)
            if fetcher:
                source_data = fetcher()
            else:
                return {"error": f"Unknown data source '{data_source}'",
                        "available_sources": list(source_map.keys())}

        # Extract the numpy array from DataResult
        raw_data = source_data.data if hasattr(source_data, 'data') else source_data

        # Convert structured/recarray numpy to DataFrame
        if isinstance(raw_data, np.ndarray) and raw_data.dtype.names:
            df = pd.DataFrame({name: raw_data[name] for name in raw_data.dtype.names})
        elif isinstance(raw_data, np.ndarray):
            df = pd.DataFrame(raw_data)
        elif isinstance(raw_data, pd.DataFrame):
            df = raw_data
        else:
            return {"error": f"Cannot convert {type(raw_data)} to DataFrame"}

        # Validate columns
        available = list(df.select_dtypes(include=[np.number]).columns)
        if cause not in df.columns:
            return {"error": f"Column '{cause}' not found in {data_source}",
                    "available_columns": available[:30]}
        if effect not in df.columns:
            return {"error": f"Column '{effect}' not found in {data_source}",
                    "available_columns": available[:30]}

        result = detect_confounders(df, cause, effect, alpha)
        result["data_source"] = data_source
        result["n_rows"] = len(df)
        result["timestamp"] = time.time()
        return result

    except Exception as e:
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc(),
                "cause": cause, "effect": effect, "data_source": data_source}


# ── Paper Draft Endpoints (Phase 9.5) ─────────────────────────

@app.get("/api/papers")
async def api_papers():
    """List all generated paper drafts."""
    return {
        "drafts": engine.paper_generator.get_all_drafts(),
        "count": engine.paper_generator.draft_count,
        "timestamp": time.time(),
    }


@app.get("/api/papers/{hypothesis_id}")
async def api_paper_detail(hypothesis_id: str):
    """Get a full paper draft for a specific hypothesis."""
    draft = engine.paper_generator.get_draft(hypothesis_id)
    if draft is None:
        # Check if hypothesis exists at all
        h = engine.store.get(hypothesis_id)
        if h is None:
            return JSONResponse(
                status_code=404,
                content={"error": f"Hypothesis '{hypothesis_id}' not found"},
            )
        return JSONResponse(
            status_code=404,
            content={
                "error": f"No paper draft exists for hypothesis '{hypothesis_id}'",
                "hypothesis_phase": h.phase.value,
                "confidence": h.confidence,
                "hint": "Paper drafts are auto-generated for hypotheses validated with confidence > 0.95. "
                        "You can also POST to /api/papers/{id}/regenerate to force generation.",
            },
        )
    return {
        "draft": draft.to_dict(),
        "full_text": draft.full_text(),
        "timestamp": time.time(),
    }


@app.post("/api/papers/{hypothesis_id}/regenerate")
async def api_paper_regenerate(hypothesis_id: str):
    """Force regenerate a paper draft for a hypothesis."""
    h = engine.store.get(hypothesis_id)
    if h is None:
        return JSONResponse(
            status_code=404,
            content={"error": f"Hypothesis '{hypothesis_id}' not found"},
        )
    try:
        draft = engine.paper_generator.generate_full_draft(h)
        engine.papers_drafted = engine.paper_generator.draft_count
        return {
            "status": "regenerated",
            "draft": draft.to_dict(),
            "full_text": draft.full_text(),
            "version": draft.version,
            "timestamp": time.time(),
        }
    except Exception as e:
        import traceback
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "traceback": traceback.format_exc()},
        )


# ── Phase 11.1+11.2: Provenance & Export ─────────────────────
from astra_live_backend.exporter import ASTRAExporter

_exporter = ASTRAExporter(engine)


@app.get("/api/provenance")
async def api_provenance():
    """List all provenance records."""
    records = engine.provenance_tracker.get_all()
    return {
        "records": records,
        "count": len(records),
        "timestamp": time.time(),
    }


@app.get("/api/provenance/{discovery_id}")
async def api_provenance_detail(discovery_id: str):
    """Get provenance records for a specific discovery/hypothesis."""
    from dataclasses import asdict
    records = engine.provenance_tracker.get_by_discovery(discovery_id)
    return {
        "discovery_id": discovery_id,
        "records": [asdict(r) for r in records],
        "count": len(records),
        "timestamp": time.time(),
    }


@app.get("/api/provenance/{discovery_id}/lineage")
async def api_provenance_lineage(discovery_id: str):
    """Get full lineage chain for a discovery."""
    from dataclasses import asdict
    lineage = engine.provenance_tracker.get_lineage(discovery_id)
    return {
        "discovery_id": discovery_id,
        "lineage": [asdict(r) for r in lineage],
        "chain_length": len(lineage),
        "timestamp": time.time(),
    }


@app.get("/api/export/discoveries.json")
async def api_export_discoveries_json(domain: str = None):
    """Export all discoveries as JSON with provenance."""
    return JSONResponse(
        content=json.loads(_exporter.export_discoveries_json(filter_domain=domain)),
        media_type="application/json",
    )


@app.get("/api/export/discoveries.csv")
async def api_export_discoveries_csv(domain: str = None):
    """Export all discoveries as CSV."""
    from fastapi.responses import PlainTextResponse
    csv_text = _exporter.export_discoveries_csv(filter_domain=domain)
    return PlainTextResponse(content=csv_text, media_type="text/csv")


@app.get("/api/export/hypothesis/{hypothesis_id}.tex")
async def api_export_hypothesis_latex(hypothesis_id: str):
    """Export a hypothesis as LaTeX for paper supplement."""
    from fastapi.responses import PlainTextResponse
    latex = _exporter.export_hypothesis_latex(hypothesis_id)
    if latex is None:
        return JSONResponse(
            status_code=404,
            content={"error": f"Hypothesis '{hypothesis_id}' not found"},
        )
    return PlainTextResponse(content=latex, media_type="application/x-tex")


@app.get("/api/export/full-report.json")
async def api_export_full_report():
    """Export complete ASTRA report — hypotheses, discoveries, provenance, engine state."""
    return JSONResponse(
        content=json.loads(_exporter.export_full_report_json()),
        media_type="application/json",
    )


# ── Stigmergy / Pheromone API ────────────────────────────────────────

@app.get("/api/pheromones/status")
async def api_pheromones_status():
    """Full stigmergy status — pheromone field, memory, metrics, A/B test."""
    return engine.stigmergy.get_status()


@app.get("/api/pheromones/hotspots")
async def api_pheromones_hotspots(pheromone_type: str = "success", top_k: int = 10):
    """Top-N pheromone hotspots for a given type."""
    return engine.stigmergy.get_hotspots(pheromone_type, top_k)


@app.post("/api/pheromones/gradient")
async def api_pheromones_gradient(request: Request):
    """Compute pheromone gradient at a domain location."""
    body = await request.json()
    domain = body.get("domain", "Astrophysics")
    ptype = body.get("pheromone_type", "success")
    return engine.stigmergy.compute_gradient(domain, ptype)


@app.get("/api/pheromones/deposits")
async def api_pheromones_deposits(limit: int = 50):
    """Recent pheromone deposit history."""
    return engine.stigmergy.get_recent_deposits(limit)


@app.get("/api/stigmergy/state")
async def api_stigmergy_state():
    """StigmergicMemory state — fields, trails, discoveries."""
    return engine.stigmergy.stigmergic_memory.get_state()


@app.post("/api/stigmergy/recommendations")
async def api_stigmergy_recommendations(request: Request):
    """Get swarm recommendations for a location/agent type."""
    body = await request.json()
    location = body.get("location", "astrophysics")
    agent_type = body.get("agent_type", "explorer")
    return engine.stigmergy.stigmergic_memory.get_swarm_recommendations(
        location, agent_type
    )


@app.get("/api/stigmergy/gaps")
async def api_stigmergy_gaps():
    """Knowledge gap analysis from pheromone coverage."""
    return engine.stigmergy.stigmergy_gaps()


@app.get("/api/pheromones/field")
async def api_pheromones_field():
    """Full pheromone field data for visualization."""
    return engine.stigmergy.get_field_data()


@app.get("/api/pheromones/ab-test")
async def api_pheromones_ab_test():
    """A/B test results — pheromone-guided vs baseline."""
    return engine.stigmergy.get_ab_summary()


@app.post("/api/pheromones/weight")
async def api_pheromones_weight(request: Request):
    """Adjust pheromone blending weight (0-1)."""
    body = await request.json()
    weight = body.get("weight", 0.3)
    new_weight = engine.stigmergy.set_weight(weight)
    return {"pheromone_weight": new_weight}


@app.get("/api/swarm/status")
async def api_swarm_status():
    """Swarm agent status — all 5 agent types."""
    return engine.swarm.get_swarm_summary()


@app.get("/api/stigmergy/exploration")
async def api_stigmergy_exploration(domain: str = "Astrophysics"):
    """Get pheromone-guided exploration direction for a domain."""
    return engine.stigmergy.get_exploration_direction(domain)


# ═══════════════════════════════════════════════════════════════
# ECCp-131 ECDLP Challenge Endpoints
# ═══════════════════════════════════════════════════════════════

try:
    from astra_live_backend.ecdlp_solver import (
        EllipticCurve, PollardRhoSolver,
        ECCP131, ECCP131_P, ECCP131_Q,
    )
    _ecdlp_available = True
    _ECCP131_PARAMS = {
        "q": ECCP131.q, "a": ECCP131.a, "b": ECCP131.b,
        "order": ECCP131.order,
        "Px": ECCP131_P[0], "Py": ECCP131_P[1],
        "Qx": ECCP131_Q[0], "Qy": ECCP131_Q[1],
    }
except Exception as _ecdlp_err:
    print(f"Warning: ecdlp_solver not available: {_ecdlp_err}")
    _ecdlp_available = False
    _ECCP131_PARAMS = {}

# Global solver state
_ecdlp_solver_state = {
    "running": False,
    "thread": None,
    "solver": None,
    "iterations": 0,
    "distinguished_points": 0,
    "hashrate": 0,
    "start_time": None,
    "last_benchmark": None,
}

@app.get("/api/ecdlp/status")
async def ecdlp_status():
    """Current ECCp-131 solver status"""
    state = _ecdlp_solver_state
    elapsed = 0
    if state["start_time"]:
        elapsed = time.time() - state["start_time"]
    return {
        "challenge": "ECCp-131",
        "prize": "$20,000 USD",
        "status": "running" if state["running"] else "idle",
        "iterations_completed": state["iterations"],
        "distinguished_points": state["distinguished_points"],
        "hashrate_ips": state["hashrate"],
        "elapsed_seconds": elapsed,
        "estimated_total_iterations": "2^65.4 ≈ 4.5 × 10^19",
        "estimated_years_single_thread": round(4.5e19 / max(state["hashrate"], 1) / 3.156e7, 1) if state["hashrate"] > 0 else None,
        "solved": False
    }

@app.get("/api/ecdlp/parameters")
async def ecdlp_parameters():
    """ECCp-131 challenge curve parameters"""
    if not _ecdlp_available:
        return {"error": "ecdlp_solver module not available"}
    p = _ECCP131_PARAMS
    return {
        "challenge": "ECCp-131 (Certicom ECC Challenge Level I)",
        "curve_type": "Weierstrass y² = x³ + ax + b over GF(q)",
        "field_prime_q": hex(p["q"]),
        "coefficient_a": hex(p["a"]),
        "coefficient_b": hex(p["b"]),
        "generator_P": {"x": hex(p["Px"]), "y": hex(p["Py"])},
        "target_Q": {"x": hex(p["Qx"]), "y": hex(p["Qy"])},
        "point_order": hex(p["order"]),
        "bit_length": 131,
        "security_level_bits": 65.5,
        "goal": "Find integer k such that Q = k·P",
        "source": "https://www.certicom.com/content/certicom/en/the-certicom-ecc-challenge.html"
    }

@app.get("/api/ecdlp/benchmark")
async def ecdlp_benchmark():
    """Run a quick benchmark on ECCp-131 curve"""
    if not _ecdlp_available:
        return {"error": "ecdlp_solver module not available"}
    P = ECCP131_P
    Q = ECCP131_Q

    import time as _time
    start = _time.time()
    R = P
    for i in range(10000):
        R = ECCP131.add(R, Q)  # EC point addition
    elapsed = _time.time() - start

    ips = 10000 / elapsed
    _ecdlp_solver_state["last_benchmark"] = ips
    _ecdlp_solver_state["hashrate"] = ips

    total_needed = 2**65.4
    years = total_needed / ips / 3.156e7

    return {
        "iterations": 10000,
        "elapsed_seconds": round(elapsed, 3),
        "iterations_per_second": round(ips, 1),
        "estimated_total_iterations": "2^65.4",
        "estimated_years_single_thread": round(years, 1),
        "estimated_years_1000_gpus": round(years / 50000, 2),
        "platform": "Python (pure, no C extensions)"
    }

@app.get("/api/ecdlp/approaches")
async def ecdlp_approaches():
    """Known approaches for solving ECCp-131"""
    return {
        "approaches": [
            {
                "name": "Pollard's Rho",
                "complexity": "O(√n) ≈ 2^65.5",
                "feasibility": "Feasible with ~$2-5M GPU compute",
                "status": "Implemented in ASTRA",
                "description": "Random walk on EC group with cycle detection. Best known generic algorithm."
            },
            {
                "name": "Pollard's Kangaroo",
                "complexity": "O(√n) for bounded range",
                "feasibility": "Same as Rho (full range search needed)",
                "status": "Not applicable (no range constraint)",
                "description": "Only useful when private key is known to lie in a small range."
            },
            {
                "name": "Baby-Step Giant-Step",
                "complexity": "O(√n) time and space",
                "feasibility": "Infeasible (2^65 memory entries needed)",
                "status": "Not practical",
                "description": "Deterministic but requires impossible amount of memory."
            },
            {
                "name": "Index Calculus (Summation Polynomials)",
                "complexity": "Subexponential (binary fields only)",
                "feasibility": "Not applicable to prime field curves",
                "status": "Research only",
                "description": "Semaev's approach works for characteristic-2 fields but not GF(p)."
            },
            {
                "name": "Shor's Algorithm (Quantum)",
                "complexity": "O(log³ n) ≈ polynomial",
                "feasibility": "Requires fault-tolerant quantum computer (10-20+ years)",
                "status": "Future technology",
                "description": "Would solve ECDLP trivially but requires ~500+ logical qubits."
            },
            {
                "name": "Weil Descent",
                "complexity": "Varies",
                "feasibility": "Only for extension field curves",
                "status": "Not applicable",
                "description": "Transfers ECDLP to hyperelliptic Jacobian. Not useful for prime fields."
            },
            {
                "name": "AI/ML-Guided Search",
                "complexity": "Unknown",
                "feasibility": "Speculative",
                "status": "Research direction",
                "description": "Use neural networks to optimize walk functions or predict distinguished points."
            }
        ]
    }


_ecdlp_analysis_cache = {}

@app.get("/api/ecdlp/analysis")
async def ecdlp_analysis():
    """Run mathematical structure analysis on ECCp-131 curve — checks for exploitable weaknesses (cached)."""
    if not _ecdlp_analysis_cache:
        try:
            from astra_live_backend.ecdlp_math import analyze_curve_structure
            _ecdlp_analysis_cache["result"] = analyze_curve_structure()
        except Exception as e:
            return {"error": str(e), "status": "analysis_failed"}
    return _ecdlp_analysis_cache["result"]


# ══════════════════════════════════════════════════════════════
# Theory Engine API  — Phases 1–3 Theoretical Framework
# ══════════════════════════════════════════════════════════════

@app.get("/api/theory/status")
async def theory_status():
    """Theory engine status — all phases."""
    return engine.theory_engine.status().to_dict()


@app.get("/api/theory/summary")
async def theory_summary():
    """Full theory engine state: theories, contradictions, analogies, experiments."""
    return engine.theory_engine.full_summary()


@app.get("/api/theory/theories")
async def get_theories():
    """All proposed and validated theoretical frameworks."""
    return {"theories": engine.theory_engine.get_theories()}


@app.post("/api/theory/cycle")
async def run_theory_cycle():
    """Trigger an immediate synchronous theory engine cycle."""
    result = engine.theory_engine.run_cycle_sync(engine.store)
    return result


# ── Phase 1 ──────────────────────────────────────────────────

@app.get("/api/theory/contradictions")
async def get_contradictions():
    """All detected contradictions in the hypothesis store."""
    return {
        "contradictions": engine.theory_engine.get_contradictions(),
        "unresolved": sum(
            1 for c in engine.theory_engine.get_contradictions()
            if not c.get("resolved", False)
        )
    }


@app.post("/api/theory/contradictions/{cid}/resolve")
async def resolve_contradiction(cid: str):
    """Mark a contradiction as resolved."""
    ok = engine.theory_engine.resolve_contradiction(cid)
    return {"resolved": ok, "contradiction_id": cid}


@app.get("/api/theory/dimensional/exponent/{value}")
async def match_universal_exponent(value: float):
    """Check if an observed exponent matches a known universal value."""
    try:
        from astra_live_backend.symbolic_dimensional import UniversalExponentMatcher
        matcher = UniversalExponentMatcher()
        match = matcher.find_nearest(value)
        return match if match else {"match": None, "value": value}
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/theory/dimensional/generate")
async def generate_scaling_relations(body: dict):
    """
    Generate candidate scaling relations from dimensional analysis.
    Body: {"variables": {"mass": "mass", "velocity": "velocity", ...}}
    """
    try:
        from astra_live_backend.symbolic_dimensional import CandidateEquationSet
        variables = body.get("variables", {})
        eq_set = CandidateEquationSet()
        candidates = eq_set.generate_from_variables(variables)
        return {"candidates": [c.to_dict() if hasattr(c, 'to_dict') else c
                               for c in candidates]}
    except Exception as e:
        return {"error": str(e)}


# ── Phase 2 ──────────────────────────────────────────────────

@app.get("/api/theory/analogies")
async def get_analogies():
    """All detected cross-domain structural analogies."""
    analogies = engine.theory_engine.get_analogies()
    return {
        "analogies": analogies,
        "novel_count": sum(1 for a in analogies if a.get("novel", False))
    }


@app.get("/api/theory/symmetries")
async def get_symmetry_findings():
    """All detected symmetries and universal behaviour."""
    return {"symmetry_findings": engine.theory_engine.get_symmetry_findings()}


# ── Phase 3 ──────────────────────────────────────────────────

@app.get("/api/theory/abduction")
async def get_abductive_explanations():
    """All abductive explanations for anomalous validated results."""
    explanations = engine.theory_engine.get_abductive_explanations()
    return {
        "explanations": explanations,
        "count": len(explanations)
    }


@app.get("/api/theory/experiments")
async def get_critical_experiments():
    """Prioritised list of critical discriminating experiments."""
    experiments = engine.theory_engine.get_critical_experiments()
    return {
        "experiments": experiments,
        "count": len(experiments),
        "high_value": sum(1 for e in experiments
                          if e.get("scientific_value", 0) > 0.6)
    }


@app.get("/api/theory/consistency")
async def get_consistency_reports():
    """Self-consistency check results for all active theories."""
    return {"reports": engine.theory_engine.get_consistency_reports()}


# ═══════════════════════════════════════════════════════════════
# Phase 15: Cognitive Architecture Endpoints (Scientific AGI)
# ═══════════════════════════════════════════════════════════════

@app.get("/api/cognitive/status")
async def api_cognitive_status():
    """Cognitive architecture status and capabilities."""
    if not engine.cognitive_core:
        return {"enabled": False, "message": "Cognitive architecture not available"}

    summary = engine.cognitive_core.get_cognitive_summary()

    return {
        "enabled": True,
        "cognitive_mode": summary.get("cognitive_mode"),
        "perceptions": summary.get("perceptions", 0),
        "insights": summary.get("insights", 0),
        "discoveries": summary.get("discoveries", 0),
        "knowledge_graph": summary.get("knowledge_graph_stats", {}),
        "neuro_symbolic": summary.get("neuro_symbolic_stats", {}),
        "metacognition": summary.get("metacognitive_report", {})
    }


@app.get("/api/knowledge-graph/statistics")
async def api_knowledge_graph_stats():
    """Knowledge graph statistics: entities, relations, gaps."""
    if not engine.cognitive_core:
        return {"error": "Cognitive core not available"}

    stats = engine.cognitive_core.knowledge_graph.get_statistics()

    return {
        "statistics": stats,
        "total_entities": stats.get("total_entities", 0),
        "total_relations": stats.get("total_relations", 0),
        "knowledge_gaps": stats.get("knowledge_gaps", 0),
        "domains": stats.get("domains", {}),
        "graph_density": stats.get("graph_density", 0)
    }


@app.get("/api/knowledge-graph/gaps")
async def api_knowledge_graph_gaps():
    """Get current knowledge gaps identified by the knowledge graph."""
    if not engine.cognitive_core:
        return {"error": "Cognitive core not available"}

    gaps = engine.cognitive_core.knowledge_graph.find_knowledge_gaps()

    # Return top 10 gaps by priority
    top_gaps = sorted(gaps, key=lambda g: g.priority, reverse=True)[:10]

    return {
        "total_gaps": len(gaps),
        "high_priority_gaps": len([g for g in gaps if g.priority > 0.7]),
        "top_gaps": [
            {
                "gap_type": g.gap_type,
                "description": g.description,
                "priority": g.priority,
                "suggestions": g.suggestions
            }
            for g in top_gaps
        ]
    }


@app.get("/api/knowledge-graph/analogies")
async def api_knowledge_graph_analogies():
    """Get cross-domain analogies discovered by the knowledge graph."""
    if not engine.cognitive_core:
        return {"error": "Cognitive core not available"}

    analogies = engine.cognitive_core.knowledge_graph.find_cross_domain_analogies()

    return {
        "total_analogies": len(analogies),
        "analogies": [
            {
                "domain1": a["domain1"],
                "domain2": a["domain2"],
                "entity1": a["entity1"],
                "entity2": a["entity2"],
                "similarity": a["similarity"],
                "shared_properties": a["shared_properties"]
            }
            for a in analogies[:10]  # Top 10
        ]
    }


@app.get("/api/metacognition/report")
async def api_metacognition_report():
    """Get meta-cognitive self-awareness report."""
    if not engine.cognitive_core:
        return {"error": "Cognitive core not available"}

    report = engine.cognitive_core.metacognition.get_self_awareness_report()

    return {
        "cognitive_state": report.get("cognitive_state"),
        "total_traces": report.get("total_traces", 0),
        "recent_success_rate": report.get("recent_success_rate", 0),
        "error_patterns": report.get("error_patterns_detected", 0),
        "methods_tracked": report.get("methods_tracked", 0),
        "top_errors": report.get("top_error_patterns", []),
        "best_methods": report.get("best_methods", [])
    }


@app.post("/api/cognitive/discover")
async def api_cognitive_discover(request: Request):
    """
    Run cognitive discovery on provided data.

    Expected body:
    {
        "data": [[...]],  # Numerical data array
        "features": {"feature1": [...], "feature2": [...]},
        "data_type": "numerical"
    }
    """
    if not engine.cognitive_core:
        return {"error": "Cognitive core not available"}

    body = await request.json()

    data = np.array(body.get("data", []))
    features = body.get("features", {})
    data_type = body.get("data_type", "numerical")

    discovery = engine.cognitive_core.discover(data, data_type, features)

    if discovery:
        return {
            "discovery_id": discovery.discovery_id,
            "title": discovery.title,
            "confidence": discovery.confidence,
            "significance": discovery.significance,
            "novelty": discovery.novelty,
            "explanation": discovery.explanation,
            "next_steps": discovery.next_steps
        }

    return {"error": "No discovery generated"}


@app.get("/api/cognitive/discoveries")
async def api_cognitive_discoveries():
    """Get recent cognitive discoveries."""
    if not engine.cognitive_core:
        return {"error": "Cognitive core not available"}

    discoveries = engine.cognitive_core.discoveries[-10:]  # Last 10

    return {
        "total_discoveries": len(engine.cognitive_core.discoveries),
        "recent_discoveries": [
            {
                "id": d.discovery_id,
                "title": d.title,
                "type": d.discovery_type,
                "confidence": d.confidence,
                "significance": d.significance,
                "novelty": d.novelty,
                "explanation": d.explanation[:200] + "..." if len(d.explanation) > 200 else d.explanation
            }
            for d in discoveries
        ]
    }


@app.get("/api/cognitive/explain/{discovery_id}")
async def api_cognitive_explain(discovery_id: str, audience: str = "expert"):
    """
    Get explanation for a cognitive discovery at different audience levels.

    Audience levels: expert, student, public
    """
    if not engine.cognitive_core:
        return {"error": "Cognitive core not available"}

    try:
        explanation = engine.cognitive_core.explain_discovery(
            int(discovery_id) if discovery_id.isdigit() else discovery_id,
            audience_level=audience
        )

        if explanation:
            return explanation

        return {"error": "Discovery not found"}
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/cognitive/reflect")
async def api_cognitive_reflect():
    """Trigger meta-cognitive reflection and self-improvement."""
    if not engine.cognitive_core:
        return {"error": "Cognitive core not available"}

    reflection = engine.cognitive_core.reflect()

    if reflection and reflection.get("reflection"):
        refl = reflection["reflection"]

        return {
            "timestamp": refl.timestamp,
            "insights": refl.insights,
            "improvements": refl.improvements,
            "strategy_changes": refl.strategy_changes,
            "cognitive_state": reflection.get("cognitive_state"),
            "knowledge_gaps_found": len(reflection.get("knowledge_gaps", []))
        }

    return {"error": "Reflection failed"}


@app.post("/api/cognitive/integrate-theory-data")
async def api_cognitive_integrate(request: Request):
    """
    Integrate theoretical description with empirical data validation.

    Expected body:
    {
        "theory_description": "Entropic gravity predicts MOND-like behavior",
        "data": [[...]]  # Observational data
    }
    """
    if not engine.cognitive_core:
        return {"error": "Cognitive core not available"}

    body = await request.json()

    theory_description = body.get("theory_description", "")
    data = np.array(body.get("data", []))

    result = engine.cognitive_core.unify_theory_and_data(theory_description, data)

    return result


@app.get("/api/state/persistence")
async def api_state_persistence():
    """Get state persistence status and summary."""
    from astra_live_backend.state_persistence import get_state_summary

    summary = get_state_summary()

    return {
        "persistence_enabled": True,
        "state_dir_exists": summary.get("state_dir_exists"),
        "engine_state_saved": summary.get("engine_state_exists"),
        "hypotheses_saved": summary.get("hypotheses_exist"),
        "cognitive_state_saved": summary.get("cognitive_state_exists"),
        "last_saved": summary.get("last_saved"),
        "cycle_count": summary.get("cycle_count"),
        "hypotheses_count": summary.get("hypotheses_count", 0),
        "active_hypotheses": summary.get("active_hypotheses", 0)
    }


@app.post("/api/state/save")
async def api_state_save():
    """Manually trigger state save."""
    from astra_live_backend.state_persistence import save_engine_state, save_hypotheses, save_cognitive_state

    try:
        save_engine_state(engine)
        save_hypotheses(engine.store)
        if engine.cognitive_core:
            save_cognitive_state(engine.cognitive_core)

        return {
            "success": True,
            "message": "State saved successfully",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/cognitive/dashboard")
async def api_cognitive_dashboard():
    """
    Get comprehensive cognitive dashboard data.

    Combines all cognitive systems into a unified view.
    """
    if not engine.cognitive_core:
        return {"enabled": False, "message": "Cognitive architecture not available"}

    summary = engine.cognitive_core.get_cognitive_summary()

    # Get additional details
    kg_stats = engine.cognitive_core.knowledge_graph.get_statistics()
    meta_report = engine.cognitive_core.metacognition.get_self_awareness_report()
    gaps = engine.cognitive_core.knowledge_graph.find_knowledge_gaps()

    return {
        "enabled": True,
        "summary": summary,
        "knowledge_graph": {
            "statistics": kg_stats,
            "gaps_count": len(gaps),
            "high_priority_gaps": len([g for g in gaps if g.priority > 0.7])
        },
        "metacognition": {
            "cognitive_state": meta_report.get("cognitive_state"),
            "success_rate": meta_report.get("recent_success_rate", 0),
            "error_patterns": meta_report.get("error_patterns_detected", 0)
        },
        "recent_discoveries": len(engine.cognitive_core.discoveries),
        "total_insights": len(engine.cognitive_core.insights)
    }


# ── V9.0: Multi-Agent Scientific Collaboration ─────────────────────

@app.get("/api/agents/status")
async def api_agents_status():
    """
    Get status of multi-agent collaboration system (V9.0).
    """
    if not engine.multi_agent_orchestrator:
        return {"enabled": False, "message": "Multi-agent system not initialized"}

    orchestrator = engine.multi_agent_orchestrator
    metrics = orchestrator.metrics.get_summary() if hasattr(orchestrator, 'metrics') else {}

    return {
        "enabled": True,
        "registered_agents": len(orchestrator.agent_registry),
        "active_debates": len(orchestrator.active_debates),
        "debate_history": len(orchestrator.debate_history),
        "metrics": metrics
    }


@app.post("/api/agents/create")
async def api_agents_create(request: Request):
    """
    Create specialized agents for collaboration (V9.0).

    Body:
        roles: List[str] - Agent roles to create (theorist, empiricist, etc.)
        count: int - Number of agents per role
    """
    if not engine.multi_agent_orchestrator:
        return {"success": False, "error": "Multi-agent system not initialized"}

    data = await request.json()
    roles = data.get("roles", ["theorist", "empiricist", "synthesizer"])
    count = data.get("count", 1)

    from astra_live_backend.multi_agent import AgentFactory, AgentRole

    role_map = {
        "theorist": AgentRole.THEORIST,
        "empiricist": AgentRole.EMPIRICIST,
        "experimentalist": AgentRole.EXPERIMENTALIST,
        "mathematician": AgentRole.MATHEMATICIAN,
        "skeptic": AgentRole.SKEPTIC,
        "synthesizer": AgentRole.SYNTHESIZER
    }

    created_agents = []
    for role_name in roles:
        role = role_map.get(role_name)
        if role:
            for _ in range(count):
                agent = AgentFactory.create_agent(role)
                engine.multi_agent_orchestrator.register_agent(agent)
                created_agents.append({
                    "id": agent.id,
                    "role": role.value,
                    "domains": agent.expertise.domains
                })

    return {
        "success": True,
        "created_agents": created_agents,
        "total_agents": len(engine.multi_agent_orchestrator.agent_registry)
    }


@app.get("/api/agents/consensus")
async def api_agents_consensus(question: str = None):
    """
    Get consensus from multi-agent system on a question (V9.0).

    Query parameters:
        question: The scientific question to analyze
        method: Consensus method (majority_vote, weighted_vote, etc.)
    """
    if not engine.multi_agent_orchestrator:
        return {"consensus": None, "error": "Multi-agent system not initialized"}

    if not question:
        return {"consensus": None, "error": "Question parameter required"}

    # Get all agents
    agents = list(engine.multi_agent_orchestrator.agent_registry.values())
    if not agents:
        return {"consensus": None, "error": "No agents available"}

    # Collect opinions
    opinions = []
    for agent in agents:
        try:
            opinion = agent.analyze(question, {})
            opinions.append(opinion)
        except Exception as e:
            # Continue with other agents
            pass

    # Compute consensus
    from astra_live_backend.multi_agent import ConsensusEngine

    consensus_engine = ConsensusEngine()
    consensus = consensus_engine.compute_consensus(opinions)

    return {
        "question": question,
        "consensus": consensus.to_dict(),
        "opinions_count": len(opinions),
        "agents_participated": len(opinions)
    }


@app.post("/api/agents/debate")
async def api_agents_debate(request: Request):
    """
    Start or advance a structured scientific debate (V9.0).

    Body:
        question: str - Research question to debate
        participants: List[str] - Agent IDs to participate
        action: str - "start", "advance", or "conclude"
        debate_id: str - Required for advance/conclude
    """
    if not engine.multi_agent_orchestrator:
        return {"success": False, "error": "Multi-agent system not initialized"}

    data = await request.json()
    action = data.get("action", "start")

    if action == "start":
        question = data.get("question")
        participants = data.get("participants", [])

        if not question:
            return {"success": False, "error": "Question required"}

        # Use all agents if no participants specified
        if not participants:
            participants = list(engine.multi_agent_orchestrator.agent_registry.keys())

        debate_id = engine.multi_agent_orchestrator.start_debate(question, participants)

        return {
            "success": True,
            "debate_id": debate_id,
            "question": question,
            "participants": participants
        }

    elif action == "advance":
        debate_id = data.get("debate_id")
        if not debate_id:
            return {"success": False, "error": "debate_id required"}

        new_phase = engine.multi_agent_orchestrator.advance_debate(debate_id)

        return {
            "success": True,
            "debate_id": debate_id,
            "current_phase": new_phase
        }

    elif action == "conclude":
        debate_id = data.get("debate_id")
        if not debate_id:
            return {"success": False, "error": "debate_id required"}

        result = engine.multi_agent_orchestrator.conclude_debate(debate_id)

        if result:
            return {
                "success": True,
                "debate_id": debate_id,
                "result": {
                    "consensus_reached": result.final_consensus.consensus_reached,
                    "consensus_position": result.final_consensus.consensus_position,
                    "agreement_level": result.final_consensus.agreement_level,
                    "recommendation": result.recommendation,
                    "key_insights": result.key_insights
                }
            }
        else:
            return {"success": False, "error": "Debate not found"}

    else:
        return {"success": False, "error": f"Unknown action: {action}"}


# ── V9.0: Autonomous Scientific Agenda ───────────────────────────────

@app.get("/api/agenda/status")
async def api_agenda_status():
    """
    Get status of autonomous scientific agenda (V9.0).
    """
    if not engine.autonomous_agenda:
        return {"enabled": False, "message": "Autonomous agenda not initialized"}

    summary = engine.autonomous_agenda.get_agenda_summary()

    return {
        "enabled": True,
        "mode": engine.autonomous_agenda.mode,
        **summary
    }


@app.get("/api/agenda/goals")
async def api_agenda_goals():
    """
    Get current research goals.
    """
    if not engine.autonomous_agenda:
        return {"goals": [], "error": "Autonomous agenda not initialized"}

    goals = engine.autonomous_agenda.current_goals

    return {
        "goals": [g.to_dict() for g in goals],
        "total": len(goals)
    }


@app.post("/api/agenda/generate")
async def api_agenda_generate(request: Request):
    """
    Generate new research goals based on knowledge gaps (V9.0).

    Body:
        num_goals: int - Number of goals to generate (default: 5)
        time_horizon: str - "short", "medium", or "long"
    """
    if not engine.autonomous_agenda:
        return {"success": False, "error": "Autonomous agenda not initialized"}

    data = await request.json()
    num_goals = data.get("num_goals", 5)
    time_horizon = data.get("time_horizon", "medium")

    goals = engine.autonomous_agenda.generate_research_agenda(
        num_goals=num_goals,
        time_horizon=time_horizon
    )

    return {
        "success": True,
        "goals_generated": len(goals),
        "goals": [g.to_dict() for g in goals]
    }


@app.post("/api/agenda/approve")
async def api_agenda_approve(request: Request):
    """
    Approve or reject a proposed research goal (V9.0).

    Body:
        goal_id: str - ID of goal to approve/reject
        approved: bool - True to approve, False to reject
        feedback: str - Optional feedback for rejection
    """
    if not engine.autonomous_agenda:
        return {"success": False, "error": "Autonomous agenda not initialized"}

    data = await request.json()
    goal_id = data.get("goal_id")
    approved = data.get("approved", False)
    feedback = data.get("feedback", "")

    # Find goal
    goal = None
    for g in engine.autonomous_agenda.current_goals:
        if g.id == goal_id:
            goal = g
            break

    if not goal:
        return {"success": False, "error": f"Goal {goal_id} not found"}

    # Update goal status
    if approved:
        goal.status = "approved"  # String to match JSON serialization
        goal.approved_by = "human"
    else:
        goal.status = "cancelled"

    return {
        "success": True,
        "goal_id": goal_id,
        "new_status": goal.status,
        "feedback_recorded": bool(feedback)
    }


# ── Conformal Prediction Endpoints (Optional Enhancement) ────────
# Monte Carlo Conformal Prediction for ML uncertainty quantification.
# This is an OPTIONAL module for ML-assisted discovery workflows.
# Requires: numpy, scipy (included), optionally sklearn for models.

# Try importing conformal module
CONFORMAL_IMPORT_ERROR = None
try:
    from astra_live_backend.conformal import (
        ConformalDiscovery,
        ConformalEngine,
        ConformalMethod,
        HAS_CONFORMAL as CONFORMAL_LIB_AVAILABLE,
    )
    CONFORMAL_AVAILABLE = True
except ImportError as e:
    CONFORMAL_AVAILABLE = False
    CONFORMAL_IMPORT_ERROR = str(e)


@app.get("/api/conformal/status")
def api_conformal_status():
    """
    Check if conformal prediction module is available.

    Returns:
        - available: bool - Whether conformal prediction is enabled
        - external_lib: bool - Whether external conformal library is installed
        - mode: str - "full", "numpy_only", or "unavailable"
    """
    if not CONFORMAL_AVAILABLE:
        return {
            "available": False,
            "external_lib": False,
            "mode": "unavailable",
            "error": "conformal module not found",
            "note": "Install with: pip install conformal-prediction OR pip install mapie"
        }

    mode = "full" if CONFORMAL_LIB_AVAILABLE else "numpy_only"
    return {
        "available": True,
        "external_lib": CONFORMAL_LIB_AVAILABLE,
        "mode": mode,
        "supported_tasks": ["regression", "classification"],
        "documentation": "Use POST /api/conformal/calibrate to calibrate a model"
    }


@app.post("/api/conformal/calibrate")
async def api_conformal_calibrate(request: Request):
    """
    Calibrate an ML model with conformal prediction intervals.

    This endpoint provides uncertainty quantification for ML predictions,
    useful for ML-assisted discovery workflows (e.g., candidate selection
    from large astronomical surveys).

    Body:
        - X: list[list] - Feature matrix (2D array)
        - y: list - Target values (regression) or labels (classification)
        - model_type: str - "linear_regression", "logistic_regression",
                         "random_forest", "gradient_boosting", or "custom"
        - task: str - "regression" or "classification" (auto-detected if None)
        - confidence: float - Target coverage (default: 0.90)
        - test_size: float - Fraction for calibration set (default: 0.2)

    Returns:
        - summary: Calibration summary including empirical coverage
        - model_metrics: RMSE, accuracy, etc.
        - conformal_id: ID for subsequent predictions
        - warning: If coverage is significantly off target
    """
    if not CONFORMAL_AVAILABLE:
        return JSONResponse(
            status_code=503,
            content={
                "success": False,
                "error": "Conformal prediction module not available",
                "note": "Optional module - install dependencies if needed"
            }
        )

    try:
        data = await request.json()
        X = np.array(data.get("X", []))
        y = np.array(data.get("y", []))
        model_type = data.get("model_type", "linear_regression")
        task = data.get("task")  # None = auto-detect
        confidence = data.get("confidence", 0.90)
        test_size = data.get("test_size", 0.2)

        # Validate inputs
        if X.size == 0 or y.size == 0:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "X and y cannot be empty"}
            )

        if len(X) != len(y):
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "X and y must have same length"}
            )

        if not 0.5 <= confidence <= 0.999:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "confidence must be in [0.5, 0.999]"}
            )

        # Auto-detect task if not specified
        if task is None:
            # Classification: few unique values (< 20% of samples)
            n_unique = len(np.unique(y))
            task = "classification" if n_unique < max(10, len(y) * 0.2) else "regression"

        # Import sklearn if available
        try:
            from sklearn.linear_model import LinearRegression, LogisticRegression
            from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
            from sklearn.model_selection import train_test_split
            HAS_SKLEARN_CONFORMAL = True
        except ImportError:
            HAS_SKLEARN_CONFORMAL = False
            return JSONResponse(
                status_code=503,
                content={
                    "success": False,
                    "error": "scikit-learn required for model training",
                    "note": "Install with: pip install scikit-learn"
                }
            )

        # Create model based on type and task
        model_map = {
            "linear_regression": (LinearRegression, "regression"),
            "logistic_regression": (LogisticRegression, "classification"),
            "random_forest": (RandomForestRegressor, "regression"),
            "gradient_boosting": (RandomForestRegressor, "regression"),
        }

        if model_type == "custom":
            # User will provide pre-trained model (not implemented in this endpoint)
            return JSONResponse(
                status_code=501,
                content={
                    "success": False,
                    "error": "Custom models not supported via API. "
                            "Use ConformalDiscovery class directly in Python."
                }
            )

        # Select model class
        if task == "classification":
            if model_type == "random_forest":
                ModelClass = RandomForestClassifier
            elif model_type == "linear_regression":
                ModelClass = LogisticRegression
            else:
                ModelClass = LogisticRegression
        else:  # regression
            if model_type == "logistic_regression":
                ModelClass = LinearRegression  # Fallback
            else:
                ModelClass, _ = model_map.get(model_type, (LinearRegression, "regression"))

        # Train model and calibrate
        model = ModelClass(random_state=42)
        discover = ConformalDiscovery()
        result = discover.calibrate_ml_discovery(
            model=model,
            X=X,
            y=y,
            test_size=test_size,
            confidence=confidence,
        )

        # Format response
        conformal_id = f"conf-{time.time():.0f}"
        summary = result["summary"]

        response = {
            "success": True,
            "conformal_id": conformal_id,
            "summary": {
                "task_type": summary["task_type"],
                "target_coverage": summary["target_coverage"],
                "empirical_coverage": summary["empirical_coverage"],
                "coverage_error": summary["coverage_error"],
                "is_well_calibrated": summary["is_well_calibrated"],
            },
            "model_metrics": {},
            "warning": None,
        }

        # Add task-specific metrics
        if summary["task_type"] == "regression":
            response["model_metrics"] = {
                "rmse": summary.get("rmse"),
                "mean_interval_width": summary.get("mean_interval_width"),
            }
        else:
            response["model_metrics"] = {
                "accuracy": summary.get("accuracy"),
                "mean_set_size": summary.get("mean_set_size"),
            }

        # Warning if coverage is off
        if not summary["is_well_calibrated"]:
            response["warning"] = (
                f"Empirical coverage ({summary['empirical_coverage']:.3f}) "
                f"differs significantly from target ({summary['target_coverage']:.3f}). "
                f"This may indicate model misspecification or data shift."
            )

        return response

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@app.post("/api/conformal/predict")
async def api_conformal_predict(request: Request):
    """
    Make predictions with conformal uncertainty intervals.

    Note: This is a simplified endpoint. For production use with
    pre-trained models, use the ConformalEngine class directly.

    Body:
        - X: list[list] - Feature matrix for predictions
        - conformal_id: str - ID from previous calibration (not yet implemented)
        - confidence: float - Target coverage

    Returns:
        - predictions: list - Point predictions
        - lower_bound: list - Lower confidence bounds
        - upper_bound: list - Upper confidence bounds
        - interval_width: list - Width of each interval
        - mean_interval_width: float - Average interval width
    """
    if not CONFORMAL_AVAILABLE:
        return JSONResponse(
            status_code=503,
            content={"success": False, "error": "Conformal module not available"}
        )

    try:
        data = await request.json()
        X = np.array(data.get("X", []))
        confidence = data.get("confidence", 0.90)

        if X.size == 0:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "X cannot be empty"}
            )

        # Simplified: return mock predictions with uncertainty
        # Real implementation would use stored calibrated model
        n_samples = len(X)
        predictions = np.random.randn(n_samples)
        interval_width = 2.0  # Mock width
        lower = predictions - interval_width / 2
        upper = predictions + interval_width / 2

        return {
            "success": True,
            "predictions": predictions.tolist(),
            "lower_bound": lower.tolist(),
            "upper_bound": upper.tolist(),
            "interval_width": [interval_width] * n_samples,
            "mean_interval_width": interval_width,
            "confidence": confidence,
            "note": "This is a simplified endpoint. "
                    "For production use, import ConformalEngine directly."
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@app.get("/api/conformal/history")
def api_conformal_history():
    """
    Get summary of all conformal calibration runs in this session.

    Returns:
        - n_runs: int - Number of calibrations performed
        - mean_coverage_error: float - Average deviation from target
        - well_calibrated_count: int - Number of well-calibrated models
    """
    if not CONFORMAL_AVAILABLE:
        return JSONResponse(
            status_code=503,
            content={"success": False, "error": "Conformal module not available"}
        )

    try:
        discover = ConformalDiscovery()
        summary = discover.uncertainty_summary()

        return {
            "success": True,
            **summary
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@app.post("/api/conformal/out-of-distribution")
async def api_conformal_ood(request: Request):
    """
    Detect out-of-distribution samples using conformal prediction.

    OOD samples have prediction intervals significantly wider than reference,
    indicating the model is extrapolating beyond its training distribution.

    Body:
        - X: list[list] - New samples to evaluate
        - reference_scores: list - Non-conformity scores from calibration
        - threshold_multiplier: float - OOD threshold multiplier (default: 2.0)

    Returns:
        - is_out_of_distribution: list[bool] - OOD flag for each sample
        - n_ood: int - Number of OOD samples detected
        - ood_fraction: float - Fraction of samples that are OOD
    """
    if not CONFORMAL_AVAILABLE:
        return JSONResponse(
            status_code=503,
            content={"success": False, "error": "Conformal module not available"}
        )

    try:
        data = await request.json()
        X = np.array(data.get("X", []))
        reference_scores = np.array(data.get("reference_scores", []))
        threshold_multiplier = data.get("threshold_multiplier", 2.0)

        if X.size == 0 or reference_scores.size == 0:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "X and reference_scores required"}
            )

        # Mock model for OOD detection
        class MockModel:
            def predict(self, X):
                return np.mean(X, axis=1) if X.ndim > 1 else X

        mock_model = MockModel()
        discover = ConformalDiscovery()
        result = discover.detect_out_of_distribution(
            model=mock_model,
            X_new=X,
            reference_scores=reference_scores,
            threshold_multiplier=threshold_multiplier,
        )

        return {
            "success": True,
            **result
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


# ══════════════════════════════════════════════════════════════
# GraphPalace Connections API  — Cross-Domain Discovery Network
# ══════════════════════════════════════════════════════════════

@app.get("/api/connections/network")
async def get_connections_network():
    """
    Get cross-domain discovery network visualization data.

    Returns:
        - nodes: List of domain/topic nodes
        - links: List of connections between nodes
    """
    try:
        if not hasattr(engine, 'discovery_memory'):
            return {"nodes": [], "links": []}

        memory = engine.discovery_memory

        # Check if GraphPalace is available
        if not hasattr(memory, 'palace'):
            return {"nodes": [], "links": []}

        # Get domain statistics
        hot_domains = memory.get_hot_domains(top_n=10)

        # Create nodes
        nodes = []
        node_id = 0
        domain_node_map = {}

        for domain, score in hot_domains:
            node_id_str = f"domain_{domain}"
            nodes.append({
                "id": node_id_str,
                "label": domain,
                "domain": domain,
                "discoveries": int(score * 10),  # Approximate
                "type": "domain"
            })
            domain_node_map[domain] = node_id_str
            node_id += 1

        # Add finding type nodes
        finding_types = set()
        for disc in memory.discoveries:
            finding_types.add(disc.finding_type)

        for ftype in finding_types:
            nodes.append({
                "id": f"type_{ftype}",
                "label": ftype,
                "domain": "general",
                "discoveries": sum(1 for d in memory.discoveries if d.finding_type == ftype),
                "type": "finding_type"
            })
            node_id += 1

        # Create links (cross-domain connections)
        links = []
        domains = list(domain_node_map.keys())

        for i, domain1 in enumerate(domains):
            for domain2 in domains[i+1:]:
                try:
                    connections = memory.find_cross_domain_connections(domain1, domain2, k=2)

                    for conn in connections:
                        strength = conn.get("confidence", 0.5)
                        links.append({
                            "source": domain_node_map[domain1],
                            "target": domain_node_map[domain2],
                            "strength": strength,
                            "topic": conn.get("topic", ""),
                            "type": "cross_domain"
                        })
                except Exception:
                    pass

        return {
            "nodes": nodes,
            "links": links
        }

    except Exception as e:
        return {"nodes": [], "links": [], "error": str(e)}


@app.get("/api/connections/domains")
async def get_connections_domains():
    """
    Get domain statistics for cross-domain analysis.

    Shows data sources as domains for better granularity.

    Returns:
        - domains: List of domain statistics
    """
    try:
        if not hasattr(engine, 'discovery_memory'):
            return {"domains": []}

        memory = engine.discovery_memory

        # Build domain statistics from data sources
        domain_stats = {}

        for disc in memory.discoveries:
            # Use data_source as domain for better granularity
            domain = getattr(disc, 'data_source', disc.domain)

            if domain not in domain_stats:
                domain_stats[domain] = {
                    "discoveries": [],
                    "types": set(),
                    "momentum": 0
                }

            domain_stats[domain]["discoveries"].append(disc)
            domain_stats[domain]["types"].add(disc.finding_type)
            domain_stats[domain]["momentum"] += disc.strength

        # Build domain list with statistics
        domains = []
        for domain, stats in domain_stats.items():
            discoveries = stats["discoveries"]
            types = list(stats["types"])

            # Count connections to other domains
            connections = 0
            if hasattr(memory, 'palace') and memory.palace:
                try:
                    for other_domain in domain_stats:
                        if other_domain != domain:
                            cross = memory.find_cross_domain_connections(domain, other_domain, k=1)
                            connections += len(cross)
                except Exception:
                    pass

            # Only include domains with at least 1 discovery
            if len(discoveries) > 0:
                domains.append({
                    "name": domain,
                    "discoveries": len(discoveries),
                    "types": types,
                    "connections": connections,
                    "momentum": round(stats["momentum"], 2),
                    "strength": round(sum(d.strength for d in discoveries) / len(discoveries), 3) if discoveries else 0
                })

        # Sort by discovery count (most active first)
        domains.sort(key=lambda x: -x["discoveries"])

        return {"domains": domains[:15]}  # Top 15 domains

    except Exception as e:
        logger.error(f"Error getting domain statistics: {e}")
        return {"domains": [], "error": str(e)}


@app.get("/api/connections/cross-domain")
async def get_cross_domain_discoveries():
    """
    Get discoveries that span multiple domains with diversity filtering.

    Returns:
        - discoveries: List of cross-domain discoveries with improved diversity
    """
    try:
        if not hasattr(engine, 'discovery_memory'):
            return {"discoveries": []}

        memory = engine.discovery_memory

        # Find discoveries with cross-domain potential
        cross_discoveries = []
        seen_discovery_types = {}  # Track discovery types to ensure diversity

        for disc in memory.discoveries:
            if disc.strength > 0.6:  # Only strong discoveries
                cross_domains = []

                # Check if variables appear in other domains
                for var in disc.variables:
                    for other_disc in memory.discoveries:
                        if (other_disc.id != disc.id and
                            var in other_disc.variables and
                            other_disc.domain != disc.domain):
                            if other_disc.domain not in cross_domains:
                                cross_domains.append(other_disc.domain)

                if cross_domains:
                    # Create discovery type key for diversity tracking
                    # Combine finding type, description pattern, and variable count
                    discovery_type = (
                        disc.finding_type,
                        disc.description.split(':')[0] if ':' in disc.description else disc.description[:30],
                        len(disc.variables)
                    )

                    # Limit number of discoveries per type to ensure diversity
                    type_count = seen_discovery_types.get(discovery_type, 0)
                    if type_count < 3:  # Max 3 per discovery type
                        seen_discovery_types[discovery_type] = type_count + 1

                        cross_discoveries.append({
                            "id": disc.id,
                            "domain": disc.domain,
                            "data_source": getattr(disc, 'data_source', disc.domain),
                            "finding_type": disc.finding_type,
                            "description": disc.description,
                            "strength": disc.strength,
                            "variables": disc.variables,
                            "cross_domains": cross_domains[:3],  # Top 3
                            "unique_id": f"{disc.id}_{disc.finding_type}_{len(disc.variables)}"  # For deduplication
                        })

        # Sort by strength and data source diversity
        cross_discoveries.sort(key=lambda x: (
            -x["strength"],  # Higher strength first
            x["data_source"]  # Then by data source for diversity
        ))

        # Final deduplication - ensure unique entries only
        seen_unique = set()
        diverse_discoveries = []
        for disc in cross_discoveries:
            unique_key = disc["unique_id"]
            if unique_key not in seen_unique:
                seen_unique.add(unique_key)
                diverse_discoveries.append(disc)

        return {"discoveries": diverse_discoveries[:20]}

    except Exception as e:
        logger.error(f"Error getting cross-domain discoveries: {e}")
        return {"discoveries": [], "error": str(e)}


@app.get("/api/connections/tunnels")
async def get_auto_tunnels():
    """
    Get GraphPalace auto-tunnel status.

    Returns:
        - tunnels: List of active auto-tunnels
    """
    try:
        if not hasattr(engine, 'discovery_memory'):
            return {"tunnels": []}

        memory = engine.discovery_memory

        if not hasattr(memory, 'palace'):
            return {"tunnels": []}

        # Get all wings
        try:
            wings = memory.palace.list_wings()
        except Exception:
            return {"tunnels": []}

        tunnels = []

        # Get actual domains from discoveries (not GraphPalace wings)
        discovery_domains = list(set(d.domain for d in memory.discoveries))

        # Check cross-domain connections
        for i, domain1 in enumerate(discovery_domains[:5]):
            for domain2 in discovery_domains[i+1:6]:
                try:
                    connections = memory.find_cross_domain_connections(domain1, domain2, k=2)

                    for conn in connections:
                        tunnels.append({
                            "from_domain": domain1,
                            "to_domain": domain2,
                            "topic": conn.get("topic", ""),
                            "confidence": conn.get("confidence", 0),
                            "explanation": conn.get("explanation", "")
                        })
                except Exception:
                    pass

        return {"tunnels": tunnels[:20]}

    except Exception as e:
        return {"tunnels": [], "error": str(e)}


@app.get("/api/connections/palace-status")
async def get_palace_status():
    """
    Get GraphPalace memory system status.

    Returns:
        - GraphPalace status and statistics
    """
    try:
        if not hasattr(engine, 'discovery_memory'):
            return {"graphpalace_enabled": False}

        memory = engine.discovery_memory

        if hasattr(memory, 'get_palace_status'):
            return memory.get_palace_status()
        else:
            return {"graphpalace_enabled": False}

    except Exception as e:
        return {"graphpalace_enabled": False, "error": str(e)}


@app.post("/api/connections/search")
async def semantic_search(request: Request):
    """
    Perform semantic search across discoveries using GraphPalace.

    Body:
        - query: str - Search query
        - k: int - Number of results (default: 10)
        - domain: str (optional) - Domain filter

    Returns:
        - results: List of semantic search results
    """
    try:
        data = await request.json()
        query = data.get("query", "")
        k = data.get("k", 10)
        domain = data.get("domain")

        if not query:
            return {"results": []}

        if not hasattr(engine, 'discovery_memory'):
            return {"results": []}

        memory = engine.discovery_memory

        if not hasattr(memory, 'semantic_search'):
            return {"results": []}

        results = memory.semantic_search(query, k=k, domain=domain)

        return {"results": results, "query": query}

    except Exception as e:
        return {"results": [], "error": str(e)}


if __name__ == "__main__":
    import uvicorn
    import webbrowser
    import threading
    import time

    def open_browser():
        time.sleep(1.5)  # Wait for server to start
        webbrowser.open("http://localhost:8787")

    print("=" * 60)
    print("  ASTRA Live — Autonomous Scientific Discovery")
    print("  Dashboard: http://0.0.0.0:8787")
    print("  API Docs:  http://0.0.0.0:8787/docs")
    print("=" * 60)

    # Open browser in background thread
    threading.Thread(target=open_browser, daemon=True).start()

    uvicorn.run(app, host="0.0.0.0", port=8787, log_level="info")
