from flask import Blueprint, current_app, flash, redirect, render_template, request, session
from flask_mail import Mail, Message
from requests import get as get_avatar
from sqlalchemy import select
from uuid import uuid4
from werkzeug.security import check_password_hash, generate_password_hash

import os

from database import db, User
from helpers import logged_in, login_required

# Configure blueprint
blueprint = Blueprint("general", __name__)


@blueprint.route("/")
def index():
    """Return main page or dashboard depending on whether user is logged in or not."""
    if logged_in():
        return render_template("dashboard.html")

    return render_template("index.html")


@blueprint.route("/account")
def account():
    """Return signup/login page."""
    return render_template("account.html")


@blueprint.route("/signup", methods=["POST"])
def signup():
    """Route users use to sign up for an account."""
    username = request.form.get("username")
    email = request.form.get("email")
    password = request.form.get("password")

    if not username or not email or not password:
        # Information not provided
        flash("Oops, looks like some fields are missing! Fill out everything to continue.")
        return redirect("/account")

    # Create avatar for user
    avatar_data = get_avatar(f"https://avatars.dicebear.com/api/initials/{username}.svg").content
    avatar_filename = os.path.join(current_app.config["AVATAR_FOLDER"], f"{email}.svg")
    with open(avatar_filename, "wb") as file:
        file.write(avatar_data)

    # Create unique ID
    uid = str(uuid4())
    while db.session.execute(
            select(User).where(User.uid == uid)
        ).fetchone():
            # ID isn't unique, so generate new one
            uid = str(uuid4())

    # Create user
    user = User(
        uid=uid,
        username=username,
        email=email,
        password=generate_password_hash(password),
        avatar=avatar_filename.replace("\\", "/"),
        token=str(uuid4())
    )

    db.session.add(user)
    db.session.commit()

    # Send verification email
    mail = Mail()
    msg = Message(
        subject="OfficeHours - Verify email",
        sender=current_app.config["MAIL_USERNAME"],
        recipients=[user.email]
    )
    msg.html = render_template(
        "verify.html",
        name=user.username,
        email=user.email,
        token=user.token
    )
    mail.send(msg)

    flash("We've sent a verification link to your email inbox. Once you verify your email, you can start using OfficeHours!")
    return redirect("/")


@blueprint.route("/login", methods=["POST"])
def login():
    """Route users use to log into their account."""
    email = request.form.get("email")
    password = request.form.get("password")

    if not email or not password:
        # Information not provided
        flash("Oops, looks like some fields are missing! Fill out everything to continue.")
        return redirect("/account")

    user = db.session.execute(
        select(User).where(
            User.email == email
        )
    ).fetchone()

    if not user:
        # User doesn't exist
        flash("Oops, it looks like you haven't made an account yet! Try signing up first.")
        return redirect("/account")
    elif user[0].token:
        # User hasn't verified their email yet
        flash("Oops, it looks like you haven't verified your email yet! Verify it to get started with OfficeHours.")
        return redirect("/account")
    elif not check_password_hash(user[0].password, password):
        # Incorrect password
        flash("Oops, looks like your email or password is incorrect. Try again.")
        return redirect("/account")

    # Log user in
    session["user_id"] = user[0].id
    session["user_uid"] = user[0].uid

    return redirect("/")


@blueprint.route("/logout")
@login_required
def logout():
    """Log out users."""
    session.clear()
    return redirect("/")


@blueprint.route("/verify")
def verify():
    """Verify user email."""
    email = request.args.get("email")
    token = request.args.get("token")

    if not email or not token:
        # Invalid verification link
        flash("Oops, it looks like you used an invalid verification link.")
        return redirect("/")

    # Check if email and token are in database
    user = db.session.execute(
        select(User).where(
            (User.email == email) &
            (User.token == token)
        )
    ).fetchone()
    if not user:
        # Email and token not in database
        flash("Oops, it looks like you used an invalid verification link.")
        return redirect("/")

    # Clear token so user can log into their account
    user[0].token = None
    db.session.add(user[0])
    db.session.commit()

    flash("Great! Your email has been verfied and you're set to start using OfficeHours.")
    return redirect("/")
