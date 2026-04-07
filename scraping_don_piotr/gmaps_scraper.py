"""
gmaps_scraper.py
Extractor de datos de restaurantes desde Google Maps usando Selenium.
Sistema de Inteligencia de Mercado Don Piotr

Estrategia: Busca por cada zona de La Paz para cubrir toda la ciudad,
eliminando duplicados entre zonas.
"""

from typing import Dict, List, Optional, Set

from selenium import webdriver
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
    clean_text,
    extract_number,
    get_random_user_agent,
    normalize_phone,
    validate_coordinates,
    wait_random,
)


class GoogleMapsScraper(BaseScraper):
    """Extractor de restaurantes desde Google Maps.

    Utiliza Selenium para navegar la interfaz dinámica de Google Maps,
    buscando por cada zona de La Paz para cubrir toda la ciudad.
    """

    def __init__(self, headless: bool = False) -> None:
        super().__init__()
        self.driver: Optional[webdriver.Chrome] = None
        self.headless = headless
        self._seen_names: Set[str] = set()

    def setup_driver(self) -> None:
        """Configura el driver de Selenium con opciones anti-detección."""
        options = webdriver.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument(f"user-agent={get_random_user_agent()}")
        options.add_argument("--lang=es")

        if self.headless:
            options.add_argument("--headless=new")

        self.driver = webdriver.Chrome(options=options)
        self.driver.implicitly_wait(10)
        logger.info("ChromeDriver iniciado correctamente")

    def _safe_find(
        self,
        selector: str,
        fallback_selector: Optional[str] = None,
        attribute: Optional[str] = None,
    ) -> Optional[str]:
        """Busca un elemento con selector CSS, usando fallback si falla.

        Args:
            selector: Selector CSS principal.
            fallback_selector: Selector CSS alternativo.
            attribute: Atributo a extraer. Si None, extrae texto.

        Returns:
            Texto o atributo extraído, o None si no se encuentra.
        """
        for sel in [selector, fallback_selector]:
            if sel is None:
                continue
            try:
                elem = self.driver.find_element(By.CSS_SELECTOR, sel)
                raw = elem.get_attribute(attribute) if attribute else elem.text
                return clean_text(raw)
            except NoSuchElementException:
                continue
        return None

    def _extract_coordinates(self) -> Dict[str, Optional[float]]:
        """Extrae coordenadas GPS desde la URL actual del navegador.

        Returns:
            Dict con 'latitud' y 'longitud' (pueden ser None).
        """
        coords: Dict[str, Optional[float]] = {
            "latitud": None,
            "longitud": None,
        }
        try:
            url = self.driver.current_url
            if "@" in url:
                parts = url.split("@")[1].split(",")[:2]
                lat, lon = float(parts[0]), float(parts[1])
                if validate_coordinates(lat, lon):
                    coords["latitud"] = lat
                    coords["longitud"] = lon
        except (ValueError, IndexError, TypeError) as e:
            logger.debug(f"No se pudieron extraer coordenadas: {e}")

        return coords

    def _detect_zona(self, direccion: Optional[str]) -> Optional[str]:
        """Detecta la zona de La Paz desde la dirección.

        Args:
            direccion: Texto de dirección del restaurante.

        Returns:
            Nombre de la zona detectada o None.
        """
        if not direccion:
            return None
        direccion_lower = direccion.lower()
        for zona in config.ZONAS_LA_PAZ:
            if zona.lower() in direccion_lower:
                return zona
        return None

    def extract_restaurant_data(self, url: str, zona_fallback: Optional[str] = None) -> Optional[RestaurantData]:
        """Extrae datos de un restaurante individual de Google Maps.

        Args:
            url: URL del restaurante en Google Maps.

        Returns:
            RestaurantData o None si falla o es duplicado.
        """
        try:
            self.driver.get(url)
            wait_random(config.DELAY_GMAPS)

            WebDriverWait(self.driver, config.TIMEOUT_SELENIUM).until(
                EC.presence_of_element_located((By.TAG_NAME, "h1"))
            )

            # Nombre (requerido)
            nombre = self._safe_find(
                config.GMAPS_SELECTORS["nombre"],
                config.GMAPS_SELECTORS["nombre_fallback"],
            )
            if not nombre:
                return None

            # Deduplicar entre zonas
            nombre_key = nombre.lower().strip()
            if nombre_key in self._seen_names:
                logger.debug(f"Duplicado ignorado: {nombre}")
                return None
            self._seen_names.add(nombre_key)

            # Dirección
            direccion = self._safe_find(
                config.GMAPS_SELECTORS["direccion"],
            )
            # Fallback: botón con aria-label (estructura antigua)
            if not direccion:
                direccion = self._safe_find(
                    config.GMAPS_SELECTORS["direccion_fallback"],
                    attribute="aria-label",
                )
            # Limpiar prefijo "Dirección: " si existe
            if direccion and direccion.lower().startswith("dirección:"):
                direccion = direccion[len("dirección:"):].strip()

            # Zona
            zona = self._detect_zona(direccion) or zona_fallback

            # Teléfono
            telefono_raw = self._safe_find(
                config.GMAPS_SELECTORS["telefono"],
                config.GMAPS_SELECTORS["telefono_fallback"],
                attribute="aria-label",
            )
            telefono = None
            if telefono_raw:
                # Limpiar prefijo "Teléfono: "
                if ":" in telefono_raw:
                    telefono_raw = telefono_raw.split(":", 1)[1].strip()
                telefono = normalize_phone(telefono_raw)

            # Rating
            rating_text = self._safe_find(
                config.GMAPS_SELECTORS["rating"],
                config.GMAPS_SELECTORS["rating_fallback"],
            )
            rating = extract_number(rating_text) if rating_text else None

            # Número de reseñas
            resenas_text = self._safe_find(
                config.GMAPS_SELECTORS["num_resenas"],
                config.GMAPS_SELECTORS["num_resenas_fallback"],
            )
            num_resenas = None
            if resenas_text:
                num = extract_number(resenas_text)
                if num is not None:
                    num_resenas = int(num)

            # Categoría
            categoria = self._safe_find(
                config.GMAPS_SELECTORS["categoria"],
                config.GMAPS_SELECTORS["categoria_fallback"],
            )

            # Coordenadas
            coords = self._extract_coordinates()

            restaurant = RestaurantData(
                nombre=nombre,
                fuente="Google Maps",
                url=self.driver.current_url,
                direccion=direccion,
                telefono=telefono,
                rating=rating,
                num_resenas=num_resenas,
                latitud=coords["latitud"],
                longitud=coords["longitud"],
                categoria=categoria,
                zona=zona,
            )

            logger.info(f"Extraido: {nombre}")
            return restaurant

        except TimeoutException:
            logger.warning(f"Timeout esperando carga de {url}")
            return None
        except Exception as e:
            logger.error(f"Error extrayendo datos de {url}: {e}")
            return None

    def _scroll_results(self) -> None:
        """Hace scroll en el panel de resultados para cargar más restaurantes."""
        try:
            results_container = self.driver.find_element(
                By.CSS_SELECTOR, 'div[role="feed"]'
            )
            last_count = 0
            stable_rounds = 0

            for i in range(20):
                self.driver.execute_script(
                    "arguments[0].scrollTop = arguments[0].scrollHeight",
                    results_container,
                )
                wait_random(1.5)

                # Verificar si se cargaron nuevos resultados
                links = self.driver.find_elements(
                    By.CSS_SELECTOR, 'a[href*="/maps/place/"]'
                )
                current_count = len(links)

                if current_count == last_count:
                    stable_rounds += 1
                    if stable_rounds >= 3:
                        logger.info(
                            f"Scroll completado: no más resultados "
                            f"después de {i + 1} scrolls ({current_count} links)"
                        )
                        break
                else:
                    stable_rounds = 0
                    last_count = current_count

                logger.debug(
                    f"Scroll {i + 1}: {current_count} links encontrados"
                )

        except NoSuchElementException:
            logger.warning("No se encontró contenedor de resultados")

    def _collect_restaurant_urls(self) -> List[str]:
        """Recolecta URLs únicas de restaurantes del panel de resultados.

        Returns:
            Lista de URLs de restaurantes sin duplicados.
        """
        urls: List[str] = []
        seen: Set[str] = set()

        link_elements = self.driver.find_elements(
            By.CSS_SELECTOR, 'a[href*="/maps/place/"]'
        )

        for elem in link_elements:
            href = elem.get_attribute("href")
            if href and "/maps/place/" in href and href not in seen:
                seen.add(href)
                urls.append(href)

        return urls

    def _restart_driver(self) -> None:
        """Reinicia el driver de Chrome (para evitar crashes por sesiones largas)."""
        try:
            if self.driver:
                self.driver.quit()
        except Exception:
            pass
        self.setup_driver()

    def _scrape_zone(self, query: str, limit_per_zone: Optional[int]) -> int:
        """Scrapea una zona específica de La Paz.

        Usa un driver fresco para cada zona para evitar crashes.

        Args:
            query: Query de búsqueda para Google Maps.
            limit_per_zone: Máximo de restaurantes por zona.

        Returns:
            Número de restaurantes nuevos extraídos en esta zona.
        """
        url = config.GMAPS_SEARCH_TEMPLATE.format(query=query)
        zona_name = query.replace("+", " ").replace("restaurantes ", "")
        # Extraer solo el nombre de zona (sin " La Paz Bolivia")
        zona_fallback = zona_name.replace(" La Paz Bolivia", "").strip()

        try:
            # Driver fresco para cada zona
            self._restart_driver()

            logger.info(f"Buscando en: {zona_name}")
            self.driver.get(url)
            wait_random(config.DELAY_GMAPS * 2)

            # Aceptar cookies si aparece el diálogo
            try:
                accept_btn = self.driver.find_element(
                    By.CSS_SELECTOR, 'button[aria-label*="Aceptar"]'
                )
                accept_btn.click()
                wait_random(1.0)
            except NoSuchElementException:
                pass

            self._scroll_results()
            restaurant_urls = self._collect_restaurant_urls()

            logger.info(
                f"  {zona_name}: {len(restaurant_urls)} restaurantes encontrados"
            )

            count = 0
            for rest_url in restaurant_urls:
                if limit_per_zone and count >= limit_per_zone:
                    break

                try:
                    data = self.extract_restaurant_data(rest_url, zona_fallback=zona_fallback)
                    if data:
                        self.results.append(data)
                        count += 1
                except Exception as e:
                    logger.warning(f"Error en restaurante individual: {e}")
                    break

            return count

        except Exception as e:
            logger.error(f"Error scrapeando zona {zona_name}: {e}")
            return 0

    def scrape(self, limit: Optional[int] = None) -> List[RestaurantData]:
        """Ejecuta el scraping de Google Maps por zonas de La Paz.

        Busca en cada zona configurada para cubrir toda la ciudad,
        eliminando duplicados entre zonas. Reinicia el driver por zona.

        Args:
            limit: Número máximo total de restaurantes a extraer.

        Returns:
            Lista de RestaurantData con los datos extraídos.
        """
        try:
            total = 0
            for query in config.GMAPS_QUERIES:
                if limit and total >= limit:
                    break

                remaining = (limit - total) if limit else None
                count = self._scrape_zone(query, remaining)
                total += count

                logger.info(
                    f"  Zona completada: +{count} nuevos "
                    f"(total: {len(self.results)})"
                )

            logger.info(
                f"Scraping de Google Maps completo: "
                f"{len(self.results)} restaurantes únicos "
                f"en {len(config.GMAPS_QUERIES)} zonas"
            )
            return self.results

        except Exception as e:
            logger.error(f"Error en scraping de Google Maps: {e}")
            return self.results
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                except Exception:
                    pass
                logger.info("ChromeDriver cerrado")
