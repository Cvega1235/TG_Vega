"""
tripadvisor_scraper.py
Extractor de datos de restaurantes desde TripAdvisor usando undetected-chromedriver.
Sistema de Inteligencia de Mercado Don Piotr

TripAdvisor usa DataDome CAPTCHA que bloquea Selenium estándar.
Se usa undetected-chromedriver para evadir la detección.

Estrategia: Extraer datos del JSON-LD embebido en las páginas de listado,
que contiene 30 restaurantes por página con datos estructurados.
Solo se visitan páginas individuales para datos faltantes.
"""

import json
from typing import Dict, List, Optional, Set

import undetected_chromedriver as uc
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from scraping_don_piotr import config
from scraping_don_piotr.base_scraper import BaseScraper, RestaurantData
from scraping_don_piotr.logger import logger
from scraping_don_piotr.utils import (
    validate_coordinates,
    wait_random,
)


class TripAdvisorScraper(BaseScraper):
    """Extractor de restaurantes desde TripAdvisor.

    Utiliza undetected-chromedriver para evadir DataDome CAPTCHA.
    Extrae datos del JSON-LD embebido en páginas de listado (30 por página).
    """

    def __init__(self, headless: bool = False) -> None:
        super().__init__()
        self.driver: Optional[uc.Chrome] = None
        self.headless = headless
        self._seen_names: Set[str] = set()

    def setup_driver(self) -> None:
        """Configura undetected-chromedriver."""
        options = uc.ChromeOptions()
        options.add_argument("--lang=es")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        if self.headless:
            options.add_argument("--headless=new")

        self.driver = uc.Chrome(
            options=options,
            headless=self.headless,
            version_main=144,
        )
        self.driver.implicitly_wait(10)
        logger.info("undetected-chromedriver iniciado para TripAdvisor")

    def _dismiss_popups(self) -> None:
        """Cierra popups de idioma, cookies, etc."""
        popup_selectors = [
            "button[aria-label='Close']",
            "button[aria-label='Cerrar']",
            "#onetrust-accept-btn-handler",
            "button.evidon-barrier-acceptall",
        ]
        for sel in popup_selectors:
            try:
                btn = self.driver.find_element(By.CSS_SELECTOR, sel)
                btn.click()
                wait_random(1.0)
            except (NoSuchElementException, Exception):
                continue

    def extract_restaurant_data(self, url: str) -> Optional[RestaurantData]:
        """No se usa en la estrategia de JSON-LD de listado."""
        return None

    def _detect_zona(self, direccion: Optional[str]) -> Optional[str]:
        """Detecta la zona de La Paz desde la dirección."""
        if not direccion:
            return None
        direccion_lower = direccion.lower()
        for zona in config.ZONAS_LA_PAZ:
            if zona.lower() in direccion_lower:
                return zona
        return None

    def _extract_from_listing_jsonld(self) -> List[Dict]:
        """Extrae datos de restaurantes del JSON-LD ItemList en la página de listado.

        Returns:
            Lista de diccionarios con datos de cada restaurante.
        """
        restaurants = []
        try:
            scripts = self.driver.find_elements(
                By.CSS_SELECTOR, 'script[type="application/ld+json"]'
            )
            for script in scripts:
                try:
                    data = json.loads(script.get_attribute("innerHTML"))
                    if (
                        data.get("@type") == "ItemList"
                        and "itemListElement" in data
                    ):
                        for item in data["itemListElement"]:
                            restaurant = item.get("item", {})
                            if restaurant.get("@type") == "Restaurant":
                                rest_data = {
                                    "nombre": restaurant.get("name"),
                                    "url": restaurant.get("url"),
                                }
                                # Rating y reseñas
                                agg = restaurant.get("aggregateRating", {})
                                if agg:
                                    try:
                                        rest_data["rating"] = float(
                                            agg.get("ratingValue", 0)
                                        )
                                    except (ValueError, TypeError):
                                        pass
                                    try:
                                        rest_data["num_resenas"] = int(
                                            agg.get("reviewCount", 0)
                                        )
                                    except (ValueError, TypeError):
                                        pass
                                # Precio
                                rest_data["precio"] = restaurant.get("priceRange")
                                # Dirección
                                addr = restaurant.get("address", {})
                                if addr:
                                    parts = [
                                        addr.get("streetAddress", ""),
                                        addr.get("addressLocality", ""),
                                    ]
                                    rest_data["direccion"] = ", ".join(
                                        p for p in parts if p
                                    )
                                # Coordenadas
                                geo = restaurant.get("geo", {})
                                if geo:
                                    try:
                                        lat = float(geo.get("latitude", 0))
                                        lon = float(geo.get("longitude", 0))
                                        if validate_coordinates(lat, lon):
                                            rest_data["latitud"] = lat
                                            rest_data["longitud"] = lon
                                    except (ValueError, TypeError):
                                        pass
                                # Cocina
                                cuisine = restaurant.get("servesCuisine")
                                if cuisine:
                                    if isinstance(cuisine, list):
                                        rest_data["tipo_cocina"] = ", ".join(
                                            cuisine
                                        )
                                    else:
                                        rest_data["tipo_cocina"] = str(cuisine)
                                # Teléfono
                                tel = restaurant.get("telephone")
                                if tel:
                                    rest_data["telefono"] = tel

                                restaurants.append(rest_data)
                        return restaurants
                except (json.JSONDecodeError, ValueError, TypeError):
                    continue
        except Exception as e:
            logger.error(f"Error extrayendo JSON-LD: {e}")

        return restaurants

    def scrape(self, limit: Optional[int] = None) -> List[RestaurantData]:
        """Ejecuta el scraping completo de TripAdvisor con paginación.

        Extrae datos del JSON-LD embebido en cada página de listado.
        30 restaurantes por página, hasta 5 páginas = 150 máximo.
        """
        try:
            self.setup_driver()
            count = 0
            max_pages = config.TRIPADVISOR_MAX_PAGES

            for page in range(max_pages):
                if limit and count >= limit:
                    break

                if page == 0:
                    page_url = config.TRIPADVISOR_BASE_URL
                else:
                    offset = page * config.TRIPADVISOR_PER_PAGE
                    page_url = config.TRIPADVISOR_PAGE_URL.format(offset=offset)

                logger.info(f"TripAdvisor página {page + 1}: {page_url}")
                self.driver.get(page_url)
                wait_random(config.DELAY_TRIPADVISOR * 2)

                if page == 0:
                    self._dismiss_popups()

                # Esperar a que cargue la página
                try:
                    WebDriverWait(self.driver, config.TIMEOUT_SELENIUM).until(
                        EC.presence_of_element_located(
                            (By.CSS_SELECTOR, 'script[type="application/ld+json"]')
                        )
                    )
                except TimeoutException:
                    logger.warning(
                        f"No se cargó JSON-LD en página {page + 1}"
                    )
                    break

                wait_random(2.0)

                # Extraer datos del JSON-LD de la página de listado
                page_restaurants = self._extract_from_listing_jsonld()

                if not page_restaurants:
                    logger.info(
                        f"No hay más restaurantes en página {page + 1}"
                    )
                    break

                logger.info(
                    f"  Página {page + 1}: "
                    f"{len(page_restaurants)} restaurantes en JSON-LD"
                )

                for rest_data in page_restaurants:
                    if limit and count >= limit:
                        break

                    nombre = rest_data.get("nombre")
                    if not nombre:
                        continue

                    # Deduplicar
                    nombre_key = nombre.lower().strip()
                    if nombre_key in self._seen_names:
                        continue
                    self._seen_names.add(nombre_key)

                    # Limpiar URL
                    url = rest_data.get("url", "")
                    if url:
                        url = url.split("?")[0]

                    zona = self._detect_zona(rest_data.get("direccion"))

                    restaurant = RestaurantData(
                        nombre=nombre,
                        fuente="TripAdvisor",
                        url=url,
                        direccion=rest_data.get("direccion"),
                        telefono=rest_data.get("telefono"),
                        rating=rest_data.get("rating"),
                        num_resenas=rest_data.get("num_resenas"),
                        precio=rest_data.get("precio"),
                        tipo_cocina=rest_data.get("tipo_cocina"),
                        latitud=rest_data.get("latitud"),
                        longitud=rest_data.get("longitud"),
                        zona=zona,
                    )

                    self.results.append(restaurant)
                    count += 1
                    logger.info(
                        f"  Extraido: {nombre} "
                        f"(rating={rest_data.get('rating')}, "
                        f"resenas={rest_data.get('num_resenas')}, "
                        f"precio={rest_data.get('precio')})"
                    )

            logger.info(
                f"Scraping de TripAdvisor completo: "
                f"{len(self.results)} restaurantes"
            )
            return self.results

        except WebDriverException as e:
            logger.error(f"Error de WebDriver en TripAdvisor: {e}")
            return self.results
        except Exception as e:
            logger.error(f"Error en scraping de TripAdvisor: {e}")
            return self.results
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                except Exception:
                    pass
                logger.info("ChromeDriver cerrado (TripAdvisor)")
