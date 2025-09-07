import os, sqlite3
from pathlib import Path
from flask import g

# Resolve to the repo root (folder that contains app.py, schema.sql, etc.)
PROJECT_ROOT = Path(__file__).resolve().parent

# Local defaults: put DB in repo root; read schema from repo root.
# In prod, override via env (e.g., DATABASE=/data/database.db)
DATABASE = Path(os.getenv("DATABASE", str(PROJECT_ROOT / "database.db")))
SCHEMA   = Path(os.getenv("SCHEMA",   str(PROJECT_ROOT / "schema.sql")))

def _ensure_dir():
    DATABASE.parent.mkdir(parents=True, exist_ok=True)

def init_db():
    _ensure_dir()
    with sqlite3.connect(DATABASE) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        with open(SCHEMA, "r", encoding="utf-8") as f:
            conn.executescript(f.read())

def ensure_db():
    _ensure_dir()
    p = Path(DATABASE)
    if (not p.exists()) or p.stat().st_size == 0:
        init_db()

def get_db():
    if "db" not in g:
        _ensure_dir()
        conn = sqlite3.connect(DATABASE, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        g.db = conn
    return g.db

def close_db(error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()





