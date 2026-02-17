"""
Script para ejecutar el pipeline de ML de Don Piotr.
"""
import logging
import sys
from pathlib import Path

import pandas as pd

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

from ml_module.config import ICP_DATA_PATH, OUTPUT_DIR
from ml_module.pipeline import MLPipeline

RESTAURANTS_CSV = Path("scraping_don_piotr/output/restaurantes_la_paz.csv")

def main():
    # Cargar datos
    print(f"Cargando restaurantes desde: {RESTAURANTS_CSV}")
    df_restaurants = pd.read_csv(RESTAURANTS_CSV)
    print(f"  -> {len(df_restaurants)} restaurantes cargados")

    print(f"Cargando clientes desde: {ICP_DATA_PATH}")
    df_clients = pd.read_csv(ICP_DATA_PATH)
    print(f"  -> {len(df_clients)} clientes cargados")

    # Crear directorio de salida
    output_dir = str(OUTPUT_DIR)
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Ejecutar pipeline
    pipeline = MLPipeline(df_restaurants, df_clients, output_dir=output_dir)
    results = pipeline.run()

    # Exportar resultados
    export_path = str(OUTPUT_DIR / "ml_results")
    pipeline.export_results(export_path)

    # Resumen
    ranked = results["ranked_restaurants"]
    print("\n" + "=" * 60)
    print("TOP 10 PROSPECTOS PARA DON PIOTR")
    print("=" * 60)
    top10 = ranked.head(10)[["rank", "nombre", "zona", "composite_score", "icp_similarity", "cluster_id"]]
    print(top10.to_string(index=False))
    print(f"\nResultados exportados en: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
