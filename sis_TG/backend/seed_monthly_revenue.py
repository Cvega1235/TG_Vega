"""
Populates monthly_revenue for existing clients using an estimate based on
restaurant size (num_resenas) and price tier (precio).

Formula: AVG_BASE × size_factor(log scale) × price_factor
"""
import math
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.database import engine
from sqlalchemy import text

AVG_BASE = 5905.43
REF_REVIEWS = 419.0

PRICE_FACTOR = {
    None: 1.0,
    "$": 0.8,
    "$$": 1.0,
    "$$$": 1.3,
}


def _size_factor(num_resenas: int | None) -> float:
    if not num_resenas or num_resenas <= 0:
        return 1.0
    raw = math.log10(num_resenas + 1) / math.log10(REF_REVIEWS + 1)
    return max(0.5, min(2.0, raw))


def estimate(num_resenas: int | None, precio: str | None) -> float:
    sf = _size_factor(num_resenas)
    pf = PRICE_FACTOR.get(precio, 1.0)
    return round(AVG_BASE * sf * pf, 2)


with engine.connect() as conn:
    rows = conn.execute(
        text("SELECT id, num_resenas, precio FROM restaurants WHERE status = 'cliente'")
    ).fetchall()

    print(f"Updating {len(rows)} clients with estimated monthly_revenue...")
    for rid, num_resenas, precio in rows:
        revenue = estimate(num_resenas, precio)
        conn.execute(
            text("UPDATE restaurants SET monthly_revenue = :rev WHERE id = :id"),
            {"rev": revenue, "id": rid},
        )
        print(f"  id={rid:4d}  resenas={str(num_resenas):>5}  precio={str(precio):>4}  -> {revenue:,.2f} Bs")

    conn.commit()
    print("Done.")
