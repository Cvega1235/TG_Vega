"""
Script para migrar datos del SQLite del scraping a PostgreSQL.
Uso: python -m app.migration_tool.migrate_sqlite
"""
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from app.database import SessionLocal, engine, Base
from app.restaurants.models import Restaurant, ScrapingImport
from app.scoring.engine import calculate_all_scores
from app.users.models import User
from app.auth.security import hash_password
from app.config import settings

SQLITE_PATH = Path(__file__).resolve().parent.parent.parent.parent / "scraping_don_piotr" / "output" / "don_piotr.db"

ZONAS_LA_PAZ = [
    "San Miguel", "Calacoto", "Sopocachi", "Miraflores",
    "Zona Sur", "Centro", "Obrajes", "Achumani", "Irpavi", "Cota Cota",
]

COORD_PATTERN = re.compile(r"!3d(-?[\d.]+)!4d(-?[\d.]+)")


def clean_address(address: str | None) -> str | None:
    if not address:
        return None
    address = re.sub(r"^Direcci[oó]n:\s*", "", address.strip())
    return address.strip() if address.strip() else None


def clean_phone(phone: str | None) -> str | None:
    if not phone:
        return None
    phone = re.sub(r"^Tel[eé]fono:\s*", "", phone.strip())
    digits = re.sub(r"\D", "", phone)
    return digits if len(digits) >= 7 else None


def parse_coords_from_url(url: str | None) -> tuple[float | None, float | None]:
    if not url:
        return None, None
    match = COORD_PATTERN.search(url)
    if match:
        lat = float(match.group(1))
        lon = float(match.group(2))
        if -17.5 <= lat <= -15.5 and -69.5 <= lon <= -67.5:
            return lat, lon
    return None, None


def detect_zone(address: str | None) -> str | None:
    if not address:
        return None
    addr_lower = address.lower()
    for zona in ZONAS_LA_PAZ:
        if zona.lower() in addr_lower:
            return zona
    return None


def run_migration():
    if not SQLITE_PATH.exists():
        print(f"ERROR: No se encontro el archivo SQLite en {SQLITE_PATH}")
        return

    # Create all tables
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()

    try:
        # Seed superadmin if not exists
        existing_admin = db.query(User).filter(User.email == settings.SUPERADMIN_EMAIL).first()
        if not existing_admin:
            admin = User(
                email=settings.SUPERADMIN_EMAIL,
                hashed_password=hash_password(settings.SUPERADMIN_PASSWORD),
                full_name="Super Administrador",
                role="superadmin",
            )
            db.add(admin)
            db.commit()
            print(f"SuperAdmin creado: {settings.SUPERADMIN_EMAIL}")

        # Read SQLite data
        conn = sqlite3.connect(str(SQLITE_PATH))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM restaurantes")
        rows = cursor.fetchall()
        conn.close()

        print(f"Registros encontrados en SQLite: {len(rows)}")

        imported = 0
        skipped = 0

        for row in rows:
            row_dict = dict(row)
            nombre = row_dict.get("nombre", "").strip()
            fuente = row_dict.get("fuente", "").strip()

            if not nombre:
                skipped += 1
                continue

            # Check for duplicates
            existing = db.query(Restaurant).filter(
                Restaurant.nombre == nombre, Restaurant.fuente == fuente
            ).first()
            if existing:
                skipped += 1
                continue

            direccion = clean_address(row_dict.get("direccion"))
            telefono = clean_phone(row_dict.get("telefono"))

            # Try to get coordinates
            lat = None
            lon = None
            raw_lat = row_dict.get("latitud")
            raw_lon = row_dict.get("longitud")

            if raw_lat and raw_lon:
                try:
                    lat = float(raw_lat)
                    lon = float(raw_lon)
                except (ValueError, TypeError):
                    lat, lon = None, None

            if lat is None or lon is None:
                lat, lon = parse_coords_from_url(row_dict.get("url"))

            zona = detect_zone(direccion)

            rating = None
            raw_rating = row_dict.get("rating")
            if raw_rating is not None:
                try:
                    rating = float(raw_rating)
                    if rating < 0 or rating > 5:
                        rating = None
                except (ValueError, TypeError):
                    rating = None

            num_resenas = None
            raw_resenas = row_dict.get("num_resenas")
            if raw_resenas is not None:
                try:
                    num_resenas = int(raw_resenas)
                except (ValueError, TypeError):
                    num_resenas = None

            restaurant = Restaurant(
                fuente=fuente,
                url=row_dict.get("url"),
                nombre=nombre,
                direccion=direccion,
                telefono=telefono,
                rating=rating,
                num_resenas=num_resenas,
                latitud=lat,
                longitud=lon,
                precio=row_dict.get("precio"),
                tipo_cocina=row_dict.get("tipo_cocina"),
                categoria=row_dict.get("categoria"),
                descripcion=row_dict.get("descripcion"),
                servicios=row_dict.get("servicios"),
                zona=zona,
                status="nuevo",
                scraped_at=datetime.now(timezone.utc),
            )
            db.add(restaurant)
            imported += 1

        db.commit()

        # Log the import
        import_log = ScrapingImport(
            source_file=str(SQLITE_PATH),
            source_type="sqlite",
            records_total=len(rows),
            records_imported=imported,
            records_skipped=skipped,
        )
        db.add(import_log)
        db.commit()

        print(f"Importados: {imported}, Omitidos: {skipped}")

        # Calculate scores
        count = calculate_all_scores(db)
        print(f"Scores calculados para {count} restaurantes")

    finally:
        db.close()


if __name__ == "__main__":
    run_migration()
