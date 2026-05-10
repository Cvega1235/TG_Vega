"""
Cifrado de campos sensibles con Fernet (AES-128-CBC + HMAC-SHA256).
Si ENCRYPTION_KEY no está configurada en .env, los campos se almacenan
sin cifrar (modo desarrollo) y se emite un aviso en el log.
"""
import logging
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import TypeDecorator, Text

logger = logging.getLogger("app.security.encryption")
_cipher: Optional[Fernet] = None
_key_checked = False


def _get_cipher() -> Optional[Fernet]:
    global _cipher, _key_checked
    if not _key_checked:
        _key_checked = True
        from app.config import settings
        key = getattr(settings, "ENCRYPTION_KEY", "")
        if key:
            try:
                _cipher = Fernet(key.encode() if isinstance(key, str) else key)
                logger.info("Cifrado de campos activado (Fernet/AES-128-CBC)")
            except Exception as e:
                logger.error(f"ENCRYPTION_KEY inválida: {e}")
        else:
            logger.warning(
                "ENCRYPTION_KEY no configurada — campos sensibles sin cifrar. "
                "Genere una clave con: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
            )
    return _cipher


def encrypt_field(value: Optional[str]) -> Optional[str]:
    """Cifra un valor de texto. Retorna None si el valor es None."""
    if value is None:
        return None
    cipher = _get_cipher()
    if cipher is None:
        return value
    return cipher.encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_field(value: Optional[str]) -> Optional[str]:
    """Descifra un valor. Si falla (dato no cifrado), retorna el valor original."""
    if value is None:
        return None
    cipher = _get_cipher()
    if cipher is None:
        return value
    try:
        return cipher.decrypt(value.encode("utf-8")).decode("utf-8")
    except (InvalidToken, Exception):
        # Dato ya existente sin cifrar → devolverlo tal cual
        return value


class EncryptedString(TypeDecorator):
    """
    TypeDecorator de SQLAlchemy que cifra al escribir y descifra al leer.
    Úsalo igual que String/Text en los modelos.
    """
    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        return encrypt_field(value)

    def process_result_value(self, value, dialect):
        return decrypt_field(value)
