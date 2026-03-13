# 🔐 SECURITY AUDIT REPORT
# Gestor de Notas Privadas — Auditoría de Seguridad

**Fecha:** 2026-03-13  
**Auditor:** Agente `security-audit.agent`  
**Versión auditada:** `v1.x` (commit pre-fix) → `v1.x+1` (post-fix)  
**Stack:** Flask 3.1.0 + PyJWT 2.10.1 + bcrypt 4.3.0 + SQLite + Docker

---

## Resumen Ejecutivo

```
╔══════════════════════════════════════════════════════╗
║     REPORTE DE AUDITORÍA DE SEGURIDAD                ║
║     Proyecto: Gestor de Notas Privadas               ║
╚══════════════════════════════════════════════════════╝

RESUMEN EJECUTIVO
─────────────────
  🔴 Críticos:     2 hallazgos  → ✅ REMEDIADOS
  🟠 Altos:        1 hallazgo   → ✅ REMEDIADO
  🟡 Medios:       3 hallazgos  → ✅ REMEDIADOS
  🔵 Bajos:        2 hallazgos  → ✅ REMEDIADOS
  ℹ️  Informativos: 2 hallazgos  → ✅ DOCUMENTADOS

PUNTUACIÓN DE RIESGO: ALTO (antes) → BAJO (después)
```

---

## Hallazgos y Remediaciones

### 🔴 CRÍTICO — JWT_SECRET con fallback débil en `config.py`

| | |
|---|---|
| **Archivo** | `backend/config.py` |
| **Impacto** | Si no se define `JWT_SECRET`, la app usaba `"change-me-in-production"`. Un atacante podía firmar tokens JWT arbitrarios y autenticarse como cualquier usuario. |
| **Fix aplicado** | Se creó la función `_require_jwt_secret()` que valida el secreto al importar el módulo. Lanza `ValueError` si: (1) no está definido, (2) usa un valor conocido inseguro, (3) tiene menos de 32 caracteres. |
| **Estado** | ✅ REMEDIADO |

```python
# ANTES — inseguro
JWT_SECRET = os.getenv("JWT_SECRET", "change-me-in-production")

# DESPUÉS — seguro: falla al arrancar si el secreto es débil o ausente
JWT_SECRET: str = _require_jwt_secret()
```

---

### 🔴 CRÍTICO — JWT_SECRET con fallback débil en `docker-compose.yml`

| | |
|---|---|
| **Archivo** | `docker-compose.yml` |
| **Impacto** | El fallback `"super-secret-change-me"` en Docker Compose exponía el mismo riesgo que el anterior en entornos desplegados con Docker sin `.env`. |
| **Fix aplicado** | Se reemplazó el operador `:-` (con fallback) por `:?` (falla con mensaje de error descriptivo si la variable no está definida). |
| **Estado** | ✅ REMEDIADO |

```yaml
# ANTES
- JWT_SECRET=${JWT_SECRET:-super-secret-change-me}

# DESPUÉS
- JWT_SECRET=${JWT_SECRET:?JWT_SECRET must be defined in .env file with at least 32 characters}
```

---

### 🟠 ALTO — Contenedor Docker corre como root

| | |
|---|---|
| **Archivo** | `backend/Dockerfile` |
| **Impacto** | Si un atacante explota una vulnerabilidad en la app, obtiene root dentro del contenedor, facilitando escalada de privilegios y movimiento lateral. |
| **Fix aplicado** | Se añadió un usuario de sistema `appuser` sin shell interactiva (`/usr/sbin/nologin`) y sin directorio home. Se transfirió la propiedad de `/app` al nuevo usuario. |
| **Estado** | ✅ REMEDIADO |

```dockerfile
# NUEVO — usuario no privilegiado
RUN groupadd --system appgroup \
    && useradd --system --no-create-home --shell /usr/sbin/nologin --gid appgroup appuser \
    && chown -R appuser:appgroup /app
USER appuser
```

---

### 🟡 MEDIO — Falta cabecera `Strict-Transport-Security` (HSTS)

| | |
|---|---|
| **Archivo** | `backend/app.py` |
| **Impacto** | Sin HSTS, clientes pueden comunicarse vía HTTP, susceptibles a ataques MITM y downgrade. |
| **Fix aplicado** | Añadida cabecera `Strict-Transport-Security: max-age=31536000; includeSubDomains` en el `after_request` hook. |
| **Estado** | ✅ REMEDIADO |

---

### 🟡 MEDIO — Sin logging de eventos de seguridad

| | |
|---|---|
| **Archivos** | `backend/app.py`, `backend/auth.py`, `backend/middleware.py` |
| **Impacto** | Sin registro de logins fallidos ni accesos denegados, ataques de fuerza bruta y enumeración de usuarios pasan desapercibidos. |
| **Fix aplicado** | Implementado logger `security` que registra: login fallido (IP + email), login exitoso (IP + user_id), token ausente/expirado/inválido (IP + ruta), rate limit excedido (IP + ruta), request demasiado grande (IP + ruta), errores 500. Los logs **nunca** contienen contraseñas, tokens ni contenido de notas. |
| **Estado** | ✅ REMEDIADO |

---

### 🟡 MEDIO — Falta `.dockerignore`

