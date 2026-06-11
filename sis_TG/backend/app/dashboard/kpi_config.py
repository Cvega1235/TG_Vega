# KPI revenue estimation configuration.
# Source: Tabla 13 (Análisis ICP, Tesis) + precios del catálogo interno.
# Only public sale prices and consumption statistics are stored here.
# Full ingredient/recipe data is kept exclusively in the encrypted archive (recipes.enc).

_PRODUCTS = [
    # (name, price_bs_per_kg, avg_kg_per_client_per_month, pct_clients_who_buy)
    ("Kielbasa",            60.0,  37.7, 0.67),
    ("Chorizo Parrillero",  54.0,  20.6, 0.58),
    ("Jamón Inglés",        60.0,  17.7, 0.58),
    ("Costilla Ahumada",    68.0,  17.5, 0.58),
    ("Jamón Ahumado",       68.0,  15.0, 0.42),
    ("Jamón Crudo",        120.0,  14.3, 0.42),
    ("Tocino",              70.0,  14.2, 0.50),
    ("Salame",              55.0,  13.0, 0.58),
    ("Cabanosy",            65.0,  11.6, 0.50),
]

PRODUCT_DETAILS = [
    {
        "nombre": name,
        "precio_bs_kg": price,
        "consumo_kg_mes": consumption,
        "adopcion": adoption,
        "ingreso_esperado_por_cliente": round(price * consumption * adoption, 2),
    }
    for name, price, consumption, adoption in _PRODUCTS
]

# Expected monthly revenue per active client.
# Based on: 40 kg/day × 20 working days = 800 kg/month capacity,
# average price ~90 Bs/kg, distributed across 29 current clients.
# 800 × 90 / 29 = 2,482.76 Bs/client/month
AVG_MONTHLY_REVENUE_PER_CLIENT: float = 2482.76

# Traffic light thresholds
THRESHOLDS = {
    "revenue_green":      150_000.0,
    "revenue_yellow":      75_000.0,
    "clients_green":  30,
    "clients_yellow": 15,
    "new_clients_green":  5,
    "new_clients_yellow": 2,
}
