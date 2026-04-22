"""
menu_analyzer.py
Análisis de afinidad de productos Don Piotr sobre datos scrapeados.

Detecta si un restaurante usa ingredientes que ofrece la fábrica
mediante búsqueda de palabras clave en los campos de texto disponibles.
"""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.restaurants.models import Restaurant

# ---------------------------------------------------------------------------
# Productos del catálogo de Don Piotr con sus palabras clave de detección
# ---------------------------------------------------------------------------
PRODUCTOS_DON_PIOTR: dict[str, list[str]] = {
    "Kielbasa":        ["kielbasa"],
    "Chorizo":         ["chorizo"],
    "Jamón Inglés":    ["jamón inglés", "jamon ingles", "jamón ingles", "jamon inglés"],
    "Costilla Ahumada":["costilla ahumada", "costilla"],
    "Jamón Ahumado":   ["jamón ahumado", "jamon ahumado"],
    "Jamón Crudo":     ["jamón crudo", "jamon crudo", "jamón serrano", "jamon serrano"],
    "Tocino":          ["tocino", "bacon"],
    "Salame":          ["salame", "salami"],
    "Cabanosy":        ["cabanosy", "kabanosy"],
}

# Palabras clave de cocina/categoría que indican uso probable de embutidos
KEYWORDS_AFINES: list[str] = [
    "pizza", "pizzería", "pizzeria",
    "hamburgues", "burger",
    "desayuno americano", "brunch",
    "parrilla", "parrillada", "asado", "bbq", "grill",
    "alemán", "alemana", "german",
    "sandwich", "sándwich", "deli",
    "italiana", "italiano",
    "hot dog", "frankfurt",
    "embutido", "salchicha",
    "comida rápida", "fast food",
    "club sandwich",
]

# Palabras clave que indican que NO se usan embutidos
KEYWORDS_NEGATIVOS: list[str] = [
    "vegetariano", "vegetariana", "vegetarian",
    "vegano", "vegana", "vegan",
    "sushi",
    "thai",
    "árabe", "arabe",
    "halal",
    "sin carne",
]


def _build_text(restaurant: Restaurant) -> str:
    """Concatena todos los campos de texto del restaurante en minúsculas."""
    parts = [
        restaurant.nombre or "",
        restaurant.categoria or "",
        restaurant.tipo_cocina or "",
        restaurant.descripcion or "",
        restaurant.servicios or "",
        restaurant.menu_texto_ocr or "",
    ]
    return " ".join(parts).lower()


def analyze_restaurant(restaurant: Restaurant) -> dict:
    """Analiza un restaurante y determina su afinidad con productos Don Piotr.

    Returns:
        dict con:
            tiene_embutidos (bool | None)
            productos_detectados (str | None)
    """
    texto = _build_text(restaurant)

    if not texto.strip():
        return {"tiene_embutidos": None, "productos_detectados": None}

    # 1. Verificar keywords negativos primero
    for kw in KEYWORDS_NEGATIVOS:
        if kw in texto:
            return {"tiene_embutidos": False, "productos_detectados": None}

    # 2. Buscar productos específicos del catálogo
    encontrados: list[str] = []
    for producto, keywords in PRODUCTOS_DON_PIOTR.items():
        for kw in keywords:
            if kw in texto:
                encontrados.append(producto)
                break

    if encontrados:
        return {
            "tiene_embutidos": True,
            "productos_detectados": ", ".join(encontrados),
        }

    # 3. Buscar keywords de cocinas afines (evidencia indirecta)
    for kw in KEYWORDS_AFINES:
        if kw in texto:
            return {"tiene_embutidos": True, "productos_detectados": None}

    return {"tiene_embutidos": None, "productos_detectados": None}


def run_analysis(db: Session, force: bool = False) -> dict:
    """Ejecuta el análisis sobre todos los restaurantes de la base de datos.

    Args:
        db:    Sesión de SQLAlchemy.
        force: Si True, re-analiza también los restaurantes ya procesados.

    Returns:
        Resumen con conteos por resultado.
    """
    query = db.query(Restaurant)
    if not force:
        query = query.filter(Restaurant.menu_analizado_at.is_(None))

    restaurants = query.all()

    conteos = {
        "analizados": 0,
        "con_embutidos": 0,
        "sin_embutidos": 0,
        "sin_datos": 0,
    }

    for restaurant in restaurants:
        resultado = analyze_restaurant(restaurant)
        restaurant.tiene_embutidos = resultado["tiene_embutidos"]
        restaurant.productos_detectados = resultado["productos_detectados"]
        restaurant.menu_analizado_at = datetime.now(timezone.utc)

        if resultado["tiene_embutidos"] is True:
            conteos["con_embutidos"] += 1
        elif resultado["tiene_embutidos"] is False:
            conteos["sin_embutidos"] += 1
        else:
            conteos["sin_datos"] += 1

        conteos["analizados"] += 1

    db.commit()
    return conteos
