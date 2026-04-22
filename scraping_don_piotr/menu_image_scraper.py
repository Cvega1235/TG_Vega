"""
menu_image_scraper.py
Enriquecimiento de datos: extrae texto de imágenes de menú de Google Maps
mediante OCR (pytesseract) y actualiza el campo menu_texto_ocr en PostgreSQL.

Requisitos del sistema:
    - Tesseract OCR instalado: https://github.com/UB-Mannheim/tesseract/wiki
      (marcar "Spanish" durante la instalación)
    - Paquetes Python: pip install -r requirements.txt

Requisitos de configuración:
    Crear scraping_don_piotr/.env con:
        DATABASE_URL=postgresql://don_piotr:password@localhost:5432/don_piotr_db

Uso:
    python menu_image_scraper.py              # procesa restaurantes sin OCR
    python menu_image_scraper.py --limit 50   # procesa solo 50
    python menu_image_scraper.py --force      # re-procesa todos
"""

import argparse
import io
import logging
import os
import time
import random
from datetime import datetime, timezone
from typing import Optional

import requests
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from sqlalchemy import create_engine, Column, Integer, Text, update
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Mapped, mapped_column
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("menu_ocr.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("menu_ocr")

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL no definida.\n"
        "Crea scraping_don_piotr/.env con:\n"
        "  DATABASE_URL=postgresql://don_piotr:password@localhost:5432/don_piotr_db"
    )

MAX_IMAGES_PER_RESTAURANT = 5
OCR_LANGUAGE = "spa"
WAIT_TIMEOUT = 10
DELAY_MIN = 2.0
DELAY_MAX = 4.0

# Selectores XPath para el tab de menú de Google Maps.
# Google Maps puede mostrar este tab como "Menú", "Carta" o "Menu"
# dependiendo de la región y versión del navegador.
MENU_TAB_XPATHS = [
    '//div[@role="tablist"]//button[.//span[normalize-space(text())="Carta"]]',
    '//div[@role="tablist"]//button[.//span[normalize-space(text())="Menú"]]',
    '//div[@role="tablist"]//button[.//span[normalize-space(text())="Menu"]]',
    '//button[@aria-label="Carta"]',
    '//button[@aria-label="Menú"]',
    '//button[normalize-space(.)="Carta"]',
    '//button[normalize-space(.)="Menú"]',
    '//div[@role="tab"][contains(normalize-space(.), "Carta")]',
    '//div[@role="tab"][contains(normalize-space(.), "Menú")]',
]

# Selectores CSS para imágenes dentro del tab de menú
MENU_IMG_SELECTORS = [
    'img[src*="googleusercontent.com"]',
    'img[src*="lh5.googleusercontent"]',
    'img[src*="lh3.googleusercontent"]',
]


# ---------------------------------------------------------------------------
# Modelo mínimo para acceso a la tabla restaurants
# ---------------------------------------------------------------------------
class Base(DeclarativeBase):
    pass


class Restaurant(Base):
    __tablename__ = "restaurants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    nombre: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    menu_texto_ocr: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


# ---------------------------------------------------------------------------
# OCR
# ---------------------------------------------------------------------------

def _preprocess_image(img: Image.Image) -> Image.Image:
    """Convierte a escala de grises y mejora contraste para OCR."""
    img = img.convert("L")
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.5)
    img = img.filter(ImageFilter.SHARPEN)
    return img


def _run_ocr(img: Image.Image) -> str:
    """Ejecuta OCR sobre una imagen y devuelve el texto limpio."""
    img = _preprocess_image(img)
    config = "--psm 3 --oem 3"
    text = pytesseract.image_to_string(img, lang=OCR_LANGUAGE, config=config)
    # Limpiar líneas vacías y espacios redundantes
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return " | ".join(lines)


def _download_image(url: str, cookies: dict) -> Optional[Image.Image]:
    """Descarga una imagen de Google Maps usando las cookies de sesión de Selenium."""
    # Aumentar resolución reemplazando parámetro de tamaño en la URL
    high_res_url = url.split("=w")[0] + "=w1200-h900" if "=w" in url else url
    try:
        resp = requests.get(
            high_res_url,
            cookies=cookies,
            timeout=15,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                "Referer": "https://www.google.com/maps/",
            },
        )
        if resp.status_code == 200 and resp.content:
            return Image.open(io.BytesIO(resp.content))
    except Exception as e:
        logger.debug(f"Error descargando imagen: {e}")
    return None


# ---------------------------------------------------------------------------
# Selenium
# ---------------------------------------------------------------------------

def _setup_driver() -> webdriver.Chrome:
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--lang=es")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(5)
    return driver


def _find_menu_tab(driver: webdriver.Chrome) -> Optional[object]:
    """Busca el botón de la pestaña 'Menú' con múltiples selectores."""
    for xpath in MENU_TAB_XPATHS:
        try:
            elem = driver.find_element(By.XPATH, xpath)
            return elem
        except NoSuchElementException:
            continue
    return None


def _extract_menu_images(driver: webdriver.Chrome) -> list[str]:
    """Extrae URLs de imágenes del tab Menú activo."""
    urls: list[str] = []
    seen: set[str] = set()

    for selector in MENU_IMG_SELECTORS:
        try:
            imgs = driver.find_elements(By.CSS_SELECTOR, selector)
            for img in imgs:
                src = img.get_attribute("src") or ""
                if (
                    src
                    and src.startswith("http")
                    and src not in seen
                    and len(urls) < MAX_IMAGES_PER_RESTAURANT
                ):
                    seen.add(src)
                    urls.append(src)
        except Exception:
            continue

        if urls:
            break

    return urls


