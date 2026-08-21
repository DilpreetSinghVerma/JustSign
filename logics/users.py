from functools import wraps
from typing import Callable, Any

from flask import g, session, flash, redirect, url_for
import sqlite3

from werkzeug import Response
from werkzeug.security import generate_password_hash, check_password_hash

from logics.sqlitedb import get_db


def _get_cursor_row_factory():
    """
    Helper to get a cursor that returns sqlite3.Row so rows behave like dicts.
    Assumes get_db() returns an sqlite3.Connection.
    """
    db = get_db()
    db.row_factory = sqlite3.Row
    return db, db.cursor()


def get_user(username):
    """
    Return a user row (sqlite3.Row) for given username or None.
    """
    db, cur = _get_cursor_row_factory()
    cur.execute("SELECT * FROM users WHERE username = ?", (username,))
    return cur.fetchone()


def check_user(username):
    """
    Same as get_user but kept separate for compatibility with your code.
    """
    return get_user(username)


def login(username, password):
    """
    Attempt to log in user: if OK, set session['user'] and g.user.
    """
    if "user" in session:
        g.user = session.get("user")
        return True

    user = get_user(username)
    if not user:
        flash("Invalid username or password.", "danger")
        return False

    stored_hash = user["password"]
    if check_password_hash(stored_hash, password):
        session["user"] = user["username"]
        g.user = user["username"]
        flash("Logged in successfully.", "success")
        return True

    flash("Invalid username or password.", "danger")
    return False


def register(username, password):
    """
    Register a new user. Hashes password before storing.
    """
    if check_user(username):
        flash("Username already exists.", "danger")
        return False

    db = get_db()
    cur = db.cursor()
    pwd_hash = generate_password_hash(password)
    cur.execute(
        "INSERT INTO users (username, password) VALUES (?, ?)",
        (username, pwd_hash)
    )
    db.commit()

    flash("Successfully Registered.", "success")
    return True


def logout():
    session.clear()
    g.user = None
    flash("You have been logged out!", "success")
    return redirect(url_for("homepage"))


def logged_in():
    g.user = session.get("user")
    return session.get("user")


def login_required(f: Callable) -> Callable[[tuple[Any, ...], dict[str, Any]], Response | Any]:
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user" in session:
            g.user = session.get("user")
            return f(*args, **kwargs)
        flash("You need to login first", "danger")
        return redirect(url_for("login_page"))
    return wrapper