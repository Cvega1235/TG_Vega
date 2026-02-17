"""Tests para el cálculo del ICP y similitud."""

import numpy as np
import pandas as pd
import pytest

from ml_module.feature_engineering import FeatureEngineer
from ml_module.icp import ICPCalculator


@pytest.fixture
def fitted_engineer(sample_restaurants_df):
    """FeatureEngineer ya ajustado con datos de ejemplo."""
    fe = FeatureEngineer(sample_restaurants_df)
    fe.fit_transform()
    return fe


class TestComputeICP:
    def test_icp_is_centroid(self, sample_clients_df, fitted_engineer):
        icp_calc = ICPCalculator(sample_clients_df, fitted_engineer)
        icp = icp_calc.compute_icp()

        assert isinstance(icp, np.ndarray)
        assert len(icp) > 0

    def test_raises_before_compute(self, sample_clients_df, fitted_engineer):
        icp_calc = ICPCalculator(sample_clients_df, fitted_engineer)

        with pytest.raises(RuntimeError):
            icp_calc.compute_similarity(np.zeros((5, 10)))


class TestComputeSimilarity:
    def test_scores_in_0_100_range(
        self, sample_restaurants_df, sample_clients_df, fitted_engineer,
    ):
        icp_calc = ICPCalculator(sample_clients_df, fitted_engineer)
        icp_calc.compute_icp()

        feature_matrix = fitted_engineer.fit_transform()
        similarities = icp_calc.compute_similarity(feature_matrix.values)

        assert similarities.min() >= 0
        assert similarities.max() <= 100

    def test_max_similarity_is_100(
        self, sample_restaurants_df, sample_clients_df, fitted_engineer,
    ):
        icp_calc = ICPCalculator(sample_clients_df, fitted_engineer)
        icp_calc.compute_icp()

        feature_matrix = fitted_engineer.fit_transform()
        similarities = icp_calc.compute_similarity(feature_matrix.values)

        assert np.isclose(similarities.max(), 100.0)


class TestGetICPProfile:
    def test_returns_dict(self, sample_clients_df, fitted_engineer):
        icp_calc = ICPCalculator(sample_clients_df, fitted_engineer)
        icp_calc.compute_icp()

        feature_names = fitted_engineer.get_feature_names()
        profile = icp_calc.get_icp_profile(feature_names)

        assert isinstance(profile, dict)
        assert len(profile) == len(feature_names)
