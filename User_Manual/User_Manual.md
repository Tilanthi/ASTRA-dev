# ASTRA User Manual
## Autonomous System for Scientific Discovery in Astrophysics

**Version**: 4.7
**Date**: April 2026
**Authors**: Glenn J. White & Robin Dey
**Repository**: https://github.com/Tilanthi/ASTRA

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [System Architecture](#2-system-architecture)
3. [Installation and Setup](#3-installation-and-setup)
4. [Getting Started](#4-getting-started)
5. [Core Capabilities Overview](#5-core-capabilities-overview)
6. [Use Case Examples](#6-use-case-examples)
7. [Advanced Features](#7-advanced-features)
8. [Domain Modules](#8-domain-modules)
9. [API Reference](#9-api-reference)
10. [Best Practices](#10-best-practices)
11. [Troubleshooting](#11-troubleshooting)
12. [Appendices](#12-appendices)

---

## 1. Introduction

### 1.1 What is ASTRA?

ASTRA (Autonomous System for Scientific Discovery in Astrophysics) is an integrated computational framework that combines numerical data analysis, causal reasoning, physical validation, and statistical inference to enable automated scientific discovery in astrophysics. Unlike traditional machine learning systems that detect patterns without understanding their physical meaning, or large language models that can explain concepts but cannot process numerical data, ASTRA integrates multiple analytical approaches to provide physically interpretable, validated scientific insights.

### 1.2 Key Design Principles

**Physics-Aware Reasoning**: All discoveries are validated against fundamental physical principles including conservation laws, dimensional consistency, and established theoretical frameworks.

**Causal Understanding**: ASTRA distinguishes between correlation and causation using structural causal models, enabling identification of physical mechanisms rather than mere associations.

**Uncertainty Quantification**: Every result includes properly propagated uncertainties, confidence intervals, and statistical significance assessments.

**Reproducibility**: All analyses are fully documented and reproducible, with complete provenance tracking from raw data to final conclusions.

**Modularity**: The system is organized into specialized components that can be used independently or combined for complex multi-step analyses.

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

### 1.4 Scope of This Manual

This manual covers:
- Complete system architecture and component organization
- Installation and configuration procedures
- Twenty detailed use case examples with natural language commands
- All core and advanced capabilities
- Domain module reference
- Best practices and troubleshooting

For implementation details, algorithm documentation, and source code, readers are referred to the GitHub repository and technical documentation.

---

## 2. System Architecture

### 2.1 Architectural Overview

ASTRA implements a layered architecture designed for astrophysical data analysis and inference. The system consists of approximately 303,000 lines of Python code organized into modular components that work together through coordinated interfaces.

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
│                    Foundation Layer                         │
│  Memory systems, I/O handling, numerical libraries         │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Core Components

#### 2.2.1 Physics Engine

The Physics Engine implements fundamental physical laws and constraints that govern all analyses:

**Conservation Laws**: Mass, energy, momentum, and charge conservation are enforced throughout all calculations. Discovered relations that violate these principles are automatically flagged for review.

**Dimensional Analysis**: The Buckingham π theorem is automatically applied to identify dimensionless parameters and ensure dimensional consistency of all equations and relationships.

**Equation Solving**: Numerical methods for solving differential equations, optimization problems, and constraint satisfaction problems.

**Units Management**: Automatic unit conversion, consistency checking, and dimensional analysis throughout all calculations.

**Physical Constraints**: Application of observational constraints such as resolution limits, sensitivity curves, and selection effects.

#### 2.2.2 Causal Reasoning Module

The Causal Reasoning Module enables discovery and inference of causal relationships from observational data:

**PC Algorithm**: The Peter-Spirtes causal discovery algorithm identifies causal structures from observational data by testing conditional independence relationships.

**Conditional Independence Testing**: Fisher's Z-test and other statistical tests determine whether variables are independent given conditioning sets.

**V-Structure Detection**: Identifies colliders in causal graphs, which are crucial for distinguishing causal directions.

**Do-Calculus**: Predicts effects of interventions using Pearl's calculus of intervention.

**Domain Adaptations**: Astrophysical domain knowledge constrains the search space to physically plausible causal structures.

#### 2.2.3 Bayesian Inference Engine

The Bayesian Inference Engine provides rigorous model comparison and uncertainty quantification:

**Evidence Computation**: Marginal likelihood estimation using bridge sampling, thermodynamic integration, and other advanced Monte Carlo methods.

**Bayes Factors**: Model comparison using ratios of evidences, with automatic interpretation using Kass-Raftery guidelines.

**Occam's Razor**: Automatic complexity penalty prevents overfitting by favoring simpler models when fit is comparable.

**Posterior Predictive Checking**: Validates model predictions against observed data to detect model inadequacy.

**Markov Chain Monte Carlo**: Advanced sampling algorithms for posterior exploration and parameter estimation.

#### 2.2.4 Data Processing Pipeline

The Data Processing Pipeline handles ingestion, validation, and preparation of astronomical data:

**Format Support**: CSV, FITS, HDF5, JSON, and astropy Tables for catalogs; time-series formats; image formats; spectral data formats.

**Validation**: Automatic validation of data formats, units, value ranges, and required metadata.

**Cleaning**: Outlier detection, missing value handling, and quality flag processing.

**Normalization**: Coordinate system transformations, unit conversions, and standardization procedures.

**Uncertainty Preservation**: Measurement uncertainties and error correlations are preserved through all transformations.

#### 2.2.5 Domain Knowledge Systems

Organized astrophysical knowledge provides context for all analyses:

**MORK Ontology**: Hierarchical encoding of astronomical concepts, relationships, and causal structures.

**Knowledge Graphs**: Semantic networks representing relationships between astronomical objects, phenomena, and theories.

**Vector Memory**: Embedding-based retrieval of related concepts and prior analyses.

**Domain Modules**: Seventy-five specialized modules for specific astrophysical domains (ISM, star formation, exoplanets, etc.).

### 2.3 Memory Systems

ASTRA implements multiple complementary memory systems:

#### 2.3.1 Working Memory

Short-term storage with 7±2 item capacity limit, implementing cognitive constraints on simultaneous information processing. Automatic management of information flow based on attention and relevance.

#### 2.3.2 Episodic Memory

Storage of specific analyses and their contexts, enabling retrieval of previous similar cases and their outcomes. Includes provenance tracking for all results.

#### 2.3.3 Semantic Memory

General astronomical knowledge including physical laws, typical parameter ranges, and established relationships. Automatically updated from successful analyses.

#### 2.3.4 Procedural Memory

Learned procedures and workflows that have proven effective for specific analysis types. Enables automatic adaptation of analysis strategies based on problem characteristics.

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

Clone the repository and install dependencies:

```
Clone the ASTRA repository from GitHub
Navigate to the cloned directory
Install ASTRA using pip with editable mode for development
Install optional dependencies for full functionality
```

#### 3.2.2 Verification of Installation

After installation, verify that ASTRA is correctly installed:

```
Open a Python interpreter or Jupyter notebook
Import the core ASTRA module
Create a system instance
Query the system status
```

Expected output includes version information, available capabilities, and system status.

### 3.3 Configuration

#### 3.3.1 Basic Configuration

ASTRA uses a configuration file for customizable settings:

```
Create a configuration file in your home directory
Set default data directories
Configure memory limits
Specify preferred computational backends
```

#### 3.3.2 Domain Module Loading

Domain modules can be loaded on-demand to reduce startup time:

```
Load only required domains for your analysis
Preload frequently used domains for faster access
Customize domain parameters for specific research areas
```

#### 3.3.3 Computational Resources

Configure ASTRA to use available computational resources:

```
Set the number of parallel worker processes
Enable GPU acceleration if available
Configure memory limits for large datasets
Set timeout values for long-running analyses
```

---

## 4. Getting Started

### 4.1 Your First Analysis

The simplest way to use ASTRA is through the unified interface:

```
Create an ASTRA system instance
Load your astronomical data
Ask ASTRA to analyze the data
Review the results including confidence assessments
```

ASTRA will automatically select appropriate analysis methods based on the data characteristics and your question.

### 4.2 Understanding ASTRA's Output

ASTRA provides structured output for every analysis:

**Results**: The primary answer to your question, with appropriate precision and units

**Confidence**: Statistical confidence intervals or uncertainty bounds

**Methodology**: Description of methods used, including algorithm choices and parameter values

**Validation**: Checks performed against physical constraints and domain knowledge

**Provenance**: Complete record of data processing steps from raw input to final result

**Recommendations**: Suggestions for further analysis or validation when appropriate

### 4.3 Interactive vs. Batch Processing

ASTRA supports both interactive exploration and batch processing:

**Interactive Mode**: Best for exploratory analysis, Jupyter notebooks, and rapid prototyping

**Batch Mode**: Best for large-scale processing, automated pipelines, and production analyses

### 4.4 Common First Tasks

New users typically start with these tasks:

```
Load and explore a familiar dataset
Perform basic statistical characterization
Test specific hypotheses about the data
Generate visualizations of results
Export results for further analysis or publication
```

---

## 5. Core Capabilities Overview

ASTRA integrates sixteen distinct analytical capabilities. These capabilities can be used individually or combined for complex multi-step analyses.

### 5.1 Causal and Statistical Analysis

#### 5.1.1 Bias Detection

ASTRA identifies and quantifies observational biases that can affect scientific conclusions. Common biases include Malmquist bias, selection effects, and incompleteness.

**What it does**: Detects biases from survey geometry, flux limits, and selection criteria

**When to use**: When working with flux-limited surveys, magnitude-limited samples, or any dataset with non-uniform selection

**Output**: Quantified bias magnitude, corrected estimates, physical interpretation

#### 5.1.2 Scaling Relations Discovery

Automatically discovers physical scaling laws from observational data using dimensional analysis and functional form detection.

**What it does**: Identifies power-law, logarithmic, or broken power-law relationships between physical quantities

**When to use**: When exploring correlations between physical variables in astrophysical systems

**Output**: Discovered scaling relation, statistical significance, physical validation against theory

#### 5.1.3 Causal Inference

Discovers causal structures from observational data using the PC algorithm and related methods.

**What it does**: Identifies causal relationships between variables, distinguishes physical laws from spurious correlations

**When to use**: When you need to understand cause-and-effect relationships in your data

**Output**: Causal graph, confidence in causal relationships, identification of confounding variables

#### 5.1.4 Model Selection

Compares competing scientific theories using Bayesian evidence computation.

**What it does**: Computes Bayes factors comparing models, implements automatic Occam's razor

**When to use**: When choosing between competing physical models or theoretical frameworks

**Output**: Model rankings, Bayes factors with interpretation, predictive performance

### 5.2 Data Integration and Analysis

#### 5.2.1 Multi-Wavelength Fusion

Cross-matches sources across multiple wavelength observations with proper uncertainty propagation.

**What it does**: Matches sources, combines measurements, classifies based on multi-wavelength properties

**When to use**: When working with data from multiple telescopes or wavelength regimes

**Output**: Matched source catalog, combined measurements, source classifications

#### 5.2.2 Uncertainty Quantification

Propagates measurement uncertainties through all analyses, separating systematic and statistical components.

**What it does**: First-order error propagation, Monte Carlo methods, systematic error estimation

**When to use**: For any analysis where measurement uncertainties are important

**Output**: Results with confidence intervals, uncertainty budgets, error correlation matrices

#### 5.2.3 Temporal Reasoning

Analyzes time-series data to detect periodic signals, transients, and trends.

**What it does**: Period detection, phase folding, transient detection, forecasting

**When to use**: With light curves, radial velocity curves, or any time-series astronomical data

**Output**: Period measurements, classifications, transient detections, forecasts with uncertainties

#### 5.2.4 Instrument-Aware Analysis

Evaluates observational requirements and compatibility across multiple astronomical facilities.

**What it does**: Assesses whether instruments can observe targets, calculates signal-to-noise ratios

**When to use**: When planning observations or selecting appropriate instruments for targets

**Output**: Feasibility assessments, optimal instrument selection, exposure time calculations

### 5.3 Knowledge Generation

#### 5.3.1 Hypothesis Generation

Identifies patterns in data and generates novel testable hypotheses with specific observational requirements.

**What it does**: Pattern recognition, anomaly detection, hypothesis formulation, testability assessment

**When to use**: When exploring new datasets or looking for novel phenomena

**Output**: Generated hypotheses, testability ratings, required observations for validation

#### 5.3.2 Analogical Reasoning

Discovers structural similarities between different astrophysical systems based on shared physics.

**What it does**: Structural mapping between systems, physics-based analogy identification

**When to use**: When applying insights from one astrophysical domain to another

**Output**: Discovered analogies, confidence assessments, predictive applications

#### 5.3.3 Counterfactual Analysis

Simulates physically-grounded scenarios to predict effects of interventions or observational changes.

**What it does**: Simulates "what if" scenarios with proper physical constraints

**When to use**: When predicting effects of observational changes or theoretical interventions

**Output**: Simulated outcomes, physical consistency checks, quantitative predictions

#### 5.3.4 Physical Model Discovery

Automatically identifies functional forms and validates against theoretical predictions.

**What it does**: Dimensional analysis, automatic model discovery, theory validation

**When to use**: When discovering physical relationships from data

**Output**: Discovered models, theoretical validation, comparison to established theory

### 5.4 Meta-Cognitive Capabilities

#### 5.4.1 Meta-Cognitive Evaluation

Provides quantitative assessments of data sufficiency, resolution limits, and observational constraints.

**What it does**: Evaluates whether data are sufficient for specific scientific questions

**When to use**: Before committing to extensive analysis or when results are inconclusive

**Output**: Sufficiency assessments, specific limitations, recommendations for improvement

#### 5.4.2 Anomaly Detection

Identifies unusual objects using ensemble methods combining multiple detection approaches.

**What it does**: Multi-method anomaly detection, interpretation of anomalous features

**When to use**: When searching for rare or unusual objects in large datasets

**Output**: Anomaly scores, classifications, physical interpretation of anomalies

#### 5.4.3 Ensemble Prediction

Combines multiple models using Bayesian Model Averaging for robust predictions.

**What it does**: Model combination, weight optimization, robust uncertainty quantification

**When to use**: When making predictions with multiple plausible models

**Output**: Ensemble predictions, improved uncertainties, model contribution analysis

#### 5.4.4 Physical Validation

Checks all results against dimensional consistency, conservation laws, and established principles.

**What it does**: Validates results against physical constraints, flags potential issues

**When to use**: Automatically for all analyses; essential for novel discoveries

**Output**: Validation status, identified issues, physical consistency checks

---

## 6. Use Case Examples

The following examples demonstrate typical ASTRA workflows using natural language descriptions. These examples illustrate how to interact with ASTRA for common astronomical analysis tasks.

### Example 1: Discovering Scaling Relations in Molecular Cloud Filaments

**Task**: Discover physical relationships between filament properties from Herschel observations

**Natural Language Command**:
```
Load the Herschel filament catalog with mass, length, and velocity dispersion measurements
Discover any scaling relations between these quantities using dimensional analysis
Validate discovered relations against the virial theorem prediction
Quantify uncertainties using bootstrap resampling
Generate plots showing the discovered relationships with confidence bands
```

**What ASTRA Does**:
- Performs dimensional analysis to identify relevant dimensionless parameters
- Searches for power-law, logarithmic, and broken power-law relationships
- Tests discovered relations against theoretical predictions from virial theorem
- Computes confidence intervals using bootstrap methods
- Creates publication-quality visualizations

**Expected Output**:
- Discovered scaling relation: σ_v ∝ √(M/L)
- Statistical significance: r = 0.988, p < 10^-18
- Agreement with virial theorem: 88%
- Universal width: 0.098 ± 0.019 pc
- Plots with data, fit, and confidence intervals

### Example 2: Identifying Malmquist Bias in Gaia Data

**Task**: Detect and quantify Malmquist bias in a stellar sample

**Natural Language Command**:
```
Load the Gaia DR2 catalog with 10,000 stars including distance and luminosity data
Test for correlation between distance and luminosity that would indicate Malmquist bias
Quantify the magnitude of the bias in magnitudes
Create volume-limited subsamples to verify the bias interpretation
Generate visualizations showing the bias effect and corrected distributions
```

**What ASTRA Does**:
- Computes correlation between distance and luminosity
- Tests statistical significance of detected correlation
- Calculates bias magnitude in magnitudes
- Creates volume-limited samples for verification
- Separates physical from selection effects

**Expected Output**:
- Detected correlation: r = 0.025, p = 0.012
- Bias magnitude: -13.12 magnitudes
- Interpretation: Severe Malmquist bias affecting sample
- Corrected luminosity function
- Diagnostic plots showing bias effect

### Example 3: Cross-Matching Multi-Wavelength Sources

**Task**: Match sources across X-ray, optical, and infrared catalogs

**Natural Language Command**:
```
Load the Chandra Deep Field South X-ray source catalog
Load the HST optical source catalog
Load the infrared source catalog
Cross-match sources across all three wavelengths using Bayesian likelihood methods
Propagate astrometric uncertainties through the matching process
Classify matched sources based on their multi-wavelength properties
Generate completeness and reliability statistics for the matching
```

**What ASTRA Does**:
- Computes Bayesian likelihood ratios for source matching
- Properly propagates astrometric uncertainties
- Uses physics-based classification criteria
- Calculates completeness and reliability metrics
- Identifies unmatched sources and investigates reasons

**Expected Output**:
- 60 matched sources across all three wavelengths
- Classification: 41 AGN, 19 stars
- Match quality statistics with confidence assessments
- Plots of multi-wavelength properties
- Unmatched source analysis

### Example 4: Generating Novel Hypotheses from Galaxy Data

**Task**: Generate testable hypotheses from SDSS galaxy properties

**Natural Language Command**:
```
Load the SDSS galaxy catalog with stellar mass, star formation rate, metallicity, and environment
Identify patterns and correlations in the high-dimensional parameter space
Detect unusual objects that don't follow typical relationships
Generate specific testable hypotheses based on identified patterns
Assess testability of each hypothesis and identify required observations
Rank hypotheses by scientific interest and feasibility
```

**What ASTRA Does**:
- Performs correlation analysis across all parameters
- Identifies outliers and unusual objects
- Formulates specific, testable hypotheses
- Assesses feasibility of testing each hypothesis
- Ranks by potential scientific impact

**Expected Output**:
- Five novel testable hypotheses:
  1. Metallicity-luminosity correlation evolution
  2. Environment-driven star formation quenching
  3. AGN feedback in low-mass galaxies
  4. Merger rate vs redshift relation
  5. Dark matter halo scaling laws
- Testability assessments for each
- Required observational data for validation
- Scientific impact ranking

### Example 5: Discovering Causal Structures in Stellar Data

**Task**: Infer causal relationships between stellar properties

**Natural Language Command**:
```
Load the Gaia DR2 stellar catalog with distance, parallax, apparent magnitude, absolute magnitude, and luminosity
Apply the PC algorithm to discover causal structures
Test conditional independence relationships
Identify v-structures (colliders) in the causal graph
Distinguish physical causal relationships from selection biases
Perform intervention analysis using do-calculus
Visualize the discovered causal structure
```

**What ASTRA Does**:
- Applies PC algorithm with appropriate significance thresholds
- Tests conditional independence using Fisher's Z-test
- Detects v-structures for causal direction identification
- Distinguishes physical from spurious relationships
- Predicts effects of interventions

**Expected Output**:
- Causal graph showing relationships:
  - absolute_mag → luminosity (definition, correctly identified)
  - distance → apparent_magnitude (physical law, detected)
  - distance × luminosity (confounding, correctly identified)
- V-structures identified
- Intervention predictions
- Causal visualization

### Example 6: Bayesian Model Selection for Scaling Relations

**Task**: Compare competing models for filament scaling relations

**Natural Language Command**:
```
Load the Herschel filament data with velocity dispersion and mass/length measurements
Define four competing models: power law, linear, logarithmic, and broken power law
Compute Bayesian evidence for each model using bridge sampling
Calculate Bayes factors comparing all models to the power-law model
Apply automatic complexity penalty (Occam's razor)
Perform posterior predictive checks for the best model
Validate the best model against virial theorem predictions
Generate model comparison plots with evidence values
```

**What ASTRA Does**:
- Fits all four models to the data
- Computes marginal likelihood for each model
- Calculates Bayes factors with proper interpretation
- Applies complexity penalty
- Performs posterior predictive checks
- Validates against physical theory

**Expected Output**:
- Model comparison table:
  - Power law: log evidence = -35.18 (reference)
  - Linear: log evidence = -45.59, Bayes factor = 1/33,000
  - Logarithmic: log evidence = -35.36, Bayes factor = 1/1.2
  - Broken power: log evidence = -46.91, Bayes factor = 1/123,000
- Power law strongly favored
- Validation: 70% agreement with virial theorem
- Model comparison visualizations

### Example 7: Period Detection in Variable Star Light Curves

**Task**: Detect and characterize periodic signals in time-series data

**Natural Language Command**:
```
Load the light curve data for eclipsing binary candidates
Apply Lomb-Scargle periodogram to detect periodic signals
Identify significant peaks above the false alarm probability threshold
Fold the light curve at the best-fit period
Classify the variable type based on period and light curve shape
Estimate uncertainty in the period measurement
Forecast future epochs of minimum light
Generate diagnostic plots including periodogram and folded light curve
```

**What ASTRA Does**:
- Computes Lomb-Scargle periodogram across frequency range
- Calculates false alarm probabilities
- Identifies significant periods
- Performs phase folding
- Classifies variable type
- Propagates timing uncertainties
- Predicts future events

**Expected Output**:
- Detected period: 3.456 ± 0.002 days
- False alarm probability: < 10^-10
- Classification: Eclipsing binary
- Ephemeris for future minima
- Periodogram and folded light curve plots

### Example 8: Anomaly Detection in Large Stellar Catalogs

**Task**: Identify unusual objects in the Gaia catalog

**Natural Language Command**:
```
Load the Gaia DR2 catalog with 9,851 stars
Apply ensemble of anomaly detection methods: isolation forest, local outlier factor, and one-class SVM
Combine results from multiple methods using Bayesian model averaging
Identify high-confidence anomalies with agreement across methods
Characterize the physical properties of detected anomalies
Investigate potential explanations for each anomaly
Generate anomaly ranking with interpretation
```

**What ASTRA Does**:
- Applies multiple anomaly detection algorithms
- Combines results using ensemble methods
- Identifies high-confidence anomalies
- Analyzes physical properties
- Provides physical interpretation

**Expected Output**:
- 115 high-confidence anomalies detected
- Anomaly types:
  - 45 high proper motion stars
  - 30 unusual color indices
  - 25 parallax outliers
  - 15 magnitude anomalies
- Physical characterization of each anomaly
- Investigative leads for follow-up

### Example 9: Instrument Selection for Target Observations

**Task**: Determine optimal instruments for observing exoplanet atmospheres

**Natural Language Command**:
```
Define the target: exoplanet atmosphere transmission spectroscopy
Specify target properties: host star magnitude, planetary radius, orbital period
Load instrument specifications for HST, JWST, VLT, and Keck
Calculate signal-to-noise ratios for each instrument
Assess feasibility of detecting molecular features
Consider wavelength coverage, spectral resolution, and sensitivity
Rank instruments by scientific return and observational efficiency
Provide exposure time estimates for feasible instruments
```

**What ASTRA Does**:
- Loads instrument specifications from database
- Calculates SNR for each instrument-target combination
- Assesses feature detectability
- Considers practical constraints
- Ranks options by multiple criteria

**Expected Output**:
- Instrument rankings:
  1. JWST NIRSpec: SNR = 25, 5 features detectable, 4 hours
  2. HST WFC3: SNR = 12, 2 features detectable, 10 hours
  3. VLT X-Shooter: SNR = 8, 1 feature detectable, 8 hours
- Detailed feasibility assessment
- Exposure time calculations
- Scientific return estimates

### Example 10: Counterfactual Analysis of Survey Depth

**Task**: Predict how sample would change with deeper observations

**Natural Language Command**:
```
Load the current magnitude-limited stellar sample
Define counterfactual scenarios: deeper magnitude limits, improved astrometry, different wavelength coverage
Simulate each scenario with proper physical models
Predict which additional stars would be detected in each scenario
Quantify selection effects and bias changes
Compare physical properties of samples under different scenarios
Generate visualizations showing sample evolution with depth
```

**What ASTRA Does**:
- Applies physical models for stellar populations
- Simulates detection under different conditions
- Tracks selection effects through all scenarios
- Compares sample properties systematically
- Quantifies bias evolution

**Expected Output**:
- Scenario 1 (2 magnitudes deeper):
  - Additional 2,500 stars detected
  - Sample extends to 800 pc
  - Malmquist bias reduced by 40%
- Scenario 2 (improved astrometry):
  - Distance precision: 3.3% → 1.7%
  - Parallax outliers reduced by 60%
- Bias evolution plots
- Sample comparison statistics

### Example 11: Physical Model Discovery from Observational Data

**Task**: Automatically discover the functional form of a physical relationship

**Natural Language Command**:
```
Load the dataset with two correlated physical quantities
Perform dimensional analysis to identify dimensionless parameters
Automatically search across functional forms: power laws, exponentials, logarithms
Compare models using information criteria (AIC, BIC)
Validate the best model against physical constraints
Test whether discovered relationship matches theoretical predictions
Quantify agreement between data and theory
```

**What ASTRA Does**:
- Identifies dimensionless parameters using π theorem
- Searches functional form space automatically
- Compares models using multiple criteria
- Validates against physical constraints
- Tests theoretical predictions

**Expected Output**:
- Discovered model: power law with sqrt transformation
- R² = 0.977, best among tested forms
- Dimensionless parameter: Π = 1.012 ± 0.087
- Theoretical prediction: Π = √2 = 1.414
- Agreement: 72%
- Physical interpretation: consistent with virial equilibrium

### Example 12: Analogical Reasoning Between Astrophysical Systems

**Task**: Discover structural similarities between different astrophysical systems

**Natural Language Command**:
```
Define source systems: black hole accretion disks and protostellar infall
Extract structural features: mass flow geometry, energy transport, timescales
Identify shared physics principles between systems
Map structural correspondences
Test whether predictions transfer successfully between systems
Generate novel insights from the discovered analogies
Validate predictions against observational data
```

**What ASTRA Does**:
- Extracts structural features from each system
- Identifies shared underlying physics
- Creates structural mappings
- Tests transferability of predictions
- Generates new insights from analogies

**Expected Output**:
- Discovered structural mapping:
  - Accretion disk → Protostellar envelope (mass flow geometry)
  - Jet launching → Outflow launching (magnetic fields)
  - Variability timescales → Episodic accretion (gravitational instability)
- Shared physics: gravity, magnetohydrodynamics
- Transferable predictions: 5 confirmed
- New insights: 3 novel predictions

### Example 13: Ensemble Prediction Combining Multiple Models

**Task**: Combine multiple stellar evolution models for robust predictions

**Natural Language Command**:
```
Load results from three different stellar evolution codes
Define the prediction task: main sequence lifetime as function of mass
Assess model performance on validation dataset
Calculate Bayesian model averaging weights based on predictive performance
Generate ensemble predictions combining all three models
Quantify uncertainty including model uncertainty
Compare ensemble performance to individual models
```

**What ASTRA Does**:
- Validates each model on held-out data
- Calculates BMA weights from predictive likelihoods
- Combines predictions with weight uncertainty
- Separates model uncertainty from parametric uncertainty
- Assesses improvement over individual models

**Expected Output**:
- Model weights:
  - Model A: 0.45 ± 0.08
  - Model B: 0.35 ± 0.07
  - Model C: 0.20 ± 0.05
- Ensemble RMSE: 12% lower than best single model
- Uncertainty properly inflated by model disagreement
- Predictions with 95% confidence intervals

### Example 14: Meta-Cognitive Assessment of Data Sufficiency

**Task**: Evaluate whether data are sufficient to answer specific scientific questions

**Natural Language Command**:
```
Define the scientific question: What is the star formation history of this galaxy?
Load the available observational data: photometry, limited spectroscopy
Assess whether current data can constrain star formation history
Identify specific limitations: wavelength coverage, spectral resolution, age sensitivity
Quantify the degeneracies in current parameter constraints
Recommend additional observations that would most improve constraints
Provide specific metrics for data sufficiency
```

**What ASTRA Does**:
- Analyzes information content of available data
- Identifies parameter degeneracies
- Quantifies constraints on star formation history
- Assesses age-metallicity degeneracy
- Recommends optimal additional observations

**Expected Output**:
- Sufficiency assessment: 60% sufficient for basic SFH
- Main limitations: spectral resolution, age-sensitive features
- Current constraints: formation epoch 8-11 Gyr ago, large uncertainty
- Recommended additions:
  - Higher resolution spectroscopy (R > 10,000)
  - UV coverage for young populations
- Expected improvement with additions: 85% sufficiency

### Example 15: Multi-Epoch Transient Detection and Classification

**Task**: Detect and classify transient events in time-domain survey data

**Natural Language Command**:
```
Load multi-epoch survey data with thousands of observations
Identify sources that show significant brightness variations
Separate variables from transients based on light curve shape
Classify transients using photometric and temporal features
Estimate distances using standard candle relations or host galaxy redshifts
Calculate luminosities and compare to known transient classes
Identify unusual transients that don't fit standard classifications
Generate alerts for high-priority candidates
```

**What ASTRA Does**:
- Performs statistical change detection
- Separates periodic from transient behavior
- Classifies using feature-based machine learning
- Estimates distances with proper uncertainty
- Compares to known transient populations
- Identifies outliers for special attention

**Expected Output**:
- 45 transients detected
- Classifications:
  - 20 supernovae (Type Ia: 12, Type II: 8)
  - 15 classical novae
  - 5 tidal disruption events
  - 3 unknown/unusual
- Distance estimates for all transients
- 2 high-priority unusual candidates flagged

### Example 16: Spectral Energy Distribution Fitting with Physical Models

**Task**: Fit galaxy spectral energy distributions with stellar population synthesis

**Natural Language Command**:
```
Load multi-wavelength photometry from UV to far-infrared
Define grid of stellar population synthesis models
Include dust attenuation and emission components
Fit SEDs using Bayesian inference with proper likelihoods
Generate posterior distributions for physical parameters
Identify degeneracies between parameters
Compare different model assumptions
Assess model adequacy using posterior predictive checks
```

**What ASTRA Does**:
- Fits full UV-FIR SEDs with physical models
- Explores full posterior distribution
- Identifies parameter degeneracies
- Compares star formation histories
- Tests different dust models
- Validates model fit quality

**Expected Output**:
- Physical parameters with posteriors:
  - Stellar mass: 10^10.5 ± 0.2 M_sun
  - Star formation rate: 15 ± 3 M_sun/yr
  - Dust attenuation: A_V = 1.2 ± 0.3 mag
- Identified degeneracy: mass-SFR-dust
- Model comparison: delayed vs. burst SFH
- Posterior predictive checks: adequate fit

### Example 17: Galaxy Cluster Analysis with Multi-Component Modeling

**Task**: Analyze galaxy cluster properties using multi-wavelength data

**Natural Language Command**:
```
Load X-ray data from Chandra observation of galaxy cluster
Load optical spectroscopy of cluster members
Load Sunyaev-Zel'dovich effect measurements
Fit X-ray surface brightness profile to determine cluster mass
Analyze velocity dispersion of member galaxies
Combine mass estimates from different methods using Bayesian hierarchal model
Test for hydrostatic equilibrium
Compare cluster properties to scaling relations
Identify merging or disturbed systems
```

**What ASTRA Does**:
- Fits X-ray profiles to derive mass profiles
- Analyzes galaxy velocity distributions
- Combines mass measurements hierarchically
- Tests dynamical state
- Compares to cluster scaling relations
- Identifies merging systems

**Expected Output**:
- Cluster mass: M_500 = 2.5 ± 0.4 × 10^14 M_sun
- Velocity dispersion: 650 ± 50 km/s
- Combined mass estimate from all methods
- Hydrostatic test: consistent within 20%
- Comparison to mass-temperature relation: 1.1σ outlier
- Dynamical state: possibly disturbed

### Example 18: Exoplanet Transit Analysis with Atmospheric Retrieval

**Task**: Analyze transit light curves and perform atmospheric retrieval

**Natural Language Command**:
```
Load high-precision transit light curves from multiple observatories
Fit transit model to derive planetary radius, orbital inclination, and stellar density
Perform joint fit with radial velocity data for planetary mass
Search for transit timing variations
Perform atmospheric retrieval from transmission spectroscopy
Generate posterior distributions for atmospheric parameters
Compare atmospheric composition to equilibrium chemistry models
Assess detectability of specific molecular species
Predict requirements for future observations
```

**What ASTRA Does**:
- Fits transit models with limb-darkening
- Combines transit and radial velocity data
- Searches for TTVs indicating additional planets
- Performs atmospheric retrieval using forward models
- Compares to chemical equilibrium predictions
- Assesses feasibility of detecting specific molecules

**Expected Output**:
- Planetary parameters:
  - Radius: 1.15 ± 0.02 R_Jup
  - Mass: 0.85 ± 0.05 M_Jup
  - Density: 0.56 ± 0.04 g/cm³
- No significant TTVs detected
- Atmospheric retrieval:
  - H2O: 3.2 × 10^-5 ± 30%
  - CO2: < 10^-6 (upper limit)
- Detectability predictions for JWST

### Example 19: Gravitational Lens Modeling and Time Delay Cosmography

**Task**: Model strong gravitational lens system for cosmography

**Natural Language Command**:
```
Load HST images of strong lensing system with multiple images and arcs
Identify lensing galaxy and background source components
Construct lens model using mass profile parameterization
Fit model to observed image positions and flux ratios
Extract time delays between multiple images if monitored
Use time delays and mass model to constrain Hubble constant
Quantify systematic uncertainties from mass profile shape
Combine with other lens systems for improved constraints
```

**What ASTRA Does**:
- Models lens mass distribution
- Fits to image positions and flux ratios
- Incorporates stellar velocity dispersion if available
- Extracts time delays from light curves
- Performs cosmological inference
- Assesses systematic uncertainties

**Expected Output**:
- Lens model parameters:
  - Einstein radius: 1.45 ± 0.03 arcsec
  - Mass profile slope: 2.05 ± 0.08
- Time delays: Δt_AB = 45 ± 3 days
- Derived Hubble constant: H0 = 72 ± 6 km/s/Mpc
- Systematic uncertainty assessment
- Combination with other lenses

### Example 20: Population Synthesis and Inference

**Task**: Infer population properties from observed sample with selection effects

**Natural Language Command**:
```
Load observed sample of stellar mergers from gravitational wave detections
Define population model: mass distribution, merger rate, redshift evolution
Simulate detection process including detector sensitivity and selection effects
Use hierarchical Bayesian inference to infer true population parameters
Account for selection bias and measurement uncertainties
Compare inferred population to theoretical predictions
Forecast detection rates for future detector upgrades
Identify features that would discriminate between formation channels
```

**What ASTRA Does**:
- Constructs population models
- Simulates full detection pipeline
- Performs hierarchical Bayesian inference
- Properly accounts for selection effects
- Compares to astrophysical predictions
- Forecasts future detections

**Expected Output**:
- Inferred population parameters:
  - Primary mass: 35 ± 5 M_sun
  - Mass ratio: 0.7 ± 0.2
  - Merger rate: 15 ± 5 Gpc^-3 yr^-1
- Evidence for mass gap objects: 3σ
- Comparison to formation channel predictions
- Forecasts for O4 and O5 observing runs

---

## 7. Advanced Features

### 7.1 Custom Analysis Workflows

ASTRA allows users to define custom workflows combining multiple capabilities:

```
Define a custom workflow that sequences multiple analysis steps
Specify input data requirements for each step
Configure how results flow between steps
Add custom validation or quality control checks
Save the workflow for reuse or sharing
```

### 7.2 Distributed Computation

For large datasets or computationally intensive analyses:

```
Configure ASTRA to use distributed computing resources
Specify the number of worker processes
Set up data partitioning for parallel processing
Monitor progress of distributed jobs
Combine results from parallel workers
```

### 7.3 Interactive Visualization

ASTRA provides interactive visualization capabilities:

```
Generate interactive plots using plotly or bokeh
Create dashboards for monitoring analysis progress
Enable real-time visualization of streaming data
Customize plot styles for publication or presentation
Export figures in multiple formats (PDF, PNG, SVG)
```

### 7.4 Provenance Tracking

Every analysis includes complete provenance information:

```
Track all data processing steps from input to output
Record all parameter values and random seeds
Document the reasoning behind method choices
Enable reproducibility of all results
Export provenance in standard formats (PROV, JSON-LD)
```

### 7.5 Extensibility

Users can extend ASTRA with custom capabilities:

```
Define custom analysis functions following ASTRA conventions
Register new domain modules for specialized astrophysical subfields
Add new data format readers
Contribute custom visualization methods
Share extensions with the ASTRA community
```

---

## 8. Domain Modules

ASTRA includes 75 specialized domain modules covering all major areas of astrophysics. These modules provide domain-specific knowledge, analysis methods, and validation criteria.

### 8.1 Available Domain Modules

**Stellar and Galactic Astrophysics**:
- Star Formation and the Interstellar Medium
- Stellar Evolution and Remnants
- Galactic Structure and Dynamics
- Stellar Populations
- Variable Stars

**Extragalactic Astrophysics**:
- Galaxy Evolution
- Active Galactic Nuclei
- Galaxy Clusters and Large-Scale Structure
- Cosmology
- High-Energy Astrophysics

**Solar System and Exoplanets**:
- Planetary Science
- Exoplanet Detection and Characterization
- Small Bodies (Comets, Asteroids)
- Planetary Atmospheres

**Time-Domain and Multi-Messenger**:
- Time-Domain Astronomy
- Gravitational Wave Astronomy
- Neutrino Astronomy
- High-Energy Particles

**Observational Techniques**:
- Photometry and Spectroscopy
- Interferometry
- Polarimetry
- Astrometry

### 8.2 Using Domain Modules

Domain modules are automatically loaded based on the analysis context:

```
ASTRA automatically selects relevant domain modules
Users can manually specify preferred modules
Domain modules provide specialized methods and validation
Modules contribute domain knowledge to guide analysis
```

---

## 9. API Reference

### 9.1 Core Functions

#### 9.1.1 Creating a System Instance

```
Create an ASTRA system with default configuration
Create with custom configuration options
Create with specific domain modules preloaded
```

#### 9.1.2 Loading Data

```
Load data from a file (CSV, FITS, etc.)
Load data from a database query
Load data from an Astropy Table object
Validate loaded data for required fields
```

#### 9.1.3 Running Analyses

```
Run a simple analysis with automatic method selection
Run a specific analysis method
Run multiple analyses in sequence
Run analyses with custom parameters
```

#### 9.1.4 Accessing Results

```
Get the primary result of an analysis
Get confidence intervals or uncertainties
Get detailed method descriptions
Get validation results
Get provenance information
```

### 9.2 Advanced API Usage

#### 9.2.1 Custom Workflows

```
Define a workflow as a directed acyclic graph
Specify dependencies between analysis steps
Configure error handling and retry logic
Save and load workflow definitions
```

#### 9.2.2 Batch Processing

```
Define a batch processing job
Specify input data patterns
Configure output file organization
Monitor batch job progress
```

---

## 10. Best Practices

### 10.1 Data Preparation

**Always validate data quality**:
- Check for missing values and outliers
- Verify units and coordinate systems
- Examine data distributions before analysis

**Preserve uncertainty information**:
- Keep measurement uncertainties with all data
- Document error correlations
- Propagate uncertainties through all operations

**Document data provenance**:
- Record source surveys and catalogs
- Track any preprocessing steps
- Note selection criteria and completeness

### 10.2 Analysis Design

**Start with exploratory analysis**:
- Examine basic statistics and distributions
- Visualize key relationships
- Identify potential issues before detailed analysis

**Use appropriate significance thresholds**:
- Account for multiple testing when needed
- Consider false discovery rate for large datasets
- Report both p-values and effect sizes

**Validate against physical constraints**:
- Check dimensional consistency
- Verify conservation laws are satisfied
- Compare to theoretical expectations

### 10.3 Interpretation and Reporting

**Report uncertainties properly**:
- Always include confidence intervals
- Distinguish statistical and systematic uncertainties
- Report both central values and uncertainties

**Acknowledge limitations**:
- Discuss selection effects and biases
- Note assumptions and their validity
- Identify areas requiring further validation

**Make analyses reproducible**:
- Document all analysis steps
- Record random seeds and parameter values
- Share code and data where possible

### 10.4 Computational Considerations

**Optimize for large datasets**:
- Use appropriate data types for memory efficiency
- Consider chunking or streaming for very large datasets
- Profile performance bottlenecks

**Use appropriate computational resources**:
- Enable parallel processing for independent tasks
- Use GPU acceleration when available
- Monitor memory usage for large analyses

---

## 11. Troubleshooting

### 11.1 Common Issues

**Issue**: Analysis takes too long
- **Solution**: Reduce dataset size for testing, enable parallel processing, check for inefficient operations

**Issue**: Results seem physically unreasonable
- **Solution**: Check input data for errors, verify units, examine intermediate results, validate assumptions

**Issue**: Uncertainties seem too small or large
- **Solution**: Verify uncertainty propagation, check for systematic errors, review statistical methods

**Issue**: Memory errors with large datasets
- **Solution**: Process data in chunks, reduce memory footprint, use appropriate data types

### 11.2 Getting Help

**Documentation**: Check the GitHub repository for detailed documentation
**Issues**: Report bugs or issues via GitHub Issues
**Community**: Engage with the ASTRA user community for advice
**Examples**: Review example notebooks and use cases

---

## 12. Appendices

### Appendix A: Data Format Specifications

**Supported Input Formats**:
- CSV: Columnar data with header row
- FITS: Binary and ASCII FITS tables
- HDF5: Hierarchical data format
- JSON: Structured data
- Astropy Tables: Native Python format

**Required Metadata**:
- Units for all physical quantities
- Coordinate system information
- Time system information (MJD, JD, etc.)
- Uncertainty information

### Appendix B: Configuration Reference

**Global Configuration Options**:
- Maximum memory usage
- Number of worker processes
- Default plot styles
- Logging verbosity

**Domain-Specific Options**:
- Module-specific parameters
- Validation criteria
- Visualization preferences

### Appendix C: Performance Benchmarks

**Typical Analysis Times**:
- Scaling relations: < 1 second for 100 objects
- Causal inference: 10 seconds for 1000 objects, 10 variables
- Bayesian model selection: 30 seconds for 4 models, 100 objects
- Anomaly detection: 5 seconds for 10,000 objects

**Scaling with Dataset Size**:
- Most analyses scale linearly with number of objects
- Causal inference scales quadratically with number of variables
- Bayesian methods scale linearly with dataset size

### Appendix D: Glossary

**Bayes Factor**: Ratio of evidences for two competing models
**Causal Graph**: Directed graph representing causal relationships
**Dimensional Analysis**: Method for checking dimensional consistency
**Evidence**: Marginal likelihood of data given a model
**Malmquist Bias**: Selection effect in flux-limited surveys
**Occam's Razor**: Principle favoring simpler explanations
**Posterior Predictive Check**: Validation of model fit

### Appendix E: References

**Key Methodological References**:
- Pearl, J. (2009). Causality: Models, Reasoning, and Inference
- Kass, R. E., & Raftery, A. E. (1995). Bayes Factors
- Spirtes, P., Glymour, C., & Scheines, R. (2000). Causation, Prediction, and Search
- Gelman, A., et al. (2013). Bayesian Data Analysis

**ASTRA Documentation**:
- GitHub Repository: https://github.com/Tilanthi/ASTRA
- API Documentation: Available in repository
- Example Notebooks: Available in repository

---

## Index

A
Analogical Reasoning, 45
Anomaly Detection, 47
Architecture, 13
ASTRA (definition), 3

B
Bayesian Inference, 18
Bayes Factors, 43
Bias Detection, 37

C
Causal Inference, 40
Causal Reasoning Module, 16
Configuration, 29
Counterfactual Analysis, 44

D
Data Processing Pipeline, 17
Domain Knowledge Systems, 18
Domain Modules, 59

E
Ensemble Prediction, 48
Examples, 31
Installation, 25

G
Getting Started, 30

H
Hypothesis Generation, 42

I
Instrument-Aware Analysis, 40
Installation, 25

M
Memory Systems, 22
Meta-Cognitive Evaluation, 46
Methods, 15
Model Selection, 43
Multi-Wavelength Fusion, 38

O
Orchestration Layer, 14

P
Physical Model Discovery, 45
Physics Engine, 15
Positioning, 50
Provenance, 57

S
Scaling Relations, 38
System Requirements, 25

T
Temporal Reasoning, 39
Troubleshooting, 62

U
Uncertainty Quantification, 38
User Interface, 14

---

**Document Version**: 1.0
**Last Updated**: April 2026
**Maintainers**: Glenn J. White & Robin Dey
**License**: See GitHub Repository

For the latest version of this manual and additional documentation, please visit:
https://github.com/Tilanthi/ASTRA
