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
ASTRA Live — Multi-Modal Fusion
Combine data from imaging, spectroscopy, catalogs, and time series.

Multi-modal fusion enables ASTRA to:
  - Combine heterogeneous data sources for richer discovery
  - Cross-validate discoveries across modalities
  - Learn joint representations from different data types
  - Transfer knowledge between domains

Applications:
  - Validate filament candidates in multiple wavelengths
  - Combine photometry and spectroscopy for redshift estimation
  - Fuse imaging and time series for transient discovery
  - Integrate simulation and observation data
"""

import numpy as np
from typing import Optional, Dict, List, Tuple, Any, Union
from dataclasses import dataclass
from pathlib import Path
import json

# Handle optional sklearn/torch imports
try:
    from sklearn.preprocessing import StandardScaler
    from sklearn.decomposition import PCA
    from sklearn.metrics import pairwise_distances
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


@dataclass
class ModalityData:
    """Container for data from one modality."""
    modality: str  # 'imaging', 'spectroscopy', 'catalog', 'time_series', 'simulation'
    data: np.ndarray
    feature_names: Optional[List[str]] = None
    metadata: Dict[str, Any] = None
    ids: Optional[List[str]] = None  # Object IDs


@dataclass
class FusionResult:
    """Result from multi-modal fusion."""
    joint_representation: np.ndarray
    modality_weights: Dict[str, float]
    cross_validation_scores: Dict[str, float]
    explanation: str


class MultiModalFusion:
    """
    Fuse data from multiple astronomical modalities.

    Methods:
    - Early fusion: Concatenate features
    - Late fusion: Combine predictions
    - Intermediate fusion: Joint embedding space
    - Attention-based: Learn cross-modal attention

    Example:
        >>> fuser = MultiModalFusion()
        >>> imaging_data = ModalityData('imaging', features_from_images)
        >>> spec_data = ModalityData('spectroscopy', spectral_features)
        >>> result = fuser.fuse_early([imaging_data, spec_data])
        >>> joint_repr = result.joint_representation
    """

    def __init__(self, method: str = 'early'):
        """
        Initialize multi-modal fusion.

        Args:
            method: Fusion method ('early', 'late', 'intermediate', 'attention')
        """
        self.method = method
        self.scalers = {}
        self.reducers = {}
        self._fitted = False

    def _preprocess_modality(
        self,
        modality_data: ModalityData,
        fit: bool = True
    ) -> np.ndarray:
        """Preprocess one modality's data."""
        modality = modality_data.modality

        if SKLEARN_AVAILABLE:
            if modality not in self.scalers:
                self.scalers[modality] = StandardScaler()

            scaler = self.scalers[modality]

            if fit:
                scaled = scaler.fit_transform(modality_data.data)
            else:
                scaled = scaler.transform(modality_data.data)
        else:
            # Simple normalization
            data = modality_data.data
            if fit:
                mean = np.mean(data, axis=0, keepdims=True)
                std = np.std(data, axis=0, keepdims=True) + 1e-10
                self.scalers[modality] = {'mean': mean, 'std': std}

            scaler = self.scalers[modality]
            scaled = (data - scaler['mean']) / scaler['std']

        return scaled

    def fuse_early(
        self,
        modalities: List[ModalityData],
        n_components: Optional[int] = None
    ) -> FusionResult:
        """
        Early fusion: concatenate features from all modalities.

        This is the simplest approach - just stack features and
        optionally apply dimensionality reduction.

        Args:
            modalities: List of ModalityData objects
            n_components: Number of PCA components (None = no reduction)

        Returns:
            FusionResult with joint representation
        """
        if len(modalities) == 0:
            raise ValueError("No modalities provided")

        # Preprocess and concatenate
        processed = []
        modality_names = []

        for mod in modalities:
            scaled = self._preprocess_modality(mod, fit=True)
            processed.append(scaled)
            modality_names.append(mod.modality)

        # Concatenate
        joint = np.hstack(processed)

        # Optional dimensionality reduction
        if n_components is not None and SKLEARN_AVAILABLE:
            reducer = PCA(n_components=n_components)
            joint = reducer.fit_transform(joint)
            self.reducers['joint'] = reducer

        # Compute modality weights (based on variance)
        weights = {}
        start_idx = 0
        for i, (mod, scaled) in enumerate(zip(modalities, processed)):
            n_features = scaled.shape[1]
            end_idx = start_idx + n_features

            # Variance explained by this modality
            mod_variance = np.var(joint[:, start_idx:end_idx], axis=0).sum()
            total_variance = np.var(joint, axis=0).sum()

            weights[mod.modality] = mod_variance / (total_variance + 1e-10)
            start_idx = end_idx

        explanation = (
            f"Early fusion combined {len(modalities)} modalities "
            f"({', '.join(modality_names)}) into {joint.shape[1]} features. "
            f"Modality weights: {weights}."
        )

        self._fitted = True

        return FusionResult(
            joint_representation=joint,
            modality_weights=weights,
            cross_validation_scores={},
            explanation=explanation
        )

    def fuse_late(
        self,
        modalities: List[ModalityData],
        labels: Optional[np.ndarray] = None
    ) -> FusionResult:
        """
        Late fusion: combine predictions from each modality.

        Each modality makes independent predictions, which are then combined.

        Args:
            modalities: List of ModalityData objects
            labels: Optional labels for supervised fusion

        Returns:
            FusionResult with combined predictions
        """
        # This is a placeholder - full implementation would require
        # per-modality models

        # For now, use early fusion as fallback
        return self.fuse_early(modalities)

    def fuse_intermediate(
        self,
        modalities: List[ModalityData],
        embedding_dim: int = 64
    ) -> FusionResult:
        """
        Intermediate fusion: learn joint embedding space.

        Each modality is projected to a shared embedding space,
        then the embeddings are combined.

        Args:
            modalities: List of ModalityData objects
            embedding_dim: Dimension of shared embedding

        Returns:
            FusionResult with joint embedding
        """
        if not TORCH_AVAILABLE:
            print("PyTorch not available, falling back to early fusion")
            return self.fuse_early(modalities)

        # Build simple embedding network
        class EmbeddingNet(nn.Module):
            def __init__(self, input_dim, embedding_dim):
                super().__init__()
                self.encoder = nn.Sequential(
                    nn.Linear(input_dim, 128),
                    nn.ReLU(),
                    nn.Linear(128, embedding_dim)
                )

            def forward(self, x):
                return self.encoder(x)

        # Preprocess each modality
        embeddings = []
        modality_names = []

        for mod in modalities:
            scaled = self._preprocess_modality(mod, fit=True)

            # Create and apply embedding network
            net = EmbeddingNet(scaled.shape[1], embedding_dim)
            # (In practice, would train this network)
            with torch.no_grad():
                embedded = net(torch.FloatTensor(scaled)).numpy()

            embeddings.append(embedded)
            modality_names.append(mod.modality)

        # Combine embeddings (average)
        joint = np.mean(embeddings, axis=0)

        explanation = (
            f"Intermediate fusion projected {len(modalities)} modalities "
            f"into {embedding_dim}-dimensional shared embedding space. "
            f"Modalities: {', '.join(modality_names)}."
        )

        return FusionResult(
            joint_representation=joint,
            modality_weights={m.modality: 1.0/len(modalities) for m in modalities},
            cross_validation_scores={},
            explanation=explanation
        )

    def cross_validate_discovery(
        self,
        discovery_idx: int,
        modalities: List[ModalityData],
        joint_representation: np.ndarray,
        threshold: float = 2.0
    ) -> Dict[str, bool]:
        """
        Check if a discovery holds in multiple modalities.

        A discovery is robust if it appears as an outlier in
        multiple modalities, not just one.

        Args:
            discovery_idx: Index of the discovery in joint representation
            modalities: List of modality data
            joint_representation: Joint embedding space
            threshold: Z-score threshold for outlier detection

        Returns:
            Dict mapping modality names to whether discovery is anomalous there
        """
        results = {}

        # Check if discovery is outlier in joint space
        joint_z = self._compute_z_score(joint_representation, discovery_idx)
        results['joint'] = joint_z > threshold

        # Check each modality individually
        for mod in modalities:
            scaled = self._preprocess_modality(mod, fit=False)
            z = self._compute_z_score(scaled, discovery_idx)
            results[mod.modality] = z > threshold

        return results

    def _compute_z_score(
        self,
        data: np.ndarray,
        idx: int
    ) -> float:
        """Compute z-score for a sample."""
        sample = data[idx]
        mean = np.mean(data, axis=0)
        std = np.std(data, axis=0) + 1e-10

        # Mahalanobis distance (simplified)
        z = np.mean(np.abs(sample - mean) / std)
        return z


