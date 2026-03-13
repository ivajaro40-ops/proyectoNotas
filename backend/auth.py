import logging
import re
from datetime import datetime, timedelta, timezone
from flask import Blueprint, request, jsonify
import bcrypt
import jwt
import urllib.request
import urllib.parse
import json
from config import Config
from database import get_db
from jwt_security import create_access_token, create_refresh_token, decode_token_secure, blacklist_token
from middleware import require_auth, get_client_ip
from flask import g
import hmac
import time
import threading
from collections import defaultdict
from dataclasses import dataclass
from extensions import limiter

_login_attempts = defaultdict(list)
_lock = threading.Lock()

def check_progressive_lockout(ip: str) -> tuple[bool, int]:
    now = time.time()
    with _lock:
        _login_attempts[ip] = [t for t in _login_attempts[ip] if now - t < 3600]
        attempts = len(_login_attempts[ip])

    if attempts >= 20:
        wait = 3600
    elif attempts >= 10:
        wait = 300
    elif attempts >= 5:
        wait = 30
    else:
        return False, 0

    last_attempt = _login_attempts[ip][-1] if _login_attempts[ip] else 0
    remaining = int(wait - (now - last_attempt))
    if remaining > 0:
        return True, remaining
    return False, 0

@dataclass
class PasswordPolicy:
    min_length: int = 12
    require_uppercase: bool = True
    require_lowercase: bool = True
    require_digits: bool = True
    require_special: bool = True
    special_chars: str = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    max_length: int = 128

def validate_password(password: str) -> tuple[bool, list[str]]:
    policy = PasswordPolicy()
    errors = []
    if len(password) < policy.min_length:
        errors.append(f"Mínimo {policy.min_length} caracteres.")
    if len(password) > policy.max_length:
        errors.append(f"Máximo {policy.max_length} caracteres.")
    if policy.require_uppercase and not re.search(r'[A-Z]', password):
        errors.append("Debe contener al menos una mayúscula.")
    if policy.require_lowercase and not re.search(r'[a-z]', password):
        errors.append("Debe contener al menos una minúscula.")
    if policy.require_digits and not re.search(r'\d', password):
        errors.append("Debe contener al menos un número.")
    if policy.require_special and not any(c in policy.special_chars for c in password):
        errors.append("Debe contener al menos un carácter especial.")

    COMMON_PASSWORDS = {"password123", "admin1234", "qwerty123", "123456789012"}
    if password.lower() in COMMON_PASSWORDS:
        errors.append("Contraseña demasiado común. Elige una más única.")

    return len(errors) == 0, errors

def verify_password_safe(plain: str, hashed: bytes) -> bool:
    try:
        result = bcrypt.checkpw(plain.encode('utf-8'), hashed)
        return hmac.compare_digest(str(result).encode(), b'True')
    except Exception:
        return False

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

# Security event logger
security_logger = logging.getLogger("security")

def verify_recaptcha(token: str) -> bool:
    """Verifies the reCAPTCHA token using Google's API."""
    if not token:
        return False
    url = "https://www.google.com/recaptcha/api/siteverify"
    data = urllib.parse.urlencode({
        "secret": Config.RECAPTCHA_SECRET_KEY,
        "response": token
    }).encode("utf-8")
    try:
        req = urllib.request.Request(url, data=data)
        with urllib.request.urlopen(req, timeout=5) as response:
            result = json.loads(response.read().decode("utf-8"))
            if not result.get("success", False):
                security_logger.warning("reCAPTCHA failed: %s", result.get("error-codes"))
                return False
            return True
    except Exception as e:
        security_logger.error("reCAPTCHA API error: %s", e)
        return False


