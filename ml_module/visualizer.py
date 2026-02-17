"""
visualizer.py
Visualizaciones para resultados de ML (calidad tesis).
Sistema de Inteligencia de Mercado Don Piotr
"""

import logging
from typing import Dict, List, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA

logger = logging.getLogger("ml_module.visualizer")

# Estilo global
plt.style.use("seaborn-v0_8-whitegrid")
COLORS = [
    "#2196F3", "#4CAF50", "#FF9800", "#F44336", "#9C27B0",
    "#00BCD4", "#795548", "#607D8B", "#E91E63", "#3F51B5",
]


class MLVisualizer:
    """Generador de visualizaciones de calidad para tesis.

    Produce gráficos estandarizados con títulos, ejes y leyendas
    listos para inclusión en documentos académicos.
    """

    def __init__(self, output_dir: Optional[str] = None) -> None:
        """Inicializa el visualizador.

        Args:
            output_dir: Directorio para guardar figuras. Si None, solo muestra.
        """
        self.output_dir = output_dir

    def _save_or_show(self, fig: plt.Figure, filename: str) -> plt.Figure:
        """Guarda la figura si hay directorio de salida, si no la muestra."""
        fig.tight_layout()
        if self.output_dir:
            path = f"{self.output_dir}/{filename}"
            fig.savefig(path, dpi=150, bbox_inches="tight")
            logger.info(f"Figura guardada: {path}")
        return fig

    def plot_elbow(
        self,
        k_range: range,
        inertias: List[float],
        optimal_k: int,
    ) -> plt.Figure:
        """Gráfico del método del codo (Elbow).

        Args:
            k_range: Rango de valores de K evaluados.
            inertias: Inercia para cada K.
            optimal_k: K seleccionado como óptimo.

        Returns:
            Figura matplotlib.
        """
        fig, ax = plt.subplots(figsize=(10, 6))
        k_values = list(k_range)

        ax.plot(k_values, inertias, "bo-", linewidth=2, markersize=8)
        ax.axvline(
            x=optimal_k, color="red", linestyle="--", linewidth=2,
            label=f"K optimo = {optimal_k}",
        )
        ax.set_xlabel("Numero de Clusters (K)", fontsize=12)
        ax.set_ylabel("Inercia (WCSS)", fontsize=12)
        ax.set_title("Metodo del Codo - Seleccion de K", fontsize=14)
        ax.legend(fontsize=11)
        ax.set_xticks(k_values)

        return self._save_or_show(fig, "elbow_method.png")

    def plot_silhouette(
        self,
        k_range: range,
        silhouette_scores: List[float],
        optimal_k: int,
    ) -> plt.Figure:
        """Gráfico del coeficiente de Silhouette por K.

        Args:
            k_range: Rango de valores de K.
            silhouette_scores: Score Silhouette para cada K.
            optimal_k: K seleccionado como óptimo.

        Returns:
            Figura matplotlib.
        """
        fig, ax = plt.subplots(figsize=(10, 6))
        k_values = list(k_range)

        ax.plot(
            k_values, silhouette_scores, "go-",
            linewidth=2, markersize=8,
        )
        ax.axvline(
            x=optimal_k, color="red", linestyle="--", linewidth=2,
            label=f"K optimo = {optimal_k}",
        )
        ax.axhline(
            y=0.5, color="orange", linestyle=":", linewidth=1.5,
            label="Umbral minimo (0.5)",
        )
        ax.set_xlabel("Numero de Clusters (K)", fontsize=12)
        ax.set_ylabel("Coeficiente de Silhouette", fontsize=12)
        ax.set_title(
            "Coeficiente de Silhouette - Seleccion de K", fontsize=14,
        )
        ax.legend(fontsize=11)
        ax.set_xticks(k_values)

        return self._save_or_show(fig, "silhouette_scores.png")

    def plot_pca_2d(
        self,
        X: np.ndarray,
        labels: np.ndarray,
        centers: np.ndarray,
        title: str = "Clustering K-means - Proyeccion PCA 2D",
    ) -> plt.Figure:
        """Gráfico de dispersión PCA 2D coloreado por cluster.

        Args:
            X: Matriz de features.
            labels: Etiquetas de cluster.
            centers: Centroides de clusters.
            title: Título del gráfico.

        Returns:
            Figura matplotlib.
        """
        pca = PCA(n_components=2)
        X_pca = pca.fit_transform(X)
        centers_pca = pca.transform(centers)

        fig, ax = plt.subplots(figsize=(12, 8))

        for i in sorted(np.unique(labels)):
            mask = labels == i
            ax.scatter(
                X_pca[mask, 0], X_pca[mask, 1],
                c=COLORS[i % len(COLORS)],
                label=f"Cluster {i} (n={mask.sum()})",
                alpha=0.6, s=40, edgecolors="white", linewidth=0.5,
            )

        # Centroides
        ax.scatter(
            centers_pca[:, 0], centers_pca[:, 1],
            c="black", marker="X", s=200, linewidths=2,
            edgecolors="white", label="Centroides", zorder=5,
        )

        variance = pca.explained_variance_ratio_ * 100
        ax.set_xlabel(
            f"Componente Principal 1 ({variance[0]:.1f}% varianza)",
            fontsize=12,
        )
        ax.set_ylabel(
            f"Componente Principal 2 ({variance[1]:.1f}% varianza)",
            fontsize=12,
        )
        ax.set_title(title, fontsize=14)
        ax.legend(fontsize=10, loc="best")

        return self._save_or_show(fig, "pca_2d_clusters.png")

    def plot_cluster_profiles(
        self, profiles: Dict[int, Dict]
    ) -> plt.Figure:
        """Gráfico de barras comparativo de perfiles de clusters.

        Args:
            profiles: Diccionario de perfiles por cluster.

        Returns:
            Figura matplotlib.
        """
        fig, axes = plt.subplots(1, 3, figsize=(16, 5))

        cluster_ids = sorted(profiles.keys())
        colors = [COLORS[i % len(COLORS)] for i in cluster_ids]

        # Rating promedio
        ratings = [profiles[c].get("avg_rating", 0) or 0 for c in cluster_ids]
        axes[0].bar(
            [str(c) for c in cluster_ids], ratings,
            color=colors, edgecolor="black",
        )
        axes[0].set_title("Rating Promedio por Cluster", fontsize=13)
        axes[0].set_xlabel("Cluster")
        axes[0].set_ylabel("Rating Promedio")
        axes[0].set_ylim(0, 5.5)

        # Tamaño
        sizes = [profiles[c]["size"] for c in cluster_ids]
        axes[1].bar(
            [str(c) for c in cluster_ids], sizes,
            color=colors, edgecolor="black",
        )
        axes[1].set_title("Tamano de Clusters", fontsize=13)
        axes[1].set_xlabel("Cluster")
        axes[1].set_ylabel("Cantidad de Restaurantes")

        # Reseñas promedio
        reviews = [
            profiles[c].get("avg_reviews", 0) or 0 for c in cluster_ids
        ]
        axes[2].bar(
            [str(c) for c in cluster_ids], reviews,
            color=colors, edgecolor="black",
        )
        axes[2].set_title("Resenas Promedio por Cluster", fontsize=13)
        axes[2].set_xlabel("Cluster")
        axes[2].set_ylabel("Resenas Promedio")

        fig.suptitle("Perfiles de Clusters", fontsize=15, y=1.02)
        return self._save_or_show(fig, "cluster_profiles.png")

    def plot_icp_radar(
        self,
        icp_vector: np.ndarray,
        feature_names: List[str],
        max_features: int = 10,
    ) -> plt.Figure:
        """Gráfico radar del perfil ICP.

        Args:
            icp_vector: Vector del ICP.
            feature_names: Nombres de features.
            max_features: Máximo de features a mostrar.

        Returns:
            Figura matplotlib.
        """
        # Seleccionar top features por magnitud
        indices = np.argsort(np.abs(icp_vector))[-max_features:]
        values = icp_vector[indices]
        names = [feature_names[i] for i in indices]

        # Normalizar a [0, 1] para el radar
        v_min, v_max = values.min(), values.max()
        if v_max > v_min:
            values_norm = (values - v_min) / (v_max - v_min)
        else:
            values_norm = np.ones_like(values) * 0.5

        # Radar chart
        angles = np.linspace(0, 2 * np.pi, len(names), endpoint=False)
        values_norm = np.concatenate([values_norm, [values_norm[0]]])
        angles = np.concatenate([angles, [angles[0]]])

        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
        ax.fill(angles, values_norm, alpha=0.25, color="#2196F3")
        ax.plot(angles, values_norm, "o-", linewidth=2, color="#2196F3")
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(names, fontsize=9)
        ax.set_title(
            "Perfil de Cliente Ideal (ICP) - Top Features",
            fontsize=14, pad=20,
        )

        return self._save_or_show(fig, "icp_radar.png")

    def plot_score_distribution(
        self, composite_scores: np.ndarray
    ) -> plt.Figure:
        """Histograma de distribución del score compuesto.

        Args:
            composite_scores: Array de scores compuestos.

        Returns:
            Figura matplotlib.
        """
        fig, ax = plt.subplots(figsize=(10, 6))

        ax.hist(
            composite_scores, bins=25, edgecolor="black",
            alpha=0.7, color="#2196F3",
        )
        ax.axvline(
            np.mean(composite_scores), color="red", linestyle="--",
            linewidth=2,
            label=f"Media: {np.mean(composite_scores):.1f}",
        )
        ax.axvline(
            np.median(composite_scores), color="green", linestyle="-.",
            linewidth=2,
            label=f"Mediana: {np.median(composite_scores):.1f}",
        )
        ax.set_xlabel("Score Compuesto", fontsize=12)
        ax.set_ylabel("Frecuencia", fontsize=12)
        ax.set_title(
            "Distribucion del Score Compuesto de Prospectos", fontsize=14,
        )
        ax.legend(fontsize=11)

        return self._save_or_show(fig, "score_distribution.png")

    def plot_top_prospects(
        self,
        df: pd.DataFrame,
        scores: np.ndarray,
        n: int = 20,
    ) -> plt.Figure:
        """Gráfico de barras horizontales de los top N prospectos.

        Args:
            df: DataFrame original con datos de restaurantes.
            scores: Array de scores compuestos.
            n: Número de top prospectos a mostrar.

        Returns:
            Figura matplotlib.
        """
        df_ranked = df.copy()
        df_ranked["composite_score"] = scores
        top = df_ranked.nlargest(n, "composite_score")

        fig, ax = plt.subplots(figsize=(12, max(6, n * 0.4)))

        colors_bar = [
            "#4CAF50" if s >= 70 else "#FF9800" if s >= 50 else "#F44336"
            for s in top["composite_score"]
        ]

        bars = ax.barh(
            range(len(top)), top["composite_score"].values,
            color=colors_bar, edgecolor="black", alpha=0.8,
        )
        ax.set_yticks(range(len(top)))
        ax.set_yticklabels(top["nombre"].values, fontsize=10)
        ax.invert_yaxis()
        ax.set_xlabel("Score Compuesto", fontsize=12)
        ax.set_title(f"Top {n} Prospectos por Score Compuesto", fontsize=14)
        ax.set_xlim(0, 105)

        # Anotar scores
        for i, (bar, score) in enumerate(
            zip(bars, top["composite_score"].values)
        ):
            ax.text(
                score + 1, i, f"{score:.1f}",
                va="center", fontsize=9,
            )

        return self._save_or_show(fig, "top_prospects.png")
