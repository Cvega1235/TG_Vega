"""Tests para el scoring compuesto ML."""

import numpy as np
import pytest

from ml_module.scoring import MLScorer


@pytest.fixture
def scorer_inputs():
    """Inputs pre-calculados para el MLScorer."""
    np.random.seed(42)
    n = 30
    return {
        "icp_similarities": np.random.uniform(0, 100, n),
        "cluster_labels": np.array([0] * 10 + [1] * 10 + [2] * 10),
        "cluster_centers": np.random.randn(3, 5),
        "icp_vector": np.random.randn(5),
    }


class TestComputeClusterScores:
    def test_returns_array_of_correct_length(self, scorer_inputs):
        scorer = MLScorer(**scorer_inputs)
        cluster_scores = scorer.compute_cluster_scores()

        assert len(cluster_scores) == 30

    def test_scores_in_valid_range(self, scorer_inputs):
        scorer = MLScorer(**scorer_inputs)
        cluster_scores = scorer.compute_cluster_scores()

        assert cluster_scores.min() >= 0
        assert cluster_scores.max() <= 100

    def test_same_cluster_same_score(self, scorer_inputs):
        scorer = MLScorer(**scorer_inputs)
        cluster_scores = scorer.compute_cluster_scores()

        # Todos los del cluster 0 deben tener el mismo cluster_score
        cluster_0_scores = cluster_scores[:10]
        assert np.all(cluster_0_scores == cluster_0_scores[0])


class TestCompositeScores:
    def test_composite_range(self, scorer_inputs):
        scorer = MLScorer(**scorer_inputs)
        composite = scorer.compute_composite_scores()

        assert composite.min() >= 0
        assert composite.max() <= 100

    def test_composite_length(self, scorer_inputs):
        scorer = MLScorer(**scorer_inputs)
        composite = scorer.compute_composite_scores()

        assert len(composite) == 30

    def test_weights_applied_correctly(self, scorer_inputs):
        scorer = MLScorer(**scorer_inputs)
        composite = scorer.compute_composite_scores()
        cluster_scores = scorer.compute_cluster_scores()

        # Verificar fórmula: 0.6 * ICP + 0.4 * cluster
        expected = (
            0.6 * scorer_inputs["icp_similarities"]
            + 0.4 * cluster_scores
        )
        np.testing.assert_array_almost_equal(composite, expected)
