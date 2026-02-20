"""
tripadvisor_api.py
Scraper de TripAdvisor usando la Content API oficial.
Sistema de Inteligencia de Mercado Don Piotr
"""

import os
import time
from typing import Any, Dict, List, Optional

import requests

from scraping_don_piotr.base_scraper import BaseScraper, RestaurantData
from scraping_don_piotr.logger import logger
from scraping_don_piotr import config

# Coordenadas de búsqueda: zonas principales + sub-puntos para mayor cobertura
# nearby_search devuelve max 10 por llamada, así que subdividimos zonas grandes
ZONE_COORDS = [
    # Zona Sur - subdividida en múltiples puntos
    {"name": "San Miguel", "lat": -16.5410, "lon": -68.0790},
    {"name": "San Miguel Sur", "lat": -16.5440, "lon": -68.0770},
    {"name": "Calacoto", "lat": -16.5445, "lon": -68.0835},
    {"name": "Calacoto Norte", "lat": -16.5400, "lon": -68.0850},
    {"name": "Zona Sur", "lat": -16.5500, "lon": -68.0750},
    {"name": "Zona Sur Oeste", "lat": -16.5520, "lon": -68.0820},
    {"name": "Megacenter", "lat": -16.5340, "lon": -68.0870},
    {"name": "Achumani", "lat": -16.5370, "lon": -68.0650},
    {"name": "Achumani Alto", "lat": -16.5330, "lon": -68.0600},
    {"name": "Irpavi", "lat": -16.5350, "lon": -68.0740},
    {"name": "Irpavi II", "lat": -16.5380, "lon": -68.0700},
    {"name": "Cota Cota", "lat": -16.5410, "lon": -68.0600},
    {"name": "Obrajes", "lat": -16.5280, "lon": -68.1050},
    {"name": "Obrajes Alto", "lat": -16.5240, "lon": -68.1000},
    # Zona Central - subdividida
    {"name": "Sopocachi", "lat": -16.5060, "lon": -68.1280},
    {"name": "Sopocachi Norte", "lat": -16.5020, "lon": -68.1260},
    {"name": "Sopocachi Sur", "lat": -16.5100, "lon": -68.1300},
    {"name": "Miraflores", "lat": -16.5090, "lon": -68.1140},
    {"name": "Miraflores Sur", "lat": -16.5130, "lon": -68.1120},
    {"name": "Miraflores Este", "lat": -16.5070, "lon": -68.1090},
    {"name": "Centro", "lat": -16.4960, "lon": -68.1335},
    {"name": "Centro Sur", "lat": -16.5000, "lon": -68.1320},
    {"name": "San Pedro", "lat": -16.4980, "lon": -68.1390},
    {"name": "San Pedro Sur", "lat": -16.5020, "lon": -68.1400},
    # Zonas adicionales
    {"name": "Bajo Seguencoma", "lat": -16.5300, "lon": -68.0920},
    {"name": "Seguencoma", "lat": -16.5260, "lon": -68.0950},
    {"name": "Los Pinos", "lat": -16.5460, "lon": -68.0680},
    {"name": "Florida", "lat": -16.5350, "lon": -68.0810},
    {"name": "Av Ballivian", "lat": -16.5390, "lon": -68.0800},
    {"name": "Av Arce", "lat": -16.5080, "lon": -68.1200},
    {"name": "El Prado", "lat": -16.5000, "lon": -68.1330},
    {"name": "Plaza Avaroa", "lat": -16.5050, "lon": -68.1310},
    {"name": "Av 6 de Agosto", "lat": -16.5030, "lon": -68.1250},
    {"name": "San Jorge", "lat": -16.5010, "lon": -68.1220},
    {"name": "Plaza Murillo", "lat": -16.4955, "lon": -68.1340},
    {"name": "Rosario", "lat": -16.4940, "lon": -68.1370},
    {"name": "Max Paredes", "lat": -16.4920, "lon": -68.1400},
    {"name": "Av Camacho", "lat": -16.4970, "lon": -68.1350},
    {"name": "Av Mariscal Santa Cruz", "lat": -16.4990, "lon": -68.1360},
    {"name": "Villa Copacabana", "lat": -16.4890, "lon": -68.1180},
    {"name": "Tembladerani", "lat": -16.5050, "lon": -68.1420},
]

