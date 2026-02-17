"""
clustering.py
Pipeline de clustering K-means con selección óptima de K.
Sistema de Inteligencia de Mercado Don Piotr
"""

import logging
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

from ml_module import config as ml_config

logger = logging.getLogger("ml_module.clustering")


class ClusteringPipeline:
    """Pipeline de clustering K-means con selección automática de K.

    Evalúa múltiples valores de K usando el método del codo (Elbow)
    y el coeficiente de Silhouette para determinar el K óptimo.

    Uso:
        cp = ClusteringPipeline(feature_matrix)
        optimal_k = cp.find_optimal_k()
        labels = cp.fit(optimal_k)
        profiles = cp.get_cluster_profiles(df_original)
    """

    def __init__(
        self,
        feature_matrix: np.ndarray,
        k_range: range = ml_config.K_RANGE,
    ) -> None:
        """Inicializa el pipeline de clustering.

        Args:
            feature_matrix: Matriz de features (n_samples, n_features).
            k_range: Rango de valores de K a evaluar.
        """
        self.X = feature_matrix
        self.k_range = k_range
        self.optimal_k: Optional[int] = None
        self.model: Optional[KMeans] = None
        self.labels: Optional[np.ndarray] = None
        self.inertias: List[float] = []
        self.silhouette_scores: List[float] = []

    def find_optimal_k(self) -> int:
        """Determina el K óptimo usando Elbow + Silhouette.

        Evalúa cada K en el rango, calcula inercia y Silhouette,
        y selecciona el K con mejor Silhouette.

        Returns:
            K óptimo seleccionado.
        """
        logger.info(
            f"Evaluando K en rango [{self.k_range.start}, "
            f"{self.k_range.stop - 1}]..."
        )

        self.inertias = []
        self.silhouette_scores = []

        for k in self.k_range:
            kmeans = KMeans(
                n_clusters=k,
                random_state=ml_config.RANDOM_STATE,
                n_init=ml_config.N_INIT,
            )
            labels = kmeans.fit_predict(self.X)

            self.inertias.append(kmeans.inertia_)
            sil = silhouette_score(self.X, labels)
            self.silhouette_scores.append(sil)

            logger.info(
                f"  K={k}: Inercia={kmeans.inertia_:.2f}, "
                f"Silhouette={sil:.4f}"
            )

        # Seleccionar K con mejor Silhouette
        best_idx = int(np.argmax(self.silhouette_scores))
        self.optimal_k = list(self.k_range)[best_idx]

        logger.info(
            f"K optimo seleccionado: {self.optimal_k} "
            f"(Silhouette={self.silhouette_scores[best_idx]:.4f})"
        )
        return self.optimal_k

    def fit(self, k: Optional[int] = None) -> np.ndarray:
        """Ajusta K-means con el K dado o el óptimo calculado.

        Args:
            k: Número de clusters. Si None, usa el óptimo.

        Returns:
            Array con las etiquetas de cluster asignadas.

        Raises:
            ValueError: Si no se proporcionó K y no se calculó el óptimo.
        """
        k = k or self.optimal_k
        if k is None:
            raise ValueError(
                "Debe proporcionar K o llamar find_optimal_k() primero"
            )

        logger.info(f"Ajustando K-means con K={k}...")

        self.model = KMeans(
            n_clusters=k,
            random_state=ml_config.RANDOM_STATE,
            n_init=ml_config.N_INIT,
        )
        self.labels = self.model.fit_predict(self.X)

        logger.info(f"Clustering completado: {k} clusters asignados")
        return self.labels

    def get_cluster_centers(self) -> np.ndarray:
        """Retorna los centroides de los clusters.

        Returns:
            Matriz (n_clusters, n_features) con los centroides.

        Raises:
            RuntimeError: Si no se ha ajustado el modelo.
        """
        if self.model is None:
            raise RuntimeError("Debe llamar fit() primero")
        return self.model.cluster_centers_

    def get_cluster_profiles(
        self,
        df: pd.DataFrame,
        feature_names: Optional[List[str]] = None,
    ) -> Dict[int, Dict]:
        """Genera perfiles descriptivos para cada cluster.

        Args:
            df: DataFrame original con datos de restaurantes.
            feature_names: Nombres de features (para estadísticas).

        Returns:
            Diccionario con perfil de cada cluster:
            {cluster_id: {size, avg_rating, avg_reviews, dominant_cuisine,
                          dominant_zone, dominant_price}}
        """
        if self.labels is None:
            raise RuntimeError("Debe llamar fit() primero")

        df_clustered = df.copy()
        df_clustered["cluster"] = self.labels

        profiles: Dict[int, Dict] = {}

        for cluster_id in sorted(df_clustered["cluster"].unique()):
            cluster_df = df_clustered[df_clustered["cluster"] == cluster_id]

            profile: Dict = {
                "size": len(cluster_df),
                "avg_rating": None,
                "avg_reviews": None,
                "dominant_cuisine": None,
                "dominant_zone": None,
                "dominant_price": None,
            }

            if "rating" in cluster_df.columns:
                avg_rating = cluster_df["rating"].mean()
                profile["avg_rating"] = (
                    round(float(avg_rating), 2)
                    if pd.notna(avg_rating)
                    else None
                )

            if "num_resenas" in cluster_df.columns:
                avg_reviews = cluster_df["num_resenas"].mean()
                profile["avg_reviews"] = (
                    round(float(avg_reviews), 1)
                    if pd.notna(avg_reviews)
                    else None
                )

            if "tipo_cocina" in cluster_df.columns:
                mode = cluster_df["tipo_cocina"].mode()
                profile["dominant_cuisine"] = (
                    mode.iloc[0] if len(mode) > 0 else None
                )

            if "zona" in cluster_df.columns:
                mode = cluster_df["zona"].mode()
                profile["dominant_zone"] = (
                    mode.iloc[0] if len(mode) > 0 else None
                )

            if "precio" in cluster_df.columns:
                mode = cluster_df["precio"].mode()
                profile["dominant_price"] = (
                    mode.iloc[0] if len(mode) > 0 else None
                )

            profiles[cluster_id] = profile
            logger.info(
                f"Cluster {cluster_id}: {profile['size']} restaurantes, "
                f"rating_avg={profile['avg_rating']}, "
                f"cocina={profile['dominant_cuisine']}"
            )

        return profiles
