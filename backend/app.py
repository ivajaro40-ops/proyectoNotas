import logging
import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_talisman import Talisman
from extensions import limiter
from config import Config
from database import close_db, init_db
from auth import auth_bp
from notes import notes_bp
from waf import init_waf
from middleware import get_client_ip
from logger_config import setup_security_logging

setup_security_logging()
# Security logger (ahora configurado globalmente por setup_security_logging)
security_logger = logging.getLogger("security")


def create_app(test_config=None):
    """Application factory for the Flask app."""
    app = Flask(
        __name__,
        static_folder="static",
        static_url_path="",
    )

    # --- Configuration ---
    app.config["DATABASE_URL"] = Config.DATABASE_URL
    app.config["JWT_SECRET"] = Config.JWT_SECRET
    app.config["DEBUG"] = Config.DEBUG
    # Limit request body size to 1 MB to prevent basic DoS via large payloads
    app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024
    app.config["PROPAGATE_EXCEPTIONS"] = False

    init_waf(app)

    if test_config:
        app.config.update(test_config)

    # --- CORS ---
    CORS(app, resources={r"/api/*": {"origins": list(Config.ALLOWED_ORIGINS)}})

    # --- Rate Limiting ---
    limiter.init_app(app)

    # --- Security Headers (Talisman) ---
    csp = {
        'default-src': ["'self'"],
        'style-src': ["'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net", "https://fonts.googleapis.com"],
        'script-src': ["'self'", "https://cdn.jsdelivr.net", "https://www.google.com/recaptcha/", "https://www.gstatic.com/recaptcha/"],
        'font-src': ["'self'", "https://fonts.gstatic.com", "https://cdn.jsdelivr.net"],
        'img-src': ["'self'", "data:"],
        'frame-src': ["https://www.google.com/recaptcha/", "https://recaptcha.google.com/recaptcha/"],
        'connect-src': ["'self'"],
        'frame-ancestors': ["'none'"],
        'base-uri': ["'self'"],
        'form-action': ["'self'"],
        'object-src': ["'none'"],
        'upgrade-insecure-requests': [],
    }

    Talisman(
        app,
        force_https=False, # Rely on NGINX for prod https, keep false locally
        strict_transport_security=True,
        strict_transport_security_max_age=31536000,
        strict_transport_security_include_subdomains=True,
        strict_transport_security_preload=True,
        content_security_policy=csp,
        referrer_policy='strict-origin-when-cross-origin',
        x_content_type_options=True,
        x_xss_protection=False,
        frame_options='DENY',
    )

    @app.after_request
    def remove_server_header(response):
        response.headers.pop('Server', None)
        response.headers.pop('X-Powered-By', None)
        response.headers['Cache-Control'] = 'no-store, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        return response

    # --- Blueprints ---
    app.register_blueprint(auth_bp)
    app.register_blueprint(notes_bp)

    # --- Health Check ---
    @app.route('/health', methods=['GET'])
    def health_check():
        return jsonify(status="ok"), 200

    @app.route("/api/config")
    def get_config():
        """Expose necessary public configuration to the frontend."""
        return jsonify({
            "recaptcha_site_key": Config.RECAPTCHA_SITE_KEY
        })

    # --- Serve frontend ---
    @app.route("/")
    def index():
        return app.send_static_file("index.html")

    # --- Error Handlers (Consolidados) ---
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"error": "Solicitud incorrecta."}), 400

    @app.errorhandler(401)
    def unauthorized(e):
        return jsonify({"error": "No autorizado."}), 401

    @app.errorhandler(403)
    def forbidden(e):
        return jsonify({"error": "Acceso prohibido."}), 403

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Recurso no encontrado."}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"error": "Método no permitido."}), 405

    @app.errorhandler(413)
    def request_too_large(e):
        security_logger.warning(
            "Request body too large | ip=%s path=%s", get_client_ip(), request.path
        )
        return jsonify({"error": "La petición supera el tamaño máximo permitido (1 MB)."}), 413

    @app.errorhandler(429)
    def rate_limit_exceeded(e):
        security_logger.warning(
            "Rate limit exceeded | ip=%s path=%s", get_client_ip(), request.path
        )
        return jsonify({"error": "Demasiadas peticiones. Inténtalo más tarde."}), 429

    @app.errorhandler(500)
    def internal_error(e):
        security_logger.error(
            "Internal server error | ip=%s path=%s error=%s",
            get_client_ip(), request.path, str(e)
        )
        return jsonify({"error": "Error interno del servidor."}), 500

    # --- Database lifecycle ---
    app.teardown_appcontext(close_db)

    with app.app_context():
        init_db(app)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=Config.PORT, debug=Config.DEBUG)
