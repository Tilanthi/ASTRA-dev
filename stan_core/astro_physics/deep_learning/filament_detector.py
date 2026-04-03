#!/usr/bin/env python3
"""
Filament Detection and Characterization using Deep Learning

Detects and analyzes filamentary structures in molecular clouds and the ISM.
Combines traditional filament tracing with learned representations.

Applications:
- Filament detection in Herschel/Planck dust emission maps
- Characterization of filament properties (width, length, curvature)
- Hub and branch point identification
- Velocity-coherent filament detection in spectral line cubes
- Filament stability analysis (virial parameter estimation)

Author: STAN Evolution Team
Date: 2025-03-18
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from scipy.ndimage import distance_transform_edt, label
from sklearn.cluster import DBSCAN


@dataclass
class FilamentProperties:
    """Properties of a detected filament"""
    id: int
    mask: np.ndarray
    centerline: np.ndarray
    length: float  # in pixels or physical units
    width: float  # mean FWHM
    width_variance: float
    curvature: float  # mean curvature
    orientation: float  # mean angle in radians
    intensity_mean: float
    intensity_std: float
    mass: float  # estimated mass if column density provided
    virial_parameter: float  # alpha_vir
    stability: str  # 'stable', 'unstable', 'critical'
    branches: List[int]  # IDs of connected filaments
    hubs: List[np.ndarray]  # Coordinates of hub junctions


class FilamentDetectionHead(nn.Module):
    """
    Specialized head for filament detection from image features.

    Outputs:
    - filament_mask: Binary mask of filamentary structures
    - centerline: Skeletonized centerline prediction
    - width: Local filament width at each point
    - orientation: Local filament orientation angle
    """

    def __init__(self, in_channels: int = 256):
        super().__init__()

        # Filament mask prediction (segmentation)
        self.mask_conv = nn.Sequential(
            nn.Conv2d(in_channels, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.Conv2d(128, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.Conv2d(64, 1, kernel_size=1),
            nn.Sigmoid()
        )

        # Centerline prediction (thinned skeleton)
        self.centerline_conv = nn.Sequential(
            nn.Conv2d(in_channels, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.Conv2d(128, 1, kernel_size=1),
            nn.Sigmoid()
        )

        # Width prediction (regression)
        self.width_conv = nn.Sequential(
            nn.Conv2d(in_channels, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.Conv2d(128, 1, kernel_size=1),
            nn.Softplus()  # Positive output
        )

        # Orientation prediction (angle in [-pi, pi])
        self.orientation_conv = nn.Sequential(
            nn.Conv2d(in_channels, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.Conv2d(128, 2, kernel_size=1),  # sin and cos components
        )

    def forward(self, features: torch.Tensor) -> Dict[str, torch.Tensor]:
        """
        Args:
            features: Feature tensor [B, C, H, W]

        Returns:
            Dictionary with predictions
        """
        filament_mask = self.mask_conv(features)
        centerline = self.centerline_conv(features)
        width = self.width_conv(features)
        orientation_raw = self.orientation_conv(features)

        # Normalize orientation to unit vectors
        orientation_norm = torch.norm(orientation_raw, dim=1, keepdim=True) + 1e-8
        orientation = orientation_raw / orientation_norm

        return {
            'filament_mask': filament_mask,
            'centerline': centerline,
            'width': width,
            'orientation': orientation
        }


class FilamentEncoder(nn.Module):
    """
    Encoder for filament detection in dust emission or column density maps.

    Architecture: Multi-scale encoder with attention to filamentary features.
    """

    def __init__(self, in_channels: int = 1, base_features: int = 64):
        super().__init__()

        # Encoder blocks
        self.enc1 = self._make_block(in_channels, base_features)
        self.enc2 = self._make_block(base_features, base_features * 2)
        self.enc3 = self._make_block(base_features * 2, base_features * 4)
        self.enc4 = self._make_block(base_features * 4, base_features * 8)

        # Attention to filament-like structures (high aspect ratio)
        self.filament_attention = nn.ModuleList([
            FilamentAttentionBlock(base_features * 2),
            FilamentAttentionBlock(base_features * 4),
            FilamentAttentionBlock(base_features * 8)
        ])

        # Pooling
        self.pool = nn.MaxPool2d(2)

    def _make_block(self, in_ch: int, out_ch: int) -> nn.Module:
        return nn.Sequential(
            nn.Conv2d(in_ch, out_ch, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_ch, out_ch, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True)
        )

    def forward(self, x: torch.Tensor) -> List[torch.Tensor]:
        """
        Args:
            x: Input image [B, C, H, W]

        Returns:
            List of feature maps at different scales
        """
        features = []

        x1 = self.enc1(x)
        features.append(x1)
        x = self.pool(x1)

        x2 = self.enc2(x)
        x2 = self.filament_attention[0](x2)
        features.append(x2)
        x = self.pool(x2)

        x3 = self.enc3(x)
        x3 = self.filament_attention[1](x3)
        features.append(x3)
        x = self.pool(x3)

        x4 = self.enc4(x)
        x4 = self.filament_attention[2](x4)
        features.append(x4)

        return features


class FilamentAttentionBlock(nn.Module):
    """
    Attention mechanism that focuses on filamentary structures.

    Uses oriented filters to detect structures with high aspect ratios.
    """

    def __init__(self, channels: int, num_orientations: int = 8):
        super().__init__()

        # Oriented filters at multiple angles
        self.num_orientations = num_orientations
        self.oriented_convs = nn.ModuleList([
            nn.Conv2d(channels, channels // num_orientations,
                     kernel_size=(1, 7), padding=(0, 3))
            for _ in range(num_orientations)
        ])

        # Channel attention
        self.channel_attn = nn.Sequential(
            nn.AdaptiveAvgPool2d(1),
            nn.Conv2d(channels, channels // 4, kernel_size=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(channels // 4, channels, kernel_size=1),
            nn.Sigmoid()
        )

        # Fusion
        self.fusion = nn.Conv2d(channels, channels, kernel_size=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: Input features [B, C, H, W]

        Returns:
            Attention-enhanced features
        """
        B, C, H, W = x.shape

        # Apply oriented filters
        oriented_features = []
        for i, conv in enumerate(self.oriented_convs):
            # Rotate input effectively by using transposed convolution
            if i % 2 == 0:
                feat = conv(x)
            else:
                feat = conv(x.transpose(2, 3)).transpose(2, 3)
            oriented_features.append(feat)

        oriented = torch.cat(oriented_features, dim=1)

        # Channel attention
        attn = self.channel_attn(x)
        x = x * attn

        # Fuse with oriented features
        x = self.fusion(torch.cat([x, oriented[:, :C]], dim=1))

        return x


