let socket;

const loadChatroomAsCreator = (groupID, memberID) => {
    socket.emit("load_chatroom/creator", {
        groupID: groupID,
        memberID: memberID
    });
};

const loadChatroomAsMember = (groupID) => {
    socket.emit("load_chatroom/member", {
        groupID: groupID
    });
};

window.onload = () => {
    socket = io.connect(`http://${document.domain}:${location.port}/`);
    socket.on("error", (err) => {
        let toast = `
        <div class="toast show" id="js-toast">
            <div class="toast-header">
                <strong class="me-auto">Notification</strong>
                <button class="btn-close" data-bs-dismiss="toast" type="button"></button>
            </div>
            <div class="toast-body">${err.desc}</div>
        </div>
        `;
        document.querySelector(".toast-container").insertAdjacentHTML("beforeend", toast);
    });
    socket.on("load_chatroom/success", (group) => {
        document.getElementById("chatroom-title").innerText = group.name;
        document.getElementById("chatroom-receiver").innerText = group.receiver_email;
        document.getElementById("chatroom").innerHTML = "";
        let bubble;
        for (let message of group.messages) {
            if (message.self) {
                bubble = `
                <div class="message self-message">
                    <div class="message-content">${message.content}</div>
                </div>
                `;
            } else {
                bubble = `
                <div class="message others-message">
                    <div class="message-content">${message.content}</div>
                </div>
                `;
            }
            document.getElementById("chatroom").insertAdjacentHTML("beforeend", bubble);
        }
        document.getElementById("send-message").style.display = "block";
        document.getElementById("send-message").addEventListener("submit", function() {
            event.stopImmediatePropagation();
            event.stopPropagation();
            event.preventDefault();
            socket.emit("send", {
                content: this.elements.message.value,
                groupID: group.id,
                receiverID: group.receiver_id
            });
        });
        socket.on(`receive_new/${group.id}`, (message) => {
            if (message.receiver_id != group.receiver_id) {
                bubble = `
                <div class="message others-message">
                    <div class="message-content">${message.content}</div>
                </div>
                `;
                document.getElementById("chatroom").insertAdjacentHTML("beforeend", bubble);
            }
        });
        socket.on(`receive_own/${group.id}`, (message) => {
            if (message.receiver_id == group.receiver_id) {
                bubble = `
                <div class="message self-message">
                    <div class="message-content">${message.content}</div>
                </div>
                `;
                document.getElementById("chatroom").insertAdjacentHTML("beforeend", bubble);
            }
        });
    });
};
