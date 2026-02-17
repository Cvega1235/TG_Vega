"""
data_cleaner.py
Pipeline de limpieza, normalización y deduplicación de datos.
Sistema de Inteligencia de Mercado Don Piotr
"""

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from scraping_don_piotr import config
from scraping_don_piotr.logger import logger
from scraping_don_piotr.utils import normalize_name, normalize_phone

# ============================================================================
# MAPEO DE SINÓNIMOS DE COCINA
# ============================================================================

CUISINE_SYNONYMS: Dict[str, str] = {
    # Hamburguesas
    "hamburguesas": "Hamburguesas",
    "burgers": "Hamburguesas",
    "burger": "Hamburguesas",
    "hamburgueseria": "Hamburguesas",
    # Pizza
    "pizza": "Pizza",
    "pizzeria": "Pizza",
    "pizzas": "Pizza",
    # Comida rápida
    "comida rapida": "Comida Rapida",
    "fast food": "Comida Rapida",
    "comida rápida": "Comida Rapida",
    # Parrilla
    "parrilla": "Parrilla",
    "grill": "Parrilla",
    "asado": "Parrilla",
    "parrillada": "Parrilla",
    # Italiana
    "italiana": "Italiana",
    "italian": "Italiana",
    "comida italiana": "Italiana",
    # Boliviana
    "boliviana": "Boliviana",
    "comida boliviana": "Boliviana",
    "tipica": "Boliviana",
    "comida tipica": "Boliviana",
    # Internacional
    "internacional": "Internacional",
    "international": "Internacional",
    "fusion": "Internacional",
    # Mexicana
    "mexicana": "Mexicana",
    "mexican": "Mexicana",
    "comida mexicana": "Mexicana",
    "tex-mex": "Mexicana",
    # Café
    "cafe": "Cafe",
    "café": "Cafe",
    "cafeteria": "Cafe",
    "cafetería": "Cafe",
    "coffee": "Cafe",
    # Sushi / Japonesa
    "sushi": "Japonesa",
    "japonesa": "Japonesa",
    "japanese": "Japonesa",
    # China
    "china": "China",
    "chinese": "China",
    "comida china": "China",
    # Pollo
    "pollo": "Pollo",
    "pollos": "Pollo",
    "broaster": "Pollo",
    "chicken": "Pollo",
    # Mariscos
    "mariscos": "Mariscos",
    "seafood": "Mariscos",
    "pescados": "Mariscos",
    # Desayunos
    "desayunos": "Desayunos",
    "breakfast": "Desayunos",
    "brunch": "Desayunos",
    # Vegetariana
    "vegetariana": "Vegetariana",
    "vegetarian": "Vegetariana",
    "vegana": "Vegetariana",
    "vegan": "Vegetariana",
    # Peruana
    "peruana": "Peruana",
    "peruvian": "Peruana",
    "comida peruana": "Peruana",
}

# ============================================================================
# MAPEO DE NIVELES DE PRECIO
# ============================================================================

PRICE_SYNONYMS: Dict[str, str] = {
    "$": "$",
    "$$": "$$",
    "$$$": "$$$",
    "$$$$": "$$$$",
    "$ - $$": "$$",
    "$$ - $$$": "$$$",
    "$$$ - $$$$": "$$$$",
    "economico": "$",
    "económico": "$",
    "barato": "$",
    "moderado": "$$",
    "medio": "$$",
    "caro": "$$$",
    "premium": "$$$$",
    "exclusivo": "$$$$",
    "lujoso": "$$$$",
}

# ============================================================================
# ZONAS CON CALLES/LANDMARKS CONOCIDOS
# ============================================================================

