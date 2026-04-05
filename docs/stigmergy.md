# ASTRA Stigmergy Integration

## Architecture Overview

The stigmergy subsystem enables biologically-inspired swarm intelligence within ASTRA's discovery engine. It connects three previously disconnected modules into a unified pheromone-guided discovery pipeline.

```
┌─────────────────────────────────────────────────────────────────┐
│                    ASTRA Discovery Engine                       │
│  ┌──────────┐  ┌──────────┐  ┌─────────────┐  ┌────────────┐  │
│  │  ORIENT   │→│  SELECT   │→│ INVESTIGATE  │→│  EVALUATE   │→ │
│  │ (scout)   │  │(rank+pher)│  │(test+deposit)│  │(discover)  │  │
│  └────┬─────┘  └────┬─────┘  └──────┬──────┘  └─────┬──────┘  │
│       │              │               │               │          │
│  ┌────▼──────────────▼───────────────▼───────────────▼──────┐  │
│  │                 StigmergyBridge                            │  │
│  │  ┌────────────────┐ ┌──────────────┐ ┌─────────────────┐ │  │
│  │  │ PheromoneField  │ │ StigmergicMem│ │ SwarmCoordinator│ │  │
│  │  │ (20×20×6 grid) │ │ (TAU/ETA/C_K)│ │ (5 agent types) │ │  │
│  │  └────────────────┘ └──────────────┘ └─────────────────┘ │  │
│  └──────────────────────────────────────────────────────────┘  │
│       │                                                        │
│  ┌────▼─────────────────────────────────────────────────────┐  │
│  │  UPDATE: All agents deposit, cross-domain links, persist │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Component Map

| File | Purpose | Lines |
|------|---------|-------|
| `astra_core/intelligence/pheromone_dynamics.py` | Digital pheromone field (V36 hypothesis space) | 705 |
| `astra_core/self_teaching/stigmergic_memory.py` | TAU/ETA/C_K biological field memory | 653 |
| `astra_core/swarm/transforms.py` | Gordon's biological transforms | 340 |
| `astra_live_backend/stigmergy_bridge.py` | **Bridge** connecting subsystem to engine | ~500 |
| `astra_live_backend/swarm_agents.py` | 5 swarm agent types + coordinator | ~400 |
| `astra_live_backend/engine.py` | Discovery engine (with stigmergy hooks) | ~2000 |
| `astra_live_backend/server.py` | FastAPI (12 stigmergy endpoints) | ~1400 |
| `tests/test_stigmergy_integration.py` | 50 tests | ~600 |

---

## Pheromone Types

| Type | Purpose | Decay Rate | Use |
|------|---------|------------|-----|
| `EXPLORATION` | Marks visited regions | 0.10 (fast) | Avoid revisiting |
| `SUCCESS` | Marks confirmed hypotheses | 0.02 (slow) | Attract exploitation |
| `FAILURE` | Marks rejected hypotheses | 0.05 (medium) | Repel future attempts |
| `ANALOGY` | Marks cross-domain links | 0.03 (slow) | Guide analogist agents |
| `NOVELTY` | Marks novel discoveries | 0.02 (slowest) | Attract investigation |
| `ATTENTION` | Marks areas needing study | 0.15 (fastest) | Short-term focus |

---

## Engine Integration Hooks

### Hook 1: `orient()` → Scout + Exploration Direction
```python
# ScoutAgent scans for novelty
scout_action = self.swarm.run_orient_phase()
# Get pheromone-guided exploration direction
direction = self.stigmergy.get_exploration_direction(domain)
# direction.strategy = 'explore' | 'exploit' | 'balanced'
# direction.curiosity_value = C_K (0-1)
```

### Hook 2: `select()` → Pheromone Re-ranking
```python
# Re-rank hypotheses using pheromone signals
# final_score = (1-w) * original_score + w * pheromone_score
reranked = self.stigmergy.rank_hypotheses(h_dicts, scores)
```

### Hook 3: `investigate()` → Deposit After Test
```python
# After each hypothesis test, deposit SUCCESS or FAILURE pheromone
self.stigmergy.on_hypothesis_tested(hypothesis_dict, result_dict)
# Also records A/B test data for pheromone vs baseline comparison
self.stigmergy.record_ab_result(guided=True, success=passed)
```

### Hook 4: `evaluate()` → Record Discoveries
```python
# Significant results (p < 0.05) deposit NOVELTY pheromone
self.stigmergy.on_discovery({
    'domain': h.domain,
    'category': category,
    'significance': 1.0 - p_val,
    'content': description,
})
```

### Hook 5: `update()` → Swarm Deposits + Cross-Domain
```python
# All 5 swarm agents deposit pheromones
self.swarm.run_update_phase(cycle_results)
# Cross-domain connections deposit ANALOGY pheromone
self.stigmergy.on_cross_domain_connection(domain_a, domain_b, ...)
```

---

## Swarm Agent Types

| Agent | Role | Deposits | Follows |
|-------|------|----------|---------|
| **ExplorerAgent** | Maximize coverage | EXPLORATION | Low-EXPLORATION regions |
| **ExploiterAgent** | Exploit success | SUCCESS | High-SUCCESS trails |
| **FalsifierAgent** | Test theories | FAILURE | High-C_K theories |
| **AnalogistAgent** | Find analogies | ANALOGY | Cross-domain patterns |
| **ScoutAgent** | Random discovery | NOVELTY | Random walk |

All agents implement **Gordon's contact rate protocol**: 2–10 contacts/minute with 15% task-switching probability.

---

## API Reference

### Pheromone Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/pheromones/status` | Full stigmergy status |
| GET | `/api/pheromones/hotspots?pheromone_type=success&top_k=10` | Top-N hotspots |
| POST | `/api/pheromones/gradient` | Gradient at domain `{"domain":"Astrophysics"}` |
| GET | `/api/pheromones/deposits?limit=50` | Recent deposit history |
| GET | `/api/pheromones/field` | Full field data (for viz) |
| GET | `/api/pheromones/ab-test` | A/B test results |
| POST | `/api/pheromones/weight` | Set weight `{"weight": 0.3}` |

