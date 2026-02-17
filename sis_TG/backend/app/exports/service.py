import csv
import io
from datetime import datetime, timezone

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

from app.restaurants.models import Restaurant, RestaurantScore


EXPORT_COLUMNS = [
    "nombre", "fuente", "zona", "direccion", "telefono", "rating",
    "num_resenas", "tipo_cocina", "precio", "status", "score",
]

COLUMN_HEADERS = [
    "Nombre", "Fuente", "Zona", "Direccion", "Telefono", "Rating",
    "Resenas", "Tipo Cocina", "Precio", "Estado", "Score",
]


def _get_filtered_data(
    db: Session,
    fuente: str | None = None,
    zona: str | None = None,
    status: str | None = None,
    rating_min: float | None = None,
    rating_max: float | None = None,
    search: str | None = None,
) -> list[dict]:
    query = db.query(Restaurant).outerjoin(RestaurantScore).options(
        joinedload(Restaurant.score)
    )
    if fuente:
        query = query.filter(Restaurant.fuente == fuente)
    if zona:
        query = query.filter(Restaurant.zona == zona)
    if status:
        query = query.filter(Restaurant.status == status)
    if rating_min is not None:
        query = query.filter(Restaurant.rating >= rating_min)
    if rating_max is not None:
        query = query.filter(Restaurant.rating <= rating_max)
    if search:
        query = query.filter(
            or_(
                Restaurant.nombre.ilike(f"%{search}%"),
                Restaurant.direccion.ilike(f"%{search}%"),
            )
        )

    restaurants = query.order_by(Restaurant.nombre).all()
    rows = []
    for r in restaurants:
        rows.append({
            "nombre": r.nombre,
            "fuente": r.fuente,
            "zona": r.zona or "",
            "direccion": r.direccion or "",
            "telefono": r.telefono or "",
            "rating": float(r.rating) if r.rating else "",
            "num_resenas": r.num_resenas or 0,
            "tipo_cocina": r.tipo_cocina or "",
            "precio": r.precio or "",
            "status": r.status,
            "score": float(r.score.total_score) if r.score else "",
        })
    return rows


def export_csv(db: Session, **filters) -> str:
    rows = _get_filtered_data(db, **filters)
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=EXPORT_COLUMNS)
    writer.writerow(dict(zip(EXPORT_COLUMNS, COLUMN_HEADERS)))
    for row in rows:
        writer.writerow(row)
    return output.getvalue()


def export_excel(db: Session, **filters) -> bytes:
    rows = _get_filtered_data(db, **filters)
    wb = Workbook()
    ws = wb.active
    ws.title = "Restaurantes"

    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="2563EB", end_color="2563EB", fill_type="solid")

    for col_num, header in enumerate(COLUMN_HEADERS, 1):
        cell = ws.cell(row=1, column=col_num, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center")

    for row_num, row_data in enumerate(rows, 2):
        for col_num, key in enumerate(EXPORT_COLUMNS, 1):
            ws.cell(row=row_num, column=col_num, value=row_data[key])

    for col_num in range(1, len(COLUMN_HEADERS) + 1):
        ws.column_dimensions[chr(64 + col_num)].width = 18

    output = io.BytesIO()
    wb.save(output)
    return output.getvalue()


def export_pdf(db: Session, **filters) -> bytes:
    rows = _get_filtered_data(db, **filters)
    output = io.BytesIO()
    doc = SimpleDocTemplate(output, pagesize=landscape(letter))
    styles = getSampleStyleSheet()

    elements = []
    title = Paragraph(
        f"Reporte de Restaurantes - Don Piotr ({datetime.now(timezone.utc).strftime('%Y-%m-%d')})",
        styles["Title"],
    )
    elements.append(title)
    elements.append(Spacer(1, 12))

    # Use abbreviated headers for PDF
    pdf_headers = ["Nombre", "Fuente", "Zona", "Rating", "Resenas", "Estado", "Score"]
    pdf_keys = ["nombre", "fuente", "zona", "rating", "num_resenas", "status", "score"]

    table_data = [pdf_headers]
    for row in rows:
        table_data.append([str(row[k])[:30] for k in pdf_keys])

    if len(table_data) > 1:
        table = Table(table_data, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563EB")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
        ]))
        elements.append(table)
    else:
        elements.append(Paragraph("No hay datos para exportar.", styles["Normal"]))

    elements.append(Spacer(1, 12))
    elements.append(
        Paragraph(f"Total: {len(rows)} restaurantes", styles["Normal"])
    )

    doc.build(elements)
    return output.getvalue()
