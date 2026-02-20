"""
fix_ratings.py
Corrige ratings de Google Maps que fueron parseados sin decimal (4,3 → 43 en vez de 4.3).
Solo afecta registros con fuente='Google Maps' y rating > 5.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
backend_dir = project_root / "sis_TG" / "backend"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(backend_dir))

from dotenv import load_dotenv
load_dotenv(backend_dir / ".env")

from app.users.models import User  # noqa: F401
from app.database import SessionLocal
from app.restaurants.models import Restaurant
from scraping_don_piotr.logger import logger


def main():
    db = SessionLocal()
    try:
        # Buscar restaurantes de Google Maps con ratings > 5 (incorrectos)
        bad_ratings = db.query(Restaurant).filter(
            Restaurant.fuente == "Google Maps",
            Restaurant.rating > 5.0
        ).all()

        logger.info(f"Encontrados {len(bad_ratings)} restaurantes con rating incorrecto")

        fixed = 0
        for r in bad_ratings:
            old_rating = r.rating
            r.rating = round(old_rating / 10.0, 1)
            logger.info(f"  {r.nombre}: {old_rating} -> {r.rating}")
            fixed += 1

        # También corregir Bolivia en tus Manos si aplica
        bad_bolivia = db.query(Restaurant).filter(
            Restaurant.fuente == "Bolivia en tus Manos",
            Restaurant.rating > 5.0
        ).all()
        for r in bad_bolivia:
            old_rating = r.rating
            r.rating = round(old_rating / 10.0, 1)
            logger.info(f"  {r.nombre}: {old_rating} -> {r.rating}")
            fixed += 1

        db.commit()
        logger.info(f"Corregidos {fixed} ratings en total")

        # Estadísticas post-corrección
        all_with_rating = db.query(Restaurant).filter(
            Restaurant.rating.isnot(None)
        ).all()
        ratings = [r.rating for r in all_with_rating]
        if ratings:
            logger.info(f"Ratings post-corrección: min={min(ratings)}, max={max(ratings)}, "
                        f"promedio={sum(ratings)/len(ratings):.2f}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
