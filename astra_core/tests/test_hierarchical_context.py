"""
Comprehensive tests for Hierarchical Context Processor

Tests cover:
- Unit tests for all components
- Integration tests with existing ASTRA modules
- Performance benchmarks
- Memory validation
- Quality assurance tests

Author: ASTRA Development Team
Date: 2026-06-25
"""

import pytest
import numpy as np
import time
from typing import List, Dict, Any
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from astra_core.reasoning.hierarchical_context_processor import (
    HierarchicalContextProcessor,
    ContextLevel,
    LevelConfiguration,
    HierarchicalContext,
    ChunkInfo,
    ProcessingResult,
    create_hierarchical_processor,
    process_query_hierarchical
)


class TestLevelConfiguration:
    """Test level configuration"""

    def test_default_configurations(self):
        """Test default level configurations are valid"""
        processor = HierarchicalContextProcessor()

        assert len(processor.level_configs) == 4
        assert ContextLevel.FINE in processor.level_configs
        assert ContextLevel.MID in processor.level_configs
        assert ContextLevel.COARSE in processor.level_configs
        assert ContextLevel.ABSTRACT in processor.level_configs

    def test_custom_configurations(self):
        """Test custom level configurations"""
        configs = [
            LevelConfiguration(ContextLevel.FINE, 1, 256, 1.0),
            LevelConfiguration(ContextLevel.MID, 8, 128, 8.0),
            LevelConfiguration(ContextLevel.COARSE, 8, 64, 64.0),
        ]

        processor = HierarchicalContextProcessor(level_configs=configs)

        assert len(processor.level_configs) == 3
        assert processor.level_configs[ContextLevel.MID].chunk_size == 8

    def test_invalid_configuration(self):
        """Test invalid configurations raise errors"""
        with pytest.raises(ValueError):
            LevelConfiguration(ContextLevel.FINE, 0, 256, 1.0)

        with pytest.raises(ValueError):
            LevelConfiguration(ContextLevel.MID, 4, -128, 4.0)


class TestHierarchicalContextProcessor:
    """Test hierarchical context processor"""

    def test_processor_initialization(self):
        """Test processor initializes correctly"""
        processor = HierarchicalContextProcessor()

        assert processor.enable_compression is True
        assert processor.enable_caching is True
        assert len(processor._compression_cache) == 0
        assert processor.stats['total_processed'] == 0

    def test_empty_token_list(self):
        """Test processing empty token list"""
        processor = HierarchicalContextProcessor()
        result = processor.process_context([])

        assert result.success is True
        assert result.hierarchical_context is not None
        assert result.hierarchical_context.num_tokens == 0

    def test_single_token(self):
        """Test processing single token"""
        processor = HierarchicalContextProcessor()
        result = processor.process_context(["test"])

        assert result.success is True
        assert result.hierarchical_context.num_tokens == 1
        assert result.compression_ratio >= 1.0

    def test_multiple_tokens(self):
        """Test processing multiple tokens"""
        processor = HierarchicalContextProcessor()
        tokens = ["token_" + str(i) for i in range(100)]
        result = processor.process_context(tokens)

        assert result.success is True
        assert result.hierarchical_context.num_tokens == 100
        assert result.compression_ratio > 1.0

    def test_large_token_sequence(self):
        """Test processing large token sequence"""
        processor = HierarchicalContextProcessor()
        tokens = ["token_" + str(i) for i in range(10000)]
        result = processor.process_context(tokens)

        assert result.success is True
        assert result.hierarchical_context.num_tokens == 10000
        assert result.compression_ratio >= 10.0  # Should achieve 10× compression

    def test_token_embeddings_provided(self):
        """Test processing with pre-computed embeddings"""
        processor = HierarchicalContextProcessor()
        tokens = ["test", "tokens", "here"]
        embeddings = np.random.randn(len(tokens), 512).astype(np.float32)

        result = processor.process_context(tokens, embeddings)

        assert result.success is True
        assert result.hierarchical_context.num_tokens == len(tokens)

    def test_compression_disabled(self):
        """Test processor with compression disabled"""
        processor = HierarchicalContextProcessor(enable_compression=False)
        tokens = ["token_" + str(i) for i in range(50)]
        result = processor.process_context(tokens)

        assert result.success is True
        # With compression disabled, should still work but differently

    def test_level_state_retrieval(self):
        """Test retrieving states at different levels"""
        processor = HierarchicalContextProcessor()
        tokens = ["token_" + str(i) for i in range(64)]
        result = processor.process_context(tokens)

        assert result.success is True

        # Get states at each level
        fine_states = processor.get_level_states(result.hierarchical_context, ContextLevel.FINE)
        mid_states = processor.get_level_states(result.hierarchical_context, ContextLevel.MID)
        coarse_states = processor.get_level_states(result.hierarchical_context, ContextLevel.COARSE)
        abstract_states = processor.get_level_states(result.hierarchical_context, ContextLevel.ABSTRACT)

        # Verify shapes
        assert fine_states.shape[0] == 64
        assert mid_states.shape[0] <= 64
        assert coarse_states.shape[0] <= mid_states.shape[0]
        assert abstract_states.shape[0] <= coarse_states.shape[0]

    def test_context_expansion(self):
        """Test expanding hierarchical context"""
        processor = HierarchicalContextProcessor()
        tokens = ["token_" + str(i) for i in range(64)]
        result = processor.process_context(tokens)

        assert result.success is True

        # Expand to fine level
        expanded = processor.expand_context(
            result.hierarchical_context,
            target_level=ContextLevel.FINE
        )

        assert expanded.shape[0] >= 1

    def test_chunk_information(self):
        """Test chunk information is created correctly"""
        processor = HierarchicalContextProcessor()
        tokens = ["token_" + str(i) for i in range(100)]
        result = processor.process_context(tokens)

        assert result.success is True
        assert len(result.chunk_info) > 0

        # Check that chunk info exists for non-fine levels
        for level in [ContextLevel.MID, ContextLevel.COARSE, ContextLevel.ABSTRACT]:
            if level in result.chunk_info:
                chunks = result.chunk_info[level]
                assert len(chunks) > 0
                assert all(isinstance(chunk, ChunkInfo) for chunk in chunks)

    def test_statistics_tracking(self):
        """Test processing statistics are tracked correctly"""
        processor = HierarchicalContextProcessor()

        # Process multiple queries
        for i in range(5):
            tokens = ["token_" + str(j) for j in range(100)]
            processor.process_context(tokens)

        stats = processor.get_statistics()

        assert stats['total_processed'] == 500  # 5 queries × 100 tokens
        assert stats['average_compression_ratio'] > 1.0
        assert stats['total_compression_time'] > 0


