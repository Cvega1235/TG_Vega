"""Servicio de envio de emails para OTP."""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.config import settings

logger = logging.getLogger("app.auth.email")


def send_otp_email(to_email: str, otp_code: str, user_name: str) -> None:
    """Envia un codigo OTP de 6 digitos al email del usuario via Gmail SMTP."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Don Piotr - Codigo de Verificacion"
    msg["From"] = settings.SMTP_FROM_EMAIL
    msg["To"] = to_email

    text_body = (
        f"Hola {user_name},\n\n"
        f"Tu codigo de verificacion es: {otp_code}\n\n"
        f"Este codigo expira en {settings.OTP_EXPIRE_MINUTES} minutos.\n\n"
        f"Si no solicitaste este codigo, ignora este mensaje.\n\n"
        f"- Sistema Don Piotr"
    )

    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px; background: #f9fafb;">
        <div style="max-width: 420px; margin: 0 auto; background: white;
                    border-radius: 12px; padding: 32px; text-align: center;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
            <h2 style="color: #4F46E5; margin-bottom: 8px;">Don Piotr</h2>
            <p style="color: #6B7280; font-size: 14px; margin-bottom: 24px;">
                Sistema de Inteligencia de Mercado
            </p>
            <p style="color: #374151;">Hola <strong>{user_name}</strong>,</p>
            <p style="color: #374151;">Tu codigo de verificacion es:</p>
            <div style="font-size: 36px; font-weight: bold; letter-spacing: 10px;
                        color: #1F2937; background: #F3F4F6; padding: 16px 24px;
                        border-radius: 8px; margin: 20px 0; display: inline-block;">
                {otp_code}
            </div>
            <p style="color: #9CA3AF; font-size: 13px; margin-top: 20px;">
                Este codigo expira en {settings.OTP_EXPIRE_MINUTES} minutos.
            </p>
            <hr style="border: none; border-top: 1px solid #E5E7EB; margin: 24px 0;">
            <p style="color: #9CA3AF; font-size: 12px;">
                Si no solicitaste este codigo, ignora este mensaje.
            </p>
        </div>
    </body>
    </html>
    """

    msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_FROM_EMAIL, to_email, msg.as_string())
        logger.info(f"OTP enviado a {to_email}")
    except Exception as e:
        logger.error(f"Error enviando OTP a {to_email}: {e}")
        raise
