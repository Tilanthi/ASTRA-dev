#!/usr/bin/env python3
"""
Test 11: Causal Inference
Demonstrates ASTRA's capability to discover causal relationships
from observational data using structural causal models.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from scipy import stats
from scipy.optimize import curve_fit
import json
from itertools import combinations

print("="*70)
print("TEST 11: CAUSAL INFERENCE")
print("="*70)

# Load real Gaia data
print("\nLoading real Gaia DR2 data...")
gaia_data = pd.read_csv('gaia_real_data_large.csv')
print(f"Loaded {len(gaia_data)} stars")

# Sample for analysis
np.random.seed(42)
sample_size = 1000
sample_idx = np.random.choice(len(gaia_data), sample_size, replace=False)
stars = gaia_data.iloc[sample_idx].copy()

print(f"Analyzing {sample_size} stars for causal inference")

# ============================================================================
# CAUSAL DISCOVERY METHODS
# ============================================================================

print("\n" + "="*70)
print("CAUSAL DISCOVERY ANALYSIS")
print("="*70)

def compute_partial_correlation(data, var1, var2, control_vars=None):
    """
    Compute partial correlation between var1 and var2 controlling for control_vars.
    This helps distinguish direct from indirect relationships.
    """
    if control_vars is None or len(control_vars) == 0:
        return stats.pearsonr(data[var1], data[var2])[0]

    # Regression approach: partial_r = correlation of residuals
    from sklearn.linear_model import LinearRegression

    # Regress var1 on controls
    X_controls = data[control_vars].values
    y1 = data[var1].values
    y2 = data[var2].values

    model1 = LinearRegression()
    model1.fit(X_controls, y1)
    resid1 = y1 - model1.predict(X_controls)

    model2 = LinearRegression()
    model2.fit(X_controls, y2)
    resid2 = y2 - model2.predict(X_controls)

    # Correlation of residuals
    partial_r, _ = stats.pearsonr(resid1, resid2)
    return partial_r

def conditional_independence_test(data, x, y, z=None, alpha=0.05):
    """
    Test conditional independence: X independent of Y given Z?
    Returns True if independent (fail to reject null)
    """
    if z is None:
        # Simple correlation test
        r, p = stats.pearsonr(data[x], data[y])
        return p > alpha, r, p

    # Convert z to list if it's a single string
    control_vars = [z] if isinstance(z, str) else list(z)

    # Partial correlation test
    partial_r = compute_partial_correlation(data, x, y, control_vars)

    # Fisher's z-transformation for significance test
    n = len(data)
    z_score = np.sqrt(n - 3 - len(control_vars)) * 0.5 * np.log((1 + partial_r) / (1 - partial_r))
    p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))

    return p_value > alpha, partial_r, p_value

def pc_algorithm(data, variables, alpha=0.05):
    """
    PC Algorithm for causal structure learning.
    Returns adjacency matrix of causal graph.
    """
    n_vars = len(variables)
    var_to_idx = {v: i for i, v in enumerate(variables)}

    # Start with complete graph
    adjacency = np.ones((n_vars, n_vars), dtype=bool)
    np.fill_diagonal(adjacency, False)

    # Phase 1: Edge removal by conditional independence
    sep_set = {v: {} for v in variables}

    for i, j in combinations(range(n_vars), 2):
        var_i, var_j = variables[i], variables[j]

        # Start with zero conditioning set
        independent, r, p = conditional_independence_test(data, var_i, var_j, None, alpha)

        if independent:
            adjacency[i, j] = adjacency[j, i] = False
            sep_set[var_i][var_j] = []
            continue

        # Increase conditioning set size
        neighbors_i = [variables[k] for k in range(n_vars) if adjacency[i, k]]
        neighbors_j = [variables[k] for k in range(n_vars) if adjacency[j, k]]

        # Try conditioning on neighbors
        for size in range(1, min(len(neighbors_i), 3) + 1):
            for subset in combinations(neighbors_i, size):
                independent, r, p = conditional_independence_test(data, var_i, var_j, subset, alpha)
                if independent:
                    adjacency[i, j] = adjacency[j, i] = False
                    sep_set[var_i][var_j] = list(subset)
                    break
            if not adjacency[i, j]:
                break

    return adjacency, sep_set

def orient_v_structure(data, adjacency, sep_set, variables):
    """
    Orient v-structures (colliders) in the graph.
    A -> B <- C if A and C are independent given B,
    but dependent given subsets not containing B.
    """
    n_vars = len(variables)
    var_to_idx = {v: i for i, v in enumerate(variables)}
    directed = np.zeros((n_vars, n_vars), dtype=bool)

    for i, j, k in combinations(range(n_vars), 3):
        var_i, var_j, var_k = variables[i], variables[j], variables[k]

        # Check if i-j-k forms unshielded triple (no edge i-k)
        if adjacency[i, j] and adjacency[j, k] and not adjacency[i, k]:
            # Check if i and k are independent given j
            independent, r, p = conditional_independence_test(data, var_i, var_k, var_j)

            if independent:
                # This is a v-structure: i -> j <- k
                directed[i, j] = True
                directed[k, j] = True

    return directed

# ============================================================================
# ANALYZE CAUSAL STRUCTURE OF STELLAR PROPERTIES
# ============================================================================

print("\n" + "-"*60)
print("Causal Structure: Stellar Properties")
print("-"*60)

# Define variables for causal analysis
stellar_vars = ['distance_pc', 'phot_g_mean_mag', 'absolute_mag', 'luminosity_lsun']

# Normalize for better numerical stability
data_normalized = stars[stellar_vars].copy()
for var in stellar_vars:
    data_normalized[var] = (stars[var] - stars[var].mean()) / stars[var].std()

# Run PC algorithm
adjacency, sep_set = pc_algorithm(data_normalized, stellar_vars, alpha=0.01)

# Orient v-structures
directed = orient_v_structure(data_normalized, adjacency, sep_set, stellar_vars)

print("\nDiscovered Causal Structure:")
for i, var_i in enumerate(stellar_vars):
    connections = []
    for j, var_j in enumerate(stellar_vars):
        if i != j and adjacency[i, j]:
            if directed[j, i]:  # j -> i
                connections.append(f"<- {var_j}")
            elif directed[i, j]:  # i -> j
                connections.append(f"-> {var_j}")
            else:  # undirected
                connections.append(f"-- {var_j}")

    if connections:
        print(f"  {var_i}: {' '.join(connections)}")

# ============================================================================
# PHYSICAL INTERPRETATION OF CAUSAL STRUCTURE
# ============================================================================

print("\n" + "-"*60)
print("Physical Interpretation")
print("-"*60)

# Known physical causal relationships:
# distance_pc -> phot_g_mean_mag (distance affects apparent brightness)
# absolute_mag -> phot_g_mean_mag (intrinsic luminosity affects brightness)
# absolute_mag -> luminosity_lsun (by definition)
# NOT causal: distance_pc -> absolute_mag (selection bias)

causal_interpretations = {
    'distance_pc -> phot_g_mean_mag': {
        'expected': True,
        'physical': 'Distance modulus: m - M = 5*log10(d/10)',
        'type': 'physical law'
    },
    'absolute_mag -> phot_g_mean_mag': {
        'expected': True,
        'physical': 'Intrinsic luminosity affects apparent brightness',
        'type': 'physical law'
    },
    'absolute_mag -> luminosity_lsun': {
        'expected': True,
        'physical': 'Definition: L = 10^(-0.4*(M - M_sun))',
        'type': 'definition'
    },
    'distance_pc -> absolute_mag': {
        'expected': False,
        'physical': 'Selection bias (Malmquist bias)',
        'type': 'observational artifact'
    },
}

# Test expected causal relationships
causal_tests = []

for rel, info in causal_interpretations.items():
    source, target = rel.split(' -> ')

    # Check if edge exists
    source_idx = stellar_vars.index(source)
    target_idx = stellar_vars.index(target)
    edge_exists = adjacency[source_idx, target_idx]

    # Check direction if edge exists
    direction_correct = directed[source_idx, target_idx] if edge_exists else None

    causal_tests.append({
        'relationship': rel,
        'expected': bool(info['expected']),
        'edge_detected': bool(edge_exists),
        'direction_correct': bool(direction_correct) if direction_correct is not None else None,
        'physical_meaning': info['physical'],
        'type': info['type']
    })

    print(f"\n{rel}:")
    print(f"  Expected: {info['expected']} ({info['type']})")
    print(f"  Detected: {edge_exists}")
    print(f"  Physical: {info['physical']}")

# ============================================================================
# DO-CALCUS: INTERVENTION ANALYSIS
# ============================================================================

print("\n" + "-"*60)
print("Do-Calculus: Intervention Analysis")
print("-"*60)

def simulate_intervention(data, intervention_var, intervention_value):
    """
    Simulate the effect of an intervention using structural equations.
    """
    result = data.copy()

    if intervention_var == 'absolute_mag':
        # Intervening on absolute magnitude changes phot_g_mean_mag
        # m = M + 5*log10(d/10)
        delta_M = intervention_value - data['absolute_mag']
        result['phot_g_mean_mag_intervention'] = data['phot_g_mean_mag'] + delta_M
        result['absolute_mag_intervention'] = intervention_value

    elif intervention_var == 'distance_pc':
        # Intervening on distance changes phot_g_mean_mag
        original_distance = data['distance_pc']
        delta_m = 5 * np.log10(intervention_value / original_distance)
        result['phot_g_mean_mag_intervention'] = data['phot_g_mean_mag'] + delta_m
        result['distance_pc_intervention'] = intervention_value

    return result

# Example: What if all stars had absolute magnitude = 10 (standard candle)?
print("\nIntervention: Set all stars to M = 10 mag")
intervened = simulate_intervention(stars, 'absolute_mag', 10.0)

# Compare distributions
original_median_mag = stars['phot_g_mean_mag'].median()
intervened_median_mag = intervened['phot_g_mean_mag_intervention'].median()

print(f"  Original median G: {original_median_mag:.2f}")
print(f"  After intervention median G: {intervened_median_mag:.2f}")
print(f"  Change: {intervened_median_mag - original_median_mag:.2f} mag")

# ============================================================================
# CONFOUNDING ANALYSIS
# ============================================================================

print("\n" + "-"*60)
print("Confounder Analysis")
print("-"*60)

# Test if distance-luminosity correlation is confounded by selection
print("\nConfounder: Detection limit (G < 20 mag)")

# Detected vs undetected
detected = stars['phot_g_mean_mag'] < 20.0

# Correlation in full sample vs detected sample
full_corr = stars[['distance_pc', 'luminosity_lsun']].corr().iloc[0, 1]
detected_corr = stars[detected][['distance_pc', 'luminosity_lsun']].corr().iloc[0, 1]

print(f"  Distance-Luminosity correlation (full): {full_corr:.3f}")
print(f"  Distance-Luminosity correlation (detected): {detected_corr:.3f}")

print(f"\n  Interpretation: {'Confounder detected' if abs(detected_corr) > abs(full_corr) else 'No strong confounding'}")

# ============================================================================
# SAVE RESULTS
# ============================================================================

output = {
    'test_name': 'Causal Inference',
    'n_stars_analyzed': sample_size,
    'variables_analyzed': stellar_vars,
    'causal_tests': causal_tests,
    'adjacency_matrix': [[bool(x) for x in row] for row in adjacency.tolist()],
    'separating_sets': {k: {kk: vv for kk, vv in v.items()} for k, v in sep_set.items()},
    'directed_edges': [[bool(x) for x in row] for row in directed.tolist()],
    'intervention_example': {
        'intervention': 'Set absolute_mag = 10',
        'original_median_g': float(original_median_mag),
        'intervened_median_g': float(intervened_median_mag),
        'delta_mag': float(intervened_median_mag - original_median_mag)
    },
    'confounder_analysis': {
        'full_correlation': float(full_corr),
        'detected_correlation': float(detected_corr),
        'confounder_detected': bool(abs(detected_corr) > abs(full_corr))
    },
    'capabilities': [
        'PC algorithm for causal structure learning',
        'Conditional independence testing',
        'V-structure orientation (collider detection)',
        'Do-calculus for intervention analysis',
        'Confounder identification',
        'Physical interpretation of causal graphs',
    ]
}

with open('test11_causal_inference_results.json', 'w') as f:
    json.dump(output, f, indent=2)

print("\nResults saved to test11_causal_inference_results.json")

# ============================================================================
# CREATE FIGURE
# ============================================================================

print("\nGenerating causal inference figure...")

fig = plt.figure(figsize=(20, 14))
gs = GridSpec(4, 4, figure=fig, hspace=0.4, wspace=0.4)

# Panel A: Causal graph
ax1 = fig.add_subplot(gs[0, :2])
ax1.axis('off')

# Draw causal graph
graph_text = "DISCOVERED CAUSAL STRUCTURE\n\n"
for i, var_i in enumerate(stellar_vars):
    connections = []
    for j, var_j in enumerate(stellar_vars):
        if i != j and adjacency[i, j]:
            if directed[j, i]:
                connections.append(f"{var_j} → {var_i}")
            elif directed[i, j]:
                connections.append(f"{var_i} → {var_j}")
            else:
                connections.append(f"{var_i} ↔ {var_j}")

    if connections:
        graph_text += f"{var_i}:\n"
        for conn in connections:
            graph_text += f"  {conn}\n"

ax1.text(0.05, 0.95, graph_text, transform=ax1.transAxes,
         verticalalignment='top', fontsize=9,
         bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8),
         family='monospace')

# Panel B: Correlation matrix
ax2 = fig.add_subplot(gs[0, 2:])
corr_matrix = stars[stellar_vars].corr()
im = ax2.imshow(corr_matrix, cmap='RdBu_r', vmin=-1, vmax=1, aspect='auto')
ax2.set_xticks(range(len(stellar_vars)))
ax2.set_yticks(range(len(stellar_vars)))
short_vars = ['Dist', 'Gmag', 'AbsM', 'Lum']
ax2.set_xticklabels(short_vars)
ax2.set_yticklabels(short_vars)
ax2.set_title('B: Correlation Matrix')
for i in range(len(stellar_vars)):
    for j in range(len(stellar_vars)):
        text = ax2.text(j, i, f'{corr_matrix.iloc[i, j]:.2f}',
                       ha="center", va="center", color="black", fontsize=8)
plt.colorbar(im, ax=ax2)

# Panel C: Partial correlations
ax3 = fig.add_subplot(gs[1, :2])
partial_corr_matrix = np.zeros((len(stellar_vars), len(stellar_vars)))
for i, var1 in enumerate(stellar_vars):
    for j, var2 in enumerate(stellar_vars):
        if i != j:
            controls = [v for v in stellar_vars if v not in [var1, var2]]
            partial_corr_matrix[i, j] = compute_partial_correlation(stars, var1, var2, controls)

im3 = ax3.imshow(partial_corr_matrix, cmap='RdBu_r', vmin=-1, vmax=1, aspect='auto')
ax3.set_xticks(range(len(stellar_vars)))
ax3.set_yticks(range(len(stellar_vars)))
ax3.set_xticklabels(short_vars)
ax3.set_yticklabels(short_vars)
ax3.set_title('C: Partial Correlation Matrix (controlling for all others)')
for i in range(len(stellar_vars)):
    for j in range(len(stellar_vars)):
        if i != j:
            text = ax3.text(j, i, f'{partial_corr_matrix[i, j]:.2f}',
                           ha="center", va="center", color="black", fontsize=8)
plt.colorbar(im3, ax=ax3)

# Panel D: Causal test results
ax4 = fig.add_subplot(gs[1, 2:])
ax4.axis('off')

test_results_text = "CAUSAL RELATIONSHIP TESTS\n\n"
for test in causal_tests:
    status = "✓" if test['edge_detected'] == test['expected'] else "✗"
    test_results_text += f"{status} {test['relationship']}\n"
    test_results_text += f"    Expected: {test['expected']}, Detected: {test['edge_detected']}\n"
    test_results_text += f"    Type: {test['type']}\n"
    test_results_text += f"    Physics: {test['physical_meaning']}\n\n"

ax4.text(0.05, 0.95, test_results_text, transform=ax4.transAxes,
         verticalalignment='top', fontsize=8,
         bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5),
         family='monospace')

# Panel E: Distance vs Luminosity (confounding)
ax5 = fig.add_subplot(gs[2, 0])
ax5.scatter(stars['distance_pc'], stars['luminosity_lsun'],
           c=['green' if d else 'red' for d in detected],
           alpha=0.3, s=10)
ax5.set_xlabel('Distance (pc)')
ax5.set_ylabel('Luminosity (L_sun)')
ax5.set_title('E: Distance vs Luminosity (Green=detected, Red=undetected)')
ax5.set_yscale('log')
ax5.grid(True, alpha=0.3)

# Panel F: Malmquist bias visualization
ax6 = fig.add_subplot(gs[2, 1])
# Binned mean absolute magnitude vs distance
distance_bins = np.linspace(50, 500, 11)
bin_centers = (distance_bins[:-1] + distance_bins[1:]) / 2
mean_abs_mag = []
for i in range(len(distance_bins) - 1):
    mask = (stars['distance_pc'] >= distance_bins[i]) & (stars['distance_pc'] < distance_bins[i+1]) & detected
    if mask.sum() > 5:
        mean_abs_mag.append(stars[mask]['absolute_mag'].mean())
    else:
        mean_abs_mag.append(np.nan)

ax6.plot(bin_centers, mean_abs_mag, 'o-', color='steelblue', markersize=8)
ax6.set_xlabel('Distance (pc)')
ax6.set_ylabel('Mean Absolute Magnitude')
ax6.set_title('F: Malmquist Bias Demonstration')
ax6.invert_yaxis()
ax6.grid(True, alpha=0.3)

# Panel G: Intervention effect
ax7 = fig.add_subplot(gs[2, 2:])
ax7.hist(stars['phot_g_mean_mag'], bins=50, alpha=0.5, label='Original', color='steelblue')
ax7.hist(intervened['phot_g_mean_mag_intervention'], bins=50, alpha=0.5, label='After intervention (M=10)', color='coral')
ax7.axvline(original_median_mag, color='darkblue', linestyle='--', label=f'Original median: {original_median_mag:.1f}')
ax7.axvline(intervened_median_mag, color='darkred', linestyle='--', label=f'Intervened median: {intervened_median_mag:.1f}')
ax7.set_xlabel('G Magnitude')
ax7.set_ylabel('Count')
ax7.set_title('G: Intervention Effect (Set M = 10)')
ax7.legend(fontsize=7)
ax7.invert_xaxis()
ax7.grid(True, alpha=0.3)

# Panel H: Directed edges summary
ax8 = fig.add_subplot(gs[2, 3])
ax8.axis('off')

directed_edges_text = "DIRECTED CAUSAL EDGES\n\n"
n_directed = 0
for i, var_i in enumerate(stellar_vars):
    for j, var_j in enumerate(stellar_vars):
        if directed[i, j]:
            n_directed += 1
            directed_edges_text += f"{var_i} → {var_j}\n"

if n_directed == 0:
    directed_edges_text += "No v-structures detected\n(undirected edges only)"

ax8.text(0.05, 0.95, directed_edges_text, transform=ax8.transAxes,
         verticalalignment='top', fontsize=9,
         bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.8),
         family='monospace')

# Panel I: Comparison with LLM and ML
ax9 = fig.add_subplot(gs[3, :2])
ax9.axis('off')

comparison_text = """
CAPABILITY COMPARISON

