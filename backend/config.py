import os
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(dotenv_path=env_path)


import sys

REQUIRED_ENV_VARS = {
    'JWT_SECRET': {
        'min_length': 64,
        'description': 'Secreto JWT (genera con: openssl rand -hex 64)'
    },
    'ENCRYPTION_MASTER_KEY': {
        'min_length': 32,
        'description': 'Clave de cifrado de notas'
    },
    'DATABASE_URL': {
        'min_length': 10,
        'description': 'URL de conexión a la base de datos'
    },
}

def validate_environment():
    """Valida todas las variables de entorno requeridas al arranque. Falla rápido."""
    errors = []
    # If test mode, bypass this strict validation
    if os.environ.get("FLASK_ENV") == "testing" or os.environ.get("TESTING") == "true":
        return

    for var, config in REQUIRED_ENV_VARS.items():
        value = os.environ.get(var, '')
        if not value:
            errors.append(f"[CRÍTICO] Variable de entorno '{var}' no definida. {config['description']}")
        elif len(value) < int(config['min_length']):
            errors.append(
                f"[CRÍTICO] '{var}' demasiado corta ({len(value)} chars). "
                f"Mínimo: {config['min_length']} chars."
            )

    # Detectar secretos débiles conocidos
    WEAK_SECRETS = {'secret', 'password', 'changeme', 'test', '12345', 'dev', 'random-secret-string'}
    jwt_secret = os.environ.get('JWT_SECRET', '').lower()
    if any(weak in jwt_secret for weak in WEAK_SECRETS):
        errors.append("[CRÍTICO] JWT_SECRET contiene un valor débil o de ejemplo.")

    if errors:
        for error in errors:
            print(f"ERROR DE CONFIGURACIÓN: {error}", file=sys.stderr)
        sys.exit(1)  # Falla rápido — nunca arrancar con config insegura

# Llamar en el inicio de config.py ANTES de cualquier otra inicialización
validate_environment()
class Config:
    """Application configuration loaded from environment variables."""
    JWT_SECRET: str = os.getenv("JWT_SECRET", "")
    ENCRYPTION_MASTER_KEY: str = os.getenv("ENCRYPTION_MASTER_KEY", "")
    JWT_EXPIRATION_HOURS: int = int(os.getenv("JWT_EXPIRATION_HOURS", "1"))
    PORT: int = int(os.getenv("PORT", "5000"))
    DATABASE_URL: str = os.getenv("DATABASE_URL", os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "data", "notes.db"
    ))
    DEBUG: bool = os.getenv("FLASK_DEBUG", "0") == "1"
    ALLOWED_ORIGINS: list = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:5000").split(",") if o.strip()]
    TITLE_MAX_LENGTH: int = 200
    CONTENT_MAX_LENGTH: int = 50000
    RECAPTCHA_SECRET_KEY: str = os.getenv("RECAPTCHA_SECRET_KEY", "6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe")
    RECAPTCHA_SITE_KEY: str = os.getenv("RECAPTCHA_SITE_KEY", "6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI")


