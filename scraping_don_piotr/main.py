"""
main.py
Orquestador principal del sistema de web scraping.
Sistema de Inteligencia de Mercado Don Piotr
"""

import argparse
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from scraping_don_piotr import config
from scraping_don_piotr.base_scraper import RestaurantData
from scraping_don_piotr.bolivia_scraper import BoliviaEnTusManosScraper
from scraping_don_piotr.gmaps_scraper import GoogleMapsScraper
from scraping_don_piotr.logger import logger
from scraping_don_piotr.tripadvisor_scraper import TripAdvisorScraper
from scraping_don_piotr.tripadvisor_api import TripAdvisorAPIScraper


def log_statistics(results: List[Dict[str, Any]]) -> None:
    """Registra estadísticas resumen de los datos extraídos.

    Args:
        results: Lista de diccionarios con datos de restaurantes.
    """
    if not results:
        return

    df = pd.DataFrame(results)
    total = len(df)

    logger.info("-" * 50)
    logger.info("ESTADISTICAS DE EXTRACCION")
    logger.info("-" * 50)

    # Registros por fuente
    source_counts = df["fuente"].value_counts()
    for fuente, count in source_counts.items():
        logger.info(f"  {fuente}: {count} registros")

    # Completitud de campos
    logger.info("Completitud de campos:")
    key_fields = [
        "nombre", "direccion", "telefono", "rating",
        "num_resenas", "latitud", "longitud", "precio",
        "tipo_cocina", "zona",
    ]
    for field in key_fields:
        if field in df.columns:
            non_null = df[field].notna().sum()
            pct = (non_null / total) * 100
            logger.info(f"  {field}: {non_null}/{total} ({pct:.1f}%)")

    # Rating promedio
    if "rating" in df.columns:
        avg_rating = df["rating"].mean()
        if pd.notna(avg_rating):
            logger.info(f"Rating promedio: {avg_rating:.2f}")

    logger.info("-" * 50)


def export_results(
    results: List[Dict[str, Any]], output_dir: Path
) -> None:
    """Exporta los resultados a CSV, JSON y SQLite.

    Args:
        results: Lista de diccionarios con datos de restaurantes.
        output_dir: Directorio de salida para los archivos.
    """
    if not results:
        logger.warning("No hay resultados para exportar")
        return

    output_dir.mkdir(parents=True, exist_ok=True)

    # Exportar a CSV
    if config.EXPORT_CSV:
        csv_path = output_dir / "restaurantes_la_paz.csv"
        try:
            df = pd.DataFrame(results)
            df.to_csv(csv_path, index=False, encoding="utf-8")
            logger.info(f"Exportado CSV: {csv_path}")
        except Exception as e:
            logger.error(f"Error exportando CSV: {e}")

    # Exportar a JSON
    if config.EXPORT_JSON:
        json_path = output_dir / "restaurantes_la_paz.json"
        try:
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            logger.info(f"Exportado JSON: {json_path}")
        except Exception as e:
            logger.error(f"Error exportando JSON: {e}")

    # Exportar a SQLite
    if config.EXPORT_SQLITE:
        db_path = output_dir / "don_piotr.db"
        try:
            conn = sqlite3.connect(db_path)
            df = pd.DataFrame(results)
            df.to_sql("restaurantes", conn, if_exists="replace", index=False)
            conn.close()
            logger.info(f"Exportado SQLite: {db_path}")
        except Exception as e:
            logger.error(f"Error exportando SQLite: {e}")


def main() -> List[Dict[str, Any]]:
    """Punto de entrada principal del sistema de scraping.

    Returns:
        Lista de diccionarios con los datos extraídos.
    """
    parser = argparse.ArgumentParser(
        description="Sistema de Web Scraping - Don Piotr"
    )
    parser.add_argument(
        "--source",
        choices=["gmaps", "tripadvisor", "tripadvisor_api", "bolivia", "all"],
        default="all",
        help="Fuente de datos a extraer (default: all)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limite de registros por fuente",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Directorio de salida (default: output/)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Ejecutar sin guardar resultados",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Ejecutar Chrome en modo headless",
    )

    args = parser.parse_args()

    output_dir = Path(args.output_dir) if args.output_dir else config.OUTPUT_DIR

    logger.info("=" * 60)
    logger.info("INICIO DEL SISTEMA DE WEB SCRAPING DON PIOTR")
    logger.info("=" * 60)
    logger.info(f"Fuente: {args.source}")
    logger.info(f"Limite: {args.limit if args.limit else 'Sin limite'}")
    logger.info(f"Directorio de salida: {output_dir}")
    logger.info(f"Modo dry-run: {args.dry_run}")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")

    all_results: List[RestaurantData] = []

    # Google Maps
    if args.source in ["gmaps", "all"]:
        logger.info("Iniciando scraping de Google Maps...")
        gmaps = GoogleMapsScraper(headless=args.headless)
        gmaps_data = gmaps.scrape(limit=args.limit)
        all_results.extend(gmaps_data)
        logger.info(f"Google Maps: {len(gmaps_data)} registros")

    # TripAdvisor (solo si se pide explícitamente, bloqueado por DataDome CAPTCHA)
    if args.source == "tripadvisor":
        logger.info("Iniciando scraping de TripAdvisor...")
        logger.warning(
            "TripAdvisor usa DataDome CAPTCHA. "
            "Puede fallar si detecta automatización."
        )
        trip = TripAdvisorScraper(headless=args.headless)
        trip_data = trip.scrape(limit=args.limit)
        all_results.extend(trip_data)
        logger.info(f"TripAdvisor: {len(trip_data)} registros")

    # TripAdvisor API (incluido en "all")
    if args.source in ["tripadvisor_api", "all"]:
        logger.info("Iniciando scraping de TripAdvisor (API oficial)...")
        try:
            trip_api = TripAdvisorAPIScraper()
            trip_api_data = trip_api.scrape(limit=args.limit)
            all_results.extend(trip_api_data)
            logger.info(f"TripAdvisor API: {len(trip_api_data)} registros ({trip_api.api_calls} llamadas API)")
        except ValueError as e:
            logger.warning(f"TripAdvisor API no disponible: {e}")

    # Bolivia en tus Manos
    if args.source in ["bolivia", "all"]:
        logger.info("Iniciando scraping de Bolivia en tus Manos...")
        bolivia = BoliviaEnTusManosScraper()
        bolivia_data = bolivia.scrape(limit=args.limit)
        all_results.extend(bolivia_data)
        logger.info(f"Bolivia en tus Manos: {len(bolivia_data)} registros")

    # Convertir a diccionarios para exportación
    results_dicts = [r.to_dict() for r in all_results]

    logger.info("=" * 60)
    logger.info(f"SCRAPING COMPLETADO: {len(results_dicts)} registros totales")
    logger.info("=" * 60)

    # Estadísticas
    log_statistics(results_dicts)

    # Exportar resultados
    if results_dicts and not args.dry_run:
        export_results(results_dicts, output_dir)
    elif args.dry_run:
        logger.info("Modo dry-run: resultados no guardados")

    return results_dicts


if __name__ == "__main__":
    main()