@auth_bp.route("/register", methods=["POST"])
@limiter.limit("3 per hour")
def register():
    """Register a new user account."""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Se requiere un cuerpo JSON válido."}), 400

    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    password_confirm = data.get("password_confirm") or ""

    # --- Validation ---
    errors = []
    if not email:
        errors.append("El email es obligatorio.")
    elif not EMAIL_REGEX.match(email):
        errors.append("El formato del email no es válido.")

    if not password:
        errors.append("La contraseña es obligatoria.")
    else:
        valid, pwd_errors = validate_password(password)
        if not valid:
            errors.extend(pwd_errors)

    if password != password_confirm:
        errors.append("Las contraseñas no coinciden.")

    if errors:
        return jsonify({"error": " ".join(errors)}), 400

    recaptcha_token = data.get("recaptcha_token") or ""
    if not verify_recaptcha(recaptcha_token):
        return jsonify({"error": "Falló la verificación del reCAPTCHA."}), 400

    # --- Check uniqueness ---
    db = get_db()
    existing = db.execute("SELECT id FROM usuarios WHERE email = ?", (email,)).fetchone()
    if existing:
        return jsonify({"error": "Ya existe una cuenta con ese email."}), 409

    # --- Create user (bcrypt rounds=12 explicitly documented) ---
    password_hash = bcrypt.hashpw(
        password.encode("utf-8"), bcrypt.gensalt(rounds=12)
    ).decode("utf-8")
    cursor = db.execute(
        "INSERT INTO usuarios (email, password_hash) VALUES (?, ?)",
        (email, password_hash),
    )
    db.commit()

    security_logger.info("User registered | email=%s", email)
    return jsonify({"id": cursor.lastrowid, "email": email}), 201


@auth_bp.route("/login", methods=["POST"])
@limiter.limit("5 per minute; 20 per hour")
def login():
    """Authenticate user and return a JWT token."""
    ip = get_client_ip()
    locked, remaining = check_progressive_lockout(ip)
    if locked:
        security_logger.warning("Progressive lockout active | ip=%s wait=%s", ip, remaining)
        return jsonify({"error": f"Demasiados intentos fallidos. Inténtalo de nuevo en {remaining} segundos."}), 429

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Se requiere un cuerpo JSON válido."}), 400

    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "Email y contraseña son obligatorios."}), 400

    recaptcha_token = data.get("recaptcha_token") or ""
    if not verify_recaptcha(recaptcha_token):
        return jsonify({"error": "Falló la verificación del reCAPTCHA."}), 400

    db = get_db()
    user = db.execute(
        "SELECT id, email, password_hash FROM usuarios WHERE email = ?", (email,)
    ).fetchone()

    if not user or not verify_password_safe(password, user["password_hash"].encode("utf-8")):
        with _lock:
            _login_attempts[ip].append(time.time())
        security_logger.warning(
            "Failed login attempt | ip=%s email=%s",
            ip,
            email,
        )
        return jsonify({"error": "Credenciales incorrectas."}), 401

    access_token = create_access_token(user["id"], user["email"])
    refresh_token = create_refresh_token(user["id"])

    security_logger.info("Successful login | ip=%s user_id=%s", request.remote_addr, user["id"])
    return jsonify({"access_token": access_token, "refresh_token": refresh_token}), 200


@auth_bp.route("/refresh", methods=["POST"])
def refresh():
    """Generates a new access token from a valid refresh token."""
    data = request.get_json(silent=True)
    if not data or not data.get("refresh_token"):
        return jsonify({"error": "Token de refresco requerido."}), 400
        
    refresh_token = data.get("refresh_token")
    payload = decode_token_secure(refresh_token, expected_type="refresh")
    
    if not payload:
        return jsonify({"error": "Token de refresco inválido o expirado."}), 401
    
    user_id = int(payload["sub"])
    
    db = get_db()
    user = db.execute("SELECT email FROM usuarios WHERE id = ?", (user_id,)).fetchone()
    if not user:
        return jsonify({"error": "Usuario no encontrado."}), 404
        
    new_access_token = create_access_token(user_id, user["email"])
    return jsonify({"access_token": new_access_token}), 200


@auth_bp.route("/logout", methods=["POST"])
@require_auth
def logout():
    """Logout endpoint. Blaclists the active access token."""
    blacklist_token(g.jti, 15 * 60) # 15 minutos en segundos
    
    data = request.get_json(silent=True)
    if data and data.get("refresh_token"):
        # También agregamos el refresh_token a la blacklist si se envía
        rt_payload = decode_token_secure(data.get("refresh_token"), expected_type="refresh")
        if rt_payload:
            blacklist_token(rt_payload["jti"], 7 * 24 * 60 * 60)

    return jsonify({"message": "Sesión cerrada correctamente."}), 200
