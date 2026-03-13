# Changelog

Todos los cambios notables de este proyecto se documentan aquí.

## [1.0.0] - 2026-03-13

### Añadido
- **Autenticación**: Registro de usuarios con validación de email y contraseña (bcrypt hash).
- **Login**: Inicio de sesión con JWT (expiración configurable, por defecto 1 hora).
- **Logout**: Endpoint para cerrar sesión (invalidación en cliente).
- **CRUD de Notas**: Crear, listar, ver, editar y borrar notas privadas.
- **Autorización**: Cada usuario solo puede acceder a sus propias notas (`user_id` verificado en cada operación).
- **Validación server-side**: Email formato RFC, contraseña mínimo 8 caracteres, título ≤ 200 chars, contenido ≤ 50.000 chars.
- **Sanitización**: Limpieza de HTML con `bleach` para prevenir XSS.
- **Seguridad**:
    - WAF (Web Application Firewall) ligero para bloquear SQLi, XSS, Path Traversal y Command Injection.
    - Estructura Dual JWT (Access Token 15m + Refresh Token 7d) con almacenamiento seguro.
    - Blacklist de tokens (invalidación forzada al logout).
    - Bloqueo Progresivo (Progressive Lockout) basado en IP para mitigar ataques de fuerza bruta.
    - Integración con Google reCAPTCHA v2 para prevenir registros y logins automatizados.
    - Políticas de seguridad reforzadas con Talisman y CORS (lista blanca estricta).
    - Prevención de IDOR: Los recursos no autorizados devuelven 404 para minimizar la fuga de información (Superficie Mínima).
    - Registro Estructurado (Structured JSON Logging) de eventos de seguridad.
- **Frontend**: SPA con Bootstrap 5, tema oscuro premium, animaciones y diseño responsive.
- **Docker**: Dockerfile en `/backend` y `docker-compose.yml` en raíz con volumen para persistencia SQLite.
- **Tests**: Suite de tests con pytest cubriendo registro, login, CRUD de notas, aislamiento de autorización y validación.
- **Documentación**: README con instrucciones de ejecución, variables de entorno y ejemplos curl.
- **Scripts**: `init_db.py` para migración de base de datos, `Makefile` con targets útiles.
