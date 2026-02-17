"""
icp.py
Cálculo del Perfil de Cliente Ideal (ICP) y similitud.
Sistema de Inteligencia de Mercado Don Piotr
"""

import logging
from typing import Optional

import numpy as np
import pandas as pd

from ml_module.feature_engineering import FeatureEngineer

logger = logging.getLogger("ml_module.icp")


class ICPCalculator:
    """Calcula el Perfil de Cliente Ideal (ICP) a partir de los clientes actuales.

    El ICP es el centroide (vector promedio) de los 31 clientes actuales
    en el espacio de features. La similitud de cada restaurante potencial
    se calcula como la inversa de la distancia euclidiana al ICP.

    Uso:
        icp_calc = ICPCalculator(df_clientes, feature_engineer)
        icp_vector = icp_calc.compute_icp()
        similarities = icp_calc.compute_similarity(feature_matrix)
    """

    def __init__(
        self,
        clients_df: pd.DataFrame,
        feature_engineer: FeatureEngineer,
    ) -> None:
        """Inicializa el calculador de ICP.

        Args:
            clients_df: DataFrame con datos de los clientes actuales.
            feature_engineer: FeatureEngineer ya ajustado (fitted).
        """
        self.clients_df = clients_df
        self.feature_engineer = feature_engineer
        self.icp_vector: Optional[np.ndarray] = None

    def compute_icp(self) -> np.ndarray:
        """Calcula el ICP como centroide de los clientes actuales.

        Transforma los datos de clientes usando el mismo pipeline
        de feature engineering y calcula el vector promedio.

        Returns:
            Vector ICP (1D array con n_features dimensiones).
        """
        logger.info(
            f"Calculando ICP desde {len(self.clients_df)} clientes actuales..."
        )

        client_features = self.feature_engineer.transform(self.clients_df)
        self.icp_vector = client_features.mean(axis=0).values.astype(np.float64)

        logger.info(f"ICP calculado: vector de {len(self.icp_vector)} dimensiones")
        return self.icp_vector

    def compute_similarity(
        self, feature_matrix: np.ndarray
    ) -> np.ndarray:
        """Calcula la similitud de cada restaurante al ICP.

        Usa distancia euclidiana convertida a similitud:
            similitud = 1 / (1 + distancia)
        Normalizada a escala 0-100.

        Args:
            feature_matrix: Matriz de features (n_samples, n_features).

        Returns:
            Array de similitudes normalizadas (0-100).

        Raises:
            RuntimeError: Si no se ha calculado el ICP.
        """
        if self.icp_vector is None:
            raise RuntimeError("Debe llamar compute_icp() primero")

        # Distancia euclidiana de cada restaurante al ICP
        distances = np.linalg.norm(
            feature_matrix - self.icp_vector, axis=1
        )

        # Convertir distancia a similitud (0-1)
        similarities = 1.0 / (1.0 + distances)

        # Normalizar a escala 0-100
        max_sim = similarities.max()
        if max_sim > 0:
            normalized = (similarities / max_sim) * 100
        else:
            normalized = np.zeros_like(similarities)

        logger.info(
            f"Similitudes calculadas: "
            f"min={normalized.min():.2f}, "
            f"max={normalized.max():.2f}, "
            f"media={normalized.mean():.2f}"
        )
        return normalized

    def get_icp_profile(
        self, feature_names: list
    ) -> dict:
        """Retorna el perfil ICP como diccionario con nombres de features.

        Args:
            feature_names: Lista de nombres de features.

        Returns:
            Diccionario {feature_name: value}.

        Raises:
            RuntimeError: Si no se ha calculado el ICP.
        """
        if self.icp_vector is None:
            raise RuntimeError("Debe llamar compute_icp() primero")

        return dict(zip(feature_names, self.icp_vector))
