"""
Comprehensive tests for Hierarchical Knowledge Compressor

Tests cover:
- Unit tests for encoding at each level
- Unit tests for decoding and predictions
- Integration with hierarchical context processor
- Performance benchmarks
- Quality assurance tests

Author: ASTRA Development Team
Date: 2026-06-25
"""

import pytest
import numpy as np
from typing import List, Dict, Any
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from astra_core.knowledge.hierarchical_knowledge_compressor import (
    HierarchicalKnowledgeCompressor,
    KnowledgeLevel,
    KnowledgeState,
    EncodingResult,
    DecodingResult,
    ObservationData,
    create_knowledge_compressor,
    encode_observations,
    decode_predictions
)


class TestObservationData:
    """Test observation data creation"""

    def test_create_observation_data(self):
        """Test creating observation data"""
        obs = ObservationData(
            data_type="spectrum",
            values=np.array([1.0, 2.0, 3.0]),
            uncertainties=np.array([0.1, 0.1, 0.1]),
            metadata={'instrument': 'test'}
        )

        assert obs.data_type == "spectrum"
        assert len(obs.values) == 3
        assert obs.uncertainties is not None
        assert obs.metadata['instrument'] == 'test'

    def test_observation_without_uncertainties(self):
        """Test observation without uncertainties"""
        obs = ObservationData(
            data_type="image",
            values=np.random.randn(10, 10)
        )

        assert obs.uncertainties is None
        assert obs.values.shape == (10, 10)


class TestKnowledgeEncoding:
    """Test knowledge encoding"""

    def test_encode_observations_basic(self):
        """Test basic observation encoding"""
        compressor = create_knowledge_compressor()

        observations = [
            ObservationData(
                data_type="spectrum",
                values=np.array([1.0, 2.0, 3.0, 4.0, 5.0])
            )
        ]

        result = compressor.encode_observations(observations)

        assert result.success is True
        assert len(result.knowledge_states) == 4  # All 4 levels

    def test_encode_multiple_observations(self):
        """Test encoding multiple observations"""
        compressor = create_knowledge_compressor()

        observations = [
            ObservationData("spectrum", np.random.randn(100)),
            ObservationData("image", np.random.randn(50, 50)),
            ObservationData("time_series", np.random.randn(200))
        ]

        result = compressor.encode_observations(observations)

        assert result.success is True
        assert result.compression_ratio > 1.0

    def test_encode_observations_level(self):
        """Test encoding at observation level"""
        compressor = create_knowledge_compressor()

        observations = [
            ObservationData("spectrum", np.array([1.0, 2.0, 3.0]))
        ]

        result = compressor.encode_observations(observations)

        obs_state = result.knowledge_states[KnowledgeLevel.OBSERVATIONS]
        assert obs_state.level == KnowledgeLevel.OBSERVATIONS
        assert len(obs_state.state_vector) > 0
        assert obs_state.confidence == 1.0

    def test_encode_parameters_level(self):
        """Test encoding at parameter level"""
        compressor = create_knowledge_compressor()

        observations = [
            ObservationData("spectrum", np.random.randn(50))
        ]

        result = compressor.encode_observations(observations)

        param_state = result.knowledge_states[KnowledgeLevel.PARAMETERS]
        assert param_state.level == KnowledgeLevel.PARAMETERS
        assert param_state.source_level == KnowledgeLevel.OBSERVATIONS
        assert param_state.compression_ratio > 1.0

    def test_encode_principles_level(self):
        """Test encoding at principles level"""
        compressor = create_knowledge_compressor()

        observations = [
            ObservationData("spectrum", np.random.randn(100))
        ]

        result = compressor.encode_observations(observations)

        principle_state = result.knowledge_states[KnowledgeLevel.PRINCIPLES]
        assert principle_state.level == KnowledgeLevel.PRINCIPLES
        assert principle_state.source_level == KnowledgeLevel.PARAMETERS

    def test_encode_theories_level(self):
        """Test encoding at theories level"""
        compressor = create_knowledge_compressor()

        observations = [
            ObservationData("spectrum", np.random.randn(100))
        ]

        result = compressor.encode_observations(observations)

        theory_state = result.knowledge_states[KnowledgeLevel.THEORIES]
        assert theory_state.level == KnowledgeLevel.THEORIES
        assert theory_state.confidence > 0.8

    def test_compression_ratio_calculation(self):
        """Test compression ratio is calculated correctly"""
        compressor = create_knowledge_compressor()

        observations = [
            ObservationData("spectrum", np.random.randn(1000))
        ]

        result = compressor.encode_observations(observations)

        assert result.success is True
        assert result.compression_ratio > 10.0  # Should achieve significant compression

    def test_information_loss_estimation(self):
        """Test information loss estimation"""
        compressor = create_knowledge_compressor()

        observations = [
            ObservationData("spectrum", np.random.randn(500))
        ]

        result = compressor.encode_observations(observations)

        assert result.success is True
        assert 0.0 <= result.information_loss <= 1.0
        assert result.reconstruction_fidelity == 1.0 - result.information_loss