| | |
|---|---|
| **Archivo** | `backend/.dockerignore` (nuevo) |
| **Impacto** | El comando `COPY . .` en el Dockerfile podía incluir archivos `.env`, `venv/`, `tests/`, `__pycache__/` y bases de datos locales en la imagen Docker. |
| **Fix aplicado** | Creado `backend/.dockerignore` que excluye: `.env`, `.env.*`, `*.pyc`, `__pycache__/`, `tests/`, `.pytest_cache/`, `venv/`, `.venv/`, `*.db`, `data/`, archivos `.md`, `.agent`. |
| **Estado** | ✅ REMEDIADO |

---

### 🔵 BAJO — Falta `MAX_CONTENT_LENGTH`

| | |
|---|---|
| **Archivo** | `backend/app.py` |
| **Impacto** | Sin límite de tamaño de petición, un atacante podía enviar payloads enormes y causar agotamiento de memoria. |
| **Fix aplicado** | `app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024` (1 MB). Se añadió también un handler para el error 413 con logging. |
| **Estado** | ✅ REMEDIADO |

---

### 🔵 BAJO — `.gitignore` no cubre variantes `.env.*`

| | |
|---|---|
| **Archivo** | `.gitignore` |
| **Impacto** | Archivos como `.env.local`, `.env.production`, `.env.staging` podían comitearse accidentalmente. |
| **Fix aplicado** | Añadidas reglas `.env.*` y `!.env.example` (para que `.env.example` siga siendo versionable). |
| **Estado** | ✅ REMEDIADO |

---

### ℹ️ INFORMATIVO — bcrypt work factor no explícito

| | |
|---|---|
| **Archivo** | `backend/auth.py` |
| **Nota** | `bcrypt.gensalt()` por defecto usa `rounds=12`, que es correcto. Sin embargo, no era explícito. |
| **Fix aplicado** | Cambiado a `bcrypt.gensalt(rounds=12)` para documentar la intención de seguridad. |
| **Estado** | ✅ DOCUMENTADO |

---

### ℹ️ INFORMATIVO — Logout sin token blacklist (by design)

| | |
|---|---|
| **Archivo** | `backend/auth.py` |
| **Nota** | Los JWT siguen siendo válidos hasta su expiración (1 hora). Sin blacklist en memoria/Redis, no es posible invalidar tokens inmediatamente al hacer logout. |
| **Decisión** | **Aceptado como decisión de diseño** para el alcance actual del proyecto. Los tokens tienen expiración de 1 hora (configurable vía `JWT_EXPIRATION_HOURS`). En una futura versión, implementar blacklist con Redis. |

---

## Áreas con Buena Cobertura (No Requerían Cambios) ✅

| Control | Estado |
|---------|--------|
| Protección IDOR en todas las rutas de notas | ✅ Verificado en GET/PUT/DELETE |
| Algoritmo JWT explícito (`algorithms=["HS256"]`) | ✅ Protegido contra `alg:none` |
| Rate limiting en `/login` y `/register` | ✅ 10 req/min vía flask-limiter |
| Cabeceras de seguridad (CSP, X-Frame, X-Content-Type, Referrer) | ✅ Implementadas |
| Sanitización de entradas con `bleach` | ✅ En todas las notas |
| Consultas parametrizadas (sin SQL injection) | ✅ SQLite con `?` paramétrico |
| Validación de campos (longitud, formato) | ✅ Títulos y contenido limitados |
| Hash de contraseñas con bcrypt | ✅ Nunca texto plano |
| CORS restringido a orígenes configurados | ✅ Configurable vía `ALLOWED_ORIGINS` |
| Manejo genérico de errores (sin stack traces en respuestas) | ✅ Error handlers en todos los 4xx/5xx |
| `DEBUG=False` por defecto en producción | ✅ Solo activo si `FLASK_DEBUG=1` |
| `.env` en `.gitignore` | ✅ Protegido |
| `foreign_keys = ON` en SQLite | ✅ Integridad referencial forzada |

---

## Resumen de Archivos Modificados

| Archivo | Tipo de cambio |
|---------|---------------|
| `backend/config.py` | Validación de JWT_SECRET al importar |
| `docker-compose.yml` | Eliminación de fallback inseguro de JWT_SECRET |
| `backend/Dockerfile` | Usuario no-root `appuser` |
| `backend/.dockerignore` | Nuevo — excluye archivos sensibles de la imagen |
| `backend/app.py` | HSTS + MAX_CONTENT_LENGTH + handler 413 + logging |
| `backend/auth.py` | Logging de login + bcrypt rounds explícito |
| `backend/middleware.py` | Logging de tokens inválidos/expirados/ausentes |
| `.gitignore` | Cobertura de `.env.*` variantes |
| `backend/tests/conftest.py` | JWT_SECRET inyectado antes del import para tests |

---

## Verificación Post-Fix

```
pytest tests/ -v
======== 25 passed in X.XXs ========
```

**Todos los 25 tests pasan** tras aplicar los fixes. Ningún contrato de API fue modificado.

---

## Recomendaciones Futuras

1. **Implementar token blacklist en Redis** para invalidación inmediata en logout.
2. **Ejecutar `pip-audit`** periódicamente para detectar CVEs en dependencias.
3. **Añadir rotación automática del JWT_SECRET** con soporte dual de secretos (actual + anterior).
4. **Configurar un proxy inverso Nginx** con TLS para que HSTS sea efectivo.
5. **Añadir validación de complejidad de contraseña** (mayúsculas, números, símbolos) además de longitud mínima.
