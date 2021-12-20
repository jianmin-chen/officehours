let socket;

const loadChatroom = (groupID, memberIDe) => {
    socket.emit("load_chatroom", {
        groupID: groupID,
        memberID: memberID,
    });

    socket.on("chatroom_loaded", (messages) => {

    })
}

window.onload = () => {
    socket = io.connect(`http://${document.domain}:${location.port}/`);
    socket.on("error", (err) => {
        console.log(err);
    });
}
