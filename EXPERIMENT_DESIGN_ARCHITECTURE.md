# ASTRA Experiment Design Architecture
## Automated Observation Proposal Generation for Theory Validation

**Date**: 2026-04-06
**Version**: 1.0

---

## Executive Summary

The Experiment Design Engine completes ASTRA's closed-loop scientific discovery system by enabling it to propose observations to test theoretical predictions.

### Critical Design Principle

**ASTRA proposes, humans execute.**

ASTRA cannot point telescopes or collect observations, but it can:
1. Identify what observations are needed to test theories
2. Find gaps in existing data coverage
3. Prioritize observations by scientific impact and feasibility
4. Generate detailed proposals that astronomers can submit to telescope time allocation committees
5. Track proposal status through the review and execution process

This makes ASTRA a "theory proposal engine" that guides real observational astronomy programs.

### Phase 3 Complete: Closed-Loop Discovery

```
Theory Generation → Prediction → Validation → [DATA GAP?] → Experiment Design
                                                              ↓
                                                         Proposal Generation
                                                              ↓
                                                    (Human Astronomers Execute)
                                                              ↓
                                                         Results Returned
                                                              ↓
                                                    Validation & Theory Refinement
```

---

## Architecture Overview

```
┌───────────────────────────────────────────────────────────────────┐
│                 EXPERIMENT DESIGN ENGINE                            │
│                                                                      │
│  ┌────────────┐   ┌────────────┐   ┌────────────┐   ┌──────────┐ │
│  │ IDENTIFY   │   │ FIND DATA  │   │ PRIORITIZE │   │GENERATE  │ │
│  │REQUIREMENTS│──→│   GAPS     │──→│OBSERVATIONS│──→│ PROPOSAL │ │
│  └────────────┘   └────────────┘   └────────────┘   └────┬─────┘ │
│                                                   │                │
│  ┌────────────────────────────────────────────────┴─────────┐     │
│  │                   PROPOSAL TRACKING SYSTEM                   │     │
│  │  DRAFT → PROPOSED → UNDER_REVIEW → ACCEPTED → SCHEDULED   │     │
│  │    → IN_PROGRESS → COMPLETED → RESULTS_RETURNED            │     │
│  └────────────────────────────────────────────────────────────┘     │
│                                                                      │
│  Input: Theoretical predictions + Data inventory                     │
│  Output: Observation proposals ready for submission                  │
└───────────────────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. Observation Requirements Analyzer

**Purpose**: Analyze theoretical predictions to determine what observations are needed

**Key Features**:
- Extracts parameter ranges from theoretical predictions
- Determines required precision and sample sizes
- Identifies appropriate object types for observations
- Calculates statistical power requirements

**Key Classes**:
```python
@dataclass
class ObservationRequirement:
    theory_name: str                      # Which theory needs this?
    parameter_range: Tuple[float, float]  # (min, max) values
    parameter_name: str                   # What to measure?
    object_types: List[str]               # What objects?
    observables: List[str]                # What measurements?
    precision_required: float             # How precise?
    sample_size_needed: int               # Statistical power
    urgency: str                          # "high", "medium", "low"
```

**Example**:
```python
# Theory predicts MOND-like behavior at low acceleration
requirement = ObservationRequirement(
    theory_name="Entropic Gravity",
    parameter_range=(1e-12, 1e-10),  # m/s²
    parameter_name="acceleration",
    object_types=["dwarf_galaxies", "low_surface_brightness_galaxies"],
    observables=["velocity_curve", "surface_brightness"],
    precision_required=0.05,  # 5% precision
    sample_size_needed=64,    # For statistical power
    urgency="high"
)
```

---

### 2. Data Gap Finder

**Purpose**: Identify gaps between existing data and what's needed to test theories

**Key Features**:
- Maintains inventory of existing astronomical data coverage
- Calculates coverage percentage for each parameter range
- Identifies where data is insufficient (< 80% coverage = gap)
- Estimates scientific impact and feasibility

**Key Classes**:
```python
@dataclass
class DataGap:
    gap_type: str                 # What's missing?
    theory_names: List[str]       # Which theories need this?
    missing_range: str            # What parameter/scale?
    existing_coverage: float      # Percentage [0-1]
    priority_impact: float        # How important? [0-1]
    feasibility: float            # How hard to observe? [0-1]
    estimated_cost: str           # e.g., "10 HST orbits"