class FilamentDetector(nn.Module):
    """
    Complete filament detection system.

    Detects and characterizes filaments in:
    - Dust emission maps (Herschel, Planck)
    - Column density maps
    - Spectral line data (velocity-coherent structures)
    - Molecular line integrated intensity maps

    Example:
        >>> detector = FilamentDetector(in_channels=1)
        >>> image = torch.randn(1, 1, 256, 256)  # Column density map
        >>> output = detector(image)
        >>> filaments = detector.extract_filaments(
        ...     output['filament_mask'][0].detach().cpu().numpy(),
        ...     output['centerline'][0].detach().cpu().numpy(),
        ...     output['width'][0].detach().cpu().numpy()
        ... )
    """

    def __init__(self, in_channels: int = 1, base_features: int = 64):
        super().__init__()

        self.encoder = FilamentEncoder(in_channels, base_features)

        # Decoder with skip connections
        self.up3 = nn.ConvTranspose2d(base_features * 8, base_features * 4,
                                       kernel_size=2, stride=2)
        self.dec3 = self._make_dec_block(base_features * 8, base_features * 4)

        self.up2 = nn.ConvTranspose2d(base_features * 4, base_features * 2,
                                       kernel_size=2, stride=2)
        self.dec2 = self._make_dec_block(base_features * 4, base_features * 2)

        self.up1 = nn.ConvTranspose2d(base_features * 2, base_features,
                                       kernel_size=2, stride=2)
        self.dec1 = self._make_dec_block(base_features * 2, base_features)

        # Detection head
        self.detection_head = FilamentDetectionHead(base_features)

    def _make_dec_block(self, in_ch: int, out_ch: int) -> nn.Module:
        return nn.Sequential(
            nn.Conv2d(in_ch, out_ch, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_ch, out_ch, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True)
        )

    def forward(self, x: torch.Tensor) -> Dict[str, torch.Tensor]:
        """
        Args:
            x: Input image [B, C, H, W]

        Returns:
            Dictionary with filament predictions
        """
        # Encode
        features = self.encoder(x)

        # Decode with skip connections
        x = self.up3(features[3])
        x = torch.cat([x, features[2]], dim=1)
        x = self.dec3(x)

        x = self.up2(x)
        x = torch.cat([x, features[1]], dim=1)
        x = self.dec2(x)

        x = self.up1(x)
        x = torch.cat([x, features[0]], dim=1)
        x = self.dec1(x)

        # Detection head
        outputs = self.detection_head(x)

        return outputs

    def extract_filaments(
        self,
        filament_mask: np.ndarray,
        centerline: np.ndarray,
        width_map: np.ndarray,
        orientation_map: np.ndarray,
        min_length: float = 10.0,
        min_width: float = 0.1
    ) -> List[FilamentProperties]:
        """
        Extract individual filaments from network predictions.

        Args:
            filament_mask: Predicted filament mask [H, W]
            centerline: Predicted centerline [H, W]
            width_map: Predicted width map [H, W]
            orientation_map: Predicted orientation [H, W, 2]
            min_length: Minimum filament length (pixels)
            min_width: Minimum filament width (pixels)

        Returns:
            List of FilamentProperties for each detected filament
        """
        # Binarize masks
        filament_binary = filament_mask > 0.5
        centerline_binary = centerline > 0.5

        # Label connected components
        labeled, num_filaments = label(filament_binary)

        filaments = []

        for i in range(1, num_filaments + 1):
            mask = labeled == i

            # Get corresponding centerline
            cl_mask = mask & centerline_binary

            if np.sum(cl_mask) < min_length:
                continue

            # Extract properties
            props = self._analyze_filament(
                i, mask, cl_mask, width_map, orientation_map, filament_mask
            )

            if props is not None and props.length >= min_length:
                filaments.append(props)

        return filaments

    def _analyze_filament(
        self,
        filament_id: int,
        mask: np.ndarray,
        centerline_mask: np.ndarray,
        width_map: np.ndarray,
        orientation_map: np.ndarray,
        intensity_map: np.ndarray
    ) -> Optional[FilamentProperties]:
        """Analyze a single filament and extract its properties."""

        # Get centerline coordinates
        centerline_coords = np.argwhere(centerline_mask)

        if len(centerline_coords) < 2:
            return None

        # Order points along the filament
        centerline = self._order_points(centerline_coords)

        # Length
        length = self._compute_length(centerline)

        # Width statistics
        widths = width_map[mask]
        width_mean = np.mean(widths)
        width_std = np.std(widths)

        if width_mean < 0.1:
            return None

        # Curvature
        curvature = self._compute_curvature(centerline)

        # Orientation
        angles = np.arctan2(orientation_map[mask, 1], orientation_map[mask, 0])
        orientation_mean = np.mean(angles)

        # Intensity statistics
        intensities = intensity_map[mask]
        intensity_mean = np.mean(intensities)
        intensity_std = np.std(intensities)

        # Estimate mass (simplified - needs distance and dust opacity)
        mass = self._estimate_mass(intensities, width_mean, length)

        # Virial parameter (simplified)
        virial_param = self._compute_virial_parameter(mass, length, width_mean)

        # Stability classification
        if virial_param < 1.0:
            stability = 'unstable'
        elif virial_param > 2.0:
            stability = 'stable'
        else:
            stability = 'critical'

        return FilamentProperties(
            id=filament_id,
            mask=mask,
            centerline=centerline,
            length=length,
            width=width_mean,
            width_variance=width_std ** 2,
            curvature=curvature,
            orientation=orientation_mean,
            intensity_mean=intensity_mean,
            intensity_std=intensity_std,
            mass=mass,
            virial_parameter=virial_param,
            stability=stability,
            branches=[],
            hubs=[]
        )

    def _order_points(self, points: np.ndarray) -> np.ndarray:
        """Order points along a filament using nearest neighbor."""
        ordered = [points[0]]
        remaining = points[1:].copy()

        while len(remaining) > 0:
            last = ordered[-1]
            distances = np.sum((remaining - last) ** 2, axis=1)
            nearest_idx = np.argmin(distances)
            ordered.append(remaining[nearest_idx])
            remaining = np.delete(remaining, nearest_idx, axis=0)

        return np.array(ordered)

    def _compute_length(self, centerline: np.ndarray) -> float:
        """Compute filament length as sum of segment lengths."""
        if len(centerline) < 2:
            return 0.0

        diffs = np.diff(centerline, axis=0)
        segment_lengths = np.sqrt(np.sum(diffs ** 2, axis=1))

        return np.sum(segment_lengths)

    def _compute_curvature(self, centerline: np.ndarray) -> float:
        """Compute mean curvature of centerline."""
        if len(centerline) < 3:
            return 0.0

        # Second derivative approximation
        d2 = centerline[:-2] - 2 * centerline[1:-1] + centerline[2:]

        # Mean curvature magnitude
        curvature = np.mean(np.sqrt(np.sum(d2 ** 2, axis=1)))

        return curvature

    def _estimate_mass(self, intensities: np.ndarray, width: float,
                       length: float) -> float:
        """
        Estimate filament mass from column density.

        This is a simplified calculation. Real mass estimation requires:
        - Distance to source
        - Dust opacity
        - Dust-to-gas ratio

        Returns: Mass in arbitrary units
        """
        # Simplified: mass ~ intensity * area
        mean_intensity = np.mean(intensities)
        area = width * length

        return mean_intensity * area

    def _compute_virial_parameter(self, mass: float, length: float,
                                   width: float) -> float:
        """
        Compute virial parameter for stability assessment.

        alpha_vir = 5 * sigma^2 * R / (G * M)

        Simplified version using characteristic scales.
        """
        # Very simplified - should use actual velocity dispersion
        G = 1.0  # Normalized gravitational constant

        # Approximate velocity dispersion from Larson's relations
        sigma = 0.1 * np.sqrt(length / 1.0)  # km/s per pc scale

        radius = width / 2.0

        alpha_vir = 5 * sigma ** 2 * radius / (G * mass + 1e-10)

        return alpha_vir


