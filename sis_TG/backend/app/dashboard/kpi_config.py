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

# Expected monthly revenue per active client = Σ (price × consumption × adoption_rate)
# This is the weighted-average spend across all products a typical client buys.
AVG_MONTHLY_REVENUE_PER_CLIENT: float = round(
    sum(price * consumption * adoption for _, price, consumption, adoption in _PRODUCTS),
    2,
)

# Traffic light thresholds
THRESHOLDS = {
    # Estimated total monthly revenue (Bs)
    "revenue_green":      150_000.0,
    "revenue_yellow":      75_000.0,
    # Cumulative active clients
    "clients_green":  30,
    "clients_yellow": 15,
    # New clients in a given month
    "new_clients_green":  5,
    "new_clients_yellow": 2,
}