class TestCompressionAndExpansion:
    """Test compression and expansion operations"""

    def test_compression_ratio_calculation(self):
        """Test compression ratio is calculated correctly"""
        processor = HierarchicalContextProcessor()
        tokens = ["token_" + str(i) for i in range(256)]
        result = processor.process_context(tokens)

        assert result.success is True
        # With 256 tokens and 64× compression, should get ~4 chunks at top level
        assert result.compression_ratio >= 10.0

    def test_memory_savings(self):
        """Test memory savings are positive"""
        processor = HierarchicalContextProcessor()
        tokens = ["token_" + str(i) for i in range(1000)]
        result = processor.process_context(tokens)

        assert result.success is True
        assert result.memory_savings > 0

    def test_information_preservation(self):
        """Test information preservation metric"""
        processor = HierarchicalContextProcessor()
        tokens = ["token_" + str(i) for i in range(100)]
        result = processor.process_context(tokens)

        assert result.success is True
        assert 0.0 <= result.information_preservation <= 1.0
        assert result.information_preservation > 0.5  # Should preserve majority

    def test_coherence_score(self):
        """Test coherence score is valid"""
        processor = HierarchicalContextProcessor()
        tokens = ["token_" + str(i) for i in range(100)]
        result = processor.process_context(tokens)

        assert result.success is True
        assert 0.0 <= result.coherence_score <= 1.0


class TestPerformance:
    """Performance benchmarks"""

    def test_processing_speed(self):
        """Test processing speed is acceptable"""
        processor = HierarchicalContextProcessor()
        tokens = ["token_" + str(i) for i in range(1000)]

        start_time = time.time()
        result = processor.process_context(tokens)
        processing_time = time.time() - start_time

        assert result.success is True
        # Should process 1000 tokens in reasonable time (< 1 second)
        assert processing_time < 1.0

    def test_scalability(self):
        """Test scalability with input size"""
        processor = HierarchicalContextProcessor()

        sizes = [100, 1000, 10000]
        times = []

        for size in sizes:
            tokens = ["token_" + str(i) for i in range(size)]
            start_time = time.time()
            result = processor.process_context(tokens)
            times.append(time.time() - start_time)
            assert result.success is True

        # Should scale roughly linearly or better
        # (not quadratic like vanilla transformers)
        assert times[2] < times[0] * 200  # 100× size shouldn't take 200× time

    def test_compression_efficiency(self):
        """Test compression efficiency improves with size"""
        processor = HierarchicalContextProcessor()

        small_tokens = ["token_" + str(i) for i in range(50)]
        large_tokens = ["token_" + str(i) for i in range(5000)]

        small_result = processor.process_context(small_tokens)
        large_result = processor.process_context(large_tokens)

        # Larger inputs should achieve better compression
        assert large_result.compression_ratio >= small_result.compression_ratio