API_BASE = "https://api.content.tripadvisor.com/api/v1"


class TripAdvisorAPIScraper(BaseScraper):
    """Scraper de TripAdvisor usando la Content API oficial."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        super().__init__()
        self.api_key = api_key or os.environ.get("TRIPADVISOR_API_KEY", "")
        if not self.api_key:
            raise ValueError(
                "Se requiere TRIPADVISOR_API_KEY. "
                "Configura la variable de entorno o pasa api_key al constructor."
            )
        self.session = requests.Session()
        self.seen_ids: set = set()
        self.api_calls = 0

    def _api_get(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Hace una llamada GET a la API de TripAdvisor."""
        url = f"{API_BASE}{endpoint}"
        params = params or {}
        params["key"] = self.api_key

        try:
            resp = self.session.get(url, params=params, timeout=config.TIMEOUT_DEFAULT)
            self.api_calls += 1
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 429:
                logger.warning("Rate limit alcanzado, esperando 5 segundos...")
                time.sleep(5)
                return self._api_get(endpoint, {k: v for k, v in params.items() if k != "key"})
            else:
                logger.error(f"API error {resp.status_code}: {resp.text[:200]}")
                return None
        except requests.RequestException as e:
            logger.error(f"Error de conexion a TripAdvisor API: {e}")
            return None

    def _search_nearby(self, lat: float, lon: float, radius: str = "2") -> List[Dict]:
        """Busca restaurantes cercanos a unas coordenadas."""
        data = self._api_get("/location/nearby_search", {
            "latLong": f"{lat},{lon}",
            "category": "restaurants",
            "radius": radius,
            "radiusUnit": "km",
            "language": "es",
        })
        if data and "data" in data:
            return data["data"]
        return []

    def _search_query(self, query: str) -> List[Dict]:
        """Busca restaurantes por texto."""
        data = self._api_get("/location/search", {
            "searchQuery": query,
            "category": "restaurants",
            "language": "es",
        })
        if data and "data" in data:
            return data["data"]
        return []

    def _get_details(self, location_id: str) -> Optional[Dict]:
        """Obtiene los detalles completos de un restaurante."""
        data = self._api_get(f"/location/{location_id}/details", {
            "language": "es",
            "currency": "BOB",
        })
        return data

    def _detect_zone(self, address: str, lat: Optional[float] = None, lon: Optional[float] = None) -> Optional[str]:
        """Detecta la zona basándose en la dirección o coordenadas."""
        addr_lower = address.lower() if address else ""
        for zona in config.ZONAS_LA_PAZ:
            if zona.lower() in addr_lower:
                return zona

        if lat and lon:
            best_zone = None
            best_dist = float("inf")
            for zone in ZONE_COORDS:
                dist = (lat - zone["lat"]) ** 2 + (lon - zone["lon"]) ** 2
                if dist < best_dist:
                    best_dist = dist
                    best_zone = zone["name"]
            if best_dist < 0.001:  # ~1km aprox
                return best_zone

        return None

    def _parse_restaurant(self, details: Dict) -> Optional[RestaurantData]:
        """Convierte los detalles de la API a RestaurantData."""
        name = details.get("name", "").strip()
        if not name:
            return None

        # Coordenadas
        lat = None
        lon = None
        try:
            lat = float(details["latitude"])
            lon = float(details["longitude"])
        except (KeyError, ValueError, TypeError):
            pass

        # Rating
        rating = None
        try:
            rating = float(details["rating"])
        except (KeyError, ValueError, TypeError):
            pass

        # Num reviews
        num_resenas = None
        try:
            num_resenas = int(details["num_reviews"])
        except (KeyError, ValueError, TypeError):
            pass

        # Precio
        precio = details.get("price_level")

        # Cuisine
        cuisines = details.get("cuisine", [])
        tipo_cocina = ", ".join(c.get("localized_name", c.get("name", "")) for c in cuisines) if cuisines else None

        # Dirección
        addr_obj = details.get("address_obj", {})
        direccion = addr_obj.get("address_string", "")

        # Teléfono
        telefono = details.get("phone")

        # URL
        url = details.get("web_url")

        # Descripción
        descripcion = details.get("description")

        # Servicios/features
        features = details.get("features", [])
        servicios = ", ".join(features) if features else None

        # Zona
        zona = self._detect_zone(direccion, lat, lon)

        return RestaurantData(
            nombre=name,
            fuente="TripAdvisor",
            url=url,
            direccion=direccion,
            telefono=telefono,
            rating=rating,
            num_resenas=num_resenas,
            latitud=lat,
            longitud=lon,
            precio=precio,
            tipo_cocina=tipo_cocina,
            categoria="Restaurante",
            descripcion=descripcion,
            servicios=servicios,
            zona=zona,
        )

    def extract_restaurant_data(self, source: Any) -> Optional[RestaurantData]:
        """Implementación del método abstracto."""
        if isinstance(source, dict):
            return self._parse_restaurant(source)
        return None

    def scrape(self, limit: Optional[int] = None) -> List[RestaurantData]:
        """Ejecuta el scraping completo usando la API de TripAdvisor.

        Estrategia:
        1. Buscar por coordenadas de cada zona (nearby_search) → location_ids
        2. Buscar por texto adicional para cubrir más restaurantes
        3. Obtener detalles completos de cada uno (location details)
        """
        logger.info("Iniciando scraping de TripAdvisor (API oficial)...")
        location_ids: List[str] = []

        # Fase 1: Búsqueda por zona (nearby_search)
        for zone in ZONE_COORDS:
            logger.info(f"Buscando en zona: {zone['name']}...")
            results = self._search_nearby(zone["lat"], zone["lon"])
            for r in results:
                loc_id = r.get("location_id")
                if loc_id and loc_id not in self.seen_ids:
                    self.seen_ids.add(loc_id)
                    location_ids.append(loc_id)
            logger.info(f"  {zone['name']}: {len(results)} encontrados ({len(location_ids)} unicos total)")
            time.sleep(0.3)

        # Fase 2: Búsqueda por texto adicional (por tipo de cocina y barrio)
        text_queries = [
            "restaurantes La Paz Bolivia",
            "mejores restaurantes La Paz Bolivia",
            "comida La Paz Bolivia",
            "restaurante boliviano La Paz",
            "pizza La Paz Bolivia",
            "sushi La Paz Bolivia",
            "comida italiana La Paz Bolivia",
            "comida china La Paz Bolivia",
            "comida mexicana La Paz Bolivia",
            "parrilla La Paz Bolivia",
            "cafe La Paz Bolivia",
            "comida rapida La Paz Bolivia",
            "hamburguesas La Paz Bolivia",
            "pollo La Paz Bolivia",
            "restaurante Sopocachi La Paz",
            "restaurante Calacoto La Paz",
            "restaurante San Miguel La Paz",
            "restaurante Miraflores La Paz",
            "restaurante Centro La Paz",
            "restaurante Obrajes La Paz",
            "restaurante Achumani La Paz",
            "comida vegetariana La Paz Bolivia",
            "bar restaurante La Paz Bolivia",
            "desayuno brunch La Paz Bolivia",
        ]
        for query in text_queries:
            logger.info(f"Buscando: '{query}'...")
            results = self._search_query(query)
            for r in results:
                loc_id = r.get("location_id")
                if loc_id and loc_id not in self.seen_ids:
                    self.seen_ids.add(loc_id)
                    location_ids.append(loc_id)
            time.sleep(0.3)

        logger.info(f"Total location_ids unicos encontrados: {len(location_ids)}")

        # Aplicar límite
        if limit and len(location_ids) > limit:
            location_ids = location_ids[:limit]
            logger.info(f"Limitado a {limit} restaurantes")

        # Fase 3: Obtener detalles de cada restaurante
        for i, loc_id in enumerate(location_ids):
            logger.info(f"Obteniendo detalles [{i + 1}/{len(location_ids)}]: ID {loc_id}...")
            details = self._get_details(loc_id)
            if details:
                restaurant = self._parse_restaurant(details)
                if restaurant:
                    self.results.append(restaurant)
                    logger.info(f"  OK: {restaurant.nombre} ({restaurant.tipo_cocina}) - {restaurant.precio}")
            time.sleep(0.2)

        logger.info(
            f"TripAdvisor API: {len(self.results)} restaurantes obtenidos "
            f"({self.api_calls} llamadas API usadas)"
        )
        return self.results
