import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from config import Config
from database import close_db, init_db
from auth import auth_bp
from notes import notes_bp


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

    if test_config:
        app.config.update(test_config)

    # --- CORS ---
    CORS(app, resources={r"/api/*": {"origins": Config.ALLOWED_ORIGINS}})

    # --- Rate Limiting ---
    limiter = Limiter(
        key_func=get_remote_address,
        app=app,
        default_limits=["200 per hour"],
        storage_uri="memory://",
    )
    limiter.limit("10 per minute")(auth_bp)

    # --- Security Headers ---
    @app.after_request
    def set_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
            "script-src 'self' https://cdn.jsdelivr.net; "
            "font-src 'self' https://fonts.gstatic.com https://cdn.jsdelivr.net; "
            "img-src 'self' data:;"
        )
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

    # --- Blueprints ---
    app.register_blueprint(auth_bp)
    app.register_blueprint(notes_bp)

    # --- Serve frontend ---
    @app.route("/")
    def index():
        return app.send_static_file("index.html")

    # --- Error handlers ---
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"error": "Solicitud incorrecta."}), 400

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Recurso no encontrado."}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"error": "Método no permitido."}), 405

    @app.errorhandler(429)
    def rate_limit_exceeded(e):
        return jsonify({"error": "Demasiadas peticiones. Inténtalo más tarde."}), 429

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({"error": "Error interno del servidor."}), 500

    # --- Database lifecycle ---
    app.teardown_appcontext(close_db)

    with app.app_context():
        init_db(app)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=Config.PORT, debug=Config.DEBUG)
