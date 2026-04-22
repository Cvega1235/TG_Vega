"""
bolivia_scraper.py
Extractor de datos de restaurantes desde Bolivia en tus Manos.
Sistema de Inteligencia de Mercado Don Piotr

Estructura real del sitio (verificada 2026-02):
    <li>
      <div class="par1"><img class="logo" ...></div>
      <div class="par2">
        <h2><a href="...">NOMBRE RESTAURANTE</a></h2>
        <div class="direccion">Calle, Zona - Ciudad</div>
        <div class="descripcion">Texto descriptivo...</div>
        <div class="mas">
          <button onclick="mostrarSeleccionT(...)">Teléfono</button>
          <div class="despliegue">2794518</div>
          <button onclick="mostrarSeleccionC(...)">Celular</button>
          <div class="despliegue">(591) 61207683</div>
        </div>
      </div>
    </li>

URL pattern: /amarillas/932/{page}/lapaz/restaurantes.html
"""

from typing import Callable, List, Optional

import requests
from bs4 import BeautifulSoup

from scraping_don_piotr import config
from scraping_don_piotr.base_scraper import BaseScraper, RestaurantData
from scraping_don_piotr.logger import logger
from scraping_don_piotr.utils import (
    clean_text,
    get_random_user_agent,
    normalize_phone,
    retry,
    wait_random,
)


