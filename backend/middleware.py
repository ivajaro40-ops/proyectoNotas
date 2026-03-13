import functools
import logging
from flask import request, jsonify, g, abort
from jwt_security import decode_token_secure
from database import get_db

# Security event logger
security_logger = logging.getLogger("security")

def get_client_ip() -> str:
    """Obtiene la IP real del cliente respetando proxies de confianza."""
    if request.headers.get('X-Forwarded-For'):
        # Solo confiar en la primera IP (cliente original)
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    return request.remote_addr or 'unknown'

def require_auth(f):
    """
    Decorador de autenticación que:
    1. Extrae y valida el JWT del header Authorization.
    2. Verifica que el token no está en la blacklist.
    3. Carga el usuario en el contexto global `g`.
    4. Registra el acceso en el log de seguridad.
    """
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            security_logger.warning(
                "AUTH_MISSING | IP=%s | Path=%s", get_client_ip(), request.path
            )
            return jsonify({"error": "Token de autenticación requerido."}), 401

        token = auth_header[7:]  # Elimina "Bearer "
        payload = decode_token_secure(token, expected_type="access")

        if not payload:
            security_logger.warning(
                "AUTH_INVALID | IP=%s | Path=%s", get_client_ip(), request.path
            )
            return jsonify({"error": "Token inválido o expirado."}), 401

        g.current_user_id = int(payload["sub"])
        g.current_user_email = payload.get("email", "")
        g.jti = payload["jti"]
        return f(*args, **kwargs)
    return decorated

def require_note_ownership(f):
    """
    Decorador anti-IDOR: verifica que la nota pertenece al usuario autenticado.
    Úsalo siempre junto a @require_auth en rutas con <note_id>.
    """
    @functools.wraps(f)
    def decorated(*args, note_id: int, **kwargs):
        db = get_db()
        note = db.execute(
            "SELECT user_id FROM notas WHERE id = ?", (note_id,)
        ).fetchone()

        if not note:
            # Existencia de la nota es información — no revelar si es 401 o 404
            return jsonify({"error": "Nota no encontrada."}), 404

        if note['user_id'] != g.current_user_id:
            security_logger.critical(
                "IDOR_ATTEMPT | user_id=%s | note_id=%s | IP=%s",
                g.current_user_id, note_id, get_client_ip()
            )
            # Devuelve 404, no 403 — no confirma existencia del recurso
            return jsonify({"error": "Nota no encontrada."}), 404

        return f(*args, note_id=note_id, **kwargs)
    return decorated
