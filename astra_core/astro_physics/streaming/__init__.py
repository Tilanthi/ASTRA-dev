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
