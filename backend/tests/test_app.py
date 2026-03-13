"""
Tests for the Gestor de Notas Privadas API.
Covers: registration, login, notes CRUD, authorization isolation, and validation.
"""


class TestAuthRegister:
    """Tests for POST /api/auth/register."""

    def test_register_success(self, client):
        resp = client.post("/api/auth/register", json={
            "email": "new@example.com",
            "password": "securepass",
            "password_confirm": "securepass",
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["email"] == "new@example.com"
        assert "id" in data
        assert "password" not in data
        assert "password_hash" not in data

    def test_register_duplicate_email(self, client):
        client.post("/api/auth/register", json={
            "email": "dup@example.com",
            "password": "securepass",
            "password_confirm": "securepass",
        })
        resp = client.post("/api/auth/register", json={
            "email": "dup@example.com",
            "password": "securepass",
            "password_confirm": "securepass",
        })
        assert resp.status_code == 409
        assert "error" in resp.get_json()

    def test_register_password_mismatch(self, client):
        resp = client.post("/api/auth/register", json={
            "email": "user@example.com",
            "password": "securepass",
            "password_confirm": "different",
        })
        assert resp.status_code == 400
        assert "coinciden" in resp.get_json()["error"]

    def test_register_short_password(self, client):
        resp = client.post("/api/auth/register", json={
            "email": "user@example.com",
            "password": "short",
            "password_confirm": "short",
        })
        assert resp.status_code == 400
        assert "8 caracteres" in resp.get_json()["error"]

    def test_register_invalid_email(self, client):
        resp = client.post("/api/auth/register", json={
            "email": "not-an-email",
            "password": "securepass",
            "password_confirm": "securepass",
        })
        assert resp.status_code == 400
        assert "email" in resp.get_json()["error"].lower()

    def test_register_missing_fields(self, client):
        resp = client.post("/api/auth/register", json={})
        assert resp.status_code == 400


class TestAuthLogin:
    """Tests for POST /api/auth/login."""

    def test_login_success(self, client):
        client.post("/api/auth/register", json={
            "email": "login@example.com",
            "password": "securepass",
            "password_confirm": "securepass",
        })
        resp = client.post("/api/auth/login", json={
            "email": "login@example.com",
            "password": "securepass",
        })
        assert resp.status_code == 200
        assert "token" in resp.get_json()

    def test_login_wrong_password(self, client):
        client.post("/api/auth/register", json={
            "email": "login2@example.com",
            "password": "securepass",
            "password_confirm": "securepass",
        })
        resp = client.post("/api/auth/login", json={
            "email": "login2@example.com",
            "password": "wrongpassword",
        })
        assert resp.status_code == 401
        assert "error" in resp.get_json()

    def test_login_nonexistent_user(self, client):
        resp = client.post("/api/auth/login", json={
            "email": "noone@example.com",
            "password": "whatever",
        })
        assert resp.status_code == 401

    def test_login_missing_fields(self, client):
        resp = client.post("/api/auth/login", json={})
        assert resp.status_code == 400


class TestNotesCRUD:
    """Tests for notes CRUD operations."""

    def test_create_note(self, client, auth_headers):
        resp = client.post("/api/notes", headers=auth_headers, json={
            "titulo": "Mi primera nota",
            "contenido": "Contenido de prueba",
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["titulo"] == "Mi primera nota"
        assert data["contenido"] == "Contenido de prueba"
        assert "id" in data

    def test_list_notes(self, client, auth_headers):
        client.post("/api/notes", headers=auth_headers, json={
            "titulo": "Nota 1", "contenido": "Contenido 1",
        })
        client.post("/api/notes", headers=auth_headers, json={
            "titulo": "Nota 2", "contenido": "Contenido 2",
        })
        resp = client.get("/api/notes", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data) == 2
        # Should have snippet, not full contenido
        assert "snippet" in data[0]

    def test_get_note(self, client, auth_headers):
        create_resp = client.post("/api/notes", headers=auth_headers, json={
            "titulo": "Detalle", "contenido": "Contenido detallado",
        })
        note_id = create_resp.get_json()["id"]
        resp = client.get(f"/api/notes/{note_id}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.get_json()["contenido"] == "Contenido detallado"

    def test_update_note(self, client, auth_headers):
        create_resp = client.post("/api/notes", headers=auth_headers, json={
            "titulo": "Original", "contenido": "Contenido original",
        })
        note_id = create_resp.get_json()["id"]
        resp = client.put(f"/api/notes/{note_id}", headers=auth_headers, json={
            "titulo": "Editado", "contenido": "Contenido editado",
        })
        assert resp.status_code == 200
        assert resp.get_json()["titulo"] == "Editado"

    def test_delete_note(self, client, auth_headers):
        create_resp = client.post("/api/notes", headers=auth_headers, json={
            "titulo": "A borrar", "contenido": "Se eliminará",
        })
        note_id = create_resp.get_json()["id"]
        resp = client.delete(f"/api/notes/{note_id}", headers=auth_headers)
        assert resp.status_code == 204
        # Confirm it's gone
        resp = client.get(f"/api/notes/{note_id}", headers=auth_headers)
        assert resp.status_code == 404


class TestNotesAuthorization:
    """Tests that a user CANNOT access another user's notes."""

    def test_user_cannot_see_other_notes(self, client, auth_headers, auth_headers_user2):
        create_resp = client.post("/api/notes", headers=auth_headers, json={
            "titulo": "Privada", "contenido": "Solo para user1",
        })
        note_id = create_resp.get_json()["id"]

        # User 2 tries to read user 1's note
        resp = client.get(f"/api/notes/{note_id}", headers=auth_headers_user2)
        assert resp.status_code == 403

    def test_user_cannot_edit_other_notes(self, client, auth_headers, auth_headers_user2):
        create_resp = client.post("/api/notes", headers=auth_headers, json={
            "titulo": "Privada", "contenido": "Solo para user1",
        })
        note_id = create_resp.get_json()["id"]

        resp = client.put(f"/api/notes/{note_id}", headers=auth_headers_user2, json={
            "titulo": "Hackeado", "contenido": "Intento de edición",
        })
        assert resp.status_code == 403

    def test_user_cannot_delete_other_notes(self, client, auth_headers, auth_headers_user2):
        create_resp = client.post("/api/notes", headers=auth_headers, json={
            "titulo": "Privada", "contenido": "Solo para user1",
        })
        note_id = create_resp.get_json()["id"]

        resp = client.delete(f"/api/notes/{note_id}", headers=auth_headers_user2)
        assert resp.status_code == 403

    def test_list_only_own_notes(self, client, auth_headers, auth_headers_user2):
        client.post("/api/notes", headers=auth_headers, json={
            "titulo": "User1 Nota", "contenido": "Pertenece a user1",
        })
        client.post("/api/notes", headers=auth_headers_user2, json={
            "titulo": "User2 Nota", "contenido": "Pertenece a user2",
        })

        resp = client.get("/api/notes", headers=auth_headers)
        notes = resp.get_json()
        assert len(notes) == 1
        assert notes[0]["titulo"] == "User1 Nota"


class TestNotesValidation:
    """Tests for input validation on notes endpoints."""

    def test_create_empty_title(self, client, auth_headers):
        resp = client.post("/api/notes", headers=auth_headers, json={
            "titulo": "", "contenido": "Contenido",
        })
        assert resp.status_code == 400

    def test_create_empty_content(self, client, auth_headers):
        resp = client.post("/api/notes", headers=auth_headers, json={
            "titulo": "Título", "contenido": "",
        })
        assert resp.status_code == 400

    def test_create_title_too_long(self, client, auth_headers):
        resp = client.post("/api/notes", headers=auth_headers, json={
            "titulo": "A" * 201, "contenido": "Contenido",
        })
        assert resp.status_code == 400

    def test_unauthenticated_access(self, client):
        resp = client.get("/api/notes")
        assert resp.status_code == 401

    def test_invalid_token(self, client):
        resp = client.get("/api/notes", headers={
            "Authorization": "Bearer invalid.token.here",
        })
        assert resp.status_code == 401

    def test_get_nonexistent_note(self, client, auth_headers):
        resp = client.get("/api/notes/99999", headers=auth_headers)
        assert resp.status_code == 404
