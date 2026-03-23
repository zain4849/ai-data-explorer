"""Fernet encryption for stored connection credentials."""

import base64
import hashlib

from cryptography.fernet import Fernet

from .config import settings


def _derive_key() -> bytes:
    """Derive a 32-byte Fernet key from the app's secret_key or encryption_key."""
    raw = settings.encryption_key or settings.secret_key
    digest = hashlib.sha256(raw.encode()).digest()
    return base64.urlsafe_b64encode(digest)


_fernet: Fernet | None = None


def _get_fernet() -> Fernet:
    global _fernet
    if _fernet is None:
        _fernet = Fernet(_derive_key())
    return _fernet


def encrypt(plaintext: str) -> str:
    return _get_fernet().encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str) -> str:
    return _get_fernet().decrypt(ciphertext.encode()).decode()