ZONE_LANDMARKS: Dict[str, List[str]] = {
    "Sopocachi": [
        "sopocachi", "av. 20 de octubre", "guachalla",
        "pedro salazar", "rosendo gutierrez", "aspiazu",
        "sanchez lima", "j.j. perez",
    ],
    "Miraflores": [
        "miraflores", "av. busch", "av. saavedra",
        "av. del ejercito", "kantutani",
    ],
    "San Miguel": [
        "san miguel", "calle 21", "av. montenegro",
    ],
    "Calacoto": [
        "calacoto", "calle 12", "calle 13", "calle 14",
        "calle 15", "calle 16", "ballivian",
    ],
    "Zona Sur": [
        "zona sur", "av. ballivian",
    ],
    "Achumani": [
        "achumani", "calle 38",
    ],
    "Irpavi": [
        "irpavi", "calle 4 de irpavi",
    ],
    "Obrajes": [
        "obrajes", "av. hernando siles",
    ],
    "Cota Cota": [
        "cota cota", "calle 30 de cota cota",
    ],
    "Centro": [
        "centro", "el prado", "av. camacho", "av. mariscal santa cruz",
        "comercio", "sagarnaga", "linares", "jaen",
        "av. 16 de julio", "plaza murillo",
    ],
}


@dataclass
class CleaningReport:
    """Reporte resumen de las operaciones de limpieza realizadas."""

    total_input: int = 0
    total_output: int = 0
    duplicates_removed: int = 0
    records_with_fixes: int = 0
    field_corrections: Dict[str, int] = field(default_factory=dict)
    null_field_counts: Dict[str, int] = field(default_factory=dict)

    def __str__(self) -> str:
        lines = [
            f"Registros entrada: {self.total_input}",
            f"Registros salida: {self.total_output}",
            f"Duplicados removidos: {self.duplicates_removed}",
            f"Registros corregidos: {self.records_with_fixes}",
        ]
        if self.field_corrections:
            lines.append("Correcciones por campo:")
            for k, v in sorted(self.field_corrections.items()):
                lines.append(f"  {k}: {v}")
        if self.null_field_counts:
            lines.append("Campos nulos restantes:")
            for k, v in sorted(self.null_field_counts.items()):
                lines.append(f"  {k}: {v}")
        return "\n".join(lines)


