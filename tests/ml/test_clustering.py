"""Tests para el pipeline de clustering K-means."""

import numpy as np
import pytest

from ml_module.clustering import ClusteringPipeline


class TestFindOptimalK:
    def test_returns_valid_k(self, sample_feature_matrix):
        cp = ClusteringPipeline(sample_feature_matrix, k_range=range(2, 6))
        k = cp.find_optimal_k()

        assert isinstance(k, int)
        assert 2 <= k <= 5

    def test_stores_inertias(self, sample_feature_matrix):
        cp = ClusteringPipeline(sample_feature_matrix, k_range=range(2, 6))
        cp.find_optimal_k()

        assert len(cp.inertias) == 4  # k=2,3,4,5
        # Inercia debe decrecer con más clusters
        for i in range(1, len(cp.inertias)):
            assert cp.inertias[i] <= cp.inertias[i - 1]

    def test_stores_silhouette_scores(self, sample_feature_matrix):
        cp = ClusteringPipeline(sample_feature_matrix, k_range=range(2, 6))
        cp.find_optimal_k()

        assert len(cp.silhouette_scores) == 4
        for score in cp.silhouette_scores:
            assert -1 <= score <= 1


class TestFit:
    def test_produces_correct_number_of_clusters(self, sample_feature_matrix):
        cp = ClusteringPipeline(sample_feature_matrix)
        labels = cp.fit(k=3)

        assert len(np.unique(labels)) == 3

    def test_all_samples_assigned(self, sample_feature_matrix):
        cp = ClusteringPipeline(sample_feature_matrix)
        labels = cp.fit(k=3)

        assert len(labels) == len(sample_feature_matrix)

    def test_raises_without_k(self, sample_feature_matrix):
        cp = ClusteringPipeline(sample_feature_matrix)
        with pytest.raises(ValueError):
            cp.fit()


class TestClusterCenters:
    def test_shape_matches_k(self, sample_feature_matrix):
        cp = ClusteringPipeline(sample_feature_matrix)
        cp.fit(k=3)
        centers = cp.get_cluster_centers()

        assert centers.shape == (3, sample_feature_matrix.shape[1])

    def test_raises_before_fit(self, sample_feature_matrix):
        cp = ClusteringPipeline(sample_feature_matrix)
        with pytest.raises(RuntimeError):
            cp.get_cluster_centers()
