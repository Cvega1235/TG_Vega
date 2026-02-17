"""
logger.py
Sistema de logging centralizado
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from scraping_don_piotr import config

def setup_logger(name='scraping_don_piotr'):
    """
    Configura y retorna un logger con handlers para archivo y consola
    
    Args:
        name: Nombre del logger
        
    Returns:
        logging.Logger: Logger configurado
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, config.LOG_LEVEL))
    
    # Evitar duplicación de handlers
    if logger.handlers:
        return logger
    
    # Formato
    formatter = logging.Formatter(
        config.LOG_FORMAT,
        datefmt=config.LOG_DATE_FORMAT
    )
    
    # Handler para archivo
    file_handler = logging.FileHandler(config.LOG_FILE, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

# Crear logger global
logger = setup_logger()
