"""
scoring.py
Score compuesto para ranking de clientes potenciales.
Sistema de Inteligencia de Mercado Don Piotr
"""

import logging

import numpy as np

from ml_module import config as ml_config

logger = logging.getLogger("ml_module.scoring")


class MLScorer:
    """Calcula el score compuesto para cada restaurante.

    Formula: score = 0.6 * similitud_ICP + 0.4 * score_cluster

    Donde:
    - similitud_ICP: Similitud al perfil ideal (0-100)
    - score_cluster: Score del cluster basado en la distancia de su
      centroide al ICP (0-100)

    Uso:
        scorer = MLScorer(icp_similarities, cluster_labels,
                          cluster_centers, icp_vector)
        composite_scores = scorer.compute_composite_scores()
    """

    def __init__(
        self,
        icp_similarities: np.ndarray,
        cluster_labels: np.ndarray,
        cluster_centers: np.ndarray,
        icp_vector: np.ndarray,
    ) -> None:
        """Inicializa el scorer.

        Args:
            icp_similarities: Similitudes al ICP (0-100) por restaurante.
            cluster_labels: Etiquetas de cluster asignadas.
            cluster_centers: Centroides de los clusters.
            icp_vector: Vector del perfil de cliente ideal.
        """
        self.icp_similarities = icp_similarities
        self.cluster_labels = cluster_labels
        self.cluster_centers = cluster_centers
        self.icp_vector = icp_vector

    def compute_cluster_scores(self) -> np.ndarray:
        """Calcula el score de cada cluster basado en su cercanía al ICP.

        Clusters más cercanos al ICP reciben scores más altos.

        Returns:
            Array con score de cluster (0-100) por restaurante.
        """
        # Distancia de cada centroide al ICP
        center_distances = np.linalg.norm(
            self.cluster_centers - self.icp_vector, axis=1
        )

        # Convertir a similitud
        center_similarities = 1.0 / (1.0 + center_distances)

        # Normalizar a 0-100
        max_sim = center_similarities.max()
        if max_sim > 0:
            center_scores = (center_similarities / max_sim) * 100
        else:
            center_scores = np.zeros_like(center_similarities)

        # Mapear score del cluster a cada restaurante
        restaurant_cluster_scores = center_scores[self.cluster_labels]

        logger.info(
            f"Cluster scores calculados: {len(center_scores)} clusters, "
            f"rango=[{restaurant_cluster_scores.min():.1f}, "
            f"{restaurant_cluster_scores.max():.1f}]"
        )
        return restaurant_cluster_scores

    def compute_composite_scores(self) -> np.ndarray:
        """Calcula el score compuesto final para cada restaurante.

        Formula: 0.6 * similitud_ICP + 0.4 * score_cluster

        Returns:
            Array con scores compuestos (0-100) por restaurante.
        """
        cluster_scores = self.compute_cluster_scores()

        composite = (
            ml_config.ICP_SIMILARITY_WEIGHT * self.icp_similarities
            + ml_config.CLUSTER_SCORE_WEIGHT * cluster_scores
        )

        logger.info(
            f"Scores compuestos calculados "
            f"(pesos: ICP={ml_config.ICP_SIMILARITY_WEIGHT}, "
            f"cluster={ml_config.CLUSTER_SCORE_WEIGHT}): "
            f"min={composite.min():.2f}, max={composite.max():.2f}, "
            f"media={composite.mean():.2f}"
        )
        return composite
