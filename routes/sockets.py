from datetime import date, datetime, time, timedelta
from flask import Blueprint, Flask, current_app, render_template, session
from flask_mail import Mail
from flask_mail import Message as Email
from functools import wraps
from pytz import timezone as pytz_timezone
from sqlalchemy import select
from uuid import uuid4

from database import db, User, Group, Member, Message
from helpers import scheduler, socketio, logged_in

# Configure blueprint
blueprint = Blueprint("sockets", __name__)


def login_required(f):
    """Authorize function that makes sure user is logged in before they can access a route."""
    @wraps(f)
    def decorate(*args, **kwargs):
        if not logged_in():
            # User isn't logged in yet
            socketio.emit("error", {
                "desc": "Oops, looks like you're not logged in yet!"
            })
            return

        return f(*args, **kwargs)

    return decorate


def email(msg, app):
    with app.app_context():
        mail = Mail()
        mail.send(msg)


@socketio.on("load_chatroom/creator")
@login_required
def load_chatroom_as_creator(json):
    group_id = json.get("groupID")
    member_id = json.get("memberID")

    if not group_id or not member_id:
        # Information not provided
        socketio.emit("error", {
            "desc": "Oops, looks like there wasan error loading your chatroom!"
        })
        return

    query = db.session.execute(
        select(Member).where(
            (Member.group_id == group_id) &
            (Member.user_id == member_id)
        )
    ).fetchone()

    if not query:
        # Member is not part of group
        socketio.emit("error", {
            "desc": "Oops, looks like there was an error loading your chatroom!"
        })
        return
    elif query[0].group.creator_id != session["user_id"]:
        # User is not creator of group
        socketio.emit("error", {
            "desc": "Oops, looks like there was an error loading your chatroom!"
        })
        return

    name = query[0].group.name
    receiver_id = query[0].user.id
    receiver_email = query[0].user.email
    receiver_time = f"{query[0].user.open_time.strftime('%H:%M')} - {query[0].user.close_time.strftime('%H:%M')} {query[0].user.timezone}"

    # Get messages
    messages = []
    query = db.session.execute(
        select(Message).where(
            (Message.group_id == group_id) &
            (((Message.sender_id == session["user_id"]) & (Message.receiver_id == member_id)) | ((Message.sender_id == member_id) & (Message.receiver_id == session["user_id"])))
        ).order_by(Message.date.asc())
    ).fetchall()
    for message in query:
        messages.append({
            "self": message[0].sender_id == session["user_id"],
            "content": message[0].content
        })

    socketio.emit(f"load_chatroom/{session['user_id']}/{group_id}", {
        "name": name,
        "id": group_id,
        "receiver_id": receiver_id,
        "receiver_email": receiver_email,
        "receiver_time": receiver_time,
        "messages": messages
    })


@socketio.on("load_chatroom/member")
@login_required
def load_chatroom_as_member(json):
    group_id = json.get("groupID")

    if not group_id:
        # Information not provided
        socketio.emit("error", {
            "desc": "Oops, looks like there was an error loading that chatroom!"
        })
        return

    query = db.session.execute(
        select(Member).where(
            (Member.group_id == group_id) &
            (Member.user_id == session["user_id"])
        )
    ).fetchone()

    if not query:
        # Member is not part of group
        socketio.emit("error", {
            "error": "Oops, looks like there was an error loading your chatroom!",
        })
        return

    name = query[0].group.name
    creator_id = query[0].group.creator_id
    creator_email = query[0].group.creator.email
    creator_time = f"{query[0].group.creator.open_time.strftime('%H:%M')} - {query[0].group.creator.close_time.strftime('%H:%M')} {query[0].group.creator.timezone}"

    # Get messages
    messages = []
    query = db.session.execute(
        select(Message).where(
            (Message.group_id == group_id) &
            (((Message.sender_id == session["user_id"]) & (Message.receiver_id == creator_id)) | ((Message.sender_id == creator_id) & (Message.receiver_id == session["user_id"])))
        ).order_by(Message.date.asc())
    ).fetchall()
    for message in query:
        messages.append({
            "self": message[0].sender_id == session["user_id"],
            "content": message[0].content
        })

    socketio.emit(f"load_chatroom/{session['user_id']}/{group_id}", {
        "name": name,
        "id": group_id,
        "receiver_id": creator_id,
        "receiver_email": creator_email,
        "receiver_time": creator_time,
        "messages": messages
    })


