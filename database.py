
# database.py
import os, pathlib, sqlite3
from flask import g

DATABASE = os.getenv("DATABASE", "/data/database.db")
SCHEMA   = os.getenv("SCHEMA", "/code/schema.sql")

def _ensure_dir():
    pathlib.Path(DATABASE).parent.mkdir(parents=True, exist_ok=True)

def init_db():
    _ensure_dir()
    with sqlite3.connect(DATABASE) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        with open(SCHEMA, "r") as f:
            conn.executescript(f.read())

def ensure_db():
    _ensure_dir()
    p = pathlib.Path(DATABASE)
    if (not p.exists()) or p.stat().st_size == 0:
        init_db()

def get_db():
    if "db" not in g:
        _ensure_dir()
        g.db = sqlite3.connect(DATABASE, check_same_thread=False)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
        g.db.execute("PRAGMA journal_mode = WAL")
    return g.db

def close_db(error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()





