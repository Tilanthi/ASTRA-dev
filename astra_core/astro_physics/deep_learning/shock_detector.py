#!/usr/bin/env python3

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
Interstellar Shock Detection and Classification using Deep Learning

Detects and characterizes shock waves in the interstellar medium using
multi-wavelength data. Identifies shock types and estimates physical parameters.

Applications:
- Supernova remnant shell identification
- Herbig-Haro object detection
- Jet-induced shock detection
- Galactic shock identification
- Wind-blown bubble detection
- Shock front tracing
- Shock velocity estimation

Shock Types Detected:
- Radiative shocks (cooling, emission-line dominated)
- Non-radiative shocks (adiabatic, X-ray dominated)
- J-type shocks (jump conditions)
- C-type shocks (continuous, molecular)
- Magnetohydrodynamic (MHD) shocks

Author: STAN Evolution Team
Date: 2025-03-18
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass


@dataclass
class ShockProperties:
    """Properties of a detected shock"""
    id: int
    shock_type: str  # 'radiative', 'non_radiative', 'j_type', 'c_type', 'mhd'
    mask: np.ndarray
    front_position: np.ndarray  # Front boundary
    velocity: float  # km/s
    mach_number: float
    pre_shock_density: float  # cm^-3
    post_shock_density: float  # cm^-3
    temperature: float  # K
    magnetic_field: float  # Gauss (optional)
    age: float  # years (for SNRs)
    driving_source: Optional[str]  # 'supernova', 'jet', 'wind', 'cloud_collision'
    confidence: float


class ShockBoundaryDetection(nn.Module):
    """
    Detects shock boundaries in multi-wavelength images.

    Uses edge detection and curvature analysis to identify sharp gradients
    characteristic of shock fronts.
    """

    def __init__(self, in_channels: int = 1):
        super().__init__()

        # Multi-scale edge detection
        self.edge_conv1 = nn.Conv2d(in_channels, 32, kernel_size=3, padding=1)
        self.edge_conv2 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.edge_conv3 = nn.Conv2d(64, 128, kernel_size=3, padding=1)

        # Boundary refinement
        self.boundary_conv = nn.Sequential(
            nn.Conv2d(128, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.Conv2d(64, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.Conv2d(32, 1, kernel_size=1),
            nn.Sigmoid()
        )

        # Gradient direction prediction (normal to shock front)
        self.direction_conv = nn.Conv2d(128, 2, kernel_size=1)  # sin, cos

        self.relu = nn.ReLU(inplace=True)

    def forward(self, x: torch.Tensor) -> Dict[str, torch.Tensor]:
        """
        Args:
            x: Input image [B, C, H, W]

        Returns:
            Dictionary with boundary predictions
        """
        # Extract edge features
        e1 = self.relu(self.edge_conv1(x))
        e2 = self.relu(self.edge_conv2(e1))
        e3 = self.relu(self.edge_conv3(e2))

        # Boundary probability
        boundary = self.boundary_conv(e3)

        # Direction (normal to front)
        direction = self.direction_conv(e3)
        direction = F.normalize(direction, dim=1)

        return {
            'boundary': boundary,
            'direction': direction,
            'features': e3
        }


class ShockTypeClassifier(nn.Module):
    """
    Classifies shock type based on spectral and morphological features.

    Output classes:
    - Radiative shock: Strong cooling, bright emission lines
    - Non-radiative shock: Adiabatic, X-ray emission
    - J-type shock: Discontinuous jump, ionized
    - C-type shock: Continuous, molecular
    - MHD shock: Magnetic effects dominant
    """

    def __init__(self, in_features: int = 256):
        super().__init__()

        self.classifier = nn.Sequential(
            nn.Linear(in_features, 512),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),
            nn.Linear(512, 256),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),
            nn.Linear(256, 64),
            nn.ReLU(inplace=True),
            nn.Dropout(0.2),
            nn.Linear(64, 5)  # 5 shock types
        )

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        """
        Args:
            features: Feature vector [B, C]

        Returns:
            Class logits [B, 5]
        """
        return self.classifier(features)


