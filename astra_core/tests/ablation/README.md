# ASTRA Ablation Testing Framework

Comprehensive ablation testing framework for validating ASTRA's architectural design decisions.

## Overview

This framework systematically tests the contribution of each ASTRA component to overall system performance by:

1. Establishing a performance baseline with the full system
2. Individually disabling each component (ablation)
3. Measuring performance degradation across 14 evaluation metrics
4. Generating reports and visualizations suitable for peer review

## Directory Structure

```
astra_core/tests/ablation/
├── configurations.py      # Ablation configuration definitions
├── metrics.py             # Evaluation metrics and scoring functions
├── run_ablations.py       # Main test runner
├── visualize.py           # Visualization tools
├── generate_report.py     # Report generation
├── results/               # Generated results and visualizations
└── README.md             # This file
```

## Usage

### Quick Start

Run all ablation studies:

```bash
cd astra_core/tests/ablation
python run_ablations.py
```

Run only critical ablations (faster):

```bash
python run_ablations.py --critical-only
```

Run a specific ablation:

```bash
python run_ablations.py --ablation no_mmol
```

### Generate Visualizations

After running ablations, generate visualizations:

```bash
python visualize.py ablation_results_YYYYMMDD_HHMMSS.json
```

### Generate Report

Generate a comprehensive report:

```bash
python generate_report.py ablation_results_YYYYMMDD_HHMMSS.json
```

## Ablation Categories

### Core Architecture
- **no_mce**: Remove Meta-Context Engine
- **no_asc**: Remove Autocatalytic Self-Compiler
- **no_crn**: Remove Cognitive-Relativity Navigator
- **no_mmol**: Remove Multi-Mind Orchestration Layer

### Memory System
- **no_working_memory**: Remove Working Memory (7±2 constraint)
- **no_episodic_memory**: Remove Episodic Memory
- **no_mork_ontology**: Remove MORK Ontology
- **no_vector_store**: Remove Vector Store
- **minimal_memory**: All memory components disabled

### Domain Modules
- **core_domains_only**: Only core domains, no astrophysics
- **no_ism_domains**: Remove ISM-related domains
- **no_star_formation_domains**: Remove star formation domains
- **no_exoplanet_domains**: Remove exoplanet domains
- **no_high_energy_domains**: Remove high-energy domains

### Physics Engine
- **basic_physics_only**: Only basic physics stage
- **no_analogical_reasoning**: Remove physics analogical reasoning
- **no_constraint_validation**: Remove physics constraint validation
- **no_unified_physics**: Remove unified physics engine

### Causal Discovery
- **no_v50_causal**: Remove V50 causal discovery engine
- **no_v70_causal**: Remove V70 causal discovery engine
- **no_astro_causal**: Remove astrophysical causal models
- **no_causal_discovery**: Remove all causal discovery

### Meta-Learning
- **no_maml**: Remove MAML optimizer
- **no_cross_domain_meta**: Remove cross-domain meta-learner
- **no_meta_learning**: Remove all meta-learning

### Capabilities
- **no_specialist_capabilities**: Remove all 66+ specialist capabilities
- **basic_capabilities_only**: Only basic capabilities (V1-V20)

## Evaluation Metrics

### Hypothesis Generation (Weight: 1.0-1.2)
- **Novelty**: Originality of generated hypotheses
- **Feasibility**: Testability of proposed mechanisms
- **Specificity**: Quantitative specificity

### Scientific Accuracy (Weight: 0.8-1.5)
- **Factual Correctness**: Accuracy of factual claims
- **Physics Consistency**: Consistency with physical laws
- **Citation Quality**: Quality of references

### Reasoning Quality (Weight: 1.0-1.2)
- **Logical Coherence**: Logical flow and consistency
- **Reasoning Depth**: Multi-step reasoning capability
- **Inference Quality**: Quality of inferences drawn

### Cross-Domain Synthesis (Weight: 0.8-1.2)
- **Domain Breadth**: Number of domains integrated
- **Synthesis Quality**: Quality of cross-domain connections
- **Analogy Quality**: Analogical reasoning capability

### Efficiency (Weight: 0.5)
- **Processing Time**: Query processing speed

### Robustness (Weight: 0.5-0.7)
- **Error Recovery**: Ability to recover from errors
- **Confidence Calibration**: Accuracy of confidence estimates

## Output Files

### Results Files
- `ablation_results_TIMESTAMP.json`: Raw ablation data
- `ablation_report_TIMESTAMP.md`: Comprehensive report in Markdown

### Visualizations
- `component_importance_TIMESTAMP.png`: Bar chart of component importance
- `performance_degradation_TIMESTAMP.png`: Performance degradation over ablations
- `metric_heatmap_TIMESTAMP.png`: Heatmap of metric comparisons
- `radar_chart_TIMESTAMP.png`: Radar chart by metric category

## Integration with Paper

The generated reports and visualizations are designed for direct inclusion in academic papers:

1. **Component Importance Chart**: Figure for "Ablation Studies" section
2. **Performance Degradation Graph**: Shows relative importance of components
3. **Metric Heatmap**: Detailed performance breakdown by metric
4. **Report Tables**: LaTeX-formatted tables for results section

## Example Results

Expected performance degradation for critical components:

- **MMOL Removal**: ~20% degradation (most critical)
- **Minimal Memory**: ~35% degradation
- **Core Domains Only**: ~40% degradation
- **No Causal Discovery**: ~20% degradation

## Notes

- Full ablation studies take 2-4 hours to complete
- Critical ablations only take 30-45 minutes
- Results are deterministic given the same system state
- All metrics are normalized to 0-1 scale for comparability

## Citation

If you use this framework in your research, please cite:

```
ASTRA: Autonomous System for Scientific Discovery in Astrophysics
arXiv:XXXX.XXXXX [astro-ph.IM]
```
