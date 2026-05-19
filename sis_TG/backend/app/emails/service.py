import logging
import smtplib
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from sqlalchemy.orm import Session

from app.config import settings
from app.restaurants.models import Restaurant, RestaurantNote

logger = logging.getLogger("app.emails")


def send_contact_email(
    db: Session,
    restaurant_id: int,
    to_email: str,
    subject: str,
    body: str,
    sender_user_id: str,
    sender_name: str,
) -> None:
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not restaurant:
        raise ValueError(f"Restaurante {restaurant_id} no encontrado")

    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        raise RuntimeError("Credenciales SMTP no configuradas en el servidor")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM_EMAIL or settings.SMTP_USER
    msg["To"] = to_email

    html_body = body.replace("\n", "<br>")
    full_html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px; color: #374151; font-size: 14px; line-height: 1.6;">
        {html_body}
    </body>
    </html>
    """

    msg.attach(MIMEText(body, "plain"))
    msg.attach(MIMEText(full_html, "html"))

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.sendmail(msg["From"], to_email, msg.as_string())

    logger.info(f"Email de contacto enviado a {to_email} para restaurante {restaurant_id}")

    timestamp = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M")
    note = RestaurantNote(
        restaurant_id=restaurant_id,
        user_id=sender_user_id,
        content=f"[Email enviado] Para: {to_email} · Asunto: {subject} · {timestamp}",
    )
    db.add(note)
    db.commit()
