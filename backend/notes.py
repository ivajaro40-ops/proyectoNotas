from datetime import datetime
from flask import Blueprint, request, jsonify, g
import bleach
from config import Config
from database import get_db
from middleware import require_auth, require_note_ownership
from crypto_utils import encrypt_content, decrypt_content

notes_bp = Blueprint("notes", __name__, url_prefix="/api/notes")


def sanitize(text):
    """Strip any HTML tags from user input."""
    return bleach.clean(text, tags=[], strip=True)


def note_to_dict(row, snippet=False):
    """Convert a database row to a JSON-serializable dict."""
    d = {
        "id": row["id"],
        "titulo": row["titulo"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }
    # Decrypt content before returning
    decrypted_content = decrypt_content(row["contenido"], g.current_user_id)
    if snippet:
        d["snippet"] = (decrypted_content or "")[:150]
    else:
        d["contenido"] = decrypted_content
    return d


@notes_bp.route("", methods=["GET"])
@require_auth
def list_notes():
    """List all notes belonging to the authenticated user."""
    db = get_db()
    rows = db.execute(
        "SELECT id, titulo, contenido, created_at, updated_at "
        "FROM notas WHERE user_id = ? ORDER BY created_at DESC",
        (g.current_user_id,),
    ).fetchall()
    return jsonify([note_to_dict(r, snippet=True) for r in rows]), 200


@notes_bp.route("", methods=["POST"])
@require_auth
def create_note():
    """Create a new note for the authenticated user."""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Se requiere un cuerpo JSON válido."}), 400

    titulo = sanitize((data.get("titulo") or "").strip())
    contenido = sanitize((data.get("contenido") or "").strip())

    errors = []
    if not titulo:
        errors.append("El título es obligatorio.")
    elif len(titulo) > Config.TITLE_MAX_LENGTH:
        errors.append(f"El título no puede superar {Config.TITLE_MAX_LENGTH} caracteres.")

    if not contenido:
        errors.append("El contenido es obligatorio.")
    elif len(contenido) > Config.CONTENT_MAX_LENGTH:
        errors.append(f"El contenido no puede superar {Config.CONTENT_MAX_LENGTH} caracteres.")

    if errors:
        return jsonify({"error": " ".join(errors)}), 400

    db = get_db()
    now = datetime.utcnow().isoformat()
    encrypted_content = encrypt_content(contenido, g.current_user_id)
    cursor = db.execute(
        "INSERT INTO notas (user_id, titulo, contenido, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?)",
        (g.current_user_id, titulo, encrypted_content, now, now),
    )
    db.commit()

    note = db.execute(
        "SELECT id, titulo, contenido, created_at, updated_at FROM notas WHERE id = ?",
        (cursor.lastrowid,),
    ).fetchone()

    return jsonify(note_to_dict(note)), 201


@notes_bp.route("/<int:note_id>", methods=["GET"])
@require_auth
@require_note_ownership
def get_note(note_id):
    """Retrieve a single note if it belongs to the authenticated user."""
    db = get_db()
    note = db.execute(
        "SELECT id, user_id, titulo, contenido, created_at, updated_at "
        "FROM notas WHERE id = ?",
        (note_id,),
    ).fetchone()

    return jsonify(note_to_dict(note)), 200


@notes_bp.route("/<int:note_id>", methods=["PUT"])
@require_auth
@require_note_ownership
def update_note(note_id):
    """Update a note if it belongs to the authenticated user."""
    db = get_db()

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Se requiere un cuerpo JSON válido."}), 400

    titulo = sanitize((data.get("titulo") or "").strip())
    contenido = sanitize((data.get("contenido") or "").strip())

    errors = []
    if not titulo:
        errors.append("El título es obligatorio.")
    elif len(titulo) > Config.TITLE_MAX_LENGTH:
        errors.append(f"El título no puede superar {Config.TITLE_MAX_LENGTH} caracteres.")

    if not contenido:
        errors.append("El contenido es obligatorio.")
    elif len(contenido) > Config.CONTENT_MAX_LENGTH:
        errors.append(f"El contenido no puede superar {Config.CONTENT_MAX_LENGTH} caracteres.")

    if errors:
        return jsonify({"error": " ".join(errors)}), 400

    now = datetime.utcnow().isoformat()
    encrypted_content = encrypt_content(contenido, g.current_user_id)
    db.execute(
        "UPDATE notas SET titulo = ?, contenido = ?, updated_at = ? WHERE id = ?",
        (titulo, encrypted_content, now, note_id),
    )
    db.commit()

    updated = db.execute(
        "SELECT id, titulo, contenido, created_at, updated_at FROM notas WHERE id = ?",
        (note_id,),
    ).fetchone()

    return jsonify(note_to_dict(updated)), 200


@notes_bp.route("/<int:note_id>", methods=["DELETE"])
@require_auth
@require_note_ownership
def delete_note(note_id):
    """Delete a note if it belongs to the authenticated user."""
    db = get_db()
    db.execute("DELETE FROM notas WHERE id = ?", (note_id,))
    db.commit()

    return "", 204
