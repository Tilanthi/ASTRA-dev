"""
Reciprocal Rank Fusion (RRF)

Combines rankings from multiple sources for unified retrieval.
Fusion weights: Graph (0.4) > Ontology (0.3) > Vector (0.3)
"""

from typing import List, Dict, Tuple, Any, Optional
from collections import defaultdict


class ReciprocalRankFusion:
    """
    Reciprocal Rank Fusion for multi-source retrieval.

    Combines rankings from:
    - Graph connectivity (memory graph)
    - Ontological structure (semantic memory)
    - Vector similarity (embeddings)

    Formula: score = Σ (weight / (k + rank))
    where k is a constant (default 60)
    """

    def __init__(self,
                 k: int = 60,
                 weights: Optional[Dict[str, float]] = None):
        """
        Initialize RRF.

        Args:
            k: RRF constant (higher reduces impact of top ranks)
            weights: Source weights (default: graph=0.4, ontology=0.3, vector=0.3)
        """
        self.k = k
        self.weights = weights or {
            'graph': 0.4,
            'ontology': 0.3,
            'vector': 0.3
        }

    def fuse(self,
             rankings: Dict[str, List[Tuple[str, float]]]) -> List[Tuple[str, float]]:
        """
        Fuse rankings from multiple sources.

        Args:
            rankings: Dict mapping source name to list of (item_id, score) tuples

        Returns:
            Fused ranking as list of (item_id, fused_score) tuples
        """
        fused_scores = defaultdict(float)

        for source, results in rankings.items():
            weight = self.weights.get(source, 1.0 / len(rankings))

            for rank, (item_id, score) in enumerate(results):
                # RRF formula
                rrf_score = weight / (self.k + rank + 1)
                fused_scores[item_id] += rrf_score

        # Sort by fused score
        result = sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)
        return result

    def fuse_with_scores(self,
                        rankings: Dict[str, List[Tuple[str, float]]],
                        normalize: bool = True) -> List[Tuple[str, float]]:
        """
        Fuse rankings considering both rank and original scores.

        Args:
            rankings: Dict mapping source to (item_id, score) tuples
            normalize: Whether to normalize scores first

        Returns:
            Fused ranking
        """
        # Normalize scores if requested
        if normalize:
            normalized = {}
            for source, results in rankings.items():
                if not results:
                    normalized[source] = []
                    continue

                # Min-max normalization
                scores = [s for _, s in results]
                min_score = min(scores)
                max_score = max(scores)

                if max_score == min_score:
                    normalized[source] = [(iid, 1.0) for iid, _ in results]
                else:
                    normalized[source] = [
                        (iid, (s - min_score) / (max_score - min_score))
                        for iid, s in results
                    ]
            rankings = normalized

        # Combine rank and score information
        fused_scores = defaultdict(float)

        for source, results in rankings.items():
            weight = self.weights.get(source, 1.0 / len(rankings))

            for rank, (item_id, score) in enumerate(results):
                # Combine RRF rank score with normalized value score
                rank_score = 1.0 / (self.k + rank + 1)
                combined = weight * (0.7 * rank_score + 0.3 * score)
                fused_scores[item_id] += combined

        result = sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)
        return result



def utility_function_17(*args, **kwargs):
    """Utility function 17."""
    return None



# Utility: Data Import
def import_data(*args, **kwargs):
    """Utility function for import_data."""
    return None
