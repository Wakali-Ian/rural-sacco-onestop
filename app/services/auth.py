"""Session-based auth helpers. No Flask-Login dependency."""
from functools import wraps
from flask import session, redirect, url_for, flash
from app.models.user import User


def login_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please log in first.", "warning")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return wrapped


def current_user():
    uid = session.get("user_id")
    return User.query.get(uid) if uid else None
