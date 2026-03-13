/**
 * Gestor de Notas Privadas — Frontend Application
 * Handles authentication, CRUD operations, and UI state management.
 */
(function () {
    "use strict";

    const API_BASE = "";

    // ===== DOM References =====
    const authSection = document.getElementById("auth-section");
    const notesSection = document.getElementById("notes-section");
    const navUserSection = document.getElementById("nav-user-section");
    const navUserEmail = document.getElementById("nav-user-email");
    const authTitle = document.getElementById("auth-title");
    const authSubtitle = document.getElementById("auth-subtitle");
    const authAlert = document.getElementById("auth-alert");
    const notesAlert = document.getElementById("notes-alert");
    const loginForm = document.getElementById("login-form");
    const registerForm = document.getElementById("register-form");
    const authToggle = document.getElementById("auth-toggle");
    const authToggleText = document.getElementById("auth-toggle-text");
    const btnLogout = document.getElementById("btn-logout");
    const btnNewNote = document.getElementById("btn-new-note");
    const notesContainer = document.getElementById("notes-container");
    const notesEmpty = document.getElementById("notes-empty");
    const notesLoading = document.getElementById("notes-loading");
    const noteModal = new bootstrap.Modal(document.getElementById("note-modal"));
    const noteModalTitle = document.getElementById("note-modal-title");
    const noteIdField = document.getElementById("note-id");
    const noteTitulo = document.getElementById("note-titulo");
    const noteContenido = document.getElementById("note-contenido");
    const tituloCount = document.getElementById("titulo-count");
    const contenidoCount = document.getElementById("contenido-count");
    const btnSaveNote = document.getElementById("btn-save-note");
    const deleteModal = new bootstrap.Modal(document.getElementById("delete-modal"));
    const btnConfirmDelete = document.getElementById("btn-confirm-delete");

    let isLoginMode = true;
    let deleteNoteId = null;
    let recaptchaSiteKey = null;
    let loginWidgetId = null;
    let registerWidgetId = null;

    // ===== Utility Functions =====

    function getToken() {
        return localStorage.getItem("access_token");
    }

    function setToken(token) {
        localStorage.setItem("access_token", token);
    }

    function getRefreshToken() {
        return localStorage.getItem("refresh_token");
    }

    function setRefreshToken(token) {
        localStorage.setItem("refresh_token", token);
    }

    function clearToken() {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        localStorage.removeItem("user_email");
    }

    function getUserEmail() {
        return localStorage.getItem("user_email");
    }

    function setUserEmail(email) {
        localStorage.setItem("user_email", email);
    }

    function showAlert(element, message, type) {
        element.className = `alert alert-${type}`;
        element.textContent = message;
        element.classList.remove("d-none");
        setTimeout(() => element.classList.add("d-none"), 5000);
    }

    function escapeHtml(text) {
        const div = document.createElement("div");
        div.textContent = text;
        return div.innerHTML;
    }

    function formatDate(dateStr) {
        const d = new Date(dateStr);
        return d.toLocaleDateString("es-ES", {
            day: "2-digit",
            month: "short",
            year: "numeric",
            hour: "2-digit",
            minute: "2-digit",
        });
    }

    async function apiRequest(path, options = {}) {
        const headers = { "Content-Type": "application/json" };
        const token = getToken();
        if (token) {
            headers["Authorization"] = `Bearer ${token}`;
        }
        const response = await fetch(`${API_BASE}${path}`, {
            ...options,
            headers: { ...headers, ...options.headers },
        });

        if (response.status === 401) {
            clearToken();
            showAuthView();
            return null;
        }

        if (response.status === 403 || response.status === 404) {
             // Handle Forbidden / Anti-IDOR 404
             const data = await response.json().catch(() => ({}));
             return { error: data.error || "No tienes permiso para acceder a este recurso.", _status: response.status };
        }

        if (response.status === 204) {
            return { _status: 204 };
        }

        const data = await response.json();
        data._status = response.status;
        return data;
    }

    // ===== View Management =====

    function showAuthView() {
        authSection.classList.remove("d-none");
        notesSection.classList.add("d-none");
        navUserSection.classList.add("d-none");
    }

    function showNotesView() {
        authSection.classList.add("d-none");
        notesSection.classList.remove("d-none");
        navUserSection.classList.remove("d-none");
        navUserEmail.textContent = getUserEmail();
        loadNotes();
    }

    function toggleAuthMode() {
        isLoginMode = !isLoginMode;
        authAlert.classList.add("d-none");

        if (isLoginMode) {
            loginForm.classList.remove("d-none");
            registerForm.classList.add("d-none");
            authTitle.textContent = "Iniciar Sesión";
            authSubtitle.textContent = "Accede a tus notas privadas";
            authToggleText.innerHTML =
                '¿No tienes cuenta? <a href="#" id="auth-toggle" class="text-decoration-none fw-semibold">Regístrate</a>';
        } else {
            loginForm.classList.add("d-none");
            registerForm.classList.remove("d-none");
            authTitle.textContent = "Crear Cuenta";
            authSubtitle.textContent = "Regístrate para empezar";
            authToggleText.innerHTML =
                '¿Ya tienes cuenta? <a href="#" id="auth-toggle" class="text-decoration-none fw-semibold">Inicia sesión</a>';
        }

        if (window.grecaptcha && loginWidgetId !== null && registerWidgetId !== null) {
            try {
                grecaptcha.reset(loginWidgetId);
                grecaptcha.reset(registerWidgetId);
            } catch (e) {
                console.error("Error resetting reCAPTCHA:", e);
            }
        }

        // Re-attach event listener since we replaced the element
        document.getElementById("auth-toggle").addEventListener("click", (e) => {
            e.preventDefault();
            toggleAuthMode();
        });
    }

    // ===== Auth Handlers =====

    loginForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const email = document.getElementById("login-email").value.trim();
        const password = document.getElementById("login-password").value;
        const recaptcha_token = e.target.querySelector('[name="g-recaptcha-response"]')?.value || "";

        if (!recaptcha_token) {
            showAlert(authAlert, "Por favor, completa el botón 'No soy un robot'.", "danger");
            return;
        }

        const data = await apiRequest("/api/auth/login", {
            method: "POST",
            body: JSON.stringify({ email, password, recaptcha_token }),
        });

        if (!data) return;

        if (data._status !== 200) {
            showAlert(authAlert, data.error || "Error al iniciar sesión.", "danger");
            if (window.grecaptcha && loginWidgetId !== null) {
                grecaptcha.reset(loginWidgetId);
            }
            return;
        }

        setToken(data.access_token);
        if (data.refresh_token) {
            setRefreshToken(data.refresh_token);
        }
        setUserEmail(email);
        loginForm.reset();
        showNotesView();
    });

    registerForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const email = document.getElementById("register-email").value.trim();
        const password = document.getElementById("register-password").value;
        const password_confirm = document.getElementById("register-password-confirm").value;
        const recaptcha_token = e.target.querySelector('[name="g-recaptcha-response"]')?.value || "";

        if (!recaptcha_token) {
            showAlert(authAlert, "Por favor, completa el botón 'No soy un robot'.", "danger");
            return;
        }

        const data = await apiRequest("/api/auth/register", {
            method: "POST",
            body: JSON.stringify({ email, password, password_confirm, recaptcha_token }),
        });

        if (!data) return;

        if (data._status !== 201) {
            showAlert(authAlert, data.error || "Error al registrar.", "danger");
            if (window.grecaptcha && registerWidgetId !== null) {
                grecaptcha.reset(registerWidgetId);
            }
            return;
        }

        showAlert(authAlert, "¡Cuenta creada! Ahora inicia sesión.", "success");
        registerForm.reset();
        toggleAuthMode();
    });

    btnLogout.addEventListener("click", async () => {
        const refresh_token = getRefreshToken();
        await apiRequest("/api/auth/logout", { 
            method: "POST",
            body: JSON.stringify({ refresh_token })
        });
        clearToken();
        showAuthView();
    });

    authToggle.addEventListener("click", (e) => {
        e.preventDefault();
        toggleAuthMode();
    });

    // ===== Notes CRUD =====

    async function loadNotes() {
        notesLoading.classList.remove("d-none");
        notesEmpty.classList.add("d-none");
        notesContainer.innerHTML = "";

        const data = await apiRequest("/api/notes");
        notesLoading.classList.add("d-none");

        if (!data) return;

        if (!Array.isArray(data)) {
            showAlert(notesAlert, data.error || "Error al cargar notas.", "danger");
            return;
        }

        if (data.length === 0) {
            notesEmpty.classList.remove("d-none");
            return;
        }

        data.forEach((note) => {
            const col = document.createElement("div");
            col.className = "col-12 col-sm-6 col-lg-4";
            col.innerHTML = `
                <div class="note-card" data-id="${note.id}">
                    <div class="note-title">${escapeHtml(note.titulo)}</div>
                    <div class="note-snippet">${escapeHtml(note.snippet || "")}</div>
                    <div class="note-meta">
                        <span class="note-date">
                            <i class="bi bi-clock me-1"></i>${formatDate(note.created_at)}
                        </span>
                        <div class="note-actions">
                            <button class="note-action-btn edit" title="Editar">
                                <i class="bi bi-pencil"></i>
                            </button>
                            <button class="note-action-btn delete" title="Eliminar">
                                <i class="bi bi-trash"></i>
                            </button>
                        </div>
                    </div>
                </div>`;

            col.querySelector(".note-card").addEventListener("click", () => {
                window.app.viewNote(note.id);
            });

            col.querySelector(".edit").addEventListener("click", (e) => {
                e.stopPropagation();
                window.app.editNote(note.id);
            });

            col.querySelector(".delete").addEventListener("click", (e) => {
                e.stopPropagation();
                window.app.deleteNote(note.id);
            });

            notesContainer.appendChild(col);
        });
    }

    btnNewNote.addEventListener("click", () => {
        noteIdField.value = "";
        noteTitulo.value = "";
        noteContenido.value = "";
        tituloCount.textContent = "0";
        contenidoCount.textContent = "0";
        noteModalTitle.textContent = "Nueva Nota";
        noteModal.show();
    });

    // Character counters
    noteTitulo.addEventListener("input", () => {
        tituloCount.textContent = noteTitulo.value.length;
    });

    noteContenido.addEventListener("input", () => {
        contenidoCount.textContent = noteContenido.value.length;
    });

    btnSaveNote.addEventListener("click", async () => {
        const id = noteIdField.value;
        const titulo = noteTitulo.value.trim();
        const contenido = noteContenido.value.trim();

        if (!titulo || !contenido) {
            showAlert(notesAlert, "Título y contenido son obligatorios.", "warning");
            noteModal.hide();
            return;
        }

        let data;
        if (id) {
            data = await apiRequest(`/api/notes/${id}`, {
                method: "PUT",
                body: JSON.stringify({ titulo, contenido }),
            });
        } else {
            data = await apiRequest("/api/notes", {
                method: "POST",
                body: JSON.stringify({ titulo, contenido }),
            });
        }

        noteModal.hide();

        if (!data) return;

        if (data.error) {
            showAlert(notesAlert, data.error, "danger");
            return;
        }

        showAlert(notesAlert, id ? "Nota actualizada." : "Nota creada.", "success");
        loadNotes();
    });

    // ===== Global API (for inline onclick handlers) =====
    window.app = {
        async viewNote(id) {
            const data = await apiRequest(`/api/notes/${id}`);
            if (!data || data.error) {
                showAlert(notesAlert, (data && data.error) || "Error al cargar la nota.", "danger");
                return;
            }
            noteIdField.value = data.id;
            noteTitulo.value = data.titulo;
            noteContenido.value = data.contenido;
            tituloCount.textContent = data.titulo.length;
            contenidoCount.textContent = data.contenido.length;
            noteModalTitle.textContent = "Ver / Editar Nota";
            noteModal.show();
        },

        async editNote(id) {
            this.viewNote(id);
        },

        deleteNote(id) {
            deleteNoteId = id;
            deleteModal.show();
        },
    };

    btnConfirmDelete.addEventListener("click", async () => {
        if (!deleteNoteId) return;

        const data = await apiRequest(`/api/notes/${deleteNoteId}`, {
            method: "DELETE",
        });

        deleteModal.hide();

        if (!data) return;

        if (data.error) {
            showAlert(notesAlert, data.error, "danger");
            return;
        }

        showAlert(notesAlert, "Nota eliminada.", "success");
        deleteNoteId = null;
        loadNotes();
    });

    // ===== Init =====
    async function init() {
        // Fetch public config
        try {
            const config = await apiRequest("/api/config");
            if (config && config.recaptcha_site_key) {
                recaptchaSiteKey = config.recaptcha_site_key;
                renderRecaptcha();
            }
        } catch (e) {
            console.error("Failed to load config:", e);
        }

        if (getToken()) {
            showNotesView();
        } else {
            showAuthView();
        }
    }

    function renderRecaptcha() {
        if (typeof grecaptcha === 'undefined' || typeof grecaptcha.render !== 'function' || !recaptchaSiteKey) {
            setTimeout(renderRecaptcha, 500);
            return;
        }

        try {
            if (loginWidgetId === null) {
                loginWidgetId = grecaptcha.render("recaptcha-login", {
                    'sitekey': recaptchaSiteKey
                });
            }
            if (registerWidgetId === null) {
                registerWidgetId = grecaptcha.render("recaptcha-register", {
                    'sitekey': recaptchaSiteKey
                });
            }
        } catch (e) {
            console.error("reCAPTCHA render error:", e);
        }
    }

    init();
})();
