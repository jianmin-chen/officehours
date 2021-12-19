from datetime import time
from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, session
from flask_mail import Mail, Message
from sqlalchemy import select
from uuid import uuid4

from database import db, User, Group, Member, Message
from helpers import socketio, logged_in, login_required

# Configure blueprint
blueprint = Blueprint("dashboard", __name__)


@blueprint.route("/create", methods=["POST"])
@login_required
def create():
    """Create group route."""
    name = request.form.get("name")
    open_time = request.form.get("openhr")
    close_time = request.form.get("closehr")
    timezone = request.form.get("timezone")

    if not name or not open_time or not close_time or not timezone:
        # Information not provided
        flash("Oops, looks like some fields are missing! Fill out everything to continue.")
        return redirect("/")

    # Make sure time is valid
    open_time = time(*open_time.split(":"))
    close_time = time(*close_time.split(":"))
    if open_time > close_time:
        # Open time is greater than close time
        flash("Oops, it looks like your open time is later than your close time! Try reversing them.")
        return redirect("/")

    # Create unique ID
    uid = str(uuid4())
    while db.session.execute(
            select(Group).where(Group.uid == uid)
        ).fetchone():
            # ID isn't unique, so generate new one
            uid = str(uuid4())

    # Create group in database
    group = Group(
        uid=uid,
        name=name,
        open_time=open_time,
        close_time=close_time,
        timezone=timezone,
        creator_id=session["user_id"]
    )
    db.session.add(group)
    db.session.commit()

    return redirect("/")


@blueprint.route("/invite", methods=["POST"])
@login_required
def invite():
    """Invite member route."""
    group_id = request.form.get("group_id")
    email = request.form.get("email")

    if not group_id or not email:
        # Information not provided
        flash("Oops, looks like there was an error sending an invite email! Try again.")
        return redirect("/")

    group = db.session.execute(
        select(Group).where(
            (Group.id == id) &
            (Group.creator_id == session["user_id"])
        )
    ).fetchone()

    if not group:
        # Group doesn't exist/user isn't authorized to send invite emails
        flash("Oops, looks like there was an error sending an invite email! Try again.")
        return redirect("/")

    # Send invite code
    mail = Mail()
    msg = Message(
        subject="OfficeHours - Invite code",
        sender=current_app.config["MAIL_USERNAME"],
        recipients=[email]
    )
    msg.html = render_template(
        "invite.html",
        code=group[0].uid
    )
    mail.send(msg)

    flash(f"We've sent an invite code to {email}. Once they sign up and join your group using the code, they'll show up in the group!")
    return redirect("/")


@blueprint.route("/join", methods=["POST"])
@login_required
def join():
    """Join group route."""
    code = request.form.get("code")

    if not code:
        # Information not provided
        flash("Oops, it looks like there was an error joining that group! Try again.")
        return redirect("/")

    group = db.session.execute(
        select(Group).where(Group.uid == code)
    ).fetchone()

    if not group:
        # Invalid code
        flash("Oops, it looks like that group doesn't exist!")
        return redirect("/")

    # Add user to group
    member = Member(
        group_id=group[0].id,
        user_id=session["user_id"]
    )
    db.session.add(member)
    db.session.commit()

    flash(f"Cool! You're a member of {group[0].name} now.")
    return redirect("/")


@socketio.on("load_chatroom")
def load_chatroom(json):
    if not logged_in():
        # User isn't logged in
        socketio.emit("Error", {
            "desc": "Oops, looks like you're not logged in yet!"
        })
    socketio.emit("Success", {})


@socketio.on("send")
def send(json):
    if not logged_in():
        # User isn't logged in
        socketio.emit("Error", {
            "desc": "Oops, looks like you're not logged in yet!"
        })
    socketio.emit("Success", {})


@socketio.on("receive")
def receive(json):
    if not logged_in():
        # User isn't logged in
        socketio.emit("Error", {
            "desc": "Oops, looks like you're not logged in yet!"
        })
    socketio.emit("Success", {})