class TestKnowledgeDecoding:
    """Test knowledge decoding"""

    def test_decode_from_theory_level(self):
        """Test decoding from theory level"""
        compressor = create_knowledge_compressor()

        # First encode some observations
        observations = [
            ObservationData("spectrum", np.random.randn(100))
        ]
        encoding_result = compressor.encode_observations(observations)

        assert encoding_result.success is True

        # Get theory state
        theory_state = encoding_result.knowledge_states[KnowledgeLevel.THEORIES]

        # Decode to observations
        decoding_result = compressor.decode_predictions(theory_state)

        assert decoding_result.success is True
        assert decoding_result.predictions is not None
        assert decoding_result.accuracy > 0.0

    def test_decode_to_specific_level(self):
        """Test decoding to specific level"""
        compressor = create_knowledge_compressor()

        # Encode observations
        observations = [ObservationData("spectrum", np.random.randn(100))]
        encoding_result = compressor.encode_observations(observations)

        theory_state = encoding_result.knowledge_states[KnowledgeLevel.THEORIES]

        # Decode to parameters level only
        decoding_result = compressor.decode_predictions(
            theory_state,
            target_level=KnowledgeLevel.PARAMETERS
        )

        assert decoding_result.success is True

    def test_reconstruct_at_level(self):
        """Test reconstruction at specific level"""
        compressor = create_knowledge_compressor()

        # Encode
        observations = [ObservationData("spectrum", np.random.randn(100))]
        encoding_result = compressor.encode_observations(observations)

        theory_state = encoding_result.knowledge_states[KnowledgeLevel.THEORIES]

        # Reconstruct at principles level
        reconstructed = compressor.reconstruct_at_level(
            theory_state,
            KnowledgeLevel.PRINCIPLES
        )

        assert reconstructed.level == KnowledgeLevel.PRINCIPLES
        assert len(reconstructed.state_vector) > 0

    def test_expansion_ratio_calculation(self):
        """Test expansion ratio calculation"""
        compressor = create_knowledge_compressor()

        # Encode
        observations = [ObservationData("spectrum", np.random.randn(100))]
        encoding_result = compressor.encode_observations(observations)

        theory_state = encoding_result.knowledge_states[KnowledgeLevel.THEORIES]

        # Decode
        decoding_result = compressor.decode_predictions(theory_state)

        assert decoding_result.success is True
        assert decoding_result.expansion_ratio >= 1.0


class TestIntegration:
    """Integration tests with other ASTRA components"""

    def test_integration_with_hierarchical_context(self):
        """Test integration with hierarchical context processor"""
        from astra_core.reasoning.hierarchical_context_processor import HierarchicalContextProcessor

        # Create both processors
        context_proc = HierarchicalContextProcessor()
        knowledge_proc = HierarchicalKnowledgeCompressor()

        # Process query through context processor
        query_tokens = ["Analyze", "stellar", "spectrum"]
        ctx_result = context_proc.process_context(query_tokens)

        assert ctx_result.success is True

        # Create observations from context
        observations = [ObservationData("context", np.random.randn(50))]
        knowledge_result = knowledge_proc.encode_observations(observations)

        assert knowledge_result.success is True


