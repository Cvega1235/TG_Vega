"""Tests para el pipeline de Feature Engineering."""

import numpy as np
import pandas as pd
import pytest

from ml_module.feature_engineering import FeatureEngineer


class TestBinaryFeatures:
    def test_creates_binary_columns(self, sample_restaurants_df):
        fe = FeatureEngineer(sample_restaurants_df)
        features = fe.fit_transform()

        assert "has_phone" in features.columns
        assert "has_address" in features.columns
        assert "has_coordinates" in features.columns

    def test_binary_values_are_0_or_1(self, sample_restaurants_df):
        fe = FeatureEngineer(sample_restaurants_df)
        features = fe.fit_transform()

        for col in ["has_phone", "has_address", "has_coordinates"]:
            if col in features.columns:
                assert set(features[col].unique()).issubset({0, 1})


class TestImputation:
    def test_no_nulls_in_numeric_features(self, sample_restaurants_df):
        fe = FeatureEngineer(sample_restaurants_df)
        features = fe.fit_transform()

        numeric_cols = [c for c in ["rating", "num_resenas", "latitud", "longitud"]
                        if c in features.columns]
        for col in numeric_cols:
            assert features[col].isna().sum() == 0


class TestOneHotEncoding:
    def test_removes_original_categorical_columns(self, sample_restaurants_df):
        fe = FeatureEngineer(sample_restaurants_df)
        features = fe.fit_transform()

        assert "tipo_cocina" not in features.columns
        assert "zona" not in features.columns
        assert "precio" not in features.columns

    def test_creates_encoded_columns(self, sample_restaurants_df):
        fe = FeatureEngineer(sample_restaurants_df)
        features = fe.fit_transform()

        # Debe haber columnas con prefijo de las categorías
        onehot_cols = [c for c in features.columns
                       if c.startswith("tipo_cocina_") or
                       c.startswith("zona_") or
                       c.startswith("precio_")]
        assert len(onehot_cols) > 0


class TestStandardization:
    def test_numeric_features_standardized(self, sample_restaurants_df):
        fe = FeatureEngineer(sample_restaurants_df)
        features = fe.fit_transform()

        for col in ["rating", "num_resenas"]:
            if col in features.columns:
                mean = features[col].mean()
                std = features[col].std()
                # Media cercana a 0, std cercana a 1
                assert abs(mean) < 0.5
                assert abs(std - 1.0) < 0.5 or len(features) < 5


class TestTransform:
    def test_transform_after_fit(self, sample_restaurants_df, sample_clients_df):
        fe = FeatureEngineer(sample_restaurants_df)
        fe.fit_transform()

        # Transformar clientes con el mismo pipeline
        client_features = fe.transform(sample_clients_df)
        assert client_features is not None
        assert len(client_features) == len(sample_clients_df)

    def test_raises_without_fit(self, sample_restaurants_df):
        fe = FeatureEngineer(sample_restaurants_df)

        with pytest.raises(RuntimeError):
            fe.transform(sample_restaurants_df)


class TestFeatureNames:
    def test_returns_list(self, sample_restaurants_df):
        fe = FeatureEngineer(sample_restaurants_df)
        fe.fit_transform()

        names = fe.get_feature_names()
        assert isinstance(names, list)
        assert len(names) > 0

    def test_names_match_columns(self, sample_restaurants_df):
        fe = FeatureEngineer(sample_restaurants_df)
        features = fe.fit_transform()

        assert fe.get_feature_names() == list(features.columns)
