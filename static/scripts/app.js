let socket, globalGroupID, globalUserID, globalReceiverID;

const createSelfBubble = (content) => {
    let div = document.createElement("div");
    div.classList.add("message", "self-message");

    let innerMessage = document.createElement("message-content");
    innerMessage.classList.add("message-content");
    innerMessage.innerText = content;

    div.appendChild(innerMessage);
    return div;
}

const createOthersBubble = (content) => {
    let div = document.createElement("div");
    div.classList.add("message", "others-message");

    let innerMessage = document.createElement("message-content");
    innerMessage.classList.add("message-content");
    innerMessage.innerText = content;

    div.appendChild(innerMessage);
    return div;
}

const sendMessage = function() {
    event.stopImmediatePropagation();
    event.stopPropagation();
    event.preventDefault();
    document.getElementById("send-message").value = "";
    socket.emit("send", {
        content: this.elements.message.value,
        groupID: globalGroupID,
        receiverID: globalReceiverID
    });
    socket.off(`message_sent/${globalGroupID}/${globalUserID}/${globalReceiverID}`);
    socket.off(`receive_new/${globalGroupID}/${globalReceiverID}/${globalUserID}`);
    socket.on(`message_sent/${globalGroupID}/${globalUserID}/${globalReceiverID}`, (message) => {
        document.getElementById("chatroom").appendChild(createSelfBubble(message.content));
        document.getElementById("send-message").scrollIntoView({
            behavior: "smooth",
            block: "end"
        });
    });
    socket.on(`receive_new/${globalGroupID}/${globalReceiverID}/${globalUserID}`, (message) => {
        document.getElementById("chatroom").appendChild(createOthersBubble(message.content));
        document.getElementById("send-message").scrollIntoView({
            behavior: "smooth",
            block: "end"
        });
    });
}

const loadChatroomAsCreator = (groupID, memberID, userID) => {
    socket.off(`message_sent/${globalGroupID}/${globalUserID}/${globalReceiverID}`);
    socket.off(`receive_new/${globalGroupID}/${globalReceiverID}/${globalUserID}`);
    globalGroupID = groupID, globalUserID = userID, globalReceiverID = memberID;
    socket.emit("load_chatroom/creator", {
        groupID: groupID,
        memberID: memberID
    });
    socket.on(`load_chatroom/${userID}/${groupID}`, (group) => {
        document.getElementById("chatroom-title").innerText = group.name;
        document.getElementById("chatroom-receiver").innerText = `${group.receiver_email}: ${group.receiver_time}`;
        document.getElementById("chatroom").innerHTML = "";
        let bubble;
        for (let message of group.messages) {
            if (message.self) {
                bubble = createSelfBubble(message.content);
            } else {
                bubble = createOthersBubble(message.content);
            }
            document.getElementById("chatroom").appendChild(bubble);
        }
        document.getElementById("send-message").style.display = "block";
        document.getElementById("send-message").scrollIntoView({
            behavior: "smooth",
            block: "end"
        });
        document.getElementById("send-message").addEventListener("submit", sendMessage);
    });
    socket.on(`message_sent/${globalGroupID}/${globalUserID}/${globalReceiverID}`, (message) => {
        document.getElementById("chatroom").appendChild(createSelfBubble(message.content));
        document.getElementById("send-message").scrollIntoView({
            behavior: "smooth",
            block: "end"
        });
    });
    socket.on(`receive_new/${globalGroupID}/${globalReceiverID}/${globalUserID}`, (message) => {
        document.getElementById("chatroom").appendChild(createOthersBubble(message.content));
        document.getElementById("send-message").scrollIntoView({
            behavior: "smooth",
            block: "end"
        });
    });
};

const loadChatroomAsMember = (groupID, creatorID, userID) => {
    socket.off(`message_sent/${globalGroupID}/${globalUserID}/${globalReceiverID}`);
    socket.off(`receive_new/${globalGroupID}/${globalReceiverID}/${globalUserID}`);
    globalGroupID = groupID, globalUserID = userID, globalReceiverID = creatorID;
    socket.emit("load_chatroom/member", {
        groupID: groupID
    });
    socket.on(`load_chatroom/${userID}/${groupID}`, (group) => {
        document.getElementById("chatroom-title").innerText = group.name;
        document.getElementById("chatroom-receiver").innerText = `${group.receiver_email}: ${group.receiver_time}`;
        document.getElementById("chatroom").innerHTML = "";
        let bubble;
        for (let message of group.messages) {
            if (message.self) {
                bubble = createSelfBubble(message.content);
            } else {
                bubble = createOthersBubble(message.content);
            }
            document.getElementById("chatroom").appendChild(bubble);
        }
        document.getElementById("send-message").style.display = "block";
        document.getElementById("send-message").scrollIntoView({
            behavior: "smooth",
            block: "end"
        });
        document.getElementById("send-message").addEventListener("submit", sendMessage);
    });
    socket.on(`message_sent/${globalGroupID}/${globalUserID}/${globalReceiverID}`, (message) => {
        document.getElementById("chatroom").appendChild(createSelfBubble(message.content));
        document.getElementById("send-message").scrollIntoView({
            behavior: "smooth",
            block: "end"
        });
    });
    socket.on(`receive_new/${globalGroupID}/${globalReceiverID}/${globalUserID}`, (message) => {
        document.getElementById("chatroom").appendChild(createOthersBubble(message.content));
        document.getElementById("send-message").scrollIntoView({
            behavior: "smooth",
            block: "end"
        });
    });
};

window.onload = () => {
    socket = io.connect(`https://${document.domain}:${location.port}/`);
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
};
