"""
config.py
Configuración global del módulo de web scraping
Sistema de Inteligencia de Mercado Don Piotr
"""

import os
from pathlib import Path

# ============================================================================
# CONFIGURACIÓN DE DIRECTORIOS
# ============================================================================

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
OUTPUT_DIR = BASE_DIR / "output"

# Crear directorios si no existen
for directory in [DATA_DIR, LOGS_DIR, OUTPUT_DIR]:
    directory.mkdir(exist_ok=True)

# ============================================================================
# CONFIGURACIÓN DE SCRAPING
# ============================================================================

# Delays entre peticiones (segundos)
DELAY_GMAPS = 3.0
DELAY_TRIPADVISOR = 2.0
DELAY_BOLIVIA = 1.5

# Timeouts
TIMEOUT_DEFAULT = 30
TIMEOUT_SELENIUM = 45

# Reintentos
MAX_RETRIES = 3
RETRY_DELAY = 2.0  # segundos entre reintentos

# User Agents (rotación)
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
]

# ============================================================================
# URLS BASE
# ============================================================================

# Google Maps - Búsqueda por zonas para cubrir toda la ciudad
GMAPS_SEARCH_TEMPLATE = "https://www.google.com/maps/search/{query}"
GMAPS_QUERIES = [
    "restaurantes+San+Miguel+La+Paz+Bolivia",
    "restaurantes+Calacoto+La+Paz+Bolivia",
    "restaurantes+Sopocachi+La+Paz+Bolivia",
    "restaurantes+Miraflores+La+Paz+Bolivia",
    "restaurantes+Zona+Sur+La+Paz+Bolivia",
    "restaurantes+Centro+La+Paz+Bolivia",
    "restaurantes+Obrajes+La+Paz+Bolivia",
    "restaurantes+Achumani+La+Paz+Bolivia",
    "restaurantes+Irpavi+La+Paz+Bolivia",
    "restaurantes+Cota+Cota+La+Paz+Bolivia",
    "restaurantes+Megacenter+La+Paz+Bolivia",
    "restaurantes+San+Pedro+La+Paz+Bolivia",
]

# TripAdvisor - Paginación con offset oa (30 por página)
TRIPADVISOR_BASE_URL = "https://www.tripadvisor.com/Restaurants-g294072-La_Paz_La_Paz_Department.html"
TRIPADVISOR_PAGE_URL = "https://www.tripadvisor.com/Restaurants-g294072-oa{offset}-La_Paz_La_Paz_Department.html"
TRIPADVISOR_MAX_PAGES = 5  # 5 páginas × 30 = 150 restaurantes
TRIPADVISOR_PER_PAGE = 30

# Bolivia en tus Manos
BOLIVIA_BASE_URL = "https://www.boliviaentusmanos.com/amarillas/932/{page}/lapaz/restaurantes.html"
BOLIVIA_MAX_PAGES = 5  # Número máximo de páginas a scrapear

# ============================================================================
# SELECTORES CSS/XPATH
# ============================================================================

# Google Maps Selectors
GMAPS_SELECTORS = {
    'nombre': 'h1.DUwDvf',
    'nombre_fallback': 'div[role="main"] h1',
    'direccion': 'div.Io6YIe',
    'direccion_fallback': 'button[data-item-id="address"]',
    'telefono': 'button[data-item-id*="phone"]',
    'telefono_fallback': 'div.AeaXub span',
    'rating': 'div.F7nice span[aria-hidden="true"]',
    'rating_fallback': 'div.jANrlb span',
    'num_resenas': 'div.HHrUdb',
    'num_resenas_fallback': 'div.HHrUdb span',
    'categoria': 'button.DkEaL',
    'categoria_fallback': 'button[jsaction*="category"]',
    'horarios': 'div[aria-label*="Horario"]',
    'lat_xpath': '//meta[@itemprop="latitude"]/@content',
    'lon_xpath': '//meta[@itemprop="longitude"]/@content',
    'website': 'a[data-item-id="authority"]',
    'website_fallback': 'a[aria-label*="Sitio web"]',
}

# TripAdvisor Selectors (listing page - Selenium)
TRIPADVISOR_SELECTORS = {
    # Listing page selectors
    'restaurant_link': 'a[href*="/Restaurant_Review-"]',
    'restaurant_card': 'div[data-test*="location-results-card"]',
    'results_container': 'div[data-test*="all-results-section"]',
    # Detail page selectors
    'nombre': 'h1[data-test-target="top-info-header"]',
    'nombre_fallback': 'div.acKDw h1',
    'rating': 'svg[aria-label*="burbujas"]',
    'rating_fallback': 'span[data-automation="bubbleRatingValue"]',
    'num_resenas': 'span.yyzcQ',
    'num_resenas_fallback': 'a[href*="Reviews"] span',
    'precio': 'a[href*="zfp"] span',
    'precio_fallback': 'div.price-range',
    'tipo_cocina': 'span.DsyBj',
    'tipo_cocina_fallback': 'div[data-test-target="cuisine"] span',
    'direccion': 'span.yEWoV',
    'direccion_fallback': 'span.fHvkI',
}

# Bolivia en tus Manos Selectors (estructura real del sitio)
BOLIVIA_SELECTORS = {
    'card_container': '#listado li',
    'nombre': 'div.par2 h2 a',
    'nombre_fallback': 'div.par2 h6 a',
    'direccion': 'p.descripcion.direccion',
    'descripcion': 'p.descripcion:not(.direccion)',
    'telefono_container': 'div.despliegue:not(.sociales)',
    'delivery': 'a.deli',
    'logo': 'img.logo',
}

# ============================================================================
# PARÁMETROS DE BÚSQUEDA
# ============================================================================

# Zonas prioritarias de La Paz
ZONAS_LA_PAZ = [
    "San Miguel",
    "Calacoto",
    "Sopocachi",
    "Miraflores",
    "Zona Sur",
    "Centro",
    "Obrajes",
    "Achumani",
    "Irpavi",
    "Cota Cota"
]

# Categorías de restaurantes
CATEGORIAS_BUSQUEDA = [
    "restaurantes",
    "cafes",
    "cafeterias",
    "comida rapida",
    "hoteles con restaurante"
]

# ============================================================================
# CONFIGURACIÓN DE LOGGING
# ============================================================================

LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
LOG_LEVEL = 'INFO'
LOG_FILE = LOGS_DIR / 'scraping.log'

# ============================================================================
# CONFIGURACIÓN DE SALIDA
# ============================================================================

# Formatos de exportación
EXPORT_CSV = True
EXPORT_JSON = True
EXPORT_SQLITE = True

# Nombres de archivos de salida
OUTPUT_CSV = OUTPUT_DIR / 'restaurantes_la_paz.csv'
OUTPUT_JSON = OUTPUT_DIR / 'restaurantes_la_paz.json'
OUTPUT_DB = OUTPUT_DIR / 'don_piotr.db'

# ============================================================================
# VALIDACIONES
# ============================================================================

# Rangos válidos
RATING_MIN = 0.0
RATING_MAX = 5.0

# Coordenadas válidas para La Paz
LAT_MIN = -17.0
LAT_MAX = -16.0
LON_MIN = -69.0
LON_MAX = -68.0

# Longitudes mínimas de texto
MIN_NOMBRE_LENGTH = 3
MIN_DIRECCION_LENGTH = 10
MIN_TELEFONO_LENGTH = 7
