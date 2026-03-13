#!/usr/bin/env python3
"""Standalone script to initialize (migrate) the database.

Usage:
    python init_db.py
"""
import os
import sys

# Ensure the backend directory is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app  # noqa: E402

app = create_app()
print(f"✅ Base de datos inicializada en: {app.config['DATABASE_URL']}")