```

**Data Inventory**:
```python
data_inventory = {
    "exoplanets": {
        "parameter_ranges": {
            "mass": (0.01, 100),      # Jupiter masses
            "period": (0.1, 100),     # days
            "eccentricity": (0.0, 1.0)
        },
        "coverage": {
            "low_mass_pclose": 0.9,   # 90% coverage
            "hot_jupiters": 0.8,
            "long_period": 0.6        # Gap!
        }
    },
    "galaxies": {
        "parameter_ranges": {
            "acceleration": (1e-12, 1e-8),  # m/s²
            "mass": (1e8, 1e12),            # Solar masses
        },
        "coverage": {
            "high_mass": 0.7,
            "low_mass": 0.3,      # Gap in low-mass regime
            "dwarf": 0.2          # Major gap!
        }
    }
}
```

---

### 3. Observation Prioritizer

**Purpose**: Rank observations by scientific priority

**Priority Formula**:
```
priority_score = scientific_impact × feasibility
```

**Factors**:
- **Scientific Impact**: How important is this gap?
  - Multiple theories need this data (+0.2)
  - Novel parameter ranges (+0.2)
  - Extreme regimes (+0.1)

- **Feasibility**: How hard is this observation?
  - Dwarf galaxies: -0.2 (faint objects)
  - High precision: -0.2 (requires expensive instruments)
  - High redshift: -0.3 (very distant)

**Example Output**:
```python
[
    {
        'gap_type': 'acceleration: 1e-12 - 1e-10',
        'priority_score': 0.45,  # 0.9 (impact) × 0.5 (feasibility)
        'impact': 0.9,
        'feasibility': 0.5,
        'estimated_cost': '20 hours Keck time'
    },
    {
        'gap_type': 'mass: 0.5 - 2.0',
        'priority_score': 0.56,  # 0.7 (impact) × 0.8 (feasibility)
        'impact': 0.7,
        'feasibility': 0.8,
        'estimated_cost': 'Standard star formation survey'
    }
]
```

---

### 4. Proposal Generator

**Purpose**: Generate detailed observation proposals ready for submission

**Key Features**:
- Generates complete proposal documents
- Recommends appropriate facilities
- Estimates time requirements
- Provides scientific justification
- Suggests alternative approaches

**Key Classes**:
```python
@dataclass
class ObservationProposal:
    proposal_id: str
    title: str
    abstract: str                                    # 200-word summary
    theory_being_tested: str
    scientific_justification: str
    target_objects: Dict[str, Any]
    observational_requirements: Dict[str, Any]
    facility_recommendations: List[str]              # "Keck", "HST", "JWST"
    time_requirements: Dict[str, Any]
    expected_results: Dict[str, Any]
    alternative_approaches: List[str]
    proposal_status: ProposalStatus
```

**Proposal Status Pipeline**:
```
DRAFT → PROPOSED → UNDER_REVIEW → ACCEPTED → SCHEDULED
  → IN_PROGRESS → COMPLETED → RESULTS_RETURNED
```

---

## Complete Workflow Example

### Scenario: Testing Entropic Gravity at Low Accelerations

#### Step 1: Identify Requirements
```python
theory = {
    'name': 'Entropic Gravity Low Acceleration Test',
    'parameter_range': {
        'range': (1e-12, 1e-10),
        'parameter': 'acceleration',
        'objects': ['dwarf_galaxies'],
        'precision': 0.05,
        'urgency': 'high'
    }
}

requirements = engine.identify_observation_requirements([theory])
```

**Output**:
```
Requirement: Entropic Gravity Low Acceleration Test
  Parameter: acceleration ∈ [1.00e-12, 1.00e-10]
  Objects: dwarf_galaxies
  Precision needed: 5%
  Sample size: 64
```

#### Step 2: Find Data Gaps
```python
gaps = engine.find_data_gaps(requirements)
```

**Output**:
```
Gap: acceleration: 1e-12 - 1e-10
  Theories affected: Entropic Gravity Low Acceleration Test
  Missing range: 1.00e-12 - 1.00e-10
  Current coverage: 10%
  Priority: 0.90 (impact) × 0.50 (feasibility)
  Estimated cost: 20 hours Keck time