class TestPerformance:
    """Performance benchmarks"""

    def test_encoding_speed(self):
        """Test encoding speed is acceptable"""
        compressor = create_knowledge_compressor()

        observations = [
            ObservationData("spectrum", np.random.randn(1000)),
            ObservationData("image", np.random.randn(100, 100))
        ]

        import time
        start_time = time.time()
        result = compressor.encode_observations(observations)
        encoding_time = time.time() - start_time

        assert result.success is True
        assert encoding_time < 1.0  # Should encode quickly

    def test_decoding_speed(self):
        """Test decoding speed is acceptable"""
        compressor = create_knowledge_compressor()

        # First encode
        observations = [ObservationData("spectrum", np.random.randn(500))]
        encoding_result = compressor.encode_observations(observations)

        theory_state = encoding_result.knowledge_states[KnowledgeLevel.THEORIES]

        import time
        start_time = time.time()
        result = compressor.decode_predictions(theory_state)
        decoding_time = time.time() - start_time

        assert result.success is True
        assert decoding_time < 1.0

    def test_large_dataset_performance(self):
        """Test performance with large dataset"""
        compressor = create_knowledge_compressor()

        # Large dataset
        observations = [
            ObservationData("spectrum", np.random.randn(10000)),
            ObservationData("image", np.random.randn(500, 500))
        ]

        result = compressor.encode_observations(observations)

        assert result.success is True
        assert result.compression_ratio > 100.0  # High compression for large data


class TestStatistics:
    """Test statistics tracking"""

    def test_encoding_statistics(self):
        """Test encoding statistics are tracked"""
        compressor = create_knowledge_compressor()

        observations = [ObservationData("spectrum", np.random.randn(100))]

        # Encode multiple times
        for _ in range(3):
            compressor.encode_observations(observations)

        stats = compressor.get_statistics()

        assert stats['total_encodings'] == 3
        assert stats['average_compression_time'] > 0
        assert stats['total_compression_ratio'] > 1.0

    def test_decoding_statistics(self):
        """Test decoding statistics are tracked"""
        compressor = create_knowledge_compressor()

        # Encode once
        observations = [ObservationData("spectrum", np.random.randn(100))]
        encoding_result = compressor.encode_observations(observations)

        theory_state = encoding_result.knowledge_states[KnowledgeLevel.THEORIES]

        # Decode multiple times
        for _ in range(3):
            compressor.decode_predictions(theory_state)

        stats = compressor.get_statistics()

        assert stats['total_decodings'] == 3
        assert stats['average_expansion_time'] > 0


class TestEdgeCases:
    """Test edge cases"""

    def test_empty_observations(self):
        """Test with empty observations list"""
        compressor = create_knowledge_compressor()

        result = compressor.encode_observations([])

        # Should handle gracefully
        assert result.encoding_time >= 0  # Just check it doesn't crash

    def test_single_value_observation(self):
        """Test with single value observation"""
        compressor = create_knowledge_compressor()

        observations = [
            ObservationData("single", np.array([42.0]))
        ]

        result = compressor.encode_observations(observations)

        # Should handle single value
        assert result.encoding_time >= 0

    def test_very_long_observation(self):
        """Test with very long observation vector"""
        compressor = create_knowledge_compressor()

        observations = [
            ObservationData("long", np.random.randn(100000))
        ]

        result = compressor.encode_observations(observations)

        # Should handle long vectors by truncation
        assert result.encoding_time >= 0

    def test_high_dimensional_observation(self):
        """Test with high-dimensional observation"""
        compressor = create_knowledge_compressor()

        observations = [
            ObservationData("high_dim", np.random.randn(1000, 1000))
        ]

        result = compressor.encode_observations(observations)

        # Should handle high-dimensional data
        assert result.encoding_time >= 0


class TestConvenienceFunctions:
    """Test convenience functions"""

    def test_create_knowledge_compressor(self):
        """Test convenience function for creating compressor"""
        compressor = create_knowledge_compressor()

        assert isinstance(compressor, HierarchicalKnowledgeCompressor)

    def test_encode_observations_convenience(self):
        """Test convenience encoding function"""
        observations = [ObservationData("test", np.array([1.0, 2.0, 3.0]))]

        result = encode_observations(observations)

        assert result.success is True

    def test_decode_predictions_convenience(self):
        """Test convenience decoding function"""
        # First encode
        observations = [ObservationData("test", np.array([1.0, 2.0, 3.0]))]
        encoding_result = encode_observations(observations)

        theory_state = encoding_result.knowledge_states[KnowledgeLevel.THEORIES]

        # Decode using convenience function
        result = decode_predictions(theory_state)

        assert result.success is True


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