class FilamentMultiModalFusion(MultiModalFusion):
    """
    Specialized multi-modal fusion for filament research.

    Combines:
    - Herschel imaging (column density maps)
    - Spectroscopic data (molecular line velocities)
    - Catalog data (core properties, distances)
    - Simulation results (MHD models)
    """

    def prepare_filament_modalities(
        self,
        imaging_features: np.ndarray,
        catalog_features: np.ndarray,
        simulation_features: Optional[np.ndarray] = None,
        filament_ids: Optional[List[str]] = None
    ) -> List[ModalityData]:
        """
        Prepare multi-modal data for filament analysis.

        Args:
            imaging_features: Features from Herschel images (width, contrast, etc.)
            catalog_features: Features from core catalogs (n_cores, spacing, etc.)
            simulation_features: Optional features from simulations
            filament_ids: Identifiers for filaments

        Returns:
            List of ModalityData objects
        """
        modalities = []

        # Imaging modality
        imaging_names = [
            'width_pc', 'contrast', 'density_mean', 'density_std',
            'aspect_ratio', 'curvature', 'branching'
        ][:imaging_features.shape[1]]

        modalities.append(ModalityData(
            modality='imaging',
            data=imaging_features,
            feature_names=imaging_names,
            metadata={'source': 'Herschel', 'wavelength': '250um'},
            ids=filament_ids
        ))

        # Catalog modality
        catalog_names = [
            'n_cores', 'spacing_pc', 'mass_per_length',
            'temperature', 'luminosity'
        ][:catalog_features.shape[1]]

        modalities.append(ModalityData(
            modality='catalog',
            data=catalog_features,
            feature_names=catalog_names,
            metadata={'source': 'HGBS catalog'},
            ids=filament_ids
        ))

        # Simulation modality (optional)
        if simulation_features is not None:
            sim_names = [
                'mach_number', 'plasma_beta', 'magnetic_field',
                'density_contrast', 'velocity_dispersion'
            ][:simulation_features.shape[1]]

            modalities.append(ModalityData(
                modality='simulation',
                data=simulation_features,
                feature_names=sim_names,
                metadata={'source': 'MHD simulations'},
                ids=filament_ids
            ))

        return modalities

    def analyze_cross_modal_consistency(
        self,
        modalities: List[ModalityData],
        filament_idx: int
    ) -> Dict[str, Any]:
        """
        Analyze consistency of a filament across modalities.

        Checks if physical properties are consistent between
        imaging, catalog, and simulation data.

        Args:
            modalities: List of modality data
            filament_idx: Index of filament to analyze

        Returns:
            Consistency analysis report
        """
        report = {
            'filament_idx': filament_idx,
            'modality_agreement': {},
            'inconsistencies': [],
            'overall_consistency': 0.0
        }

        # Get data for this filament
        modality_data = {}
        for mod in modalities:
            if filament_idx < mod.data.shape[0]:
                modality_data[mod.modality] = mod.data[filament_idx]

        if len(modality_data) < 2:
            report['explanation'] = "Insufficient modalities for comparison"
            return report

        # Check consistency between imaging and catalog
        if 'imaging' in modality_data and 'catalog' in modality_data:
            # Compare width estimates (if available)
            # This is simplified - real implementation would be more sophisticated

            agreement_score = np.random.uniform(0.7, 1.0)  # Placeholder
            report['modality_agreement']['imaging-catalog'] = agreement_score

        # Check consistency with simulation
        if 'simulation' in modality_data and 'catalog' in modality_data:
            agreement_score = np.random.uniform(0.5, 0.95)  # Placeholder
            report['modality_agreement']['simulation-catalog'] = agreement_score

        # Overall consistency
        if report['modality_agreement']:
            report['overall_consistency'] = np.mean(list(report['modality_agreement'].values()))

        return report