```

#### Step 3: Generate Proposal
```python
proposal = engine.generate_proposal(gaps[0])
```

**Output**:
```
Proposal ID: PROP-20260406-143000
Title: Observational Test of Entropic via acceleration in Range [1.00e-12 - 1.00e-10]

Abstract:
We propose observational tests of Entropic Gravity Low Acceleration Test predictions
for acceleration in the range 1.00e-12 - 1.00e-10. Current data coverage in this
regime is only 10%, leaving theoretical predictions untested. We will observe
dwarf_galaxies to provide the necessary data. This will fill a critical gap in our
observational coverage and test fundamental theoretical predictions.

Facilities:
  - Keck Observatory (HIRESpec for low accelerations)
  - Very Large Array (radio interferometry for gas kinematics)
  - Hubble Space Telescope (deep imaging)

Time Requirements:
  - Exposure time: 2 hours per object
  - Sample size: 50 galaxies
  - Timeline: Single 6-month observing run or spread over 2 semesters

Expected Results:
  - Validate/invalidate Entropic Gravity Low Acceleration Test
  - Fill data gap in acceleration range
  - Confidence in theories will increase from 90% to >95%
```

---

## Integration with ASTRA Engine

### Update Engine Imports

```python
# In astra_live_backend/engine.py

from .experiment_design_engine import (
    ExperimentDesignEngine, ObservationProposal, ProposalStatus
)
```

### Initialize in `__init__`:

```python
# Experiment design engine (Phase 14: Observation Proposal Generation)
if THEORY_MODULES_AVAILABLE:
    self.experiment_designer = ExperimentDesignEngine()
    self._experiment_design_interval = 25  # Run every 25 cycles
    self._last_experiment_design_cycle = 0
```

### Add to UPDATE Phase:

```python
# In engine.py update() method

# Experiment design: runs every N cycles (default: 25)
# This generates observation proposals to test theoretical predictions
if self._experiment_design_enabled and \
   (self.cycle_count - self._last_experiment_design_cycle >= self._experiment_design_interval):

    # Check if we have validated theories with data gaps
    validated_theories = [t for t in self.unified_engine.candidates.values()
                         if t.status == 'validated']

    if validated_theories:
        # Identify observation requirements
        theories_to_check = [
            {
                'name': t.name,
                'parameter_range': t.prediction.parameters
            }
            for t in validated_theories[:3]
        ]

        requirements = self.experiment_designer.identify_observation_requirements(
            theories_to_check
        )

        # Find gaps and generate proposals
        gaps = self.experiment_designer.find_data_gaps(requirements)

        if gaps:
            proposals = self.experiment_designer.batch_generate_proposals(
                n_proposals=min(3, len(gaps))
            )

            # Log results
            self._log("UPDATE", "EXPERIMENT_DESIGN",
                     f"Identified {len(requirements)} requirements, "
                     f"{len(gaps)} data gaps, "
                     f"generated {len(proposals)} proposals")

            for proposal in proposals:
                self._log("PROPOSAL", proposal.proposal_id,
                         f"{proposal.title} → {proposal.proposal_status.value}")

    self._last_experiment_design_cycle = self.cycle_count
```

---

## API Endpoints

```bash
# Identify observation requirements
curl -X POST "http://localhost:8787/api/experiment/requirements" \
  -H "Content-Type: application/json" \
  -d '{
    "theories": [
      {
        "name": "Entropic Gravity",
        "parameter_range": {
          "range": [1e-12, 1e-10],
          "parameter": "acceleration",
          "objects": ["dwarf_galaxies"],
          "precision": 0.05
        }
      }
    ]
  }'

# Find data gaps
curl -X POST "http://localhost:8787/api/experiment/gaps" \
  -H "Content-Type: application/json" \
  -d '{"requirements": [...]}'

# Prioritize observations
curl -X POST "http://localhost:8787/api/experiment/prioritize" \
  -H "Content-Type: application/json" \
  -d '{"gaps": [...]}'

# Generate single proposal
curl -X POST "http://localhost:8787/api/experiment/proposal" \
  -H "Content-Type: application/json" \
  -d '{"gap_id": "gap_123"}'

# Batch generate proposals
curl -X POST "http://localhost:8787/api/experiment/proposals" \
  -H "Content-Type: application/json" \
  -d '{"n_proposals": 5}'

# Update proposal status
curl -X PUT "http://localhost:8787/api/experiment/proposal/PROP-20260406/status" \
  -H "Content-Type: application/json" \
  -d '{"status": "accepted"}'

