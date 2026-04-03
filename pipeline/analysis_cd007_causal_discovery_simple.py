#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ASTRA Autonomous - Causal Discovery for Climate-Economy-Pandemic System (CD-007) - Simplified

This script maps causal structures connecting CO2 emissions, GDP, population, and pandemic outcomes
using a basic implementation of the PC algorithm from causal-learn. The goal is to identify potential
causal relationships across these domains.

Hypothesis: The causal structure connecting CO2, GDP, population, and pandemic outcomes can be mapped —
revealing whether climate drives economics, economics drives pandemic response, or there's a hidden common cause.

Data Sources:
- co2_emissions.csv (climate data)
- covid_global.csv (epidemiology data)
- gdp.csv (economic data)
- population.csv (demographic data)

Output:
- Causal graph visualization
- Summary of causal relationships
"""

import os
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from causallearn.search.ConstraintBased.PC import pc
import matplotlib.pyplot as plt
import networkx as nx

# Data paths
CO2_PATH = '/shared/ASTRA/data/climate/co2_emissions.csv'
COVID_PATH = '/shared/ASTRA/data/epidemiology/covid_global.csv'
GDP_PATH = '/shared/ASTRA/data/economics/gdp.csv'
POPULATION_PATH = '/shared/ASTRA/data/economics/population.csv'
OUTPUT_DIR = '/shared/ASTRA/data/cross_domain/plots/'
REPORT_PATH = '/shared/ASTRA/hypotheses/cd007_results.txt'

# Create output directory if it doesn't exist
os.makedirs(OUTPUT_DIR, exist_ok=True)

def load_and_preprocess_data():
    """Load and preprocess cross-domain datasets, merging by country and year."""
    # Load datasets
    co2_df = pd.read_csv(CO2_PATH)
    covid_df = pd.read_csv(COVID_PATH)
    gdp_df = pd.read_csv(GDP_PATH)
    pop_df = pd.read_csv(POPULATION_PATH)
    
    # Preprocess CO2 data - aggregate to country-year level
    co2_agg = co2_df.groupby(['country', 'year']).agg({
        'co2': 'sum',
        'cumulative_co2': 'max',
        'temperature_change_from_co2': 'mean',
        'primary_energy_consumption': 'sum'
    }).reset_index()
    
    # Preprocess COVID data - aggregate to country-year level (latest data per year)
    covid_df['date'] = pd.to_datetime(covid_df['date'])
    covid_df['year'] = covid_df['date'].dt.year
    covid_agg = covid_df.groupby(['location', 'year']).agg({
        'total_cases': 'max',
        'total_deaths': 'max',
        'total_cases_per_million': 'mean',
        'total_deaths_per_million': 'mean',
        'gdp_per_capita': 'mean',
        'hospital_beds_per_thousand': 'mean',
        'median_age': 'mean'
    }).reset_index()
    covid_agg.rename(columns={'location': 'country'}, inplace=True)
    
    # Preprocess GDP and population data
    gdp_df.rename(columns={'Country Name': 'country', 'Year': 'year', 'Value': 'gdp'}, inplace=True)
    pop_df.rename(columns={'Country Name': 'country', 'Year': 'year', 'Value': 'population'}, inplace=True)
    
    # Merge datasets on country and year
    merged_df = co2_agg.merge(covid_agg, on=['country', 'year'], how='outer')
    merged_df = merged_df.merge(gdp_df[['country', 'year', 'gdp']], on=['country', 'year'], how='outer')
    merged_df = merged_df.merge(pop_df[['country', 'year', 'population']], on=['country', 'year'], how='outer')
    
    # Select relevant columns for causal analysis
    analysis_columns = [
        'co2', 'cumulative_co2', 'temperature_change_from_co2', 'primary_energy_consumption',
        'total_cases', 'total_deaths', 'total_cases_per_million', 'total_deaths_per_million',
        'gdp', 'population', 'gdp_per_capita', 'hospital_beds_per_thousand', 'median_age'
    ]
    
    # Drop rows with too many missing values
    merged_df = merged_df.dropna(thresh=merged_df.shape[1] * 0.5)
    
    # Impute remaining missing values with column means
    for col in analysis_columns:
        if col in merged_df.columns:
            merged_df[col].fillna(merged_df[col].mean(), inplace=True)
    
    return merged_df[analysis_columns]

def run_causal_discovery(data):
    """Run causal discovery on the merged dataset using the PC algorithm."""
    # Standardize the data
    scaler = StandardScaler()
    scaled_data = scaler.fit_transform(data)
    scaled_df = pd.DataFrame(scaled_data, columns=data.columns)
    
    # Run PC algorithm for causal structure discovery
    cg = pc(scaled_data, alpha=0.05, indep_test='fisherz')
    
    return cg, list(scaled_df.columns)

def visualize_causal_graph(causal_graph, node_names, output_path):
    """Visualize the causal graph using networkx."""
    G = nx.DiGraph()
    for i, name in enumerate(node_names):
        G.add_node(i, label=name)
    
    # Extract edges from the causal graph
    edges = []
    for i in range(len(node_names)):
        for j in range(len(node_names)):
            if causal_graph.G.graph[i][j] == -1 and causal_graph.G.graph[j][i] == -1:
                # Bidirectional edge
                edges.append((i, j))
            elif causal_graph.G.graph[i][j] == -1:
                # Directed edge i -> j
                edges.append((i, j))
    
    for edge in edges:
        G.add_edge(edge[0], edge[1])
    
    plt.figure(figsize=(12, 8))
    pos = nx.spring_layout(G)
    labels = nx.get_node_attributes(G, 'label')
    nx.draw(G, pos, with_labels=True, labels=labels, node_color='lightblue', 
            node_size=500, font_size=8, font_weight='bold', arrows=True)
    plt.title('Causal Graph for Climate-Economy-Pandemic System (CD-007)')
    plt.savefig(output_path)
    plt.close()

def write_report(causal_graph, node_names, output_path):
    """Write a summary report of the causal discovery results."""
    with open(output_path, 'w') as f:
        f.write('ASTRA Autonomous - Causal Discovery Results for CD-007\n')
        f.write('===============================================\n\n')
        f.write('Hypothesis: The causal structure connecting CO2, GDP, population, and pandemic outcomes\n')
        f.write('can be mapped — revealing whether climate drives economics, economics drives pandemic\n')
        f.write('response, or there\'s a hidden common cause.\n\n')
        f.write('Results:\n')
        edges = []
        for i in range(len(node_names)):
            for j in range(len(node_names)):
                if causal_graph.G.graph[i][j] == -1 and causal_graph.G.graph[j][i] == -1:
                    edges.append((node_names[i], node_names[j], 'bidirectional'))
                elif causal_graph.G.graph[i][j] == -1:
                    edges.append((node_names[i], node_names[j], 'directed'))
        if edges:
            f.write('A causal structure was identified with the following relationships:\n')
            for edge in edges:
                source, target, direction = edge
                f.write(f'- {source} <-> {target} ({direction} edge)\n' if direction == 'bidirectional' else f'- {source} -> {target} ({direction} edge)\n')
        else:
            f.write('No significant causal structure was identified beyond correlation.\n')
            f.write('This suggests the hypothesis may be false or the data is insufficient.\n')
        f.write('\nGenerated by ASTRA Autonomous on ' + pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S') + '\n')

def main():
    print('Loading and preprocessing data...')
    data = load_and_preprocess_data()
    print(f'Data loaded with shape: {data.shape}')
    
    print('Running causal discovery...')
    causal_graph, node_names = run_causal_discovery(data)
    print('Causal discovery completed.')
    
    print('Visualizing causal graph...')
    output_plot_path = os.path.join(OUTPUT_DIR, 'cd007_causal_graph.png')
    visualize_causal_graph(causal_graph, node_names, output_plot_path)
    print(f'Causal graph saved to {output_plot_path}')
    
    print('Writing results report...')
    write_report(causal_graph, node_names, REPORT_PATH)
    print(f'Report saved to {REPORT_PATH}')

if __name__ == '__main__':
    main()
