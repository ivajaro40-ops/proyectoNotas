import re
import logging
from flask import request, jsonify
from middleware import get_client_ip

security_logger = logging.getLogger("security")

# Patrones de ataque conocidos
ATTACK_PATTERNS = [
    # SQL Injection
    re.compile(r"(\bUNION\b|\bSELECT\b|\bDROP\b|\bINSERT\b|\bDELETE\b|\bUPDATE\b)", re.IGNORECASE),
    # XSS básico
    re.compile(r"<script[\s\S]*?>|javascript\s*:|on\w+\s*=", re.IGNORECASE),
    # Path Traversal
    re.compile(r"\.\./|\.\.\\|%2e%2e%2f|%2e%2e/", re.IGNORECASE),
    # Command Injection (ajustado para reducir falsos positivos)
    re.compile(r"(;|\|\||&&|`|\$\(|\bexec\b)", re.IGNORECASE),
]

def init_waf(app):
    """Inicializa el WAF ligero para interceptar todas las peticiones entrantes."""
    @app.before_request
    def waf_middleware():
        # 1. Validar Content-Type para peticiones con body
        if request.method in ['POST', 'PUT', 'PATCH']:
            ct = request.content_type or ''
            if not ct.startswith('application/json'):
                return jsonify({"error": "Content-Type debe ser application/json."}), 415

        # 2. Inspección de parámetros y body contra patrones de ataque
        inputs_to_check = []
        inputs_to_check.extend(request.args.values())
        inputs_to_check.extend(request.form.values())
        
        if request.is_json:
            json_data = request.get_json(silent=True) or {}
            if isinstance(json_data, dict):
                for k, v in json_data.items():
                    # Excepción: No inspeccionar contraseñas (contienen símbolos válidos)
                    if any(p in k.lower() for p in ['password', 'pwd', 'secret']):
                        continue
                    if isinstance(v, str):
                        inputs_to_check.append(v)
            elif isinstance(json_data, list):
                for item in json_data:
                    if isinstance(item, str):
                        inputs_to_check.append(item)

        for value in inputs_to_check:
            val_str = str(value)
            for pattern in ATTACK_PATTERNS:
                if pattern.search(val_str):
                    security_logger.critical(
                        "WAF_BLOCK | IP=%s | Pattern=%s | Path=%s",
                        get_client_ip(), pattern.pattern[:50], request.path
                    )
                    return jsonify({"error": "Petición bloqueada por políticas de seguridad."}), 403
