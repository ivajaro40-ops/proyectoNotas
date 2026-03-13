import os
import sqlite3
from flask import g, current_app


def get_db():
    """Get a database connection for the current request, creating it if needed."""
    if "db" not in g:
        db_path = current_app.config["DATABASE_URL"]
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(e=None):
    """Close the database connection at the end of the request."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(app=None):
    """Create tables from schema.sql if they don't exist."""
    if app is not None:
        db_path = app.config["DATABASE_URL"]
    else:
        db_path = current_app.config["DATABASE_URL"]

    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)

    schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")
    with open(schema_path, "r") as f:
        conn.executescript(f.read())

    conn.commit()
    conn.close()
