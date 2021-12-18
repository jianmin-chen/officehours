from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, session
from flask_mail import Mail, Message
from sqlalchemy import select

from database import db, User, Group, Member, Message
from helpers import logged_in, login_required

# Configure blueprint
blueprint = Blueprint("dashboard", __name__)


@blueprint.route("/create", methods=["POST"])
@login_required
def create():
    """Create group route."""

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


@blueprint.route("/send", methods=["POST"])
def send():
    """Send message route."""
    if not logged_in():
        return jsonify({
            "success": False,
            "error": "Oops, it looks like you're not logged in yet!"
        })

    return jsonify({
        "success": True
    })