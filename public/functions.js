const ws = false;
let socket = null;
let chatMessages = {};

function welcome() {
    document.addEventListener("keypress", function (event) {
        if (event.code === "Enter") {
            sendChat();
        }
    });

    document.getElementById("paragraph").innerHTML += "<br/>This text was added by JavaScript 😀";
    document.getElementById("chat-text-box").focus();

    updateChat();

    if (ws) {
        initWS();
    } else {
        setInterval(updateChat, 3000);
    }

    // use this line to start your video without having to click a button. Helpful for debugging
    // startVideo();
}

function sendChat() {
    const chatTextBox = document.getElementById("chat-text-box");
    const message = chatTextBox.value;
    chatTextBox.value = "";
    if (ws) {
        // Using WebSockets
        socket.send(JSON.stringify({'messageType': 'chatMessage', 'message': message}));
    } else {
        // Using AJAX
        const request = new XMLHttpRequest();
        request.onreadystatechange = function () {
            if (this.readyState === 4 && this.status === 200) {
                console.log(this.response);
            }
        }
        const messageJSON = {"message": message};
        request.open("POST", "/chat-messages");
        request.send(JSON.stringify(messageJSON));
    }
    chatTextBox.focus();
}

function deleteMessage(messageId) {
    const request = new XMLHttpRequest();
    request.onreadystatechange = function () {
        if (this.readyState === 4 && this.status === 200) {
            console.log(this.response);
        }
    }
    request.open("DELETE", "/chat-messages/" + messageId);
    request.send();
}


function updateChat() {
    const request = new XMLHttpRequest();
    request.onreadystatechange = function () {
        if (this.readyState === 4 && this.status === 200) {
            updateChatMessages(JSON.parse(this.response));
        }
    }
    request.open("GET", "/chat-messages");
    request.send();
}

function updateChatMessages(serverMessages) {
    let serverIndex = 0
    let localIndex = 0;

    while (serverIndex < serverMessages.length && localIndex < chatMessages.length) {
        let fromServer = serverMessages[serverIndex];
        let localMessage = chatMessages[localIndex];
        if (fromServer["id"] !== localMessage["id"]) {
            // this message has been deleted
            const messageElem = document.getElementById("message_" + localMessage["id"]);
            messageElem.parentNode.removeChild(messageElem);
            localIndex++;
        } else {
            serverIndex++;
            localIndex++;
        }
    }

    while (localIndex < chatMessages.length) {
        let localMessage = chatMessages[localIndex];
        const messageElem = document.getElementById("message_" + localMessage["id"]);
        messageElem.parentNode.removeChild(messageElem);
        localIndex++;
    }

    while (serverIndex < serverMessages.length) {
        addMessageToChat(serverMessages[serverIndex]);
        serverIndex++;
    }
    chatMessages = serverMessages;
}

function addMessageToChat(messageJSON) {
    const chatMessages = document.getElementById("chat-messages");
    chatMessages.insertAdjacentHTML("beforeend", chatMessageHTML(messageJSON))
    chatMessages.scrollIntoView(false);
    chatMessages.scrollTop = chatMessages.scrollHeight - chatMessages.clientHeight;
}

function chatMessageHTML(messageJSON) {
    const username = messageJSON.username;
    const message = messageJSON.message;
    const messageId = messageJSON.id;
    const uid = messageJSON.uid
    const cookie = document.cookie
    var mark1 = ""
    var mark2 = ""
    if (cookie.includes(uid)){
        mark1 = "<mark>"
        mark2 = "</mark>"
    }

    let messageHTML = "<div id='message_" + messageId + "'><button onclick='deleteMessage(\"" + messageId + "\")'>X</button> ";
    messageHTML += "<b>" + username + "</b>: " + mark1 + message + mark2 + "</div>";

    return messageHTML;
}

function initWS() {
    // Establish a WebSocket connection with the server
    socket = new WebSocket('ws://' + window.location.host + '/websocket');

    // Called whenever data is received from the server over the WebSocket connection
    socket.onmessage = function (ws_message) {
        const message = JSON.parse(ws_message.data);
        const messageType = message.messageType
        if (messageType === 'chatMessage') {
            addMessageToChat(message);
        } else {
            // send message to WebRTC
            processMessageAsWebRTC(message, messageType);
        }
    }
}