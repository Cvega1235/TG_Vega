"""
feature_engineering.py
Transformación de datos crudos a matriz de features para ML.
Sistema de Inteligencia de Mercado Don Piotr
"""

import logging
from typing import List, Optional

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from ml_module import config as ml_config

logger = logging.getLogger("ml_module.feature_engineering")


class FeatureEngineer:
    """Transforma datos de restaurantes en una matriz de features lista para ML.

    Pipeline:
        1. Crear features binarios de presencia/ausencia
        2. Imputar valores faltantes (mediana para numéricos, moda para categóricos)
        3. One-hot encoding de variables categóricas
        4. Estandarización z-score de variables numéricas

    Uso:
        fe = FeatureEngineer(df_restaurantes)
        feature_matrix = fe.fit_transform()
        # Para transformar nuevos datos (ej: clientes actuales):
        client_features = fe.transform(df_clientes)
    """

    def __init__(self, df: pd.DataFrame) -> None:
        """Inicializa con el DataFrame de restaurantes.

        Args:
            df: DataFrame con datos de restaurantes (columnas crudas).
        """
        self.df_raw = df.copy()
        self.df_features: Optional[pd.DataFrame] = None
        self.scaler: Optional[StandardScaler] = None
        self._numeric_medians: dict = {}
        self._categorical_modes: dict = {}
        self._onehot_columns: List[str] = []
        self._feature_names: List[str] = []
        self._is_fitted = False

    def fit_transform(self) -> pd.DataFrame:
        """Ajusta el pipeline y transforma los datos de entrenamiento.

        Returns:
            DataFrame con la matriz de features procesada.
        """
        df = self.df_raw.copy()

        df = self._create_binary_features(df)
        df = self._fit_impute(df)
        df = self._fit_one_hot_encode(df)
        df = self._fit_standardize(df)

        self.df_features = df
        self._feature_names = list(df.columns)
        self._is_fitted = True

        logger.info(
            f"Feature engineering completado: {df.shape[1]} features, "
            f"{df.shape[0]} registros"
        )
        return df

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transforma nuevos datos usando los parámetros ya ajustados.

        Args:
            df: DataFrame con datos nuevos (mismas columnas que el original).

        Returns:
            DataFrame transformado con las mismas features.

        Raises:
            RuntimeError: Si no se ha llamado a fit_transform primero.
        """
        if not self._is_fitted:
            raise RuntimeError(
                "Debe llamar fit_transform() antes de transform()"
            )

        result = df.copy()
        result = self._create_binary_features(result)
        result = self._apply_impute(result)
        result = self._apply_one_hot_encode(result)
        result = self._apply_standardize(result)

        return result

    def _create_binary_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Crea features binarios indicando presencia de datos.

        Args:
            df: DataFrame de entrada.

        Returns:
            DataFrame con columnas binarias agregadas.
        """
        df["has_phone"] = df["telefono"].notna().astype(int)
        df["has_address"] = df["direccion"].notna().astype(int)
        df["has_coordinates"] = (
            df["latitud"].notna() & df["longitud"].notna()
        ).astype(int)
        df["has_description"] = df.get(
            "descripcion", pd.Series(dtype="object")
        ).notna().astype(int) if "descripcion" in df.columns else 0
        # 1 si el restaurante usa productos embutidos (detectado por OCR o web),
        # 0 si no usa o si aún no fue analizado (None se trata como 0)
        if "tiene_embutidos" in df.columns:
            df["tiene_embutidos"] = df["tiene_embutidos"].fillna(False).astype(int)

        return df

    def _fit_impute(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcula estadísticas de imputación y aplica.

        Numéricos: mediana. Categóricos: moda o valor por defecto.

        Args:
            df: DataFrame de entrada.

        Returns:
            DataFrame con valores faltantes imputados.
        """
        # Medianas para numéricos
        for col in ml_config.NUMERIC_FEATURES:
            if col in df.columns:
                median = df[col].median()
                self._numeric_medians[col] = median if pd.notna(median) else 0.0
                df[col] = df[col].fillna(self._numeric_medians[col])

        # Modas para categóricos
        defaults = {
            "tipo_cocina": ml_config.DEFAULT_CUISINE,
            "zona": ml_config.DEFAULT_ZONE,
            "precio": ml_config.DEFAULT_PRICE,
        }
        for col in ml_config.CATEGORICAL_FEATURES:
            if col in df.columns:
                mode = df[col].mode()
                self._categorical_modes[col] = (
                    mode.iloc[0] if len(mode) > 0 else defaults.get(col, "Desconocido")
                )
                df[col] = df[col].fillna(self._categorical_modes[col])

        return df

    def _apply_impute(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aplica imputación usando estadísticas previamente calculadas."""
        for col, median in self._numeric_medians.items():
            if col in df.columns:
                df[col] = df[col].fillna(median)

        for col, mode in self._categorical_modes.items():
            if col in df.columns:
                df[col] = df[col].fillna(mode)

        return df

    def _fit_one_hot_encode(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aplica one-hot encoding y guarda las columnas resultantes.

        Args:
            df: DataFrame con variables categóricas.

        Returns:
            DataFrame con variables categóricas codificadas.
        """
        available_cats = [
            c for c in ml_config.CATEGORICAL_FEATURES if c in df.columns
        ]

        if not available_cats:
            return df

        # Para tipo_cocina, tomar solo la primera cocina (principal)
        if "tipo_cocina" in df.columns:
            df["tipo_cocina"] = df["tipo_cocina"].apply(
                lambda x: str(x).split(",")[0].strip() if pd.notna(x) else x
            )

        encoded = pd.get_dummies(df[available_cats], prefix=available_cats)
        self._onehot_columns = list(encoded.columns)

        # Eliminar columnas categóricas originales y agregar encoded
        df = df.drop(columns=available_cats)
        df = pd.concat([df, encoded], axis=1)

        return df

    def _apply_one_hot_encode(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aplica one-hot encoding usando las columnas del fit."""
        available_cats = [
            c for c in ml_config.CATEGORICAL_FEATURES if c in df.columns
        ]

        if not available_cats:
            return df

        if "tipo_cocina" in df.columns:
            df["tipo_cocina"] = df["tipo_cocina"].apply(
                lambda x: str(x).split(",")[0].strip() if pd.notna(x) else x
            )

        encoded = pd.get_dummies(df[available_cats], prefix=available_cats)
        df = df.drop(columns=available_cats)
        df = pd.concat([df, encoded], axis=1)

        # Asegurar que existen todas las columnas del fit
        for col in self._onehot_columns:
            if col not in df.columns:
                df[col] = 0

        # Eliminar columnas que no estaban en el fit
        extra = set(df.columns) - set(self._feature_names)
        # Solo eliminar las que son one-hot extras (no features originales)
        onehot_extra = [c for c in extra if any(
            c.startswith(f"{cat}_") for cat in ml_config.CATEGORICAL_FEATURES
        )]
        if onehot_extra:
            df = df.drop(columns=onehot_extra)

        return df

    def _fit_standardize(self, df: pd.DataFrame) -> pd.DataFrame:
        """Estandariza features numéricos con z-score.

        Args:
            df: DataFrame con features numéricos.

        Returns:
            DataFrame con numéricos estandarizados.
        """
        # Seleccionar solo columnas numéricas relevantes
        # (excluyendo las columnas no-feature como 'nombre', 'fuente', etc.)
        non_feature_cols = [
            "nombre", "fuente", "url", "direccion", "telefono",
            "descripcion", "servicios", "categoria", "scraped_at",
            "data_quality",
        ]
        feature_cols = [c for c in df.columns if c not in non_feature_cols]
        df = df[feature_cols].copy()

        # Estandarizar solo numéricos continuos (no binarios one-hot)
        numeric_to_scale = [
            c for c in ml_config.NUMERIC_FEATURES if c in df.columns
        ]

        if numeric_to_scale:
            self.scaler = StandardScaler()
            df.loc[:, numeric_to_scale] = self.scaler.fit_transform(
                df[numeric_to_scale]
            )

        return df

    def _apply_standardize(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aplica estandarización usando el scaler ya ajustado."""
        non_feature_cols = [
            "nombre", "fuente", "url", "direccion", "telefono",
            "descripcion", "servicios", "categoria", "scraped_at",
            "data_quality",
        ]
        feature_cols = [c for c in df.columns if c not in non_feature_cols]
        df = df[feature_cols].copy()

        numeric_to_scale = [
            c for c in ml_config.NUMERIC_FEATURES if c in df.columns
        ]

        if self.scaler and numeric_to_scale:
            df.loc[:, numeric_to_scale] = self.scaler.transform(
                df[numeric_to_scale]
            )

        return df

    def get_scaler(self) -> Optional[StandardScaler]:
        """Retorna el scaler ajustado."""
        return self.scaler

    def get_feature_names(self) -> List[str]:
        """Retorna los nombres de las features en la matriz final."""
        return self._feature_names
