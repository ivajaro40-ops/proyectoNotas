.PHONY: start build test lint clean

# Arranca la aplicación con Docker Compose
start:
	docker-compose up

# Construye la imagen Docker
build:
	docker-compose up --build

# Ejecuta los tests con pytest
test:
	cd backend && python -m pytest tests/ -v

# Ejecuta linting con flake8 (si está instalado)
lint:
	cd backend && python -m flake8 --max-line-length=120 --exclude=__pycache__,data .

# Limpia archivos generados
clean:
	docker-compose down -v
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