# Submit observation results
curl -X POST "http://localhost:8787/api/experiment/proposal/PROP-20260406/results" \
  -H "Content-Type: application/json" \
  -d '{"results": {...}}'

# Get proposal summary
curl "http://localhost:8787/api/experiment/proposal/PROP-20260406/summary"

# Get proposal statistics
curl "http://localhost:8787/api/experiment/statistics"
```

---

## Expected Discoveries

### Short-term (within current proposal cycle)
1. **Identified data gaps** in low-acceleration regime for galaxy dynamics
2. **Generated proposals** for testing entropic gravity predictions
3. **Prioritized observations** by scientific impact and feasibility
4. **Facility recommendations** matched to observation requirements

### Medium-term (with executed proposals)
1. **Validated theories** through new observational data
2. **Refined theoretical parameters** based on returned results
3. **Closed-loop discovery** where proposals lead to validation leads to new proposals
4. **Publication-ready proposals** that can be submitted to TACs

### Long-term
1. **Automated proposal generation** for routine observational tests
2. **Theory-driven observation planning** that maximizes scientific return
3. **Integration with telescope scheduling systems** for efficient execution
4. **Scientific impact tracking** across proposal cycles

---

## Key Innovations

### 1. **ASTRA Proposes, Humans Execute**
The critical distinction that makes this system scientifically honest and practically feasible. ASTRA identifies what needs to be observed but leaves the actual telescope operations to professional astronomers.

### 2. **Data Gap Quantification**
Not just "we need more data" but specifically:
- What parameter range is missing?
- What percentage coverage exists?
- How many objects are needed for statistical power?
- What precision is required?

### 3. **Scientific Impact Scoring**
Priority = Impact × Feasibility
- Impact: Multiple theories, novelty, extreme regimes
- Feasibility: Object brightness, required precision, facility availability

### 4. **Complete Proposal Generation**
Not just observation ideas but complete proposals including:
- Title and abstract
- Scientific justification
- Facility recommendations with rationale
- Time requirements and timeline
- Expected results and data products
- Alternative approaches if main proposal rejected

### 5. **Proposal Status Tracking**
Full lifecycle management from draft through execution to results return, enabling closed-loop learning where observational outcomes feed back into theory validation.

---

## Testing

```python
from astra_live_backend.experiment_design_engine import (
    ExperimentDesignEngine, ObservationRequirement, DataGap
)

# Initialize engine
engine = ExperimentDesignEngine()

# Test requirement identification
theories = [
    {
        'name': 'Entropic Gravity Test',
        'parameter_range': {
            'range': (1e-12, 1e-10),
            'parameter': 'acceleration',
            'objects': ['dwarf_galaxies'],
            'precision': 0.05,
            'urgency': 'high'
        }
    }
]

requirements = engine.identify_observation_requirements(theories)
print(f"Identified {len(requirements)} requirements")

# Test gap finding
gaps = engine.find_data_gaps(requirements)
print(f"Found {len(gaps)} data gaps")

# Test prioritization
prioritized = engine.prioritize_observations(gaps)
print(f"Top priority: {prioritized[0]['gap_type']}")
print(f"Priority score: {prioritized[0]['priority_score']:.3f}")

# Test proposal generation
if gaps:
    proposal = engine.generate_proposal(gaps[0])
    print(f"\nGenerated proposal: {proposal.proposal_id}")
    print(f"Title: {proposal.title}")
    print(f"Facilities: {', '.join(proposal.facility_recommendations)}")
    print(f"Abstract: {proposal.abstract[:200]}...")

# Test batch generation
proposals = engine.batch_generate_proposals(n_proposals=3)
print(f"\nGenerated {len(proposals)} proposals")

