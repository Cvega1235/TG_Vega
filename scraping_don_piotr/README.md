# Sistema de Web Scraping Don Piotr
## Módulo de Inteligencia de Mercado

### 📋 Descripción
Sistema modular de web scraping para extraer información de restaurantes en La Paz desde 3 fuentes:
- Google Maps (Selenium + BeautifulSoup)
- TripAdvisor (Requests + BeautifulSoup)  
- Bolivia en tus Manos (Requests + BeautifulSoup)

### 📁 Estructura del Proyecto
```
scraping_don_piotr/
├── config.py                 # Configuración global
├── logger.py                 # Sistema de logging
├── utils.py                  # Funciones utilitarias
├── gmaps_scraper.py         # Extractor Google Maps
├── tripadvisor_scraper.py   # Extractor TripAdvisor
├── bolivia_scraper.py       # Extractor Bolivia en tus Manos
├── data_processor.py        # Procesamiento y limpieza
├── storage_manager.py       # Almacenamiento
├── main.py                  # Orquestador principal
├── requirements.txt         # Dependencias
├── README.md               # Este archivo
├── data/                   # Datos temporales
├── logs/                   # Archivos de log
└── output/                # Archivos de salida
```

### 🔧 Instalación

```bash
# 1. Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Descargar ChromeDriver
# https://chromedriver.chromium.org/
```

### 🚀 Uso

```bash
# Ejecutar scraping completo
python main.py --all

# Ejecutar fuente específica
python main.py --source gmaps
python main.py --source tripadvisor
python main.py --source bolivia

# Con límite de registros (testing)
python main.py --all --limit 10
```

### 📊 Salidas
- CSV: `output/restaurantes_la_paz.csv`
- JSON: `output/restaurantes_la_paz.json`
- SQLite: `output/don_piotr.db`
- Logs: `logs/scraping.log`

### ⚙️ Configuración
Editar `config.py` para modificar:
- URLs base
- Selectores CSS/XPath
- Delays entre peticiones
- Timeouts
- Parámetros de validación

### 📝 Notas Importantes
- Respetar rate limiting (delays configurados)
- Verificar robots.txt de cada sitio
- Actualizar selectores si las páginas cambian
- Revisar logs ante errores