class DataCleaner:
    """Pipeline de limpieza, normalización y deduplicación de datos de restaurantes.

    Ejecuta una serie de transformaciones sobre los datos crudos extraídos
    por los scrapers para producir datos limpios y consistentes.

    Uso:
        cleaner = DataCleaner(raw_records)
        cleaned, report = cleaner.run_pipeline()
    """

    def __init__(self, records: List[Dict[str, Any]]) -> None:
        """Inicializa el cleaner con los registros crudos.

        Args:
            records: Lista de diccionarios con datos de restaurantes.
        """
        self._raw = records
        self._cleaned: List[Dict[str, Any]] = []
        self._corrections: Dict[str, int] = {}

    def _increment_correction(self, field_name: str) -> None:
        """Incrementa el contador de correcciones para un campo."""
        self._corrections[field_name] = self._corrections.get(field_name, 0) + 1

    def run_pipeline(self) -> Tuple[List[Dict[str, Any]], CleaningReport]:
        """Ejecuta el pipeline completo de limpieza.

        Returns:
            Tupla (registros_limpios, reporte_de_limpieza).
        """
        logger.info(f"Iniciando pipeline de limpieza con {len(self._raw)} registros")

        self._cleaned = [r.copy() for r in self._raw]
        total_input = len(self._cleaned)

        self._normalize_text_fields()
        self._normalize_phones()
        self._normalize_ratings()
        self._normalize_coordinates()
        self._normalize_cuisine_types()
        self._normalize_price_levels()
        self._detect_zones()
        self._deduplicate()
        self._compute_data_quality()

        report = self._build_report(total_input)
        logger.info(f"Pipeline completado:\n{report}")

        return self._cleaned, report

    def _normalize_text_fields(self) -> None:
        """Normaliza campos de texto: NFKC, strip, collapse spaces, title-case nombres."""
        text_fields = ["nombre", "direccion", "categoria", "descripcion"]

        for record in self._cleaned:
            for field_name in text_fields:
                value = record.get(field_name)
                if not value or not isinstance(value, str):
                    continue

                original = value
                # Normalización Unicode NFKC
                value = unicodedata.normalize("NFKC", value)
                # Strip y colapsar espacios múltiples
                value = re.sub(r"\s+", " ", value).strip()

                # Title-case para nombres
                if field_name == "nombre":
                    value = value.title()

                if value != original:
                    record[field_name] = value
                    self._increment_correction(f"{field_name}_normalizado")

    def _normalize_phones(self) -> None:
        """Normaliza teléfonos: quita prefijos, valida longitud, formato."""
        for record in self._cleaned:
            phone = record.get("telefono")
            if not phone:
                continue

            original = phone
            # Quitar prefijos comunes
            for prefix in ["tel:", "Telefono:", "Tel:", "Fono:", "fono:"]:
                if phone.startswith(prefix):
                    phone = phone[len(prefix):]

            normalized = normalize_phone(phone)
            if normalized != original:
                record["telefono"] = normalized
                self._increment_correction("telefono_normalizado")

    def _normalize_ratings(self) -> None:
        """Normaliza ratings: convierte comas, clamp a 0-5."""
        for record in self._cleaned:
            rating = record.get("rating")
            if rating is None:
                continue

            original = rating

            # Convertir string con coma decimal
            if isinstance(rating, str):
                rating = rating.replace(",", ".")
                try:
                    rating = float(rating)
                except ValueError:
                    record["rating"] = None
                    self._increment_correction("rating_invalido")
                    continue

            # Clamp a rango válido
            if not isinstance(rating, (int, float)):
                record["rating"] = None
                continue

            rating = float(rating)
            if rating < config.RATING_MIN:
                rating = config.RATING_MIN
            elif rating > config.RATING_MAX:
                rating = config.RATING_MAX

            if rating != original:
                record["rating"] = round(rating, 1)
                self._increment_correction("rating_normalizado")

    def _normalize_coordinates(self) -> None:
        """Valida coordenadas contra bounding box de La Paz."""
        for record in self._cleaned:
            lat = record.get("latitud")
            lon = record.get("longitud")

            if lat is None or lon is None:
                continue

            try:
                lat = float(lat)
                lon = float(lon)
            except (ValueError, TypeError):
                record["latitud"] = None
                record["longitud"] = None
                self._increment_correction("coordenadas_invalidas")
                continue

            in_range = (
                config.LAT_MIN <= lat <= config.LAT_MAX
                and config.LON_MIN <= lon <= config.LON_MAX
            )
            if not in_range:
                record["latitud"] = None
                record["longitud"] = None
                self._increment_correction("coordenadas_fuera_rango")

    def _normalize_cuisine_types(self) -> None:
        """Mapea tipos de cocina a formas canónicas usando sinónimos."""
        for record in self._cleaned:
            cocina = record.get("tipo_cocina")
            if not cocina or not isinstance(cocina, str):
                continue

            original = cocina
            # Puede tener múltiples tipos separados por coma
            parts = [p.strip() for p in cocina.split(",")]
            normalized_parts = []

            for part in parts:
                key = part.lower().strip()
                canonical = CUISINE_SYNONYMS.get(key, part.strip().title())
                normalized_parts.append(canonical)

            normalized = ", ".join(normalized_parts)
            if normalized != original:
                record["tipo_cocina"] = normalized
                self._increment_correction("tipo_cocina_normalizado")

    def _normalize_price_levels(self) -> None:
        """Normaliza niveles de precio a formato $/$$/$$$/$$$$."""
        for record in self._cleaned:
            precio = record.get("precio")
            if not precio or not isinstance(precio, str):
                continue

            original = precio
            key = precio.strip().lower()
            normalized = PRICE_SYNONYMS.get(key)

            if normalized and normalized != original:
                record["precio"] = normalized
                self._increment_correction("precio_normalizado")

    def _detect_zones(self) -> None:
        """Detecta la zona de La Paz desde la dirección del restaurante."""
        for record in self._cleaned:
            # Si ya tiene zona, no sobreescribir
            if record.get("zona"):
                continue

            direccion = record.get("direccion")
            if not direccion or not isinstance(direccion, str):
                continue

            addr_lower = direccion.lower()

            # Primero buscar por landmarks/calles conocidas
            detected = None
            for zona, keywords in ZONE_LANDMARKS.items():
                for keyword in keywords:
                    if keyword in addr_lower:
                        detected = zona
                        break
                if detected:
                    break

            # Fallback: buscar nombre de zona directamente
            if not detected:
                for zona in config.ZONAS_LA_PAZ:
                    if zona.lower() in addr_lower:
                        detected = zona
                        break

            if detected:
                record["zona"] = detected
                self._increment_correction("zona_detectada")

    def _deduplicate(self) -> None:
        """Remueve duplicados por nombre normalizado y fuente.

        Mantiene el registro con más campos no-nulos en caso de duplicados.
        """
        seen: Dict[str, int] = {}
        indices_to_remove: List[int] = []

        for i, record in enumerate(self._cleaned):
            nombre = record.get("nombre", "")
            fuente = record.get("fuente", "")
            key = f"{normalize_name(nombre)}|{fuente.lower()}"

            if key in seen:
                existing_idx = seen[key]
                existing = self._cleaned[existing_idx]

                # Contar campos no-nulos
                existing_count = sum(
                    1 for v in existing.values() if v is not None and v != ""
                )
                current_count = sum(
                    1 for v in record.values() if v is not None and v != ""
                )

                if current_count > existing_count:
                    # El nuevo registro es más completo, quitar el anterior
                    indices_to_remove.append(existing_idx)
                    seen[key] = i
                else:
                    indices_to_remove.append(i)
            else:
                seen[key] = i

        # Remover duplicados (en orden inverso para no afectar índices)
        for idx in sorted(set(indices_to_remove), reverse=True):
            self._cleaned.pop(idx)

        if indices_to_remove:
            removed = len(set(indices_to_remove))
            logger.info(f"Deduplicacion: {removed} duplicados removidos")

    def _compute_data_quality(self) -> None:
        """Calcula un score de calidad de datos (0-1) por registro.

        Basado en la completitud de campos clave.
        """
        quality_fields = [
            "nombre", "direccion", "telefono", "rating",
            "num_resenas", "latitud", "longitud", "precio",
            "tipo_cocina", "zona",
        ]
        total_fields = len(quality_fields)

        for record in self._cleaned:
            non_null = sum(
                1 for f in quality_fields
                if record.get(f) is not None and record.get(f) != ""
            )
            record["data_quality"] = round(non_null / total_fields, 2)

    def _build_report(self, total_input: int) -> CleaningReport:
        """Construye el reporte final de limpieza.

        Args:
            total_input: Cantidad de registros de entrada.

        Returns:
            CleaningReport con los conteos de operaciones.
        """
        # Contar campos nulos en el resultado final
        null_counts: Dict[str, int] = {}
        key_fields = [
            "nombre", "direccion", "telefono", "rating",
            "num_resenas", "latitud", "longitud", "precio",
            "tipo_cocina", "zona",
        ]
        for field_name in key_fields:
            count = sum(
                1 for r in self._cleaned
                if r.get(field_name) is None or r.get(field_name) == ""
            )
            if count > 0:
                null_counts[field_name] = count

        return CleaningReport(
            total_input=total_input,
            total_output=len(self._cleaned),
            duplicates_removed=total_input - len(self._cleaned),
            records_with_fixes=sum(self._corrections.values()),
            field_corrections=dict(self._corrections),
            null_field_counts=null_counts,
        )
