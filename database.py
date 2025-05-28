import sqlite3
from flask import g

DATABASE = 'database.db'
SCHEMA   = 'schema.sql'

def init_db():
    """Load tables from SCHEMA into DATABASE (run once at startup)."""
    with sqlite3.connect(DATABASE) as conn:
        with open(SCHEMA) as f:
            conn.executescript(f.read())

def get_db():
    """Get (and cache) a per-request SQLite connection on flask.g."""
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(error=None):
    """Close the request’s DB connection, if any."""
    db = g.pop('db', None)
    if db is not None:
        db.close()
