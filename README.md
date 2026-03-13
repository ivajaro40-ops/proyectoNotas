# 🔐 Gestor de Notas Privadas

[![Security: Secure](https://img.shields.io/badge/Security-Secure-brightgreen.svg)](https://github.com/ivajaro40-ops/proyectoNotas)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker: Ready](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)

Una aplicación de gestión de notas personales centrada en la **seguridad**, **privacidad** y **facilidad de despliegue**. Diseñada para mantener tus pensamientos e información importante bajo tu control exclusivo.

---

## 🌟 Características Principales

- **Gestión Completa de Notas (CRUD):** Crea, visualiza, edita y elimina notas personales.
- **Privacidad por Diseño:** Cada usuario solo tiene acceso a sus propias notas. Los datos están aislados a nivel de base de datos mediante identificadores únicos.
- **Arquitectura Segura:** Backend en Flask con autenticación robusta y Frontend dinámico basado en Bootstrap 5.
- **Despliegue Contenerizado:** Lista para producción mediante Docker y Docker Compose.

---

## 🛡️ Seguridad y Robustez

Este proyecto ha sido diseñado siguiendo las mejores prácticas de seguridad:

1.  **Cifrado de Contraseñas:** Utilizamos `bcrypt` con un factor de trabajo robusto para el hasheo de contraseñas antes de almacenarlas en la base de datos. ¡Nunca guardamos una contraseña en texto plano!
2.  **Autenticación JWT (JSON Web Tokens):** El sistema utiliza tokens firmados criptográficamente para gestionar las sesiones de usuario de forma segura y sin estado.
3.  **Protección de Rutas:** Middleware dedicado verifica la validez del token en cada petición sensible, impidiendo el acceso no autorizado a través de la URL.
4.  **Validación en Backend:** Todos los datos recibidos (títulos, contenidos, credenciales) son validados y sanitizados en el servidor para prevenir inyecciones y otros ataques comunes.
5.  **Control de Errores Silencioso:** La aplicación bloquea la exposición de *stack traces* o información interna del sistema en caso de fallos, devolviendo únicamente códigos HTTP y mensajes genéricos seguros.
6.  **Variables de Entorno:** Toda la configuración sensible (secretos, puertos, URLs) se gestiona a través de un archivo `.env`, manteniéndola separada del código fuente.

---

## 🚀 Instalación y Configuración

### 📋 Requisitos Previos

- [Docker](https://www.docker.com/products/docker-desktop) y [Docker Compose](https://docs.docker.com/compose/install/) (Recomendado)
- O Python 3.9+ para ejecución local.

### ⚙️ Configuración del Entorno

1.  Copia el archivo de ejemplo a uno definitivo:
    ```bash
    cp .env.example .env
    ```
2.  Edita el archivo `.env` y define tu `JWT_SECRET`. **¡Usa una cadena larga y aleatoria!**
    ```env
    JWT_SECRET=tu-secreto-super-seguro
    ```

### 🐳 Despliegue con Docker (Recomendado)

La forma más rápida y segura de levantar el proyecto:

```bash
docker-compose up --build -d
```
La aplicación estará disponible en `http://localhost:5000`.

### 🛠️ Ejecución Local (Desarrollo)

Si prefieres ejecutarlo sin Docker:

1.  **Instalar dependencias:**
    ```bash
    cd backend
    python -m venv venv
    ./venv/Scripts/activate  # En Windows
    pip install -r requirements.txt
    ```
2.  **Inicializar Base de Datos:**
    ```bash
    python init_db.py
    ```
3.  **Lanzar servidor:**
    ```bash
    python app.py
    ```

---

## 🛡️ Guía para un Uso Seguro en Producción

Para garantizar que tu instancia sea **totalmente segura**, sigue estas recomendaciones:

-   **Secretos Fuertes:** Genera tu `JWT_SECRET` usando `openssl rand -hex 32`.
-   **HTTPS:** Nunca despliegues esta aplicación en internet sin una capa de SSL/TLS (p. ej. mediante un proxy como Nginx o Caddy).
-   **Limpieza de Logs:** Asegúrate de que los logs de producción no capturen información sensible.
-   **Actualizaciones:** Mantén las dependencias actualizadas revisando el archivo `requirements.txt`.

---

## 🧪 Pruebas (Testing)

El proyecto incluye una suite de pruebas para asegurar que la lógica de seguridad y negocio funciona correctamente:

```bash
cd backend
pytest
```

---

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Consulta el archivo para más detalles.

---

Desarrollado con ❤️ para garantizar tu privacidad.