class VelocityCoherentFilamentDetector(nn.Module):
    """
    Detect velocity-coherent filaments in spectral line data cubes.

    Finds structures that are coherent in both position and velocity space,
    which is crucial for understanding filament formation and dynamics.

    Applications:
    - Identifying velocity-coherent fibers in molecular clouds
    - Separating overlapping filaments along line of sight
    - Studying filament formation via gas flow
    """

    def __init__(self, in_channels: int = 1, base_features: int = 64):
        super().__init__()

        # 3D convolution for spatial-velocity structure
        self.conv3d_1 = nn.Conv3d(in_channels, base_features,
                                   kernel_size=(3, 3, 3), padding=(1, 1, 1))
        self.conv3d_2 = nn.Conv3d(base_features, base_features * 2,
                                   kernel_size=(3, 3, 3), padding=(1, 1, 1))
        self.conv3d_3 = nn.Conv3d(base_features * 2, base_features * 4,
                                   kernel_size=(3, 3, 3), padding=(1, 1, 1))

        # 2D convolution for spatial features at each velocity
        self.spatial_conv = nn.Conv2d(base_features * 4, base_features * 4,
                                       kernel_size=3, padding=1)

        # Detection head (applied at each velocity slice)
        self.detection_head = FilamentDetectionHead(base_features * 4)

        self.bn1 = nn.BatchNorm3d(base_features)
        self.bn2 = nn.BatchNorm3d(base_features * 2)
        self.bn3 = nn.BatchNorm3d(base_features * 4)
        self.relu = nn.ReLU(inplace=True)

    def forward(self, cube: torch.Tensor) -> Dict[str, torch.Tensor]:
        """
        Args:
            cube: Input data cube [B, C, V, H, W] where V is velocity

        Returns:
            Dictionary with predictions for each velocity slice
        """
        # 3D feature extraction
        x = self.relu(self.bn1(self.conv3d_1(cube)))
        x = F.max_pool3d(x, kernel_size=(2, 2, 2))

        x = self.relu(self.bn2(self.conv3d_2(x)))
        x = F.max_pool3d(x, kernel_size=(2, 2, 2))

        x = self.relu(self.bn3(self.conv3d_3(x)))

        # Process each velocity slice
        B, C, V, H, W = x.shape

        outputs_per_velocity = []

        for v in range(V):
            slice_features = x[:, :, v, :, :]  # [B, C, H, W]
            slice_outputs = self.detection_head(slice_features)
            outputs_per_velocity.append(slice_outputs)

        # Stack outputs
        result = {}
        for key in outputs_per_velocity[0].keys():
            result[key] = torch.stack([o[key] for o in outputs_per_velocity], dim=2)

        return result


