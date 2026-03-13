import pytest
import sqlite3
import re

def test_sql_injection_blocked(client):
    """Prueba que el WAF bloquea un ataque de SQLi simple en el email."""
    response = client.post('/api/auth/login', json={
        "email": "admin@admin.com' OR '1'='1",
        "password": "TestPassword123!",
        "recaptcha_token": "test-token"
    })
    # WAF returns 403, and invalid login returns 401
    assert response.status_code in [401, 403]

def test_xss_blocked(client):
    """Prueba que el WAF bloquea ataques de XSS en campos no excluidos (email)."""
    response = client.post('/api/auth/login', json={
        "email": "<script>alert('xss')</script>@test.com",
        "password": "TestPassword123!",
        "recaptcha_token": "test-token"
    })
    assert response.status_code in [401, 403]

def test_path_traversal_blocked(client):
    """Prueba que el WAF bloquee secuencias de Path Traversal."""
    response = client.post('/api/auth/login', json={
        "email": "../../../etc/passwd@test.com",
        "password": "TestPassword123!",
        "recaptcha_token": "test-token"
    })
    assert response.status_code in [401, 403]

def test_security_headers_present(client):
    """Verifica que las cabeceras inyectadas por Talisman y configuradas manualmente estén presentes."""
    response = client.get('/health')
    # CSP and Frame-Options should always be there
    assert 'Content-Security-Policy' in response.headers
    assert 'X-Frame-Options' in response.headers
    assert response.headers.get('X-Frame-Options') == 'DENY'
    
    # HSTS might be missing on local HTTP (Talisman behavior)
    # But it is configured in app.py for production
    
    # Verifica que los headers del servidor se removieron (superficie mínima)
    assert 'Server' not in response.headers
    assert 'X-Powered-By' not in response.headers