class ShockParameterRegressor(nn.Module):
    """
    Regresses physical shock parameters from observations.

    Predicts:
    - Shock velocity
    - Mach number
    - Pre-shock density
    - Post-shock temperature
    - Magnetic field strength
    """

    def __init__(self, in_features: int = 256):
        super().__init__()

        # Shared layers
        self.shared = nn.Sequential(
            nn.Linear(in_features, 256),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),
            nn.Linear(256, 128),
            nn.ReLU(inplace=True),
        )

        # Velocity (km/s)
        self.velocity_head = nn.Sequential(
            nn.Linear(128, 64),
            nn.ReLU(inplace=True),
            nn.Linear(64, 1),
            nn.Softplus()  # v > 0
        )

        # Mach number
        self.mach_head = nn.Sequential(
            nn.Linear(128, 64),
            nn.ReLU(inplace=True),
            nn.Linear(64, 1),
            nn.Softplus()  # M > 0
        )

        # Pre-shock density (cm^-3)
        self.density_head = nn.Sequential(
            nn.Linear(128, 64),
            nn.ReLU(inplace=True),
            nn.Linear(64, 1),
            nn.Softplus()  # n > 0
        )

        # Temperature (K)
        self.temperature_head = nn.Sequential(
            nn.Linear(128, 64),
            nn.ReLU(inplace=True),
            nn.Linear(64, 1),
            nn.Softplus()  # T > 0
        )

        # Magnetic field (G)
        self.bfield_head = nn.Sequential(
            nn.Linear(128, 64),
            nn.ReLU(inplace=True),
            nn.Linear(64, 1),
            nn.Softplus()  # B > 0
        )

    def forward(self, features: torch.Tensor) -> Dict[str, torch.Tensor]:
        """
        Args:
            features: Feature vector [B, C]

        Returns:
            Dictionary with parameter predictions
        """
        x = self.shared(features)

        return {
            'velocity': self.velocity_head(x),
            'mach_number': self.mach_head(x),
            'pre_shock_density': self.density_head(x),
            'temperature': self.temperature_head(x),
            'magnetic_field': self.bfield_head(x)
        }


