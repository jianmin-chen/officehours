let socket;

window.onload = () => {
    socket = io.connect(`http://${document.domain}:${location.port}/`);
    socket.on("connect", () => {
        socket.emit("load_chatroom", {});
    });
}
