from flask import Blueprint

from helpers import socketio, logged_in

# Configure blueprint
blueprint = Blueprint("sockets", __name__)


@socketio.on("load_chatroom")
def load_chatroom(json):
    if not logged_in():
        # User isn't logged in
        socketio.emit("error", {
            "desc": "Oops, looks like you're not logged in yet!"
        })
        return

    group_id = json.get("groupID")
    member_id = json.get("memberID")

    if not group_id or not member_id:
        # Information not provided
        socketio.emit("error", {
            "desc": "Oops, looks like there was an error loading the chatroom!"
        })
        return

    # Make sure user belongs in chatroom
    user = db.session.execute(
        select(User).where(User.id == session["user_id"])
    ).fetchone()[0]
    belongs = False
    for group in [*user.in_charge, *user.part_of]:
        if group.id == group_id:
            belongs = True
            break
    if not belongs:
        # User doesn't belong to chatroom/chatroom doesn't exist
        socketio.emit("error", {
            "desc": "Oops, looks like there was an error loading the chatroom!"
        })
        return
    socketio.emit("chatroom_loaded", {"message": "Sucess! Great job..."})


@socketio.on("send")
def send(json):
    if not logged_in():
        # User isn't logged in
        socketio.emit("error", {
            "desc": "Oops, looks like you're not logged in yet!"
        })

    group_id = json.get("groupID")



    socketio.emit("Success", {})


@socketio.on("receive")
def receive(json):
    if not logged_in():
        # User isn't logged in
        socketio.emit("Error", {
            "desc": "Oops, looks like you're not logged in yet!"
        })
    socketio.emit("Success", {})
