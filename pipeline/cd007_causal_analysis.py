import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from causalnex.structure import StructureModel
from causalnex.structure.notears import from_pandas
import networkx as nx
import matplotlib.pyplot as plt

# Load the merged dataset
df = pd.read_csv('/shared/ASTRA/data/cross_domain/cd007_causal_structure/merged_dataset.csv', low_memory=False)

# Select relevant columns for causal discovery
selected_columns = ['co2', 'gdp', 'population', 'temperature_change_from_co2', 'total_cases', 'total_deaths', 'gdp_per_capita', 'hospital_beds_per_thousand', 'median_age']

# Drop rows with missing values in selected columns
df_selected = df[selected_columns].dropna()

# Scale the features
scaler = StandardScaler()
df_scaled = pd.DataFrame(scaler.fit_transform(df_selected), columns=df_selected.columns)

# Learn the causal structure using NOTEARS algorithm
sm = from_pandas(df_scaled, max_iter=100)

# Visualize the learned structure
plt.figure(figsize=(12, 8))
nx.draw(sm, with_labels=True, font_weight='bold', node_color='lightblue', node_size=500, font_size=10, pos=nx.spring_layout(sm))
plt.title('Causal Structure of Climate-Economy-Pandemic System')
plt.savefig('/shared/ASTRA/data/cross_domain/cd007_causal_structure/causal_structure_plot.png')
plt.close()

# Print edges for summary
edges = list(sm.edges())
print(f'Learned Causal Structure Edges: {edges}')

# Save results summary to text file
with open('/shared/ASTRA/data/cross_domain/cd007_causal_structure/results_summary.txt', 'w') as f:
    f.write('Causal Structure Analysis for Climate-Economy-Pandemic System\n')
    f.write('===============================================\n')
    f.write(f'Total number of nodes: {len(sm.nodes())}\n')
    f.write(f'Total number of edges: {len(edges)}\n')
    f.write('Learned Edges:\n')
    for edge in edges:
        f.write(f'  {edge[0]} -> {edge[1]}\n')
    f.write('\nInterpretation:\n')
    f.write('This graph represents the inferred causal relationships between variables from climate, economic, and epidemiological domains.\n')
    f.write('Each edge indicates a potential causal link, with the direction suggesting influence.\n')
    f.write('Further validation with domain expertise and statistical testing is recommended for confirmation.\n')

print('Causal structure analysis completed. Results saved to /shared/ASTRA/data/cross_domain/cd007_causal_structure/')
