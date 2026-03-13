from flask_limiter import Limiter
from middleware import get_client_ip

limiter = Limiter(
    key_func=get_client_ip,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
    headers_enabled=True,
)