def train_filament_detector(
    model: FilamentDetector,
    train_loader: torch.utils.data.DataLoader,
    val_loader: torch.utils.data.DataLoader,
    num_epochs: int = 100,
    learning_rate: float = 1e-3,
    device: str = 'cuda'
) -> FilamentDetector:
    """
    Train filament detector on annotated data.

    Args:
        model: FilamentDetector model
        train_loader: Training data loader
        val_loader: Validation data loader
        num_epochs: Number of training epochs
        learning_rate: Learning rate
        device: Device to train on

    Returns:
        Trained model
    """
    model = model.to(device)

    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)

    # Combined loss: mask + centerline + width + orientation
    def loss_fn(predictions, targets):
        mask_loss = F.binary_cross_entropy(
            predictions['filament_mask'],
            targets['filament_mask']
        )

        centerline_loss = F.binary_cross_entropy(
            predictions['centerline'],
            targets['centerline']
        )

        width_loss = F.mse_loss(
            predictions['width'],
            targets['width']
        )

        # Orientation loss (cosine similarity)
        orientation_pred = predictions['orientation']
        orientation_target = targets['orientation']
        orientation_loss = 1 - torch.mean(
            F.cosine_similarity(orientation_pred, orientation_target, dim=1)
        )

        # Combined loss with weights
        total_loss = (
            1.0 * mask_loss +
            0.5 * centerline_loss +
            0.1 * width_loss +
            0.2 * orientation_loss
        )

        return total_loss

    best_val_loss = float('inf')

    for epoch in range(num_epochs):
        # Training
        model.train()
        train_loss = 0.0

        for batch in train_loader:
            images = batch['image'].to(device)
            targets = {k: v.to(device) for k, v in batch.items() if k != 'image'}

            optimizer.zero_grad()
            predictions = model(images)
            loss = loss_fn(predictions, targets)
            loss.backward()
            optimizer.step()

            train_loss += loss.item()

        train_loss /= len(train_loader)

        # Validation
        model.eval()
        val_loss = 0.0

        with torch.no_grad():
            for batch in val_loader:
                images = batch['image'].to(device)
                targets = {k: v.to(device) for k, v in batch.items() if k != 'image'}

                predictions = model(images)
                loss = loss_fn(predictions, targets)
                val_loss += loss.item()

        val_loss /= len(val_loader)

        print(f"Epoch {epoch+1}/{num_epochs}: "
              f"train_loss={train_loss:.4f}, val_loss={val_loss:.4f}")

        # Save best model
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save(model.state_dict(), 'filament_detector_best.pth')

    return model


if __name__ == "__main__":
    print("="*70)
    print("Filament Detection Module")
    print("="*70)
    print()
    print("Components:")
    print("  - FilamentDetector: Main detection model")
    print("  - VelocityCoherentFilamentDetector: 3D velocity-coherent detection")
    print("  - FilamentProperties: Data structure for filament analysis")
    print("  - FilamentDetectionHead: Detection head for U-Net style models")
    print("  - FilamentEncoder: Encoder with filament attention")
    print()
    print("Applications:")
    print("  - Dust emission filament detection")
    print("  - Velocity-coherent structure identification")
    print("  - Filament property characterization")
    print("  - Stability analysis")
    print("="*70)
