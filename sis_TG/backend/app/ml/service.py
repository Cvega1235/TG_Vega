"""Servicio de Machine Learning para el backend."""

import logging
from datetime import datetime, timezone
from typing import Optional

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from app.restaurants.models import (
    MLRunMetadata,
    Restaurant,
    RestaurantMLScore,
)
from app.ml.schemas import (
    ClusterProfileResponse,
    MLRunResponse,
    MLRunResultResponse,
    TopProspectResponse,
)

logger = logging.getLogger("app.ml.service")


class MLService:
    """Servicio para ejecutar y consultar resultados del pipeline ML."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def run_pipeline(
        self, clients_data: Optional[list[dict]] = None
    ) -> MLRunResultResponse:
        """Ejecuta el pipeline completo de ML.

        Args:
            clients_data: Datos de clientes actuales. Si None,
                          se cargan desde archivo de configuración.

        Returns:
            MLRunResultResponse con metadata y perfiles de clusters.
        """
        # Importar módulo ML (ruta relativa al proyecto)
        import sys
        from pathlib import Path

        project_root = Path(__file__).resolve().parent.parent.parent.parent.parent
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))

        from ml_module.pipeline import MLPipeline
        from ml_module import config as ml_config

        # Obtener todos los restaurantes de la DB
        restaurants = self.db.query(Restaurant).all()
        if not restaurants:
            raise ValueError("No hay restaurantes en la base de datos")

        # Construir DataFrame de restaurantes
        restaurant_records = []
        for r in restaurants:
            restaurant_records.append({
                "id": r.id,
                "nombre": r.nombre,
                "fuente": r.fuente,
                "direccion": r.direccion,
                "telefono": r.telefono,
                "rating": float(r.rating) if r.rating is not None else None,
                "num_resenas": r.num_resenas,
                "latitud": float(r.latitud) if r.latitud is not None else None,
                "longitud": float(r.longitud) if r.longitud is not None else None,
                "precio": r.precio,
                "tipo_cocina": r.tipo_cocina,
                "zona": r.zona,
                "descripcion": r.descripcion,
            })
        restaurants_df = pd.DataFrame(restaurant_records)

        # Cargar o usar datos de clientes
        if clients_data:
            clients_df = pd.DataFrame(clients_data)
        elif ml_config.ICP_DATA_PATH.exists():
            clients_df = pd.read_csv(ml_config.ICP_DATA_PATH)
        else:
            raise ValueError(
                f"No se encontraron datos de clientes actuales en "
                f"{ml_config.ICP_DATA_PATH}. "
                f"Proporcione los datos o cree el archivo CSV."
            )

        # Ejecutar pipeline (sin IDs en el DataFrame de features)
        restaurants_df_ml = restaurants_df.drop(columns=["id"])
        pipeline = MLPipeline(restaurants_df_ml, clients_df)
        results = pipeline.run()

        # Guardar scores en la DB
        self._save_ml_scores(
            restaurant_ids=[r["id"] for r in restaurant_records],
            labels=results["labels"],
            icp_similarities=results["icp_similarities"],
            composite_scores=results["composite_scores"],
            cluster_profiles=results["cluster_profiles"],
        )

        # Guardar metadata de la ejecución
        run_metadata = MLRunMetadata(
            optimal_k=results["optimal_k"],
            silhouette_score=results["validation_metrics"]["silhouette_score"],
            davies_bouldin_index=results["validation_metrics"]["davies_bouldin_index"],
            calinski_harabasz_index=results["validation_metrics"]["calinski_harabasz_index"],
            total_restaurants_scored=len(restaurants),
            icp_clients_count=len(clients_df),
        )
        self.db.add(run_metadata)
        self.db.commit()
        self.db.refresh(run_metadata)

        # Construir respuesta
        cluster_profiles = []
        for cluster_id, profile in results["cluster_profiles"].items():
            # Calcular score compuesto promedio del cluster
            mask = results["labels"] == cluster_id
            avg_score = float(np.mean(results["composite_scores"][mask]))

            cluster_profiles.append(
                ClusterProfileResponse(
                    cluster_id=cluster_id,
                    label=f"Cluster {cluster_id}",
                    size=profile["size"],
                    avg_rating=profile.get("avg_rating"),
                    avg_reviews=profile.get("avg_reviews"),
                    dominant_cuisine=profile.get("dominant_cuisine"),
                    dominant_zone=profile.get("dominant_zone"),
                    dominant_price=profile.get("dominant_price"),
                    avg_composite_score=round(avg_score, 2),
                )
            )

        return MLRunResultResponse(
            run_metadata=MLRunResponse.model_validate(run_metadata),
            cluster_profiles=cluster_profiles,
            message=f"Pipeline completado: {len(restaurants)} restaurantes, "
                    f"K={results['optimal_k']}, "
                    f"Silhouette={results['validation_metrics']['silhouette_score']:.4f}",
        )

    def _save_ml_scores(
        self,
        restaurant_ids: list[int],
        labels: np.ndarray,
        icp_similarities: np.ndarray,
        composite_scores: np.ndarray,
        cluster_profiles: dict,
    ) -> None:
        """Guarda los scores ML en la base de datos."""
        # Calcular cluster_scores
        from ml_module.scoring import MLScorer

        # Eliminar scores anteriores
        self.db.query(RestaurantMLScore).delete()

        for i, restaurant_id in enumerate(restaurant_ids):
            ml_score = RestaurantMLScore(
                restaurant_id=restaurant_id,
                cluster_id=int(labels[i]),
                cluster_label=f"Cluster {labels[i]}",
                icp_similarity=round(float(icp_similarities[i]), 2),
                cluster_score=round(
                    float(composite_scores[i] - 0.6 * icp_similarities[i]) / 0.4, 2
                ),
                composite_score=round(float(composite_scores[i]), 2),
            )
            self.db.add(ml_score)

        self.db.flush()
        logger.info(f"Guardados {len(restaurant_ids)} scores ML en la DB")

    def get_latest_run(self) -> Optional[MLRunResponse]:
        """Obtiene la metadata de la última ejecución ML."""
        run = (
            self.db.query(MLRunMetadata)
            .order_by(MLRunMetadata.run_at.desc())
            .first()
        )
        if run:
            return MLRunResponse.model_validate(run)
        return None

    def get_cluster_profiles(self) -> list[ClusterProfileResponse]:
        """Obtiene perfiles de clusters desde los scores almacenados."""
        from sqlalchemy import func

        scores = self.db.query(RestaurantMLScore).all()
        if not scores:
            return []

        # Agrupar por cluster
        clusters: dict[int, list] = {}
        for score in scores:
            cid = score.cluster_id
            if cid not in clusters:
                clusters[cid] = []
            clusters[cid].append(score)

        profiles = []
        for cluster_id, cluster_scores in sorted(clusters.items()):
            restaurant_ids = [s.restaurant_id for s in cluster_scores]
            restaurants = (
                self.db.query(Restaurant)
                .filter(Restaurant.id.in_(restaurant_ids))
                .all()
            )

            ratings = [float(r.rating) for r in restaurants if r.rating is not None]
            reviews = [r.num_resenas for r in restaurants if r.num_resenas is not None]
            cuisines = [r.tipo_cocina for r in restaurants if r.tipo_cocina]
            zones = [r.zona for r in restaurants if r.zona]
            prices = [r.precio for r in restaurants if r.precio]

            avg_composite = np.mean([float(s.composite_score) for s in cluster_scores])

            profiles.append(
                ClusterProfileResponse(
                    cluster_id=cluster_id,
                    label=f"Cluster {cluster_id}",
                    size=len(cluster_scores),
                    avg_rating=round(np.mean(ratings), 2) if ratings else None,
                    avg_reviews=round(np.mean(reviews), 1) if reviews else None,
                    dominant_cuisine=max(set(cuisines), key=cuisines.count) if cuisines else None,
                    dominant_zone=max(set(zones), key=zones.count) if zones else None,
                    dominant_price=max(set(prices), key=prices.count) if prices else None,
                    avg_composite_score=round(float(avg_composite), 2),
                )
            )

        return profiles

    def get_top_prospects(self, limit: int = 20) -> list[TopProspectResponse]:
        """Obtiene los top prospectos por score compuesto."""
        results = (
            self.db.query(Restaurant, RestaurantMLScore)
            .join(
                RestaurantMLScore,
                Restaurant.id == RestaurantMLScore.restaurant_id,
            )
            .order_by(RestaurantMLScore.composite_score.desc())
            .limit(limit)
            .all()
        )

        prospects = []
        for restaurant, ml_score in results:
            prospects.append(
                TopProspectResponse(
                    id=restaurant.id,
                    nombre=restaurant.nombre,
                    fuente=restaurant.fuente,
                    zona=restaurant.zona,
                    rating=float(restaurant.rating) if restaurant.rating else None,
                    tipo_cocina=restaurant.tipo_cocina,
                    precio=restaurant.precio,
                    cluster_id=ml_score.cluster_id,
                    icp_similarity=float(ml_score.icp_similarity),
                    composite_score=float(ml_score.composite_score),
                )
            )

        return prospects
