let socket;

const loadChatroom = (groupID, memberID) => {
    socket.emit("load_chatroom", {
        group_id: groupID,
        memberID: memberID
    });

    socket.on("chatroom_loaded", (messages) => {

    })
}

window.onload = () => {
    socket = io.connect(`http://${document.domain}:${location.port}/`);
    socket.on("error", (err) => {});
}