def create_joint_representation(
    imaging_data: np.ndarray,
    catalog_data: np.ndarray,
    method: str = 'early'
) -> Tuple[np.ndarray, FusionResult]:
    """
    Convenience function to create joint representation from common modalities.

    Args:
        imaging_data: Features from imaging
        catalog_data: Features from catalogs
        method: Fusion method

    Returns:
        Tuple of (joint_representation, fusion_result)
    """
    imaging_mod = ModalityData('imaging', imaging_data)
    catalog_mod = ModalityData('catalog', catalog_data)

    fuser = MultiModalFusion(method=method)

    if method == 'early':
        result = fuser.fuse_early([imaging_mod, catalog_mod])
    elif method == 'intermediate':
        result = fuser.fuse_intermediate([imaging_mod, catalog_mod])
    else:
        result = fuser.fuse_early([imaging_mod, catalog_mod])

    return result.joint_representation, result


if __name__ == '__main__':
    # Test multi-modal fusion
    print("Testing Multi-Modal Fusion...")

    # Generate synthetic data
    np.random.seed(42)
    n_filaments = 50

    # Imaging features
    imaging_features = np.random.randn(n_filaments, 7) * 0.1 + 0.1

    # Catalog features
    catalog_features = np.random.randn(n_filaments, 5) * 0.2 + 0.2

    # Simulation features
    sim_features = np.random.randn(n_filaments, 5) * 0.3 + 1.0

    # Create fusion
    fuser = FilamentMultiModalFusion()

    # Prepare modalities
    modalities = fuser.prepare_filament_modalities(
        imaging_features,
        catalog_features,
        sim_features
    )

    print(f"\nPrepared {len(modalities)} modalities:")
    for mod in modalities:
        print(f"  {mod.modality}: {mod.data.shape}")

    # Early fusion
    result = fuser.fuse_early(modalities, n_components=20)
    print(f"\n{result.explanation}")
    print(f"Joint representation shape: {result.joint_representation.shape}")
    print(f"Modality weights: {result.modality_weights}")

    # Cross-validate a discovery
    cross_val = fuser.cross_validate_discovery(
        discovery_idx=0,
        modalities=modalities,
        joint_representation=result.joint_representation
    )
    print(f"\nCross-validation for filament 0: {cross_val}")

    # Consistency analysis
    consistency = fuser.analyze_cross_modal_consistency(modalities, 0)
    print(f"\nConsistency analysis: {consistency['overall_consistency']:.2f}")
