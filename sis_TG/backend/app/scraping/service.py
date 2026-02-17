"""Servicio para ejecutar scrapers desde el backend."""

import logging
import sys
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from app.restaurants.models import Restaurant, ScrapingImport
from app.scoring.engine import calculate_all_scores
from app.migration_tool.migrate_sqlite import (
    clean_address, clean_phone, parse_coords_from_url, detect_zone,
)
from datetime import datetime, timezone

logger = logging.getLogger("app.scraping.service")

# Agregar el directorio raíz del proyecto al path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class ScrapingService:
    """Ejecuta scrapers y guarda resultados en la DB."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def run_scraper(
        self, source: str = "all", headless: bool = True, limit: Optional[int] = None
    ) -> dict:
        """Ejecuta el scraper especificado e importa resultados a la DB.

        Args:
            source: "bolivia", "gmaps", o "all" (bolivia + gmaps)
            headless: Ejecutar Chrome sin ventana
            limit: Límite de restaurantes por fuente

        Returns:
            dict con estadísticas de la ejecución
        """
        from scraping_don_piotr.bolivia_scraper import BoliviaEnTusManosScraper
        from scraping_don_piotr.gmaps_scraper import GoogleMapsScraper

        all_results = []

        # Google Maps
        if source in ("gmaps", "all"):
            logger.info("Iniciando scraper de Google Maps...")
            try:
                gmaps = GoogleMapsScraper(headless=headless)
                gmaps_data = gmaps.scrape(limit=limit)
                all_results.extend(gmaps_data)
                logger.info(f"Google Maps: {len(gmaps_data)} restaurantes")
            except Exception as e:
                logger.error(f"Error en Google Maps scraper: {e}")

        # Bolivia en tus Manos
        if source in ("bolivia", "all"):
            logger.info("Iniciando scraper de Bolivia en tus Manos...")
            try:
                bolivia = BoliviaEnTusManosScraper()
                bolivia_data = bolivia.scrape(limit=limit)
                all_results.extend(bolivia_data)
                logger.info(f"Bolivia en tus Manos: {len(bolivia_data)} restaurantes")
            except Exception as e:
                logger.error(f"Error en Bolivia scraper: {e}")

        if not all_results:
            return {
                "source": source,
                "total_scraped": 0,
                "imported": 0,
                "skipped": 0,
                "message": "No se encontraron restaurantes",
            }

        # Importar a la DB
        records = [r.to_dict() for r in all_results]
        imported, skipped = self._import_to_db(records, source)

        return {
            "source": source,
            "total_scraped": len(records),
            "imported": imported,
            "skipped": skipped,
            "message": (
                f"Scraping completado: {len(records)} encontrados, "
                f"{imported} importados, {skipped} omitidos (duplicados)"
            ),
        }

    def _import_to_db(self, records: list[dict], source_info: str) -> tuple[int, int]:
        """Importa registros de scraping a la base de datos."""
        imported = 0
        skipped = 0

        for record in records:
            nombre = (record.get("nombre") or "").strip()
            fuente = (record.get("fuente") or "").strip()

            if not nombre:
                skipped += 1
                continue

            existing = self.db.query(Restaurant).filter(
                Restaurant.nombre == nombre, Restaurant.fuente == fuente
            ).first()
            if existing:
                skipped += 1
                continue

            direccion = clean_address(record.get("direccion"))
            telefono = clean_phone(record.get("telefono"))

            lat, lon = None, None
            if record.get("latitud"):
                try:
                    lat = float(record["latitud"])
                except (ValueError, TypeError):
                    pass
            if record.get("longitud"):
                try:
                    lon = float(record["longitud"])
                except (ValueError, TypeError):
                    pass

            if lat is None or lon is None:
                lat, lon = parse_coords_from_url(record.get("url"))

            rating = None
            if record.get("rating") is not None:
                try:
                    rating = float(record["rating"])
                    if rating < 0 or rating > 5:
                        rating = None
                except (ValueError, TypeError):
                    pass

            num_resenas = None
            if record.get("num_resenas") is not None:
                try:
                    num_resenas = int(record["num_resenas"])
                except (ValueError, TypeError):
                    pass

            restaurant = Restaurant(
                fuente=fuente,
                url=record.get("url"),
                nombre=nombre,
                direccion=direccion,
                telefono=telefono,
                rating=rating,
                num_resenas=num_resenas,
                latitud=lat,
                longitud=lon,
                precio=record.get("precio"),
                tipo_cocina=record.get("tipo_cocina"),
                categoria=record.get("categoria"),
                descripcion=record.get("descripcion"),
                servicios=record.get("servicios"),
                zona=detect_zone(direccion) or record.get("zona"),
                status="nuevo",
                scraped_at=datetime.now(timezone.utc),
            )
            self.db.add(restaurant)
            imported += 1

        self.db.commit()

        log = ScrapingImport(
            source_file=f"scraper_{source_info}",
            source_type="scraper",
            records_total=len(records),
            records_imported=imported,
            records_skipped=skipped,
        )
        self.db.add(log)
        self.db.commit()

        if imported > 0:
            calculate_all_scores(self.db)

        logger.info(f"Importados {imported} restaurantes, {skipped} omitidos")
        return imported, skipped
