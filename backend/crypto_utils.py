from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
from config import Config
from cryptography.fernet import InvalidToken

def _derive_encryption_key(master_key: str, salt: bytes) -> bytes:
    """Deriva una clave de cifrado única por usuario a partir de la clave maestra."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480_000,
    )
    return base64.urlsafe_b64encode(kdf.derive(master_key.encode()))

def encrypt_content(plaintext: str, user_id: int) -> str:
    """Cifra el contenido de una nota con AES-128 via Fernet."""
    if not plaintext:
        return ""
    user_salt = str(user_id).encode('utf-8')
    key = _derive_encryption_key(Config.ENCRYPTION_MASTER_KEY, user_salt)
    f = Fernet(key)
    return f.encrypt(plaintext.encode('utf-8')).decode('utf-8')

def decrypt_content(ciphertext: str, user_id: int) -> str:
    """Descifra el contenido de una nota. Tolera contenido en texto plano heredado."""
    if not ciphertext:
        return ""
    user_salt = str(user_id).encode('utf-8')
    key = _derive_encryption_key(Config.ENCRYPTION_MASTER_KEY, user_salt)
    f = Fernet(key)
    try:
        return f.decrypt(ciphertext.encode('utf-8')).decode('utf-8')
    except InvalidToken:
        return ciphertext # Probablemente es texto plano creado antes del cifrado
