"""
Data Scale-Up Layer for Transformational Architecture

Implements automated data ingestion for multiple astronomical surveys with
standardized CloudRecord schema and strict train/holdout splitting.

This module addresses the critical N=7 clouds problem by scaling to N≥30
independent clouds/regions with proper data provenance and holdout validation.

Version: 1.0.0
Date: 2026-07-04
"""

import hashlib
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class SurveyType(Enum):
    """Supported astronomical survey types"""
    HERSCHEL_GBS = "herschel_gould_belt_survey"
    LOFAR_LOTSS = "lofar_lotss_dr2"
    GAIA_DR3 = "gaia_dr3"
    JCMT_SCUBA2 = "jcmt_scuba2"
    ALMA_ARCHIVE = "alma_archive_continuum"
    CUSTOM = "custom_survey"


@dataclass
class CloudRecord:
    """
    Standardized schema for all cloud/region data across surveys.

    This ensures consistent handling of data from different surveys with
    proper physical units, calibration provenance, and metadata.
    """
    # Identification
    cloud_id: str  # Unique identifier (e.g., "IC5146 Herschel")
    survey_source: SurveyType  # Which survey this data comes from
    source_paper: str  # Machine-readable citation (DOI or arXiv)

    # Physical properties (all with uncertainties)
    right_ascension: float  # degrees
    declination: float  # degrees
    distance: float  # parsecs
    distance_uncertainty: float  # parsecs

    # Observational parameters
    angular_resolution: float  # arcseconds
    wavelength_band: str  # e.g., "250 micron", "150 MHz"
    calibration_provenance: str  # Calibration method/version
    data_quality_score: float  # 0-1, overall quality assessment

    # Physical measurements (with uncertainties)
    mass: Optional[float] = None  # solar masses
    mass_uncertainty: Optional[float] = None
    temperature: Optional[float] = None  # Kelvin
    temperature_uncertainty: Optional[float] = None
    column_density: Optional[float] = None  # cm^-2
    column_density_uncertainty: Optional[float] = None

    # Filament properties (if applicable)
    filament_width: Optional[float] = None  # parsecs
    filament_width_uncertainty: Optional[float] = None
    filament_length: Optional[float] = None  # parsecs
    filament_length_uncertainty: Optional[float] = None

    # Additional metadata
    additional_metadata: Dict[str, Any] = field(default_factory=dict)

    # Processing flags
    is_holdout: bool = False  # True if in holdout set
    ingestion_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['survey_source'] = self.survey_source.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CloudRecord':
        """Create from dictionary"""
        data = data.copy()
        if 'survey_source' in data and isinstance(data['survey_source'], str):
            data['survey_source'] = SurveyType(data['survey_source'])
        return cls(**data)

    def compute_hash(self) -> str:
        """
        Compute cryptographic hash of this record for holdout verification.

        This hash is used to verify that the holdout set remains untouched
        during discovery pipeline execution.
        """
        # Create canonical string representation
        canonical = json.dumps(self.to_dict(), sort_keys=True)

        # Compute SHA-256 hash
        return hashlib.sha256(canonical.encode()).hexdigest()


