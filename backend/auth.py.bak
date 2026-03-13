import re
from datetime import datetime, timedelta, timezone
from flask import Blueprint, request, jsonify
import bcrypt
import jwt
from config import Config
from database import get_db

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


@auth_bp.route("/register", methods=["POST"])
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
    elif len(password) < 8:
        errors.append("La contraseña debe tener al menos 8 caracteres.")

    if password != password_confirm:
        errors.append("Las contraseñas no coinciden.")

    if errors:
        return jsonify({"error": " ".join(errors)}), 400

    # --- Check uniqueness ---
    db = get_db()
    existing = db.execute("SELECT id FROM usuarios WHERE email = ?", (email,)).fetchone()
    if existing:
        return jsonify({"error": "Ya existe una cuenta con ese email."}), 409

    # --- Create user ---
    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    cursor = db.execute(
        "INSERT INTO usuarios (email, password_hash) VALUES (?, ?)",
        (email, password_hash),
    )
    db.commit()

    return jsonify({"id": cursor.lastrowid, "email": email}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    """Authenticate user and return a JWT token."""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Se requiere un cuerpo JSON válido."}), 400

    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "Email y contraseña son obligatorios."}), 400

    db = get_db()
    user = db.execute(
        "SELECT id, email, password_hash FROM usuarios WHERE email = ?", (email,)
    ).fetchone()

    if not user or not bcrypt.checkpw(password.encode("utf-8"), user["password_hash"].encode("utf-8")):
        return jsonify({"error": "Credenciales incorrectas."}), 401

    payload = {
        "user_id": user["id"],
        "email": user["email"],
        "exp": datetime.now(timezone.utc) + timedelta(hours=Config.JWT_EXPIRATION_HOURS),
        "iat": datetime.now(timezone.utc),
    }
    token = jwt.encode(payload, Config.JWT_SECRET, algorithm="HS256")

    return jsonify({"token": token}), 200


@auth_bp.route("/logout", methods=["POST"])
def logout():
    """Logout endpoint (client should discard the token)."""
    return jsonify({"message": "Sesión cerrada correctamente."}), 200
