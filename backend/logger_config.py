import logging
import logging.handlers
import json
import os
from datetime import datetime, timezone

class SecurityJSONFormatter(logging.Formatter):
    """Formateador de logs en JSON estructurado para SIEM."""
    def format(self, record):
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "event": record.getMessage(),
            "logger": record.name,
            "module": record.module,
            "line": record.lineno,
        }
        return json.dumps(log_entry, ensure_ascii=False)

def setup_security_logging():
    """Configura logging de seguridad estructurado con rotación de archivos."""
    os.makedirs('logs', exist_ok=True)
    
    security_handler = logging.handlers.RotatingFileHandler(
        'logs/security.log',
        maxBytes=10 * 1024 * 1024,  # 10MB por archivo
        backupCount=30,              # Mantener 30 días de logs
        encoding='utf-8'
    )
    security_handler.setFormatter(SecurityJSONFormatter())
    security_handler.setLevel(logging.INFO)

    security_logger = logging.getLogger('security')
    security_logger.setLevel(logging.INFO)
    security_logger.addHandler(security_handler)
    security_logger.propagate = False  # No propagar al logger raíz
