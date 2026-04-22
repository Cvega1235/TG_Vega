"""
website_scraper.py
Enriquecimiento de datos: visita el sitio web propio de cada restaurante
y extrae texto para detectar productos Don Piotr (chorizo, jamón, tocino, etc.)

Estrategia de extracción:
    1. Intentar con requests + BeautifulSoup (rápido, sin JS)
    2. Si el texto extraído es muy corto (<200 caracteres), reintentar con
       Selenium (más lento, pero ejecuta JavaScript)
    3. Registrar el resultado en los campos website_texto / tiene_embutidos
       / productos_detectados de la BD.

Dominios ignorados (redes sociales / plataformas que no son el sitio propio):
    facebook.com, instagram.com, twitter.com, tiktok.com, youtube.com,
    wa.me, t.me, linkedin.com, tripadvisor.com, google.com

Uso:
    python website_scraper.py              # procesa restaurantes con website_url sin texto aún
    python website_scraper.py --limit 20   # procesa solo 20
    python website_scraper.py --force      # re-procesa todos (incluyendo ya procesados)
"""

import argparse
import logging
import os
import random
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Path y configuración
# ---------------------------------------------------------------------------
project_root = Path(__file__).resolve().parent.parent
backend_dir = project_root / "sis_TG" / "backend"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(backend_dir))

load_dotenv(backend_dir / ".env")

