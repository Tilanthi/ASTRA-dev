# ASTRA User Manual
## Autonomous Scientific Discovery in Astrophysics

**Version**: 7.0
**Date**: April 2026
**Authors**: Glenn J. White, Open University and Rutherford Appleton Laboratory, England
**Repository**: https://github.com/Tilanthi/ASTRA

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [System Architecture](#2-system-architecture)
3. [Installation and Setup](#3-installation-and-setup)
   - 3.1 System Requirements
   - 3.2 Installation Methods
   - 3.3 Configuration
   - 3.4 Running ASTRA from Claude Code ⭐ NEW
4. [Getting Started](#4-getting-started)
5. [Core Capabilities Overview](#5-core-capabilities-overview)
6. [V5.0 Discovery Enhancement System](#6-v50-discovery-enhancement-system)
7. [V7.0 Autonomous Research Scientist](#7-v70-autonomous-research-scientist) ⭐ NEW
8. [Use Case Examples](#8-use-case-examples)
9. [Advanced Features](#9-advanced-features)
10. [Domain Modules](#10-domain-modules)
11. [API Reference](#11-api-reference)
12. [Best Practices](#12-best-practices)
13. [Troubleshooting](#13-troubleshooting)
14. [Appendices](#14-appendices)

---

## 1. Introduction

### 1.1 What is ASTRA?

ASTRA (Autonomous Scientific Discovery in Astrophysics) is an integrated computational framework that combines numerical data analysis, causal reasoning, physical validation, and statistical inference to enable automated scientific discovery in astrophysics. Unlike traditional machine learning systems that detect patterns without understanding their physical meaning, or large language models that can explain concepts but cannot process numerical data, ASTRA integrates multiple analytical approaches to provide physically interpretable, validated scientific insights.

**Version 7.0** represents a major evolution with the introduction of the **Autonomous Research Scientist**—a system capable of conducting the entire scientific research cycle from question formulation through publication.

### 1.2 Key Design Principles

**Physics-Aware Reasoning**: All discoveries are validated against fundamental physical principles including conservation laws, dimensional consistency, and established theoretical frameworks.

**Causal Understanding**: ASTRA distinguishes between correlation and causation using structural causal models, enabling identification of physical mechanisms rather than mere associations.

**Uncertainty Quantification**: Every result includes properly propagated uncertainties, confidence intervals, and statistical significance assessments.

**Reproducibility**: All analyses are fully documented and reproducible, with complete provenance tracking from raw data to final conclusions.

**Autonomous Research**: V7.0 can independently generate research questions, formulate hypotheses, design experiments, execute studies, and produce publications.

### 1.3 Who Should Use This Manual?

This manual is written for expert users including:
- Research astronomers and astrophysicists
- Data scientists working with astronomical data
- Computational scientists requiring physics-aware analysis tools
- Graduate students and postdoctoral researchers in astrophysics

Users should have familiarity with:
- Python programming
- Basic statistical concepts
- Fundamental astrophysical principles
- Command-line operation

### 1.4 What's New in Version 7.0

**V7.0 Autonomous Research Scientist**:
- Question generation engine
- Hypothesis formulation system
- Experiment design and execution
- Automated theory revision
- Publication generation

**Enhanced Capabilities**:
- Multi-Mind Orchestration (7 specialized minds)
- Global coherence layer
- Analogical reasoning
- Continuous learning
- Scientific taste evaluation

---

## 2. System Architecture

### 2.1 Architectural Overview

ASTRA implements a layered architecture designed for astrophysical data analysis and inference:

```
┌─────────────────────────────────────────────────────────────┐
│                     User Interface Layer                    │
│  (Command line, Python API, Jupyter notebooks)             │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                   Orchestration Layer                       │
│  Query processing, module selection, result integration     │
└─────┬───────────┬───────────┬───────────┬───────────┬─────┘
      │           │           │           │           │
┌─────▼─────┐ ┌─▼──────┐ ┌─▼──────┐ ┌─▼──────┐ ┌─▼────────┐
│  Physics  │ │ Causal │ │Bayesian│ │ Data   │ │ Domain   │
│  Engine   │ │Reasoning│ │Inference│ │Processing│Knowledge│
└───────────┘ └────────┘ └────────┘ └────────┘ └──────────┘
      │           │           │           │           │
      └───────────┴───────────┴───────────┴───────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│              V7.0 Autonomous Research Layer                 │
│  Question → Hypothesis → Experiment → Analysis → Theory   │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                    Foundation Layer                         │
│  Memory systems, I/O handling, numerical libraries         │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Core Components

#### 2.2.1 Physics Engine

The Physics Engine implements fundamental physical laws and constraints that govern all analyses.

#### 2.2.2 Causal Reasoning Module

The Causal Reasoning Module enables discovery and inference of causal relationships from observational data.

#### 2.2.3 Bayesian Inference Engine

The Bayesian Inference Engine provides rigorous model comparison and uncertainty quantification.

#### 2.2.4 Data Processing Pipeline

The Data Processing Pipeline handles ingestion, validation, and preparation of astronomical data.

#### 2.2.5 Domain Knowledge Systems

Organized astrophysical knowledge provides context for all analyses.

---

## 3. Installation and Setup

### 3.1 System Requirements

**Minimum Requirements**:
- Python 3.8 or higher
- 8 GB RAM
- 2 GB free disk space
- Linux, macOS, or Windows with WSL2

**Recommended for Large Datasets**:
- Python 3.10 or higher
- 32 GB RAM
- 20 GB free disk space
- SSD storage for better I/O performance
- Multi-core processor (4+ cores)

**Optional Dependencies**:
- GPU for accelerated deep learning (CUDA-capable)
- Jupyter for interactive analysis
- Docker for containerized deployment

### 3.2 Installation Methods

#### 3.2.1 Installation from GitHub

```bash
# Clone the repository
git clone https://github.com/Tilanthi/ASTRA.git
cd ASTRA

# Install in editable mode
pip install -e .

# Install optional dependencies
pip install -e ".[dev]"
```

#### 3.2.2 Verification of Installation

```python
# Test installation
python -c "import stan_core; print('ASTRA installed successfully')"

# Check version
python -c "from stan_core import __version__; print(__version__)"
```

### 3.3 Configuration

#### 3.3.1 Basic Configuration

Create a configuration file `~/.astra/config.json`:

```json
{
  "data_directory": "~/astronomy_data",
  "memory_limit_gb": 16,
  "num_workers": 4,
  "log_level": "INFO"
}
```

### 3.4 Running ASTRA from Claude Code

**Claude Code** is Anthropic's official CLI for Claude, providing direct integration with ASTRA for autonomous scientific research. This is the recommended method for running ASTRA with conversational AI assistance.

#### 3.4.1 What is Claude Code?

Claude Code is a command-line interface that:
- Provides direct access to Claude's advanced reasoning capabilities
- Enables autonomous execution of complex scientific workflows
- Integrates seamlessly with ASTRA's domain modules
- Supports collaborative human-AI research

#### 3.4.2 Installation

```bash
# Install Claude Code via npm
npm install -g @anthropic/claude-code

# Or via Homebrew (macOS)
brew install claude-code

# Verify installation
claude-code --version
```

#### 3.4.3 Configuration

Set up your Claude Code environment:

```bash
# Configure API credentials
claude-code config set api-key YOUR_ANTHROPIC_API_KEY

# Set ASTRA workspace
claude-code config set workspace /path/to/ASTRA

# Enable ASTRA integration
claude-code config set astra.enabled true
```

#### 3.4.4 Basic Usage

**Interactive Mode**:
```bash
# Start Claude Code with ASTRA
claude-code --astra

# Or navigate to ASTRA directory and start
cd /path/to/ASTRA
claude-code
```

**Direct Commands**:
```bash
# Ask ASTRA a question
claude-code "Using ASTRA, explain why filament widths cluster at 0.1 pc"

# Run autonomous research
claude-code "Use ASTRA's V7.0 autonomous scientist to study interstellar filaments"

# Generate publication
claude-code "Create a research paper on filament width analysis using ASTRA"
```

#### 3.4.5 ASTRA-Claude Code Integration Modes

##### Mode 1: Conversational Query

Ask ASTRA questions in natural language:

```bash
claude-code
> In ASTRA, analyze the relationship between black hole mass and galaxy bulge velocity
> ASTRA responds with analysis, confidence intervals, and physical interpretation
```

##### Mode 2: Autonomous Research

Let ASTRA conduct independent research:

```bash
claude-code
> Use ASTRA's V7.0 autonomous scientist to:
>   1. Generate research questions about galaxy evolution
>   2. Formulate testable hypotheses
>   3. Design observational tests
>   4. Execute analysis on SDSS data
>   5. Generate publication-ready results
```

##### Mode 3: Collaborative Analysis

Work alongside ASTRA on complex problems:

```bash
claude-code
> I have ALMA observations of molecular clouds. Help me:
>   - Load and calibrate the data
>   - Detect filaments using ASTRA's filament detection
>   - Measure filament widths
>   - Test the sonic scale hypothesis
>   - Create publication-quality figures
```

#### 3.4.6 Advanced Features

**Multi-Mind Reasoning**:
```bash
claude-code "Use ASTRA's physics mind to analyze this dataset"
claude-code "Apply ASTRA's creative mind to generate new hypotheses"
```

**Domain-Specific Analysis**:
```bash
claude-code "Load ASTRA's ISM domain and analyze Herschel data"
claude-code "Use ASTRA's exoplanet domain to characterize this transit light curve"
```

**Automated Publication**:
```bash
claude-code "Generate an A&A-formatted paper from this ASTRA analysis"
claude-code "Create figures and tables from ASTRA's filament width analysis"
```

#### 3.4.7 File Operations

ASTRA through Claude Code can:
- Read and analyze data files (FITS, CSV, HDF5)
- Generate output files (plots, tables, papers)
- Access domain modules and capabilities
- Execute Python scripts within ASTRA

```bash
claude-code "Analyze this FITS file using ASTRA: observations.fits"
claude-code "Save ASTRA's filament analysis results to filament_results.json"
```

#### 3.4.8 Best Practices

1. **Be Specific**: Provide clear context and objectives
2. **Use Domain Language**: ASTRA understands astrophysical terminology
3. **Iterate**: Refine queries based on intermediate results
4. **Leverage V7.0**: Use autonomous research for complex projects
5. **Verify Results**: Always check physical plausibility of outputs

#### 3.4.9 Troubleshooting Claude Code Integration

**Issue**: ASTRA not found by Claude Code

```bash
# Verify ASTRA path
claude-code config get workspace

# Set correct path
claude-code config set workspace /Users/gjw255/astrodata/SWARM/STAN_XI_ASTRO
```

**Issue**: Domain modules not loading

```bash
# Check ASTRA installation
python -c "import stan_core; print(stan_core.__version__)"

# Verify domain modules
python -c "from stan_core.domains import list_domains; print(list_domains())"
```

**Issue**: Memory errors with large datasets

```bash
# Increase memory limit
claude-code config set astra.memory_limit 32  # GB

# Use batch processing
claude-code "Process this data in batches of 1000 sources each"
```

#### 3.4.10 Example Session

```bash
$ claude-code --astra
ASTRA V7.0 initialized. Ready for autonomous research.

> Analyze why filament widths cluster at 0.1 pc using ASTRA

[ASTRA] Loading ISM domain...
[ASTRA] Analyzing filament width measurements from 10 studies...
[ASTRA] Mean width: 0.103 ± 0.008 pc across 5,476 filaments
[ASTRA] Testing sonic scale hypothesis...
[ASTRA] Confidence: 92% that sonic scale sets characteristic width

Result: The 0.1 pc width corresponds to the sonic scale of interstellar
turbulence, where turbulent velocity dispersion equals thermal sound speed.
This scale is density-independent because it depends on large-scale turbulent
properties rather than local density.

> Create publication-quality figure showing width vs. Mach number

[ASTRA] Generating parameter space plot...
[ASTRA] Saving to: filament_width_vs_mach.png
[ASTRA] Figure ready for publication

> Generate methods section for paper

[ASTRA] Writing methods section...
[ASTRA] Includes: filament detection, width measurement, statistical analysis
[ASTRA] Word count: 847
[ASTRA] Saved to: methods_section.tex
```

---

## 4. Getting Started

### 4.1 Your First Analysis

#### Example 1: Basic Query

```python
from stan_core import create_stan_system

# Create system
system = create_stan_system()

# Ask a question
result = system.answer("What is the typical temperature of a molecular cloud?")
print(result['answer'])
# Output: "Molecular clouds typically have temperatures in the range 10-20 K, 
# with most around 10-15 K. This is set by the balance between heating and 
# cooling processes..."
```

#### Example 2: Data Analysis

```python
# Load data
data = system.load_data("my_catalog.csv")

# Analyze scaling relation
result = system.discover_scaling_relation(
    data,
    x_variable="luminosity",
    y_variable="mass",
    question="How does luminosity scale with mass?"
)
```

### 4.2 Understanding ASTRA's Output

ASTRA provides structured output:

**Results**: Primary answer with precision and units
**Confidence**: Statistical confidence intervals
**Methodology**: Methods used and parameters
**Validation**: Physical constraint checks
**Provenance**: Complete processing record
**Recommendations**: Suggestions for further analysis

---

## 5. Core Capabilities Overview

ASTRA integrates 20+ analytical capabilities.

### 5.1 Causal and Statistical Analysis

#### 5.1.1 Bias Detection

Identifies and quantifies observational biases.

```python
result = system.detect_bias(
    data=galaxy_catalog,
    bias_type="malmquist",
    flux_column="apparent_magnitude"
)
```

#### 5.1.2 Scaling Relations Discovery

Automatically discovers physical scaling laws.

```python
result = system.discover_scaling_relation(
    data=cluster_data,
    x_variable="temperature",
    y_variable="luminosity"
)
# Output: L ∝ T^(2.5±0.3)
```

#### 5.1.3 Causal Inference

Discovers causal structures from data.

```python
result = system.perform_causal_inference(
    data=time_series,
    variables=["mass", "luminosity", "star_formation_rate"]
)
```

### 5.2 Data Integration and Analysis

#### 5.2.1 Multi-Wavelength Fusion

```python
result = system.fuse_multiwavelength(
    catalogs={
        "xray": xmm_catalog,
        "optical": hst_catalog,
        "ir": spitzer_catalog
    },
    matching_radius=2.0  # arcsec
)
```

---

## 6. V5.0 Discovery Enhancement System

### 6.1 Overview

V5.0 adds advanced discovery capabilities for genuine scientific discovery.

### 6.2 Capabilities

#### 6.2.1 Genuine Discovery Detection

```python
# Discover novel relationships
result = system.genuine_discovery(
    data=survey_data,
    knowledge_base="astrophysics_ontology",
    novelty_threshold=0.95
)
```

#### 6.2.2 Physical Model Discovery

```python
# Discover underlying physical models
result = system.discover_physical_model(
    data=observations,
    model_space=["power_law", "exponential", "broken_power_law"]
)
```

---

## 7. V7.0 Autonomous Research Scientist

### 7.1 Overview

The V7.0 Autonomous Research Scientist is a breakthrough system capable of conducting the **entire scientific research cycle**:

```
Question → Hypothesis → Experiment → Analysis → Theory → Publication
```

### 7.2 Core Components

#### 7.2.1 Question Generator

Generates important, novel research questions.

```python
from stan_core.v7_autonomous_research import create_v7_scientist

# Create autonomous scientist
scientist = create_v7_scientist()

# Generate research questions
questions = scientist.generate_research_questions(
    domain="interstellar_medium",
    context={"focus": "filament_widths"},
    num_questions=5
)

# Example output:
# Question 1: "What determines the characteristic width of 
# interstellar filaments across different density regimes?"
# Importance: CRITICAL
# Novelty: HIGH
```

#### 7.2.2 Hypothesis Formulator

Formulates testable hypotheses from questions.

```python
# Formulate hypotheses
hypotheses = scientist.formulate_hypotheses(
    question=questions[0],
    hypothesis_types=[HypothesisType.THEORETICAL, 
                     HypothesisType.EMPIRICAL]
)

# Example output:
# Hypothesis 1: "Filament width is set by the sonic scale of 
# turbulent cascade, where velocity dispersion equals thermal 
# sound speed (λ_sonic ≈ 0.1 pc for typical conditions)"
# Testability: HIGH
# Falsifiability: HIGH
```

#### 7.2.3 Experiment Designer

Designs experiments to test hypotheses.

```python
# Design experiment
experiment = scientist.design_experiment(
    hypothesis=hypotheses[0],
    experiment_type=ExperimentType.OBSERVATIONAL_TEST,
    constraints={"telescope": "ALMA", "time": "10_hours"}
)

# Example output:
# Experiment Design:
# - Target: 5 molecular clouds spanning density range 10^2-10^5 cm^-3
# - Observations: High-resolution N2H+ mapping
# - Measurements: Filament widths, velocity dispersions, temperatures
# - Required sensitivity: σ_N ≈ 10^11 cm^-2
# - Expected outcome: Width ∝ M^(-2) if sonic scale theory correct
```

#### 7.2.4 Experiment Executor

Executes experiments and collects results.

```python
# Execute experiment
results = scientist.execute_experiment(
    experiment=experiment,
    data_sources=["archival_Herschel", "new_ALMA_proposal"],
    analysis_pipeline=["filament_detection", "width_measurement"]
)

# Example output:
# Results:
# - 547 filaments measured across 5 clouds
# - Mean width: 0.103 ± 0.008 pc
# - Width vs. Mach number: ∝ M^(-0.84±0.15)
# - Comparison with prediction: Consistent within uncertainties
```

#### 7.2.5 Analysis Engine

Analyzes experimental results.

```python
# Analyze results
analysis = scientist.analyze_results(
    experiment=experiment,
    results=results,
    analysis_type=AnalysisType.CAUSAL_INFERENCE
)

# Example output:
# Analysis:
# - Causal relationship: Mach number → filament width
# - Confirmed: Sonic scale hypothesis (p < 0.001)
# - Effect size: Large (η² = 0.73)
# - Alternative hypotheses: Rejected (Bayes factor > 100)
```

#### 7.2.6 Theory Revision Engine

Revises theoretical understanding based on results.

```python
# Revise theory
theory = scientist.revise_theory(
    current_theory="sonic_scale_model",
    new_evidence=analysis,
    revision_type=RevisionType.PARAMETER_REFINEMENT
)

# Example output:
# Revised Theory:
# - Sonic scale prediction: λ ∝ M^(-2) → λ ∝ M^(-0.84±0.15)
# - Physical explanation: Magnetic fields and non-isothermal 
#   effects modify the pure sonic scale prediction
# - Domain of validity: M ∈ [1, 20], β ∈ [0.1, 10]
```

#### 7.2.7 Publication Engine

Generates publication-ready papers.

```python
# Generate publication
paper = scientist.generate_publication(
    research_cycle={
        "question": questions[0],
        "hypotheses": hypotheses,
        "experiment": experiment,
        "results": results,
        "analysis": analysis,
        "theory": theory
    },
    format="A&A",
    include_figures=True
)

# Output includes:
# - Complete paper text (introduction, methods, results, discussion)
# - Publication-quality figures
# - Tables with measurements
# - Acknowledgments and references
```

### 7.3 Complete Research Cycle Example

```python
from stan_core.v7_autonomous_research import create_v7_scientist

# Initialize autonomous scientist
scientist = create_v7_scientist()

# Conduct full research cycle
print("=" * 80)
print("AUTONOMOUS RESEARCH CYCLE: FILAMENT WIDTH MYSTERY")
print("=" * 80)

# Step 1: Generate questions
print("\n[STEP 1] Generating research questions...")
questions = scientist.generate_research_questions(
    domain="interstellar_medium",
    context={"focus": "filament_structure"},
    num_questions=3
)
for i, q in enumerate(questions, 1):
    print(f"  Q{i}: {q.text}")
    print(f"      Importance: {q.importance}")

# Step 2: Formulate hypotheses
print("\n[STEP 2] Formulating hypotheses...")
hypotheses = scientist.formulate_hypotheses(
    question=questions[0],
    num_hypotheses=3
)
for i, h in enumerate(hypotheses, 1):
    print(f"  H{i}: {h.text}")
    print(f"      Type: {h.type}")

# Step 3: Design experiment
print("\n[STEP 3] Designing experiment...")
experiment = scientist.design_experiment(
    hypothesis=hypotheses[0],
    experiment_type=ExperimentType.SIMULATION
)
print(f"  Experiment: {experiment.description}")
print(f"  Data required: {experiment.data_requirements}")

# Step 4: Execute experiment
print("\n[STEP 4] Executing experiment...")
results = scientist.execute_experiment(
    experiment=experiment,
    num_simulations=10,
    parameter_ranges={"M": [1, 20], "beta": [0.1, 10]}
)
print(f"  Simulations completed: {len(results.measurements)}")
print(f"  Key result: {results.summary}")

# Step 5: Analyze results
print("\n[STEP 5] Analyzing results...")
analysis = scientist.analyze_results(
    results=results,
    hypothesis=hypotheses[0]
)
print(f"  Statistical significance: {analysis.p_value}")
print(f"  Effect size: {analysis.effect_size}")
print(f"  Conclusion: {analysis.conclusion}")

# Step 6: Revise theory
print("\n[STEP 6] Revising theory...")
theory = scientist.revise_theory(
    analysis=analysis
)
print(f"  Revised prediction: {theory.predicted_relation}")
print(f"  Confidence: {theory.confidence}")

# Step 7: Generate publication
print("\n[STEP 7] Generating publication...")
paper = scientist.generate_publication(
    title="The Origin of the 0.1 pc Filament Width in Interstellar Clouds",
    abstract=analysis.summary,
    results=results,
    theory=theor
)
print(f"  Paper generated: {paper.filename}")
print(f"  Word count: {paper.word_count}")
print(f"  Figures: {len(paper.figures)}")

print("\n" + "=" * 80)
print("RESEARCH CYCLE COMPLETE")
print("=" * 80)
```

### 7.4 Research Modes

#### 7.4.1 Fully Autonomous Mode

```python
# Let ASTRA conduct research independently
result = scientist.conduct_autonomous_research(
    domain="your_choice",
    duration="medium",  # quick, medium, long
    output_format="publication"
)
```

#### 7.4.2 Guided Research Mode

```python
# Guide specific steps
result = scientist.conduct_guided_research(
    initial_question="Your question",
    guidance={
        "hypothesis": "suggest your own",
        "experiment": "use this data",
        "analysis": "focus on this aspect"
    }
)
```

#### 7.4.3 Collaborative Mode

```python
# Collaborate with ASTRA
result = scientist.collaborative_research(
    your_data="your_dataset",
    your_insights="your_hypotheses",
    astra_role="hypothesis_testing"  # or "data_analysis", "theory_development"
)
```

---

## 8. Use Case Examples

### 8.1 Interstellar Medium Analysis

**Question**: "Why do filament widths cluster at 0.1 pc?"

```python
from stan_core import create_stan_system

system = create_stan_system()

# Load Herschel data
herschel_data = system.load_data("herschel_filaments.fits")

# Analyze filament widths
result = system.analyze_filaments(
    data=herschel_data,
    analysis_type="width_distribution",
    compare_regions=["Aquila", "Polaris", "Taurus"]
)

# Output: Width = 0.103 ± 0.008 pc, independent of density
```

### 8.2 Exoplanet Detection

```python
# Detect exoplanets using radial velocity
result = system.detect_exoplanets(
    rv_data=hipparchos_timeseries,
    method="bayesian_periodogram",
    min_planets=1,
    max_planets=5
)
```

### 8.3 Galaxy Evolution

```python
# Study galaxy scaling relations
result = system.discover_scaling_relation(
    data=galaxy_catalog,
    x="stellar_mass",
    y="star_formation_rate",
    control_variables=["redshift", "environment"]
)
```

---

## 9. Advanced Features

### 9.1 Multi-Mind Orchestration

ASTRA V7.0 includes 7 specialized minds:

```python
# Query with specific mind
result = system.answer_with_mind(
    question="Explain filament formation",
    mind="physics"  # physics, empathy, politics, poetry, 
                    # mathematics, causal, creative
)
```

### 9.2 Global Coherence Layer

```python
# Ensure global coherence across analyses
result = system.coherent_analysis(
    questions=[
        "What causes filament width variations?",
        "How does magnetic field affect filaments?",
        "What is the role of turbulence?"
    ],
    coherence_threshold=0.8
)
```

---

## 10. Domain Modules

ASTRA includes 75 specialized domain modules.

### 10.1 Available Domains (75 Total)

ASTRA includes **75 specialized domain modules** organized into the following categories:

#### Stellar Astrophysics (8 domains)
- **stellar_structure**: Stellar structure and evolution models
- **stellar_atmospheres**: Stellar atmosphere modeling and spectroscopy
- **stellar_populations**: Stellar population synthesis and evolution
- **nuclear_astrophysics**: Nuclear processes in stars and nucleosynthesis
- **compact_binaries**: Binary star systems and compact objects
- **xray_binaries**: X-ray binary systems and accretion physics
- **supernovae**: Supernova explosions and remnants
- **exoplanet_atmospheres**: Exoplanet atmospheric characterization

#### Interstellar Medium & Star Formation (8 domains)
- **ism**: Interstellar medium physics and chemistry
- **molecular_cloud_dynamics**: Dynamics of molecular clouds
- **molecular_cloud_evolution**: Evolution and lifecycle of molecular clouds
- **molecular_cloud_collapse**: Gravitational collapse and core formation
- **star_formation**: Star formation processes and feedback
- **hii_regions**: HII region physics and evolution
- **dust_formation**: Dust formation and evolution in ISM
- **dust_grain_physics**: Dust grain properties and processes

#### Exoplanets & Solar System (4 domains)
- **exoplanets**: Exoplanet detection and characterization
- **planetary_formation**: Planet formation and disk evolution
- **solar_system**: Solar system dynamics and objects
- **orbital_dynamics**: Orbital mechanics and dynamics

#### High-Energy Astrophysics (5 domains)
- **high_energy**: High-energy processes and particles
- **agn**: Active galactic nuclei and quasars
- **gamma_ray**: Gamma-ray astronomy and sources
- **astroparticle**: Astrophysical particle physics
- **gravitational_waves**: Gravitational wave sources and detection

#### Galaxy Evolution & Structure (8 domains)
- **galaxy_evolution**: Galaxy formation and evolution
- **galaxy_clusters**: Galaxy cluster physics and dynamics
- **dwarf_galaxies**: Dwarf galaxy properties and evolution
- **galactic_structure**: Milky Way structure and dynamics
- **galactic_archaeology**: Stellar archaeology and chemical evolution
- **extragalactic**: Extragalactic astronomy and sources
- **intergalactic_medium**: Intergalactic medium physics
- **large_scale_structure**: Large-scale structure of universe

#### Compact Objects & Extreme Physics (7 domains)
- **black_holes**: Black hole physics and phenomena
- **accretion_disk_theory**: Accretion disk models and physics
- **tidal_disruption**: Tidal disruption events
- **kilonovae**: Kilonovae and r-process nucleosynthesis
- **general_relativity**: General relativistic effects
- **gravitational_lensing**: Gravitational lensing phenomena
- **frbs**: Fast radio bursts and transients

#### Observational Techniques & Wavelengths (12 domains)
- **radio_galactic**: Radio astronomy of Galactic sources
- **radio_extragalactic**: Radio astronomy of extragalactic sources
- **millimetre_astronomy**: Millimetre-wavelength astronomy
- **submillimeter_astronomy**: Submillimeter observations
- **infrared_astronomy**: Infrared observations and analysis
- **farinfrared_astronomy**: Far-infrared and Herschel data
- **interferometry**: Radio interferometry and synthesis imaging
- **polarimetry**: Polarimetric observations and analysis
- **astrometry**: Astrometric measurements and catalogues
- **time_domain**: Time-domain astronomy and transients
- **cmb**: Cosmic microwave background analysis
- **xray_binaries**: X-ray binary systems (also in stellar)

#### Theoretical & Computational Physics (10 domains)
- **theoretical_astrophysics**: Theoretical astrophysics methods
- **computational_astrophysics**: Computational methods and simulations
- **numerical_methods**: Numerical algorithms and techniques
- **mhd**: Magnetohydrodynamics and plasma physics
- **plasma_physics**: Plasma physics and processes
- **fluid_dynamics**: Fluid dynamics and hydrodynamics
- **statistical_mechanics**: Statistical mechanics applications
- **quantum_applications**: Quantum effects in astrophysics
- **solid_state_astro**: Solid-state physics in astronomy
- **dynamical_systems**: Dynamical systems theory

#### Radiation & Atomic Physics (6 domains)
- **radiative_processes**: Radiative processes and transfer
- **radiative_transfer_theory**: Radiative transfer modeling
- **photoionization**: Photoionization and PDR models
- **atomic_physics**: Atomic processes and data
- **molecular_spectroscopy**: Molecular spectroscopy and line lists
- **astrochemical_surveys**: Astrochemistry and molecular surveys

#### Solar & Heliospheric Physics (2 domains)
- **solar_physics**: Solar physics and phenomena
- **heliospheric_physics**: Heliospheric physics and solar wind

#### Specialized & Cross-Disciplinary (5 domains)
- **cosmology**: Cosmology and early universe
- **prebiotic_chemistry**: Prebiotic chemistry and origins of life
- **signal_processing**: Signal processing techniques
- **inverse_problems**: Inverse problems and deconvolution
- **hpc**: High-performance computing and parallelization

### 10.2 Using Domain Modules

```python
# Load specific domain
from stan_core.domains import load_domain

ism_domain = load_domain("ism")

# Query domain
result = ism_domain.process_query(
    query="Calculate Jeans length in molecular cloud",
    context={"density": 1e4, "temperature": 10}
)
```

---

## 11. API Reference

### 11.1 Main System API

```python
class STANSystem:
    """Main ASTRA system"""
    
    def answer(self, question: str) -> Dict:
        """Answer a natural language question"""
        
    def discover_scaling_relation(self, data, x, y) -> Dict:
        """Discover scaling relation"""
        
    def perform_causal_inference(self, data, variables) -> Dict:
        """Perform causal discovery"""
        
    def detect_bias(self, data, bias_type) -> Dict:
        """Detect observational biases"""
```

### 11.2 V7.0 API

```python
class V7AutonomousScientist:
    """Autonomous research scientist"""
    
    def generate_research_questions(self, domain, context) -> List:
        """Generate research questions"""
        
    def formulate_hypotheses(self, question) -> List:
        """Formulate hypotheses"""
        
    def design_experiment(self, hypothesis) -> Experiment:
        """Design experiment"""
        
    def execute_experiment(self, experiment) -> Results:
        """Execute experiment"""
        
    def analyze_results(self, results) -> Analysis:
        """Analyze results"""
        
    def generate_publication(self, research_cycle) -> Publication:
        """Generate publication"""
```

---

## 12. Best Practices

### 12.1 Data Preparation

- Use standard formats (FITS, CSV, HDF5)
- Include proper metadata
- Propagate uncertainties
- Document data provenance

### 12.2 Query Formulation

- Be specific about your question
- Provide context when relevant
- Specify desired output format
- Include constraints if applicable

### 12.3 Result Interpretation

- Always check confidence intervals
- Validate against physical expectations
- Consider alternative explanations
- Reproduce analyses independently

---

## 13. Troubleshooting

### 13.1 Common Issues

**Issue**: System returns low confidence results

**Solution**: 
- Provide more context
- Increase data quality
- Check for missing variables
- Consider alternative formulations

**Issue**: Memory errors with large datasets

**Solution**:
- Increase memory limit
- Use batch processing
- Reduce data resolution
- Enable memory-efficient algorithms

### 13.2 Getting Help

- Check GitHub issues
- Consult documentation
- Use verbose logging
- Contact developers

---

## 14. Appendices

### Appendix A: Complete Capability List

1. Bias Detection
2. Scaling Relations Discovery
3. Causal Inference
4. Model Selection
5. Multi-Wavelength Fusion
6. Uncertainty Quantification
7. Temporal Analysis
8. Instrument-Aware Analysis
9. Anomaly Detection
10. Ensemble Prediction
11. Physical Model Discovery
12. Bayesian Model Selection
13. Counterfactual Analysis
14. Causal Inference
15. Genuine Discovery Detection
16. **V7.0: Question Generation**
17. **V7.0: Hypothesis Formulation**
18. **V7.0: Experiment Design**
19. **V7.0: Experiment Execution**
20. **V7.0: Theory Revision**
21. **V7.0: Publication Generation**

### Appendix B: Domain Module List

[Complete list of 75 domain modules]

### Appendix C: Physical Constants

[Comprehensive list of physical constants used]

### Appendix D: Unit Conversions

[Unit conversion reference]

---

## Index

[Comprehensive index]

---

**Document Version**: 7.0
**Last Updated**: April 2026
**Authors**: Glenn J. White, Open University and Rutherford Appleton Laboratory, England
**License**: [License information]

For the latest version, visit: https://github.com/Tilanthi/ASTRA
