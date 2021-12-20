from flask import Blueprint, current_app, session
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
            "desc": "Oops, looks like there was an error loading your chatroom!"
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

    socketio.emit("load_chatroom/success", {
        "name": name,
        "receiver_email": receiver_email,
        "messages": messages
    })


@socketio.on("load_chatroom/member")
def load_chatroom_as_member(json):
    socketio.emit("load_chatroom")


@socketio.on("send")
@login_required
def send(json):
    content = json.get("content")
    group_id = json.get("groupID")
    receiver_id = json.get("receiverID")

    if not content or not group_id or not receiever_id:
        # Information not provided
        socketio.emit("error", {
            "desc": "Oops, looks like there was an error sending your message!"
        })
        return

    # Make sure group and receiver exist
    query = db.session.execute(
        select(Member).where(
            (Member.group_id == group_id) &
            (Member.id == member_id)
        )
    ).fetchone()

    if not query:
        socketio.emit("error", {
            "desc": "Oops, looks like there was an error sending your message!"
        })
        return

    message = Message(
        content=content,
        group_id=group_id,
        sender_id=session["user_id"],
        receiver_id=session["receiver_id"]
    )
    db.session.add(message)
    db.session.commit()

    # Schedule time for receiver to receive message during their office hours
    def email():
        mail = Mail()
        message = Email(
            subject="OfficeHours - New message",
            sender=current_app.config["EMAIL_USERNAME"],
            recipients=[]
        )

    socketio.emit(f"receive/{grou}", {})
