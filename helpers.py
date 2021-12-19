from flask import flash, redirect, session
from flask_socketio import SocketIO
from functools import wraps
from sqlalchemy import select

from database import db, User

socketio = SocketIO()


def logged_in():
    """Logged in function that determines if user is logged in."""
    if session.get("user_id") is None or session.get("user_uid") is None:
        # User isn't signed in yet
        return False

    # Make sure user isn't signed in with wrong information
    query = db.session.execute(
        select(User).where(
            (User.id == session["user_id"]) &
            (User.uid == session["user_uid"])
        )
    ).fetchone()
    if not query:
        # User is signed in with wrong information
        session.clear()
        return False

    # User is signed in
    return True


def login_required(f):
    """Authorize function that makes sure user is logged in before they can access a view."""
    @wraps(f)
    def decorate(*args, **kwargs):
        if not logged_in():
            # User isn't logged in yet
            flash("Oops, looks like you need to log in first!")
            return redirect("/account")

        # Apply Flask headers, etc.
        return f(*args, **kwargs)

    return decorate