@dataclass
class IngestionResult:
    """Result of data ingestion operation"""
    success: bool
    clouds_ingested: int
    clouds_failed: int
    survey_source: SurveyType
    ingestion_time: str
    error_messages: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class DataScaleLayer:
    """
    Data Scale-Up Layer for multi-survey astronomical data ingestion.

    This class implements automated ingestion, standardization, and
    train/holdout splitting for rigorous discovery validation.
    """

    def __init__(self, base_data_dir: Optional[Path] = None):
        """
        Initialize the Data Scale-Up Layer.

        Args:
            base_data_dir: Base directory for data storage
        """
        self.base_data_dir = base_data_dir or Path.home() / '.astra_data_scale_layer'
        self.base_data_dir.mkdir(parents=True, exist_ok=True)

        # Data storage
        self.clouds: Dict[str, CloudRecord] = {}
        self.survey_connectors: Dict[SurveyType, Any] = {}

        # Holdout set management
        self.holdout_set: Dict[str, CloudRecord] = {}
        self.training_set: Dict[str, CloudRecord] = {}
        self.holdout_hash: Optional[str] = None

        # Holdout configuration
        self.holdout_fraction = 0.20  # 20% holdout
        self.min_sample_size = 30  # Minimum N for population-level claims

        logger.info(f"[DataScaleLayer] Initialized with base directory: {self.base_data_dir}")

    def register_survey_connector(self, survey_type: SurveyType, connector: Any):
        """
        Register a survey data connector.

        Args:
            survey_type: Type of survey
            connector: Connector object implementing ingest() method
        """
        self.survey_connectors[survey_type] = connector
        logger.info(f"[DataScaleLayer] Registered connector for {survey_type.value}")

    async def ingest_survey(self, survey_type: SurveyType) -> IngestionResult:
        """
        Ingest data from a specific survey.

        Args:
            survey_type: Type of survey to ingest

        Returns:
            IngestionResult with success status and statistics
        """
        if survey_type not in self.survey_connectors:
            return IngestionResult(
                success=False,
                clouds_ingested=0,
                clouds_failed=0,
                survey_source=survey_type,
                ingestion_time=datetime.now().isoformat(),
                error_messages=[f"No connector registered for {survey_type.value}"]
            )

        connector = self.survey_connectors[survey_type]

        try:
            logger.info(f"[DataScaleLayer] Starting ingestion for {survey_type.value}")

            # Call connector's ingest method
            raw_clouds = await connector.ingest()

            # Standardize to CloudRecord format
            standardized_clouds = []
            for raw_cloud in raw_clouds:
                try:
                    cloud_record = self._standardize_cloud_record(raw_cloud, survey_type)
                    standardized_clouds.append(cloud_record)
                except Exception as e:
                    logger.warning(f"[DataScaleLayer] Failed to standardize cloud: {e}")

            # Add to database
            for cloud in standardized_clouds:
                self._add_cloud(cloud)

            result = IngestionResult(
                success=True,
                clouds_ingested=len(standardized_clouds),
                clouds_failed=len(raw_clouds) - len(standardized_clouds),
                survey_source=survey_type,
                ingestion_time=datetime.now().isoformat(),
                warnings=[f"Standardized {len(standardized_clouds)}/{len(raw_clouds)} clouds"]
            )

            logger.info(f"[DataScaleLayer] ✅ Ingested {result.clouds_ingested} clouds from {survey_type.value}")
            return result

        except Exception as e:
            logger.error(f"[DataScaleLayer] Ingestion failed for {survey_type.value}: {e}")
            return IngestionResult(
                success=False,
                clouds_ingested=0,
                clouds_failed=0,
                survey_source=survey_type,
                ingestion_time=datetime.now().isoformat(),
                error_messages=[str(e)]
            )

    def _standardize_cloud_record(self, raw_data: Dict[str, Any], survey_type: SurveyType) -> CloudRecord:
        """
        Standardize raw survey data to CloudRecord format.

        Args:
            raw_data: Raw data from survey connector
            survey_type: Type of survey

        Returns:
            Standardized CloudRecord
        """
        # Extract and validate required fields
        cloud_id = raw_data.get('cloud_id', f"{survey_type.value}_unknown")
        source_paper = raw_data.get('source_paper', 'unknown')

        # Physical coordinates
        ra = float(raw_data.get('ra', 0.0))
        dec = float(raw_data.get('dec', 0.0))
        distance = float(raw_data.get('distance', 0.0))
        distance_err = float(raw_data.get('distance_uncertainty', 0.0))

        # Observational parameters
        angular_resolution = float(raw_data.get('angular_resolution', 0.0))
        wavelength_band = str(raw_data.get('wavelength_band', 'unknown'))
        calibration_provenance = str(raw_data.get('calibration_provenance', 'unknown'))
        data_quality_score = float(raw_data.get('data_quality_score', 0.5))

        # Optional physical measurements
        # Optional physical measurements
        def safe_float(value):
            """Safely convert to float if present"""
            return float(value) if value is not None else None

        mass = safe_float(raw_data.get('mass'))
        mass_err = safe_float(raw_data.get('mass_uncertainty'))
        temperature = safe_float(raw_data.get('temperature'))
        temp_err = safe_float(raw_data.get('temperature_uncertainty'))
        column_density = safe_float(raw_data.get('column_density'))
        col_err = safe_float(raw_data.get('column_density_uncertainty'))

        # Filament properties
        filament_width = safe_float(raw_data.get('filament_width'))
        width_err = safe_float(raw_data.get('filament_width_uncertainty'))
        filament_length = safe_float(raw_data.get('filament_length'))
        length_err = safe_float(raw_data.get('filament_length_uncertainty'))

        # Additional metadata

        # Additional metadata
        additional_metadata = raw_data.get('additional_metadata', {})

        return CloudRecord(
            cloud_id=cloud_id,
            survey_source=survey_type,
            source_paper=source_paper,
            right_ascension=ra,
            declination=dec,
            distance=distance,
            distance_uncertainty=distance_err,
            angular_resolution=angular_resolution,
            wavelength_band=wavelength_band,
            calibration_provenance=calibration_provenance,
            data_quality_score=data_quality_score,
            mass=mass,
            mass_uncertainty=mass_err,
            temperature=temperature,
            temperature_uncertainty=temp_err,
            column_density=column_density,
            column_density_uncertainty=col_err,
            filament_width=filament_width,
            filament_width_uncertainty=width_err,
            filament_length=filament_length,
            filament_length_uncertainty=length_err,
            additional_metadata=additional_metadata
        )

    def _add_cloud(self, cloud: CloudRecord):
        """Add a cloud to the database"""
        self.clouds[cloud.cloud_id] = cloud
        logger.debug(f"[DataScaleLayer] Added cloud: {cloud.cloud_id}")

    def setup_train_holdout_split(self, holdout_fraction: Optional[float] = None) -> Dict[str, int]:
        """
        Setup train/holdout split with cryptographic hashing.

        This creates a strict separation between training data (used for
        hypothesis generation) and holdout data (used only for replication
        validation in the Discovery Gate).

        Args:
            holdout_fraction: Fraction of data to holdout (default 0.20)

        Returns:
            Dictionary with split statistics
        """
        if holdout_fraction is not None:
            self.holdout_fraction = holdout_fraction

        if len(self.clouds) < self.min_sample_size:
            logger.warning(
                f"[DataScaleLayer] ⚠️ Only {len(self.clouds)} clouds available, "
                f"below recommended minimum of {self.min_sample_size}"
            )

        # Get list of cloud IDs
        cloud_ids = list(self.clouds.keys())

        # Simple hash-based split for reproducibility
        # Use cloud_id hash to determine holdout status
        holdout_ids = []
        training_ids = []

        for cloud_id in cloud_ids:
            # Use hash for deterministic assignment
            hash_val = int(hashlib.sha256(cloud_id.encode()).hexdigest(), 16)
            if (hash_val % 100) < (int(self.holdout_fraction * 100)):
                holdout_ids.append(cloud_id)
            else:
                training_ids.append(cloud_id)

        # Assign to sets
        self.training_set = {cid: self.clouds[cid] for cid in training_ids}
        self.holdout_set = {cid: self.clouds[cid] for cid in holdout_ids}

        # Mark holdout status in records
        for cloud_id in holdout_ids:
            self.holdout_set[cloud_id].is_holdout = True

        # Compute holdout hash for verification
        self.holdout_hash = self._compute_holdout_hash()

        stats = {
            'total_clouds': len(self.clouds),
            'training_clouds': len(self.training_set),
            'holdout_clouds': len(self.holdout_set),
            'holdout_fraction': len(self.holdout_set) / len(self.clouds) if self.clouds else 0,
            'holdout_hash': self.holdout_hash
        }

        logger.info(f"[DataScaleLayer] ✅ Train/holdout split created: {stats}")
        return stats

    def _compute_holdout_hash(self) -> str:
        """
        Compute cryptographic hash of entire holdout set.

        This hash is used to verify that the holdout set remains untouched
        during discovery pipeline execution.
        """
        # Sort holdout IDs for canonical ordering
        sorted_ids = sorted(self.holdout_set.keys())

        # Compute combined hash
        combined_hash = hashlib.sha256()
        for cloud_id in sorted_ids:
            cloud_hash = self.holdout_set[cloud_id].compute_hash()
            combined_hash.update(cloud_hash.encode())

        return combined_hash.hexdigest()

    def verify_holdout_integrity(self) -> bool:
        """
        Verify that holdout set has not been modified.

        Returns:
            True if holdout hash matches, False otherwise
        """
        if self.holdout_hash is None:
            logger.warning("[DataScaleLayer] No holdout hash set, cannot verify integrity")
            return False

        current_hash = self._compute_holdout_hash()
        is_valid = current_hash == self.holdout_hash

        if is_valid:
            logger.info("[DataScaleLayer] ✅ Holdout integrity verified")
        else:
            logger.error("[DataScaleLayer] ❌ Holdout integrity violated!")

        return is_valid

    def get_training_data(self) -> Dict[str, CloudRecord]:
        """Get training set (for hypothesis generation)"""
        return self.training_set.copy()

    def get_holdout_data(self) -> Dict[str, CloudRecord]:
        """Get holdout set (for replication validation only)"""
        return self.holdout_set.copy()

    def get_ingestion_statistics(self) -> Dict[str, Any]:
        """Get statistics about ingested data"""
        surveys_represented = set()
        for cloud in self.clouds.values():
            surveys_represented.add(cloud.survey_source.value)

        return {
            'total_clouds': len(self.clouds),
            'training_clouds': len(self.training_set),
            'holdout_clouds': len(self.holdout_set),
            'surveys_represented': list(surveys_represented),
            'holdout_hash': self.holdout_hash,
            'min_sample_size_met': len(self.clouds) >= self.min_sample_size,
            'data_directory': str(self.base_data_dir)
        }

    def save_state(self, filepath: Optional[Path] = None):
        """
        Save current state to disk for persistence.

        Args:
            filepath: Path to save state (default: base_data_dir/state.json)
        """
        if filepath is None:
            filepath = self.base_data_dir / 'data_scale_layer_state.json'

        state = {
            'clouds': {cid: cloud.to_dict() for cid, cloud in self.clouds.items()},
            'training_ids': list(self.training_set.keys()),
            'holdout_ids': list(self.holdout_set.keys()),
            'holdout_hash': self.holdout_hash,
            'holdout_fraction': self.holdout_fraction,
            'timestamp': datetime.now().isoformat()
        }

        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2)

        logger.info(f"[DataScaleLayer] Saved state to {filepath}")

    def load_state(self, filepath: Optional[Path] = None):
        """
        Load state from disk.

        Args:
            filepath: Path to load state from (default: base_data_dir/state.json)
        """
        if filepath is None:
            filepath = self.base_data_dir / 'data_scale_layer_state.json'

        if not filepath.exists():
            logger.warning(f"[DataScaleLayer] No state file found at {filepath}")
            return

        with open(filepath, 'r') as f:
            state = json.load(f)

        # Restore clouds
        self.clouds = {
            cid: CloudRecord.from_dict(cloud_data)
            for cid, cloud_data in state['clouds'].items()
        }

        # Restore splits
        training_ids = state.get('training_ids', [])
        holdout_ids = state.get('holdout_ids', [])

        self.training_set = {cid: self.clouds[cid] for cid in training_ids}
        self.holdout_set = {cid: self.clouds[cid] for cid in holdout_ids}

        # Restore metadata
        self.holdout_hash = state.get('holdout_hash')
        self.holdout_fraction = state.get('holdout_fraction', 0.20)

        logger.info(f"[DataScaleLayer] ✅ Loaded state from {filepath}")
        logger.info(f"[DataScaleLayer] {len(self.clouds)} clouds restored")


def create_data_scale_layer(base_data_dir: Optional[Path] = None) -> DataScaleLayer:
    """
    Factory function to create DataScaleLayer.

    Args:
        base_data_dir: Base directory for data storage

    Returns:
        Configured DataScaleLayer instance
    """
    return DataScaleLayer(base_data_dir)