# Test statistics
stats = engine.get_proposal_statistics()
print(f"\nStatistics: {stats}")
```

---

## Impact on ASTRA's Capabilities

### Capabilities Matrix

| Capability | Phase 1 | Phase 2 | Phase 3 (Unified) | Phase 4 (Experiment Design) |
|-----------|---------|---------|------------------|----------------------------|
| Pattern discovery | ✅ | ✅ | ✅ | ✅ |
| Statistical testing | ✅ | ✅ | ✅ | ✅ |
| Novel theoretical concepts | ❌ | ✅ | ✅ | ✅ |
| Theory validation | ❌ | ❌ | ✅ | ✅ |
| Theory refinement | ❌ | ❌ | ✅ | ✅ |
| Theory-data integration | ❌ | ❌ | ✅ | ✅ |
| Closed-loop discovery | ❌ | ❌ | ✅ | ✅ |
| **Observation proposal generation** | ❌ | ❌ | ❌ | ✅ |
| **Data gap identification** | ❌ | ❌ | ❌ | ✅ |
| **Scientific impact prioritization** | ❌ | ❌ | ❌ | ✅ |

### Complete Closed-Loop Scientific Discovery

```
┌─────────────────────────────────────────────────────────────┐
│              ASTRA CLOSED-LOOP DISCOVERY SYSTEM              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. THEORY GENERATION                                        │
│     ├─ Conceptual blending                                   │
│     ├─ Information physics                                   │
│     └─ Mathematical structure discovery                      │
│           ↓                                                  │
│  2. PREDICTION                                               │
│     └─ Extract testable predictions from theories            │
│           ↓                                                  │
│  3. VALIDATION (against existing data)                       │
│     ├─ Compare predictions to data                          │
│     ├─ Calculate agreement scores                           │
│     └─ Identify discrepancies                               │
│           ↓                                                  │
│  4. DATA GAP ANALYSIS                                        │
│     ├─ Find where data is insufficient                       │
│     ├─ Quantify coverage gaps                               │
│     └─ Calculate scientific impact                          │
│           ↓                                                  │
│  5. EXPERIMENT DESIGN                                        │
│     ├─ Generate observation proposals                       │
│     ├─ Recommend facilities                                  │
│     └─ Estimate time requirements                           │
│           ↓                                                  │
│  6. (HUMAN EXECUTION)                                        │
│     └─ Astronomers execute proposals                         │
│           ↓                                                  │
│  7. RESULTS RETURNED                                         │
│     └─ New observations fed back into system                │
│           ↓                                                  │
│  8. THEORY REFINEMENT                                        │
│     └─ Update theories based on new data                    │
│           ↓                                                  │
│  9. REPEAT                                                   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Comparison: Before vs After

### Before (Phase 3 - Unified Discovery):
```
Theory modules → Generate predictions
     ↓
Validation Bridge → Test against EXISTING data
     ↓
     ↓
     ↙   ↘
Disagreement? → Yes → Refinement Engine → Modify theory
     ↓
     ↓
     ↙   ↘
Agreement? → Yes → Theory strengthened
     ↓
Unified output: Validated theories (but limited to existing data)
```

### After (Phase 4 - Complete Closed Loop):
```
Theory modules → Generate predictions
     ↓
Validation Bridge → Test against existing data
     ↓
     ↓
     ↙   ↘
Disagreement? → Yes → Refinement Engine → Modify theory
     ↓
     ↓
     ↙   ↘
DATA GAP? → Yes → Experiment Design Engine → Generate Proposal
                                        ↓
                                  (Human Execution)
                                        ↓
                                  New Data Returned
                                        ↓
                                  Re-validate Theory
     ↓
     ↓
     ↙   ↘
Agreement? → Yes → Theory strengthened
     ↓
Complete closed-loop: Theory → Data → Gap → Proposal → Observation → Theory
```

---

## Conclusion

The Experiment Design Engine represents the **final piece** in ASTRA's closed-loop scientific discovery system:

**From**: Theories tested only against existing data
**To**: Theories that can identify what new data is needed and propose observations to get it

This mirrors how human scientists work:
1. Propose theory
2. Test against existing data
3. Identify what new observations are needed
4. Write telescope proposals
5. (Get time, execute observations)
6. Analyze new data
7. Refine theory
8. Repeat

**Status**: ✅ **COMPLETE AND READY FOR INTEGRATION**

Files created:
- `astra_live_backend/experiment_design_engine.py` (Automated Experiment Design & Proposal Engine)
- `EXPERIMENT_DESIGN_ARCHITECTURE.md` (This document)

**Total ASTRA Evolution**:
- Phase 1: Empirical Pattern Discovery
- Phase 2: Theoretical Innovation
- Phase 3: Unified Discovery (Theory-Data Integration)
- Phase 4: Experiment Design (Observation Proposal Generation)

**Next**: Integrate into ASTRA's UPDATE phase and begin generating observation proposals for validated theories that have identified data gaps.
