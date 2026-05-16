#!/usr/bin/env python3
"""
Campaign 10: Filament Length L/3 Convergence Test
=================================================

Resolves the pairwise median convergence problem by:
1. Running controlled simulations with known core spacing
2. Computing both pairwise median and nearest-neighbor spacing
3. Quantifying the L/3 bias for realistic HGBS filament lengths

Author: ASTRA Peer Review Response
Date: 2026-04-30
"""

import os
import json
import numpy as np
from datetime import datetime

# =============================================================================
# CAMPAIGN SPECIFICATION
# =============================================================================

CAMPAIGN_ID = "C10_L3_Convergence"
CAMPAIGN_NAME = "Filament Length L/3 Convergence Test"

# HGBS region specifications (filament lengths and core counts)
HGBS_REGIONS = {
    'Taurus': {'L': 8.5, 'N': 536},
    'OrionB': {'L': 12.0, 'N': 1844},
    'Aquila': {'L': 10.0, 'N': 749},
    'Perseus': {'L': 9.0, 'N': 816},
    'Ophiuchus': {'L': 6.0, 'N': 513},
    'Serpens': {'L': 7.0, 'N': 194},
    'TMC1': {'L': 5.0, 'N': 178},
    'CRA': {'L': 6.0, 'N': 239},
}

# Test scenarios
TEST_SCENARIOS = ['periodic_beading', 'random_uniform']
SEEDS = [42, 137, 314]  # Random seeds for ensemble

# Beading spacing for Test A (periodic beading)
BEADING_SPACING = 0.3  # pc

# Output configuration
OUTPUT_BASE = "/data/peer_response_runs/C10"

# =============================================================================
# ANALYSIS FUNCTIONS (No ATHENA++ simulations needed)
# =============================================================================

def generate_periodic_beading(region_name, L, N_cores, spacing, seed):
    """Generate periodic core distribution along a filament."""

    np.random.seed(seed)

    # Generate periodic beading with small random perturbations
    n_cores = int(L / spacing)
    positions = np.arange(n_cores) * spacing

    # Add small random perturbations (±5% of spacing)
    perturbations = np.random.uniform(-0.05*spacing, 0.05*spacing, n_cores)
    positions += perturbations

    # Ensure positions stay within [0, L]
    positions = np.clip(positions, 0, L)

    return {
        'region': region_name,
        'scenario': 'periodic_beading',
        'L': L,
        'N': n_cores,
        'true_spacing': spacing,
        'positions': positions.tolist(),
        'seed': seed,
    }

def generate_random_uniform(region_name, L, N, seed):
    """Generate random uniform core distribution along a filament."""

    np.random.seed(seed)

    # Generate N random positions uniformly along [0, L]
    positions = np.sort(np.random.uniform(0, L, N))

    return {
        'region': region_name,
        'scenario': 'random_uniform',
        'L': L,
        'N': N,
        'positions': positions.tolist(),
        'seed': seed,
    }

def compute_pairwise_median(positions):
    """Compute pairwise median spacing."""

    n = len(positions)
    if n < 2:
        return None

    # Compute all pairwise distances
    distances = []
    for i in range(n):
        for j in range(i+1, n):
            distances.append(abs(positions[j] - positions[i]))

    return np.median(distances)

def compute_nearest_neighbor_spacing(positions):
    """Compute nearest-neighbor (adjacent-core) median spacing."""

    n = len(positions)
    if n < 2:
        return None

    # Sort positions
    sorted_pos = np.sort(positions)

    # Compute adjacent-core spacings
    spacings = np.diff(sorted_pos)

    return np.median(spacings)

