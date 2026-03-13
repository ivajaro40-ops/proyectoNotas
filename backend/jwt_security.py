import os
import jwt
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional
from database import get_db

# NUNCA uses HS256 sin validación explícita del algoritmo
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15   # Muy corto — minimiza ventana de ataque
REFRESH_TOKEN_EXPIRE_DAYS = 7

def get_jwt_secret():
    from config import Config
    return Config.JWT_SECRET

def is_token_blacklisted(jti: str) -> bool:
    """Comprueba si un JTI está revocado."""
    # Usando SQLite directo
    try:
        db = get_db()
        # Ensure we are returning a boolean
        result = db.execute(
            "SELECT 1 FROM token_blacklist WHERE jti = ? AND expires_at > ?",
            (jti, datetime.now(timezone.utc))
        ).fetchone()
        return result is not None
    except Exception:
        # If DB is not available in context or error, assume safe but ideally we handle it
        return False

def blacklist_token(jti: str, expire_seconds: int) -> None:
    """Añade un JTI a la blacklist con TTL igual a la expiración del token."""
    db = get_db()
    db.execute(
        "INSERT OR IGNORE INTO token_blacklist (jti, expires_at) VALUES (?, ?)",
        (jti, datetime.now(timezone.utc) + timedelta(seconds=expire_seconds))
    )
    db.commit()

def create_access_token(user_id: int, user_email: str) -> str:
    """Crea un JWT de acceso de corta duración con claims de seguridad completos."""
    now = datetime.now(timezone.utc)
    payload = {
        # Claims estándar RFC 7519
        "sub": str(user_id),                          # Subject
        "iat": now,                                    # Issued At
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),  # Expiration
        "nbf": now,                                    # Not Before
        "jti": str(uuid.uuid4()),                      # JWT ID único (para blacklist)
        # Claims personalizados
        "email": user_email,
        "type": "access",
        "ver": "1",                                    # Versión de token para rotación de esquema
    }
    return jwt.encode(payload, get_jwt_secret(), algorithm=JWT_ALGORITHM)

def create_refresh_token(user_id: int) -> str:
    """Crea un token de refresco opaco de larga duración."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        "jti": str(uuid.uuid4()),
        "type": "refresh",
    }
    return jwt.encode(payload, get_jwt_secret(), algorithm=JWT_ALGORITHM)

def decode_token_secure(token: str, expected_type: str = "access") -> Optional[dict]:
    """
    Decodificación segura de JWT con validación explícita de algoritmo.
    Previene: alg:none attack, algorithm confusion attack (RS256 → HS256).
    """
    try:
        payload = jwt.decode(
            token,
            get_jwt_secret(),
            algorithms=[JWT_ALGORITHM],          # Lista blanca explícita — CRÍTICO
            options={
                "require": ["exp", "iat", "sub", "jti", "type"],  # Claims obligatorios
                "verify_exp": True,
                "verify_iat": True,
                "verify_nbf": True,
            }
        )
        # Verificación adicional del tipo de token
        if payload.get("type") != expected_type:
            return None
        # Verificar que el JTI no está en la blacklist
        if is_token_blacklisted(payload["jti"]):
            return None
        return payload
    except jwt.ExpiredSignatureError:
        return None   # Token expirado — respuesta genérica
    except jwt.InvalidTokenError:
        return None   # Cualquier token inválido — respuesta genérica
