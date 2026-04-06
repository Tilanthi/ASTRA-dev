"""
ASTRA Live — Unsupervised Structure Discovery
Discovers hidden structures in astrophysical data without theoretical priors.

Inspired by particle physics ML approaches (Abdelhaq et al., Quevedo et al.):
- Standard Model structure discovered from data alone
- Conserved quantities emerge from clustering analysis
- Symmetry patterns revealed without theoretical input

This module enables ASTRA to discover patterns it wasn't explicitly looking for.
"""
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import warnings

# Handle ML library imports gracefully
try:
    from sklearn.decomposition import PCA
    from sklearn.manifold import TSNE
    from sklearn.cluster import KMeans, AgglomerativeClustering, DBSCAN
    from sklearn.mixture import GaussianMixture
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import silhouette_score, calinski_harabasz_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    warnings.warn("scikit-learn not available. Some features will be limited.")

try:
    import umap
    UMAP_AVAILABLE = True
except ImportError:
    UMAP_AVAILABLE = False


class DiscoveryType(Enum):
    """Types of structures that can be discovered."""
    CLUSTER = "cluster"  # Distinct groups in parameter space
    MANIFOLD = "manifold"  # Nonlinear geometric structure
    INVARIANT = "invariant"  # Conserved quantities
    SYMMETRY = "symmetry"  # Symmetry relationships
    TRAJECTORY = "trajectory"  # Evolutionary sequences (like Regge trajectories)
    OUTLIER = "outlier"  # Anomalous objects


@dataclass
class DiscoveredStructure:
    """A structure discovered in the data."""
    name: str
    discovery_type: DiscoveryType
    description: str
    confidence: float
    locations: np.ndarray  # Indices of objects in this structure
    mathematical_form: Optional[str] = None
    physical_interpretation: Optional[str] = None
    cross_domain_analogy: Optional[str] = None


@dataclass
class ConservedQuantity:
    """A quantity that remains approximately constant across data."""
    name: str
    conservation_type: str  # 'cluster_invariant', 'ratio_invariant', 'linear_combination'
    strength: float  # Higher = more strongly conserved
    mathematical_form: str
    variance_explained: float


@dataclass
class SymmetryGroup:
    """Objects related by symmetry transformation."""
    group_members: List[int]  # Indices of objects
    transformation: str  # Description of symmetry
    strength: float


@dataclass
class EvolutionaryTrajectory:
    """
    Sequence of objects showing progression (like Regge trajectories).

    Inspired by Paper 1's discovery of Regge trajectories from data alone.
    """
    trajectory_id: int
    object_indices: List[int]
    progression_variable: str  # What parameter increases along trajectory
    mathematical_relation: str  # e.g., "J ∝ m²" for Regge
    confidence: float


