import os
import sqlite3
from flask import g

# --- Database Path Setup ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # folder where this file lives
DB_PATH = os.path.abspath(os.path.join(BASE_DIR, "..", "database.db"))

# --- DB Connection ---
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            DB_PATH,
            detect_types=sqlite3.PARSE_DECLTYPES,
            check_same_thread=False
        )
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()