def _get_ocr_text_for_restaurant(
    driver: webdriver.Chrome, maps_url: str
) -> Optional[str]:
    """
    Navega al restaurante en Google Maps, encuentra el tab Menú,
    descarga las imágenes y ejecuta OCR sobre ellas.

    Returns:
        Texto extraído concatenado, o None si no hay tab Menú o no hay imágenes.
    """
    try:
        driver.get(maps_url)
        time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))

        # Esperar que cargue la página del restaurante
        WebDriverWait(driver, WAIT_TIMEOUT).until(
            EC.presence_of_element_located((By.TAG_NAME, "h1"))
        )

        # Buscar tab Menú
        menu_tab = _find_menu_tab(driver)
        if not menu_tab:
            logger.debug("Tab 'Menú' no encontrado")
            return None

        # Hacer click en el tab
        driver.execute_script("arguments[0].click();", menu_tab)
        time.sleep(2.0)

        # Obtener cookies de sesión para descargar imágenes
        cookies = {c["name"]: c["value"] for c in driver.get_cookies()}

        # Extraer URLs de imágenes del menú
        img_urls = _extract_menu_images(driver)
        if not img_urls:
            logger.debug("No se encontraron imágenes en el tab Menú")
            return None

        # Descargar y procesar cada imagen con OCR
        textos: list[str] = []
        for url in img_urls:
            img = _download_image(url, cookies)
            if img is None:
                continue
            texto = _run_ocr(img)
            if texto:
                textos.append(texto)
                logger.debug(f"  OCR extrajo {len(texto)} caracteres")

        return " ".join(textos) if textos else None

    except TimeoutException:
        logger.warning(f"Timeout cargando {maps_url}")
        return None
    except Exception as e:
        logger.warning(f"Error procesando {maps_url}: {e}")
        return None


# ---------------------------------------------------------------------------
# Pipeline principal
# ---------------------------------------------------------------------------

def _check_tesseract() -> None:
    """Verifica que Tesseract OCR esté instalado antes de procesar.

    Falla inmediatamente si no está disponible para evitar que los
    restaurantes queden marcados como procesados sin haber extraído texto.
    """
    try:
        pytesseract.get_tesseract_version()
    except pytesseract.TesseractNotFoundError:
        raise SystemExit(
            "\n[ERROR] Tesseract OCR no está instalado o no está en el PATH.\n"
            "Pasos para instalarlo en Windows:\n"
            "  1. Descarga el instalador desde:\n"
            "     https://github.com/UB-Mannheim/tesseract/wiki\n"
            "  2. Durante la instalación, marca el idioma 'Spanish'\n"
            "  3. Agrega la ruta de instalación al PATH del sistema\n"
            "     (por defecto: C:\\Program Files\\Tesseract-OCR)\n"
            "  4. Reinicia la terminal y vuelve a ejecutar el script\n"
        )


def run(limit: Optional[int] = None, force: bool = False) -> dict:
    """
    Recorre los restaurantes con URL de Google Maps y ejecuta OCR
    sobre las imágenes de su tab Menú.

    Args:
        limit: Máximo de restaurantes a procesar.
        force: Si True, re-procesa restaurantes que ya tienen menu_texto_ocr.

    Returns:
        Resumen de la ejecución.
    """
    _check_tesseract()

    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db: Session = SessionLocal()

    try:
        query = db.query(Restaurant).filter(Restaurant.url.ilike("%google.com/maps%"))
        if not force:
            query = query.filter(Restaurant.menu_texto_ocr.is_(None))
        if limit:
            query = query.limit(limit)

        restaurants = query.all()
        total = len(restaurants)
        logger.info(f"Restaurantes a procesar: {total}")

        if total == 0:
            logger.info("Nada que procesar.")
            return {"procesados": 0, "con_menu": 0, "sin_menu": 0, "errores": 0}

        driver = _setup_driver()
        conteos = {"procesados": 0, "con_menu": 0, "sin_menu": 0, "errores": 0}

        try:
            for i, restaurant in enumerate(restaurants, 1):
                logger.info(
                    f"[{i}/{total}] Procesando: {restaurant.nombre} — {restaurant.url}"
                )
                try:
                    texto = _get_ocr_text_for_restaurant(driver, restaurant.url)

                    if texto:
                        restaurant.menu_texto_ocr = texto
                        conteos["con_menu"] += 1
                        logger.info(
                            f"  ✓ Texto extraído: {len(texto)} caracteres"
                        )
                    else:
                        # Marcar como procesado sin resultado para no re-intentar
                        restaurant.menu_texto_ocr = ""
                        conteos["sin_menu"] += 1
                        logger.info("  — Sin imágenes de menú")

                    db.commit()
                    conteos["procesados"] += 1

                except Exception as e:
                    logger.error(f"  Error inesperado: {e}")
                    db.rollback()
                    conteos["errores"] += 1

                # Pausa entre restaurantes para evitar bloqueos
                if i < total:
                    time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))

        finally:
            driver.quit()
            logger.info("ChromeDriver cerrado")

        logger.info(
            f"\nResumen OCR:"
            f"\n  Procesados : {conteos['procesados']}"
            f"\n  Con menú   : {conteos['con_menu']}"
            f"\n  Sin menú   : {conteos['sin_menu']}"
            f"\n  Errores    : {conteos['errores']}"
        )
        return conteos

    finally:
        db.close()


# ---------------------------------------------------------------------------
# Entrada desde línea de comandos
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extrae texto de imágenes de menú de Google Maps mediante OCR."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Número máximo de restaurantes a procesar (útil para pruebas).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-procesar restaurantes que ya tienen menu_texto_ocr.",
    )
    args = parser.parse_args()
    run(limit=args.limit, force=args.force)
