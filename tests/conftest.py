"""
conftest.py
Fixtures compartidos para todos los tests.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Agregar directorios al path para imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "scraping_don_piotr"))


@pytest.fixture
def sample_restaurant_records():
    """Lista de diccionarios con datos de restaurantes de ejemplo."""
    return [
        {
            "nombre": "Restaurante El Patio",
            "fuente": "Google Maps",
            "url": "https://maps.google.com/place/el-patio",
            "direccion": "Av. Ballivian 1234, Calacoto, La Paz",
            "telefono": "2277xxxx",
            "rating": 4.5,
            "num_resenas": 120,
            "latitud": -16.5234,
            "longitud": -68.0823,
            "precio": "$$",
            "tipo_cocina": "Internacional",
            "zona": "Calacoto",
            "descripcion": "Restaurante de comida internacional",
        },
        {
            "nombre": "Burger King Sopocachi",
            "fuente": "Google Maps",
            "url": "https://maps.google.com/place/bk",
            "direccion": "Av. 20 de Octubre 456, Sopocachi, La Paz",
            "telefono": "2241xxxx",
            "rating": 3.8,
            "num_resenas": 250,
            "latitud": -16.5012,
            "longitud": -68.1234,
            "precio": "$",
            "tipo_cocina": "Hamburguesas, Comida Rapida",
            "zona": "Sopocachi",
            "descripcion": None,
        },
        {
            "nombre": "Sushi Zen",
            "fuente": "TripAdvisor",
            "url": "https://tripadvisor.com/sushi-zen",
            "direccion": "Calle 21, San Miguel, La Paz",
            "telefono": None,
            "rating": 4.2,
            "num_resenas": 85,
            "latitud": -16.5345,
            "longitud": -68.0756,
            "precio": "$$$",
            "tipo_cocina": "Japonesa, Sushi",
            "zona": "San Miguel",
            "descripcion": "El mejor sushi de La Paz",
        },
        {
            "nombre": "Pollos Copacabana",
            "fuente": "Bolivia en tus Manos",
            "url": "https://boliviaentusmanos.com/pollos",
            "direccion": "Centro, La Paz",
            "telefono": "tel:22345678",
            "rating": 3.5,
            "num_resenas": 30,
            "latitud": None,
            "longitud": None,
            "precio": "$",
            "tipo_cocina": "Pollo, Comida Rapida",
            "zona": None,
            "descripcion": None,
        },
        {
            "nombre": "La Comedie",
            "fuente": "TripAdvisor",
            "url": "https://tripadvisor.com/la-comedie",
            "direccion": "Pasaje Medinaceli, Sopocachi",
            "telefono": "67812345",
            "rating": 4.7,
            "num_resenas": 310,
            "latitud": -16.5023,
            "longitud": -68.1198,
            "precio": "$$$$",
            "tipo_cocina": "Francesa, Internacional",
            "zona": "Sopocachi",
            "descripcion": "Haute cuisine francesa",
        },
    ]


@pytest.fixture
def sample_restaurants_df(sample_restaurant_records):
    """DataFrame con datos de restaurantes de ejemplo."""
    return pd.DataFrame(sample_restaurant_records)


@pytest.fixture
def sample_clients_df():
    """DataFrame con datos de clientes actuales de ejemplo (simula ICP)."""
    return pd.DataFrame([
        {
            "nombre": "Hotel Presidente",
            "fuente": "cliente",
            "direccion": "Av. Mariscal Santa Cruz, Centro",
            "telefono": "22406666",
            "rating": 4.0,
            "num_resenas": 200,
            "latitud": -16.4966,
            "longitud": -68.1336,
            "precio": "$$$",
            "tipo_cocina": "Internacional",
            "zona": "Centro",
        },
        {
            "nombre": "Restaurante Gustu",
            "fuente": "cliente",
            "direccion": "Calle 10, Calacoto",
            "telefono": "22117491",
            "rating": 4.8,
            "num_resenas": 500,
            "latitud": -16.5367,
            "longitud": -68.0812,
            "precio": "$$$$",
            "tipo_cocina": "Boliviana, Internacional",
            "zona": "Calacoto",
        },
        {
            "nombre": "Cafe del Mundo",
            "fuente": "cliente",
            "direccion": "Sopocachi, La Paz",
            "telefono": "22411234",
            "rating": 4.3,
            "num_resenas": 150,
            "latitud": -16.5045,
            "longitud": -68.1200,
            "precio": "$$",
            "tipo_cocina": "Cafe, Desayunos",
            "zona": "Sopocachi",
        },
    ])


@pytest.fixture
def sample_feature_matrix():
    """Matriz de features pre-computada para tests de clustering."""
    np.random.seed(42)
    # 3 clusters claros
    c1 = np.random.randn(15, 5) + np.array([2, 2, 0, 0, 1])
    c2 = np.random.randn(15, 5) + np.array([-2, -2, 0, 0, -1])
    c3 = np.random.randn(15, 5) + np.array([0, 0, 3, 3, 0])
    return np.vstack([c1, c2, c3])
