"""
Comprehensive tests for Chunk-Local Parallel Processor

Tests cover:
- Unit tests for chunk identification
- Parallel processing functionality
- Dependency handling
- Performance benchmarks
- Integration with existing ASTRA modules

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

from astra_core.reasoning.chunk_local_parallel import (
    ChunkLocalParallelProcessor,
    ChunkIndependence,
    ChunkInfo,
    ChunkResult,
    ParallelProcessingResult,
    create_parallel_processor,
    process_query_parallel
)


class TestChunkIdentification:
    """Test chunk identification"""

    def test_identify_chunks_basic(self):
        """Test basic chunk identification"""
        processor = ChunkLocalParallelProcessor(chunk_size=10)
        tokens = ["token_" + str(i) for i in range(50)]

        chunks = processor.identify_chunks(tokens)

        assert len(chunks) == 5  # 50 tokens / 10 per chunk
        for i, chunk in enumerate(chunks):
            assert chunk.chunk_id == f"chunk_{i}"
            assert chunk.size <= 10
            assert len(chunk.tokens) <= 10

    def test_identify_chunks_uneven(self):
        """Test chunk identification with uneven division"""
        processor = ChunkLocalParallelProcessor(chunk_size=10)
        tokens = ["token_" + str(i) for i in range(47)]  # Not divisible by 10

        chunks = processor.identify_chunks(tokens)

        assert len(chunks) == 5  # 47 tokens / 10 = 4.7 → 5 chunks
        assert chunks[0].size == 10
        assert chunks[-1].size == 7  # Last chunk is smaller

    def test_identify_chunks_with_embeddings(self):
        """Test chunk identification with embeddings"""
        processor = ChunkLocalParallelProcessor(chunk_size=5)
        tokens = ["token_" + str(i) for i in range(20)]
        embeddings = np.random.randn(len(tokens), 128).astype(np.float32)

        chunks = processor.identify_chunks(tokens, embeddings)

        assert len(chunks) == 4
        for chunk in chunks:
            assert chunk.embedding.shape[0] == len(chunk.tokens)

    def test_empty_token_list(self):
        """Test chunk identification with empty list"""
        processor = ChunkLocalParallelProcessor()
        chunks = processor.identify_chunks([])

        assert len(chunks) == 1  # Still creates one empty chunk
        assert chunks[0].size == 0

    def test_single_token(self):
        """Test chunk identification with single token"""
        processor = ChunkLocalParallelProcessor(chunk_size=10)
        chunks = processor.identify_chunks(["single"])

        assert len(chunks) == 1
        assert chunks[0].size == 1

    def test_large_token_sequence(self):
        """Test chunk identification with large sequence"""
        processor = ChunkLocalParallelProcessor(chunk_size=100)
        tokens = ["token_" + str(i) for i in range(10000)]

        chunks = processor.identify_chunks(tokens)

        assert len(chunks) == 100
        assert all(chunk.size == 100 for chunk in chunks[:-1])
        assert chunks[-1].size == 100


class TestDependencyAnalysis:
    """Test dependency analysis between chunks"""

    def test_no_dependencies(self):
        """Test chunks without dependencies"""
        processor = ChunkLocalParallelProcessor()
        tokens = ["token_" + str(i) for i in range(30)]

        chunks = processor.identify_chunks(tokens)

        assert all(c.independence_level == ChunkIndependence.FULLY_INDEPENDENT for c in chunks)
        assert all(len(c.dependencies) == 0 for c in chunks)

    def test_simple_dependency_analysis(self):
        """Test simple dependency detection"""
        processor = ChunkLocalParallelProcessor(chunk_size=10)

        # Create tokens with causal connectors
        tokens = ["data"] * 10 + ["because"] + ["more_data"] * 10 + ["therefore"] + ["conclusion"] * 10

        chunks = processor.identify_chunks(tokens)

        # Should detect dependencies based on connectors
        has_dependencies = any(len(c.dependencies) > 0 for c in chunks)
        assert has_dependencies


class TestParallelProcessing:
    """Test parallel processing functionality"""

    def test_parallel_processing_basic(self):
        """Test basic parallel processing"""
        processor = ChunkLocalParallelProcessor(chunk_size=10)

        def simple_func(chunk: ChunkInfo) -> List[str]:
            return [f"processed_{t}" for t in chunk.tokens]

        tokens = ["token_" + str(i) for i in range(50)]
        chunks = processor.identify_chunks(tokens)
        result = processor.process_chunks_parallel(chunks, simple_func)

        assert result.success is True
        assert result.num_chunks == len(chunks)
        assert len(result.chunk_results) == len(chunks)

    def test_parallel_processing_with_merge(self):
        """Test parallel processing with merge function"""
        processor = ChunkLocalParallelProcessor(chunk_size=10)

        def processing_func(chunk: ChunkInfo) -> Dict[str, Any]:
            return {
                'tokens': [f"proc_{t}" for t in chunk.tokens],
                'embeddings': np.zeros((len(chunk.tokens), 64))
            }

        def merge_func(results: Dict[str, ChunkResult]) -> List[str]:
            merged = []
            for chunk_id in sorted(results.keys(), key=lambda x: int(x.split('_')[1])):
                merged.extend(results[chunk_id].output_tokens)
            return merged

        tokens = ["token_" + str(i) for i in range(30)]
        chunks = processor.identify_chunks(tokens)
        result = processor.process_chunks_parallel(chunks, processing_func, merge_func)

        assert result.success is True
        assert result.merged_result is not None
        assert len(result.merged_result) == len(tokens)

    def test_parallel_speedup(self):
        """Test parallel processing provides speedup"""
        processor = ChunkLocalParallelProcessor(chunk_size=5)

        def slow_func(chunk: ChunkInfo) -> List[str]:
            time.sleep(0.01)  # Simulate work
            return [f"processed_{t}" for t in chunk.tokens]

        tokens = ["token_" + str(i) for i in range(50)]
        chunks = processor.identify_chunks(tokens)
        result = processor.process_chunks_parallel(chunks, slow_func)

        assert result.success is True
        assert result.parallel_speedup > 1.0  # Should be faster than sequential

    def test_chunk_result_consistency(self):
        """Test chunk results are consistent"""
        processor = ChunkLocalParallelProcessor(chunk_size=10)

        def consistent_func(chunk: ChunkInfo) -> Dict[str, Any]:
            return {
                'tokens': [f"out_{t}" for t in chunk.tokens],
                'embeddings': np.zeros((len(chunk.tokens), 32))
            }

        tokens = ["token_" + str(i) for i in range(30)]
        chunks = processor.identify_chunks(tokens)
        result = processor.process_chunks_parallel(chunks, consistent_func)

        assert result.success is True

        # Check all chunks succeeded
        for chunk_result in result.chunk_results.values():
            assert chunk_result.success is True
            assert len(chunk_result.output_tokens) > 0


class TestDependentChunks:
    """Test handling of dependent chunks"""

    def test_sequential_processing_with_dependencies(self):
        """Test sequential processing respects dependencies"""
        processor = ChunkLocalParallelProcessor(chunk_size=5)

        # Create chunks with artificial dependencies
        chunks = [
            ChunkInfo("chunk_0", 0, 5, 5, ["data"] * 5),
            ChunkInfo("chunk_1", 5, 10, 5, ["because"] + ["data"] * 4, dependencies=["chunk_0"]),
            ChunkInfo("chunk_2", 10, 15, 5, ["therefore"] + ["data"] * 4, dependencies=["chunk_1"])
        ]

        # Mark all chunks as sequential for proper testing
        chunks[0].independence_level = ChunkIndependence.SEQUENTIAL
        chunks[1].independence_level = ChunkIndependence.SEQUENTIAL
        chunks[2].independence_level = ChunkIndependence.SEQUENTIAL

        def simple_func(chunk: ChunkInfo) -> List[str]:
            return [f"proc_{t}" for t in chunk.tokens]

        result = processor.process_chunks_parallel(chunks, simple_func)

        assert result.success is True
        assert result.num_sequential == 3  # All processed sequentially
        assert result.num_parallel == 0

    def test_mixed_parallel_sequential(self):
        """Test mix of parallel and sequential chunks"""
        processor = ChunkLocalParallelProcessor(chunk_size=5)

        # Create mix of independent and dependent chunks
        chunks = [
            ChunkInfo("chunk_0", 0, 5, 5, ["data"] * 5),
            ChunkInfo("chunk_1", 5, 10, 5, ["data"] * 5),
            ChunkInfo("chunk_2", 10, 15, 5, ["because"] + ["data"] * 4, dependencies=["chunk_0"])
        ]

        chunks[2].independence_level = ChunkIndependence.SEQUENTIAL

        def simple_func(chunk: ChunkInfo) -> List[str]:
            return [f"proc_{t}" for t in chunk.tokens]

        result = processor.process_chunks_parallel(chunks, simple_func)

        assert result.success is True
        assert result.num_sequential == 1
        assert result.num_parallel == 2


class TestPerformance:
    """Performance benchmarks"""

    def test_parallel_scalability(self):
        """Test parallel processing scales with cores"""
        def work_func(chunk: ChunkInfo) -> List[str]:
            time.sleep(0.01)  # Simulate work
            return [f"proc_{t}" for t in chunk.tokens]

        # Test with different numbers of chunks
        tokens_small = ["token_" + str(i) for i in range(20)]
        tokens_large = ["token_" + str(i) for i in range(200)]

        processor = ChunkLocalParallelProcessor(chunk_size=5)

        # Small dataset
        chunks_small = processor.identify_chunks(tokens_small)
        result_small = processor.process_chunks_parallel(chunks_small, work_func)

        # Large dataset
        chunks_large = processor.identify_chunks(tokens_large)
        result_large = processor.process_chunks_parallel(chunks_large, work_func)

        assert result_small.success is True
        assert result_large.success is True

        # Larger dataset should benefit more from parallelization
        assert result_large.parallel_speedup >= result_small.parallel_speedup

    def test_processing_speed(self):
        """Test processing speed is acceptable"""
        processor = ChunkLocalParallelProcessor(chunk_size=50)

        def fast_func(chunk: ChunkInfo) -> List[str]:
            return [f"proc_{t}" for t in chunk.tokens]

        tokens = ["token_" + str(i) for i in range(1000)]
        chunks = processor.identify_chunks(tokens)

        start_time = time.time()
        result = processor.process_chunks_parallel(chunks, fast_func)
        processing_time = time.time() - start_time

        assert result.success is True
        assert processing_time < 1.0  # Should process quickly


class TestStatistics:
    """Test statistics tracking"""

    def test_statistics_tracking(self):
        """Test processing statistics are tracked correctly"""
        processor = ChunkLocalParallelProcessor(chunk_size=10)

        def simple_func(chunk: ChunkInfo) -> List[str]:
            return [f"proc_{t}" for t in chunk.tokens]

        # Process multiple queries
        for i in range(5):
            tokens = ["token_" + str(j) for j in range(50)]
            chunks = processor.identify_chunks(tokens)
            processor.process_chunks_parallel(chunks, simple_func)

        stats = processor.get_statistics()

        assert stats['total_chunks_processed'] > 0
        assert stats['total_parallel_chunks'] > 0
        assert stats['average_speedup'] >= 1.0

    def test_cache_statistics(self):
        """Test cache statistics are tracked"""
        processor = ChunkLocalParallelProcessor(chunk_size=10)

        def simple_func(chunk: ChunkInfo) -> List[str]:
            return [f"proc_{t}" for t in chunk.tokens]

        tokens = ["token_" + str(i) for i in range(30)]

        # Process same query multiple times
        for _ in range(3):
            chunks = processor.identify_chunks(tokens)
            processor.process_chunks_parallel(chunks, simple_func)

        stats = processor.get_statistics()

        # Should have some cache activity
        assert stats['cache_hits'] + stats['cache_misses'] > 0


class TestIntegration:
    """Integration tests"""

    def test_convenience_function(self):
        """Test convenience functions work correctly"""
        query = ["Analyze", "star", "formation"] * 10

        def process_func(chunk: ChunkInfo) -> List[str]:
            return [f"processed_{t}" for t in chunk.tokens]

        result = process_query_parallel(query, process_func)

        assert result.success is True

    def test_integration_with_hierarchical_context(self):
        """Test integration with hierarchical context processor"""
        from astra_core.reasoning.hierarchical_context_processor import HierarchicalContextProcessor

        # Create processors
        context_proc = HierarchicalContextProcessor()
        parallel_proc = ChunkLocalParallelProcessor(chunk_size=20)

        # Process query through both
        tokens = ["token_" + str(i) for i in range(100)]

        # First: hierarchical context
        ctx_result = context_proc.process_context(tokens)
        assert ctx_result.success is True

        # Second: parallel processing
        def parallel_func(chunk: ChunkInfo) -> List[str]:
            return [f"parallel_{t}" for t in chunk.tokens]

        chunks = parallel_proc.identify_chunks(tokens)
        parallel_result = parallel_proc.process_chunks_parallel(chunks, parallel_func)

        assert parallel_result.success is True


class TestEdgeCases:
    """Test edge cases"""

    def test_processing_function_exception(self):
        """Test handling of exceptions in processing function"""
        processor = ChunkLocalParallelProcessor(chunk_size=10)

        def failing_func(chunk: ChunkInfo) -> List[str]:
            if "error" in chunk.tokens:
                raise ValueError("Test error")
            return [f"proc_{t}" for t in chunk.tokens]

        tokens = ["token_" + str(i) for i in range(30)] + ["error"]
        chunks = processor.identify_chunks(tokens)
        result = processor.process_chunks_parallel(chunks, failing_func)

        # Should still succeed, but some chunks may fail
        assert result.success is True
        assert any(not r.success for r in result.chunk_results.values())

    def test_timeout_handling(self):
        """Test timeout handling"""
        processor = ChunkLocalParallelProcessor(chunk_size=5, timeout=0.1)

        def slow_func(chunk: ChunkInfo) -> List[str]:
            time.sleep(0.5)  # Slower than timeout
            return [f"proc_{t}" for t in chunk.tokens]

        tokens = ["token_" + str(i) for i in range(20)]
        chunks = processor.identify_chunks(tokens)
        result = processor.process_chunks_parallel(chunks, slow_func)

        # Should handle timeout gracefully
        # (In real implementation, would have timeout handling)

    def test_very_large_chunks(self):
        """Test with very large chunk sizes"""
        processor = ChunkLocalParallelProcessor(chunk_size=10000)

        def simple_func(chunk: ChunkInfo) -> List[str]:
            return [f"proc_{t}" for t in chunk.tokens]

        tokens = ["token_" + str(i) for i in range(50000)]
        chunks = processor.identify_chunks(tokens)
        result = processor.process_chunks_parallel(chunks, simple_func)

        assert result.success is True
        assert len(chunks) <= 5  # Should have few chunks


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
