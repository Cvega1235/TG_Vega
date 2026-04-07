"""
import_clientes.py
Importa los clientes actuales desde data/clientes_actuales.csv
a la base de datos con status = "cliente".

Uso:
    cd sis_TG/backend
    python scripts/import_clientes.py
"""

import sys
from pathlib import Path

# Asegurar que el backend esté en el path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import csv
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
import app.users.models  # noqa: F401 — necesario para registrar User en SQLAlchemy
from app.restaurants.models import Base, Restaurant

CSV_PATH = Path(__file__).resolve().parent.parent.parent.parent / "data" / "clientes_actuales.csv"


def parse_float(value: str) -> float | None:
    try:
        return float(value) if value.strip() else None
    except ValueError:
        return None


def parse_int(value: str) -> int | None:
    try:
        return int(value) if value.strip() else None
    except ValueError:
        return None


def import_clientes(db: Session) -> None:
    if not CSV_PATH.exists():
        print(f"[ERROR] No se encontró el archivo: {CSV_PATH}")
        sys.exit(1)

    print(f"[INFO] Leyendo clientes desde: {CSV_PATH}")

    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"[INFO] {len(rows)} clientes encontrados en el CSV")

    insertados = 0
    actualizados = 0

    for row in rows:
        nombre = row.get("nombre", "").strip()
        if not nombre:
            continue

        # Buscar si ya existe por nombre
        existente = db.query(Restaurant).filter(Restaurant.nombre == nombre).first()

        if existente:
            # Solo actualizar status si no es ya cliente
            if existente.status != "cliente":
                existente.status = "cliente"
                actualizados += 1
                print(f"  [UPDATE] {nombre} → status=cliente")
        else:
            # Insertar nuevo registro
            restaurante = Restaurant(
                nombre=nombre,
                fuente="manual",
                rating=parse_float(row.get("rating", "")),
                tipo_cocina=row.get("tipo_cocina", "").strip() or None,
                zona=row.get("zona", "").strip() or None,
                num_resenas=parse_int(row.get("num_resenas", "")),
                direccion=row.get("direccion", "").strip() or None,
                telefono=row.get("telefono", "").strip() or None,
                precio=row.get("precio", "").strip() or None,
                latitud=parse_float(row.get("latitud", "")),
                longitud=parse_float(row.get("longitud", "")),
                status="cliente",
            )
            db.add(restaurante)
            insertados += 1
            print(f"  [INSERT] {nombre}")

    db.commit()
    print(f"\n[OK] Importación completada:")
    print(f"     Insertados: {insertados}")
    print(f"     Actualizados a cliente: {actualizados}")
    print(f"     Total procesados: {insertados + actualizados}")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        import_clientes(db)
    finally:
        db.close()
