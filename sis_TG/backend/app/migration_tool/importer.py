"""Service for importing data from JSON/CSV/SQLite uploads."""
import csv
import io
import json
import sqlite3
import tempfile
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.restaurants.models import Restaurant, ScrapingImport
from app.scoring.engine import calculate_all_scores
from app.migration_tool.migrate_sqlite import (
    clean_address, clean_phone, parse_coords_from_url, detect_zone,
)


def _import_records(db: Session, records: list[dict], source_info: str, user_id=None) -> dict:
    imported = 0
    skipped = 0

    for record in records:
        nombre = (record.get("nombre") or "").strip()
        fuente = (record.get("fuente") or "").strip()

        if not nombre:
            skipped += 1
            continue

        existing = db.query(Restaurant).filter(
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
            zona=detect_zone(direccion),
            status="nuevo",
            scraped_at=datetime.now(timezone.utc),
        )
        db.add(restaurant)
        imported += 1

    db.commit()

    log = ScrapingImport(
        source_file=source_info,
        source_type="upload",
        records_total=len(records),
        records_imported=imported,
        records_skipped=skipped,
        imported_by=user_id,
    )
    db.add(log)
    db.commit()

    calculate_all_scores(db)

    return {
        "total": len(records),
        "imported": imported,
        "skipped": skipped,
    }


def import_json(db: Session, content: bytes, user_id=None) -> dict:
    records = json.loads(content.decode("utf-8"))
    if not isinstance(records, list):
        records = [records]
    return _import_records(db, records, "json_upload", user_id)


def import_csv_data(db: Session, content: bytes, user_id=None) -> dict:
    text = content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))
    records = list(reader)
    return _import_records(db, records, "csv_upload", user_id)


def import_sqlite(db: Session, content: bytes, user_id=None) -> dict:
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        f.write(content)
        f.flush()
        conn = sqlite3.connect(f.name)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM restaurantes")
        rows = cursor.fetchall()
        records = [dict(row) for row in rows]
        conn.close()

    return _import_records(db, records, "sqlite_upload", user_id)
