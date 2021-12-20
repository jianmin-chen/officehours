from flask import Blueprint, current_app, flash, redirect, render_template, request, session
from flask_mail import Mail
from flask_mail import Message
from sqlalchemy import select
from uuid import uuid4

from database import db, User, Group, Member
from helpers import logged_in, login_required

# Configure blueprint
blueprint = Blueprint("dashboard", __name__)


@blueprint.route("/create", methods=["POST"])
@login_required
def create():
    """Create group route."""
    name = request.form.get("name")

    if not name:
        # Information not provided
        flash("Oops, looks like some fields are missing! Fill out everything to continue.")
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
            (Group.id == group_id) &
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
        email=group[0].creator.email,
        open_time=group[0].creator.open_time.strftime("%H:%M"),
        close_time=group[0].creator.close_time.strftime("%H:%M"),
        timezone=group[0].creator.timezone,
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