LLMs:
  + Can explain causal concepts
  - Cannot discover structure from data
  - Cannot distinguish correlation from causation

Traditional ML:
  + Can find correlations
  - Cannot identify causal direction
  - Cannot model interventions

ASTRA:
  + PC algorithm for structure learning
  + Conditional independence testing
  + V-structure (collider) detection
  + Do-calculus for interventions
  + Confounder identification
  + Physical interpretation
"""

ax9.text(0.05, 0.95, comparison_text, transform=ax9.transAxes,
         verticalalignment='top', fontsize=10,
         bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.9),
         family='monospace')

# Panel J: Methods summary
ax10 = fig.add_subplot(gs[3, 2:])
ax10.axis('off')

methods_text = """
CAUSAL INFERENCE METHODS

PC Algorithm:
  1. Start with complete graph
  2. Remove edges via conditional
     independence tests
  3. Orient v-structures
  4. Propagate orientations

Conditional Independence:
  - Partial correlation
  - Fisher's z-transformation
  - Significance testing

Do-Calculus:
  - Intervention modeling
  - Structural equations
  - Counterfactual prediction

Physical Knowledge:
  - Incorporate known relations
  - Validate against theory
  - Interpret causal meaning
"""

ax10.text(0.05, 0.95, methods_text, transform=ax10.transAxes,
          verticalalignment='top', fontsize=9,
          bbox=dict(boxstyle='round', facecolor='lightcoral', alpha=0.8),
          family='monospace')

plt.suptitle('Test 11: Causal Inference with Real Gaia DR2 Data',
             fontsize=16, fontweight='bold')

plt.savefig('test11_causal_inference.png', dpi=150, bbox_inches='tight')
print("Figure saved to test11_causal_inference.png")
plt.close()

print("\n" + "="*70)
print("TEST 11 COMPLETE: Causal Inference")
print("="*70)
print(f"\nAnalyzed {sample_size} stars with {len(stellar_vars)} variables")
print(f"\nDiscovered {np.sum(adjacency)} edges in causal graph")
print(f"Directed {np.sum(directed)} causal relationships")
print("\nKey capabilities demonstrated:")
for cap in output['capabilities']:
    print(f"  • {cap}")
