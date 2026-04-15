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

"""
ASTRA Live — Discovery Visualization
Interactive visualization for human-in-the-loop discovery.

Creates interactive dashboards and plots for:
  - SOM results (2D maps, cluster profiles)
  - Anomaly detection results
  - Multi-dimensional data exploration
  - Discovery timeline and hypothesis tracking

Uses Plotly for interactive visualizations that can be:
  - Viewed in Jupyter notebooks
  - Saved as standalone HTML files
  - Embedded in web dashboards
"""

import numpy as np
import warnings
from typing import Optional, Dict, List, Any, Tuple
from pathlib import Path
import json

# Handle optional imports
try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    warnings.warn("plotly not available. Install with: pip install plotly")

try:
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


class DiscoveryVisualizer:
    """
    Create interactive visualizations for discovery results.

    Example:
        >>> viz = DiscoveryVisualizer()
        >>> fig = viz.create_som_dashboard(som_result, filament_data)
        >>> fig.write_html('som_dashboard.html')
        >>> # Open in browser: som_dashboard.html
    """

    def __init__(self, theme: str = 'plotly_dark'):
        """
        Initialize visualizer.

        Args:
            theme: Plotly theme ('plotly_dark', 'plotly', 'plotly_white', etc.)
        """
        if not PLOTLY_AVAILABLE:
            raise ImportError("plotly is required for visualization. "
                            "Install with: pip install plotly")

        self.theme = theme
        self.color_scales = {
            'clusters': px.colors.qualitative.Safe,
            'anomalies': px.colors.sequential.Reds,
            'features': px.colors.sequential.Viridis
        }

    def create_som_dashboard(
        self,
        som_result: 'SOMResult',
        data: np.ndarray,
        feature_names: Optional[List[str]] = None,
        title: str = "SOM Discovery Dashboard"
    ) -> 'go.Figure':
        """
        Create interactive dashboard for SOM results.

        Dashboard includes:
        - U-matrix (distance between neighboring neurons)
        - Cluster map with sample counts
        - Feature component planes
        - 3D projection of data

        Args:
            som_result: Result from SOMDiscoverer.fit_predict()
            data: Original input data
            feature_names: Names of features
            title: Dashboard title

        Returns:
            Plotly figure object
        """
        if feature_names is None:
            feature_names = [f"Feature {i}" for i in range(data.shape[1])]

        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'U-Matrix (Distance Map)',
                'Cluster Map',
                'Feature Distribution by Cluster',
                '3D Projection'
            ),
            specs=[[{'type': 'heatmap'}, {'type': 'scatter'}],
                   [{'type': 'box'}, {'type': 'scatter3d'}]]
        )

        # U-matrix
        fig.add_trace(
            go.Heatmap(
                z=som_result.u_matrix,
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(x=0.45, len=0.25, title='Distance')
            ),
            row=1, col=1
        )

        # Cluster map
        # Create scatter plot of BMU coordinates colored by cluster
        # (Simplified - in practice would track BMU coords during SOM fitting)

        # Feature distribution (box plots for first 3 features)
        for i in range(min(3, data.shape[1])):
            fig.add_trace(
                go.Box(
                    y=data[:, i],
                    x=som_result.cluster_labels,
                    name=feature_names[i],
                    boxpoints='outliers'
                ),
                row=2, col=1
            )

        # 3D projection (using first 3 features or PCA)
        if data.shape[1] >= 3:
            proj_data = data[:, :3]
        else:
            # Pad with zeros if fewer than 3 features
            proj_data = np.zeros((data.shape[0], 3))
            proj_data[:, :data.shape[1]] = data

        for cluster_id in np.unique(som_result.cluster_labels):
            mask = som_result.cluster_labels == cluster_id
            fig.add_trace(
                go.Scatter3d(
                    x=proj_data[mask, 0],
                    y=proj_data[mask, 1],
                    z=proj_data[mask, 2],
                    mode='markers',
                    name=f'Cluster {cluster_id}',
                    marker=dict(
                        size=5,
                        color=cluster_id,
                        colorscale=self.color_scales['clusters'],
                        opacity=0.8
                    ),
                    showlegend=False
                ),
                row=2, col=2
            )

        fig.update_layout(
            title_text=title,
            template=self.theme,
            height=800,
            showlegend=True
        )

        return fig

    def create_anomaly_dashboard(
        self,
        anomaly_report: 'AnomalyReport',
        data: np.ndarray,
        feature_names: Optional[List[str]] = None,
        title: str = "Anomaly Detection Dashboard"
    ) -> 'go.Figure':
        """
        Create interactive dashboard for anomaly detection results.

        Dashboard includes:
        - Anomaly score distribution
        - Feature comparison (normal vs anomalous)
        - 2D/3D scatter with anomalies highlighted
        - Feature importance ranking

        Args:
            anomaly_report: Result from DiscoveryAnomalyDetector
            data: Original input data
            feature_names: Names of features
            title: Dashboard title

        Returns:
            Plotly figure object
        """
        if feature_names is None:
            feature_names = [f"Feature {i}" for i in range(data.shape[1])]

        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Anomaly Score Distribution',
                'Feature Comparison (Normal vs Anomalous)',
                '2D Projection with Anomalies',
                'Feature Importance'
            ),
            specs=[[{'type': 'histogram'}, {'type': 'box'}],
                   [{'type': 'scatter'}, {'type': 'bar'}]]
        )

        # Create binary labels
        labels = np.zeros(len(data), dtype=int)
        labels[anomaly_report.anomaly_indices] = 1

        # Anomaly score distribution
        # (Would need actual scores - simplified here)

        # Feature comparison
        for i in range(min(4, data.shape[1])):
            fig.add_trace(
                go.Box(
                    x=['Normal', 'Anomalous'],
                    y=[
                        data[np.where(labels == 0)[0], i],
                        data[anomaly_report.anomaly_indices, i]
                    ],
                    name=feature_names[i],
                    showlegend=False
                ),
                row=1, col=2
            )

        # 2D projection
        if data.shape[1] >= 2:
            fig.add_trace(
                go.Scatter(
                    x=data[:, 0],
                    y=data[:, 1],
                    mode='markers',
                    marker=dict(
                        color=labels,
                        colorscale=[[0, 'blue'], [1, 'red']],
                        size=8,
                        opacity=0.7
                    ),
                    name='Samples',
                    text=['Anomaly' if l == 1 else 'Normal' for l in labels],
                    showlegend=False
                ),
                row=2, col=1
            )

        # Feature importance
        if anomaly_report.feature_importance:
            features = list(anomaly_report.feature_importance.keys())
            importance = list(anomaly_report.feature_importance.values())

            fig.add_trace(
                go.Bar(
                    x=features,
                    y=importance,
                    marker_color='lightblue',
                    showlegend=False
                ),
                row=2, col=2
            )

        fig.update_layout(
            title_text=title,
            template=self.theme,
            height=800
        )

        return fig

    def create_feature_scatter_matrix(
        self,
        data: np.ndarray,
        labels: Optional[np.ndarray] = None,
        feature_names: Optional[List[str]] = None,
        max_features: int = 5
    ) -> 'go.Figure':
        """
        Create scatter matrix for multi-dimensional exploration.

        Args:
            data: Input data (n_samples, n_features)
            labels: Optional cluster/anomaly labels
            feature_names: Names of features
            max_features: Maximum number of features to show

        Returns:
            Plotly figure object
        """
        if feature_names is None:
            feature_names = [f"Feature {i}" for i in range(data.shape[1])]

        n_features = min(max_features, data.shape[1])

        # Create DataFrame for plotly express
        import pandas as pd
        df = pd.DataFrame(data[:, :n_features], columns=feature_names[:n_features])

        if labels is not None:
            df['label'] = ['Anomaly' if l == 1 else 'Normal' for l in labels]

        fig = px.scatter_matrix(
            df,
            dimensions=feature_names[:n_features],
            color='label' if labels is not None else None,
            title="Feature Scatter Matrix",
            template=self.theme
        )

        fig.update_layout(height=800)

        return fig

    def create_discovery_timeline(
        self,
        discoveries: List[Dict[str, Any]],
        title: str = "Discovery Timeline"
    ) -> 'go.Figure':
        """
        Create timeline visualization of discoveries.

        Args:
            discoveries: List of discovery dicts with 'timestamp', 'type', 'confidence'
            title: Chart title

        Returns:
            Plotly figure object
        """
        if not discoveries:
            # Create empty figure
            fig = go.Figure()
            fig.add_annotation(text="No discoveries to display",
                             xref="paper", yref="paper",
                             x=0.5, y=0.5, showarrow=False)
            return fig

        # Extract data
        timestamps = [d.get('timestamp', i) for i, d in enumerate(discoveries)]
        types = [d.get('type', 'Unknown') for d in discoveries]
        confidences = [d.get('confidence', 0.5) for d in discoveries]

        fig = go.Figure()

        # Group by type
        unique_types = list(set(types))
        for i, discovery_type in enumerate(unique_types):
            mask = [t == discovery_type for t in types]

            fig.add_trace(
                go.Scatter(
                    x=[timestamps[j] for j, m in enumerate(mask) if m],
                    y=[confidences[j] for j, m in enumerate(mask) if m],
                    mode='markers+lines',
                    name=discovery_type,
                    marker=dict(size=10),
                    connectgaps=False
                )
            )

        fig.update_layout(
            title=title,
            xaxis_title='Discovery Index',
            yaxis_title='Confidence',
            template=self.theme,
            hovermode='closest'
        )

        return fig

    def create_correlation_heatmap(
        self,
        data: np.ndarray,
        feature_names: Optional[List[str]] = None,
        title: str = "Feature Correlation Matrix"
    ) -> 'go.Figure':
        """
        Create correlation heatmap for features.

        Args:
            data: Input data (n_samples, n_features)
            feature_names: Names of features
            title: Chart title

        Returns:
            Plotly figure object
        """
        if feature_names is None:
            feature_names = [f"Feature {i}" for i in range(data.shape[1])]

        # Compute correlation matrix
        corr = np.corrcoef(data.T)

        fig = go.Figure(
            data=go.Heatmap(
                z=corr,
                x=feature_names,
                y=feature_names,
                colorscale='RdBu',
                zmid=0,
                colorbar=dict(title='Correlation')
            )
        )

        fig.update_layout(
            title=title,
            template=self.theme,
            width=800,
            height=800
        )

        return fig

    def export_html(
        self,
        figure: 'go.Figure',
        output_path: str,
        include_plotly: bool = True
    ) -> None:
        """
        Export figure as standalone HTML file.

        Args:
            figure: Plotly figure object
            output_path: Path to save HTML file
            include_plotly: Whether to include Plotly.js library
        """
        figure.write_html(output_path, include_plotlyjs=include_plotly)
        print(f"Exported visualization to {output_path}")

    def create_dashboard(
        self,
        som_result: Optional['SOMResult'] = None,
        anomaly_report: Optional['AnomalyReport'] = None,
        data: Optional[np.ndarray] = None,
        feature_names: Optional[List[str]] = None,
        output_path: str = "discovery_dashboard.html"
    ) -> str:
        """
        Create comprehensive discovery dashboard combining all visualizations.

        Args:
            som_result: Optional SOM result
            anomaly_report: Optional anomaly detection result
            data: Input data
            feature_names: Feature names
            output_path: Path to save dashboard

        Returns:
            Path to saved HTML file
        """
        from plotly.subplots import make_subplots

        # Determine number of subplots based on available results
        has_som = som_result is not None
        has_anomaly = anomaly_report is not None

        if not has_som and not has_anomaly:
            raise ValueError("At least one of som_result or anomaly_report must be provided")

        # Create multi-page dashboard
        # (Simplified version - would use Dash for full interactive app)

        if has_som and data is not None:
            fig = self.create_som_dashboard(som_result, data, feature_names)
        elif has_anomaly and data is not None:
            fig = self.create_anomaly_dashboard(anomaly_report, data, feature_names)
        else:
            # Create overview figure
            fig = go.Figure()
            fig.add_annotation(
                text="Discovery Dashboard - No results to display",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )

        self.export_html(fig, output_path)

        return output_path