class MultiWavelengthShockEncoder(nn.Module):
    """
    Encodes multi-wavelength observations of shocks.

    Combines information from:
    - Optical/IR (H-alpha, [SII], line ratios)
    - X-ray (hot gas)
    - Radio (synchrotron, free-free)
    - Molecular lines (shocked gas)
    """

    def __init__(self, num_wavelengths: int = 4):
        super().__init__()

        # Individual wavelength encoders
        self.encoders = nn.ModuleList([
            nn.Sequential(
                nn.Conv2d(1, 32, kernel_size=3, padding=1),
                nn.BatchNorm2d(32),
                nn.ReLU(inplace=True),
                nn.Conv2d(32, 64, kernel_size=3, padding=1),
                nn.BatchNorm2d(64),
                nn.ReLU(inplace=True),
                nn.MaxPool2d(2)
            )
            for _ in range(num_wavelengths)
        ])

        # Fusion layer
        total_channels = 64 * num_wavelengths
        self.fusion = nn.Sequential(
            nn.Conv2d(total_channels, 256, kernel_size=3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
            nn.Conv2d(256, 256, kernel_size=3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
            nn.AdaptiveAvgPool2d(1)
        )

    def forward(self, wavelength_images: List[torch.Tensor]) -> torch.Tensor:
        """
        Args:
            wavelength_images: List of images [B, 1, H, W] for each wavelength

        Returns:
            Fused feature vector [B, 256]
        """
        encoded_features = []

        for i, (image, encoder) in enumerate(zip(wavelength_images, self.encoders)):
            feat = encoder(image)
            encoded_features.append(feat)

        # Concatenate
        fused = torch.cat(encoded_features, dim=1)

        # Fuse
        features = self.fusion(fused).squeeze(-1).squeeze(-1)

        return features


class InterstellarShockDetector(nn.Module):
    """
    Complete shock detection and analysis system.

    Detects, classifies, and characterizes interstellar shocks using
    multi-wavelength observations.

    Example:
        >>> detector = InterstellarShockDetector(num_wavelengths=4)
        >>> optical = torch.randn(1, 1, 256, 256)  # H-alpha
        >>> xray = torch.randn(1, 1, 256, 256)     # X-ray
        >>> radio = torch.randn(1, 1, 256, 256)    # Radio continuum
        >>> molecular = torch.randn(1, 1, 256, 256) # CO line
        >>>
        >>> shocks = detector.detect_shocks([optical, xray, radio, molecular])
        >>> for shock in shocks:
        ...     print(f"{shock.shock_type}: v={shock.velocity:.1f} km/s")
    """

    def __init__(self, num_wavelengths: int = 4, in_channels: int = 1):
        super().__init__()

        # Multi-wavelength encoder
        self.multi_wavelength_encoder = MultiWavelengthShockEncoder(num_wavelengths)

        # Boundary detection (applied to each wavelength)
        self.boundary_detector = nn.ModuleList([
            ShockBoundaryDetection(in_channels)
            for _ in range(num_wavelengths)
        ])

        # Shock type classifier
        self.type_classifier = ShockTypeClassifier(256)

        # Parameter regressor
        self.parameter_regressor = ShockParameterRegressor(256)

        # Source identification (what drives the shock)
        self.source_classifier = nn.Sequential(
            nn.Linear(256, 128),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),
            nn.Linear(128, 4)  # supernova, jet, wind, cloud_collision
        )

    def forward(
        self,
        wavelength_images: List[torch.Tensor]
    ) -> Dict[str, torch.Tensor]:
        """
        Args:
            wavelength_images: List of images for each wavelength [B, 1, H, W]

        Returns:
            Dictionary with all predictions
        """
        # Encode multi-wavelength data
        fused_features = self.multi_wavelength_encoder(wavelength_images)

        # Detect boundaries in each wavelength
        boundaries = []
        directions = []

        for i, (image, detector) in enumerate(zip(wavelength_images,
                                                   self.boundary_detector)):
            result = detector(image)
            boundaries.append(result['boundary'])
            directions.append(result['direction'])

        # Stack boundary outputs
        boundary_stack = torch.stack(boundaries, dim=0)  # [num_wavelengths, B, 1, H, W]
        direction_stack = torch.stack(directions, dim=0)

        # Classify shock type
        type_logits = self.type_classifier(fused_features)

        # Regress parameters
        parameters = self.parameter_regressor(fused_features)

        # Identify driving source
        source_logits = self.source_classifier(fused_features)

        return {
            'fused_features': fused_features,
            'boundaries': boundary_stack,
            'directions': direction_stack,
            'type_logits': type_logits,
            'parameters': parameters,
            'source_logits': source_logits
        }

    def detect_shocks(
        self,
        wavelength_images: List[torch.Tensor],
        confidence_threshold: float = 0.7
    ) -> List[ShockProperties]:
        """
        Detect and characterize shocks.

        Args:
            wavelength_images: List of images for each wavelength
            confidence_threshold: Minimum confidence for detection

        Returns:
            List of ShockProperties
        """
        self.eval()

        with torch.no_grad():
            predictions = self.forward(wavelength_images)

        # Extract shocks from predictions
        shocks = self._extract_shocks(predictions, wavelength_images,
                                      confidence_threshold)

        return shocks

    def _extract_shocks(
        self,
        predictions: Dict[str, torch.Tensor],
        wavelength_images: List[torch.Tensor],
        threshold: float
    ) -> List[ShockProperties]:
        """Extract individual shock objects from predictions."""
        shocks = []

        # Get combined boundary map (average across wavelengths)
        boundaries = predictions['boundaries']  # [num_wavelengths, B, 1, H, W]
        combined_boundary = torch.mean(boundaries, dim=0)[0, 0].cpu().numpy()

        # Binarize
        boundary_binary = combined_boundary > threshold

        # Label connected components
        from scipy.ndimage import label

        labeled, num_shocks = label(boundary_binary)

        # Get parameters from network
        params = predictions['parameters']
        type_logits = predictions['type_logits'][0]
        source_logits = predictions['source_logits'][0]

        # Convert to probabilities
        type_probs = F.softmax(type_logits, dim=0).cpu().numpy()
        source_probs = F.softmax(source_logits, dim=0).cpu().numpy()

        # Get parameter values
        velocity = params['velocity'][0, 0].item()
        mach = params['mach_number'][0, 0].item()
        density = params['pre_shock_density'][0, 0].item()
        temperature = params['temperature'][0, 0].item()
        bfield = params['magnetic_field'][0, 0].item()

        # Shock type labels
        type_labels = ['radiative', 'non_radiative', 'j_type', 'c_type', 'mhd']
        source_labels = ['supernova', 'jet', 'wind', 'cloud_collision']

        for i in range(1, num_shocks + 1):
            mask = labeled == i

            if np.sum(mask) < 10:  # Skip small detections
                continue

            # Get front position (boundary)
            front_position = np.argwhere(mask)

            # Determine shock type
            shock_type = type_labels[np.argmax(type_probs)]

            # Determine driving source
            if np.max(source_probs) > 0.5:
                driving_source = source_labels[np.argmax(source_probs)]
            else:
                driving_source = None

            # Compute post-shock density from jump conditions
            # rho2 / rho1 depends on Mach number
            if shock_type == 'j_type':
                # Strong shock limit: rho2/rho1 = 4
                post_shock_density = 4 * density
            elif shock_type == 'c_type':
                # C-type can have larger compression
                post_shock_density = 10 * density
            else:
                post_shock_density = 4 * density

            # Estimate age for SNR
            if driving_source == 'supernova':
                # Simple Sedov-Taylor estimate
                age = 1000.0 / (mach + 1e-10)  # Very rough approximation
            else:
                age = 0.0

            # Confidence based on boundary strength
            confidence = np.mean(combined_boundary[mask])

            props = ShockProperties(
                id=i,
                shock_type=shock_type,
                mask=mask,
                front_position=front_position,
                velocity=velocity,
                mach_number=mach,
                pre_shock_density=density,
                post_shock_density=post_shock_density,
                temperature=temperature,
                magnetic_field=bfield,
                age=age,
                driving_source=driving_source,
                confidence=confidence
            )

            shocks.append(props)

        return shocks


class SpectralLineShockDetector(nn.Module):
    """
    Detects shocks using spectral line diagnostics.

    Uses line ratios and profiles to identify shocked gas:
    - [SII]/H-alpha ratio (>0.4 indicates shocks)
    - Line broadening
    - Excitation temperature
    - Molecular line emission (SiO, H2, etc.)
    """

    def __init__(self, num_lines: int = 10):
        super().__init__()

        # Process spectral line measurements
        self.line_encoder = nn.Sequential(
            nn.Linear(num_lines, 64),
            nn.ReLU(inplace=True),
            nn.Linear(64, 128),
            nn.ReLU(inplace=True),
            nn.Linear(128, 256)
        )

        # Shock indicator
        self.shock_indicator = nn.Sequential(
            nn.Linear(256, 64),
            nn.ReLU(inplace=True),
            nn.Linear(64, 1),
            nn.Sigmoid()
        )

        # Velocity from line width
        self.velocity_regressor = nn.Sequential(
            nn.Linear(256, 64),
            nn.ReLU(inplace=True),
            nn.Linear(64, 1),
            nn.Softplus()
        )

    def forward(self, line_intensities: torch.Tensor) -> Dict[str, torch.Tensor]:
        """
        Args:
            line_intensities: Line intensities/ratios [B, num_lines]

        Returns:
            Dictionary with predictions
        """
        features = self.line_encoder(line_intensities)

        shock_prob = self.shock_indicator(features)
        velocity = self.velocity_regressor(features)

        return {
            'shock_probability': shock_prob,
            'velocity': velocity,
            'features': features
        }


class TemporalShockDetector(nn.Module):
    """
    Detects shocks and their evolution in time-series data.

    Identifies proper motion of shock fronts and variability
    in shock properties over time.
    """

    def __init__(self, in_channels: int = 1):
        super().__init__()

        # 3D CNN for temporal data (t, y, x)
        self.conv3d_1 = nn.Conv3d(in_channels, 32, kernel_size=(3, 3, 3),
                                  padding=(1, 1, 1))
        self.conv3d_2 = nn.Conv3d(32, 64, kernel_size=(3, 3, 3),
                                  padding=(1, 1, 1))
        self.conv3d_3 = nn.Conv3d(64, 128, kernel_size=(3, 3, 3),
                                  padding=(1, 1, 1))

        # Detect proper motion
        self.motion_head = nn.Sequential(
            nn.Conv3d(128, 64, kernel_size=(1, 3, 3), padding=(0, 1, 1)),
            nn.ReLU(inplace=True),
            nn.Conv3d(64, 2, kernel_size=1)  # vy, vx
        )

        # Detect variability
        self.variability_head = nn.Sequential(
            nn.AdaptiveAvgPool3d((1, 1, 1)),
            nn.Flatten(),
            nn.Linear(128, 64),
            nn.ReLU(inplace=True),
            nn.Linear(64, 1),
            nn.Sigmoid()
        )

    def forward(self, time_series: torch.Tensor) -> Dict[str, torch.Tensor]:
        """
        Args:
            time_series: Temporal image sequence [B, C, T, H, W]

        Returns:
            Dictionary with motion and variability predictions
        """
        x = F.relu(self.conv3d_1(time_series))
        x = F.max_pool3d(x, 2)

        x = F.relu(self.conv3d_2(x))
        x = F.max_pool3d(x, 2)

        x = F.relu(self.conv3d_3(x))

        # Proper motion
        motion = self.motion_head(x)

        # Variability
        variability = self.variability_head(x)

        return {
            'proper_motion': motion,
            'variability': variability
        }


def train_shock_detector(
    model: InterstellarShockDetector,
    train_loader: torch.utils.data.DataLoader,
    val_loader: torch.utils.data.DataLoader,
    num_epochs: int = 50,
    learning_rate: float = 1e-4,
    device: str = 'cuda'
) -> InterstellarShockDetector:
    """
    Train shock detector on annotated data.

    Args:
        model: InterstellarShockDetector
        train_loader: Training data
        val_loader: Validation data
        num_epochs: Training epochs
        learning_rate: Learning rate
        device: Training device

    Returns:
        Trained model
    """
    model = model.to(device)

    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)

    def loss_fn(predictions, targets):
        # Boundary detection loss
        boundary_loss = 0.0
        for i, boundary in enumerate(predictions['boundaries']):
            boundary_loss += F.binary_cross_entropy(
                boundary,
                targets['boundaries'][i]
            )

        # Type classification loss
        type_loss = F.cross_entropy(
            predictions['type_logits'],
            targets['shock_type']
        )

        # Parameter regression losses
        vel_loss = F.mse_loss(
            predictions['parameters']['velocity'],
            targets['velocity']
        )

        mach_loss = F.mse_loss(
            predictions['parameters']['mach_number'],
            targets['mach_number']
        )

        temp_loss = F.mse_loss(
            predictions['parameters']['temperature'],
            targets['temperature']
        )

        # Source classification loss
        source_loss = F.cross_entropy(
            predictions['source_logits'],
            targets['driving_source']
        )

        # Combined loss
        total_loss = (
            2.0 * boundary_loss +
            1.0 * type_loss +
            0.1 * vel_loss +
            0.1 * mach_loss +
            0.01 * temp_loss +
            0.5 * source_loss
        )

        return total_loss

    best_val_loss = float('inf')

    for epoch in range(num_epochs):
        model.train()
        train_loss = 0.0

        for batch in train_loader:
            images = [w.to(device) for w in batch['wavelengths']]
            targets = {k: v.to(device) for k, v in batch.items()
                      if k != 'wavelengths'}

            optimizer.zero_grad()
            predictions = model(images)
            loss = loss_fn(predictions, targets)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()

            train_loss += loss.item()

        train_loss /= len(train_loader)

        # Validation
        model.eval()
        val_loss = 0.0

        with torch.no_grad():
            for batch in val_loader:
                images = [w.to(device) for w in batch['wavelengths']]
                targets = {k: v.to(device) for k, v in batch.items()
                          if k != 'wavelengths'}

                predictions = model(images)
                loss = loss_fn(predictions, targets)
                val_loss += loss.item()

        val_loss /= len(val_loader)

        print(f"Epoch {epoch+1}/{num_epochs}: "
              f"train_loss={train_loss:.4f}, val_loss={val_loss:.4f}")

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save(model.state_dict(), 'shock_detector_best.pth')

    return model


if __name__ == "__main__":
    print("="*70)
    print("Interstellar Shock Detection Module")
    print("="*70)
    print()
    print("Components:")
    print("  - InterstellarShockDetector: Main detection system")
    print("  - SpectralLineShockDetector: Spectral diagnostic detector")
    print("  - TemporalShockDetector: Time-series shock detector")
    print("  - ShockProperties: Physical property data structure")
    print("  - ShockTypeClassifier: Type classification")
    print("  - ShockParameterRegressor: Physical parameter estimation")
    print()
    print("Applications:")
    print("  - Supernova remnant shell identification")
    print("  - Herbig-Haro object detection")
    print("  - Jet-induced shock detection")
    print("  - Galactic shock identification")
    print("  - Shock front tracing and velocity estimation")
    print("="*70)
