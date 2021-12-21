from flask import Blueprint, current_app, render_template, session
from flask_mail import Mail
from flask_mail import Message as Email
from functools import wraps
from sqlalchemy import select

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
    elif is_creator:
        receiver_name = is_creator[0].creator.username
        receiver_name = is_creator[0].creator.email
        group_name = is_creator[0].name
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
    def email():
        mail = Mail()
        msg = Email(
            subject="OfficeHours - New message",
            sender=current_app.config["MAIL_USERNAME"],
            recipients=[receiver_email]
        )
        msg.html = render_template(
            "message.html",
            name=receiver_name,
            email=receiver_email,
            group_name=group_name,
            message=content
        )
        mail.send(msg)
    email()

    socketio.emit(f"message_sent/{group_id}/{session['user_id']}/{receiver_id}", {
        "content": content,
        "receiver_id": receiver_id
    })
    socketio.emit(f"receive_new/{group_id}/{session['user_id']}/{receiver_id}", {
        "content": content,
        "receiver_id": receiver_id
    })
