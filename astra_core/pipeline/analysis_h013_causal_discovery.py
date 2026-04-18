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

# ASTRA Autonomous Analysis Script for H013
# Hypothesis: Causal Discovery on H₀ Compilation
# Goal: Identify causal structure among H₀ measurement methods
# Date: 2026-04-03

import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
from causalnex.structure.notears import from_pandas
from causalnex.plots import plot_structure
import matplotlib.pyplot as plt
import os

# Set random seed for reproducibility
np.random.seed(42)

# Load data
data = pd.read_csv('/shared/ASTRA/data/discovery_run/h0_compilation.csv')
print(f'Data loaded: {data.shape[0]} measurements')

# Preprocess data
# Encode categorical variable 'method'
le = LabelEncoder()
data['method_encoded'] = le.fit_transform(data['method'])

# Select relevant columns for causal discovery
features = ['h0', 'err_plus', 'method_encoded']
X = data[features]

# Run causal discovery using NOTEARS algorithm
sm = from_pandas(X, tabu_edges=None, w_threshold=0.8)

# Plot the causal structure
plt.figure(figsize=(10, 6))
plot_structure(sm)
output_dir = '/shared/ASTRA/data/discovery_run/plots/'
os.makedirs(output_dir, exist_ok=True)
plt.savefig(os.path.join(output_dir, 'h013_causal_structure.png'), format='png', dpi=300, bbox_inches='tight')
plt.close()

# Summarize findings
nodes = sm.nodes()
edges = sm.edges()
# adj_matrix = sm.adj_matrix_  # Not available in current version

summary = f'Causal Structure Analysis for H013\n'
summary += f'Nodes: {len(nodes)}\n'
summary += f'Edges: {len(edges)}\n'
summary += f'Key Relationships:\n'
for edge in edges:
    summary += f'  {edge[0]} -> {edge[1]}\n'

# Save summary
with open('/shared/ASTRA/hypotheses/h013_results.txt', 'w') as f:
    f.write(summary)

print('Causal discovery completed. Results saved to h013_results.txt and plot to h013_causal_structure.png')

# Additional statistical analysis for method clusters
method_groups = data.groupby('method').agg({
    'h0': ['mean', 'std', 'count'],
    'err_plus': 'mean'
}).reset_index()

method_summary = 'Method-wise H₀ Statistics:\n'
for idx, row in method_groups.iterrows():
    method_summary += f"Method: {row['method']}, Mean H₀: {row['h0']['mean']:.2f}, Std: {row['h0']['std']:.2f}, Count: {row['h0']['count']}, Avg Error Plus: {row['err_plus']['mean']:.2f}\n"

with open('/shared/ASTRA/hypotheses/h013_results.txt', 'a') as f:
    f.write('\n')
    f.write(method_summary)

print('Method-wise statistics appended to h013_results.txt')
