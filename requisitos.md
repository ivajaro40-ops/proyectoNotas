# Requisitos detallados por tipo de proyecto

Este documento amplía cada opción del hackathon con requisitos de **login**, **registro** y **especificaciones técnicas** que debe cumplir cada ejemplo.

---

## Requisitos comunes a todos los proyectos

### Registro de usuario
- Formulario con: **email** (o nombre de usuario único) y **contraseña** (y confirmación de contraseña).

### Login (inicio de sesión)
- Formulario con identificador (email o usuario) y contraseña.

### Especificaciones técnicas base
- **Frontend:** HTML5 + CSS (Pico.css, Bootstrap u otro). JavaScript para llamadas a la API y manejo de formularios.
- **Backend:** Express.js (Node) o Flask (Python). Rutas REST para auth y para la lógica del proyecto.
- **Persistencia:** SQLite o archivo JSON en carpeta `/backend`. Al menos una tabla (o estructura) de usuarios con contraseña hasheada.
- **Despliegue:** Docker (Dockerfile en `/backend`) y `docker-compose.yml` en la raíz del proyecto; la app debe levantarse con `docker-compose up --build`.
- **Validación:** no confiar solo en frontend; validar y sanitizar siempre en el backend.
- **Errores:** respuestas HTTP adecuadas y mensajes de error controlados, sin exponer stack traces ni rutas del sistema.

---

## 1. Gestor de Notas Privadas

### Descripción
El usuario se registra, inicia sesión y escribe notas que **solo él** puede ver. Cada nota pertenece a un único usuario.

### Registro y login
- Cumplir los requisitos comunes de registro y login anteriores.
- Tras el login, el usuario solo debe ver sus propias notas.

### Funcionalidad específica
- **Crear nota:** título y contenido (texto); guardar asociada al usuario autenticado.
- **Listar notas:** solo las notas del usuario logueado, ordenadas por fecha (por ejemplo, más recientes primero).
- **Ver una nota:** solo si pertenece al usuario actual
- **Editar nota:** solo el dueño puede modificar título y/o contenido.
- **Eliminar nota:** solo el dueño puede borrarla.

### Modelo de datos (ejemplo)
- **usuarios:** `id`, `email` (o `username`), `password`, `created_at`.
- **notas:** `id`, `user_id` (FK), `titulo`, `contenido`, `created_at`, `updated_at`.

### Especificaciones técnicas
- API protegida: todas las rutas de notas exigen autenticación y comprobación de que el recurso pertenece al usuario.
- En respuestas JSON no incluir campos sensibles (p. ej. `password`); devolver solo lo necesario (id, email o username, etc.).
- Validación: título y contenido no vacíos; límite razonable de longitud para evitar abusos.

---

## Checklist de supervivencia (recordatorio)

Antes de entregar, comprobar en todos los proyectos:

- [ ] **Validación:** formularios vacíos o datos inválidos se rechazan en backend con mensajes claros.
- [ ] **Autenticación:** no se puede acceder a rutas protegidas solo escribiendo la URL sin estar logueado.
- [ ] **Autorización:** cada usuario solo accede a sus propios recursos (notas, mensajes propios, productos propios, su CV).
- [ ] **Reducción de información:** las respuestas no incluyen campos innecesarios ni sensibles (hashes, rutas internas).
- [ ] **Control de errores:** los fallos devuelven mensajes amigables y códigos HTTP adecuados, sin stack traces ni rutas del sistema.
