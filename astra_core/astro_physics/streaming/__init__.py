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
Real-Time Streaming Processing for Time-Domain Astronomy

Components for processing real-time astronomical alert streams and detecting
anomalous phenomena in continuous data streams.

Author: STAN Evolution Team
Date: 2025-03-18
Version: 1.0.0
"""

from .streaming_alert_processor import (
    StreamingAlertProcessor,
    AlertClassifier,
    AlertPrioritizer,
    AlertFeatureExtractor,
    AlertMetadata,
    ProcessedAlert,
    AlertSource,
    TransientType,
    create_alert_processor
)

from .real_time_anomaly_detection import (
    RealTimeAnomalyDetector,
    LightCurveAnomalyDetector,
    SpectralAnomalyDetector,
    AnomalyReport,
    IsolationForestOnline,
    OnlineStandardScaler,
    create_anomaly_detector
)

__all__ = [
    'StreamingAlertProcessor',
    'AlertClassifier',
    'AlertPrioritizer',
    'AlertFeatureExtractor',
    'AlertMetadata',
    'ProcessedAlert',
    'AlertSource',
    'TransientType',
    'create_alert_processor',
    'RealTimeAnomalyDetector',
    'LightCurveAnomalyDetector',
    'SpectralAnomalyDetector',
    'AnomalyReport',
    'IsolationForestOnline',
    'OnlineStandardScaler',
    'create_anomaly_detector',
]
