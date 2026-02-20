"""
run_ml_report.py
Ejecuta el pipeline ML y genera un reporte detallado de clusters,
incluyendo la asignación de los clientes actuales a cada cluster.
"""

import sys
from pathlib import Path
from collections import Counter

import numpy as np
import pandas as pd

project_root = Path(__file__).resolve().parent.parent
backend_dir = project_root / "sis_TG" / "backend"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(backend_dir))

from dotenv import load_dotenv
load_dotenv(backend_dir / ".env")

from app.users.models import User  # noqa: F401
from app.database import SessionLocal
from app.restaurants.models import Restaurant

from ml_module.pipeline import MLPipeline
from ml_module import config as ml_config
from scraping_don_piotr.logger import logger


def main():
    db = SessionLocal()
    try:
        # 1. Cargar restaurantes de la DB
        restaurants = db.query(Restaurant).all()
        logger.info(f"Restaurantes en DB: {len(restaurants)}")

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

        # 2. Cargar clientes actuales
        clients_df = pd.read_csv(ml_config.ICP_DATA_PATH)
        logger.info(f"Clientes actuales: {len(clients_df)}")

        # 3. Ejecutar pipeline
        restaurants_df_ml = restaurants_df.drop(columns=["id"])
        output_dir = str(ml_config.OUTPUT_DIR)
        pipeline = MLPipeline(restaurants_df_ml, clients_df, output_dir=output_dir)
        results = pipeline.run()

        # Exportar resultados
        pipeline.export_results(str(ml_config.OUTPUT_DIR / "ml_results.json"))

        # 4. Asignar clientes a clusters
        from ml_module.feature_engineering import FeatureEngineer
        fe = FeatureEngineer(restaurants_df_ml)
        fe.fit_transform()

        # Transformar clientes con el mismo pipeline de features
        client_features = fe.transform(clients_df)
        client_X = client_features.values.astype(np.float64)

        # Asignar cada cliente al cluster más cercano
        cluster_centers = results["icp_vector"]  # No, necesitamos los centroides
        from ml_module.clustering import ClusteringPipeline
        # Reconstruir el modelo para predecir
        cp = ClusteringPipeline(results["ranked_restaurants"].drop(
            columns=["cluster_id", "icp_similarity", "cluster_score",
                     "composite_score", "rank"], errors="ignore"
        ).select_dtypes(include=[np.number]).values)

        # Usar el modelo del pipeline para predecir clusters de clientes
        # Necesitamos recrear el KMeans con los mismos centroides
        from sklearn.cluster import KMeans
        kmeans = KMeans(
            n_clusters=results["optimal_k"],
            random_state=ml_config.RANDOM_STATE,
            n_init=ml_config.N_INIT,
        )
        # Fit on same data then predict clients
        X_restaurants = fe.fit_transform().values.astype(np.float64)
        kmeans.fit(X_restaurants)
        client_labels = kmeans.predict(client_X)

        # 5. REPORTE DETALLADO
        ranked_df = results["ranked_restaurants"]
        labels = results["labels"]
        optimal_k = results["optimal_k"]

        print("\n" + "=" * 70)
        print("REPORTE DETALLADO DE CLUSTERS")
        print("=" * 70)
        print(f"Total restaurantes: {len(restaurants_df)}")
        print(f"K optimo: {optimal_k}")
        print(f"Silhouette Score: {results['validation_metrics']['silhouette_score']:.4f}")
        print(f"Davies-Bouldin Index: {results['validation_metrics']['davies_bouldin_index']:.4f}")
        print(f"Calinski-Harabasz Index: {results['validation_metrics']['calinski_harabasz_index']:.2f}")
        print()

        for cluster_id in range(optimal_k):
            mask = labels == cluster_id
            cluster_data = restaurants_df_ml[mask]
            cluster_scores = results["composite_scores"][mask]

            print(f"\n{'-' * 70}")
            print(f"CLUSTER {cluster_id}")
            print(f"{'-' * 70}")
            print(f"  Tamaño: {len(cluster_data)} restaurantes")

            # Rating
            ratings = cluster_data["rating"].dropna()
            if len(ratings) > 0:
                print(f"  Rating promedio: {ratings.mean():.2f} (min={ratings.min():.1f}, max={ratings.max():.1f})")
            else:
                print(f"  Rating promedio: N/A")

            # Num reseñas
            reviews = cluster_data["num_resenas"].dropna()
            if len(reviews) > 0:
                print(f"  Reseñas promedio: {reviews.mean():.0f}")

            # Score compuesto
            print(f"  Score compuesto promedio: {cluster_scores.mean():.2f}")

            # Zona dominante (top 3)
            zonas = cluster_data["zona"].dropna()
            if len(zonas) > 0:
                zona_counts = Counter(zonas)
                top_zonas = zona_counts.most_common(3)
                zonas_str = ", ".join(f"{z} ({c})" for z, c in top_zonas)
                print(f"  Zonas principales: {zonas_str}")

            # Tipo cocina (top 5)
            cocinas = cluster_data["tipo_cocina"].dropna()
            if len(cocinas) > 0:
                # Tomar primera cocina de cada registro
                cocinas_principales = cocinas.apply(lambda x: str(x).split(",")[0].strip())
                cocina_counts = Counter(cocinas_principales)
                top_cocinas = cocina_counts.most_common(5)
                cocinas_str = ", ".join(f"{c} ({n})" for c, n in top_cocinas)
                print(f"  Cocinas principales: {cocinas_str}")

            # Precio
            precios = cluster_data["precio"].dropna()
            if len(precios) > 0:
                precio_counts = Counter(precios)
                top_precios = precio_counts.most_common(3)
                precios_str = ", ".join(f"{p} ({n})" for p, n in top_precios)
                print(f"  Rangos de precio: {precios_str}")

            # Fuente
            fuentes = cluster_data["fuente"]
            fuente_counts = Counter(fuentes)
            fuentes_str = ", ".join(f"{f} ({n})" for f, n in fuente_counts.most_common())
            print(f"  Fuentes: {fuentes_str}")

            # Completitud
            total = len(cluster_data)
            has_phone = cluster_data["telefono"].notna().sum()
            has_coords = (cluster_data["latitud"].notna() & cluster_data["longitud"].notna()).sum()
            has_cuisine = cluster_data["tipo_cocina"].notna().sum()
            has_price = cluster_data["precio"].notna().sum()
            print(f"  Completitud: telefono={has_phone}/{total}, "
                  f"coordenadas={has_coords}/{total}, "
                  f"cocina={has_cuisine}/{total}, "
                  f"precio={has_price}/{total}")

            # Clientes en este cluster
            client_in_cluster = (client_labels == cluster_id).sum()
            print(f"  Clientes actuales en este cluster: {client_in_cluster}/{len(clients_df)}")

            # Listar nombres de clientes en este cluster
            client_mask = client_labels == cluster_id
            client_names = clients_df.loc[client_mask, "nombre"].tolist()
            if client_names:
                for name in client_names[:10]:
                    print(f"    - {name}")
                if len(client_names) > 10:
                    print(f"    ... y {len(client_names) - 10} mas")

        # 6. Resumen de distribución de clientes
        print(f"\n{'=' * 70}")
        print("DISTRIBUCION DE CLIENTES POR CLUSTER")
        print(f"{'=' * 70}")
        for cluster_id in range(optimal_k):
            count = (client_labels == cluster_id).sum()
            pct = (count / len(clients_df)) * 100
            print(f"  Cluster {cluster_id}: {count} clientes ({pct:.1f}%)")

        print(f"\nTotal clientes: {len(clients_df)}")
        print("=" * 70)

    finally:
        db.close()


if __name__ == "__main__":
    main()
