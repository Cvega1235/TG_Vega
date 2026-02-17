"""
pipeline.py
Orquestador del pipeline completo de Machine Learning.
Sistema de Inteligencia de Mercado Don Piotr
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from ml_module import config as ml_config
from ml_module.clustering import ClusteringPipeline
from ml_module.feature_engineering import FeatureEngineer
from ml_module.icp import ICPCalculator
from ml_module.scoring import MLScorer
from ml_module.validation import ClusterValidator
from ml_module.visualizer import MLVisualizer

logger = logging.getLogger("ml_module.pipeline")


class MLPipeline:
    """Orquestador end-to-end del pipeline de Machine Learning.

    Ejecuta secuencialmente:
        1. Feature Engineering
        2. Clustering K-means (con selección óptima de K)
        3. Cálculo del ICP (Perfil de Cliente Ideal)
        4. Scoring compuesto
        5. Validación con métricas
        6. Generación de visualizaciones

    Uso:
        pipeline = MLPipeline(df_restaurantes, df_clientes)
        results = pipeline.run()
        pipeline.export_results("output/ml_results.json")
    """

    def __init__(
        self,
        restaurants_df: pd.DataFrame,
        clients_df: pd.DataFrame,
        output_dir: Optional[str] = None,
    ) -> None:
        """Inicializa el pipeline.

        Args:
            restaurants_df: DataFrame con datos de restaurantes potenciales.
            clients_df: DataFrame con datos de los 31 clientes actuales.
            output_dir: Directorio para figuras y resultados.
        """
        self.restaurants_df = restaurants_df
        self.clients_df = clients_df
        self.output_dir = output_dir
        self.results: Optional[Dict[str, Any]] = None

    def run(self) -> Dict[str, Any]:
        """Ejecuta el pipeline completo de ML.

        Returns:
            Diccionario con todos los resultados:
            - labels: Etiquetas de cluster
            - composite_scores: Scores compuestos
            - icp_similarities: Similitudes al ICP
            - cluster_profiles: Perfiles de cada cluster
            - validation_metrics: Métricas de validación
            - optimal_k: K seleccionado
            - icp_vector: Vector ICP
            - feature_names: Nombres de features
            - ranked_restaurants: DataFrame rankeado
        """
        logger.info("=" * 60)
        logger.info("INICIO DEL PIPELINE DE MACHINE LEARNING")
        logger.info("=" * 60)
        logger.info(
            f"Restaurantes: {len(self.restaurants_df)}, "
            f"Clientes actuales: {len(self.clients_df)}"
        )

        # 1. Feature Engineering
        logger.info("PASO 1: Feature Engineering")
        fe = FeatureEngineer(self.restaurants_df)
        feature_matrix = fe.fit_transform()
        feature_names = fe.get_feature_names()
        X = feature_matrix.values.astype(np.float64)

        logger.info(
            f"Matriz de features: {X.shape[0]} registros x "
            f"{X.shape[1]} features"
        )

        # 2. Clustering
        logger.info("PASO 2: Clustering K-means")
        cp = ClusteringPipeline(X)
        optimal_k = cp.find_optimal_k()
        labels = cp.fit(optimal_k)

        # 3. ICP
        logger.info("PASO 3: Calculo del ICP")
        icp_calc = ICPCalculator(self.clients_df, fe)
        icp_vector = icp_calc.compute_icp()
        icp_similarities = icp_calc.compute_similarity(X)

        # 4. Scoring
        logger.info("PASO 4: Scoring compuesto")
        scorer = MLScorer(
            icp_similarities, labels,
            cp.get_cluster_centers(), icp_vector,
        )
        composite_scores = scorer.compute_composite_scores()

        # 5. Validación
        logger.info("PASO 5: Validacion del clustering")
        validator = ClusterValidator(X, labels)
        metrics = validator.validate()
        is_valid = validator.is_valid()

        # 6. Perfiles de clusters
        cluster_profiles = cp.get_cluster_profiles(self.restaurants_df)

        # 7. Construir ranking
        ranked_df = self.restaurants_df.copy()
        ranked_df["cluster_id"] = labels
        ranked_df["icp_similarity"] = np.round(icp_similarities, 2)
        ranked_df["cluster_score"] = np.round(
            scorer.compute_cluster_scores(), 2
        )
        ranked_df["composite_score"] = np.round(composite_scores, 2)
        ranked_df = ranked_df.sort_values(
            "composite_score", ascending=False
        ).reset_index(drop=True)
        ranked_df["rank"] = range(1, len(ranked_df) + 1)

        # 8. Visualizaciones
        if self.output_dir:
            logger.info("PASO 6: Generando visualizaciones")
            self._generate_visualizations(
                cp, X, labels, icp_vector, feature_names,
                composite_scores, cluster_profiles, ranked_df,
            )

        # Empaquetar resultados
        self.results = {
            "labels": labels,
            "composite_scores": composite_scores,
            "icp_similarities": icp_similarities,
            "cluster_profiles": cluster_profiles,
            "validation_metrics": metrics,
            "is_valid": is_valid,
            "optimal_k": optimal_k,
            "icp_vector": icp_vector,
            "feature_names": feature_names,
            "ranked_restaurants": ranked_df,
        }

        logger.info("=" * 60)
        logger.info("PIPELINE COMPLETADO")
        logger.info(f"K optimo: {optimal_k}")
        logger.info(
            f"Silhouette: {metrics['silhouette_score']:.4f} "
            f"({'VALIDO' if is_valid else 'NO VALIDO'})"
        )
        logger.info(
            f"Top 5 prospectos: "
            f"{list(ranked_df['nombre'].head(5))}"
        )
        logger.info("=" * 60)

        return self.results

    def _generate_visualizations(
        self,
        cp: ClusteringPipeline,
        X: np.ndarray,
        labels: np.ndarray,
        icp_vector: np.ndarray,
        feature_names: list,
        composite_scores: np.ndarray,
        cluster_profiles: Dict,
        ranked_df: pd.DataFrame,
    ) -> None:
        """Genera todas las visualizaciones del pipeline."""
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        viz = MLVisualizer(output_dir=self.output_dir)

        viz.plot_elbow(cp.k_range, cp.inertias, cp.optimal_k)
        viz.plot_silhouette(
            cp.k_range, cp.silhouette_scores, cp.optimal_k
        )
        viz.plot_pca_2d(X, labels, cp.get_cluster_centers())
        viz.plot_cluster_profiles(cluster_profiles)
        viz.plot_icp_radar(icp_vector, feature_names)
        viz.plot_score_distribution(composite_scores)
        viz.plot_top_prospects(ranked_df, composite_scores)

        plt.close("all")

    def export_results(self, output_path: str) -> None:
        """Exporta resultados a JSON y CSV.

        Args:
            output_path: Ruta base para los archivos de salida.

        Raises:
            RuntimeError: Si no se ha ejecutado el pipeline.
        """
        if self.results is None:
            raise RuntimeError("Debe llamar run() primero")

        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        # Exportar ranking a CSV
        csv_path = output.with_suffix(".csv")
        self.results["ranked_restaurants"].to_csv(
            csv_path, index=False, encoding="utf-8"
        )
        logger.info(f"Ranking exportado a CSV: {csv_path}")

        # Exportar métricas y metadata a JSON
        json_path = output.with_suffix(".json")
        metadata = {
            "optimal_k": self.results["optimal_k"],
            "validation_metrics": self.results["validation_metrics"],
            "is_valid": self.results["is_valid"],
            "total_restaurants": len(self.results["ranked_restaurants"]),
            "cluster_profiles": {
                str(k): v for k, v in self.results["cluster_profiles"].items()
            },
        }
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        logger.info(f"Metadata exportada a JSON: {json_path}")
