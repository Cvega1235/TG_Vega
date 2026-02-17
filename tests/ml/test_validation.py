"""Tests para las métricas de validación del clustering."""

import numpy as np
import pytest

from ml_module.validation import ClusterValidator


class TestValidate:
    def test_computes_all_metrics(self, sample_feature_matrix):
        labels = np.array([0] * 15 + [1] * 15 + [2] * 15)
        validator = ClusterValidator(sample_feature_matrix, labels)
        metrics = validator.validate()

        assert "silhouette_score" in metrics
        assert "davies_bouldin_index" in metrics
        assert "calinski_harabasz_index" in metrics

    def test_silhouette_in_range(self, sample_feature_matrix):
        labels = np.array([0] * 15 + [1] * 15 + [2] * 15)
        validator = ClusterValidator(sample_feature_matrix, labels)
        metrics = validator.validate()

        assert -1 <= metrics["silhouette_score"] <= 1

    def test_davies_bouldin_positive(self, sample_feature_matrix):
        labels = np.array([0] * 15 + [1] * 15 + [2] * 15)
        validator = ClusterValidator(sample_feature_matrix, labels)
        metrics = validator.validate()

        assert metrics["davies_bouldin_index"] >= 0

    def test_calinski_harabasz_positive(self, sample_feature_matrix):
        labels = np.array([0] * 15 + [1] * 15 + [2] * 15)
        validator = ClusterValidator(sample_feature_matrix, labels)
        metrics = validator.validate()

        assert metrics["calinski_harabasz_index"] > 0


class TestIsValid:
    def test_passes_with_good_clustering(self, sample_feature_matrix):
        """Con 3 clusters bien separados, Silhouette debe ser alto."""
        labels = np.array([0] * 15 + [1] * 15 + [2] * 15)
        validator = ClusterValidator(sample_feature_matrix, labels)

        # Los datos del fixture tienen 3 clusters claros
        assert validator.is_valid(min_silhouette=0.3)

    def test_fails_with_random_labels(self, sample_feature_matrix):
        """Con labels aleatorios, Silhouette debe ser bajo."""
        np.random.seed(99)
        random_labels = np.random.randint(0, 3, 45)
        validator = ClusterValidator(sample_feature_matrix, random_labels)

        # Random labels no deben pasar un umbral alto
        metrics = validator.validate()
        assert metrics["silhouette_score"] < 0.5
