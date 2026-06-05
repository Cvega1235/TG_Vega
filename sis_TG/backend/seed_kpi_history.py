"""
Script para insertar historial sintético de captación/pérdida de clientes.

Distribuye los 29 clientes actuales y 2 no_interesados a lo largo de 8 meses
(Oct 2025 – May 2026) simulando una curva de crecimiento realista.

Ejecución:
    cd sis_TG/backend
    python seed_kpi_history.py
"""
import sys, random
from datetime import datetime, timezone, timedelta
from sqlalchemy import text

sys.path.insert(0, ".")
from app.database import engine

random.seed(42)

# ── Distribución mensual ────────────────────────────────────────────────────
# (año, mes, ganados, perdidos)
SCHEDULE = [
    (2025, 10, 3, 0),
    (2025, 11, 5, 0),
    (2025, 12, 4, 1),
    (2026,  1, 5, 0),
    (2026,  2, 4, 1),
    (2026,  3, 4, 0),
    (2026,  4, 4, 0),
    (2026,  5, 2, 0),
]
total_ganados = sum(g for _, _, g, _ in SCHEDULE)
total_perdidos = sum(p for _, _, _, p in SCHEDULE)
assert total_ganados - total_perdidos == 29, f"Neto incorrecto: {total_ganados - total_perdidos}"


def random_date_in_month(year: int, month: int) -> datetime:
    if month == 12:
        last_day = 28
    else:
        last_day = (datetime(year, month + 1, 1) - timedelta(days=1)).day
    day = random.randint(1, last_day)
    hour = random.randint(8, 18)
    return datetime(year, month, day, hour, 0, 0, tzinfo=timezone.utc)


def run():
    with engine.connect() as conn:
        # ── 1. Obtener IDs y user_id del superadmin ─────────────────────────
        client_rows = conn.execute(
            text("SELECT id FROM restaurants WHERE status = 'cliente' ORDER BY id")
        ).fetchall()
        lost_rows = conn.execute(
            text("SELECT id FROM restaurants WHERE status = 'no_interesado' ORDER BY id")
        ).fetchall()
        admin_row = conn.execute(
            text("SELECT id FROM users ORDER BY created_at LIMIT 1")
        ).fetchone()

        client_ids = [r[0] for r in client_rows]
        lost_ids   = [r[0] for r in lost_rows]
        admin_id   = admin_row[0]

        print(f"Clientes actuales:    {len(client_ids)}")
        print(f"No interesados:       {len(lost_ids)}")
        print(f"User id (admin):      {admin_id}")

        needed_lost = sum(p for _, _, _, p in SCHEDULE)
        if len(lost_ids) < needed_lost:
            print(f"ERROR: se necesitan {needed_lost} no_interesados, solo hay {len(lost_ids)}")
            return

        # ── 2. Borrar registros existentes ───────────────────────────────────
        deleted = conn.execute(text("DELETE FROM restaurant_status_changes")).rowcount
        print(f"Registros eliminados: {deleted}")

        # ── 3. Mezclar pools ─────────────────────────────────────────────────
        random.shuffle(client_ids)
        random.shuffle(lost_ids)
        client_pool = list(client_ids)
        loss_pool   = list(lost_ids)
        loss_gain_month = {}   # restaurant_id → (year, month)

        inserts = []
        month_order = [(y, m) for y, m, _, _ in SCHEDULE]

        # ── 4. Asignar ganancias ─────────────────────────────────────────────
        for year, month, gained, lost_count in SCHEDULE:
            # Primero los que luego se perderán (para registrar su mes de ganancia)
            for _ in range(lost_count):
                rid = loss_pool.pop(0)
                loss_gain_month[rid] = (year, month)
                inserts.append({
                    "rid": rid,
                    "uid": str(admin_id),
                    "old": None,
                    "new": "cliente",
                    "at":  random_date_in_month(year, month),
                })
            # Resto de clientes normales
            for _ in range(gained - lost_count):
                rid = client_pool.pop(0)
                inserts.append({
                    "rid": rid,
                    "uid": str(admin_id),
                    "old": None,
                    "new": "cliente",
                    "at":  random_date_in_month(year, month),
                })

        # ── 5. Asignar pérdidas al mes siguiente ─────────────────────────────
        for rid, (gy, gm) in loss_gain_month.items():
            idx = month_order.index((gy, gm))
            ly, lm = month_order[idx + 1] if idx + 1 < len(month_order) else (gy, gm)
            inserts.append({
                "rid": rid,
                "uid": str(admin_id),
                "old": "cliente",
                "new": "no_interesado",
                "at":  random_date_in_month(ly, lm),
            })

        # ── 6. Insertar ──────────────────────────────────────────────────────
        conn.execute(
            text("""
                INSERT INTO restaurant_status_changes
                    (restaurant_id, user_id, old_status, new_status, changed_at)
                VALUES
                    (:rid, :uid, :old, :new, :at)
            """),
            inserts,
        )
        conn.commit()

        ganados_n  = sum(1 for r in inserts if r["new"] == "cliente")
        perdidos_n = sum(1 for r in inserts if r["new"] == "no_interesado")
        print(f"\nRegistros insertados:")
        print(f"  new_status='cliente':        {ganados_n}")
        print(f"  new_status='no_interesado':  {perdidos_n}")
        print(f"  Total:                       {len(inserts)}")
        print("\nOK — historial generado correctamente.")


if __name__ == "__main__":
    run()
