"""
menu_analyzer.py
Analiza si los restaurantes de la BD utilizan productos embutidos
en sus menús, basándose en palabras clave y tipo de cocina.

Sistema de Inteligencia de Mercado Don Piotr
"""

import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Agregar el proyecto al path
project_root = Path(__file__).resolve().parent.parent
backend_dir = project_root / "sis_TG" / "backend"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(backend_dir))

from dotenv import load_dotenv
load_dotenv(backend_dir / ".env")

from app.users.models import User  # noqa: F401 - registra el modelo
from app.database import SessionLocal
from app.restaurants.models import Restaurant
from scraping_don_piotr.logger import logger


# ---------------------------------------------------------------------------
# Diccionario de productos Don Piotr y sus palabras clave de detección
# ---------------------------------------------------------------------------
PRODUCTOS_KEYWORDS: dict[str, list[str]] = {
    "Chorizo": [
        "chorizo", "chorizos",
    ],
    "Salchicha": [
        "salchicha", "salchichas", "hot dog", "hotdog", "hot-dog",
        "frankfurt", "frankfurter", "wiener", "vienesa",
    ],
    "Jamón": [
        "jamón", "jamon", "ham", "prosciutto",
    ],
    "Salame": [
        "salame", "salami", "salames",
    ],
    "Longaniza": [
        "longaniza", "longanizas",
    ],
    "Mortadela": [
        "mortadela", "mortadella",
    ],
    "Tocino": [
        "tocino", "bacon", "panceta",
    ],
    "Pepperoni": [
        "pepperoni", "pepperón",
    ],
    "Embutido (general)": [
        "embutido", "embutidos", "fiambre", "fiambres",
        "chacinado", "chacinados", "ahumado", "ahumados",
    ],
}

# ---------------------------------------------------------------------------
# Inferencia por tipo de cocina
# Si el restaurante NO tiene descripción, pero tiene un tipo de cocina
# que típicamente usa embutidos, se infiere que los usa.
# ---------------------------------------------------------------------------
COCINA_INFERENCIA: dict[str, list[str]] = {
    "Pizza / Italiana": [
        "pizza", "pizzería", "pizzeria", "italiana", "italiano",
        "trattoria", "ristorante",
    ],
    "Hamburguesas / Fast Food": [
        "hamburguesa", "hamburguesas", "burger", "burgers",
        "fast food", "comida rápida", "comida rapida",
    ],
    "Sándwiches / Bocadillos": [
        "sándwich", "sandwich", "sandwiches", "bocadillo",
        "sub", "deli",
    ],
    "Parrilla / BBQ": [
        "parrilla", "parrillada", "bbq", "barbecue", "asado",
        "grill", "steakhouse",
    ],
    "Tacos / Mexicana": [
        "taco", "tacos", "mexicana", "mexicano", "burrito",
        "burritos", "tex-mex", "tex mex",
    ],
    "Perros calientes": [
        "perro caliente", "perros calientes", "dog",
    ],
    "Desayunos": [
        "desayuno", "desayunos", "breakfast",
    ],
}


def normalizar(text: str) -> str:
    """Convierte a minúsculas y elimina tildes para facilitar comparación."""
    text = text.lower()
    reemplazos = {
        "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u",
        "ä": "a", "ë": "e", "ï": "i", "ö": "o", "ü": "u",
        "à": "a", "è": "e", "ì": "i", "ò": "o", "ù": "u",
    }
    for acento, sin_acento in reemplazos.items():
        text = text.replace(acento, sin_acento)
    return text


def detectar_productos(texto_completo: str) -> list[str]:
    """
    Busca keywords de productos embutidos en el texto dado.
    Retorna lista de productos detectados (sin duplicados).
    """
    if not texto_completo:
        return []

    texto_norm = normalizar(texto_completo)
    encontrados: list[str] = []

    for producto, keywords in PRODUCTOS_KEYWORDS.items():
        for kw in keywords:
            kw_norm = normalizar(kw)
            # Búsqueda con límites de palabra para evitar falsos positivos
            patron = r"\b" + re.escape(kw_norm) + r"\b"
            if re.search(patron, texto_norm):
                encontrados.append(producto)
                break  # No duplicar el mismo producto

    return encontrados


def inferir_por_cocina(tipo_cocina: Optional[str], categoria: Optional[str]) -> list[str]:
    """
    Si no se detectaron keywords directas, infiere por tipo de cocina.
    Retorna lista de categorías de cocina inferidas con uso probable.
    """
    texto = " ".join(filter(None, [tipo_cocina, categoria]))
    if not texto:
        return []

    texto_norm = normalizar(texto)
    inferidos: list[str] = []

    for cocina, keywords in COCINA_INFERENCIA.items():
        for kw in keywords:
            kw_norm = normalizar(kw)
            if kw_norm in texto_norm:
                inferidos.append(f"[Inferido] {cocina}")
                break

    return inferidos


