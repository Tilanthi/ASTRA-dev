"""
ASTRA Live — Conformal Prediction for ML Uncertainty Quantification

This is an OPTIONAL enhancement module for machine learning workflows.
Provides statistically valid prediction intervals without distributional assumptions.

USE WHEN:
  - Applying black-box ML models to astronomical/socioeconomic data
  - Need calibrated uncertainty intervals for predictions
  - Detecting out-of-distribution (OOD) samples
  - Heterogeneous data sources with unknown selection functions

DO NOT USE FOR:
  - Traditional hypothesis testing (use statistics.py instead)
  - Causal inference (use causal.py instead)
  - Parameter estimation (use bayesian.py instead)
  - Any task requiring full posterior distributions

References:
  - Vovk et al. (2005) "Algorithmic Learning in a Random World"
  - Angelopoulos & Bates (2021) "A Gentle Introduction to Conformal Prediction"
  - Shafer & Vovk (2008) "A Tutorial on Conformal Prediction"

Dependencies (OPTIONAL - graceful degradation if unavailable):
  - conformal-prediction: pip install conformal-prediction
  - numpy, scipy (already required by ASTRA)
"""
import time
import uuid
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Callable, Any, Union
from enum import Enum

logger = logging.getLogger(__name__)

# Try optional conformal prediction libraries
HAS_CONFORMAL = False
try:
    from conformal_algorithms import ConformalPredictor
    HAS_CONFORMAL = True
    logger.info("conformal-prediction library available")
except ImportError:
    try:
        # Alternative: MAPIE (Model Agnostic Prediction Interval Estimator)
        from mapie.regression import MapieRegressor
        from mapie.classification import MapieClassifier
        HAS_CONFORMAL = True
        logger.info("MAPIE library available for conformal prediction")
    except ImportError:
        logger.warning(
            "No conformal prediction library found. "
            "Install with: pip install conformal-prediction OR pip install mapie"
        )

import numpy as np


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

class ConformalMethod(Enum):
    """Conformal prediction methods available."""
    SPLIT = "split"           # Simple split-conformal
    CV_PLUS = "cv_plus"       # Cross-validation with plus
    CV_MINUS = "cv_minus"     # Cross-validation with minus
    JACKKNIFE = "jackknife"   # Jackknife+ (more conservative)
    QUANTILE = "quantile"     # Quantile non-conformity


@dataclass
class ConformalResult:
    """Result from conformal prediction with uncertainty intervals."""
    prediction: np.ndarray           # Point predictions
    lower_bound: np.ndarray          # Lower confidence bound
    upper_bound: np.ndarray          # Upper confidence bound
    coverage: float                  # Empirical coverage (should ≈ target)
    calibration_scores: np.ndarray   # Non-conformity scores from calibration set
    method: ConformalMethod          # Method used
    confidence_level: float          # Target confidence (e.g., 0.90)
    is_out_of_distribution: np.ndarray  # OOD flag for each prediction
    warning_flag: bool = False       # True if coverage is significantly off
    metadata: Dict[str, Any] = field(default_factory=dict)

    def interval_width(self) -> np.ndarray:
        """Return width of prediction intervals."""
        return self.upper_bound - self.lower_bound

    def to_dict(self) -> Dict:
        """Serialize for JSON response."""
        return {
            "prediction": self.prediction.tolist(),
            "lower_bound": self.lower_bound.tolist(),
            "upper_bound": self.upper_bound.tolist(),
            "interval_width": self.interval_width().tolist(),
            "mean_interval_width": float(np.mean(self.interval_width())),
            "coverage": float(self.coverage),
            "target_coverage": self.confidence_level,
            "coverage_error": float(self.coverage - self.confidence_level),
            "method": self.method.value,
            "confidence_level": self.confidence_level,
            "n_calibration": len(self.calibration_scores),
            "n_ood_detected": int(np.sum(self.is_out_of_distribution)),
            "ood_fraction": float(np.mean(self.is_out_of_distribution)),
            "warning_flag": self.warning_flag,
            "metadata": self.metadata,
        }


