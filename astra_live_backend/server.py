from astra_live_backend.safety.health import SystemHealthReport
"""
ASTRA Live — FastAPI Server
Real-time API for the ASTRA Live dashboard.
"""
import time
import json
import os
import sys
from pathlib import Path

from fastapi import FastAPI
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


# ── API Endpoints ────────────────────────────────────────────────

@app.get("/api/status")
def api_status():
    """Engine status — is it running, cycle count, uptime."""
    state = engine.get_state()
    return {
        "status": "running" if engine.running else "stopped",
        "engine": state,
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

DASHBOARD_DIR = Path("/shared/public/astra-live")


@app.get("/")
def serve_dashboard():
    return FileResponse(DASHBOARD_DIR / "index.html")


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
def api_discovery_discoveries(min_strength: float = 0.0, limit: int = 50):
    """List recorded discoveries, optionally filtered by strength."""
    discoveries = [d for d in engine.discovery_memory.discoveries
                   if d.strength >= min_strength]
    discoveries.sort(key=lambda d: d.strength, reverse=True)
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
    existing_names = {h.name for h in engine.store.all()}
    candidates = engine.hypothesis_generator.generate_from_discoveries(
        current_cycle=engine.cycle_count,
        existing_names=existing_names,
        max_new=3,
    )
    generated = []
    for c in candidates:
        h = engine.store.add(c["name"], c["domain"], c["description"],
                             confidence=c["confidence"])
        h.phase = engine.hypotheses.Phase.PROPOSED
        engine.discovery_memory.generation_count += 1
        generated.append({"id": h.id, "name": c["name"], "source": c.get("source_discovery_id")})
    return {"generated": generated, "total_memory_discoveries": len(engine.discovery_memory.discoveries)}


# ── Serve the Dashboard ──────────────────────────────────────────

DASHBOARD_DIR = Path("/shared/public/astra-live")


@app.get("/")
def serve_dashboard():
    return FileResponse(DASHBOARD_DIR / "index.html")


@app.get("/api/system/health")
def api_system_health():
    """Component health for the Health tab (Phase 2 Update)."""
    health = SystemHealthReport()
    return health.get_report(engine.get_state())


if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("  ASTRA Live — Autonomous Scientific Discovery")
    print("  Dashboard: http://0.0.0.0:8787")
    print("  API Docs:  http://0.0.0.0:8787/docs")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8787, log_level="info")
