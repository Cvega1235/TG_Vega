"""
base_scraper.py
Clase base abstracta y modelo de datos para scrapers.
Sistema de Inteligencia de Mercado Don Piotr
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class RestaurantData:
    """Contenedor tipado para datos de un restaurante extraído.

    Define el schema uniforme que todos los scrapers deben producir,
    garantizando consistencia entre fuentes.
    """

    nombre: str
    fuente: str
    url: Optional[str] = None
    direccion: Optional[str] = None
    telefono: Optional[str] = None
    rating: Optional[float] = None
    num_resenas: Optional[int] = None
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    precio: Optional[str] = None
    tipo_cocina: Optional[str] = None
    categoria: Optional[str] = None
    descripcion: Optional[str] = None
    servicios: Optional[str] = None
    zona: Optional[str] = None
    scraped_at: str = field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el dataclass a diccionario para exportación."""
        return asdict(self)


class BaseScraper(ABC):
    """Clase base abstracta para todos los scrapers.

    Define la interfaz común que cada scraper debe implementar,
    asegurando un contrato uniforme para el orquestador principal.
    """

    def __init__(self) -> None:
        self.results: List[RestaurantData] = []

    @abstractmethod
    def scrape(self, limit: Optional[int] = None) -> List[RestaurantData]:
        """Ejecuta el proceso de scraping completo.

        Args:
            limit: Número máximo de restaurantes a extraer.
                   None indica sin límite.

        Returns:
            Lista de RestaurantData con los datos extraídos.
        """
        ...

    @abstractmethod
    def extract_restaurant_data(self, source: Any) -> Optional[RestaurantData]:
        """Extrae datos de un restaurante individual.

        Args:
            source: Fuente de datos (URL, elemento HTML, etc.)
                    según la implementación del scraper.

        Returns:
            RestaurantData con los datos extraídos o None si falla.
        """
        ...

    def get_results_as_dicts(self) -> List[Dict[str, Any]]:
        """Retorna los resultados como lista de diccionarios.

        Útil para compatibilidad con pandas y exportación.
        """
        return [r.to_dict() for r in self.results]