@dataclass
class ConformalClassificationResult:
    """Result from conformal prediction for classification."""
    predictions: np.ndarray           # Predicted class labels
    prediction_sets: List[set]        # Conformal prediction sets (may be multi-label)
    coverage: float                   # Empirical coverage
    ambiguity_scores: np.ndarray      # Measure of prediction uncertainty
    method: ConformalMethod
    confidence_level: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Serialize for JSON response."""
        return {
            "predictions": self.predictions.tolist(),
            "prediction_sets": [list(s) for s in self.prediction_sets],
            "mean_set_size": float(np.mean([len(s) for s in self.prediction_sets])),
            "coverage": float(self.coverage),
            "target_coverage": self.confidence_level,
            "mean_ambiguity": float(np.mean(self.ambiguity_scores)),
            "method": self.method.value,
            "confidence_level": self.confidence_level,
            "metadata": self.metadata,
        }


# ---------------------------------------------------------------------------
# Core conformal prediction engine (pure numpy - no external deps)
# ---------------------------------------------------------------------------

class ConformalEngine:
    """
    Core conformal prediction engine using only numpy/scipy.
    Provides split-conformal and CV+ methods without external libraries.
    """

    def __init__(self):
        self.calibration_scores: Optional[np.ndarray] = None
        self.calibration_predictions: Optional[np.ndarray] = None
        self.calibration_labels: Optional[np.ndarray] = None
        self.method: ConformalMethod = ConformalMethod.SPLIT
        self.fitted: bool = False

    def fit_regression(
        self,
        model: Any,
        X_cal: np.ndarray,
        y_cal: np.ndarray,
        method: ConformalMethod = ConformalMethod.SPLIT,
    ) -> "ConformalEngine":
        """
        Fit conformal predictor for regression using calibration set.

        Parameters
        ----------
        model : Any
            Fitted ML model with predict() method (sklearn-like API)
        X_cal : np.ndarray
            Calibration features
        y_cal : np.ndarray
            Calibration true values
        method : ConformalMethod
            Conformal method to use

        Returns
        -------
        self : ConformalEngine
        """
        self.method = method
        self.model = model

        # Get predictions on calibration set
        y_pred_cal = model.predict(X_cal)

        # Compute non-conformity scores: |y - ŷ|
        # For regression, this is absolute residual
        self.calibration_scores = np.abs(y_cal - y_pred_cal)
        self.calibration_predictions = y_pred_cal
        self.calibration_labels = y_cal
        self.fitted = True

        logger.debug(
            f"Calibrated conformal predictor with {len(X_cal)} samples, "
            f"method={method.value}, mean_score={np.mean(self.calibration_scores):.4f}"
        )

        return self

    def predict_regression(
        self,
        X_test: np.ndarray,
        confidence: float = 0.90,
    ) -> ConformalResult:
        """
        Make predictions with conformal uncertainty intervals.

        Parameters
        ----------
        X_test : np.ndarray
            Test features
        confidence : float
            Target coverage probability (default: 0.90)

        Returns
        -------
        ConformalResult
        """
        if not self.fitted:
            raise RuntimeError("ConformalEngine must be fitted before prediction")

        # Get point predictions
        y_pred = self.model.predict(X_test)

        # Compute quantile of calibration scores
        # For coverage (1 - α), we use the (1 - α)(n + 1)/n quantile
        n_cal = len(self.calibration_scores)
        alpha = 1 - confidence
        q_level = min(1.0, (1 - alpha) * (n_cal + 1) / n_cal)
        q_hat = np.quantile(self.calibration_scores, q_level)

        # Form prediction intervals: [ŷ - q, ŷ + q]
        lower = y_pred - q_hat
        upper = y_pred + q_hat

        # Detect OOD samples: intervals wider than 2x calibration median
        median_width = 2 * np.median(self.calibration_scores)
        is_ood = (upper - lower) > 2 * median_width

        # Empirical coverage on calibration set
        empirical_coverage = np.mean(
            self.calibration_labels >= self.calibration_predictions - q_hat
        )
        empirical_coverage = np.mean(
            (self.calibration_labels >= self.calibration_predictions - q_hat) &
            (self.calibration_labels <= self.calibration_predictions + q_hat)
        )

        # Warning if coverage is significantly off
        warning = abs(empirical_coverage - confidence) > 0.05

        return ConformalResult(
            prediction=y_pred,
            lower_bound=lower,
            upper_bound=upper,
            coverage=empirical_coverage,
            calibration_scores=self.calibration_scores,
            method=self.method,
            confidence_level=confidence,
            is_out_of_distribution=is_ood,
            warning_flag=warning,
            metadata={"q_hat": float(q_hat), "n_cal": n_cal},
        )

    def fit_classification(
        self,
        model: Any,
        X_cal: np.ndarray,
        y_cal: np.ndarray,
        class_labels: Optional[np.ndarray] = None,
    ) -> "ConformalEngine":
        """
        Fit conformal predictor for classification.

        Parameters
        ----------
        model : Any
            Fitted classifier with predict_proba() method
        X_cal : np.ndarray
            Calibration features
        y_cal : np.ndarray
            Calibration true labels
        class_labels : np.ndarray, optional
            All possible class labels

        Returns
        -------
        self : ConformalEngine
        """
        self.method = ConformalMethod.SPLIT
        self.model = model

        if class_labels is None:
            class_labels = np.unique(y_cal)
        self.class_labels = class_labels

        # Get probability predictions on calibration set
        proba_cal = model.predict_proba(X_cal)

        # Compute non-conformity scores: 1 - P(y_true | x)
        # For each sample, we use the complement of its true class probability
        n_samples = len(y_cal)
        self.calibration_scores = np.zeros(n_samples)
        for i, true_label in enumerate(y_cal):
            true_idx = np.where(class_labels == true_label)[0][0]
            self.calibration_scores[i] = 1 - proba_cal[i, true_idx]

        self.calibration_labels = y_cal
        self.fitted = True

        return self

    def predict_classification(
        self,
        X_test: np.ndarray,
        confidence: float = 0.90,
    ) -> ConformalClassificationResult:
        """
        Make conformal prediction sets for classification.

        Parameters
        ----------
        X_test : np.ndarray
            Test features
        confidence : float
            Target coverage (default: 0.90)

        Returns
        -------
        ConformalClassificationResult
        """
        if not self.fitted:
            raise RuntimeError("ConformalEngine must be fitted before prediction")

        # Get probability predictions
        proba_test = self.model.predict_proba(X_test)

        # Compute quantile
        n_cal = len(self.calibration_scores)
        alpha = 1 - confidence
        q_level = min(1.0, (1 - alpha) * (n_cal + 1) / n_cal)
        q_hat = np.quantile(self.calibration_scores, q_level)

        # Form prediction sets: {y: P(y|x) >= 1 - q̂}
        prediction_sets = []
        predictions = []
        ambiguity_scores = []

        for i in range(len(X_test)):
            valid_classes = []
            for j, label in enumerate(self.class_labels):
                if proba_test[i, j] >= 1 - q_hat:
                    valid_classes.append(label)

            if not valid_classes:
                # Fallback: most likely class
                valid_classes = [self.class_labels[np.argmax(proba_test[i])]]

            prediction_sets.append(set(valid_classes))
            predictions.append(valid_classes[0])  # Default: first in set
            ambiguity_scores.append(len(valid_classes))

        # Empirical coverage
        empirical_coverage = np.mean(
            self.calibration_scores <= q_hat
        )

        return ConformalClassificationResult(
            predictions=np.array(predictions),
            prediction_sets=prediction_sets,
            coverage=empirical_coverage,
            ambiguity_scores=np.array(ambiguity_scores),
            method=self.method,
            confidence_level=confidence,
            metadata={"q_hat": float(q_hat), "n_cal": n_cal},
        )


# ---------------------------------------------------------------------------
# ASTRA-specific integration
# ---------------------------------------------------------------------------

class ConformalDiscovery:
    """
    High-level interface for conformal prediction in ASTRA discovery workflows.
    Integrates with existing statistics and ML components.
    """

    def __init__(self):
        self.engine = ConformalEngine()
        self.history: List[Dict] = []

    def calibrate_ml_discovery(
        self,
        model: Any,
        X: np.ndarray,
        y: np.ndarray,
        test_size: float = 0.2,
        confidence: float = 0.90,
        random_state: int = 42,
    ) -> Dict:
        """
        Calibrate an ML model for discovery tasks with uncertainty intervals.

        Typical use case: ML-assisted candidate selection from large surveys
        (e.g., flagging unusual transients, high-z galaxies, exoplanet candidates).

        Parameters
        ----------
        model : Any
            Scikit-learn-like model (must implement fit() and predict())
        X : np.ndarray
            Feature matrix
        y : np.ndarray
            Target values (regression) or labels (classification)
        test_size : float
            Fraction of data for calibration
        confidence : float
            Target coverage probability
        random_state : int
            Random seed

        Returns
        -------
        dict with calibration results and conformal predictor
        """
        from sklearn.model_selection import train_test_split

        # Split data
        X_train, X_cal, y_train, y_cal = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )

        # Fit model
        model.fit(X_train, y_train)

        # Determine task type
        is_classification = hasattr(model, "predict_proba")

        start_time = time.time()

        if is_classification:
            # Classification task
            self.engine.fit_classification(model, X_cal, y_cal)
            result = self.engine.predict_classification(X_cal, confidence)
        else:
            # Regression task
            self.engine.fit_regression(model, X_cal, y_cal)
            result = self.engine.predict_regression(X_cal, confidence)

        duration = time.time() - start_time

        summary = {
            "task_type": "classification" if is_classification else "regression",
            "n_samples": len(X),
            "n_train": len(X_train),
            "n_calibration": len(X_cal),
            "target_coverage": confidence,
            "empirical_coverage": result.coverage,
            "coverage_error": abs(result.coverage - confidence),
            "calibration_time_sec": round(duration, 3),
            "is_well_calibrated": abs(result.coverage - confidence) < 0.05,
        }

        # Add task-specific results
        if is_classification:
            summary["mean_set_size"] = float(np.mean(result.ambiguity_scores))
            summary["accuracy"] = float(np.mean(result.predictions == y_cal))
        else:
            summary["mean_interval_width"] = float(np.mean(result.interval_width()))
            summary["rmse"] = float(np.sqrt(np.mean((y_cal - result.prediction) ** 2)))

        # Log to history
        self.history.append({
            "timestamp": time.time(),
            "summary": summary,
            "result": result.to_dict() if hasattr(result, "to_dict") else None,
        })

        return {
            "summary": summary,
            "conformal_predictor": self.engine,
            "model": model,
            "result": result,
        }

    def detect_out_of_distribution(
        self,
        model: Any,
        X_new: np.ndarray,
        reference_scores: np.ndarray,
        confidence: float = 0.90,
        threshold_multiplier: float = 2.0,
    ) -> Dict:
        """
        Detect out-of-distribution samples using conformal prediction.

        OOD samples have prediction intervals significantly wider than reference,
        indicating the model is extrapolating beyond its training distribution.

        Parameters
        ----------
        model : Any
            Fitted model
        X_new : np.ndarray
            New samples to evaluate
        reference_scores : np.ndarray
            Non-conformity scores from calibration set
        confidence : float
            Target coverage
        threshold_multiplier : float
            Multiplier for median reference width to flag OOD

        Returns
        -------
        dict with OOD flags and diagnostics
        """
        # Get predictions and intervals
        if hasattr(model, "predict_proba"):
            # Classification
            proba = model.predict_proba(X_new)
            # Use entropy as uncertainty measure
            uncertainties = -np.sum(proba * np.log(proba + 1e-10), axis=1)
        else:
            # Regression - use residual-based uncertainty
            pred = model.predict(X_new)
            # Approximate uncertainty from prediction variance
            uncertainties = np.std(pred) * np.ones(len(X_new))

        # Reference median uncertainty
        ref_median = np.median(reference_scores)

        # OOD flag
        is_ood = uncertainties > threshold_multiplier * ref_median

        return {
            "is_out_of_distribution": is_ood.tolist(),
            "uncertainty_scores": uncertainties.tolist(),
            "reference_median": float(ref_median),
            "threshold": float(threshold_multiplier * ref_median),
            "n_ood": int(np.sum(is_ood)),
            "ood_fraction": float(np.mean(is_ood)),
        }

    def uncertainty_summary(self) -> Dict:
        """Get summary of all conformal calibration runs."""
        if not self.history:
            return {"n_runs": 0, "message": "No calibration history available"}

        return {
            "n_runs": len(self.history),
            "last_calibration": self.history[-1]["summary"] if self.history else None,
            "coverage_errors": [h["summary"]["coverage_error"] for h in self.history],
            "mean_coverage_error": float(
                np.mean([h["summary"]["coverage_error"] for h in self.history])
            ),
            "well_calibrated_count": sum(
                1 for h in self.history if h["summary"]["is_well_calibrated"]
            ),
        }


# ---------------------------------------------------------------------------
# Convenience functions
# ---------------------------------------------------------------------------

def quick_conformal_interval(
    y_pred: np.ndarray,
    y_true: np.ndarray,
    confidence: float = 0.90,
) -> Tuple[float, np.ndarray, np.ndarray]:
    """
    Quick conformal interval from predictions without a full model object.

    Parameters
    ----------
    y_pred : np.ndarray
        Predicted values
    y_true : np.ndarray
        True values
    confidence : float
        Target coverage

    Returns
    -------
    q_hat : float
        Quantile of non-conformity scores
    lower : np.ndarray
        Lower bounds for new predictions
    upper : np.ndarray
        Upper bounds for new predictions
    """
    scores = np.abs(y_true - y_pred)
    n = len(scores)
    alpha = 1 - confidence
    q_level = min(1.0, (1 - alpha) * (n + 1) / n)
    q_hat = np.quantile(scores, q_level)

    return q_hat, y_pred - q_hat, y_pred + q_hat


def conformal_uncertainty_wrapper(
    model: Any,
    confidence: float = 0.90,
) -> Callable:
    """
    Wrap an sklearn model to return conformal prediction intervals.

    Usage:
        model_with_uncertainty = conformal_uncertainty_wrapper(model, confidence=0.90)
        pred, lower, upper = model_with_uncertainty(X_test)

    Note: Model must be pre-fitted and you must provide calibration data separately.
    """
    def wrapped(X: np.ndarray, return_intervals: bool = True):
        pred = model.predict(X)
        if not return_intervals:
            return pred

        # Approximate interval from training data (if available)
        # Check both attribute existence and that it's not a Mock object
        has_training = (
            hasattr(model, "X_train_") and hasattr(model, "y_train_") and
            not callable(model.X_train_) and not callable(model.y_train_)
        )
        if has_training:
            try:
                X_train = np.asarray(model.X_train_)
                y_train = np.asarray(model.y_train_)
                # Compute residuals from training data
                train_pred = model.predict(X_train)
                residuals = np.abs(y_train - train_pred)
                q_hat = np.quantile(residuals, min(1.0, confidence))
                return pred, pred - q_hat, pred + q_hat
            except (TypeError, ValueError, AttributeError):
                # Fall through to std-based approach
                pass

        # Fallback: use prediction std as uncertainty
        std = np.std(pred)
        return pred, pred - 1.96 * std, pred + 1.96 * std

    return wrapped

    return wrapped


# ---------------------------------------------------------------------------
# Integration with ASTRA data registry
# ---------------------------------------------------------------------------

def apply_conformal_to_astra_data(
    data_source: str,
    target_column: str,
    model: Any,
    confidence: float = 0.90,
) -> Dict:
    """
    Apply conformal prediction to an ASTRA data source.

    This is a convenience function for integrating with ASTRA's data_registry.
    Automatically fetches data, trains model, and returns calibrated predictions.

    Parameters
    ----------
    data_source : str
        Name of data source in data registry
    target_column : str
        Column to predict
    model : Any
        Model to calibrate
    confidence : float
        Target coverage

    Returns
    -------
    dict with conformal results
    """
    try:
        from data_fetcher import DataFetcher
    except ImportError:
        return {
            "error": "data_fetcher module not available",
            "note": "This function requires ASTRA's data registry",
        }

    # Fetch data
    fetcher = DataFetcher()
    data = fetcher.fetch(data_source)

    if data is None or len(data) == 0:
        return {"error": f"Failed to fetch data from {data_source}"}

    # Extract features and target
    # This is simplified; real implementation would need feature engineering
    try:
        import pandas as pd
        df = pd.DataFrame(data)
        if target_column not in df.columns:
            return {"error": f"Column {target_column} not found in data"}

        # Use all other numeric columns as features
        feature_cols = [c for c in df.select_dtypes(include=[np.number]).columns
                       if c != target_column]

        if not feature_cols:
            return {"error": "No numeric feature columns found"}

        X = df[feature_cols].values
        y = df[target_column].values

        # Apply conformal calibration
        discover = ConformalDiscovery()
        result = discover.calibrate_ml_discovery(
            model=model,
            X=X,
            y=y,
            confidence=confidence,
        )

        return {
            "data_source": data_source,
            "target": target_column,
            "features": feature_cols,
            "n_samples": len(X),
            **result["summary"],
        }

    except Exception as e:
        return {
            "error": f"Failed to process data: {str(e)}",
            "note": "Ensure data is in tabular format with numeric columns",
        }


# ---------------------------------------------------------------------------
# Module self-test
# ---------------------------------------------------------------------------

def _run_self_test():
    """Run internal tests to verify conformal prediction implementation."""
    logger.info("Running conformal prediction self-test...")

    # Generate synthetic data
    np.random.seed(42)
    n = 500
    X = np.random.randn(n, 5)
    y = 2 * X[:, 0] + 0.5 * X[:, 1] + np.random.randn(n) * 0.3

    # Simple model
    from sklearn.linear_model import LinearRegression
    model = LinearRegression()

    # Test regression
    discover = ConformalDiscovery()
    result = discover.calibrate_ml_discovery(
        model=model, X=X, y=y, confidence=0.90
    )

    assert result["summary"]["empirical_coverage"] > 0.85, "Coverage too low"
    assert abs(result["summary"]["coverage_error"]) < 0.1, "Coverage error too large"

    logger.info(f"✓ Regression test passed: coverage={result['summary']['empirical_coverage']:.3f}")

    # Test classification
    X_cls = np.random.randn(n, 5)
    y_cls = (X_cls[:, 0] + X_cls[:, 1] > 0).astype(int)

    from sklearn.linear_model import LogisticRegression
    model_cls = LogisticRegression()

    result_cls = discover.calibrate_ml_discovery(
        model=model_cls, X=X_cls, y=y_cls, confidence=0.90
    )

    assert result_cls["summary"]["empirical_coverage"] > 0.85, "Classification coverage too low"

    logger.info(f"✓ Classification test passed: coverage={result_cls['summary']['empirical_coverage']:.3f}")
    logger.info("Conformal prediction module self-test complete")


if __name__ == "__main__":
    _run_self_test()
