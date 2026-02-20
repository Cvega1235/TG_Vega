"""
utils.py
Funciones utilitarias para scraping.
Sistema de Inteligencia de Mercado Don Piotr
"""

import functools
import time
import random
import re
from typing import Any, Callable, Optional, TypeVar

from scraping_don_piotr import config
from scraping_don_piotr.logger import logger

F = TypeVar("F", bound=Callable[..., Any])


def retry(
    max_retries: int = config.MAX_RETRIES,
    base_delay: float = config.RETRY_DELAY,
    exceptions: tuple = (Exception,),
) -> Callable[[F], F]:
    """Decorador que reintenta una función ante excepciones con backoff exponencial.

    Args:
        max_retries: Número máximo de reintentos.
        base_delay: Delay base entre reintentos (se multiplica por el intento).
        exceptions: Tupla de excepciones que activan el reintento.

    Returns:
        Función decorada con lógica de reintento.
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_retries:
                        logger.error(
                            f"{func.__name__} falló después de {max_retries} "
                            f"intentos: {e}"
                        )
                        raise
                    delay = base_delay * attempt
                    logger.warning(
                        f"{func.__name__} intento {attempt}/{max_retries} "
                        f"falló: {e}. Reintentando en {delay:.1f}s..."
                    )
                    wait_random(delay)
            return None

        return wrapper  # type: ignore[return-value]

    return decorator

def get_random_user_agent() -> str:
    """Retorna un User-Agent aleatorio"""
    return random.choice(config.USER_AGENTS)

def wait_random(base_delay: float, variance: float = 0.5):
    """
    Espera un tiempo aleatorio
    
    Args:
        base_delay: Tiempo base en segundos
        variance: Varianza (+/- porcentaje)
    """
    delay = base_delay * (1 + random.uniform(-variance, variance))
    time.sleep(delay)

def clean_text(text: Optional[str]) -> Optional[str]:
    """Limpia texto removiendo espacios extras y caracteres especiales"""
    if not text:
        return None
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_number(text: str) -> Optional[float]:
    """Extrae el primer número de un string"""
    if not text:
        return None
    # Reemplazar coma decimal por punto (formato español: "4,3" → "4.3")
    text = text.replace(',', '.')
    match = re.search(r'(\d+(?:\.\d+)?)', text)
    return float(match.group(1)) if match else None

def validate_rating(rating: float) -> bool:
    """Valida que el rating esté en rango válido"""
    return config.RATING_MIN <= rating <= config.RATING_MAX

def validate_coordinates(lat: float, lon: float) -> bool:
    """Valida que las coordenadas estén en rango de La Paz"""
    return (config.LAT_MIN <= lat <= config.LAT_MAX and
            config.LON_MIN <= lon <= config.LON_MAX)

def normalize_phone(phone: str) -> Optional[str]:
    """Normaliza número telefónico"""
    if not phone:
        return None
    # Remover todo excepto dígitos
    digits = re.sub(r'\D', '', phone)
    return digits if len(digits) >= config.MIN_TELEFONO_LENGTH else None

def normalize_name(name: str) -> str:
    """Normaliza nombre de establecimiento para matching"""
    if not name:
        return ""
    name = name.lower()
    name = re.sub(r'[^\w\s]', '', name)
    name = re.sub(r'\s+', ' ', name)
    return name.strip()