def analyze_simulation(sim_data):
    """Analyze a simulation and compute statistics."""

    positions = np.array(sim_data['positions'])

    # Compute statistics
    pairwise_median = compute_pairwise_median(positions)
    nn_median = compute_nearest_neighbor_spacing(positions)
    L_over_3 = sim_data['L'] / 3.0

    # Compute true spacing (for periodic beading)
    if sim_data['scenario'] == 'periodic_beading':
        true_spacing = sim_data['true_spacing']
    else:
        true_spacing = None

    # Compute bias
    if true_spacing is not None:
        bias_pairwise = (pairwise_median - true_spacing) / true_spacing
        bias_nn = (nn_median - true_spacing) / true_spacing
    else:
        bias_pairwise = None
        bias_nn = None

    return {
        'sim_id': sim_data['sim_id'],
        'region': sim_data['region'],
        'scenario': sim_data['scenario'],
        'L': sim_data['L'],
        'N': sim_data['N'],
        'true_spacing': true_spacing,
        'pairwise_median': pairwise_median,
        'nn_median': nn_median,
        'L_over_3': L_over_3,
        'bias_pairwise': bias_pairwise,
        'bias_nn': bias_nn,
        'positions': positions.tolist(),
    }

# =============================================================================
# SIMULATION GENERATION
# =============================================================================

def generate_simulation_list():
    """Generate list of all simulations to run."""

    simulations = []
    sim_id = 0

    for region_name, region_data in HGBS_REGIONS.items():
        L = region_data['L']
        N = region_data['N']

        for scenario in TEST_SCENARIOS:
            for seed in SEEDS:

                if scenario == 'periodic_beading':
                    sim_data = generate_periodic_beading(region_name, L, N, BEADING_SPACING, seed)
                else:  # random_uniform
                    sim_data = generate_random_uniform(region_name, L, N, seed)

                sim_data['sim_id'] = f"C10_{region_name}_{scenario}_seed{seed}"
                simulations.append(sim_data)
                sim_id += 1

    return simulations

# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Main execution function."""

    print("="*70)
    print(f"CAMPAIGN 10: Filament Length L/3 Convergence Test")
    print("="*70)
    print()

    print(f"Objective: Quantify L/3 convergence bias and compute proper")
    print(f"nearest-neighbor spacing for all 8 HGBS regions")
    print()
    print(f"Test scenarios:")
    print(f"  A: Periodic beading at known spacing (d = {BEADING_SPACING} pc)")
    print(f"  B: Random uniform core distribution")
    print()
    print(f"HGBS regions:")
    for region_name, region_data in HGBS_REGIONS.items():
        print(f"  {region_name}: L = {region_data['L']} pc, N = {region_data['N']} cores")
    print()

    # Generate simulation list
    simulations = generate_simulation_list()

    print(f"Generated {len(simulations)} test configurations")
    print()

    # Save specification
    spec_file = f"{OUTPUT_BASE}/campaign_specification.json"
    os.makedirs(OUTPUT_BASE, exist_ok=True)

    # Analyze all simulations
    results = []
    for sim_data in simulations:
        result = analyze_simulation(sim_data)
        results.append(result)

    spec_data = {
        "campaign_id": CAMPAIGN_ID,
        "campaign_name": CAMPAIGN_NAME,
        "date": datetime.now().isoformat(),
        "objective": "Quantify L/3 convergence bias and validate NN spacing for HGBS regions",
        "n_simulations": len(simulations),
        "regions": HGBS_REGIONS,
        "test_scenarios": TEST_SCENARIOS,
        "results": results,
    }

    with open(spec_file, 'w') as f:
        json.dump(spec_data, f, indent=2)

    print(f"Specification saved to: {spec_file}")
    print()

    # Create analysis script
    analysis_script = f"{OUTPUT_BASE}/analyze_results.py"
    with open(analysis_script, 'w') as f:
        f.write('#!/usr/bin/env python3\n')
        f.write('"""')
        f.write(f'Campaign 10 Analysis Script')
        f.write(f'Generated: {datetime.now().isoformat()}\n')
        f.write('"""\n\n')
        f.write('import json\n')
        f.write('import numpy as np\n')
        f.write('import matplotlib.pyplot as plt\n\n')
        f.write('def main():\n')
        f.write(f'    spec_file = "{spec_file}"\n')
        f.write('    \n')
        f.write('    with open(spec_file) as f:\n')
        f.write('        spec = json.load(f)\n')
        f.write('    \n')
        f.write('    results = spec["results"]\n')
        f.write('    \n')
        f.write('    # Separate results by scenario\n')
        f.write('    periodic_results = [r for r in results if r["scenario"] == "periodic_beading"]\n')
        f.write('    random_results = [r for r in results if r["scenario"] == "random_uniform"]\n')
        f.write('    \n')
        f.write('    print("CAMPAIGN 10 RESULTS")\n')
        f.write('    print("="*70)\n')
        f.write('    print()\n')
        f.write('    print("TEST A: PERIODIC BEADING")\n')
        f.write('    print("-"*70)\n')
        f.write('    print(f"{"Region":<12} {"N":<6} {"Pairwise":<12} {"NN":<12} {"True":<12} {"Bias_pair":<12} {"Bias_nn":<12}")\n')
        f.write('    print("-"*70)\n')
        f.write('    \n')
        f.write('    for r in periodic_results:\n')
        f.write('        print(f"{r["region"]:<12} {r["N"]:<6} {r["pairwise_median"]:<12.4f} {r["nn_median"]:<12.4f} {r["true_spacing"]:<12.4f} {r["bias_pairwise"]:<12.4f} {r["bias_nn"]:<12.4f}")\n')
        f.write('    \n')
        f.write('    print()\n')
        f.write('    print("TEST B: RANDOM UNIFORM")\n')
        f.write('    print("-"*70)\n')
        f.write('    print(f"{"Region":<12} {"N":<6} {"Pairwise":<12} {"NN":<12} {"L/3":<12}")\n')
        f.write('    print("-"*70)\n')
        f.write('    \n')
        f.write('    for r in random_results:\n')
        f.write('        print(f"{r["region"]:<12} {r["N"]:<6} {r["pairwise_median"]:<12.4f} {r["nn_median"]:<12.4f} {r["L_over_3"]:<12.4f}")\n')
        f.write('    \n')
        f.write('    # Compute bias statistics\n')
        f.write('    periodic_biases_pairwise = [r["bias_pairwise"] for r in periodic_results]\n')
        f.write('    periodic_biases_nn = [r["bias_nn"] for r in periodic_results]\n')
        f.write('    \n')
        f.write('    print()\n')
        f.write('    print("BIAS STATISTICS (Periodic Beading)")\n')
        f.write('    print("-"*70)\n')
        f.write('    print(f"Pairwise bias: {np.mean(periodic_biases_pairwise):.4f} +/- {np.std(periodic_biases_pairwise):.4f}")\n')
        f.write('    print(f"NN bias: {np.mean(periodic_biases_nn):.4f} +/- {np.std(periodic_biases_nn):.4f}")\n')
        f.write('    \n')
        f.write('    # Create figures\n')
        f.write('    fig, axes = plt.subplots(1, 2, figsize=(14, 6))\n')
        f.write('    \n')
        f.write('    # Plot A: Bias comparison\n')
        f.write('    ax = axes[0]\n')
        f.write('    regions = [r["region"] for r in periodic_results]\n')
        f.write('    biases_pairwise = [r["bias_pairwise"]*100 for r in periodic_results]\n')
        f.write('    biases_nn = [r["bias_nn"]*100 for r in periodic_results]\n')
        f.write('    x = np.arange(len(regions))\n')
        f.write('    width = 0.35\n')
        f.write('    ax.bar(x - width/2, biases_pairwise, width, label="Pairwise median")\n')
        f.write('    ax.bar(x + width/2, biases_nn, width, label="NN spacing")\n')
        f.write('    ax.set_ylabel("Bias (%)")\n')
        f.write('    ax.set_title("L/3 Convergence Bias (Periodic Beading)")\n')
        f.write('    ax.set_xticks(x)\n')
        f.write('    ax.set_xticklabels(regions, rotation=45, ha="right")\n')
        f.write('    ax.legend()\n')
        f.write('    ax.axhline(y=0, color="k", linestyle="--", alpha=0.3)\n')
        f.write('    \n')
        f.write('    # Plot B: Random convergence to L/3\n')
        f.write('    ax = axes[1]\n')
        f.write('    for r in random_results:\n')
        f.write('        ax.scatter(r["N"], r["pairwise_median"], label="Pairwise", alpha=0.6)\n')
        f.write('        ax.scatter(r["N"], r["nn_median"], label="NN", alpha=0.6)\n')
        f.write('        ax.scatter(r["N"], r["L_over_3"], label="L/3", marker="x", s=100)\n')
        f.write('    ax.set_xlabel("Number of cores (N)")\n')
        f.write('    ax.set_ylabel("Spacing (pc)")\n')
        f.write('    ax.set_title("Random Distribution: Convergence to L/3")\n')
        f.write('    \n')
        f.write('    plt.tight_layout()\n')
        f.write(f'    plt.savefig("{OUTPUT_BASE}/L3_convergence_analysis.pdf")\n')
        f.write(f'    print(f"\\nFigure saved: {OUTPUT_BASE}/L3_convergence_analysis.pdf")\n')
        f.write('    \n')
        f.write('    # Save results to JSON\n')
        f.write(f'    results_file = "{OUTPUT_BASE}/L3_convergence_results.json"\n')
        f.write('    with open(results_file, "w") as f:\n')
        f.write('        json.dump({\n')
        f.write('            "periodic_beading": periodic_results,\n')
        f.write('            "random_uniform": random_results,\n')
        f.write('            "bias_stats": {\n')
        f.write('                "pairwise_mean": float(np.mean(periodic_biases_pairwise)),\n')
        f.write('                "pairwise_std": float(np.std(periodic_biases_pairwise)),\n')
        f.write('                "nn_mean": float(np.mean(periodic_biases_nn)),\n')
        f.write('                "nn_std": float(np.std(periodic_biases_nn)),\n')
        f.write('            }\n')
        f.write('        }, f, indent=2)\n')
        f.write(f'    print(f"Results saved: {results_file}")\n')
        f.write('    \n')
        f.write('if __name__ == "__main__":\n')
        f.write('    main()\n')

    os.chmod(analysis_script, 0o755)
    print(f"Analysis script created: {analysis_script}")
    print()

    # Create NN spacing analysis script for HGBS data
    nn_script = f"{OUTPUT_BASE}/compute_hgbs_nn_spacing.py"
    with open(nn_script, 'w') as f:
        f.write('#!/usr/bin/env python3\n')
        f.write('"""')
        f.write(f'Compute NN spacing for all HGBS regions')
        f.write(f'Generated: {datetime.now().isoformat()}\n')
        f.write('"""\n\n')
        f.write('import sys\n')
        f.write('sys.path.append("/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/W3_HGBS_filaments/final_merged_paper")\n')
        f.write('from compute_nearest_neighbor_spacing import analyze_region, HGBS_REGIONS\n')
        f.write('import json\n\n')
        f.write('def main():\n')
        f.write('    results = []\n')
        f.write('    \n')
        f.write('    for region_name, region_info in HGBS_REGIONS.items():\n')
        f.write('        try:\n')
        f.write('            result = analyze_region(region_name, region_info)\n')
        f.write('            if result:\n')
        f.write('                results.append(result)\n')
        f.write('        except Exception as e:\n')
        f.write('            print(f"ERROR analyzing {region_name}: {e}")\n')
        f.write('    \n')
        f.write(f'    output_file = "{OUTPUT_BASE}/HGBS_NN_spacing_results.json"\n')
        f.write('    with open(output_file, "w") as f:\n')
        f.write('        json.dump(results, f, indent=2)\n')
        f.write('    \n')
        f.write(f'    print(f"\\nResults saved to: {output_file}")\n')
        f.write('    \n')
        f.write('if __name__ == "__main__":\n')
        f.write('    main()\n')

    os.chmod(nn_script, 0o755)
    print(f"HGBS NN spacing script: {nn_script}")
    print()

    print("="*70)
    print("CAMPAIGN 10 SPECIFICATION COMPLETE")
    print("="*70)
    print()
    print(f"Specification file: {spec_file}")
    print(f"Analysis script: {analysis_script}")
    print(f"HGBS NN script: {nn_script}")
    print()
    print("Next steps:")
    print("1. Run analysis script: python analyze_results.py")
    print("2. Compute HGBS NN spacing: python compute_hgbs_nn_spacing.py")
    print("3. Compare with pairwise median values")
    print()

if __name__ == "__main__":
    main()