### Stigmergy Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/stigmergy/state` | StigmergicMemory state |
| POST | `/api/stigmergy/recommendations` | Swarm recommendations |
| GET | `/api/stigmergy/gaps` | Knowledge gap analysis |
| GET | `/api/stigmergy/exploration?domain=X` | Exploration direction |

### Swarm Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/swarm/status` | All 5 agent statuses |

### Status Integration

The existing `/api/status` now includes a `stigmergy` field:
```json
{
  "status": "running",
  "engine": { ... },
  "stigmergy": {
    "pheromone_weight": 0.3,
    "total_deposits": 142,
    "success_deposits": 89,
    "failure_deposits": 34,
    "novelty_deposits": 19
  }
}
```

---

## Configuration

### Pheromone Weight
Controls how much pheromone signals influence hypothesis ranking:
- `0.0` = pure engine scoring (baseline)
- `0.3` = default (30% pheromone, 70% engine)
- `1.0` = pure pheromone (not recommended)

Adjust via API: `POST /api/pheromones/weight {"weight": 0.3}`

### Circuit Breaker
If pheromone-guided selections perform >20% worse than baseline (measured via A/B testing), the weight is automatically halved. Requires ≥20 samples in each arm before triggering.

### Gordon's Immutable Parameters
From 30 years of *Pogonomyrmex barbatus* research:

| Parameter | Value | Meaning |
|-----------|-------|---------|
| ρ (evaporation_rate) | 0.05 | Trail decay per timestep |
| α (reinforcement_rate) | 0.1 | Trail reinforcement |
| β (anternet_weight) | 0.6 | Success feedback weight |
| γ (restraint_weight) | 0.4 | Cost/utility weight |
| switch_probability | 0.15 | Task switching (15%) |
| contact_rate_min | 0.033 | 2 contacts/minute |
| contact_rate_max | 0.167 | 10 contacts/minute |

---

## Persistence

State is saved to `/shared/ASTRA/data/stigmergy/`:
- `pheromone_field.json` — Full pheromone grid + deposit history
- `stigmergic_memory.json` — TAU/ETA/C_K fields + trails + discoveries
- `metrics.json` — Bridge metrics + A/B test results + weight

Auto-saves every 100 deposits and every 50 engine cycles. Loaded on engine startup.

---

## Biological Foundations

### Deborah Gordon's Research
The swarm coordination model is based on Prof. Deborah Gordon's 30+ years of field research on *Pogonomyrmex barbatus* (red harvester ants). Key principles:

1. **No central control** — colony behavior emerges from local interactions
2. **Contact rate protocol** — ants regulate activity based on encounter frequency
3. **Task allocation** — probabilistic switching between roles (foraging, patrolling, nest maintenance)
4. **Anternet** — colony adjusts foraging effort based on returning success rate (analogous to TCP)
5. **Collective restraint** — colonies collectively limit activity when costs are high

### Application to Scientific Discovery
- **Pheromone trails** = accumulated evidence from hypothesis testing
- **SUCCESS pheromone** = confirmed scientific findings (slow decay, persistent)
- **FAILURE pheromone** = rejected hypotheses (medium decay, warning signal)
- **Exploration vs exploitation** = curiosity-driven search vs deep investigation
- **Task switching** = domain diversification (15% chance per cycle)

---

## Troubleshooting

### Server won't start after adding stigmergy
The `astra_core` package has cascading import errors in its `__init__.py` files. The bridge uses `importlib.util` to directly import the 3 required modules without triggering the init chains.

### Pheromone weight keeps decreasing
The circuit breaker is triggering — pheromone-guided selections are performing worse than baseline. Check A/B test results: `GET /api/pheromones/ab-test`. You may need to adjust the weight threshold or wait for more data.

### No deposits accumulating
Check that the engine is running: `GET /api/status`. Deposits only occur during hypothesis testing in the INVESTIGATE and EVALUATE phases.

### State not persisting
Ensure `/shared/ASTRA/data/stigmergy/` directory exists and is writable. Check server logs for persistence errors.

---

## Testing

Run all 50 stigmergy tests:
```bash
cd /shared/ASTRA
python3 -m pytest tests/test_stigmergy_integration.py -v
```

Test categories:
- `TestPheromoneField` (10 tests) — deposit, sense, evaporation, gradient, serialization
- `TestStigmergicMemory` (6 tests) — deposit, discovery, gaps, state, recommendations, persistence
- `TestStigmergyBridge` (13 tests) — all hooks, A/B testing, circuit breaker, persistence, status
- `TestSwarmAgents` (11 tests) — all 5 agent types, coordinator, contact rate
- `TestGordonParams` (9 tests) — immutable parameters, transforms, updater, curiosity
- `TestEndToEnd` (1 test) — full cycle simulation
