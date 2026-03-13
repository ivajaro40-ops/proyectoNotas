from datetime import datetime
from flask import Blueprint, request, jsonify, g
import bleach
from config import Config
from database import get_db
from middleware import token_required

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
    if snippet:
        d["snippet"] = (row["contenido"] or "")[:150]
    else:
        d["contenido"] = row["contenido"]
    return d


@notes_bp.route("", methods=["GET"])
@token_required
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
@token_required
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
    cursor = db.execute(
        "INSERT INTO notas (user_id, titulo, contenido, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?)",
        (g.current_user_id, titulo, contenido, now, now),
    )
    db.commit()

    note = db.execute(
        "SELECT id, titulo, contenido, created_at, updated_at FROM notas WHERE id = ?",
        (cursor.lastrowid,),
    ).fetchone()

    return jsonify(note_to_dict(note)), 201


@notes_bp.route("/<int:note_id>", methods=["GET"])
@token_required
def get_note(note_id):
    """Retrieve a single note if it belongs to the authenticated user."""
    db = get_db()
    note = db.execute(
        "SELECT id, user_id, titulo, contenido, created_at, updated_at "
        "FROM notas WHERE id = ?",
        (note_id,),
    ).fetchone()

    if not note:
        return jsonify({"error": "Nota no encontrada."}), 404

    if note["user_id"] != g.current_user_id:
        return jsonify({"error": "No tienes permiso para ver esta nota."}), 403

    return jsonify(note_to_dict(note)), 200


@notes_bp.route("/<int:note_id>", methods=["PUT"])
@token_required
def update_note(note_id):
    """Update a note if it belongs to the authenticated user."""
    db = get_db()
    note = db.execute(
        "SELECT id, user_id FROM notas WHERE id = ?", (note_id,)
    ).fetchone()

    if not note:
        return jsonify({"error": "Nota no encontrada."}), 404

    if note["user_id"] != g.current_user_id:
        return jsonify({"error": "No tienes permiso para editar esta nota."}), 403

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
    db.execute(
        "UPDATE notas SET titulo = ?, contenido = ?, updated_at = ? WHERE id = ?",
        (titulo, contenido, now, note_id),
    )
    db.commit()

    updated = db.execute(
        "SELECT id, titulo, contenido, created_at, updated_at FROM notas WHERE id = ?",
        (note_id,),
    ).fetchone()

    return jsonify(note_to_dict(updated)), 200


@notes_bp.route("/<int:note_id>", methods=["DELETE"])
@token_required
def delete_note(note_id):
    """Delete a note if it belongs to the authenticated user."""
    db = get_db()
    note = db.execute(
        "SELECT id, user_id FROM notas WHERE id = ?", (note_id,)
    ).fetchone()

    if not note:
        return jsonify({"error": "Nota no encontrada."}), 404

    if note["user_id"] != g.current_user_id:
        return jsonify({"error": "No tienes permiso para borrar esta nota."}), 403

    db.execute("DELETE FROM notas WHERE id = ?", (note_id,))
    db.commit()

    return "", 204