class UnsupervisedStructureDiscoverer:
    """
    Discovers hidden structures in astrophysical data without theoretical priors.

    Key innovation: Let data speak first, interpret theoretically later.

    Methodology inspired by AI rediscovery of Standard Model structure:
    1. Multi-method dimensionality reduction (PCA, t-SNE, UMAP)
    2. Multi-algorithm clustering (k-means, hierarchical, DBSCAN, GMM)
    3. Search for invariants (like baryon number, strangeness)
    4. Symmetry pattern detection (like isospin multiplets)
    5. Trajectory detection (like Regge trajectories)
    """

    def __init__(self):
        if not SKLEARN_AVAILABLE:
            warnings.warn("Running without scikit-learn - functionality limited")

        self.scaler = StandardScaler() if SKLEARN_AVAILABLE else None
        self.structures = []

    def discover_latent_structure(self,
                                   data: np.ndarray,
                                   variable_names: List[str],
                                   object_names: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Comprehensive unsupervised analysis to discover hidden structures.

        Args:
            data: Shape (n_objects, n_features) - astrophysical objects and their properties
            variable_names: Names of the features/columns
            object_names: Optional names of objects (for interpretability)

        Returns:
            Dictionary containing all discovered structures
        """
        results = {
            'dimensionality_reduction': {},
            'clustering': {},
            'invariants': [],
            'symmetries': [],
            'trajectories': [],
            'outliers': []
        }

        n_objects, n_features = data.shape

        # Standardize data
        if self.scaler is not None:
            data_scaled = self.scaler.fit_transform(data)
        else:
            data_scaled = (data - np.mean(data, axis=0)) / np.std(data, axis=0)

        # 1. Dimensionality Reduction
        if SKLEARN_AVAILABLE:
            results['dimensionality_reduction'] = self._dimensionality_reduction(
                data_scaled, variable_names
            )

        # 2. Clustering Analysis
        if SKLEARN_AVAILABLE:
            results['clustering'] = self._multi_method_clustering(
                data_scaled, variable_names
            )

        # 3. Search for Conserved Quantities (like baryon number, strangeness)
        results['invariants'] = self._discover_conserved_quantities(
            data, variable_names, results.get('clustering', {})
        )

        # 4. Symmetry Pattern Detection (like isospin multiplets)
        results['symmetries'] = self._discover_symmetry_patterns(
            data, variable_names, results.get('clustering', {})
        )

        # 5. Evolutionary Trajectories (like Regge trajectories)
        results['trajectories'] = self._discover_trajectories(
            data, variable_names, results.get('clustering', {})
        )

        # 6. Outlier Detection
        results['outliers'] = self._detect_outliers(
            data, variable_names
        )

        return results

    def _dimensionality_reduction(self,
                                   data: np.ndarray,
                                   variable_names: List[str]) -> Dict[str, Any]:
        """Apply multiple dimensionality reduction techniques."""
        results = {}

        # PCA (linear)
        pca = PCA(n_components=min(3, data.shape[1]))
        pca_result = pca.fit_transform(data)

        results['pca'] = {
            'transformed': pca_result,
            'variance_explained': pca.explained_variance_ratio_,
            'components': pca.components_,
            'interpretation': self._interpret_pca(pca, variable_names)
        }

        # t-SNE (nonlinear, local structure)
        if data.shape[0] > 5:  # t-SNE needs enough points
            tsne = TSNE(n_components=2, random_state=42, perplexity=min(30, data.shape[0]-1))
            tsne_result = tsne.fit_transform(data)

            results['tsne'] = {
                'transformed': tsne_result,
                'interpretation': 'Nonlinear embedding preserving local structure'
            }

        # UMAP (if available)
        if UMAP_AVAILABLE and data.shape[0] > 5:
            reducer = umap.UMAP(n_components=2, random_state=42)
            umap_result = reducer.fit_transform(data)

            results['umap'] = {
                'transformed': umap_result,
                'interpretation': 'Nonlinear embedding preserving both local and global structure'
            }

        return results

    def _interpret_pca(self, pca: PCA, variable_names: List[str]) -> List[Dict]:
        """Interpret PCA components in terms of original variables."""
        interpretations = []

        for i, (component, var_exp) in enumerate(zip(
            pca.components_, pca.explained_variance_ratio_
        )):
            # Find variables with highest absolute loading
            loadings = [(abs(val), var, val) for var, val in zip(variable_names, component)]
            loadings.sort(reverse=True, key=lambda x: x[0])

            dominant_vars = [var for _, var, sign in loadings[:3]]
            signs = [sign for _, var, sign in loadings[:3]]

            interpretations.append({
                'component': f'PC{i+1}',
                'variance_explained': var_exp,
                'dominant_variables': dominant_vars,
                'interpretation': f"Combination of {', '.join(dominant_vars)} ({var_exp:.1%} variance)"
            })

        return interpretations

    def _multi_method_clustering(self,
                                  data: np.ndarray,
                                  variable_names: List[str]) -> Dict[str, Any]:
        """Apply multiple clustering algorithms and find consensus."""
        results = {}
        n_objects = data.shape[0]

        # Determine reasonable number of clusters
        max_clusters = min(8, n_objects // 5)

        # K-means
        if n_objects > 3:
            kmeans_scores = []
            for k in range(2, max_clusters + 1):
                kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
                labels = kmeans.fit_predict(data)
                if len(np.unique(labels)) > 1:
                    score = silhouette_score(data, labels)
                    kmeans_scores.append((k, score, labels))

            if kmeans_scores:
                best_k, best_score, best_labels = max(kmeans_scores, key=lambda x: x[1])
                results['kmeans'] = {
                    'n_clusters': best_k,
                    'labels': best_labels,
                    'silhouette_score': best_score,
                    'interpretation': self._interpret_clusters(data, best_labels, variable_names)
                }

        # Hierarchical
        if n_objects > 3:
            hierarchical = AgglomerativeClustering(n_clusters=max_clusters)
            h_labels = hierarchical.fit_predict(data)

            results['hierarchical'] = {
                'n_clusters': max_clusters,
                'labels': h_labels,
                'interpretation': self._interpret_clusters(data, h_labels, variable_names)
            }

        # DBSCAN (density-based, can find arbitrary shapes)
        if n_objects > 5:
            dbscan = DBSCAN(eps=0.5 * np.std(data), min_samples=max(2, n_objects // 10))
            db_labels = dbscan.fit_predict(data)

            n_clusters = len(set(db_labels)) - (1 if -1 in db_labels else 0)
            n_noise = list(db_labels).count(-1)

            results['dbscan'] = {
                'n_clusters': n_clusters,
                'noise_points': n_noise,
                'labels': db_labels,
                'interpretation': self._interpret_clusters(data, db_labels, variable_names)
            }

        # Gaussian Mixture Model (probabilistic)
        if n_objects > 3:
            best_gmm_score = -np.inf
            best_gmm = None

            for k in range(2, max_clusters + 1):
                gmm = GaussianMixture(n_components=k, random_state=42)
                gmm.fit(data)
                score = gmm.bic(data)  # Lower is better for BIC

                if score < best_gmm_score or best_gmm is None:
                    best_gmm_score = score
                    best_gmm = gmm

            if best_gmm is not None:
                gm_labels = best_gmm.predict(data)
                results['gaussian_mixture'] = {
                    'n_clusters': best_gmm.n_components,
                    'labels': gm_labels,
                    'probabilities': best_gmm.predict_proba(data),
                    'bic': best_gmm_score,
                    'interpretation': self._interpret_clusters(data, gm_labels, variable_names)
                }

        # Find consensus clusters (methods that agree)
        if len(results) > 1:
            results['consensus'] = self._find_consensus_clusters(results, n_objects)

        return results

    def _interpret_clusters(self,
                             data: np.ndarray,
                             labels: np.ndarray,
                             variable_names: List[str]) -> List[Dict]:
        """Interpret what each cluster represents in physical terms."""
        interpretations = []
        unique_labels = np.unique(labels)

        for label in unique_labels:
            if label == -1:  # Noise in DBSCAN
                continue

            mask = labels == label
            cluster_data = data[mask]
            n_members = np.sum(mask)

            # Cluster statistics
            cluster_mean = np.mean(cluster_data, axis=0)
            cluster_std = np.std(cluster_data, axis=0)

            # Find defining characteristics
            characteristics = []
            for i, var in enumerate(variable_names):
                overall_mean = np.mean(data[:, i])
                overall_std = np.std(data[:, i])

                # Is this cluster notably different from overall?
                z_score = abs(cluster_mean[i] - overall_mean) / (overall_std + 1e-10)

                if z_score > 1.0:  # Notably different
                    direction = "higher" if cluster_mean[i] > overall_mean else "lower"
                    characteristics.append(
                        f"{var}: {direction} than average ({z_score:.1f}σ)"
                    )

            interpretation = {
                'cluster_id': int(label),
                'n_members': int(n_members),
                'defining_characteristics': characteristics,
                'centroid': cluster_mean
            }

            interpretations.append(interpretation)

        return interpretations

    def _find_consensus_clusters(self,
                                  clustering_results: Dict,
                                  n_objects: int) -> Dict[str, Any]:
        """Find clusters that multiple methods agree on."""
        # Collect all labelings
        all_labels = []
        method_names = []

        for method, result in clustering_results.items():
            if 'labels' in result:
                all_labels.append(result['labels'])
                method_names.append(method)

        if not all_labels:
            return {}

        # Build co-occurrence matrix
        n_methods = len(all_labels)
        cooccurrence = np.zeros((n_objects, n_objects))

        for labels in all_labels:
            for i in range(n_objects):
                for j in range(i+1, n_objects):
                    if labels[i] == labels[j] and labels[i] != -1:
                        cooccurrence[i, j] += 1
                        cooccurrence[j, i] += 1

        # Normalize
        cooccurrence /= n_methods

        # Find consensus clusters (high co-occurrence)
        consensus_threshold = 0.6  # 60% of methods agree
        visited = set()
        consensus_clusters = []

        for i in range(n_objects):
            if i in visited:
                continue

            # Find all objects that consistently cluster with i
            cluster_members = [i]
            for j in range(i+1, n_objects):
                if cooccurrence[i, j] >= consensus_threshold:
                    cluster_members.append(j)

            if len(cluster_members) > 1:
                visited.update(cluster_members)
                consensus_clusters.append(cluster_members)

        return {
            'n_consensus_clusters': len(consensus_clusters),
            'clusters': consensus_clusters,
            'threshold': consensus_threshold
        }

    def _discover_conserved_quantities(self,
                                        data: np.ndarray,
                                        variable_names: List[str],
                                        clustering_results: Dict) -> List[ConservedQuantity]:
        """
        Discover quantities that remain approximately constant across clusters.

        Inspired by discovery of baryon number, strangeness, charm in particle physics.
        """
        conserved = []

        # Get cluster labels from most reliable method
        labels = None
        if 'gaussian_mixture' in clustering_results:
            labels = clustering_results['gaussian_mixture']['labels']
        elif 'kmeans' in clustering_results:
            labels = clustering_results['kmeans']['labels']

        if labels is None:
            return conserved

        unique_labels = np.unique(labels)
        unique_labels = unique_labels[unique_labels != -1]  # Remove noise

        if len(unique_labels) < 2:
            return conserved

        # Check each variable for cluster invariance
        for i, var in enumerate(variable_names):
            values = data[:, i]

            # Within-cluster vs between-cluster variance
            within_var = 0
            between_var = 0

            overall_mean = np.mean(values)

            for label in unique_labels:
                cluster_values = values[labels == label]
                cluster_mean = np.mean(cluster_values)

                within_var += np.sum((cluster_values - cluster_mean)**2)
                between_var += len(cluster_values) * (cluster_mean - overall_mean)**2

            within_var /= len(values)
            between_var /= len(values)

            # Conservation strength: ratio of between to within variance
            if within_var > 1e-10:
                conservation_strength = between_var / within_var
            else:
                conservation_strength = between_var

            if conservation_strength > 2.0:  # Notably conserved
                conserved.append(ConservedQuantity(
                    name=var,
                    conservation_type='cluster_invariant',
                    strength=conservation_strength,
                    mathematical_form=f'{var} ≈ constant within clusters',
                    variance_explained=between_var / (between_var + within_var)
                ))

        # Check for ratio invariants (like mass ratios in particle physics)
        for i in range(len(variable_names)):
            for j in range(i+1, len(variable_names)):
                # Avoid division by zero
                denominator = data[:, j] + np.median(np.abs(data[:, j])) + 1e-10
                ratio = data[:, i] / denominator

                # Check if ratio is constant
                ratio_mean = np.mean(ratio)
                ratio_std = np.std(ratio)

                if ratio_std > 1e-10:
                    cv = ratio_std / abs(ratio_mean)  # Coefficient of variation
                else:
                    cv = 0

                if cv < 0.1:  # Less than 10% variation - very constant!
                    conserved.append(ConservedQuantity(
                        name=f'{variable_names[i]}/{variable_names[j]}',
                        conservation_type='ratio_invariant',
                        strength=1.0 / (cv + 1e-10),
                        mathematical_form=f'{variable_names[i]} ∝ {variable_names[j]}',
                        variance_explained=1.0 - cv
                    ))

        return conserved

    def _discover_symmetry_patterns(self,
                                     data: np.ndarray,
                                     variable_names: List[str],
                                     clustering_results: Dict) -> List[SymmetryGroup]:
        """
        Discover groups of objects related by symmetry transformations.

        Inspired by isospin multiplets and flavor symmetries in particle physics.
        """
        symmetries = []

        # Get cluster labels
        labels = None
        if 'gaussian_mixture' in clustering_results:
            labels = clustering_results['gaussian_mixture']['labels']
        elif 'kmeans' in clustering_results:
            labels = clustering_results['kmeans']['labels']

        if labels is None:
            return symmetries

        unique_labels = np.unique(labels)
        unique_labels = unique_labels[unique_labels != -1]

        # Look for clusters with similar structure
        for i, label1 in enumerate(unique_labels):
            for label2 in unique_labels[i+1:]:
                data1 = data[labels == label1]
                data2 = data[labels == label2]

                # Test if clusters are related by simple transformation
                transformation = self._find_symmetry_transformation(data1, data2, variable_names)

                if transformation is not None:
                    symmetries.append(SymmetryGroup(
                        group_members=[
                            np.where(labels == label1)[0].tolist(),
                            np.where(labels == label2)[0].tolist()
                        ],
                        transformation=transformation,
                        strength=0.8  # Would need proper calculation
                    ))

        return symmetries

    def _find_symmetry_transformation(self,
                                       data1: np.ndarray,
                                       data2: np.ndarray,
                                       variable_names: List[str]) -> Optional[str]:
        """Test if two clusters are related by a symmetry transformation."""
        if len(data1) < 2 or len(data2) < 2:
            return None

        # Check for scaling symmetry
        mean1 = np.mean(data1, axis=0)
        mean2 = np.mean(data2, axis=0)

        # Can we relate them by simple scaling?
        with np.errstate(divide='ignore', invalid='ignore'):
            ratios = mean2 / (mean1 + 1e-10)

        # Check if ratios are approximately constant
        valid_ratios = ratios[np.isfinite(ratios)]
        if len(valid_ratios) < 2:
            return None

        ratio_mean = np.mean(valid_ratios)
        ratio_std = np.std(valid_ratios)

        if ratio_std / abs(ratio_mean) < 0.2:  # Within 20% of constant ratio
            # Check which variables scale most similarly
            scaling_vars = [var for var, r in zip(variable_names, ratios)
                          if np.isfinite(r) and abs(r - ratio_mean) / ratio_mean < 0.3]

            if scaling_vars:
                return f"Scaling symmetry: {scaling_vars} scaled by {ratio_mean:.2f}"

        # Check for translation symmetry
        diffs = mean2 - mean1
        if np.std(diffs) / (np.mean(np.abs(diffs)) + 1e-10) < 0.2:
            return f"Translation symmetry in direction: {diffs}"

        return None

    def _discover_trajectories(self,
                                data: np.ndarray,
                                variable_names: List[str],
                                clustering_results: Dict) -> List[EvolutionaryTrajectory]:
        """
        Discover evolutionary sequences in the data.

        Inspired by Regge trajectories in particle physics (J ∝ m² relation).
        """
        trajectories = []

        # Look for power-law relationships (J ∝ m^α type relations)
        for i, var_x in enumerate(variable_names):
            for j, var_y in enumerate(variable_names):
                if i == j:
                    continue

                x = data[:, i]
                y = data[:, j]

                # Check for power law: log(y) vs log(x)
                with np.errstate(divide='ignore', invalid='ignore'):
                    log_x = np.log(x + np.min(x[x > 0]) * 0.1)
                    log_y = np.log(y + np.min(y[y > 0]) * 0.1)

                # Fit linear in log-log
                valid = np.isfinite(log_x) & np.isfinite(log_y)
                if np.sum(valid) < 3:
                    continue

                coeffs = np.polyfit(log_x[valid], log_y[valid], 1)
                correlation = np.corrcoef(log_x[valid], log_y[valid])[0, 1]

                # Strong power law?
                if abs(correlation) > 0.85:
                    trajectories.append(EvolutionaryTrajectory(
                        trajectory_id=len(trajectories),
                        object_indices=np.where(valid)[0].tolist(),
                        progression_variable=var_x,
                        mathematical_relation=f"{var_y} ∝ {var_x}^{coeff[0]:.2f}",
                        confidence=abs(correlation)
                    ))

        return trajectories

    def _detect_outliers(self,
                         data: np.ndarray,
                         variable_names: List[str]) -> Dict[str, Any]:
        """Detect anomalous objects that don't fit general patterns."""
        outliers = {}

        # Simple statistical outlier detection
        n_objects, n_features = data.shape

        # Z-score based
        z_scores = np.abs((data - np.mean(data, axis=0)) / (np.std(data, axis=0) + 1e-10))
        outlier_mask = np.any(z_scores > 3.0, axis=1)

        outliers['statistical'] = {
            'n_outliers': int(np.sum(outlier_mask)),
            'outlier_indices': np.where(outlier_mask)[0].tolist(),
            'threshold': '3σ from mean'
        }

        # Distance-based (far from centroid)
        centroid = np.mean(data, axis=0)
        distances = np.sqrt(np.sum((data - centroid)**2, axis=1))
        dist_threshold = np.mean(distances) + 2 * np.std(distances)

        distance_outliers = distances > dist_threshold
        outliers['distance_based'] = {
            'n_outliers': int(np.sum(distance_outliers)),
            'outlier_indices': np.where(distance_outliers)[0].tolist(),
            'threshold': f'{dist_threshold:.2f} from centroid'
        }

        return outliers

    def generate_discovery_report(self,
                                   results: Dict[str, Any],
                                   variable_names: List[str]) -> str:
        """Generate human-readable discovery report."""
        lines = []
        lines.append("=" * 80)
        lines.append("UNSUPERVISED STRUCTURE DISCOVERY REPORT")
        lines.append("=" * 80)

        # Dimensionality reduction findings
        if 'dimensionality_reduction' in results:
            lines.append("\n1. DIMENSIONALITY REDUCTION")
            lines.append("-" * 80)

            if 'pca' in results['dimensionality_reduction']:
                pca = results['dimensionality_reduction']['pca']
                lines.append(f"\nPrincipal Components Analysis:")
                for interp in pca['interpretation']:
                    lines.append(f"  • {interp['interpretation']}")

        # Clustering findings
        if 'clustering' in results:
            lines.append("\n2. CLUSTERING ANALYSIS")
            lines.append("-" * 80)

            if 'kmeans' in results['clustering']:
                km = results['clustering']['kmeans']
                lines.append(f"\nK-means clustering (k={km['n_clusters']}, silhouette={km['silhouette_score']:.3f}):")

                for interp in km['interpretation']:
                    lines.append(f"  • Cluster {interp['cluster_id']}: {interp['n_members']} objects")
                    for char in interp['defining_characteristics'][:2]:
                        lines.append(f"    - {char}")

        # Conserved quantities
        if results.get('invariants'):
            lines.append("\n3. CONSERVED QUANTITIES")
            lines.append("-" * 80)

            for inv in sorted(results['invariants'], key=lambda x: -x.strength)[:5]:
                lines.append(f"  • {inv.name}: {inv.mathematical_form}")
                lines.append(f"    Strength: {inv.strength:.2f}, Variance explained: {inv.variance_explained:.1%}")

        # Symmetries
        if results.get('symmetries'):
            lines.append("\n4. SYMMETRY PATTERNS")
            lines.append("-" * 80)

            for sym in results['symmetries'][:5]:
                lines.append(f"  • {sym.transformation}")
                lines.append(f"    Affects {sum(len(g) for g in sym.group_members)} objects")

        # Trajectories
        if results.get('trajectories'):
            lines.append("\n5. EVOLUTIONARY TRAJECTORIES")
            lines.append("-" * 80)

            for traj in sorted(results['trajectories'], key=lambda t: -t.confidence)[:3]:
                lines.append(f"  • {traj.mathematical_relation}")
                lines.append(f"    Confidence: {traj.confidence:.3f}, {len(traj.object_indices)} objects")

        # Outliers
        if results.get('outliers'):
            lines.append("\n6. ANOMALOUS OBJECTS")
            lines.append("-" * 80)

            if 'statistical' in results['outliers']:
                stat = results['outliers']['statistical']
                lines.append(f"  • {stat['n_outliers']} statistical outliers (>3σ)")

        lines.append("\n" + "=" * 80)

        return "\n".join(lines)


# Demonstration
if __name__ == "__main__":
    print("Unsupervised Structure Discovery Module")
    print("=" * 80)
    print("\nThis module discovers hidden structures in astrophysical data")
    print("without theoretical priors, inspired by particle physics ML.")
    print("\nKey capabilities:")
    print("  1. Multi-method dimensionality reduction (PCA, t-SNE, UMAP)")
    print("  2. Multi-algorithm clustering (k-means, hierarchical, DBSCAN, GMM)")
    print("  3. Conserved quantity discovery (like baryon number, strangeness)")
    print("  4. Symmetry pattern detection (like isospin multiplets)")
    print("  5. Evolutionary trajectories (like Regge trajectories)")
    print("  6. Outlier detection")
    print("\nUsage:")
    print("  discoverer = UnsupervisedStructureDiscoverer()")
    print("  results = discoverer.discover_latent_structure(data, variable_names)")
    print("  report = discoverer.generate_discovery_report(results, variable_names)")