def analizar_restaurante(restaurant: Restaurant) -> tuple[bool, str]:
    """
    Analiza un restaurante y retorna (tiene_embutidos, productos_csv).

    Estrategia:
    1. Concatena todos los campos de texto del restaurante
    2. Busca keywords de productos embutidos
    3. Si no hay coincidencia directa, infiere por tipo de cocina
    """
    # Concatenar todos los campos textuales disponibles
    campos_texto = " | ".join(filter(None, [
        restaurant.nombre,
        restaurant.tipo_cocina,
        restaurant.categoria,
        restaurant.descripcion,
        restaurant.servicios,
    ]))

    productos = detectar_productos(campos_texto)

    if not productos:
        # Intentar inferencia por tipo de cocina
        productos = inferir_por_cocina(restaurant.tipo_cocina, restaurant.categoria)

    tiene_embutidos = len(productos) > 0
    productos_str = ", ".join(productos) if productos else ""

    return tiene_embutidos, productos_str


def run_analysis(batch_size: int = 100, solo_no_analizados: bool = True) -> dict:
    """
    Ejecuta el análisis de menú sobre todos los restaurantes de la BD.

    Args:
        batch_size: Número de restaurantes a procesar por lote.
        solo_no_analizados: Si True, solo analiza los que no tienen análisis previo.

    Returns:
        Diccionario con estadísticas del análisis.
    """
    db = SessionLocal()
    stats = {
        "total_analizados": 0,
        "con_embutidos": 0,
        "sin_embutidos": 0,
        "productos_top": {},
    }

    try:
        query = db.query(Restaurant)
        if solo_no_analizados:
            query = query.filter(Restaurant.menu_analizado_at.is_(None))

        # Obtener todos los IDs primero para evitar bug de paginación
        ids = [r.id for r in query.with_entities(Restaurant.id).all()]
        total = len(ids)
        logger.info(f"Restaurantes a analizar: {total}")

        procesados = 0
        for i in range(0, total, batch_size):
            lote_ids = ids[i:i + batch_size]
            lote = db.query(Restaurant).filter(Restaurant.id.in_(lote_ids)).all()

            for restaurant in lote:
                tiene_embutidos, productos_str = analizar_restaurante(restaurant)

                restaurant.tiene_embutidos = tiene_embutidos
                restaurant.productos_detectados = productos_str if productos_str else None
                restaurant.menu_analizado_at = datetime.now(timezone.utc)

                if tiene_embutidos:
                    stats["con_embutidos"] += 1
                    for prod in productos_str.split(", "):
                        prod = prod.strip()
                        if prod:
                            stats["productos_top"][prod] = stats["productos_top"].get(prod, 0) + 1
                else:
                    stats["sin_embutidos"] += 1

                procesados += 1

            db.commit()
            logger.info(f"Procesados: {procesados}/{total}")

        stats["total_analizados"] = procesados

    except Exception as e:
        db.rollback()
        logger.error(f"Error en análisis: {e}")
        raise
    finally:
        db.close()

    return stats


def imprimir_resumen(stats: dict) -> None:
    """Imprime un resumen legible de los resultados del análisis."""
    total = stats["total_analizados"]
    con = stats["con_embutidos"]
    sin = stats["sin_embutidos"]
    pct = (con / total * 100) if total > 0 else 0

    print("\n" + "=" * 60)
    print("RESULTADO DEL ANALISIS DE MENU - DON PIOTR")
    print("=" * 60)
    print(f"Total analizados    : {total}")
    print(f"Con embutidos       : {con}  ({pct:.1f}%)")
    print(f"Sin embutidos       : {sin}  ({100 - pct:.1f}%)")

    if stats["productos_top"]:
        print("\nProductos detectados (frecuencia):")
        sorted_prods = sorted(
            stats["productos_top"].items(), key=lambda x: x[1], reverse=True
        )
        for prod, count in sorted_prods:
            print(f"  {prod:<35} {count} restaurantes")

    print("=" * 60)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Analiza menús de restaurantes para detectar productos embutidos"
    )
    parser.add_argument(
        "--todos",
        action="store_true",
        help="Re-analizar todos los restaurantes (incluyendo ya analizados)",
    )
    parser.add_argument(
        "--batch",
        type=int,
        default=100,
        help="Tamaño del lote de procesamiento (default: 100)",
    )
    args = parser.parse_args()

    logger.info("Iniciando análisis de menús...")
    stats = run_analysis(
        batch_size=args.batch,
        solo_no_analizados=not args.todos,
    )
    imprimir_resumen(stats)
