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


def role_required(*roles):
    """Decorator: only allow users with these roles."""
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if not session.get("user_id"):
                flash("Please log in first.", "warning")
                return redirect(url_for("auth.login"))
            user = User.query.get(session.get("user_id"))
            if not user or user.role not in roles:
                flash(f"This action requires role: {', '.join(roles)}", "danger")
                return redirect(url_for("dashboard.index"))
            return f(*args, **kwargs)
        return wrapped
    return decorator
