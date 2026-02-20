"""
enrich_from_tripadvisor.py
Enriquece restaurantes existentes en la DB con datos de TripAdvisor API
y agrega los restaurantes nuevos que no existan.
"""

import os
import sys
from difflib import SequenceMatcher
from pathlib import Path

# Agregar el proyecto al path
project_root = Path(__file__).resolve().parent.parent
backend_dir = project_root / "sis_TG" / "backend"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(backend_dir))

# Cargar .env del backend antes de importar los modelos
from dotenv import load_dotenv
load_dotenv(backend_dir / ".env")

from app.users.models import User  # noqa: F401 - registra el modelo
from app.database import SessionLocal
from app.restaurants.models import Restaurant
from scraping_don_piotr.tripadvisor_api import TripAdvisorAPIScraper
from scraping_don_piotr.logger import logger


def similarity(a: str, b: str) -> float:
    """Calcula similitud entre dos strings (0-1)."""
    a = a.lower().strip()
    b = b.lower().strip()
    return SequenceMatcher(None, a, b).ratio()


def find_match(name: str, db_restaurants: list[Restaurant], threshold: float = 0.75) -> Restaurant | None:
    """Busca un restaurante en la DB que coincida por nombre."""
    best_match = None
    best_score = 0.0

    for r in db_restaurants:
        score = similarity(name, r.nombre)
        if score > best_score and score >= threshold:
            best_score = score
            best_match = r

    return best_match


def main():
    api_key = os.environ.get("TRIPADVISOR_API_KEY", "")
    if not api_key:
        # Intentar leer del .env del backend
        env_path = project_root / "sis_TG" / "backend" / ".env"
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if line.startswith("TRIPADVISOR_API_KEY="):
                    api_key = line.split("=", 1)[1].strip()
                    break

    if not api_key:
        logger.error("No se encontro TRIPADVISOR_API_KEY")
        return

    # 1. Obtener datos de TripAdvisor API
    logger.info("Obteniendo datos de TripAdvisor API...")
    scraper = TripAdvisorAPIScraper(api_key=api_key)
    trip_results = scraper.scrape()
    logger.info(f"Obtenidos {len(trip_results)} restaurantes de TripAdvisor ({scraper.api_calls} llamadas API)")

    # 2. Conectar a la DB
    db = SessionLocal()
    try:
        all_db_restaurants = db.query(Restaurant).all()
        logger.info(f"Restaurantes en DB: {len(all_db_restaurants)}")

        enriched = 0
        added = 0
        skipped = 0

        for trip_r in trip_results:
            # Buscar coincidencia en DB (incluye los recién agregados)
            match = find_match(trip_r.nombre, all_db_restaurants)

            if match:
                # Enriquecer el registro existente
                updated = False
                if (not match.tipo_cocina or match.tipo_cocina == "") and trip_r.tipo_cocina:
                    match.tipo_cocina = trip_r.tipo_cocina
                    updated = True
                if (not match.precio or match.precio == "") and trip_r.precio:
                    match.precio = trip_r.precio
                    updated = True
                if (not match.rating or match.rating == 0) and trip_r.rating:
                    match.rating = trip_r.rating
                    updated = True
                if not match.descripcion and trip_r.descripcion:
                    match.descripcion = trip_r.descripcion
                    updated = True
                if not match.servicios and trip_r.servicios:
                    match.servicios = trip_r.servicios
                    updated = True
                if trip_r.url and (not match.url or "tripadvisor" not in (match.url or "")):
                    match.url = trip_r.url
                    updated = True

                if updated:
                    enriched += 1
                    logger.info(f"  Enriquecido: {match.nombre} <- {trip_r.tipo_cocina}, {trip_r.precio}")
                else:
                    skipped += 1
            else:
                # Agregar como nuevo restaurante
                new_restaurant = Restaurant(
                    fuente="TripAdvisor",
                    url=trip_r.url,
                    nombre=trip_r.nombre,
                    direccion=trip_r.direccion,
                    telefono=trip_r.telefono,
                    rating=trip_r.rating,
                    num_resenas=trip_r.num_resenas,
                    latitud=trip_r.latitud,
                    longitud=trip_r.longitud,
                    precio=trip_r.precio,
                    tipo_cocina=trip_r.tipo_cocina,
                    categoria=trip_r.categoria,
                    descripcion=trip_r.descripcion,
                    servicios=trip_r.servicios,
                    zona=trip_r.zona,
                    status="nuevo",
                )
                db.add(new_restaurant)
                # Agregar a la lista para evitar duplicados en esta misma ejecución
                all_db_restaurants.append(new_restaurant)
                added += 1
                logger.info(f"  Nuevo: {trip_r.nombre} ({trip_r.tipo_cocina})")

        db.commit()

        logger.info("=" * 50)
        logger.info("RESUMEN DE ENRIQUECIMIENTO")
        logger.info(f"  Restaurantes enriquecidos: {enriched}")
        logger.info(f"  Restaurantes nuevos agregados: {added}")
        logger.info(f"  Sin cambios (ya completos): {skipped}")
        logger.info(f"  Llamadas API usadas: {scraper.api_calls}")
        logger.info("=" * 50)

    finally:
        db.close()


if __name__ == "__main__":
    main()