@socketio.on("send")
@login_required
def send(json):
    content = json.get("content")
    group_id = json.get("groupID")
    receiver_id = json.get("receiverID")

    if not content or not group_id or not receiver_id:
        # Information not provided
        socketio.emit("error", {
            "desc": "Oops, looks like there was an error sending your message!"
        })
        return

    # Make sure sender belongs in chatroom
    is_member = db.session.execute(
        select(Member).where(
            (Member.group_id == group_id) &
            (Member.user_id == session["user_id"])
        )
    ).fetchone()
    is_creator = db.session.execute(
        select(Group).where(
            (Group.id == group_id) &
            (Group.creator_id == session["user_id"])
        )
    ).fetchone()

    if is_member:
        sender_email = is_member[0].user.email
    elif is_creator:
        sender_email = is_creator[0].creator.email
    else:
        # Sender doesn't belong in chatroom/chatroom doesn't exist
        socketio.emit("error", {
            "desc": "Oops, looks like there was an error sending your message!"
        })
        return

    # Make sure receiver belongs in chatroom
    is_member = db.session.execute(
        select(Member).where(
            (Member.group_id == group_id) &
            (Member.user_id == receiver_id)
        )
    ).fetchone()
    is_creator = db.session.execute(
        select(Group).where(
            (Group.id == group_id) &
            (Group.creator_id == receiver_id)
        )
    ).fetchone()

    if is_member:
        receiver_name = is_member[0].user.username
        receiver_email = is_member[0].user.email
        group_name = is_member[0].group.name
        open_time = is_member[0].user.open_time
        close_time = is_member[0].user.close_time
        timezone = is_member[0].user.timezone
    elif is_creator:
        receiver_name = is_creator[0].creator.username
        receiver_email = is_creator[0].creator.email
        group_name = is_creator[0].name
        open_time = is_creator[0].creator.open_time
        close_time = is_creator[0].creator.close_time
        timezone = is_creator[0].creator.timezone
    else:
        # Receiver doesn't belong in chatroom
        socketio.emit("error", {
            "desc": "Oops, looks like there was an error sending your message!"
        })
        return

    # Set message in database
    message = Message(
        content=content,
        group_id=group_id,
        sender_id=session["user_id"],
        receiver_id=receiver_id
    )
    db.session.add(message)
    db.session.commit()

    # Send message
    msg = Email(
        subject="OfficeHours - New message",
        sender=current_app.config["MAIL_USERNAME"],
        recipients=[receiver_email]
    )
    msg.html = render_template(
        "message.html",
        name=receiver_name,
        email=sender_email,
        group_name=group_name,
        message=content
    )

    timenow = datetime.now().astimezone(pytz_timezone(timezone))
    timeobj = time(int(timenow.hour), int(timenow.minute))
    if open_time < timeobj < close_time:
        # Send notification now
        email()
    elif timeobj < open_time:
        # Send notification later today
        with current_app.app_context():
            scheduler.add_job(
                id=str(uuid4()),
                func=email,
                trigger="date",
                run_date=datetime(timenow.year, timenow.month, timenow.day, open_time.hour, open_time.minute),
                args=[msg, scheduler.app]
            )
    else:
        # Send notification tomorrow
        timenow = date.today() + timedelta(days=1)
        with current_app.app_context():
            scheduler.add_job(
                id=str(uuid4()),
                func=email,
                trigger="date",
                run_date=datetime(timenow.year, timenow.month, timenow.day, open_time.hour, close_time.minute),
                args=[msg, scheduler.app]
            )

    socketio.emit(f"message_sent/{group_id}/{session['user_id']}/{receiver_id}", {
        "content": content,
        "receiver_id": receiver_id
    })
    socketio.emit(f"receive_new/{group_id}/{session['user_id']}/{receiver_id}", {
        "content": content,
        "receiver_id": receiver_id
    })
