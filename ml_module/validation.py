"""
validation.py
Métricas de validación para clustering K-means.
Sistema de Inteligencia de Mercado Don Piotr
"""

import logging
from typing import Dict

import numpy as np
from sklearn.metrics import (
    calinski_harabasz_score,
    davies_bouldin_score,
    silhouette_score,
)

from ml_module import config as ml_config

logger = logging.getLogger("ml_module.validation")


class ClusterValidator:
    """Calcula y evalúa métricas de validación del clustering.

    Métricas:
    - Coeficiente de Silhouette: Mide qué tan bien separados están los clusters.
      Rango [-1, 1], mayor es mejor. Umbral mínimo: 0.5
    - Índice de Davies-Bouldin: Mide la similitud entre clusters.
      Menor es mejor.
    - Índice de Calinski-Harabasz: Ratio de dispersión entre/dentro clusters.
      Mayor es mejor.

    Uso:
        validator = ClusterValidator(feature_matrix, labels)
        metrics = validator.validate()
        is_ok = validator.is_valid()
    """

    def __init__(self, X: np.ndarray, labels: np.ndarray) -> None:
        """Inicializa el validador.

        Args:
            X: Matriz de features (n_samples, n_features).
            labels: Etiquetas de cluster asignadas.
        """
        self.X = X
        self.labels = labels

    def validate(self) -> Dict[str, float]:
        """Calcula todas las métricas de validación.

        Returns:
            Diccionario con las tres métricas.
        """
        metrics = {
            "silhouette_score": float(
                silhouette_score(self.X, self.labels)
            ),
            "davies_bouldin_index": float(
                davies_bouldin_score(self.X, self.labels)
            ),
            "calinski_harabasz_index": float(
                calinski_harabasz_score(self.X, self.labels)
            ),
        }

        logger.info("Metricas de validacion del clustering:")
        logger.info(
            f"  Silhouette Score: {metrics['silhouette_score']:.4f} "
            f"(umbral: >= {ml_config.MIN_SILHOUETTE})"
        )
        logger.info(
            f"  Davies-Bouldin Index: {metrics['davies_bouldin_index']:.4f} "
            f"(menor es mejor)"
        )
        logger.info(
            f"  Calinski-Harabasz Index: "
            f"{metrics['calinski_harabasz_index']:.2f} "
            f"(mayor es mejor)"
        )

        return metrics

    def is_valid(
        self, min_silhouette: float = ml_config.MIN_SILHOUETTE
    ) -> bool:
        """Verifica si el clustering cumple el umbral de calidad.

        Args:
            min_silhouette: Coeficiente de Silhouette mínimo aceptable.

        Returns:
            True si el Silhouette >= umbral.
        """
        metrics = self.validate()
        valid = metrics["silhouette_score"] >= min_silhouette

        if valid:
            logger.info(
                f"Clustering VALIDO: Silhouette "
                f"{metrics['silhouette_score']:.4f} >= {min_silhouette}"
            )
        else:
            logger.warning(
                f"Clustering NO cumple umbral: Silhouette "
                f"{metrics['silhouette_score']:.4f} < {min_silhouette}"
            )

        return valid