class BoliviaEnTusManosScraper(BaseScraper):
    """Extractor de restaurantes desde Bolivia en tus Manos.

    Utiliza requests + BeautifulSoup para extraer datos de restaurantes
    desde el directorio de negocios boliviano (páginas amarillas).
    """

    def __init__(self) -> None:
        super().__init__()
        self.session = requests.Session()
        self._update_user_agent()

    def _update_user_agent(self) -> None:
        """Rota el User-Agent de la sesión."""
        self.session.headers.update({"User-Agent": get_random_user_agent()})

    @retry(max_retries=config.MAX_RETRIES, base_delay=config.RETRY_DELAY)
    def _fetch_page(self, url: str) -> requests.Response:
        """Realiza una petición HTTP con retry automático.

        Args:
            url: URL a solicitar.

        Returns:
            Objeto Response de la petición.

        Raises:
            requests.RequestException: Si falla después de todos los reintentos.
        """
        self._update_user_agent()
        response = self.session.get(url, timeout=config.TIMEOUT_DEFAULT)
        response.raise_for_status()
        return response

    def _extract_phones(self, card: BeautifulSoup) -> Optional[str]:
        """Extrae teléfonos de los divs ocultos 'despliegue'.

        Los teléfonos están dentro de <div class="despliegue"> que contienen
        <ul class="lista"><li>NUMERO</li></ul>.
        Se ignoran los divs con clase 'sociales' (redes sociales).

        Args:
            card: Elemento BeautifulSoup de la tarjeta <li>.

        Returns:
            Primer teléfono normalizado o None.
        """
        phone_divs = card.select(config.BOLIVIA_SELECTORS["telefono_container"])
        for div in phone_divs:
            # Buscar el número dentro de <li> para evitar concatenar múltiples
            li = div.select_one("ul.lista li")
            if li:
                raw = clean_text(li.text)
            else:
                raw = clean_text(div.text)
            if not raw:
                continue
            phone = normalize_phone(raw)
            if phone:
                return phone
        return None

    def _extract_detail_url(self, card: BeautifulSoup) -> Optional[str]:
        """Extrae la URL de detalle del restaurante.

        Args:
            card: Elemento BeautifulSoup de la tarjeta <li>.

        Returns:
            URL completa del detalle o None.
        """
        link = card.select_one(config.BOLIVIA_SELECTORS["nombre"])
        if not link:
            link = card.select_one(config.BOLIVIA_SELECTORS["nombre_fallback"])
        if link and link.get("href"):
            href = link["href"]
            if href.startswith("http"):
                return href
            return f"https://www.boliviaentusmanos.com{href}"
        return None

    def _detect_zona(self, direccion: str) -> Optional[str]:
        """Detecta la zona de La Paz a partir de la dirección.

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

    def extract_restaurant_data(
        self, card: BeautifulSoup
    ) -> Optional[RestaurantData]:
        """Extrae datos de una tarjeta <li> de restaurante.

        Args:
            card: Elemento BeautifulSoup <li> con datos del restaurante.

        Returns:
            RestaurantData con los datos extraídos o None si falla.
        """
        try:
            # Nombre (requerido)
            nombre_elem = card.select_one(config.BOLIVIA_SELECTORS["nombre"])
            if not nombre_elem:
                nombre_elem = card.select_one(
                    config.BOLIVIA_SELECTORS["nombre_fallback"]
                )
            if not nombre_elem:
                return None

            nombre = clean_text(nombre_elem.text)
            if not nombre:
                return None

            # URL de detalle
            url = self._extract_detail_url(card)

            # Dirección (p con ambas clases: descripcion y direccion)
            dir_elem = card.select_one("p.descripcion.direccion")
            direccion = clean_text(dir_elem.text) if dir_elem else None

            # Zona (detectada desde dirección)
            zona = self._detect_zona(direccion) if direccion else None

            # Teléfono (desde divs ocultos)
            telefono = self._extract_phones(card)

            # Descripción (p.descripcion que NO tiene clase direccion)
            descripcion = None
            categoria = None
            for p in card.select("p.descripcion"):
                if "direccion" not in (p.get("class") or []):
                    descripcion = clean_text(p.text)
                    if descripcion:
                        categoria = descripcion.split(".")[0].strip()
                    break

            # Servicios (delivery)
            delivery_elem = card.select_one("a.deli")
            servicios = "Delivery" if delivery_elem else None

            restaurant = RestaurantData(
                nombre=nombre,
                fuente="Bolivia en tus Manos",
                url=url,
                direccion=direccion,
                telefono=telefono,
                categoria=categoria,
                descripcion=descripcion,
                servicios=servicios,
                zona=zona,
            )

            logger.info(f"Extraido: {nombre}")
            return restaurant

        except Exception as e:
            logger.error(f"Error extrayendo tarjeta: {e}")
            return None

    def scrape(
        self,
        limit: Optional[int] = None,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
    ) -> List[RestaurantData]:
        """Ejecuta el scraping completo de Bolivia en tus Manos.

        Recorre múltiples páginas del directorio de restaurantes.

        Args:
            limit: Número máximo de restaurantes a extraer.
            progress_callback: Función opcional (mensaje, paso_actual, total_pasos).

        Returns:
            Lista de RestaurantData con los datos extraídos.
        """
        count = 0
        max_pages = config.BOLIVIA_MAX_PAGES

        for page in range(1, max_pages + 1):
            if limit and count >= limit:
                break

            if progress_callback:
                progress_callback(f"Bolivia en tus Manos: página {page}", page, max_pages)

            try:
                url = config.BOLIVIA_BASE_URL.format(page=page)
                logger.info(f"Scrapeando página {page}: {url}")

                response = self._fetch_page(url)
                soup = BeautifulSoup(response.content, "html.parser")

                # Extraer tarjetas de restaurantes
                cards = soup.select(config.BOLIVIA_SELECTORS["card_container"])

                if not cards:
                    logger.info(
                        f"No se encontraron restaurantes en página {page}. "
                        f"Fin de paginación."
                    )
                    break

                logger.info(
                    f"Página {page}: {len(cards)} restaurantes encontrados"
                )

                for card in cards:
                    if limit and count >= limit:
                        break

                    data = self.extract_restaurant_data(card)
                    if data:
                        self.results.append(data)
                        count += 1

                wait_random(config.DELAY_BOLIVIA)

            except Exception as e:
                logger.error(
                    f"Error en página {page} de Bolivia en tus Manos: {e}"
                )
                continue

        logger.info(
            f"Scraping de Bolivia en tus Manos completo: "
            f"{len(self.results)} restaurantes en {page} páginas"
        )
        return self.results