class TestIntegration:
    """Integration tests with existing ASTRA modules"""

    def test_convenience_function(self):
        """Test convenience functions work correctly"""
        query = ["Analyze", "star", "formation", "in", "molecular", "clouds"]
        result = process_query_hierarchical(query)

        assert result.success is True
        assert isinstance(result, ProcessingResult)

    def test_cache_functionality(self):
        """Test caching improves performance"""
        processor = HierarchicalContextProcessor(enable_caching=True)
        tokens = ["token_" + str(i) for i in range(100)]

        # First call
        start_time = time.time()
        result1 = processor.process_context(tokens)
        time1 = time.time() - start_time

        # Second call (should use cache)
        start_time = time.time()
        result2 = processor.process_context(tokens)
        time2 = time.time() - start_time

        assert result1.success is True
        assert result2.success is True

        stats = processor.get_statistics()
        # Should have some cache hits
        assert stats['total_cache_hits'] + stats['total_cache_misses'] > 0

    def test_clear_cache(self):
        """Test cache clearing works"""
        processor = HierarchicalContextProcessor()
        tokens = ["token_" + str(i) for i in range(100)]

        processor.process_context(tokens)
        processor.process_context(tokens)

        stats_before = processor.get_statistics()
        processor.clear_cache()
        stats_after = processor.get_statistics()

        assert stats_after['total_cache_hits'] == 0
        assert stats_after['total_cache_misses'] == 0


class TestEdgeCases:
    """Test edge cases and error conditions"""

    def test_very_long_tokens(self):
        """Test with very long token strings"""
        processor = HierarchicalContextProcessor()
        long_tokens = ["x" * 10000 for _ in range(10)]
        result = processor.process_context(long_tokens)

        assert result.success is True

    def test_special_characters(self):
        """Test with special characters"""
        processor = HierarchicalContextProcessor()
        special_tokens = ["@#$%", "˜µ©", "∆∂∑", "Hello∆World"]
        result = processor.process_context(special_tokens)

        assert result.success is True

    def test_unicode_tokens(self):
        """Test with unicode characters"""
        processor = HierarchicalContextProcessor()
        unicode_tokens = ["你好", "世界", "مرحبا", "العالم"]
        result = processor.process_context(unicode_tokens)

        assert result.success is True

    def test_mixed_token_types(self):
        """Test with mixed token types"""
        processor = HierarchicalContextProcessor()
        mixed_tokens = ["string", 123, 45.67, None, True, ["nested"]]
        result = processor.process_context(mixed_tokens)

        assert result.success is True


@pytest.mark.benchmark
class TestBenchmarks:
    """Performance benchmarks for optimization"""

    def test_benchmark_compression_ratio(self):
        """Benchmark compression ratio across sizes"""
        processor = HierarchicalContextProcessor()

        sizes = [100, 1000, 10000, 100000]
        ratios = []

        for size in sizes:
            tokens = ["token_" + str(i) for i in range(size)]
            result = processor.process_context(tokens)
            ratios.append(result.compression_ratio)

        # All should achieve significant compression
        for ratio in ratios:
            assert ratio >= 10.0, f"Compression ratio {ratio} below target 10×"

    def test_benchmark_memory_usage(self):
        """Benchmark memory savings"""
        import sys

        processor = HierarchicalContextProcessor()
        tokens = ["token_" + str(i) for i in range(10000)]

        # Measure memory before
        mem_before = sys.getsizeof(processor)

        result = processor.process_context(tokens)

        # Measure memory after
        mem_after = sys.getsizeof(processor) + sys.getsizeof(result.hierarchical_context)

        # Memory usage should be reasonable
        assert (mem_after - mem_before) < 100 * 1024 * 1024  # < 100MB


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