class FilamentDiscoveryViz(DiscoveryVisualizer):
    """
    Specialized visualization for filament discovery.

    Creates domain-specific visualizations for:
    - HGBS filament properties
    - Core spacing distributions
    - Supercriticality analysis
    - Regional comparisons
    """

    def create_filament_property_dashboard(
        self,
        filament_data: np.ndarray,
        region_names: Optional[List[str]] = None,
        feature_names: Optional[List[str]] = None
    ) -> 'go.Figure':
        """
        Create dashboard for filament property analysis.

        Args:
            filament_data: Filament feature array (n_filaments, n_features)
            region_names: Names of HGBS regions
            feature_names: Filament property names

        Returns:
            Plotly figure object
        """
        if feature_names is None:
            feature_names = ['Width (pc)', 'Spacing (pc)', 'N_cores',
                           'Density', 'M/L (M_sun/pc)', 'Aspect Ratio']

        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Width Distribution',
                'Spacing Distribution',
                'Width vs Spacing',
                'Regional Summary'
            ),
            specs=[[{'type': 'histogram'}, {'type': 'histogram'}],
                   [{'type': 'scatter'}, {'type': 'bar'}]]
        )

        # Width distribution
        if filament_data.shape[1] > 0:
            fig.add_trace(
                go.Histogram(x=filament_data[:, 0], name='Width',
                           marker_color='lightblue', showlegend=False),
                row=1, col=1
            )

        # Spacing distribution
        if filament_data.shape[1] > 2:
            fig.add_trace(
                go.Histogram(x=filament_data[:, 2], name='Spacing',
                           marker_color='lightgreen', showlegend=False),
                row=1, col=2
            )

        # Width vs Spacing scatter
        if filament_data.shape[1] > 2:
            fig.add_trace(
                go.Scatter(
                    x=filament_data[:, 0],
                    y=filament_data[:, 2],
                    mode='markers',
                    marker=dict(size=8, opacity=0.6),
                    name='Filaments',
                    showlegend=False
                ),
                row=2, col=1
            )

        # Regional summary (if region names provided)
        if region_names is not None:
            unique_regions = list(set(region_names))
            counts = [region_names.count(r) for r in unique_regions]

            fig.add_trace(
                go.Bar(
                    x=unique_regions,
                    y=counts,
                    marker_color='lightcoral',
                    showlegend=False
                ),
                row=2, col=2
            )

        fig.update_layout(
            title_text="HGBS Filament Properties Dashboard",
            template=self.theme,
            height=800,
            showlegend=False
        )

        return fig

    def create_spacing_comparison_plot(
        self,
        spacings: Dict[str, np.ndarray],
        reference_value: float = 0.213,
        title: str = "Core Spacing Comparison"
    ) -> 'go.Figure':
        """
        Create violin/box plot comparing spacing across regions.

        Args:
            spacings: Dict mapping region names to spacing arrays
            reference_value: Reference spacing (pc) for comparison
            title: Plot title

        Returns:
            Plotly figure object
        """
        fig = go.Figure()

        for region, values in spacings.items():
            fig.add_trace(
                go.Box(
                    y=values,
                    name=region,
                    boxpoints='outliers'
                )
            )

        # Add reference line
        fig.add_hline(
            y=reference_value,
            line_dash="dash",
            line_color="red",
            annotation_text=f"Reference: {reference_value} pc"
        )

        fig.update_layout(
            title=title,
            yaxis_title="Core Spacing (pc)",
            template=self.theme,
            height=600
        )

        return fig


