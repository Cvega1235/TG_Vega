"""Servicio de Machine Learning para el backend."""

import logging
from datetime import datetime, timezone
from typing import Optional

# Categorías que no son clientes potenciales de embutidos
_EXCLUDED_CATEGORIES = [
    "panaderia", "panadería",
    "heladeria", "heladería",
    "chocolateria", "chocolatería",
    "dulceria", "dulcería",
    "fruteria", "frutería",
    "jugos", "smoothie",
    "creperia", "crepería",
    "postres",
]

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from app.restaurants.models import (
    MLRunMetadata,
    Restaurant,
    RestaurantMLScore,
    RestaurantScore,
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
                "tiene_embutidos": r.tiene_embutidos,
            })
        restaurants_df = pd.DataFrame(restaurant_records)

        # Cargar clientes: primero desde la BD, luego fallback al CSV
        if clients_data:
            clients_df = pd.DataFrame(clients_data)
        else:
            db_clients = (
                self.db.query(Restaurant)
                .filter(Restaurant.status == "cliente")
                .all()
            )
            if db_clients:
                logger.info(f"Cargando {len(db_clients)} clientes desde la base de datos")
                clients_df = pd.DataFrame([{
                    "nombre": r.nombre,
                    "rating": float(r.rating) if r.rating is not None else None,
                    "tipo_cocina": r.tipo_cocina,
                    "zona": r.zona,
                    "num_resenas": r.num_resenas,
                    "direccion": r.direccion,
                    "telefono": r.telefono,
                    "precio": r.precio,
                    "latitud": float(r.latitud) if r.latitud is not None else None,
                    "longitud": float(r.longitud) if r.longitud is not None else None,
                    "tiene_embutidos": r.tiene_embutidos,
                } for r in db_clients])
            elif ml_config.ICP_DATA_PATH.exists():
                logger.warning("Sin clientes en BD, usando CSV de fallback")
                clients_df = pd.read_csv(ml_config.ICP_DATA_PATH)
                # El CSV de fallback puede no tener tiene_embutidos;
                # los clientes actuales de Don Piotr se asume que usan el producto
                if "tiene_embutidos" not in clients_df.columns:
                    clients_df["tiene_embutidos"] = True
            else:
                raise ValueError(
                    "No hay clientes en la base de datos ni archivo CSV de respaldo. "
                    "Importe los clientes actuales primero."
                )

        # Identificar posiciones de clientes en el DataFrame para el clasificador
        client_id_set = {r.id for r in self.db.query(Restaurant).filter(Restaurant.status == "cliente").all()}
        client_indices = [i for i, r in enumerate(restaurant_records) if r["id"] in client_id_set]

        # Ejecutar pipeline (sin IDs en el DataFrame de features)
        restaurants_df_ml = restaurants_df.drop(columns=["id"])
        pipeline = MLPipeline(restaurants_df_ml, clients_df, client_indices=client_indices)
        results = pipeline.run()

        # Guardar scores en la DB
        self._save_ml_scores(
            restaurant_ids=[r["id"] for r in restaurant_records],
            labels=results["labels"],
            icp_similarities=results["icp_similarities"],
            composite_scores=results["composite_scores"],
            conversion_probs=results["conversion_probs"],
            cluster_profiles=results["cluster_profiles"],
        )

        # Guardar metadata de la ejecución
        cm = results.get("classification_metrics") or {}
        run_metadata = MLRunMetadata(
            optimal_k=results["optimal_k"],
            silhouette_score=results["validation_metrics"]["silhouette_score"],
            davies_bouldin_index=results["validation_metrics"]["davies_bouldin_index"],
            calinski_harabasz_index=results["validation_metrics"]["calinski_harabasz_index"],
            total_restaurants_scored=len(restaurants),
            icp_clients_count=len(clients_df),
            cls_precision=cm.get("precision"),
            cls_recall=cm.get("recall"),
            cls_f1=cm.get("f1"),
            cls_auc_roc=cm.get("auc_roc"),
            cls_cv_f1_mean=cm.get("cv_f1_mean"),
            cls_cv_f1_std=cm.get("cv_f1_std"),
            cls_support_positive=cm.get("support_positive"),
        )
        self.db.add(run_metadata)
        self.db.commit()
        self.db.refresh(run_metadata)

        # Recalcular scores heurísticos con los pesos actuales guardados en DB
        from app.scoring.engine import calculate_all_scores
        calculate_all_scores(self.db)

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
        conversion_probs: np.ndarray,
        cluster_profiles: dict,
    ) -> None:
        """Guarda los scores ML en la base de datos."""
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
                conversion_probability=round(float(conversion_probs[i]), 4) if conversion_probs[i] > 0 else None,
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

    def get_recommendations(self) -> dict:
        """Genera recomendaciones estratégicas basadas en scores ML y estado actual."""
        from sqlalchemy import func, case

        # 1. Acciones rápidas: ya en contacto, score alto → más cerca de cerrar
        acciones_query = (
            self.db.query(Restaurant, RestaurantMLScore, RestaurantScore)
            .join(RestaurantMLScore, Restaurant.id == RestaurantMLScore.restaurant_id)
            .outerjoin(RestaurantScore, Restaurant.id == RestaurantScore.restaurant_id)
            .filter(Restaurant.status.in_(["contactado", "interesado"]))
        )
        acciones_query = self._exclude_non_prospects(acciones_query)
        acciones_rows = (
            acciones_query
            .order_by(RestaurantScore.total_score.desc().nulls_last())
            .limit(8)
            .all()
        )

        # 2. Top sin contactar: status nuevo con score más alto
        sin_contactar_query = (
            self.db.query(Restaurant, RestaurantMLScore, RestaurantScore)
            .join(RestaurantMLScore, Restaurant.id == RestaurantMLScore.restaurant_id)
            .outerjoin(RestaurantScore, Restaurant.id == RestaurantScore.restaurant_id)
            .filter(Restaurant.status == "nuevo")
        )
        sin_contactar_query = self._exclude_non_prospects(sin_contactar_query)
        sin_contactar_rows = (
            sin_contactar_query
            .order_by(RestaurantScore.total_score.desc().nulls_last())
            .limit(8)
            .all()
        )

        def _prospect_dict(restaurant: Restaurant, score: RestaurantMLScore, heuristic: RestaurantScore | None) -> dict:
            return {
                "id": restaurant.id,
                "nombre": restaurant.nombre,
                "zona": restaurant.zona,
                "status": restaurant.status,
                "tipo_cocina": restaurant.tipo_cocina,
                "rating": float(restaurant.rating) if restaurant.rating else None,
                "composite_score": float(heuristic.total_score) if heuristic else float(score.composite_score),
                "conversion_probability": float(score.conversion_probability) if score.conversion_probability else None,
            }

        # 3. Zonas con más oportunidad: prospectos de calidad (score ≥ 60) por zona
        zona_rows = (
            self.db.query(
                Restaurant.zona,
                func.count(Restaurant.id).label("total"),
                func.avg(RestaurantScore.total_score).label("avg_score"),
            )
            .join(RestaurantMLScore, Restaurant.id == RestaurantMLScore.restaurant_id)
            .outerjoin(RestaurantScore, Restaurant.id == RestaurantScore.restaurant_id)
            .filter(
                Restaurant.status.notin_(["cliente", "no_interesado"]),
                RestaurantScore.total_score >= 60,
                Restaurant.zona.isnot(None),
            )
            .group_by(Restaurant.zona)
            .order_by(func.count(Restaurant.id).desc())
            .limit(5)
            .all()
        )

        # 4. Segmentos más afines: tasa de conversión histórica por tipo de cocina
        cuisine_rows = (
            self.db.query(
                Restaurant.tipo_cocina,
                func.count(Restaurant.id).label("total"),
                func.sum(
                    case((Restaurant.status == "cliente", 1), else_=0)
                ).label("clientes"),
            )
            .filter(Restaurant.tipo_cocina.isnot(None), Restaurant.tipo_cocina != "")
            .group_by(Restaurant.tipo_cocina)
            .having(func.count(Restaurant.id) >= 3)
            .all()
        )

        segmentos = sorted(
            [
                {
                    "tipo_cocina": row.tipo_cocina,
                    "total": row.total,
                    "clientes": int(row.clientes or 0),
                    "conversion_rate": round(int(row.clientes or 0) / row.total, 3),
                }
                for row in cuisine_rows
                if row.total > 0
            ],
            key=lambda x: x["conversion_rate"],
            reverse=True,
        )[:5]

        return {
            "acciones_rapidas": [_prospect_dict(r, s, h) for r, s, h in acciones_rows],
            "top_sin_contactar": [_prospect_dict(r, s, h) for r, s, h in sin_contactar_rows],
            "zonas_oportunidad": [
                {
                    "zona": row.zona,
                    "total_prospectos": row.total,
                    "avg_score": round(float(row.avg_score), 2),
                }
                for row in zona_rows
            ],
            "segmentos_afines": segmentos,
        }

    def get_validation_report(self) -> Optional[dict]:
        """Retorna el reporte de validación de la última ejecución ML."""
        run = (
            self.db.query(MLRunMetadata)
            .order_by(MLRunMetadata.run_at.desc())
            .first()
        )
        if not run:
            return None

        return {
            "run_at": run.run_at,
            "total_restaurants_scored": run.total_restaurants_scored,
            "icp_clients_count": run.icp_clients_count,
            # Clustering
            "silhouette_score": float(run.silhouette_score),
            "davies_bouldin_index": float(run.davies_bouldin_index),
            "calinski_harabasz_index": float(run.calinski_harabasz_index),
            "optimal_k": run.optimal_k,
            # Clasificador supervisado
            "classifier_available": run.cls_f1 is not None,
            "cls_precision": float(run.cls_precision) if run.cls_precision is not None else None,
            "cls_recall": float(run.cls_recall) if run.cls_recall is not None else None,
            "cls_f1": float(run.cls_f1) if run.cls_f1 is not None else None,
            "cls_auc_roc": float(run.cls_auc_roc) if run.cls_auc_roc is not None else None,
            "cls_cv_f1_mean": float(run.cls_cv_f1_mean) if run.cls_cv_f1_mean is not None else None,
            "cls_cv_f1_std": float(run.cls_cv_f1_std) if run.cls_cv_f1_std is not None else None,
            "cls_support_positive": run.cls_support_positive,
        }

    def _exclude_non_prospects(self, query):
        """Filtra categorías sin afinidad con embutidos de cualquier consulta."""
        from sqlalchemy import and_, or_, func
        conditions = []
        for cat in _EXCLUDED_CATEGORIES:
            # Use and_(IS NOT NULL, LIKE) to avoid NULL propagation in OR
            conditions.append(
                and_(Restaurant.categoria.isnot(None), func.lower(Restaurant.categoria).contains(cat))
            )
            conditions.append(
                and_(Restaurant.tipo_cocina.isnot(None), func.lower(Restaurant.tipo_cocina).contains(cat))
            )
            # Also filter by name — catches "Panadería X" where tipo_cocina is something else
            conditions.append(func.lower(Restaurant.nombre).contains(cat))
        return query.filter(~or_(*conditions))

    def get_top_prospects(self, limit: int = 20, include_clients: bool = False) -> list[TopProspectResponse]:
        """Obtiene los top prospectos ordenados por score heurístico (pesos configurables)."""
        query = (
            self.db.query(Restaurant, RestaurantMLScore, RestaurantScore)
            .join(RestaurantMLScore, Restaurant.id == RestaurantMLScore.restaurant_id)
            .outerjoin(RestaurantScore, Restaurant.id == RestaurantScore.restaurant_id)
        )
        if not include_clients:
            query = query.filter(Restaurant.status.notin_(["cliente", "no_interesado"]))
        query = self._exclude_non_prospects(query)
        results = (
            query
            .order_by(RestaurantScore.total_score.desc().nulls_last())
            .limit(limit)
            .all()
        )

        prospects = []
        for restaurant, ml_score, heuristic_score in results:
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
                    total_score=float(heuristic_score.total_score) if heuristic_score else None,
                )
            )

        return prospects