from app.database import SessionLocal  # noqa: E402
from app.restaurants.models import Restaurant  # noqa: E402
from scraping_don_piotr.menu_analyzer import detectar_productos, inferir_por_cocina  # noqa: E402

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("website_scraper.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("website_scraper")

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------
REQUEST_TIMEOUT = 15
SELENIUM_TIMEOUT = 20
DELAY_MIN = 1.5
DELAY_MAX = 3.5
MIN_TEXT_LENGTH = 200   # Si requests devuelve menos chars, intentar con Selenium

# Dominios que no son sitios propios del restaurante
IGNORED_DOMAINS = {
    "facebook.com", "instagram.com", "twitter.com", "x.com",
    "tiktok.com", "youtube.com", "wa.me", "t.me", "telegram.me",
    "linkedin.com", "tripadvisor.com", "google.com", "maps.google.com",
    "waze.com", "yelp.com", "zomato.com", "ubereats.com", "pedidosya.com",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-BO,es;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_social_or_platform(url: str) -> bool:
    """Retorna True si la URL pertenece a una red social u otra plataforma."""
    try:
        domain = urlparse(url).netloc.lower().lstrip("www.")
        return any(domain == d or domain.endswith("." + d) for d in IGNORED_DOMAINS)
    except Exception:
        return False


def _extract_text_with_requests(url: str) -> Optional[str]:
    """Intenta extraer texto con requests + BeautifulSoup.

    Returns:
        Texto extraído o None si falla.
    """
    try:
        resp = requests.get(
            url,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
            verify=False,           # Algunos sitios tienen SSL vencido
            allow_redirects=True,
        )
        resp.raise_for_status()

        # Detectar si la respuesta es HTML
        content_type = resp.headers.get("Content-Type", "")
        if "text/html" not in content_type and "text/plain" not in content_type:
            return None

        soup = BeautifulSoup(resp.content, "html.parser")

        # Eliminar scripts, estilos y metadatos
        for tag in soup(["script", "style", "meta", "noscript", "head"]):
            tag.decompose()

        text = soup.get_text(separator=" ", strip=True)
        # Colapsar espacios múltiples
        text = re.sub(r"\s+", " ", text).strip()
        return text if text else None

    except requests.exceptions.SSLError:
        # Reintentar sin verificación SSL (ya está desactivada arriba, pero
        # por si ocurre otro error SSL específico)
        logger.debug(f"SSL error en {url}, ya se usa verify=False")
        return None
    except requests.exceptions.Timeout:
        logger.debug(f"Timeout en {url}")
        return None
    except requests.exceptions.TooManyRedirects:
        logger.debug(f"Demasiadas redirecciones en {url}")
        return None
    except requests.exceptions.ConnectionError:
        logger.debug(f"Error de conexión en {url}")
        return None
    except Exception as e:
        logger.debug(f"Error requests en {url}: {e}")
        return None


def _extract_text_with_selenium(url: str) -> Optional[str]:
    """Extrae texto usando Selenium (para sitios con JavaScript pesado).

    Returns:
        Texto extraído o None si falla.
    """
    try:
        from selenium import webdriver
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.common.by import By
        from selenium.common.exceptions import TimeoutException, WebDriverException

        options = webdriver.ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument(f"user-agent={HEADERS['User-Agent']}")
        options.add_argument("--lang=es")

        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(SELENIUM_TIMEOUT)

        try:
            driver.get(url)
            # Esperar a que cargue algo de contenido
            try:
                WebDriverWait(driver, SELENIUM_TIMEOUT).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
            except TimeoutException:
                pass

            time.sleep(2)  # Dar tiempo al JS para renderizar
            page_source = driver.page_source

            soup = BeautifulSoup(page_source, "html.parser")
            for tag in soup(["script", "style", "meta", "noscript", "head"]):
                tag.decompose()

            text = soup.get_text(separator=" ", strip=True)
            text = re.sub(r"\s+", " ", text).strip()
            return text if text else None

        except WebDriverException as e:
            logger.debug(f"Selenium WebDriver error en {url}: {e}")
            return None
        finally:
            driver.quit()

    except ImportError:
        logger.warning("Selenium no disponible para fallback JS")
        return None
    except Exception as e:
        logger.debug(f"Error Selenium en {url}: {e}")
        return None


def scrape_website(url: str) -> tuple[Optional[str], str]:
    """Extrae el texto de un sitio web con estrategia requests → Selenium fallback.

    Args:
        url: URL del sitio web del restaurante.

    Returns:
        (texto_extraido, metodo_usado)
        texto_extraido: str con el contenido o None si no se pudo extraer.
        metodo_usado: "requests", "selenium", o "no_accesible".
    """
    if _is_social_or_platform(url):
        logger.debug(f"Ignorado (red social / plataforma): {url}")
        return None, "red_social"

    # Intento 1: requests
    texto = _extract_text_with_requests(url)
    if texto and len(texto) >= MIN_TEXT_LENGTH:
        return texto, "requests"

    # Si requests devolvió poco texto, intentar con Selenium
    logger.debug(f"Texto corto ({len(texto) if texto else 0} chars), intentando Selenium: {url}")
    texto_selenium = _extract_text_with_selenium(url)
    if texto_selenium and len(texto_selenium) >= MIN_TEXT_LENGTH:
        return texto_selenium, "selenium"

    # Si Selenium tampoco dio resultados pero requests sí dio algo, usar ese
    if texto:
        return texto, "requests"

    return None, "no_accesible"


# ---------------------------------------------------------------------------
# Pipeline principal
# ---------------------------------------------------------------------------

def run(limit: Optional[int] = None, force: bool = False) -> dict:
    """Recorre los restaurantes con website_url y extrae texto de sus sitios.

    Args:
        limit: Máximo de restaurantes a procesar.
        force: Si True, re-procesa restaurantes que ya tienen website_texto.

    Returns:
        Resumen de la ejecución.
    """
    # Suprimir advertencias SSL de urllib3
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    db = SessionLocal()
    stats = {
        "procesados": 0,
        "con_texto": 0,
        "con_productos": 0,
        "no_accesibles": 0,
        "redes_sociales": 0,
        "errores": 0,
    }

    try:
        query = db.query(Restaurant).filter(Restaurant.website_url.isnot(None))
        if not force:
            query = query.filter(Restaurant.website_scrapeado_at.is_(None))
        if limit:
            query = query.limit(limit)

        restaurants = query.all()
        total = len(restaurants)
        logger.info(f"Restaurantes con sitio web a procesar: {total}")

        if total == 0:
            logger.info("Nada que procesar.")
            return stats

        for i, restaurant in enumerate(restaurants, 1):
            logger.info(
                f"[{i}/{total}] {restaurant.nombre} → {restaurant.website_url}"
            )
            try:
                texto, metodo = scrape_website(restaurant.website_url)

                if metodo == "red_social":
                    stats["redes_sociales"] += 1
                    # Marcar para no reintentar
                    restaurant.website_texto = ""
                    restaurant.website_scrapeado_at = datetime.now(timezone.utc)
                    db.commit()
                    continue

                if not texto:
                    stats["no_accesibles"] += 1
                    restaurant.website_texto = ""
                    restaurant.website_scrapeado_at = datetime.now(timezone.utc)
                    db.commit()
                    logger.info(f"  — No accesible ({metodo})")
                    continue

                # Guardar texto extraído
                restaurant.website_texto = texto
                restaurant.website_scrapeado_at = datetime.now(timezone.utc)
                stats["con_texto"] += 1
                logger.info(f"  ✓ Texto extraído: {len(texto)} chars (vía {metodo})")

                # Detectar productos Don Piotr en el texto del sitio
                productos = detectar_productos(texto)
                if not productos:
                    productos = inferir_por_cocina(
                        restaurant.tipo_cocina, restaurant.categoria
                    )

                if productos:
                    stats["con_productos"] += 1
                    productos_str = ", ".join(productos)
                    # Agregar al campo existente si ya había productos detectados
                    if restaurant.productos_detectados:
                        existentes = set(restaurant.productos_detectados.split(", "))
                        nuevos = set(productos_str.split(", "))
                        restaurant.productos_detectados = ", ".join(existentes | nuevos)
                    else:
                        restaurant.productos_detectados = productos_str
                    restaurant.tiene_embutidos = True
                    logger.info(f"  ✓ Productos detectados: {productos_str}")

                db.commit()
                stats["procesados"] += 1

            except Exception as e:
                logger.error(f"  Error inesperado: {e}")
                db.rollback()
                stats["errores"] += 1

            # Pausa entre sitios
            if i < total:
                time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))

    finally:
        db.close()

    logger.info(
        f"\nResumen scraping de sitios web:"
        f"\n  Procesados        : {stats['procesados']}"
        f"\n  Con texto         : {stats['con_texto']}"
        f"\n  Con productos     : {stats['con_productos']}"
        f"\n  No accesibles     : {stats['no_accesibles']}"
        f"\n  Redes sociales    : {stats['redes_sociales']}"
        f"\n  Errores           : {stats['errores']}"
    )
    return stats


# ---------------------------------------------------------------------------
# Entrada desde línea de comandos
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extrae texto de sitios web propios de restaurantes y detecta productos Don Piotr."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Número máximo de restaurantes a procesar.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-procesar restaurantes que ya tienen website_texto.",
    )
    args = parser.parse_args()

    logger.info("Iniciando scraping de sitios web de restaurantes...")
    stats = run(limit=args.limit, force=args.force)

    print("\n" + "=" * 60)
    print("RESULTADO DEL SCRAPING DE SITIOS WEB")
    print("=" * 60)
    for key, val in stats.items():
        print(f"  {key:<20}: {val}")
    print("=" * 60)