# Convenience functions
def quick_viz(
    data: np.ndarray,
    labels: Optional[np.ndarray] = None,
    viz_type: str = 'scatter',
    output_path: str = 'quick_viz.html'
) -> None:
    """
    Quick visualization helper.

    Args:
        data: Input data
        labels: Optional labels
        viz_type: Type of visualization ('scatter', 'correlation', 'dashboard')
        output_path: Where to save HTML
    """
    viz = DiscoveryVisualizer()

    if viz_type == 'scatter':
        fig = viz.create_feature_scatter_matrix(data, labels)
    elif viz_type == 'correlation':
        fig = viz.create_correlation_heatmap(data)
    else:
        fig = go.Figure()
        fig.add_annotation(text="Unknown visualization type",
                         xref="paper", yref="paper",
                         x=0.5, y=0.5, showarrow=False)

    viz.export_html(fig, output_path)


if __name__ == '__main__':
    # Test visualization
    print("Testing Discovery Visualization...")

    # Generate test data
    np.random.seed(42)
    data = np.random.randn(100, 4)

    # Create correlation heatmap
    viz = DiscoveryVisualizer()
    fig = viz.create_correlation_heatmap(
        data,
        feature_names=['Width', 'Spacing', 'Density', 'Temperature']
    )

    output_file = '/tmp/test_viz.html'
    viz.export_html(fig, output_file)
    print(f"Saved test visualization to {output_file}")
