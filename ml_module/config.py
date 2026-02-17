"""
config.py
Configuración del módulo de Machine Learning.
Sistema de Inteligencia de Mercado Don Piotr
"""

from pathlib import Path

# ============================================================================
# RUTAS
# ============================================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "ml_module" / "output"

# Ruta al archivo CSV de clientes actuales de Don Piotr
ICP_DATA_PATH = DATA_DIR / "clientes_actuales.csv"

# ============================================================================
# DEFINICIÓN DE FEATURES
# ============================================================================

# Features numéricos que se estandarizan con z-score
NUMERIC_FEATURES = ["rating", "num_resenas", "latitud", "longitud"]

# Features categóricos que se codifican con one-hot encoding
CATEGORICAL_FEATURES = ["tipo_cocina", "zona", "precio"]

# Features binarios derivados de la presencia/ausencia de datos
BINARY_FEATURES = [
    "has_phone",
    "has_address",
    "has_coordinates",
    "has_description",
]

# ============================================================================
# HIPERPARÁMETROS DE CLUSTERING
# ============================================================================

# Rango de K a evaluar para K-means
K_RANGE = range(2, 11)

# Semilla para reproducibilidad
RANDOM_STATE = 42

# Número de inicializaciones de K-means
N_INIT = 10

# ============================================================================
# PESOS DEL SCORE COMPUESTO
# ============================================================================

# Score = ICP_WEIGHT * similitud_ICP + CLUSTER_WEIGHT * score_cluster
ICP_SIMILARITY_WEIGHT = 0.6
CLUSTER_SCORE_WEIGHT = 0.4

# ============================================================================
# UMBRALES DE VALIDACIÓN
# ============================================================================

# Coeficiente de Silhouette mínimo aceptable
MIN_SILHOUETTE = 0.5

# ============================================================================
# IMPUTACIÓN
# ============================================================================

# Valores por defecto para imputación de categorías faltantes
DEFAULT_CUISINE = "Desconocido"
DEFAULT_ZONE = "Desconocido"
DEFAULT_PRICE = "$$"
